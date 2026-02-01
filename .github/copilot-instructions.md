# GitHub Copilot Instructions for AI Natural Language Tests

## Project Overview

Generate Cypress and Playwright E2E tests from natural language using OpenAI GPT-4o-mini and LangGraph.

## CLI Quick Reference

| Flag | Purpose |
|------|---------|
| `requirements` | Test descriptions (positional) |
| `--framework`, `-f` | Target framework: `cypress` or `playwright` (default: cypress) |
| `--url`, `-u` | Fetch URL, analyze HTML, generate fixture |
| `--data`, `-d` | Load JSON test data file |
| `--use-prompt` | Generate cy.prompt() self-healing tests (Cypress only) |
| `--run` | Execute tests after generation |
| `--docs` | Add documentation context |
| `--analyze`, `-a` | Diagnose test failure with AI |
| `--file` | Log file to analyze |

## Three Test Modes

**Cypress Traditional** (`cypress/e2e/generated/`)
- Uses fixture data from `--url` or `--data`
- MUST use `function()` syntax for `this.testData`
- Fast, deterministic, best for CI/CD

**Cypress cy.prompt()** (`cypress/e2e/prompt-powered/`)
- Self-healing with natural language
- Requires Cypress 15.8.1+ and `experimentalCypressPrompt: true`
- Best for development

**Playwright Standard** (`tests/generated/`)
- TypeScript tests with modern async/await
- Multi-browser support (Chromium, Firefox, WebKit)
- Intelligent locator strategies

## Test Data Options

**URL Analysis** (`--url`)
- Fetches page, extracts selectors, generates test cases
- Saves to `cypress/fixtures/url_test_data.json`
- Works for ANY URL (login, contact, signup, search forms)

**JSON Data** (`--data`)
- Loads existing test data file
- Same structure as URL-generated data

## Dynamic Test Pattern (v2.2)

Tests use selectors dynamically from fixture - no hardcoded values:

```javascript
describe('Tests', function () {
    beforeEach(function () {
        cy.fixture('url_test_data').then((data) => {
            this.testData = data;
        });
    });

    it('should succeed with valid data', function () {
        cy.visit(this.testData.url);
        const valid = this.testData.test_cases.find(tc => tc.name === 'valid_test');
        const selectors = this.testData.selectors;
        
        Object.keys(selectors).forEach(field => {
            if (field !== 'submit' && valid[field]) {
                cy.get(selectors[field]).type(valid[field]);
            }
        });
        
        cy.get(selectors.submit).click();
    });
});
```

**Rules**: Use `function()` not `=>`, store in `this.testData`, access selectors dynamically.

## Fixture JSON Structure

```json
{
  "url": "https://example.com",
  "selectors": {"username": "#username", "password": "#password", "submit": "button[type=submit]"},
  "test_cases": [
    {"name": "valid_test", "username": "tom", "password": "secret", "expected": "success"},
    {"name": "invalid_test", "username": "wrong", "password": "wrong", "expected": "error"}
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
| cy.prompt() not working | Enable `experimentalCypressPrompt: true` (Cypress only) |
| Tests only work for one URL | Use dynamic selector pattern (v2.2) |
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
```

## Code Style

- Use `function()` for Cypress tests (not arrow functions)
- Use dynamic selectors from `this.testData.selectors`
- No hardcoded URLs or selectors
- No emojis in output
- Simple if/else, no complex ternaries
- Use async/await for Playwright tests
- Prefer semantic locators in Playwright (getByRole, getByText, etc.)