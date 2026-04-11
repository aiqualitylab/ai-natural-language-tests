#!/usr/bin/env python3
"""Gradio UI for AI-Powered Cypress, Playwright, and WebdriverIO test generator."""

import argparse
import json
import logging
import queue
import threading
import time
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Generator, List

import gradio as gr

from qa_config import FRAMEWORK_CONFIG
from qa_workflow import TestState, create_workflow


def _split_requirements(requirements_text: str) -> List[str]:
    return [line.strip() for line in requirements_text.splitlines() if line.strip()]


def _cleanup_exports(export_dir: Path, max_keep: int = 25) -> None:
    files = sorted(export_dir.glob("generated_tests_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale_file in files[max_keep:]:
        stale_file.unlink(missing_ok=True)


def _write_export_zip(run_id: str, generated_tests: list, code_output: str) -> Path:
    export_dir = Path("generated_exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    _cleanup_exports(export_dir)

    export_path = export_dir / f"generated_tests_{run_id}.zip"
    with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("combined_generated_tests.txt", code_output)

        summary = {
            "run_id": run_id,
            "generated_tests_count": len(generated_tests),
            "generated_tests": generated_tests,
        }
        archive.writestr("summary.json", json.dumps(summary, indent=2, default=str))

        for item in generated_tests:
            filepath = item.get("filepath", "")
            if not filepath:
                continue
            path = Path(filepath)
            if not path.exists():
                continue
            archive.write(path, arcname=path.as_posix())

    return export_path


class _QueueLogHandler(logging.Handler):
    def __init__(self, out_queue: queue.Queue):
        super().__init__(level=logging.INFO)
        self.out_queue = out_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.out_queue.put(self.format(record))


def _run_generation(
    requirements_text: str,
    framework: str,
    url: str,
) -> Generator[tuple[str, str, str, str | None], None, None]:
    requirements = _split_requirements(requirements_text)
    if not requirements:
        yield json.dumps({"error": "Add at least one requirement (one line per requirement)."}, indent=2), "", "", None
        return

    url_value = url.strip()
    if not url_value:
        yield json.dumps({"error": "URL is mandatory. Enter exactly one URL."}, indent=2), "", "", None
        return

    # Step 2 guardrail: this field accepts one URL value only.
    if len(url_value.split()) > 1 or "," in url_value:
        yield json.dumps({"error": "Enter only one URL in the URL field."}, indent=2), "", "", None
        return

    output_dir = FRAMEWORK_CONFIG.get(framework, {}).get("default_output", "cypress/e2e")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_payload = {
        "message": "Generation started.",
        "framework": framework,
        "url": url_value,
        "run_id": run_id,
    }

    log_queue: queue.Queue[str] = queue.Queue()
    capture_handler = _QueueLogHandler(log_queue)
    capture_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    app_logger = logging.getLogger("ai-natural-language-tests")
    app_logger.addHandler(capture_handler)

    logs_buffer: list[str] = []
    result_holder: dict[str, object] = {}
    error_holder: dict[str, str] = {}

    def _worker() -> None:
        try:
            state = TestState(
                requirements=requirements,
                output_dir=output_dir,
                use_prompt=False,
                approve=False,
                framework=framework,
                url=url_value,
                run_tests=False,
                llm_provider="openai",
                run_id=run_id,
            )

            final_state = create_workflow().invoke(
                state,
                config={"configurable": {"thread_id": run_id}},
            )

            generated_tests = final_state.get("generated_tests", [])
            similar_patterns = final_state.get("similar_patterns", [])

            generated_code_chunks = []
            for item in generated_tests:
                filepath = item.get("filepath", "")
                if not filepath:
                    continue
                path = Path(filepath)
                if not path.exists():
                    continue
                code_text = path.read_text(encoding="utf-8")
                generated_code_chunks.append(f"// FILE: {filepath}\n{code_text}")

            code_output = "\n\n".join(generated_code_chunks)

            export_path = _write_export_zip(run_id, generated_tests, code_output)

            response = {
                "message": "Generation complete.",
                "requirements_count": len(requirements),
                "framework": framework,
                "url": url_value,
                "output_dir": output_dir,
                "run_id": run_id,
                "generated_tests_count": len(generated_tests),
                "similar_patterns_count": len(similar_patterns),
                "generated_tests": generated_tests,
                "test_results": final_state.get("test_results"),
            }

            result_holder["response_json"] = json.dumps(response, indent=2, default=str)
            result_holder["code_output"] = code_output
            result_holder["export_path"] = str(export_path)
        except Exception as exc:
            error_holder["details"] = str(exc)

    worker_thread = threading.Thread(target=_worker, daemon=True)
    worker_thread.start()

    yield json.dumps(start_payload, indent=2), "", "", None

    try:
        while worker_thread.is_alive() or not log_queue.empty():
            while not log_queue.empty():
                logs_buffer.append(log_queue.get_nowait())
            yield json.dumps(start_payload, indent=2), "\n".join(logs_buffer), "", None
            time.sleep(0.2)

        while not log_queue.empty():
            logs_buffer.append(log_queue.get_nowait())

        logs_output = "\n".join(logs_buffer)
        if error_holder:
            error_payload = {
                "error": "Generation failed.",
                "details": error_holder["details"],
            }
            yield json.dumps(error_payload, indent=2), logs_output, "", None
            return

        yield (
            str(result_holder.get("response_json", json.dumps({"error": "No response generated."}, indent=2))),
            logs_output,
            str(result_holder.get("code_output", "")),
            str(result_holder.get("export_path", "")) or None,
        )
    finally:
        app_logger.removeHandler(capture_handler)
        capture_handler.close()


def _analyze_placeholder(log_text: str) -> str:
    if not log_text.strip():
        return json.dumps(
            {
                "message": "Paste log text to continue.",
            },
            indent=2,
        )
    return json.dumps(
        {
            "message": "Analyze placeholder response.",
            "log_length": len(log_text),
        },
        indent=2,
    )


def _build_ui() -> gr.Blocks:
    with gr.Blocks(title="AI Test Generator UI") as app:
        gr.Markdown(
            """
# AI-Powered E2E Test Generation Platform
Translate natural language requirements into production-ready end-to-end tests.

Enterprise-grade platform to generate and execute Cypress, Playwright, and WebdriverIO end-to-end tests from natural language requirements.

© 2026 AI Quality Lab / [Sreekanth Harigovindan](https://www.linkedin.com/in/sreekanthharigovindan/).
https://tests.aiqualitylab.org/
            """
        )

        with gr.Tab("Generate Tests"):
            with gr.Row():
                with gr.Column(scale=1):
                    requirements_text = gr.Textbox(label="Test requirements (one per line)", lines=4)
                    framework = gr.Dropdown(
                        label="Framework",
                        choices=["cypress", "playwright", "webdriverio"],
                        value="cypress",
                    )
                    url = gr.Textbox(label="URL (mandatory, one URL only)", placeholder="https://example.com/login")
                    generate_button = gr.Button("Generate")
                    generate_output = gr.Code(label="Output", language="json")

                with gr.Column(scale=1):
                    generate_logs = gr.Textbox(label="Console Logs (live)", lines=10)
                    generated_test_code = gr.Code(label="Generated Test Code (copy)", language="javascript")
                    generated_code_file = gr.File(label="Generated Test Code File (save/download)")

            generate_button.click(
                _run_generation,
                inputs=[requirements_text, framework, url],
                outputs=[generate_output, generate_logs, generated_test_code, generated_code_file],
            )

        with gr.Tab("Analyze Failure"):
            with gr.Row():
                with gr.Column(scale=1):
                    log_text = gr.Textbox(label="Log Text", lines=12)
                    analyze_button = gr.Button("Analyze")

                with gr.Column(scale=1):
                    analyze_output = gr.Code(label="Output", language="json")

            analyze_button.click(_analyze_placeholder, inputs=[log_text], outputs=[analyze_output])

        with gr.Tab("Settings"):
            gr.Markdown("Configure provider keys here. These fields are masked.")
            openai_key = gr.Textbox(label="OpenAI API Key", type="password", lines=1)
            anthropic_key = gr.Textbox(label="Anthropic API Key", type="password", lines=1)
            google_key = gr.Textbox(label="Google API Key", type="password", lines=1)

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
