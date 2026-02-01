# Playwright AI Test Generation Skill

An AI-powered skill for generating Playwright end-to-end tests from natural language requirements.

## Overview

This skill leverages OpenAI GPT-4o-mini, LangChain, and LangGraph to automatically generate comprehensive Playwright test suites from simple natural language descriptions.

## Features

- **Natural Language Processing**: Convert plain English test requirements into executable Playwright tests
- **Multi-Browser Support**: Generate tests that work across Chromium, Firefox, and WebKit
- **AI Failure Analysis**: Automatically diagnose and fix test failures with intelligent suggestions
- **Pattern Learning**: Build and reuse test patterns for consistent, high-quality test generation
- **TypeScript Output**: Generate modern, type-safe Playwright tests

## Usage

### Basic Test Generation
```bash
python qa_automation.py "Test user login with valid credentials" --framework playwright --url https://example.com
```

### Multiple Test Cases
```bash
python qa_automation.py \
  "Test successful login" \
  "Test login with invalid password" \
  "Test form validation" \
  --framework playwright --url https://example.com
```

### Run Generated Tests
```bash
npx playwright test tests/generated/
```

### AI Failure Analysis
```bash
python qa_automation.py --analyze "page.locator('#username').waitFor() timed out"
```

## Architecture

The skill uses a sophisticated LangGraph workflow:

1. **Initialize Vector Store**: Load existing test patterns
2. **Fetch Test Data**: Analyze target URL and extract selectors
3. **Search Similar Patterns**: Find relevant test patterns from history
4. **Generate Tests**: Use AI to create Playwright tests with context
5. **Run Tests**: Execute tests and provide feedback

## Dependencies

- Python 3.11+
- Node.js 20+
- Playwright
- OpenAI API access
- LangChain & LangGraph

## Configuration

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Output Structure

Generated tests are saved in `tests/generated/` with the pattern:
```
{sequence}_{slugified-requirement}_{timestamp}.spec.ts
```

Example: `01_test-user-login_20250103_142530.spec.ts`

## Capabilities

- **Selector Strategies**: Intelligent element selection using multiple strategies
- **Wait Management**: Automatic wait handling for dynamic content
- **Assertion Generation**: Smart assertion creation based on page content
- **Error Handling**: Robust error handling and recovery
- **Cross-Browser**: Tests work across all Playwright-supported browsers

## Integration

This skill integrates seamlessly with:
- CI/CD pipelines (GitHub Actions, Jenkins, etc.)
- Test management tools
- Browser automation workflows
- AI-powered testing suites

## Examples

### E-commerce Testing
```bash
python qa_automation.py "Test adding items to cart and checkout" --framework playwright --url https://example-shop.com
```

### Form Validation
```bash
python qa_automation.py "Test contact form with valid and invalid inputs" --framework playwright --url https://contact-form.com
```

### Navigation Testing
```bash
python qa_automation.py "Test main navigation menu functionality" --framework playwright --url https://website.com
```

## Contributing

To extend this skill:
1. Add new test patterns to the vector store
2. Enhance the prompt templates in `prompts/`
3. Improve the LangGraph workflow logic
4. Add support for new Playwright features

## License

MIT License - see LICENSE file for details.