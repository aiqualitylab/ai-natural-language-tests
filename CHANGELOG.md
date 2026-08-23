# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.0.0] - 2026-08-23
### Added
- **Local LLM Support (Privacy-First):** Added support for local LLM providers enabling offline test generation without sending HTML to external APIs:
  - **Ollama** (`--llm ollama`): Local open-source models via Ollama server (Llama 2, Mistral, etc.)
  - **Local OpenAI-Compatible** (`--llm local-openai`): vLLM, LM Studio, and other OpenAI-compatible servers
  - Environment variables: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `LOCAL_OPENAI_BASE_URL`, `LOCAL_OPENAI_MODEL`
  - Reduces latency and cost; enables enterprise deployment in air-gapped environments
- **Conversational Test Refinement UI:** Interactive, multi-turn natural language refinement interface within web UI
  - Panel-based UI: code editor + instruction input + refined output
  - Safety rules: file integrity checks, no empty sections, disk-only writes, error recovery
  - Zero heavy dependencies in refinement module
- **AI-Powered Test Code Review:** New test quality review capability across four dimensions:
  - **Assertions**: Sufficient coverage and semantic correctness
  - **Selectors**: Robust, maintainable, resilient to layout changes
  - **Structure**: Logical organization, proper setup/teardown, readable test names
  - **Determinism**: Avoiding flaky patterns (hardcoded waits, race conditions, etc.)
  - Integrated into `qa_refinement.py` with concrete issue detection
- **Collapsible UI Sections:** Enhanced API configuration and failure analysis display with expandable sections
- **Suggested Refinement Textbox:** New refinement suggestion input field in review UI for guided test improvements
- **Unit Test Suite:** Added comprehensive 23-test suite validating core logic:
  - Framework selection logic
  - Parser implementations
  - Selector path resolution
  - Scoring mechanisms
  - ~10s execution time with zero external API dependencies
- **CI/CD Test Workflow:** New `test` job in GitHub Actions running Python 3.12 with pytest and dependency caching

### Changed
- **LLM Provider Selection**: `--llm` flag now supports: `openai`, `anthropic`, `google`, `ollama`, `local-openai` (default: `openai`)
- **Model Configuration**: LLM provider initialization refactored for extensibility with `ChatOllama` and `ChatOpenAI` local endpoint support
- **Workflow Diagrams:** Updated README architecture diagrams to highlight local LLM provider support
- **Dependency Updates:**
  - Cypress upgraded to v15.21.0
  - Playwright upgraded to v1.62.1
  - Sentence-transformers updated to v6
  - FAISS-CPU updated to v1.15.0
  - pytest upgraded to v9
  - All development dependencies updated via Renovate

### Fixed
- **UI Rendering**: Collapsible sections now properly toggle state during API configuration and failure analysis display
- **Model Initialization**: Fixed fallback logic for local providers when API keys are unavailable

### Documentation
- Added comprehensive Local LLM Provider Guide with setup instructions for Ollama, vLLM, and LM Studio
- Updated README with local provider environment variable table
- Documented privacy-first deployment architecture (no HTML sent to cloud APIs)
- Updated CLI reference with all LLM provider options and model names
- Added conversational refinement usage examples and safety rule documentation

### Dependencies
- Added `langchain-community` integration for Ollama and local OpenAI-compatible endpoints
- All workflow versions pinned to v6.0.0 in GitHub Actions and CI/CD configurations

## [5.1.0] - 2026-06-23
### Added
- **Appium Mobile Support (Experimental):** WebdriverIO-based test generation for Android and iOS with prompt-powered self-healing
  - Android (default, UiAutomator2) and iOS (XCUITest via `APP_PLATFORM=ios`)
  - Dedicated folder structure: `webdriverio/tests/appium-tests/` for Appium tests
  - Shared WDIO configuration base (`wdio.shared.conf.js`) for desktop and mobile runners

### Changed
- **Appium Test Output Folder:** Tests generated with `--framework appium --use-prompt` now output to `webdriverio/tests/appium-tests/` (instead of `prompt-powered`)
- **WDIO Spec Pattern:** Updated shared config to include `appium-tests` in test discovery glob
- Updated README with Appium setup prerequisites, environment variables, and emulator creation guide

### Documentation
- Added Appium section to README with Experimental status warnings and infrastructure requirements
- Documented Android/iOS device setup and Appium server configuration
- Updated CLI reference table with Appium commands and modes

## [5.0.0] - 2026-05-03
### Added
- **Scoring in NLP Baseline**: `ragas_nlp_evaluator.py` now computes ROUGE and NonLLMStringSimilarity; overall average is the mean of all metrics.
- **Overall Quality Score**: `ragas_evaluator.py` now computes and prints an `Overall Score` (mean of all four Ragas metrics) with pass/fail status per evaluation run.
- **LangChain Parser Layer**: Introduced parser classes for structured output handling:
  - `CodeFenceParser` in `qa_workflow.py`
  - `JsonFenceParser` and `FailureAnalysisParser` in `qa_runtime.py`
- **Runnable Wrappers**: Added `RunnableLambda` wrappers in CLI/UI and workflow generation paths to simplify orchestration boundaries.

### Changed
- **Python 3.12 in CI**: Both `nlp-baseline` and `test` jobs upgraded from Python 3.11 to Python 3.12 to match the Dockerfile base image.
- **CI Dependency Caching**: Added `actions/cache@v4` for pip (per-framework keyed on `requirements.txt`) and npm (keyed on `package-lock.json`) to reduce install times.
- **Prompt Rendering Path**: Prompt formatting now uses LangChain `PromptTemplate` in configuration loading.
- **Failure Analysis Messaging**: Runtime now sends analysis prompts using LangChain message classes (`SystemMessage`, `HumanMessage`).
- **Evaluator Prompt Flow**: `ragas_evaluator.py` now uses `ChatPromptTemplate` and `StrOutputParser` chains for generated answer and ground-truth synthesis.
- **Release Metadata Versioning**: Bumped from `4.2.0`/`v4.2.0` to `5.0.0`/`v5.0.0` across:
  - `package.json` and root `package-lock.json`
  - `agent.yaml`
  - `Dockerfile` (`ARG RELEASE_TAG`)
  - `docker-compose.yml` (image tags and build context)
  - `README.md` (pinned release tag table)
  - `CONTRIBUTING.md` (publish examples and tag conventions)
  - `.github/workflows/publish-ghcr.yml` (tag comment)

### Fixed
- **Loki Non-Blocking Behavior**: Added safe Loki handler behavior that suppresses transient 5xx transport traceback noise and keeps generation flow uninterrupted.
- **Embeddings Deprecation Path**: Prefer `langchain_huggingface.HuggingFaceEmbeddings` with fallback to `langchain_community` to reduce deprecation warnings.


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
