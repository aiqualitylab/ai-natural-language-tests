---
name: cypress-ai-test-generation
description: Guide for AI-powered Cypress test generation from natural language. Supports traditional tests with fixtures, cy.prompt() self-healing tests, URL analysis, JSON data, and AI failure diagnosis.
license: MIT
---

# Cypress AI Test Generation Skill

Generate Cypress E2E tests from natural language using OpenAI GPT-4o-mini and LangGraph.

## CLI Quick Reference

| Flag | Purpose |
|------|---------|
| `requirements` | Test descriptions (positional) |
| `--url`, `-u` | Fetch URL, analyze HTML, generate fixture |
| `--data`, `-d` | Load JSON test data file |
| `--use-prompt` | Generate cy.prompt() self-healing tests |
| `--run` | Execute tests after generation |
| `--docs` | Add documentation context |
| `--analyze`, `-a` | Diagnose test failure with AI |
| `--file`, `-f` | Log file to analyze |

## Two Test Modes

**Traditional** (`cypress/e2e/generated/`)
- Uses fixture data from `--url` or `--data`
- MUST use `function()` syntax for `this.testData`
- Fast, deterministic, best for CI/CD

**cy.prompt()** (`cypress/e2e/prompt-powered/`)
- Self-healing with natural language
- Requires Cypress 15.8.1+ and `experimentalCypressPrompt: true`
- Best for development

## Test Data Options

**URL Analysis** (`--url`)
- Fetches page, extracts selectors, generates test cases
- Saves to `cypress/fixtures/url_test_data.json`

**JSON Data** (`--data`)
- Loads existing test data file
- Same structure as URL-generated data

## Critical Patterns

### Traditional Test with Fixtures

```javascript
describe('Tests', function () {
    beforeEach(function () {
        cy.fixture('url_test_data').then((data) => {
            this.testData = data;
        });
    });

    it('test case', function () {
        cy.visit(this.testData.url);
        const valid = this.testData.test_cases.find(tc => tc.name === 'valid_test');
        cy.get('#field').type(valid.value);
    });
});
```

**Rules**: Use `function()` not `=>`, store in `this.testData`, access in `it()` blocks.

### Fixture JSON Structure

```json
{
  "url": "https://example.com",
  "selectors": {"field": "#selector"},
  "test_cases": [
    {"name": "valid_test", "field": "value", "expected": "success"},
    {"name": "invalid_test", "field": "wrong", "expected": "error"}
  ]
}
```

### AI Failure Analysis

```bash
python qa_automation.py --analyze "CypressError: Element not found"
```

Returns: `REASON: ... FIX: ...` (FREE via OpenRouter DeepSeek R1)

## Environment Variables

```bash
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key  # For --analyze
```

## Common Issues

| Problem | Solution |
|---------|----------|
| `this.testData` undefined | Use `function()` not arrow functions |
| Wrong selectors | Use `--url` to fetch real selectors |
| cy.prompt() not working | Enable `experimentalCypressPrompt: true` |
| Slow CI/CD | Use traditional tests, not cy.prompt() |

## File Organization

```
cypress/
├── e2e/
│   ├── generated/       # Traditional tests
│   └── prompt-powered/  # cy.prompt() tests
└── fixtures/
    └── url_test_data.json
```