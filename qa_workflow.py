from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from qa_config import FRAMEWORK_CONFIG, SYMBOLIC_RULES, get_llm, load_prompt_template
from qa_runtime import (
    VECTOR_DB_DIR,
    build_html_analysis_result,
    build_run_command,
    fetch_html_content,
    get_pattern_store,
    logger,
    save_html_analysis_debug,
    tracer,
)


WORKFLOW_CHECKPOINTER = MemorySaver()


class CodeFenceParser(BaseOutputParser[str]):
    def parse(self, text: str) -> str:
        fence_markers = ["```typescript", "```javascript", "```js", "```"]
        marker = next((item for item in fence_markers if item in text), None)
        if marker is None:
            return text
        return text.split(marker, 1)[1].split("```", 1)[0].strip()


CODE_FENCE_PARSER = CodeFenceParser()


@dataclass
class TestState:
    requirements: List[str]
    output_dir: str
    use_prompt: bool
    approve: bool = False
    framework: str = "cypress"
    url: Optional[str] = None
    run_tests: bool = False
    llm_provider: str = "openai"
    test_data: Optional[Dict] = None
    context: str = ""
    similar_patterns: List = field(default_factory=list)
    generated_tests: List = field(default_factory=list)
    test_results: Optional[Dict] = None
    run_id: str = ""


def extract_code_fence(content: str) -> str:
    return CODE_FENCE_PARSER.parse(content)


def get_test_filepath(framework: str, output_dir: str, use_prompt_mode: bool, index: int, requirement: str) -> tuple:
    import os
    import re

    fw = FRAMEWORK_CONFIG[framework]
    folder_name = "prompt-powered" if framework == "cypress" and use_prompt_mode else "generated"
    output_base = output_dir if output_dir != "cypress/e2e" else fw["default_output"]
    folder = f"{output_base}/{folder_name}"
    os.makedirs(folder, exist_ok=True)
    slug = re.sub(r"[^\w\s-]", "", requirement.lower()).replace(" ", "-")[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{index:02d}_{slug}_{timestamp}{fw['file_ext']}"
    filepath = f"{folder}/{filename}"
    return filepath, filename, folder_name


def preview_and_approve(content: str, requirement: str, filepath: str) -> bool:
    print(f"\nPreview: {requirement}")
    print(content)
    print(f"Save to: {filepath}")
    return input("Approve save? (y/N): ").strip().lower() == "y"


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

        html = fetch_html_content(state.url)
        span.set_attribute("html_length", len(html))

        test_data, prompt, raw_response = build_html_analysis_result(state.url, html, state.llm_provider)
        filepath = "cypress/fixtures/url_test_data.json"

        import os
        import json

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as file:
            json.dump(test_data, file, indent=2)

        logger.info(f"Saved test data to: {filepath}")
        span.set_attribute("fixture_path", filepath)

        get_pattern_store()
        state.run_id = state.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = save_html_analysis_debug(
            {
                "run_id": state.run_id,
                "timestamp": datetime.now().isoformat(),
                "url": state.url,
                "html_sample": html,
                "prompt": prompt,
                "raw_response": raw_response,
                "parsed_test_data": test_data,
                "selectors_snapshot": test_data.get("selectors", {}),
                "selector_reasoning": test_data.get("selector_reasoning", {}),
            }
        )
        logger.info(f"Saved HTML analysis debug run: {run_id}")
        span.set_attribute("html_debug_run_id", run_id)

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
        store = get_pattern_store()

        search_chain = RunnableLambda(store.search_similar_patterns)
        all_patterns = list(chain.from_iterable(search_chain.batch(state.requirements)))

        state.similar_patterns = all_patterns
        logger.info(f"Found {len(all_patterns)} similar patterns total")
        span.set_attribute("patterns_found", len(all_patterns))

        if all_patterns:
            state.context += "\n\nSIMILAR PATTERNS FROM PAST:\n" + "\n".join(
                f"\nPattern {i}:\n{p.page_content[:200]}..." for i, p in enumerate(all_patterns[:3], 1)
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
        store = get_pattern_store()
        generated_tests = []
        prompt_file = fw["prompt_file_prompt"] if use_prompt_mode else fw["prompt_file_standard"]
        build_prompt = RunnableLambda(
            lambda req: load_prompt_template(
                prompt_file,
                requirement=req,
                context=state.context,
                symbolic_rules=SYMBOLIC_RULES,
            )
        )
        generation_chain = build_prompt | llm | CODE_FENCE_PARSER

        for index, requirement in enumerate(state.requirements, 1):
            with tracer.start_as_current_span("generate_single_test") as test_span:
                logger.info(f"Generating test {index}/{len(state.requirements)}: {requirement}")
                test_span.set_attribute("requirement", requirement)
                test_span.set_attribute("index", index)
                test_span.set_attribute("framework", state.framework)

                content = generation_chain.invoke(requirement)
                filepath, filename, _folder_name = get_test_filepath(
                    state.framework, state.output_dir, use_prompt_mode, index, requirement
                )

                if state.approve and not preview_and_approve(content, requirement, filepath):
                    logger.info(f"Skipped: {filename}")
                    continue

                with open(filepath, "w") as file:
                    file.write(f"// Requirement: {requirement}\n\n{content}")

                logger.info(f"Saved: {filename}")
                test_span.set_attribute("filepath", filepath)

                store.store_pattern(
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
        cmd = build_run_command(state.framework, state.generated_tests, state.output_dir, use_prompt_mode)

        import os

        logger.info(f"Running: {cmd}")
        span.set_attribute("run_command", cmd)
        exit_code = os.system(cmd)

        state.test_results = {
            "exit_code": exit_code,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat(),
        }
        span.set_attribute("exit_code", exit_code)
        span.set_attribute("success", exit_code == 0)
        logger.info(f"Tests finished with exit code: {exit_code}")
        return state


def should_run_tests(state: TestState) -> str:
    return "run_tests" if state.run_tests else END


def create_workflow() -> Any:
    logger.info("Building workflow")
    workflow = StateGraph(TestState)
    workflow.add_node("step_2", step_2_fetch_test_data)
    workflow.add_node("step_3", step_3_search_similar_patterns)
    workflow.add_node("step_4", step_4_generate_tests)
    workflow.add_node("step_5", step_5_run_tests)
    workflow.set_entry_point("step_2")
    workflow.add_edge("step_2", "step_3")
    workflow.add_edge("step_3", "step_4")
    workflow.add_conditional_edges("step_4", should_run_tests, {"run_tests": "step_5", END: END})
    workflow.add_edge("step_5", END)
    logger.info("Workflow ready")
    return workflow.compile(checkpointer=WORKFLOW_CHECKPOINTER)