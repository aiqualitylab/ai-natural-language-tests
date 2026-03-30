#!/usr/bin/env python3
# Copyright (c) 2024-2026 Sreekanth Harigovindan / AI Quality Lab
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
AI-Powered Cypress, Playwright, and WebdriverIO test generator with LangGraph & Vector Store
"""

import os
import re
import sys
import json
import argparse
import requests
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from dotenv import load_dotenv

# FAISS + SQLite imports
import sqlite3

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


PROMPT_SPEC_DIR = Path(__file__).parent / "prompt_specs"
VECTOR_DB_DIR = Path(__file__).parent / "vector_db"

LLM_CONFIG = {
    "openai":    {"name": "OpenAI (ChatGPT)",   "model": "gpt-4o-mini",               "provider": "openai"},
    "anthropic": {"name": "Anthropic (Claude)", "model": "claude-3-5-sonnet-20241022", "provider": "anthropic"},
    "google":    {"name": "Google (Gemini)",     "model": "gemini-2.0-flash",           "provider": "google"},
}

DEFAULT_LLM = "openai"

ALLOWED_FAILURE_CATEGORIES = {
    "SELECTOR",
    "TIMING",
    "ASSERTION",
    "NETWORK",
    "STATE",
    "NAVIGATION",
    "INTERACTION",
    "CONFIGURATION",
}

SYMBOLIC_RULES = """
SELECTOR CONVENTIONS (MANDATORY):
- ALWAYS prefer data-testid attributes: [data-testid="submit-button"]
- Use data-cy as second choice for Cypress-specific attributes: [data-cy="login-form"]
- Use aria-label or role-based selectors as third choice: [aria-label="Password"]
- Use CSS class or ID only when no semantic alternative exists
- NEVER use XPath selectors (//, .//tag[@attr])
- NEVER use :nth-child(), :nth-of-type(), or positional pseudo-selectors
- NEVER chain more than 2 CSS descendant combinators (e.g. .a .b .c is the limit)
- NEVER use inline style attribute selectors (e.g. [style="color: red"])

ASSERTION REQUIREMENTS (MANDATORY):
- Every test MUST have at least one explicit assertion (not just an action)
- Assertions must check observable outcomes: visibility, text content, URL change, or element state
- NEVER assert on implementation details such as CSS class names that carry no semantic meaning
- Use existence + visibility assertions together: .should('exist') and .should('be.visible') for Cypress
- For success flows: assert that a success indicator is visible OR the URL changed away from the action page
- For error flows: assert that an error indicator is visible with non-empty text
- NEVER leave an assertion as a TODO or placeholder comment
"""


def _get_provider_constructor(provider: str) -> Any:
    providers = {
        "openai": lambda cfg: ChatOpenAI(model=cfg["model"], temperature=0),
        "anthropic": lambda cfg: ChatAnthropic(model=cfg["model"], temperature=0) if ChatAnthropic else None,
        "google": lambda cfg: ChatGoogleGenerativeAI(model=cfg["model"], temperature=0) if ChatGoogleGenerativeAI else None,
    }
    return providers.get(provider, lambda cfg: ChatOpenAI(model=cfg["model"], temperature=0))

def get_llm(provider: str = DEFAULT_LLM) -> Any:
    if provider not in LLM_CONFIG:
        logger.warning(f"Unknown provider '{provider}', using default {DEFAULT_LLM}")
        provider = DEFAULT_LLM
    config = LLM_CONFIG[provider]
    ctor = _get_provider_constructor(provider)
    result = ctor(config)
    if result is None:
        logger.warning(f"{provider} not installed, falling back to OpenAI")
        return ChatOpenAI(model=LLM_CONFIG[DEFAULT_LLM]["model"], temperature=0)
    return result


FRAMEWORK_CONFIG = {
    "cypress": {
        "name": "Cypress",
        "file_ext": ".cy.js",
        "default_output": "cypress/e2e",
        "run_cmd": "npx cypress run --spec",
        "code_fence": "javascript",
        "prompt_file_standard": "test_generation_traditional.yaml",
        "prompt_file_prompt": "test_generation_prompt_powered.yaml",
        "supports_prompt_mode": True,
    },
    "playwright": {
        "name": "Playwright",
        "file_ext": ".spec.ts",
        "default_output": "tests",
        "run_cmd": "npx playwright test",
        "code_fence": "typescript",
        "prompt_file_standard": "test_generation_playwright.yaml",
        "supports_prompt_mode": False,
    },
    "webdriverio": {
        "name": "WebdriverIO",
        "file_ext": ".spec.js",
        "default_output": "webdriverio/tests",
        "run_cmd": "npx wdio run wdio.conf.js",
        "code_fence": "javascript",
        "prompt_file_standard": "test_generation_webdriverio.yaml",
        "supports_prompt_mode": False,
    },
}


# VECTOR STORE + METADATA

class TestPatternStore:
    """Simple FAISS + SQLite pattern store."""

    def __init__(self, db_name: str = "test_patterns.db") -> None:
        logger.info("Setting up FAISS + SQLite vector store")
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

        self.db_path = VECTOR_DB_DIR / db_name
        self.faiss_index_path = VECTOR_DB_DIR / "faiss_index"

        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )

        self._init_sqlite()
        self.vectorstore = self._load_faiss_index()
        logger.info("FAISS + SQLite vector store ready")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _get_table_columns(self) -> set:
        with self._connect() as conn:
            rows = conn.execute("PRAGMA table_info(test_patterns)").fetchall()
            return {row[1] for row in rows}

    def _init_sqlite(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS test_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requirement TEXT NOT NULL,
                    url TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    test_code TEXT NOT NULL
                )
                """
            )
            conn.commit()

        columns = self._get_table_columns()
        if "test_code" not in columns:
            with self._connect() as conn:
                conn.execute("ALTER TABLE test_patterns ADD COLUMN test_code TEXT NOT NULL DEFAULT ''")
                conn.commit()

    def _load_faiss_index(self) -> Optional[FAISS]:
        if not self.faiss_index_path.exists():
            return None

        try:
            logger.info("Loading existing FAISS index")
            return FAISS.load_local(
                str(self.faiss_index_path),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            logger.warning(f"Could not load FAISS index: {e}")
            return None

    def store_pattern(self, test_code: str, requirement: str, url: str, test_type: str, filepath: str) -> None:
        logger.info(f"Storing pattern: {requirement}")

        timestamp = datetime.now().isoformat()
        metadata = {
            "requirement": requirement,
            "url": url,
            "test_type": test_type,
            "filepath": filepath,
            "timestamp": timestamp,
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO test_patterns (requirement, url, test_type, filepath, timestamp, test_code)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (requirement, url, test_type, filepath, timestamp, test_code),
            )
            conn.commit()

        doc = Document(page_content=test_code, metadata=metadata)
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents([doc], self.embeddings)
        else:
            self.vectorstore.add_documents([doc])

        self.vectorstore.save_local(str(self.faiss_index_path))
        logger.info("Pattern stored")

    def search_similar_patterns(self, requirement: str, k: int = 2) -> List[Document]:
        logger.info(f"Searching for patterns like: {requirement}")
        if self.vectorstore is None:
            return []

        try:
            results = self.vectorstore.similarity_search(requirement, k=max(1, k))
            logger.info(f"Found {len(results)} similar patterns")
            return results
        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []

    def get_all_patterns(self) -> List[Document]:
        logger.info("Retrieving all patterns")
        columns = self._get_table_columns()
        query = """
            SELECT requirement, url, test_type, filepath, timestamp, test_code
            FROM test_patterns
            ORDER BY id DESC
        """ if "test_code" in columns else """
            SELECT requirement, url, test_type, filepath, timestamp, '' AS test_code
            FROM test_patterns
            ORDER BY id DESC
        """
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()

        return [
            Document(
                page_content=row[5],
                metadata={
                    "requirement": row[0],
                    "url": row[1],
                    "test_type": row[2],
                    "filepath": row[3],
                    "timestamp": row[4],
                },
            )
            for row in rows
        ]



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

def load_prompt_template(filename: str, **variables: Any) -> str:
    spec = load_prompt_spec(filename, required_keys=["template"])
    template = str(spec.get("template", ""))
    return template.format(**variables)


def load_prompt_spec(filename: str, required_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    logger.info(f"Loading prompt spec: {filename}")
    spec_path = PROMPT_SPEC_DIR / filename
    with open(spec_path, "r", encoding="utf-8") as file:
        spec = yaml.safe_load(file) or {}

    # Validate required keys strictly, but keep recommended keys as warnings.
    missing_required = [key for key in (required_keys or []) if key not in spec]
    if missing_required:
        raise ValueError(f"Prompt spec '{filename}' is missing required key '{missing_required[0]}'")

    for key in ("name", "version", "metadata"):
        if key not in spec:
            logger.warning(f"Prompt spec '{filename}' is missing recommended key '{key}'")

    return spec


def load_prompt_system(filename: str) -> str:
    spec = load_prompt_spec(filename)
    return str(spec.get("system", ""))


def extract_code_fence(content: str) -> str:
    fence_markers = ["```typescript", "```javascript", "```js", "```"]
    for marker in fence_markers:
        if marker in content:
            between = content.split(marker)[1].split("```")[0].strip()
            return between
    return content


def get_test_filepath(framework: str, output_dir: str, use_prompt_mode: bool, index: int, requirement: str) -> tuple:
    fw = FRAMEWORK_CONFIG[framework]
    folder_name = "prompt-powered" if (framework == "cypress" and use_prompt_mode) else "generated"
    output_base = output_dir if output_dir != "cypress/e2e" else fw["default_output"]
    folder = f"{output_base}/{folder_name}"
    os.makedirs(folder, exist_ok=True)
    slug = re.sub(r"[^\w\s-]", "", requirement.lower()).replace(" ", "-")[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{index:02d}_{slug}_{timestamp}{fw['file_ext']}"
    filepath = f"{folder}/{filename}"
    return filepath, filename, folder_name


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
        prompt = load_prompt_template("html_analysis.yaml", url=state.url, html=html)
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
            logger.warning(f"--use-prompt ignored: {fw['name']} does not support prompt-powered mode")

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
                prompt = load_prompt_template(
                    prompt_file,
                    requirement=requirement,
                    context=state.context,
                    symbolic_rules=SYMBOLIC_RULES,
                )
                ai_response = llm.invoke(prompt)
                content = extract_code_fence(ai_response.content)

                filepath, filename, folder_name = get_test_filepath(
                    state.framework, state.output_dir, use_prompt_mode, index, requirement
                )

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


def build_run_command(framework: str, generated_tests: List, output_dir: str, use_prompt_mode: bool) -> str:
    fw = FRAMEWORK_CONFIG[framework]
    if framework == "playwright":
        specs = [f'"{t["filepath"]}"' for t in generated_tests if t.get("filepath", "").endswith(fw["file_ext"])]
        return f"npx playwright test {' '.join(specs)}" if specs else \
               f"npx playwright test {output_dir if output_dir != 'cypress/e2e' else fw['default_output']}/generated"
    elif framework == "webdriverio":
        spec_paths = [t["filepath"] for t in generated_tests if t.get("filepath", "").endswith(fw["file_ext"])]
        spec_arg = ",".join(spec_paths)
        return f'npx wdio run wdio.conf.js --spec "{spec_arg}"' if spec_arg else "npx wdio run wdio.conf.js"
    else:
        folder_name = "prompt-powered" if use_prompt_mode else "generated"
        return f"npx cypress run --spec 'cypress/e2e/{folder_name}/**/*.cy.js'"

def step_5_run_tests(state: TestState) -> TestState:
    with tracer.start_as_current_span("step_5_run_tests") as span:
        logger.info("STEP 5: Run Tests")
        span.set_attribute("step", 5)
        span.set_attribute("framework", state.framework)

        fw = FRAMEWORK_CONFIG[state.framework]
        use_prompt_mode = state.use_prompt and fw["supports_prompt_mode"]
        cmd = build_run_command(state.framework, state.generated_tests, state.output_dir, use_prompt_mode)

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

def build_failure_analysis_messages(log_text: str) -> List[Dict[str, str]]:
    system_content = load_prompt_system("failure_analysis.yaml")
    user_content = load_prompt_template("failure_analysis.yaml", log=log_text)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _read_value(content: str, key: str) -> str:
    prefix = f"{key}:"
    for line in content.splitlines():
        clean_line = line.strip()
        if clean_line.upper().startswith(prefix):
            return clean_line[len(prefix):].strip()
    return ""


FAILURE_DEFAULTS = {
    "REASON": "Unable to determine root cause from log; output did not include structured reason.",
    "FIX": "Add explicit waits/assertions around the failing step and verify selectors for the detected framework.",
}

def format_failure_analysis(content: str) -> str:
    category = _read_value(content, "CATEGORY").upper()
    reason = _read_value(content, "REASON") or FAILURE_DEFAULTS["REASON"]
    fix = _read_value(content, "FIX") or FAILURE_DEFAULTS["FIX"]
    category = category if category in ALLOWED_FAILURE_CATEGORIES else "CONFIGURATION"
    return f"CATEGORY: {category}\nREASON: {reason}\nFIX: {fix}"

def analyze_test_failure(log_text: str) -> str:
    with tracer.start_as_current_span("analyze_test_failure") as span:
        logger.info("Analyzing test failure")
        span.set_attribute("log_length", len(log_text))
        messages = build_failure_analysis_messages(log_text)
        response = requests.post(
            url="https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": messages, "max_tokens": 300}
        )
        logger.info("Analysis complete")
        span.set_attribute("success", response.ok)
        if not response.ok:
            return f"Error: {response.text}"

        content = response.json()["choices"][0]["message"]["content"]
        return format_failure_analysis(content)


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
        framework_name = FRAMEWORK_CONFIG.get(args.framework, {}).get("name", args.framework)
        logger.info(f"Framework: {framework_name}")
        logger.info(f"Generated tests: {len(final_state['generated_tests'])}")
        logger.info(f"Similar patterns used: {len(final_state['similar_patterns'])}")
        for test in final_state["generated_tests"]:
            logger.info(f"  - {test['filename']}")
        if final_state.get("test_results"):
            logger.info(f"Tests passed: {final_state['test_results']['success']}")
            span.set_attribute("tests_passed", final_state["test_results"]["success"])


# MAIN

def dispatch_cli_mode(args: argparse.Namespace) -> None:
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
    parser = argparse.ArgumentParser()
    parser.print_help()

def main() -> None:
    logger.info("AI-Powered Test Generator (Cypress, Playwright, and WebdriverIO)")
    logger.info("With LangGraph Workflows and Vector Store Learning")

    parser = argparse.ArgumentParser(
        description="AI Test Generator — Cypress, Playwright, and WebdriverIO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python qa_automation.py "Test login" --url https://example.com/login
  python qa_automation.py "Test login" --url https://example.com/login --framework playwright
  python qa_automation.py "Test login" --url https://example.com/login --framework webdriverio
  python qa_automation.py "Test login" --url https://example.com/login --use-prompt
  python qa_automation.py "Test login" --url https://example.com/login --run
  python qa_automation.py "Test login" --url https://example.com/login --llm anthropic
  python qa_automation.py --analyze "CypressError: Element not found"
  python qa_automation.py --analyze -f error.log
  python qa_automation.py --list-patterns
"""
    )
    parser.add_argument("requirements", nargs="*", help="Test requirements in natural language")
    parser.add_argument(
        "--framework",
        "-fw",
        choices=["cypress", "playwright", "webdriverio"],
        default="cypress",
    )
    parser.add_argument("--url", "-u")
    parser.add_argument("--out", default="cypress/e2e")
    parser.add_argument("--use-prompt", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--llm", choices=list(LLM_CONFIG.keys()), default=DEFAULT_LLM)
    parser.add_argument("--analyze", "-a", nargs="?", const="")
    parser.add_argument("--file", "-f")
    parser.add_argument("--list-patterns", action="store_true")

    args = parser.parse_args()
    dispatch_cli_mode(args)


if __name__ == "__main__":
    main()