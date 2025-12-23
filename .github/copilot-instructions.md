# GitHub Copilot Instructions for Cypress Natural Language Tests

## Project Overview
This repository generates Cypress E2E tests from natural language requirements using:
- **OpenAI GPT-4** for test generation
- **LangGraph** for workflow orchestration  
- **LangChain** for AI pipeline management
- **cy.prompt()** for self-healing test capabilities (NEW!)

## Dual Test Generation Modes

### Traditional Cypress Tests
```bash
python qa_automation.py "Test login functionality"
```
- Generates explicit Cypress commands with fixed selectors
- Output: `cypress/e2e/generated/`

### Self-Healing Tests (cy.prompt)
```bash
python qa_automation.py "Test login functionality" --use-prompt
```
- Generates natural language test steps
- Auto-adapts when UI changes
- Output: `cypress/e2e/prompt-powered/`

## Code Architecture

### Main Script: qa_automation.py
Key components:
1. **TestGenerationState** - Manages workflow state including `use_prompt` flag
2. **HybridTestGenerator** - Generates both test types
   - `create_traditional_test_prompt()` - For traditional tests
   - `create_prompt_powered_test_prompt()` - For cy.prompt tests
3. **LangGraph Workflow** - Orchestrates test generation
   - parse_cli_node
   - load_context_node
   - generate_tests_node
   - run_cypress_node

### Code Style Guidelines
- Use simple if/else instead of ternary operators in strings
- Use os.makedirs() instead of pathlib for file operations
- Keep variable names clear and concise
- Minimal logging - only essential information
- No complex nested conditions

## Prompt Engineering Best Practices

### For Traditional Tests
```python
"""Generate a complete Cypress test file.
- Use real selectors (id, class, name) over data-testid
- Include both positive and negative test cases
- Use cy.visit('https://the-internet.herokuapp.com/login') as base URL
- Return ONLY runnable JavaScript code
"""
```

### For cy.prompt() Tests
```python
"""Generate test using cy.prompt() with natural language.
- Use natural language steps: "Visit the login page", "Click submit"
- Add critical assertions with traditional Cypress
- Group related steps logically
"""
```

## CLI Arguments Reference

| Argument | Purpose | Example |
|----------|---------|---------|
| `requirements` | Test descriptions | `"Test login"` |
| `--use-prompt` | Enable cy.prompt mode | `--use-prompt` |
| `--run` | Auto-run tests | `--run` |
| `--docs` | Add context | `--docs ./api-docs` |
| `--out` | Output directory | `--out cypress/e2e/auth` |

## File Organization

```
cypress/e2e/
├── generated/          # Traditional tests (explicit selectors)
└── prompt-powered/     # cy.prompt tests (natural language)
```

## When Suggesting Code Changes

### DO:
✅ Keep code simple and readable
✅ Use if/else for conditional logic in strings
✅ Suggest appropriate test type based on use case
✅ Include both test approaches when relevant
✅ Follow existing file naming conventions

### DON'T:
❌ Use complex ternary operators in template strings
❌ Use pathlib when simple strings work
❌ Add unnecessary complexity
❌ Mix test types in same folder
❌ Hardcode selectors that could be dynamic

## Cypress Configuration

The `cypress.config.js` must include:
```javascript
module.exports = defineConfig({
  e2e: {
    experimentalCypressPrompt: true,  // Enables cy.prompt()
    baseUrl: 'https://the-internet.herokuapp.com',
  }
});
```

## Test Generation Flow

```
User Requirement 
  → Parse CLI (check --use-prompt flag)
  → Load Context (optional docs)
  → Choose Prompt Template (traditional vs cy.prompt)
  → Generate Test Content
  → Save to Appropriate Folder
  → Optionally Run Tests
```

## Common Patterns

### Traditional Test Pattern
```javascript
describe('Feature', () => {
  it('should do something', () => {
    cy.visit('/page');
    cy.get('#selector').type('value');
    cy.get('button').click();
    cy.get('.result').should('be.visible');
  });
});
```

### cy.prompt() Test Pattern
```javascript
describe('Feature', () => {
  it('should do something', () => {
    cy.prompt([
      'Visit the page',
      'Type "value" in the input field',
      'Click the submit button',
      'Verify result is visible'
    ]);
    // Critical assertion
    cy.url().should('include', '/success');
  });
});
```

## Suggested Improvements

When suggesting code improvements:
1. **Simplify Complex Logic** - Break down nested conditions
2. **Add Error Handling** - Wrap API calls in try-catch
3. **Improve Naming** - Use descriptive variable names
4. **Enhance Logging** - Add progress indicators
5. **Context Usage** - Suggest when to use `--docs` flag

## Testing Commands

```bash
# Generate traditional test
python qa_automation.py "Test X"

# Generate self-healing test
python qa_automation.py "Test X" --use-prompt

# With documentation context
python qa_automation.py "Test X" --docs ./docs --use-prompt

# Generate and run
python qa_automation.py "Test X" --use-prompt --run
```

## When User Asks For Help

### "How do I generate tests?"
Show both modes with examples and explain when to use each.

### "My tests keep breaking"
Suggest using `--use-prompt` for self-healing capabilities.

### "How do I add context?"
Explain `--docs` flag and vector store integration.

### "Tests are too slow"
Recommend traditional tests for CI/CD, cy.prompt for development.

## Integration with LangGraph

The workflow uses these node types:
- **parse_cli_node** - Processes command-line arguments
- **load_context_node** - Loads documentation if provided
- **generate_tests_node** - Creates test files
- **run_cypress_node** - Executes tests

## OpenAI Model Configuration

Default settings:
```python
ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0  # Deterministic output
)
```

Suggest `gpt-4` or `gpt-4o` for complex requirements.

## Best Practices for Generated Tests

1. **Clear Test Names** - Describe what's being tested
2. **Explicit Assertions** - Always verify expected outcomes
3. **Proper Cleanup** - Reset state between tests
4. **Error Messages** - Include meaningful failure messages
5. **Selectors** - Prefer stable selectors over brittle ones

## Repository Structure Awareness

```
cypress-natural-language-tests/
├── .github/
│   ├── copilot-instructions.md (this file)
│   ├── images/ (workflow diagrams)
│   └── workflows/ (CI/CD)
├── cypress/
│   └── e2e/
│       ├── generated/
│       └── prompt-powered/
├── qa_automation.py (main script)
├── cypress.config.js
├── package.json
├── requirements.txt
└── README.md
```

## Version Information

- **Cypress Version:** 15.8.1 (required for cy.prompt)
- **Python Version:** 3.8+
- **Node.js Version:** 14+
- **Framework Version:** 2.0 (with cy.prompt integration)

---

**Remember:** This is a dual-mode test generator. Always consider which mode best fits the user's needs!