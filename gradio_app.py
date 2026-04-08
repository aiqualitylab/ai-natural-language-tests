#!/usr/bin/env python3
"""Gradio scaffold for step-by-step development."""

import argparse

import gradio as gr


def _generate_placeholder(requirements_text: str, framework: str, url: str) -> str:
    line_count = len([line for line in requirements_text.splitlines() if line.strip()])
    url_value = url.strip() or "(no url)"
    return (
        "Step 1 scaffold only.\n"
        f"Requirements lines: {line_count}\n"
        f"Framework: {framework}\n"
        f"URL: {url_value}\n"
        "Next step will connect this button to qa_workflow.create_workflow()."
    )


def _analyze_placeholder(log_text: str) -> str:
    if not log_text.strip():
        return "Paste log text to continue."
    return "Step 1 scaffold only. Next step will connect this tab to analyze_test_failure()."


def _build_ui() -> gr.Blocks:
    with gr.Blocks(title="AI Test Generator UI - Step 1") as app:
        gr.Markdown(
            """
# AI-Powered E2E Test Generator (Step 1)

This is the basic UI structure only.
- Keys are masked.
- Actions are placeholders.
- Backend wiring comes in the next commits.
            """
        )

        with gr.Accordion("Provider Keys (masked)", open=False):
            gr.Textbox(label="OpenAI API Key", type="password", lines=1)
            gr.Textbox(label="Anthropic API Key", type="password", lines=1)
            gr.Textbox(label="Google API Key", type="password", lines=1)

        with gr.Tab("Generate Tests"):
            requirements_text = gr.Textbox(label="Requirements (one per line)", lines=8)
            framework = gr.Dropdown(
                label="Framework",
                choices=["cypress", "playwright", "webdriverio"],
                value="cypress",
            )
            url = gr.Textbox(label="URL (optional)")
            generate_button = gr.Button("Generate")
            generate_output = gr.Textbox(label="Output", lines=8)
            generate_button.click(
                _generate_placeholder,
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
