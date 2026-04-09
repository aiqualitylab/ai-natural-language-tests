#!/usr/bin/env python3
"""Gradio scaffold for step-by-step development."""

import argparse
import json
from datetime import datetime
from typing import List

import gradio as gr

from qa_workflow import TestState


def _split_requirements(requirements_text: str) -> List[str]:
    return [line.strip() for line in requirements_text.splitlines() if line.strip()]


def _build_state_preview(requirements_text: str, framework: str, url: str) -> str:
    requirements = _split_requirements(requirements_text)
    if not requirements:
        return "Add at least one requirement (one line per requirement)."

    state = TestState(
        requirements=requirements,
        output_dir="cypress/e2e",
        use_prompt=False,
        approve=False,
        framework=framework,
        url=url.strip() or None,
        run_tests=False,
        llm_provider="openai",
        run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
    )

    preview = {
        "requirements_count": len(state.requirements),
        "framework": state.framework,
        "url": state.url,
        "output_dir": state.output_dir,
        "run_id": state.run_id,
        "requirements": state.requirements,
    }
    return json.dumps(preview, indent=2)


def _analyze_placeholder(log_text: str) -> str:
    if not log_text.strip():
        return "Paste log text to continue."
    return "Step 1 scaffold only. Next step will connect this tab to analyze_test_failure()."


def _build_ui() -> gr.Blocks:
    with gr.Blocks(title="AI Test Generator UI") as app:
        gr.Markdown(
            """
# AI-Powered E2E Test Generator
This is a scaffold for a Gradio UI to interact with the AI test generation workflow. It includes two tabs: "Generate Tests" and "Analyze Failure". The "Generate Tests" tab allows you to input test requirements, select a framework, and optionally provide a URL. The "Analyze Failure" tab is a placeholder for future functionality to analyze test failure logs.
            """
        )

        with gr.Accordion("Provider Keys (masked)", open=False):
            openai_key = gr.Textbox(label="OpenAI API Key", type="password", lines=1)
            anthropic_key = gr.Textbox(label="Anthropic API Key", type="password", lines=1)
            google_key = gr.Textbox(label="Google API Key", type="password", lines=1)

        with gr.Tab("Generate Tests"):
            requirements_text = gr.Textbox(label="Test requirements (one per line)", lines=8)
            framework = gr.Dropdown(
                label="Framework",
                choices=["cypress", "playwright", "webdriverio"],
                value="cypress",
            )
            url = gr.Textbox(label="URL")
            generate_button = gr.Button("Generate")
            generate_output = gr.Textbox(label="Output", lines=8)
            generate_button.click(
                _build_state_preview,
                inputs=[requirements_text, framework, url],
                outputs=[generate_output],
            )

        with gr.Tab("Analyze Failure"):
            log_text = gr.Textbox(label="Log Text", lines=10)
            analyze_button = gr.Button("Analyze")
            analyze_output = gr.Textbox(label="Output", lines=4)
            analyze_button.click(_analyze_placeholder, inputs=[log_text], outputs=[analyze_output])

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Gradio scaffold")
    parser.add_argument("--server-name", default="127.0.0.1")
    parser.add_argument("--server-port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    app = _build_ui()
    app.launch(server_name=args.server_name, server_port=args.server_port, share=args.share)


if __name__ == "__main__":
    main()
