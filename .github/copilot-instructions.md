# GitHub Copilot Instructions for Cypress Natural Language Tests

## Project Overview
This repository generates Cypress E2E tests from natural language requirements using:
- **OpenAI GPT-4o-mini** for test generation
- **LangGraph** for workflow orchestration  
- **LangChain** for AI pipeline management
- **cy.prompt()** for self-healing test capabilities
- **OpenRouter DeepSeek R1** for FREE failure analysis

## Test Data Options

### URL Analysis (--url)
```bash
python qa_automation.py "Test login" --url https://example.com/login
```
- Fetches live URL and analyzes HTML
- Extracts real selectors (#id, .class, [name=x])
- Generates test cases (valid_test + invalid_test)
- Saves fixture to `cypress/fixtures/url_test_data.json`

### JSON Data (--data)
```bash
python qa_automation.py "Test login" --data cypress/fixtures/login_data.json
```
- Uses existing JSON file with test data
- Supports same structure as URL-generated data

## Dual Test Generation Modes

### Traditional Cypress Tests
```bash
python qa_automation.py "Test login functionality" --url https://example.com/login
```
- Generates explicit Cypress commands with fixture data
- Uses `function()` syntax for `this.testData` access
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

1. **analyze_failure()** - Sends logs to OpenRouter for instant diagnosis

2. **generate_test_data_from_url()** - Fetches URLs, analyzes HTML, generates test data
   - Extracts selectors from HTML
   - Creates valid_test and invalid_test cases
   - Saves to `cypress/fixtures/url_test_data.json`

3. **TestGenerationState** - Manages workflow state
   - `requirements`: List of test descriptions
   - `output_dir`: Where to save tests
   - `use_prompt`: Boolean for cy.prompt mode
   - `docs_context`: Optional documentation context
   - `generated_tests`: Results
   - `run_tests`: Whether to execute after generation
   - `error`: Any error messages

4. **HybridTestGenerator** - Generates both test types
   - `create_traditional_test_prompt()` - For traditional tests with fixtures
   - `create_prompt_powered_test_prompt()` - For cy.prompt tests
   - `generate_test_content()` - AI generation
   - `save_test_file()` - File output

5. **DocumentContextLoader** - Vector store for documentation context

6. **LangGraph Workflow Nodes**
   - `parse_cli_node` - Process arguments
   - `load_context_node` - Load documentation
   - `generate_tests_node` - Create tests
   - `run_cypress_node` - Execute tests

### Code Style Guidelines
- Use simple if/else instead of ternary operators in strings
- Use os.makedirs() instead of pathlib for file operations
- Keep variable names clear and concise
- Minimal logging - only essential information
- No complex nested conditions
- No emojis in output messages

## CLI Arguments Reference

| Argument | Purpose | Example |
|----------|---------|---------|
| `requirements` | Test descriptions | `"Test login"` |
| `--url`, `-u` | Live URL to analyze | `--url https://example.com/login` |
| `--data`, `-d` | JSON test data file | `--data testdata.json` |
| `--use-prompt` | Enable cy.prompt mode | `--use-prompt` |
| `--run` | Auto-run tests | `--run` |
| `--docs` | Add documentation context | `--docs ./api-docs` |
| `--out` | Output directory | `--out cypress/e2e/auth` |
| `--analyze`, `-a` | Analyze failure | `--analyze "error message"` |
| `--file`, `-f` | Log file to analyze | `-f error.log` |

## File Organization

```
cypress/
├── e2e/
│   ├── generated/          # Traditional tests (explicit selectors)
│   └── prompt-powered/     # cy.prompt tests (natural language)
└── fixtures/
    └── url_test_data.json  # Auto-generated from --url
```

## When Suggesting Code Changes

### DO:
- Keep code simple and readable
- Use if/else for conditional logic in strings
- Suggest appropriate test type based on use case
- Include both test approaches when relevant
- Follow existing file naming conventions
- Use `function()` syntax for traditional tests (this.testData access)
- Recommend --url for new applications
- Recommend --data for CI/CD pipelines

### DON'T:
- Use complex ternary operators in template strings
- Use pathlib when simple strings work
- Add unnecessary complexity
- Mix test types in same folder
- Hardcode selectors that could be dynamic
- Use emojis in code output

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
  -> Parse CLI (check --use-prompt, --url, --data flags)
  -> Load Context (optional docs, URL analysis, JSON data)
  -> Save Fixture (if --url or --data)
  -> Choose Prompt Template (traditional vs cy.prompt)
  -> Generate Test Content
  -> Save to Appropriate Folder
  -> Optionally Run Tests
```

## Common Patterns

### Traditional Test Pattern (with fixtures)
```javascript
describe('Login Tests', function () {
    beforeEach(function () {
        cy.fixture('url_test_data').then((data) => {
            this.testData = data;
        });
    });

    it('should login successfully with valid credentials', function () {
        cy.visit(this.testData.url);
        const valid = this.testData.test_cases.find(tc => tc.name === 'valid_test');
        cy.get('#username').type(valid.username);
        cy.get('#password').type(valid.password);
        cy.get('button[type="submit"]').click();
        cy.url().should('include', '/secure');
    });

    it('should show error with invalid credentials', function () {
        cy.visit(this.testData.url);
        const invalid = this.testData.test_cases.find(tc => tc.name === 'invalid_test');
        cy.get('#username').type(invalid.username);
        cy.get('#password').type(invalid.password);
        cy.get('button[type="submit"]').click();
        cy.get('#flash').should('contain', 'invalid');
    });
});
```

### cy.prompt() Test Pattern
```javascript
describe('User Login Tests', () => {
    const baseUrl = 'https://the-internet.herokuapp.com/login';

    beforeEach(() => {
        cy.visit(baseUrl);
    });

    it('should successfully log in with valid credentials', () => {
        cy.get('input[type="text"]').type('tomsmith');
        cy.get('input[type="password"]').type('SuperSecretPassword!');
        cy.get('button[type="submit"]').click();

        cy.url().should('include', '/secure');
        cy.get('.flash.success').should('be.visible').and('contain', 'You logged into a secure area!');
    });
});
```

## Suggested Improvements

When suggesting code improvements:
1. **Simplify Complex Logic** - Break down nested conditions
2. **Add Error Handling** - Wrap API calls in try-catch
3. **Improve Naming** - Use descriptive variable names
4. **Enhance Logging** - Add progress indicators (no emojis)
5. **Context Usage** - Suggest when to use `--docs`, `--url`, or `--data` flags

## Testing Commands

```bash
# Generate traditional test with URL analysis
python qa_automation.py "Test X" --url https://example.com/page

# Generate traditional test with JSON data
python qa_automation.py "Test X" --data cypress/fixtures/data.json

# Generate self-healing test
python qa_automation.py "Test X" --use-prompt

# With documentation context
python qa_automation.py "Test X" --docs ./docs --url https://example.com

# Generate and run
python qa_automation.py "Test X" --url https://example.com --run

# Analyze failure
python qa_automation.py --analyze "CypressError: Element not found"
python qa_automation.py --analyze -f error.log
```

## When User Asks For Help

### "How do I generate tests?"
Show both modes with examples and explain when to use each. Recommend --url for new apps.

### "My tests keep breaking"
Suggest using `--use-prompt` for self-healing capabilities, or `--analyze` to diagnose failures.

### "How do I add test data?"
Explain `--url` for live URL analysis, `--data` for JSON files, `--docs` for documentation.

### "Tests are too slow"
Recommend traditional tests with --data for CI/CD, cy.prompt for development.

## Integration with LangGraph

The workflow uses these node types:
- **parse_cli_node** - Processes command-line arguments
- **load_context_node** - Loads documentation if provided
- **generate_tests_node** - Creates test files
- **run_cypress_node** - Executes tests

## LLM Configuration

Current settings (hardcoded in qa_automation.py):
```python
# Test generation
ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Failure analysis
model="deepseek/deepseek-r1-0528:free"  # FREE via OpenRouter
```

## Best Practices for Generated Tests

1. **Clear Test Names** - Describe what's being tested
2. **Explicit Assertions** - Always verify expected outcomes
3. **Proper Cleanup** - Reset state between tests
4. **Error Messages** - Include meaningful failure messages
5. **Selectors** - Use real selectors from fixtures
6. **Fixtures** - Use cy.fixture() with function() syntax for data-driven tests

## Repository Structure Awareness

```
cypress-natural-language-tests/
├── .github/
│   ├── copilot-instructions.md (this file)
│   ├── images/ (workflow diagrams)
│   └── workflows/ (CI/CD)
├── cypress/
│   ├── e2e/
│   │   ├── generated/
│   │   └── prompt-powered/
│   └── fixtures/
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
- **Framework Version:** 2.1 (with URL analysis and failure analyzer)

---

**Remember:** This is a dual-mode test generator with URL analysis and failure diagnosis. Always consider which mode and data source best fits the user's needs!