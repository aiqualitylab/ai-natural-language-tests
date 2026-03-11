# AI-Powered E2E Test Generation from Natural Language

An AI-powered tool that generates **[Cypress](https://www.cypress.io/)** and **[Playwright](https://playwright.dev/)** end-to-end tests from natural language requirements using [OpenAI](https://platform.openai.com/docs/) GPT-4, [LangChain](https://python.langchain.com/docs/introduction/), [LangGraph](https://langchain-ai.github.io/langgraph/) workflows, and [ChromaDB](https://docs.trychroma.com/) vector store pattern learning.

[![CI](https://github.com/aiqualitylab/ai-natural-language-tests/actions/workflows/ci.yml/badge.svg)](https://github.com/aiqualitylab/ai-natural-language-tests/actions/workflows/ci.yml)

## Workflow Overview

<p align="center">
  <img src=".github/images/complete-workflow.png" alt="Complete End-to-End Workflow" width="700"/>
</p>

Supports local development and CI/CD pipelines.

---

## Architecture

<p align="center">
  <img src=".github/images/architecture.png" alt="System Architecture" width="600"/>
</p>

---

## New in v3.3 — Multi-Provider LLM Support

- 🤖 **3 LLM Providers**: OpenAI (ChatGPT), Anthropic (Claude), Google (Gemini)
- ⚡ **ChatGPT Default**: No flag needed, uses `gpt-4o-mini` by default
- 🔄 **Graceful Fallback**: Missing providers automatically fall back to OpenAI
- 🆕 **Simple CLI**: Just add `--llm openai|anthropic|google`
- 📦 **Optional Packages**: Install only providers you need

## New in v3.4 — Accessible HTML Analysis + Normalized Fixture Schema

- ♿ **Accessible Locators First**: HTML analysis now prioritizes role/label/placeholder/test-id selectors
- 🧱 **Normalized Selectors**: Each selector is stored as `{ cypress, playwright, fallback_css }`
- 🔁 **Stable Test Data Shape**: Test inputs are normalized under `test_cases[*].field_name`
- 🛡️ **Backfill Defaults**: Missing selector entries and test values are auto-completed for resilience
- 🐳 **Docker Fixture Persistence**: `cypress/fixtures/` is now mounted in Compose runs

### Previous Approach vs v3.4

Previous approach (before v3.4):
- HTML analysis mostly returned CSS-first selectors (for example `#id`, `.class`, `input[name='...']`)
- Selector entries were often plain strings, not a structured cross-framework object
- Test case values could vary in shape (flat fields vs nested data), which caused generator inconsistency
- Dynamic URL coverage worked for many sites, but schema drift could break generated tests on some pages

Current approach (v3.4):
- Accessible-locator-first extraction (role, label, placeholder, test-id, text), with CSS fallback retained
- Unified selector schema per field: `{ cypress, playwright, fallback_css }`
- Unified test case payload shape: `test_cases[*].field_name`
- Automatic normalization/backfill for missing `submit`, `error_container`, `success_container`, and missing field values
- Better generator compatibility across Cypress and Playwright through one normalized fixture contract

### Dynamic URL Behavior and Failure Handling

Expected behavior:
- With `--url`, the tool should work across dynamic websites by analyzing live HTML and producing normalized fixture data.

If failures still happen:
- Common failure modes from earlier versions (incomplete selectors, mixed test-case shapes, missing containers) are already fixed by normalization and defaults in `qa_automation.py`.
- The generator now supports both legacy and new fixture formats for backward compatibility.
- For site-specific runtime issues (DOM changes, delayed rendering, anti-bot behavior), re-run generation and use failure analysis:

```bash
python qa_automation.py --analyze "<test failure message>"
```

- If needed, update the generated fixture at `cypress/fixtures/url_test_data.json` and regenerate.

## New in v3.2 — Docker Support

- 🐳 **Docker Compose**: Single command to build and run — no local Python or Node.js needed
- 📦 **Tagged Images**: `docker compose build` creates `ai-natural-language-tests:v3.4`
- 🔒 **Secrets Safe**: API keys injected at runtime, never baked into the image
- 💾 **Persistent Patterns**: Vector store mounted as volume, patterns survive across runs

## New in v3.1 — Playwright Support

- 🎭 **Multi-Framework**: Generate tests for Cypress (JavaScript) or Playwright (TypeScript) with `--framework`
- 🧠 **Smart Prompt**: Playwright prompt covers all Playwright methods — locators, actions, assertions, network interception, dialogs, multi-tab, and more
- 🔒 **Cypress Unchanged**: Default is still `cypress`. All existing commands work as before
- ⚠️ **cy.prompt() is Cypress-only**: `--use-prompt` is ignored with a warning when used with `--framework playwright`

### Framework Comparison

| | Cypress | Playwright |
|---|---|---|
| Language | JavaScript (`.cy.js`) | TypeScript (`.spec.ts`) |
| Output directory | `cypress/e2e/generated/` | `tests/generated/` |
| cy.prompt() support | ✅ Yes | ❌ No |
| Run command | `npx cypress run` | `npx playwright test` |
| Prompt file | `test_generation_traditional.txt` | `test_generation_playwright.txt` |

---

### LangGraph Workflow

<p align="center">
  <img src=".github/images/langgraph-workflow.png" alt="5-Step LangGraph Workflow" width="500"/>
</p>

Five workflow steps:
1. Initialize Vector Store - Create pattern database
2. Fetch Test Data - Pull HTML and extract selectors  
3. Search Similar Patterns - Query past test patterns
4. Generate Tests - Build test with AI and patterns
5. Run Tests - Execute via Cypress or Playwright (optional)

### Pattern Learning

- Saves test patterns to vector database
- Finds similar patterns from history
- Applies past patterns during generation
- Builds pattern library over time

---

## Example Flow

### Initial Test
```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login
```
Steps:
1. Create vector store
2. Fetch page HTML
3. No patterns available
4. Generate fresh test
5. Save pattern

### Using Patterns
```bash
python qa_automation.py "Test user authentication" --url https://the-internet.herokuapp.com/login
```
Steps:
1. Load vector store
2. Fetch page HTML
3. Find matching patterns
4. Generate test with pattern context
5. Save new pattern

---

## Development Flow

<p align="center">
  <img src=".github/images/local-flow.png" alt="Local Development Flow" width="400"/>
</p>

---

## Failure Analysis

<p align="center">
  <img src=".github/images/Analyzer.png" alt="AI Failure Analyzer Flow" width="400"/>
</p>

```bash
# Direct analysis
python qa_automation.py --analyze "CypressError: Element not found"

# From log file
python qa_automation.py --analyze -f error.log
```

<p align="center">
  <img src=".github/images/Analysis.png" alt="Failure Analysis Process" width="600"/>
</p>

---

## CI/CD Integration

<p align="center">
  <img src=".github/images/cicd-pipeline.png" alt="CI/CD Pipeline Integration" width="500"/>
</p>

---

## Capabilities

- LangGraph workflow engine
- Vector-based pattern storage
- Semantic pattern matching
- Natural language to test code
- URL-based test generation
- AI-powered failure diagnosis with 3 LLM providers
- Traditional and cy.prompt() modes (Cypress)
- Playwright TypeScript test generation
- Multi-framework support via `FRAMEWORK_CONFIG`
- Pattern library management
- **Multi-provider LLM support**: OpenAI, Anthropic, Google
- Docker support for zero-install usage

---

## Setup

### Local Setup

```bash
git clone https://github.com/aiqualitylab/ai-natural-language-tests.git
cd ai-natural-language-tests

pip install -r requirements.txt

echo "OPENAI_API_KEY=sk-your-key" > .env

# Install all Node dependencies from package-lock.json
npm ci

# Install Playwright browser runtime
npx playwright install chromium
```

### Docker Setup

No local Python or Node.js required — only [Docker](https://docs.docker.com/get-docker/) (Docker Compose is included with Docker Desktop).

**Step 1** — Clone and create `.env`

```bash
git clone https://github.com/aiqualitylab/ai-natural-language-tests.git
cd ai-natural-language-tests
echo "OPENAI_API_KEY=sk-your-key" > .env
```

**Step 2** — Build the image

```bash
docker compose build
```

Note: Docker does not need a separate `npm install @testing-library/cypress --save-dev` step.
The image uses `npm ci --include=dev`, so all dependencies from `package-lock.json`
(including `@testing-library/cypress`) are installed automatically.

**Step 3** — Generate tests

```bash
# Cypress test (default)
docker compose run --rm test-generator \
  "Test login" --url https://the-internet.herokuapp.com/login

# Playwright test
docker compose run --rm test-generator \
  "Test login" --url https://the-internet.herokuapp.com/login --framework playwright

# cy.prompt() test (Cypress only)
docker compose run --rm test-generator \
  "Test login" --url https://the-internet.herokuapp.com/login --use-prompt

# Multiple requirements
docker compose run --rm test-generator \
  "Test successful login with valid credentials" \
  "Test login failure with invalid password" \
  "Test login form validation for empty fields" \
  --url https://the-internet.herokuapp.com/login --framework playwright

# Failure analysis
docker compose run --rm test-generator \
  --analyze "CypressError: Element not found"

# List stored patterns
docker compose run --rm test-generator --list-patterns
```

Generated tests appear in the same output directories as local setup. Pattern learning persists across runs via volume mounts.

| Volume Mount                  | Purpose                              |
|-------------------------------|--------------------------------------|
| `cypress/e2e/generated/`     | Generated Cypress standard tests      |
| `cypress/e2e/prompt-powered/`| Generated cy.prompt() tests           |
| `cypress/fixtures/`          | Latest normalized HTML analysis fixture(s) |
| `tests/generated/`           | Generated Playwright tests            |
| `vector_db/`                 | ChromaDB pattern store persists here  |

### HTML Analysis Output Schema (v3.4)

`--url` analysis now writes normalized fixture data to `cypress/fixtures/url_test_data.json`.

```json
{
  "url": "https://example.com/login",
  "page_type": "login",
  "selectors": {
    "username": {
      "cypress": "cy.findByLabelText(/username/i)",
      "playwright": "page.getByLabel('Username')",
      "fallback_css": "input[name='username']"
    },
    "submit": {
      "cypress": "cy.findByRole('button', {name: /login/i})",
      "playwright": "page.getByRole('button', {name: 'Login'})",
      "fallback_css": "button[type='submit']"
    }
  },
  "element_types": {
    "username": "text",
    "password": "password"
  },
  "test_cases": [
    {
      "name": "valid_test",
      "description": "Test with valid data",
      "field_name": {
        "username": "tomsmith",
        "password": "SuperSecretPassword!"
      },
      "expected": "success"
    },
    {
      "name": "invalid_test",
      "description": "Test with invalid data",
      "field_name": {
        "username": "invalidUser",
        "password": "wrongPassword"
      },
      "expected": "error"
    }
  ]
}
```

Compatibility behavior built into the generator:
- Supports old string selectors and new selector objects
- Resolves selector objects to `fallback_css` for traditional Cypress generation
- Supports both flat test case values and nested `field_name` values
- Auto-adds `submit`, `error_container`, and `success_container` when missing

---

## Environment Variables

```bash
# Required (default provider)
OPENAI_API_KEY=your_key

# Optional (for Anthropic)
ANTHROPIC_API_KEY=your_key

# Optional (for Google)
GOOGLE_API_KEY=your_key
```

---

## Commands

### Basic Generation (ChatGPT Default)
```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login
```

### Multi-Provider LLM Support
```bash
# Use Claude (Anthropic)
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --llm anthropic

# Use Gemini (Google)
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --llm google

# View available providers
python qa_automation.py --help
```

### cy.prompt() Mode
```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --use-prompt
```
### Playwright — Standard Generation
```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework playwright
```

### Multiple Requirements — Playwright
```bash
python qa_automation.py \
  "Test successful login with valid credentials" \
  "Test login failure with invalid password" \
  "Test login form validation for empty fields" \
  --url https://the-internet.herokuapp.com/login \
  --framework playwright
```

### Generate and Execute
```bash
# Cypress
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --run

# Playwright
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework playwright --run
```

### Execution Videos

- Cypress terminal execution recording: `.github/images/Cypress_execution.mp4`
- Playwright terminal execution recording: `.github/images/Playwright_execution.mp4`

### View Patterns
```bash
python qa_automation.py --list-patterns
```

### Analyze Errors
```bash
python qa_automation.py --analyze "CypressError: Element not found"
```

Returns: `CATEGORY: SELECTOR REASON: ... FIX: ...` (via OpenAI GPT-4o-mini)

### Command Line Arguments

| Argument | Description | Default |
|---|---|---|
| `requirements` | One or more test requirements (positional) | Required |
| `--framework` | Target framework: `cypress` or `playwright` | `cypress` |
| `--url`, `-u` | URL to analyze for selectors and test data | None |
| `--out` | Output directory for generated specs | Framework default |
| `--use-prompt` | Use cy.prompt() style (Cypress only) | `false` |
| `--run` | Run tests after generation | `false` |
| `--llm` | LLM provider: `openai`, `anthropic`, `google` | `openai` |
| `--analyze`, `-a` | Analyze a test failure log | — |
| `--file`, `-f` | Log file to analyze | — |
| `--list-patterns` | List all stored patterns in vector store | — |

## Running Generated Tests

### Cypress
```bash
# Run all generated tests
npx cypress run --spec 'cypress/e2e/generated/**/*.cy.js'

# Run cy.prompt() tests
npx cypress run --spec 'cypress/e2e/prompt-powered/**/*.cy.js'

# Open Cypress UI
npx cypress open
```

### Playwright
```bash
# Run all generated tests
npx playwright test tests/generated/

# Run with visible browser
npx playwright test --headed

# Run only Chromium
npx playwright test --project=chromium

# View HTML report
npx playwright show-report
```

---

## Directory Structure

```
ai-natural-language-tests/
├── cypress/
│   ├── e2e/
│   │   ├── generated/                        # Standard Cypress tests
│   │   └── prompt-powered/                   # cy.prompt() Cypress tests
│   └── fixtures/
│       └── url_test_data.json
├── tests/
│   └── generated/                            # Playwright tests
├── prompts/
│   ├── html_analysis.txt
│   ├── test_generation_traditional.txt
│   ├── test_generation_prompt_powered.txt
│   └── test_generation_playwright.txt
├── vector_db/                                # Pattern storage
│   └── chroma.sqlite3
├── .env
├── .gitignore
├── .dockerignore                             # NEW in v3.2
├── cypress.config.js
├── docker-compose.yml                        # NEW in v3.2
├── Dockerfile                                # NEW in v3.2
├── playwright.config.ts
├── package.json
├── qa_automation.py
├── requirements.txt
└── README.md
```

---

## How Tests Are Generated

### Generation Pipeline (per run)

Every time you run `qa_automation.py`, this five-step LangGraph workflow executes:

```
Step 1 — Initialize Vector Store
  Load or create ChromaDB at vector_db/
  Past patterns are available immediately

Step 2 — Fetch Test Data
  If --url is given: fetch live HTML, run AI HTML analysis,
  write normalized fixture to cypress/fixtures/url_test_data.json
  If --data is given: load existing fixture JSON
  normalize_test_data() runs on every fixture to apply
  the v3.4 schema (selector objects, field_name map, backfill defaults)

Step 3 — Search Similar Patterns
  Query vector store for the closest matching past test pattern
  If no patterns exist (first run): generation proceeds without context
  If patterns exist: the closest match is injected into the AI prompt

Step 4 — Generate Tests
  AI receives: requirement text + fixture data + similar pattern (if found)
  + framework-specific prompt template (traditional / prompt-powered / playwright)
  AI returns: complete test file source code
  Test file is written to the output directory with a timestamped filename

Step 5 — Optionally Run Tests
  If --run is given: execute the generated spec immediately
  Cypress: npx cypress run --spec <file>
  Playwright: npx playwright test <file>
  Pattern is saved to vector store after generation regardless of --run
```

### What the AI Receives

For each generation call the AI prompt is assembled from:

| Input | Source |
|-------|--------|
| Requirement text | CLI positional args |
| Fixture JSON (selectors + test cases) | `cypress/fixtures/url_test_data.json` |
| Flat CSS selector map | `flatten_css_selectors()` extracts `fallback_css` from fixture |
| Similar past pattern | Vector store semantic search result |
| Prompt template | `prompts/test_generation_traditional.txt`, `_prompt_powered.txt`, or `_playwright.txt` |

### What Happens on Every New Run

Each run is **additive and non-destructive** by default:

- A new timestamped file is always written — existing files are never overwritten.
- The fixture at `cypress/fixtures/url_test_data.json` **is** overwritten when `--url` is used. Save or rename it before re-running if you want to keep the previous version.
- The new test pattern is appended to the vector store, enriching future pattern matching.
- If `--run` is used, only the newly generated file is executed (not all files in the directory).

```
First run (no patterns):           clean AI generation from requirement + fixture
Second run (same requirement):     AI sees the first run as a matching pattern, refines output
Third run (different requirement): AI sees the closest prior requirement, adapts the pattern
```

Running many requirements in one command generates one file per requirement in sequence. They share the same fixture fetch (one `--url` call) but each gets its own AI generation call.

---

## Recommended Folder Architecture — Group by Functionality

The default output directories (`cypress/e2e/generated/`, `tests/generated/`) put all generated tests in a flat list. As the test suite grows, grouping by feature or functional area improves navigability, CI scoping, and team ownership.

### Summary — Architecture Decision

| Approach | Best For |
|----------|----------|
| Flat `generated/` folder | Quick prototyping, single-page testing, early development |
| Folder per functional area | Production suites, team ownership, CI parallelization |
| Folder per page/URL | URL-heavy apps where each page is fully independent |
| Folder per user journey | End-to-end flow testing (login → search → checkout) |

The recommended default for a growing test suite is **folder per functional area** because it maps directly to how teams are organized, how CI pipelines are scoped, and how failures are triaged.

---

## File Naming

Pattern:
```
{sequence}_{slugified-requirement}_{timestamp}.{ext}
```

Examples:
```
01_test-login_20250103_142530.cy.js        # Cypress
02_test-signup_20250103_142545.cy.js        # Cypress
01_test-login_20250103_142530.spec.ts       # Playwright
```

Components:
- sequence: 01, 02, 03...
- requirement: URL-safe requirement text
- timestamp: YYYYMMDD_HHMMSS
- `.cy.js` for Cypress, `.spec.ts` for Playwright

---

## Adding a New Framework

Add an entry to `FRAMEWORK_CONFIG` in `qa_automation.py`:

```python
FRAMEWORK_CONFIG = {
    # ... existing entries ...
    "selenium": {
        "name": "Selenium",
        "file_ext": ".test.py",
        "default_output": "selenium_tests",
        "run_cmd": "pytest",
        "code_fence": "python",
        "prompt_file_standard": "test_generation_selenium.txt",
        "supports_prompt_mode": False,
    },
}
```

Then create `prompts/test_generation_selenium.txt`.

---

## Releases

**v3.4** — Accessible HTML analysis, normalized selector schema, Docker fixture persistence  
**v3.3** — Multi-provider LLM support (OpenAI, Anthropic, Google)  
**v3.2** — Docker support, docker-compose setup  
**v3.1** — Playwright support, multi-framework architecture  
**v3.0** — LangGraph workflows, vector pattern learning  
**v2.2** — Dynamic test generation  
**v2.1** — AI failure analyzer  
**v2.0** — cy.prompt() support

---
**Medium**: [Let's Automate](https://aiqualityengineer.com/)
