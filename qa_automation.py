#!/usr/bin/env python3
# Copyright (c) 2024-2026 Sreekanth Harigovindan / AI Quality Lab
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
AI-Powered Cypress & Playwright Test Generator with LangGraph & Vector Store
"""

import os
import re
import sys
import json
import argparse
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

# ── OpenTelemetry (Traces → Grafana Tempo) ────────────────────────────────────
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def _setup_tracing() -> tuple:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip().rstrip("/")
    auth = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "").strip().replace("Authorization=", "", 1)
    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
        headers={"Authorization": auth},
    )
    provider = TracerProvider(resource=Resource.create({"service.name": "ai-natural-language-tests"}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ai-natural-language-tests"), provider

tracer, _otel_provider = _setup_tracing()


# ── Loki Logging (Logs → Grafana Loki) ───────────────────────────────────────
def _setup_loki_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    _logger = logging.getLogger("ai-natural-language-tests")
    try:
        import logging_loki
        _logger.addHandler(logging_loki.LokiHandler(
            url=f"{os.getenv('GRAFANA_LOKI_URL').strip()}/loki/api/v1/push",
            tags={"service_name": "ai-natural-language-tests", "app": "ai-quality-lab"},
            auth=(os.getenv("GRAFANA_INSTANCE_ID").strip(), os.getenv("GRAFANA_API_TOKEN").strip()),
            version="1",
        ))
        _logger.info("[LOKI] Handler attached")
    except Exception as e:
        _logger.warning(f"[LOKI] Skipped: {e}")
    return _logger

logger = _setup_loki_logging()


try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None


PROMPT_DIR = Path(__file__).parent / "prompts"
VECTOR_DB_DIR = Path(__file__).parent / "vector_db"

LLM_CONFIG = {
    "openai":    {"name": "OpenAI (ChatGPT)",   "model": "gpt-4o-mini",               "provider": "openai"},
    "anthropic": {"name": "Anthropic (Claude)", "model": "claude-3-5-sonnet-20241022", "provider": "anthropic"},
    "google":    {"name": "Google (Gemini)",     "model": "gemini-2.0-flash",           "provider": "google"},
}

DEFAULT_LLM = "openai"


def get_llm(provider: str = DEFAULT_LLM) -> Any:
    if provider not in LLM_CONFIG:
        logger.warning(f"Unknown provider '{provider}', using default {DEFAULT_LLM}")
        provider = DEFAULT_LLM
    config = LLM_CONFIG[provider]
    if provider == "openai":
        return ChatOpenAI(model=config["model"], temperature=0)
    elif provider == "anthropic":
        if ChatAnthropic is None:
            logger.warning("Anthropic not installed, falling back to OpenAI")
            return ChatOpenAI(model=LLM_CONFIG[DEFAULT_LLM]["model"], temperature=0)
        return ChatAnthropic(model=config["model"], temperature=0)
    elif provider == "google":
        if ChatGoogleGenerativeAI is None:
            logger.warning("Google not installed, falling back to OpenAI")
            return ChatOpenAI(model=LLM_CONFIG[DEFAULT_LLM]["model"], temperature=0)
        return ChatGoogleGenerativeAI(model=config["model"], temperature=0)
    return ChatOpenAI(model=LLM_CONFIG[DEFAULT_LLM]["model"], temperature=0)


FRAMEWORK_CONFIG = {
    "cypress": {
        "name": "Cypress",
        "file_ext": ".cy.js",
        "default_output": "cypress/e2e",
        "run_cmd": "npx cypress run --spec",
        "code_fence": "javascript",
        "prompt_file_standard": "test_generation_traditional.txt",
        "prompt_file_prompt": "test_generation_prompt_powered.txt",
        "supports_prompt_mode": True,
    },
    "playwright": {
        "name": "Playwright",
        "file_ext": ".spec.ts",
        "default_output": "tests",
        "run_cmd": "npx playwright test",
        "code_fence": "typescript",
        "prompt_file_standard": "test_generation_playwright.txt",
        "supports_prompt_mode": False,
    },
}


# VECTOR STORE

class TestPatternStore:
    def __init__(self) -> None:
        logger.info("Setting up vector store")
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma(
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=self.embeddings
        )
        logger.info("Vector store ready")

    def store_pattern(self, test_code: str, requirement: str, url: str, test_type: str, filepath: str) -> None:
        logger.info(f"Storing pattern: {requirement}")
        doc = Document(
            page_content=test_code,
            metadata={"requirement": requirement, "url": url, "test_type": test_type,
                      "filepath": filepath, "timestamp": datetime.now().isoformat()}
        )
        self.vectorstore.add_documents([doc])
        logger.info("Pattern stored")

    def search_similar_patterns(self, requirement: str) -> List[Document]:
        logger.info(f"Searching for patterns like: {requirement}")
        count = self.vectorstore._collection.count()
        results = self.vectorstore.similarity_search(requirement, k=min(2, count)) if count > 0 else []
        logger.info(f"Found {len(results)} similar patterns")
        return results

    def get_all_patterns(self) -> List[Document]:
        count = self.vectorstore._collection.count()
        return self.vectorstore.similarity_search("", k=count) if count > 0 else []


# STATE

@dataclass
class TestState:
    requirements: List[str]
    output_dir: str
    use_prompt: bool
    framework: str = "cypress"
    url: Optional[str] = None
    run_tests: bool = False
    llm_provider: str = DEFAULT_LLM
    test_data: Optional[Dict] = None
    context: str = ""
    similar_patterns: List = field(default_factory=list)
    generated_tests: List = field(default_factory=list)
    test_results: Optional[Dict] = None
    vector_store: Optional[TestPatternStore] = None


# UTILITIES

def load_prompt_file(filename: str, **variables: Any) -> str:
    logger.info(f"Loading prompt: {filename}")
    return (PROMPT_DIR / filename).read_text(encoding="utf-8").format(**variables)


# WORKFLOW NODES — every step has its own span ✅

def step_1_initialize_vector_store(state: TestState) -> TestState:
    with tracer.start_as_current_span("step_1_initialize_vector_store") as span:
        logger.info("STEP 1: Initialize Vector Store")
        span.set_attribute("step", 1)
        state.vector_store = TestPatternStore()
        span.set_attribute("vector_db_dir", str(VECTOR_DB_DIR))
        return state


def step_2_fetch_test_data(state: TestState) -> TestState:
    with tracer.start_as_current_span("step_2_fetch_test_data") as span:
        logger.info("STEP 2: Fetch Test Data")
        span.set_attribute("step", 2)
        span.set_attribute("url", state.url or "none")
        span.set_attribute("llm_provider", state.llm_provider)

        if not state.url:
            logger.info("No URL provided, skipping HTML analysis")
            span.set_attribute("skipped", True)
            return state

        logger.info(f"Fetching URL: {state.url}")
        response = requests.get(state.url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        html = response.text[:5000]
        logger.info(f"Got {len(html)} characters of HTML")
        span.set_attribute("html_length", len(html))

        llm = get_llm(state.llm_provider)
        prompt = load_prompt_file("html_analysis.txt", url=state.url, html=html)
        ai_response = llm.invoke(prompt)
        content = ai_response.content.strip()

        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()

        test_data = json.loads(content)
        filepath = "cypress/fixtures/url_test_data.json"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(test_data, f, indent=2)

        logger.info(f"Saved test data to: {filepath}")
        span.set_attribute("fixture_path", filepath)

        state.test_data = test_data
        state.context = (
            f"FIXTURE: {filepath}\nURL: {state.url}\n"
            f"SELECTORS: {json.dumps(test_data.get('selectors', {}))}\n"
            f"TEST_CASES: {json.dumps(test_data.get('test_cases', []))}\n"
            f"TEST_DATA_JSON: {json.dumps(test_data)}"
        )
        return state


def step_3_search_similar_patterns(state: TestState) -> TestState:
    with tracer.start_as_current_span("step_3_search_similar_patterns") as span:
        logger.info("STEP 3: Search Similar Patterns")
        span.set_attribute("step", 3)
        span.set_attribute("requirements_count", len(state.requirements))

        all_patterns = []
        for requirement in state.requirements:
            all_patterns.extend(state.vector_store.search_similar_patterns(requirement))

        state.similar_patterns = all_patterns
        logger.info(f"Found {len(all_patterns)} similar patterns total")
        span.set_attribute("patterns_found", len(all_patterns))

        if all_patterns:
            state.context += "\n\nSIMILAR PATTERNS FROM PAST:\n" + "\n".join(
                f"\nPattern {i}:\n{p.page_content[:200]}..."
                for i, p in enumerate(all_patterns[:3], 1)
            )
        return state


def step_4_generate_tests(state: TestState) -> TestState:
    with tracer.start_as_current_span("step_4_generate_tests") as span:
        logger.info("STEP 4: Generate Tests")
        span.set_attribute("step", 4)
        span.set_attribute("framework", state.framework)
        span.set_attribute("llm_provider", state.llm_provider)
        span.set_attribute("requirements_count", len(state.requirements))

        fw = FRAMEWORK_CONFIG[state.framework]
        use_prompt_mode = state.use_prompt and fw["supports_prompt_mode"]

        if state.use_prompt and not fw["supports_prompt_mode"]:
            logger.warning(f"--use-prompt ignored: {fw['name']} does not support cy.prompt()")

        llm = get_llm(state.llm_provider)
        generated_tests = []

        for index, requirement in enumerate(state.requirements, 1):
            # child span per test — visible as nested spans in Grafana Tempo
            with tracer.start_as_current_span("generate_single_test") as test_span:
                logger.info(f"Generating test {index}/{len(state.requirements)}: {requirement}")
                test_span.set_attribute("requirement", requirement)
                test_span.set_attribute("index", index)
                test_span.set_attribute("framework", state.framework)

                prompt_file = fw["prompt_file_prompt"] if use_prompt_mode else fw["prompt_file_standard"]
                prompt = load_prompt_file(prompt_file, requirement=requirement, context=state.context)
                ai_response = llm.invoke(prompt)
                content = ai_response.content

                if "```typescript" in content:
                    content = content.split("```typescript")[1].split("```")[0].strip()
                elif "```javascript" in content:
                    content = content.split("```javascript")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                folder_name = "prompt-powered" if (state.framework == "cypress" and use_prompt_mode) else "generated"
                output_base = state.output_dir if state.output_dir != "cypress/e2e" else fw["default_output"]
                folder = f"{output_base}/{folder_name}"
                os.makedirs(folder, exist_ok=True)

                slug = re.sub(r"[^\w\s-]", "", requirement.lower()).replace(" ", "-")[:50]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{index:02d}_{slug}_{timestamp}{fw['file_ext']}"
                filepath = f"{folder}/{filename}"

                with open(filepath, "w") as f:
                    f.write(f"// Requirement: {requirement}\n\n{content}")

                logger.info(f"Saved: {filename}")
                test_span.set_attribute("filepath", filepath)

                state.vector_store.store_pattern(
                    test_code=content,
                    requirement=requirement,
                    url=state.url or "",
                    test_type=f"{state.framework}_{'prompt_powered' if use_prompt_mode else 'traditional'}",
                    filepath=filepath,
                )
                generated_tests.append({"requirement": requirement, "filepath": filepath, "filename": filename})

        state.generated_tests = generated_tests
        span.set_attribute("tests_generated", len(generated_tests))
        return state


def step_5_run_tests(state: TestState) -> TestState:
    with tracer.start_as_current_span("step_5_run_tests") as span:
        logger.info("STEP 5: Run Tests")
        span.set_attribute("step", 5)
        span.set_attribute("framework", state.framework)

        fw = FRAMEWORK_CONFIG[state.framework]
        use_prompt_mode = state.use_prompt and fw["supports_prompt_mode"]

        if state.framework == "playwright":
            specs = [f'"{t["filepath"]}"' for t in state.generated_tests if t.get("filepath", "").endswith(fw["file_ext"])]
            cmd = f"npx playwright test {' '.join(specs)}" if specs else \
                  f"npx playwright test {state.output_dir if state.output_dir != 'cypress/e2e' else fw['default_output']}/generated"
        else:
            folder_name = "prompt-powered" if use_prompt_mode else "generated"
            cmd = f"npx cypress run --spec 'cypress/e2e/{folder_name}/**/*.cy.js'"

        logger.info(f"Running: {cmd}")
        span.set_attribute("run_command", cmd)
        exit_code = os.system(cmd)

        state.test_results = {"exit_code": exit_code, "success": exit_code == 0, "timestamp": datetime.now().isoformat()}
        span.set_attribute("exit_code", exit_code)
        span.set_attribute("success", exit_code == 0)
        logger.info(f"Tests finished with exit code: {exit_code}")
        return state


# WORKFLOW

def should_run_tests(state: TestState) -> str:
    return "run_tests" if state.run_tests else END


def create_workflow() -> Any:
    logger.info("Building workflow")
    workflow = StateGraph(TestState)
    workflow.add_node("step_1", step_1_initialize_vector_store)
    workflow.add_node("step_2", step_2_fetch_test_data)
    workflow.add_node("step_3", step_3_search_similar_patterns)
    workflow.add_node("step_4", step_4_generate_tests)
    workflow.add_node("step_5", step_5_run_tests)
    workflow.set_entry_point("step_1")
    workflow.add_edge("step_1", "step_2")
    workflow.add_edge("step_2", "step_3")
    workflow.add_edge("step_3", "step_4")
    workflow.add_conditional_edges("step_4", should_run_tests, {"run_tests": "step_5", END: END})
    workflow.add_edge("step_5", END)
    logger.info("Workflow ready")
    return workflow.compile()


# ACTIONS

def analyze_test_failure(log_text: str) -> str:
    with tracer.start_as_current_span("analyze_test_failure") as span:
        logger.info("Analyzing test failure")
        span.set_attribute("log_length", len(log_text))
        prompt_path = PROMPT_DIR / "failure_analysis.txt"
        with open(prompt_path, "r") as f:
            prompt = f.read().replace("{log}", log_text)
        response = requests.post(
            url="https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300}
        )
        logger.info("Analysis complete")
        span.set_attribute("success", response.ok)
        return response.json()["choices"][0]["message"]["content"] if response.ok else f"Error: {response.text}"


def list_all_patterns() -> None:
    logger.info("Listing all patterns")
    patterns = TestPatternStore().get_all_patterns()
    logger.info(f"Total patterns: {len(patterns)}")
    for i, p in enumerate(patterns, 1):
        logger.info(f"Pattern {i}: {p.metadata.get('requirement', 'N/A')}")
        logger.info(f"  Type: {p.metadata.get('test_type', 'N/A')}")
        logger.info(f"  Preview: {p.page_content[:100]}...")


def generate_tests_action(args: argparse.Namespace) -> None:
    with tracer.start_as_current_span("generate_tests_action") as span:
        logger.info("Starting test generation")
        span.set_attribute("framework", args.framework)
        span.set_attribute("llm_provider", args.llm)
        span.set_attribute("requirements_count", len(args.requirements))
        span.set_attribute("url", args.url or "none")

        state = TestState(
            requirements=args.requirements,
            output_dir=args.out,
            use_prompt=args.use_prompt,
            framework=args.framework,
            url=args.url,
            run_tests=args.run,
            llm_provider=args.llm,
        )

        final_state = create_workflow().invoke(state)

        # Flush all spans to Grafana before process exits
        _otel_provider.force_flush(timeout_millis=10000)

        logger.info("=" * 50)
        logger.info("GENERATION COMPLETE")
        logger.info("=" * 50)
        logger.info(f"Framework: {args.framework.upper()}")
        logger.info(f"Generated tests: {len(final_state['generated_tests'])}")
        logger.info(f"Similar patterns used: {len(final_state['similar_patterns'])}")
        for test in final_state["generated_tests"]:
            logger.info(f"  - {test['filename']}")
        if final_state.get("test_results"):
            logger.info(f"Tests passed: {final_state['test_results']['success']}")
            span.set_attribute("tests_passed", final_state["test_results"]["success"])


# MAIN

def main() -> None:
    logger.info("AI-Powered Test Generator (Cypress & Playwright)")
    logger.info("With LangGraph Workflows and Vector Store Learning")

    parser = argparse.ArgumentParser(
        description="AI Test Generator — Cypress & Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python qa_automation.py "Test login" --url https://example.com/login
  python qa_automation.py "Test login" --url https://example.com/login --framework playwright
  python qa_automation.py "Test login" --url https://example.com/login --use-prompt
  python qa_automation.py "Test login" --url https://example.com/login --run
  python qa_automation.py "Test login" --url https://example.com/login --llm anthropic
  python qa_automation.py --analyze "CypressError: Element not found"
  python qa_automation.py --analyze -f error.log
  python qa_automation.py --list-patterns
"""
    )
    parser.add_argument("requirements", nargs="*", help="Test requirements in natural language")
    parser.add_argument("--framework", "-fw", choices=["cypress", "playwright"], default="cypress")
    parser.add_argument("--url", "-u")
    parser.add_argument("--out", default="cypress/e2e")
    parser.add_argument("--use-prompt", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--llm", choices=list(LLM_CONFIG.keys()), default=DEFAULT_LLM)
    parser.add_argument("--analyze", "-a", nargs="?", const="")
    parser.add_argument("--file", "-f")
    parser.add_argument("--list-patterns", action="store_true")

    args = parser.parse_args()

    if args.analyze is not None or args.file:
        log_text = open(args.file).read() if args.file else args.analyze or sys.stdin.read()
        logger.info(analyze_test_failure(log_text))
        return

    if args.list_patterns:
        list_all_patterns()
        return

    if args.requirements:
        generate_tests_action(args)
        return

    parser.print_help()


if __name__ == "__main__":
    main()