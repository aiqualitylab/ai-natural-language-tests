<div align="center">

# AI-Powered E2E Test Generation Platform

> *Describe tests in plain English. AI writes the code.*

Enterprise-grade platform to generate and execute Cypress and Playwright end-to-end tests from natural language requirements.

This project combines LLM-driven generation, LangGraph workflow orchestration, and vector-based pattern learning to improve test authoring speed while maintaining repeatability and CI/CD readiness.

[![CI](https://github.com/aiqualitylab/ai-natural-language-tests/actions/workflows/ci.yml/badge.svg)](https://github.com/aiqualitylab/ai-natural-language-tests/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-003087?logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22-FF9933?logo=node.js&logoColor=white)
![License](https://img.shields.io/badge/License-AGPL%20v3-808080)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-FFD700?logo=openai&logoColor=black)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-FF9933?logoColor=white)
![Google](https://img.shields.io/badge/Google-Gemini-003087?logo=google&logoColor=white)
![Cypress](https://img.shields.io/badge/Cypress-FF9933?logo=cypress&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-003087?logo=playwright&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1A1A1A?logo=langchain&logoColor=FF9933)
![LangGraph](https://img.shields.io/badge/LangGraph-FF9933?logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-003087?logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Apache%202.0-808080?logo=docker&logoColor=white)
![GHCR](https://img.shields.io/badge/GitHub%20Packages-GHCR-181717?logo=github&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-AGPL%20v3-FF9933?logo=grafana&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Apache%202.0-003087?logo=opentelemetry&logoColor=white)
![Loki](https://img.shields.io/badge/Loki-AGPL%20v3-FFD700?logo=grafana&logoColor=black)

</div>

---

## Table of Contents

### Getting Started
- [Overview](#overview)
- [Business Value](#business-value)
- [Core Capabilities](#core-capabilities)

### Platform Design
- [Architecture](#architecture)
- [Workflow](#workflow)
- [Technology Stack](#technology-stack)

### Setup & Configuration
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [GitHub Registry (GHCR)](#github-registry-ghcr)
- [Configuration](#configuration)

### Using the Platform
- [Usage](#usage)
- [CI/CD Integration](#cicd-integration)

### Operations
- [Security and Compliance Guidance](#security-and-compliance-guidance)
- [Troubleshooting](#troubleshooting)

### Project Info
- [Contributing](#contributing)
- [Change Log Highlights](#change-log-highlights)
- [Release History](#release-history)
- [Support](#support)

## Overview

The platform translates natural language requirements into executable E2E tests for:

| Framework | Output | Style |
|-----------|--------|-------|
| Cypress | `.cy.js` | Traditional & prompt-powered |
| Playwright | `.spec.ts` | TypeScript async/await |

It supports both local engineering workflows and automated pipeline execution. The generator uses contextual data from live HTML analysis and historical pattern matching to produce stable, maintainable test assets.

## Business Value

> [!NOTE]
> - Reduces manual test authoring effort and onboarding time.
> - Standardizes generated test structure across teams.
> - Improves reuse through vector-based pattern memory.
> - Supports enterprise delivery with CI/CD and Docker workflows.
> - Enables faster root-cause diagnosis using AI-assisted failure analysis.

## Core Capabilities

| Capability | Detail |
|------------|--------|
| Test Generation | Natural language to executable E2E test generation |
| Orchestration | LangGraph-based multi-step orchestration |
| URL Analysis | Dynamic URL analysis and fixture generation |
| Pattern Memory | Pattern storage and semantic retrieval using ChromaDB |
| LLM Support | Multi-provider: OpenAI, Anthropic, Google |
| Cypress Modes | Traditional mode and Cypress prompt-powered mode |
| Playwright | TypeScript generation |
| Execution | Optional immediate test execution after generation |
| Tracing | OpenTelemetry trace export to Grafana Tempo |
| Logging | Optional log shipping to Grafana Loki |

## Architecture

```mermaid
graph TB
    subgraph "User Input"
        A[Natural Language<br/>Requirements]
        B[URL/HTML Data<br/>--url flag]
        C[JSON Test Data<br/>--data flag]
    end

    subgraph "AI & Workflow Engine"
        D[LangGraph Workflow<br/>5-Step Process]
        E[Multi-Provider LLM<br/>OpenAI / Anthropic / Google]
        F[Vector Store<br/>Pattern Learning<br/>Chroma DB]
    end

    subgraph "Framework Generation"
        G{Cypress Framework}
        H{Playwright Framework}
        I[Cypress Tests<br/>.cy.js files<br/>Traditional & cy.prompt&#40;&#41;]
        J[Playwright Tests<br/>.spec.ts files<br/>TypeScript]
    end

    subgraph "Execution & Analysis"
        K[Cypress Runner<br/>npx cypress run]
        L[Playwright Runner<br/>npx playwright test]
        M[AI Failure Analyzer<br/>--analyze flag<br/>Multi-Provider LLM]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F --> D
    D --> G
    D --> H
    G --> I
    H --> J
    I --> K
    J --> L
    K --> M
    L --> M

    style D fill:#e3f2fd,color:#333333,stroke:#666666
    style E fill:#f3e5f5,color:#333333,stroke:#666666
    style F fill:#fff3e0,color:#333333,stroke:#666666
    style G fill:#c8e6c9,color:#333333,stroke:#666666
    style H fill:#ffcdd2,color:#333333,stroke:#666666
```

<details>
<summary><strong>High-Level Components</strong></summary>

- CLI interface (`qa_automation.py`)
- LangGraph workflow engine
- LLM provider adapters
- HTML analysis and fixture writer
- Vector store pattern manager
- Test file generation and optional execution
- Observability layer (OpenTelemetry + Loki)

</details>

## Workflow

```mermaid
flowchart TD
    A[Start: User Input<br/>Requirements + Framework] --> B[Step 1: Initialize Vector Store<br/>Load/Create Chroma DB<br/>Pattern Database]
    B --> C[Step 2: Fetch Test Data<br/>Analyze URL/HTML<br/>Extract Selectors<br/>Generate Fixtures]
    C --> D[Step 3: Search Similar Patterns<br/>Query Vector Store<br/>Find Matching Test Patterns<br/>From Past Generations]
    D --> E[Step 4: Generate Tests<br/>Use AI + Patterns<br/>Create Framework-Specific Code<br/>Cypress .cy.js or Playwright .spec.ts]
    E --> F[Step 5: Run Tests<br/>Execute via Framework Runner<br/>Optional --run flag]
    F --> G[End: Tests Executed<br/>Ready for CI/CD]

    style A fill:#e1f5fe,color:#333333,stroke:#666666
    style B fill:#fff3e0,color:#333333,stroke:#666666
    style C fill:#c8e6c9,color:#333333,stroke:#666666
    style D fill:#ffcdd2,color:#333333,stroke:#666666
    style E fill:#f3e5f5,color:#333333,stroke:#666666
    style F fill:#e8f5e8,color:#333333,stroke:#666666
    style G fill:#f3e5f5,color:#333333,stroke:#666666
```

Generation follows a deterministic five-step flow:

| Step | Name | Description |
|------|------|-------------|
| 1 | Initialize Vector Store | Load or create the Chroma pattern database |
| 2 | Fetch Test Data | Analyze URL/HTML, extract selectors, generate fixtures |
| 3 | Search Similar Patterns | Query vector store for matching historical patterns |
| 4 | Generate Tests | Use AI + patterns to create framework-specific code |
| 5 | Run Tests | Optionally execute via framework runner (`--run`) |

## Technology Stack

| Layer | Technology |
|-------|------------|
| Orchestration | Python CLI orchestration |
| Workflow | LangChain + LangGraph |
| Vector Store | ChromaDB vector store |
| LLM Backends | OpenAI / Anthropic / Google |
| Test Runners | Cypress and Playwright runners |
| Observability | OpenTelemetry SDK and OTLP exporter |
| Logging | Loki logging handler (optional) |

## Repository Structure

<details>
<summary>View repository tree</summary>

```text
ai-natural-language-tests/
|-- cypress/
|   |-- e2e/
|   |   |-- generated/
|   |   `-- prompt-powered/
|   `-- fixtures/
|-- tests/
|   `-- generated/
|-- prompts/
|-- vector_db/
|-- qa_automation.py
|-- cypress.config.js
|-- playwright.config.ts
|-- package.json
|-- requirements.txt
|-- Dockerfile
|-- docker-compose.yml
`-- README.md
```

</details>

## Prerequisites

| Requirement | Version / Notes |
|-------------|------------------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | latest |
| Git | latest |
| Playwright browsers | `npx playwright install chromium` |

## Installation

<details>
<summary><strong>Local Setup</strong></summary>

```bash
git clone https://github.com/aiqualitylab/ai-natural-language-tests.git
cd ai-natural-language-tests
pip install -r requirements.txt
npm ci
npx playwright install chromium
```

Create `.env`:

```bash
OPENAI_API_KEY=your_key
```

</details>

<details>
<summary><strong>Docker Setup</strong></summary>

```bash
git clone https://github.com/aiqualitylab/ai-natural-language-tests.git
cd ai-natural-language-tests
docker compose build
```

Docker Compose loads `.env` and now explicitly forwards observability variables for Tempo and Loki to the container runtime.

Run in container:

```bash
docker compose run --rm test-generator "Test login" --url https://the-internet.herokuapp.com/login
```

Run with observability enabled:

```bash
docker compose run --rm test-generator \
  "Test login" --url https://the-internet.herokuapp.com/login --framework playwright --run
```

</details>

## GitHub Registry (GHCR)

Pre-built Docker images are published to GitHub Container Registry. No local clone or build required.

| Without GHCR | With GHCR |
|---|---|
| Clone → install → build → run | `docker run` — done |
| Each user builds their own image | One image built once, shared everywhere |
| "Works on my machine" problems | Identical environment for every user |

### Pull and run

```bash
docker pull ghcr.io/aiqualitylab/ai-natural-language-tests:latest

docker run --rm \
  -e OPENAI_API_KEY=your_key \
  ghcr.io/aiqualitylab/ai-natural-language-tests:latest \
  "Test login" --url https://the-internet.herokuapp.com/login
```

### Image tags

| Tag | Use case |
|-----|----------|
| `latest` | Always the most recently published version — use for quick runs |
| `v3.6.1` | Pinned to a specific release — use in CI/CD for reproducibility |

For publishing and release management, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Configuration

<details>
<summary><strong>Core API Keys</strong></summary>

```bash
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

</details>

<details>
<summary><strong>OpenTelemetry (Grafana Tempo)</strong></summary>

```bash
OTEL_PROVIDER=grafana
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-eu-north-0.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64(instance_id:api_token)>
```

</details>

<details>
<summary><strong>Loki Logging (Optional)</strong></summary>

```bash
GRAFANA_LOKI_URL=https://logs-prod-eu-north-0.grafana.net
GRAFANA_INSTANCE_ID=<instance_id>
GRAFANA_API_TOKEN=<logs_write_token>
```

</details>

## Usage

**Quick Reference**

| Mode | Command |
|------|---------|
| Cypress (default) | `python qa_automation.py "requirement" --url <url>` |
| Playwright | `python qa_automation.py "requirement" --url <url> --framework playwright` |
| Prompt-powered Cypress | `python qa_automation.py "requirement" --url <url> --use-prompt` |
| Generate + Execute | `python qa_automation.py "requirement" --url <url> --run` |
| Failure Analysis | `python qa_automation.py --analyze "error message"` |
| Pattern Inventory | `python qa_automation.py --list-patterns` |

**Natural Language Prompt Examples**

| What you type | What AI generates |
|---------------|-------------------|
| `"Test login with valid credentials"` | Login form fill + submit + success assertion |
| `"Test login fails with wrong password"` | Negative test with error message assertion |
| `"Test contact form submission"` | Form field detection + submit + confirmation |
| `"Test search returns results"` | Search input + trigger + results count assertion |
| `"Test signup with missing fields"` | Validation error coverage for required fields |
| `"Test logout clears session"` | Post-login logout + redirect assertion |

> [!TIP]
> **Writing effective AI requirements**
>
> - Be specific about the action: *"Test login"* vs *"Test login with valid credentials and verify dashboard loads"*
> - Mention the expected outcome when it matters: *"...and verify error message appears"*
> - Use `--url` to give the AI real page context — it reads the HTML and picks the right selectors automatically
> - Chain multiple requirements in one run: `"Test login" "Test logout" --url <url>`

### Generate Cypress Test

<details>
<summary>Show command</summary>

```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login
```

</details>

### Generate Playwright Test

<details>
<summary>Show command</summary>

```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework playwright
```

</details>

### Prompt-Powered Cypress Mode

<details>
<summary>Show command</summary>

```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --use-prompt
```

</details>

### Generate and Execute

<details>
<summary>Show command</summary>

```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework playwright --run
```

</details>

### Failure Analysis

<details>
<summary>Show commands</summary>

```bash
python qa_automation.py --analyze "CypressError: Element not found"
python qa_automation.py --analyze -f error.log
```

</details>

> [!NOTE]
> The AI failure analyzer returns a structured diagnosis:
>
> | Field | Description |
> |-------|-------------|
> | `CATEGORY` | Error type: `SELECTOR`, `TIMEOUT`, `ASSERTION`, `NETWORK`, etc. |
> | `REASON` | Root cause explanation in plain English |
> | `FIX` | Suggested code change or configuration fix |

### Pattern Inventory

<details>
<summary>Show command</summary>

```bash
python qa_automation.py --list-patterns
```

</details>

## CI/CD Integration

```mermaid
flowchart TD
    A[Code Changes<br/>Pushed to Repo] --> B[CI/CD Pipeline<br/>Triggers]
    B --> C[Install Dependencies<br/>pip install -r requirements.txt<br/>npm install]
    C --> D[Generate Tests<br/>python qa_automation.py<br/>--url or --data]
    D --> E[Run Tests<br/>npx cypress run<br/>or npx playwright test]
    E --> F{Tests Pass?}
    F -->|Yes| G[Deploy Application<br/>Success]
    F -->|No| H[AI Failure Analysis<br/>--analyze in pipeline]
    H --> I[Auto-Fix & Regenerate<br/>If possible]
    I --> E
    H --> J[Notify Developers<br/>Manual intervention]

    style A fill:#e1f5fe,color:#333333,stroke:#666666
    style B fill:#fff3e0,color:#333333,stroke:#666666
    style C fill:#c8e6c9,color:#333333,stroke:#666666
    style D fill:#ffcdd2,color:#333333,stroke:#666666
    style E fill:#f3e5f5,color:#333333,stroke:#666666
    style G fill:#e8f5e8,color:#333333,stroke:#666666
    style J fill:#ffebee,color:#333333,stroke:#666666
```

Recommended pipeline stages:

| Stage | Action |
|-------|--------|
| 1 | Install Python and Node dependencies |
| 2 | Validate environment variables and secrets injection |
| 3 | Generate tests from requirements |
| 4 | Execute generated tests |
| 5 | Publish artifacts and reports |
| 6 | Export telemetry to observability stack |

## Security and Compliance Guidance

> [!IMPORTANT]
> - Store secrets only in secure secret managers (never commit `.env`).
> - Use scoped API tokens with least-privilege access.
> - Rotate provider keys and Grafana tokens on a fixed cadence.
> - Keep generated tests and reports free of sensitive production data.
> - Apply repository protection rules and mandatory CI checks.

## Troubleshooting

> [!WARNING]
> **Traces Not Visible in Grafana Tempo**
>
> - Verify OTLP endpoint region and datasource selection.
> - Verify `Authorization=Basic <base64(instance_id:api_token)>` format.
> - Query with:
>
> ```traceql
> {resource.service.name="ai-natural-language-tests"}
> ```

> [!NOTE]
> **Loki Authentication Errors**
>
> - Ensure token has `logs:write` scope.
> - Confirm instance ID and logs endpoint match the same Grafana stack.

> [!TIP]
> **Docker Observability Validation**
>
> - Confirm `.env` includes OTLP and Loki keys before `docker compose run`.
> - Use `docker compose config` to verify environment interpolation.
> - In Grafana Explore, query Tempo with `service.name="ai-natural-language-tests"`.
> - In Grafana Loki, query labels: `{service_name="ai-natural-language-tests"}`.

## Contributing

Contribution standards, branch conventions, commit format, and review expectations are documented in `CONTRIBUTING.md`.

> [!TIP]
> **Playwright Runtime Issues**
>
> - Install required browser runtime.
> - Retry with generated single-spec command from logs.

## Change Log Highlights

<details>
<summary><strong>v3.6.1</strong> — Docker runtime compatibility update</summary>

- Switched Docker base image from Python 3.14 to Python 3.12 for ChromaDB/Pydantic compatibility.
- Prepared GHCR release examples and compose tags for `v3.6.1`.

</details>

<details>
<summary><strong>v3.6</strong> — Licensing clarity and release alignment</summary>

- Updated Docker Compose image tag to `v3.6`.
- Added explicit project authorship notice (`NOTICE`).
- Added AGPL SPDX/copyright header to `qa_automation.py`.
- Added explicit documentation copyright and CC BY 4.0 note in README footer.

</details>

<details>
<summary><strong>v3.5</strong> — Grafana observability updates</summary>

- Grafana observability updates for both Tempo traces and optional Loki logs.
- Docker Compose now forwards observability environment variables explicitly.
- Enterprise documentation updates, including `CONTRIBUTING.md`.

</details>

<details>
<summary><strong>v3.4</strong> — Accessible HTML analysis and normalized fixture schema</summary>

- Accessible-locator-first HTML analysis.
- Normalized selector schema: `{ cypress, playwright, fallback_css }`.
- Stable test case shape: `test_cases[*].field_name`.
- Resilience backfills for missing selector/test fields.
- Docker fixture persistence improvements.

</details>

<details>
<summary><strong>v3.3</strong> — Multi-provider LLM support</summary>

- Multi-provider LLM support.
- Default OpenAI flow with graceful fallback behavior.

</details>

<details>
<summary><strong>v3.2</strong> — Docker and Docker Compose support</summary>

- Docker and Docker Compose support.
- Portable, zero-local-install workflow option.

</details>

<details>
<summary><strong>v3.1</strong> — Playwright framework support</summary>

- Playwright framework support.
- Framework-aware generation architecture.

</details>

## Release History

| Version | Highlights |
|---------|------------|
| **v3.6.1** | Docker runtime compatibility update and release tag alignment |
| **v3.6** | Licensing clarity updates and Docker release alignment |
| **v3.5** | Grafana observability and Docker environment propagation updates |
| **v3.4** | Accessible HTML analysis and normalized fixture schema |
| **v3.3** | Multi-provider LLM support |
| **v3.2** | Docker support |
| **v3.1** | Playwright support |
| **v3.0** | LangGraph workflows and vector pattern learning |
| **v2.2** | Dynamic test generation |
| **v2.1** | AI failure analyzer |
| **v2.0** | Cypress prompt-powered mode |

---

<div align="center">

## Support

Documentation updates and issues: repository Issues tab

External writing: [Let's Automate](https://aiqualityengineer.com/)

---

*Built with AI. Tested by AI. Ready for CI.*

© 2026 AI Quality Lab / Sreekanth Harigovindan.
Documentation licensed under CC BY 4.0.

</div>
