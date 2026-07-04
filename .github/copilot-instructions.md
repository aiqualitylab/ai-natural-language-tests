# GitHub Copilot Instructions for AI Natural Language Tests

## Project Overview

Generate Cypress, Playwright, WebdriverIO, and Appium E2E tests from natural language using OpenAI GPT-4o-mini, Anthropic Claude, Google Gemini, or local LLM endpoints (Ollama, vLLM, LM Studio) and LangGraph.

## CLI Quick Reference

| Flag | Purpose |
|------|---------|
| `requirements` | Test descriptions (positional) |
| `--framework`, `-f` | Target framework: `cypress`, `playwright`, `webdriverio`, or `appium` (default: cypress) |
| `--url`, `-u` | Fetch URL, analyze HTML, generate fixture |
| `--llm` | LLM provider: `openai`, `anthropic`, `google`, `ollama`, or `local-openai` (default: openai) |
| `--use-prompt` | Generate prompt-powered self-healing tests (Cypress and Appium) |
| `--run` | Execute tests after generation |
| `--analyze`, `-a` | Diagnose test failure with AI |
| `--file` | Log file to analyze |
| `--list-patterns` | List all stored historical test patterns |
| `--list-html-replays` | List saved HTML analysis replay IDs |
| `--replay-html-analysis` | Print saved HTML analysis snapshot by run ID |

## LLM Providers

### Cloud Providers
- **OpenAI** (default): `gpt-4o-mini` — Requires `OPENAI_API_KEY`
- **Anthropic**: `claude-3-5-sonnet-20241022` — Requires `ANTHROPIC_API_KEY`
- **Google**: `gemini-2.0-flash` — Requires `GOOGLE_API_KEY`

### Local Providers (Privacy-First, No HTML Sent to APIs)
- **Ollama**: Local open-source models (Llama, Mistral, etc.)
  - Set: `OLLAMA_BASE_URL=http://localhost:11434/v1` (default)
  - Set: `OLLAMA_MODEL=llama2` (or any Ollama model)
- **Local OpenAI-compatible** (vLLM, LM Studio):
  - Set: `LOCAL_OPENAI_BASE_URL=http://localhost:8000/v1` (default)
  - Set: `LOCAL_OPENAI_MODEL=gpt-3.5-turbo` (any compatible model name)

## Framework Modes

**Cypress Traditional** (`cypress/e2e/generated/`)
- Uses fixture data from `--url` or `--data`
- MUST use `function()` syntax for `this.testData`
- Fast, deterministic, best for CI/CD

**Cypress cy.prompt()** (`cypress/e2e/prompt-powered/`)
- Requires Cypress 15.8.1+ and `experimentalPromptCommand: true`
- Best for development

**Playwright Standard** (`tests/generated/`)
- TypeScript tests with modern async/await
- Multi-browser support (Chromium, Firefox, WebKit)
- Intelligent locator strategies

**WebdriverIO Standard** (`webdriverio/tests/generated/`)
- JavaScript `.spec.js` tests using WebdriverIO with Mocha and Jest-like `expect`
- CSS-first selectors with `browser.url()`, `$(selector)`, and resilient assertions
- Runs through `wdio.conf.js` with Chrome + chromedriver service

**Appium + WebdriverIO** (`webdriverio/tests/appium-tests/`)
- JavaScript `.spec.js` tests using WebdriverIO with Appium service
- Mobile test generation for Android (default) and iOS
- Self-healing with prompt-powered natural language selectors
- Mobile capabilities for Android by default, iOS via `APP_PLATFORM=ios`
- Self-healing with prompt-powered natural language selectors
- Runs through `wdio.appium.conf.js`

## Test Data Options

**URL Analysis** (`--url`)
- Fetches page, extracts selectors, generates test cases
- Saves to `cypress/fixtures/url_test_data.json`
- Works for ANY URL (login, contact, signup, search forms)

**JSON Data** (`--data`)
- Loads existing test data file
- Same structure as URL-generated data

## Dynamic Test Pattern (v5.0)

Tests use selectors dynamically from fixture - no hardcoded values:

```javascript
describe('Tests', function () {
    function getSelector(selectorEntry) {
        if (!selectorEntry) {
            return null;
        }

        if (typeof selectorEntry === 'string') {
            return selectorEntry;
        }

        if (typeof selectorEntry === 'object') {
            return selectorEntry.fallback_css || null;
        }

        return null;
    }

    function fillFormFields(testCase, selectors) {
        const values = testCase.field_name || testCase;

        Object.keys(values).forEach(function (field) {
            const selector = getSelector(selectors[field]);
            const value = values[field];

            if (selector && typeof value === 'string' && value) {
                cy.get(selector).clear().type(value);
            }
        });
    }

    beforeEach(function () {
        cy.fixture('url_test_data').then((data) => {
            this.testData = data;
        });
    });

    it('should succeed with valid data', function () {
        cy.visit(this.testData.url);
        const valid = this.testData.test_cases.find(tc => tc.name === 'valid_test');
        const selectors = this.testData.selectors;
        
        fillFormFields(valid, selectors);

        const submitSelector = getSelector(selectors.submit);
        cy.get(submitSelector).click();
    });
});
```

**Rules**: Use `function()` not `=>`, store in `this.testData`, resolve selector objects via `fallback_css`, and support both flat and `field_name` test values.

## Fixture JSON Structure

```json
{
  "url": "https://example.com",
    "selectors": {
        "username": {
            "cypress": "cy.findByLabelText(/username/i)",
            "playwright": "page.getByLabel('Username')",
            "fallback_css": "input[name='username']"
        },
        "password": {
            "cypress": "cy.findByLabelText(/password/i)",
            "playwright": "page.getByLabel('Password')",
            "fallback_css": "input[name='password']"
        },
        "submit": {
            "cypress": "cy.findByRole('button', {name: /login/i})",
            "playwright": "page.getByRole('button', {name: 'Login'})",
            "fallback_css": "button[type='submit']"
        }
    },
  "test_cases": [
        {"name": "valid_test", "field_name": {"username": "tom", "password": "secret"}, "expected": "success"},
        {"name": "invalid_test", "field_name": {"username": "wrong", "password": "wrong"}, "expected": "error"}
  ]
}
```

## AI Failure Analysis

```bash
python qa_automation.py --analyze "CypressError: Element not found"
python qa_automation.py --analyze "page.locator('#username').waitFor() timed out"
```

Returns: `CATEGORY: SELECTOR REASON: ... FIX: ...` (via OpenAI GPT-4o-mini)

## Environment Variables

```bash
OPENAI_API_KEY=your_key
```

## Common Issues

| Problem | Solution |
|---------|----------|
| `this.testData` undefined | Use `function()` not arrow functions (Cypress) |
| Wrong selectors | Use `--url` to fetch real selectors |
| cy.prompt() not working | Enable `experimentalPromptCommand: true` (Cypress only) |
| Tests only work for one URL | Use normalized dynamic selector pattern (v5.0) |
| Playwright locator timeouts | Use `page.waitForLoadState('networkidle')` before locating elements |
| Browser context issues | Ensure proper `await` usage in Playwright tests |

## File Organization

```
cypress/
├── e2e/
│   ├── generated/       # Traditional Cypress tests
│   └── prompt-powered/  # cy.prompt() Cypress tests
└── fixtures/
    └── url_test_data.json

tests/
└── generated/          # Playwright tests

webdriverio/
└── tests/
    ├── generated/      # WebdriverIO tests
    ├── appium-tests/   # Appium mobile tests (Android/iOS)
    └── prompt-powered/ # WebdriverIO prompt-powered tests
```

## Code Style

- Use `function()` for Cypress tests (not arrow functions)
- Use dynamic selectors from `this.testData.selectors` and resolve selector objects with `fallback_css`
- No hardcoded URLs or selectors
- No emojis in output
- Simple if/else, no complex ternaries
- Use async/await for Playwright tests
- Prefer semantic locators in Playwright (getByRole, getByText, etc.)
- Use WebdriverIO `describe`/`it` with `browser.url()`, `$(selector)`, and resilient `expect(...)` assertions
