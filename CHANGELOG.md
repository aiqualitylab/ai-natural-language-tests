# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2026-05-02
### Added
- **Scoring in NLP Baseline**: `ragas_nlp_evaluator.py` now computes ROUGE and NonLLMStringSimilarity; overall average is the mean of all metrics.
- **Overall Quality Score**: `ragas_evaluator.py` now computes and prints an `Overall Score` (mean of all four Ragas metrics) with pass/fail status per evaluation run.

### Changed
- **Python 3.12 in CI**: Both `nlp-baseline` and `test` jobs upgraded from Python 3.11 to Python 3.12 to match the Dockerfile base image.
- **CI Dependency Caching**: Added `actions/cache@v4` for pip (per-framework keyed on `requirements.txt`) and npm (keyed on `package-lock.json`) to reduce install times.
- **Release Metadata Versioning**: Bumped from `4.2.0`/`v4.2.0` to `5.0.0`/`v5.0.0` across:
  - `package.json` and root `package-lock.json`
  - `agent.yaml`
  - `Dockerfile` (`ARG RELEASE_TAG`)
  - `docker-compose.yml` (image tags and build context)
  - `README.md` (pinned release tag table)
  - `CONTRIBUTING.md` (publish examples and tag conventions)
  - `.github/workflows/publish-ghcr.yml` (tag comment)


### Added
- **HITL (Human-In-The-Loop) Approval Flow**: New `--approve` flag to insert manual approval checkpoint during generated test save, enabling QA engineers to review and validate tests before persistence.
- **HTML Replay Utilities**: 
  - `--list-html-replays`: List all stored HTML analysis replay snapshots with metadata.
  - `--replay-html-analysis <run_id>`: Replay and re-analyze a specific HTML snapshot run for debugging and root cause analysis.
- **Replay Persistence Layer**: HTML analysis debug snapshots automatically stored under `vector_db/html_analysis_debug/` for audit trails and failure investigation.
- **Reusable Release Execution Playbook**: `docs/releases/release-playbook-4.2.0.md` as a standardized checklist and guide for repeatable, low-error release processes.

### Changed
- **Modular Architecture Refactor** - Separated single-file runtime into specialized modules:
  - `qa_automation.py`: CLI entrypoint and command routing only.
  - `qa_config.py`: Configuration loading, prompt spec YAML parsing, and LLM model initialization.
  - `qa_runtime.py`: Runtime services (logging, distributed tracing, vector storage, replay management).
  - `qa_workflow.py`: LangGraph workflow definition, state machine, and node implementations.
  - **Benefit**: Clearer separation of concerns, easier testing, improved code maintainability.
- **Orchestration vs Business Logic**: LangGraph remains the orchestration layer; business logic moved into dedicated service modules for better reusability.
- **Release Metadata Versioning**: Bumped from `4.0.0`/`v4.0.0` to `4.2.0`/`v4.2.0` across:
  - `package.json` and root `package-lock.json`
  - `agent.yaml` (agent version and tag references)
  - `Dockerfile` (`ARG RELEASE_TAG`)
  - `docker-compose.yml` (image tags and build context)
  - `README.md` (pinned release tag table for users)
  - `CONTRIBUTING.md` (publish examples and tag conventions)
  - GitHub Actions workflow files (publisher tags and GHCR references)
- **Updated Release Documentation**: All examples now reference `v4.2.0` for tag pinning guidance and reproducible deployments.
- **Simplified Implementation Paths**: Refactored logic for readability without changing end-user behavior or API contracts.

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
