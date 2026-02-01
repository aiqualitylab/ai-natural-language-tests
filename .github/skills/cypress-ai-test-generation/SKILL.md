# Cypress AI Test Generation Skill

An AI-powered skill for generating Cypress end-to-end tests from natural language requirements, featuring cy.prompt() self-healing capabilities.

## Overview

This skill leverages OpenAI GPT-4o-mini, LangChain, and LangGraph to automatically generate comprehensive Cypress test suites from simple natural language descriptions, with support for both traditional and cy.prompt() powered tests.

## Features

- **Natural Language Processing**: Convert plain English test requirements into executable Cypress tests
- **cy.prompt() Support**: Generate self-healing tests that adapt to UI changes
- **AI Failure Analysis**: Automatically diagnose and fix test failures with intelligent suggestions
- **Pattern Learning**: Build and reuse test patterns for consistent, high-quality test generation
- **Dual Modes**: Traditional Cypress tests and cy.prompt() powered tests

## Usage

### Basic Test Generation
```bash
python qa_automation.py "Test user login with valid credentials" --framework cypress --url https://example.com
```

### cy.prompt() Mode
```bash
python qa_automation.py "Test user login with valid credentials" --framework cypress --url https://example.com --use-prompt
```

### Multiple Test Cases
```bash
python qa_automation.py \
  "Test successful login" \
  "Test login with invalid password" \
  "Test form validation" \
  --framework cypress --url https://example.com
```

### Run Generated Tests
```bash
# Traditional tests
npx cypress run --spec 'cypress/e2e/generated/**/*.cy.js'

# cy.prompt() tests
npx cypress run --spec 'cypress/e2e/prompt-powered/**/*.cy.js'
```

### AI Failure Analysis
```bash
python qa_automation.py --analyze "CypressError: cy.get('#username') failed because the element was not found"
```

## Architecture

The skill uses a sophisticated LangGraph workflow:

1. **Initialize Vector Store**: Load existing test patterns
2. **Fetch Test Data**: Analyze target URL and extract selectors
3. **Search Similar Patterns**: Find relevant test patterns from history
4. **Generate Tests**: Use AI to create Cypress tests with context
5. **Run Tests**: Execute tests and provide feedback

## Dependencies

- Python 3.11+
- Node.js 20+
- Cypress 15.8.1+
- OpenAI API access
- LangChain & LangGraph

## Configuration

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Enable cy.prompt() in cypress.config.js:
```javascript
export default defineConfig({
  experimentalCypressPrompt: true,
  // ... other config
})
```

## Output Structure

### Traditional Tests
Saved in `cypress/e2e/generated/` with the pattern:
```
{sequence}_{slugified-requirement}_{timestamp}.cy.js
```

### cy.prompt() Tests
Saved in `cypress/e2e/prompt-powered/` with the same naming pattern.

Example: `01_test-user-login_20250103_142530.cy.js`

## Capabilities

- **Selector Strategies**: Intelligent element selection using multiple strategies
- **Wait Management**: Automatic wait handling for dynamic content
- **Assertion Generation**: Smart assertion creation based on page content
- **Error Handling**: Robust error handling and recovery
- **Self-Healing**: cy.prompt() tests adapt to UI changes automatically

## cy.prompt() Mode

cy.prompt() tests use natural language descriptions instead of hardcoded selectors:

```javascript
it('should login successfully', function () {
  cy.visit(this.testData.url);
  cy.prompt('Fill in the username field with a valid username');
  cy.prompt('Fill in the password field with a valid password');
  cy.prompt('Click the login button');
  cy.prompt('Verify that the user is logged in');
});
```

## Integration

This skill integrates seamlessly with:
- CI/CD pipelines (GitHub Actions, Jenkins, etc.)
- Cypress Dashboard
- Test management tools
- AI-powered testing suites

## Examples

### Authentication Testing
```bash
python qa_automation.py "Test user registration and login flow" --framework cypress --url https://auth-app.com
```

### E-commerce Testing
```bash
python qa_automation.py "Test adding items to cart and checkout process" --framework cypress --url https://ecommerce.com
```

### Form Validation
```bash
python qa_automation.py "Test contact form validation with various inputs" --framework cypress --url https://contact.com
```

## Contributing

To extend this skill:
1. Add new test patterns to the vector store
2. Enhance the prompt templates in `prompts/`
3. Improve the LangGraph workflow logic
4. Add support for new Cypress features

## License

MIT License - see LICENSE file for details.