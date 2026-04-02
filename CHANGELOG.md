# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.1.0] - 2026-04-02
### Added
- Added HITL (human-in-the-loop) approval checkpoint during generated test save flow using `--approve`.
- Added HTML replay utilities:
	- `--list-html-replays`
	- `--replay-html-analysis <run_id>`
- Added replay snapshot persistence under `vector_db/html_analysis_debug/`.

### Changed
- Refactored from single-file runtime into a modular architecture:
	- `qa_automation.py` (CLI entrypoint)
	- `qa_config.py` (configuration and prompt/model loading)
	- `qa_runtime.py` (runtime services: logging, tracing, storage, replay)
	- `qa_workflow.py` (LangGraph workflow/state/nodes)
- Updated workflow implementation to keep orchestration in LangGraph and business logic in service modules.
- Simplified implementation paths for readability while preserving behavior.

## [4.0.0] - 2026-03-28
### Changed
- **BREAKING**: Migrated from ChromaDB to FAISS + SQLite for vector storage.
- **BREAKING**: Switched embeddings from OpenAI to local sentence-transformers (all-MiniLM-L6-v2).
- Updated dependencies: replaced `chromadb` and `langchain-chroma` with `faiss-cpu` and `langchain-community`.
- Updated architecture diagrams to reflect FAISS + SQLite vector store.
- Improved memory efficiency with local embeddings (no API calls required for pattern search).

## [3.9.0] - 2026-03-26
### Changed
- Migrated prompt templates from `prompts/*.txt` to `prompt_specs/*.yaml`.
- Updated generation and failure-analysis flows to load prompt specs from YAML.
- Aligned runtime and release tag references to `v3.9.0`.

## [3.8.0] - 2026-03-26
### Added
- Added WebdriverIO `.spec.js` generation with Mocha runner support and Jest-like expectations.
- Added `wdio.conf.js`, Docker/CI/runtime wiring, and generated output path support for WebdriverIO.

### Changed
- Bumped version references to `v3.8.0` across release-tagged files.

## [3.6.2] - 2026-03-26
### Changed
- Bumped version references to `v3.6.2` across `Dockerfile`, `docker-compose.yml`, `package.json`, `package-lock.json`, `CONTRIBUTING.md`, and workflow files.
- Prepared GHCR release examples and compose tags for `v3.6.2`.

## [3.6.1] - 2026-03-26
### Changed
- Switched Docker base image from Python 3.14 to Python 3.12 for ChromaDB/Pydantic compatibility.
- Prepared GHCR release examples and compose tags for `v3.6.1`.

## [3.6.0] - 2026-03-26
### Added
- Added explicit project authorship notice (`NOTICE`).
- Added AGPL SPDX/copyright header to `qa_automation.py`.
- Added explicit documentation copyright and CC BY 4.0 note in README footer.

### Changed
- Updated Docker Compose image tag to `v3.6`.

## [3.5.0] - 2026-03-26
### Added
- Added Grafana observability updates for both Tempo traces and optional Loki logs.

### Changed
- Docker Compose now forwards observability environment variables explicitly.
- Updated enterprise documentation, including `CONTRIBUTING.md`.

## [3.4.0] - 2026-03-26
### Added
- Added accessible-locator-first HTML analysis.
- Added normalized selector schema: `{ cypress, playwright, fallback_css }`.
- Added stable test case shape: `test_cases[*].field_name`.
- Added resilience backfills for missing selector/test fields.
- Added Docker fixture persistence improvements.

## [3.3.0] - 2026-03-26
### Added
- Added multi-provider LLM support.

### Changed
- Set default OpenAI flow with graceful fallback behavior.

## [3.2.0] - 2026-03-26
### Added
- Added Docker and Docker Compose support.
- Added portable, zero-local-install workflow option.

## [3.1.0] - 2026-03-26
### Added
- Added Playwright framework support.
- Added framework-aware generation architecture.

## [3.0.0] - 2026-03-26
### Added
- Added LangGraph workflows and vector pattern learning.

## [2.2.0] - 2026-03-26
### Added
- Added dynamic test generation.

## [2.1.0] - 2026-03-26
### Added
- Added AI failure analyzer.

## [2.0.0] - 2026-03-26
### Added
- Added Cypress prompt-powered mode.
