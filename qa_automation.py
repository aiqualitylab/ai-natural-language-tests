#!/usr/bin/env python3
# Copyright (c) 2024-2026 Sreekanth Harigovindan / AI Quality Lab
# SPDX-License-Identifier: AGPL-3.0-or-later

"""AI-Powered Cypress, Playwright, WebdriverIO, and Appium test generator."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from langchain_core.runnables import RunnableLambda
from qa_config import DEFAULT_LLM, FRAMEWORK_CONFIG, LLM_CONFIG
from qa_runtime import (
    _otel_provider,
    analyze_test_failure,
    get_pattern_store,
    list_html_replay_ids,
    load_html_analysis_debug,
    logger,
    tracer,
)
from qa_workflow import TestState, create_workflow


WORKFLOW_INVOKER = RunnableLambda(
    lambda payload: create_workflow().invoke(
        payload["state"],
        config={"configurable": {"thread_id": payload["thread_id"]}},
    )
)


READ_TEXT = RunnableLambda(lambda path: Path(path).read_text(encoding="utf-8"))


def list_all_patterns() -> None:
    logger.info("Listing all patterns")
    patterns = get_pattern_store().get_all_patterns()
    logger.info(f"Total patterns: {len(patterns)}")
    for i, pattern in enumerate(patterns, 1):
        logger.info(f"Pattern {i}: {pattern.metadata.get('requirement', 'N/A')}")
        logger.info(f"  Type: {pattern.metadata.get('test_type', 'N/A')}")
        logger.info(f"  Preview: {pattern.page_content[:100]}...")


def replay_html_analysis_action(args: argparse.Namespace) -> None:
    try:
        data = load_html_analysis_debug(args.replay_html_analysis)
        print(f"Run: {args.replay_html_analysis}")
        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"URL: {data.get('url', 'N/A')}")
        print("\nFetched HTML (full snapshot):\n")
        print(str(data.get("html_sample", "")))
    except FileNotFoundError as e:
        logger.error(str(e))


def list_html_replays_action() -> None:
    run_ids = list_html_replay_ids()
    if not run_ids:
        logger.info("No HTML replay snapshots found.")
        return

    logger.info(f"HTML replay snapshots: {len(run_ids)}")
    for run_id in run_ids:
        logger.info(run_id)


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
            approve=args.approve,
            framework=args.framework,
            url=args.url,
            run_tests=args.run,
            llm_provider=args.llm,
            run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )

        final_state = WORKFLOW_INVOKER.invoke({"state": state, "thread_id": state.run_id})

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


def dispatch_cli_mode(args: argparse.Namespace) -> None:
    if args.list_html_replays:
        list_html_replays_action()
        return

    if args.replay_html_analysis:
        replay_html_analysis_action(args)
        return

    if args.analyze is not None or args.file:
        log_text = READ_TEXT.invoke(args.file) if args.file else args.analyze or sys.stdin.read()
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
    logger.info("AI-Powered Test Generator (Cypress, Playwright, WebdriverIO, and Appium)")
    logger.info("With LangGraph Workflows and Vector Store Learning")

    parser = argparse.ArgumentParser(
        description="AI Test Generator — Cypress, Playwright, WebdriverIO, and Appium",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework playwright
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework webdriverio
    python qa_automation.py "Test login" --framework appium --use-prompt
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --use-prompt
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --run
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --llm anthropic
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --llm ollama
    python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --llm local-openai
  python qa_automation.py --analyze "CypressError: Element not found"
  python qa_automation.py --analyze -f error.log
  python qa_automation.py --list-patterns
  python qa_automation.py --list-html-replays
""",
    )
    parser.add_argument("requirements", nargs="*", help="Test requirements in natural language")
    parser.add_argument(
        "--framework",
        "-fw",
        choices=["cypress", "playwright", "webdriverio", "appium"],
        default="cypress",
    )
    parser.add_argument("--url", "-u")
    parser.add_argument("--out", default="cypress/e2e")
    parser.add_argument("--use-prompt", action="store_true")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--llm", choices=list(LLM_CONFIG.keys()), default=DEFAULT_LLM)
    parser.add_argument("--analyze", "-a", nargs="?", const="")
    parser.add_argument("--file", "-f")
    parser.add_argument("--list-patterns", action="store_true")
    parser.add_argument("--list-html-replays", action="store_true", help="List saved HTML replay run ids")
    parser.add_argument("--replay-html-analysis", help="Replay HTML analysis for a run id")

    args = parser.parse_args()
    dispatch_cli_mode(args)


if __name__ == "__main__":
    main()