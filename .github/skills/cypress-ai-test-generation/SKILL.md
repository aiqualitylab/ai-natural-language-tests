---
name: cypress-ai-test-generation
description: Guide for generating and working with AI-powered Cypress tests from natural language requirements. Supports both traditional tests and self-healing cy.prompt() tests. Use this when creating, modifying, or debugging the natural language to Cypress test conversion pipeline.
license: MIT
---

# Cypress AI Test Generation Skill

This skill provides specialized knowledge for working with the AI-powered Cypress test generation framework. Use this skill when you need to understand or modify how natural language requirements are converted into executable Cypress tests, with support for both traditional and self-healing cy.prompt() modes.

## When to Use This Skill

Use this skill when you need to:
- Generate Cypress tests from natural language requirements (traditional or cy.prompt)
- Choose between traditional and self-healing test modes
- Modify the LangGraph workflow for dual-mode test generation
- Adjust LLM prompts for better test quality in both modes
- Debug issues in the test generation pipeline
- Integrate documentation context into test generation
- Customize the output format of generated tests
- Work with the vector store for additional context

## Architecture Overview

### Dual Test Generation Modes

The framework supports two test generation modes:

**Traditional Tests**
- Uses explicit selectors (id, class, data-testid)
- Fast execution with no runtime AI calls
- Deterministic behavior
- Best for stable applications and CI/CD
- Output: `cypress/e2e/generated/`

**Self-Healing Tests (cy.prompt)**
- Uses natural language step descriptions
- Adapts automatically when UI changes
- Requires Cypress 13.18+
- Best for active development
- Output: `cypress/e2e/prompt-powered/`

### Workflow Pipeline

The test generation follows a LangGraph-orchestrated pipeline:

```
ParseCLI → LoadContext → GenerateTests → RunCypress
```

**ParseCLI**: Parses command-line arguments including requirements, output directory, and `--use-prompt` flag
**LoadContext**: Optionally indexes documentation for additional context
**GenerateTests**: Uses LLM to convert requirements into Cypress test code (mode-specific)
**RunCypress**: Optionally executes the generated tests from appropriate folder

### Key Components

1. **State Management**: Dataclass-based state with `use_prompt` flag that flows through the workflow
2. **LLM Integration**: OpenAI GPT-4 via LangChain
3. **Vector Store**: ChromaDB for document embeddings and retrieval
4. **Dual Template System**: Separate prompts for traditional and cy.prompt() test generation
5. **Organized Output**: Automatic folder organization based on test type

## Test Generation Prompt Templates

### Traditional Test Template

The core prompt template for traditional Cypress tests:

```python
def create_traditional_test_prompt(self) -> str:
    return """You are an expert Cypress test automation engineer.

Generate a complete Cypress test file based on the requirement.

REQUIREMENT: {requirement}

CONTEXT (if available): {context}

GUIDELINES:
- Use Cypress best practices
- Use `describe` and `it` blocks
- Prefer real, working selectors (id, class, name) over data-testid
- Include clear assertions for both success and error cases
- Handle forms, buttons, and navigation
- Use `cy.visit('https://the-internet.herokuapp.com/login')` as the base URL
- Include both positive and negative test paths when applicable
- Return ONLY runnable JavaScript code, no explanations

Generate ONLY the test code, no explanations."""
```

### Self-Healing Test Template (cy.prompt)

The prompt template for cy.prompt() tests:

```python
def create_prompt_powered_test_prompt(self) -> str:
    return """You are an expert Cypress test automation engineer with cy.prompt() expertise.

Generate a Cypress test file using cy.prompt() for self-healing capabilities.

REQUIREMENT: {requirement}

CONTEXT (if available): {context}

GUIDELINES FOR cy.prompt():
- Use cy.prompt() with natural language step arrays
- Each step should be clear and descriptive
- Include verification steps
- Use natural language like "Visit the login page", "Click the submit button"
- Group related steps logically
- Add fallback traditional Cypress commands for critical assertions

EXAMPLE STRUCTURE:
describe('User Login Tests', () => {{
    const baseUrl = 'https://the-internet.herokuapp.com/login';

    beforeEach(() => {{
        cy.visit(baseUrl);
    }});

    it('should successfully log in with valid credentials', () => {{
        cy.get('input[type="text"]').type('tomsmith');
        cy.get('input[type="password"]').type('SuperSecretPassword!');
        cy.get('button[type="submit"]').click();

        cy.url().should('include', '/secure');
        cy.get('.flash.success').should('be.visible');
    }});
}});

Generate ONLY the test code, no explanations."""
```

### Prompt Engineering Guidelines

When modifying the prompt templates:
- **Maintain separation**: Keep distinct templates for traditional vs cy.prompt
- **Be specific about output format**: "Return only JavaScript code"
- **Reference the requirement explicitly**: Use `{requirement}` placeholder
- **Include context conditionally**: Use `{context}` for vector store results
- **Define quality criteria**: List specific Cypress best practices for each mode
- **Set constraints**: Specify base URL, naming patterns, structure
- **Use imperative language**: "Generate", "Use", "Include"
- **Add mode-specific examples**: Show actual code structure for each type
- **Test iteratively**: Validate with diverse requirements after changes

## Vector Store Integration

### When to Use Vector Stores

Use vector stores when:
- Working with projects that have extensive documentation
- Requirements reference specific API endpoints or features
- Tests need domain-specific context not in the LLM's training
- Consistency with existing patterns is critical
- Generating either traditional or cy.prompt() tests with context

### Vector Store Setup

```python
class DocumentContextLoader:
    """Load and process documentation for context"""
    
    def load_documents(self, docs_dir: str) -> List[Document]:
        """Load documents from directory"""
        docs = []
        docs_path = Path(docs_dir)
        
        if not docs_path.exists():
            return docs
        
        for file_path in docs_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        docs.append(Document(
                            page_content=content,
                            metadata={"source": str(file_path)}
                        ))
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        return docs
    
    def create_vector_store(self, docs, persist_dir="./vector_store"):
        """Create vector store from documents"""
        if not docs:
            return None
        
        splits = self.text_splitter.split_documents(docs)
        vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=persist_dir
        )
        return vector_store
```

### Retrieving Context

```python
def get_relevant_context(self, vector_store, query: str, k: int = 3) -> str:
    """Retrieve relevant context for a query"""
    if not vector_store:
        return ""
    
    results = vector_store.similarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in results])
    return context
```

## Generated Test Standards

### File Naming Convention

Generated tests follow this pattern:
```
{sequence}_{slugified-requirement}_{timestamp}.cy.js
```

Example: `01_test-user-login-with-valid-credentials_20241223_100000.cy.js`

### File Organization

```
cypress/e2e/
├── generated/              # Traditional Cypress tests
│   ├── 01_test-login_20241223_100000.cy.js
│   └── 02_test-signup_20241223_100001.cy.js
└── prompt-powered/         # cy.prompt() self-healing tests
    ├── 01_test-checkout_20241223_100000.cy.js
    └── 02_test-cart_20241223_100001.cy.js
```

### Traditional Test Structure Template

```javascript
// Requirement: [Original natural language requirement]
// Test Type: Traditional

describe('[Test Suite Name]', () => {
  beforeEach(() => {
    cy.visit('https://the-internet.herokuapp.com/login');
  });

  it('should login with valid credentials', () => {
    cy.get('#username').type('tomsmith');
    cy.get('#password').type('SuperSecretPassword!');
    cy.get('button[type="submit"]').click();
    cy.get('.flash.success').should('contain', 'You logged into a secure area!');
  });
  
  it('should show error with invalid credentials', () => {
    cy.get('#username').type('invaliduser');
    cy.get('#password').type('wrongpassword');
    cy.get('button[type="submit"]').click();
    cy.get('.flash.error').should('contain', 'Your username is invalid!');
  });
});
```

### Self-Healing Test Structure Template (cy.prompt)

```javascript
// Requirement: [Original natural language requirement]
// Test Type: cy.prompt()

describe('[Test Suite Name]', () => {
  const baseUrl = 'https://the-internet.herokuapp.com/login';

  beforeEach(() => {
    cy.visit(baseUrl);
  });

  it('should login with valid credentials', () => {
    cy.get('input[type="text"]').type('tomsmith');
    cy.get('input[type="password"]').type('SuperSecretPassword!');
    cy.get('button[type="submit"]').click();
    
    // Critical assertion with traditional Cypress
    cy.url().should('include', '/secure');
  });
});
```

### Cypress Best Practices to Enforce

**Traditional Tests:**
1. **Selectors Priority**:
   - `data-testid` attributes (best)
   - Semantic HTML / ARIA labels (good)
   - CSS classes (acceptable)
   - XPath (avoid)

2. **Waiting Strategies**:
   - Use built-in Cypress waiting: `.should()`, `.contains()`
   - Avoid hard-coded `cy.wait(1000)`
   - Let Cypress automatically retry assertions

3. **Assertions**:
   - Use chainable `.should()` assertions
   - Be specific: `.should('have.length', 5)` not `.should('exist')`
   - Test both positive and negative cases

4. **Test Independence**:
   - Each test should be runnable in isolation
   - Clean up state in `afterEach()` if needed
   - Don't rely on test execution order

**Self-Healing Tests (cy.prompt):**
1. **Natural Language Steps**:
   - Use clear, descriptive language
   - Be specific about what to interact with
   - Include verification steps

2. **Critical Assertions**:
   - Add traditional Cypress assertions for critical checks
   - Combine cy.prompt() navigation with explicit assertions
   - Don't rely solely on AI for validation

3. **Step Grouping**:
   - Group related actions logically
   - Keep step arrays focused on single workflows
   - Break complex scenarios into multiple it() blocks

## LangGraph Workflow Patterns

### Defining State Schema

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class TestGenerationState:
    """State for test generation workflow with dual-mode support"""
    requirements: List[str]
    output_dir: str
    use_prompt: bool              # KEY: Toggle between test types
    docs_context: Optional[str]
    generated_tests: List[Dict[str, Any]]
    run_tests: bool
    error: Optional[str]
```

The `use_prompt` flag is critical - it determines which template to use and where to save tests.

### Creating Workflow Nodes

```python
def generate_tests_node(state: TestGenerationState) -> TestGenerationState:
    """Generate Cypress tests from requirements based on mode"""
    generator = HybridTestGenerator()
    generated = []
    
    for idx, requirement in enumerate(state.requirements, 1):
        try:
            # Generate test - mode determined by use_prompt flag
            content = generator.generate_test_content(
                requirement=requirement,
                context=state.docs_context or "",
                use_prompt=state.use_prompt  # KEY parameter
            )
            
            # Save to appropriate folder based on mode
            result = generator.save_test_file(
                content=content,
                requirement=requirement,
                output_dir=state.output_dir,
                use_prompt=state.use_prompt,  # Determines folder
                index=idx
            )
            
            generated.append(result)
            
        except Exception as e:
            state.error = str(e)
    
    state.generated_tests = generated
    return state
```

### Building the Workflow Graph

```python
from langgraph.graph import StateGraph, END

def create_workflow() -> StateGraph:
    """Create LangGraph workflow with dual-mode support"""
    workflow = StateGraph(TestGenerationState)
    
    # Add nodes
    workflow.add_node("parse_cli", parse_cli_node)
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("generate_tests", generate_tests_node)
    workflow.add_node("run_cypress", run_cypress_node)
    
    # Define edges
    workflow.set_entry_point("parse_cli")
    workflow.add_edge("parse_cli", "load_context")
    workflow.add_edge("load_context", "generate_tests")
    workflow.add_edge("generate_tests", "run_cypress")
    workflow.add_edge("run_cypress", END)
    
    return workflow.compile()
```

## Configuration Requirements

### For All Tests
- Python 3.8+
- Node.js 14+
- OpenAI API key (set in `.env` file)
- Cypress installed

### For Self-Healing Tests (cy.prompt)
Enable in `cypress.config.js`:
```javascript
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    baseUrl: 'https://the-internet.herokuapp.com',
    
    // REQUIRED: Enable cy.prompt() feature
    experimentalCypressPrompt: true,
    
    // Optional: Configure AI behavior
    cypressPromptOptions: {
      enableSelfHealing: true,
      showGeneratedCode: true,
      timeout: 30000,
    },
    
    defaultCommandTimeout: 10000,
  },
});
```

**Important**: Cypress version 13.18+ is required for cy.prompt() support.

## Debugging and Troubleshooting

### Common Issues and Solutions

**Issue**: Self-healing tests don't execute
- **Solution**: Verify `experimentalCypressPrompt: true` in cypress.config.js
- **Prevention**: Check Cypress version is 13.18+

**Issue**: Generated tests have incorrect selectors (Traditional)
- **Solution**: Add example selectors to the prompt template
- **Prevention**: Include HTML snippets in vector store documentation

**Issue**: Tests are too generic or don't match requirements
- **Solution**: Make requirements more specific and detailed
- **Prevention**: Add more context from documentation with --docs flag

**Issue**: LLM generates explanatory text instead of just code
- **Solution**: Strengthen "Return only JavaScript code" instruction
- **Prevention**: Add few-shot examples to the prompt

**Issue**: cy.prompt() tests are slow in CI/CD
- **Solution**: Use traditional tests for CI/CD pipelines
- **Prevention**: Export cy.prompt() code to traditional format for production

**Issue**: Wrong test type generated
- **Solution**: Verify `use_prompt` flag is set correctly in state
- **Prevention**: Check CLI argument parsing in parse_cli_node

**Issue**: Vector store queries return irrelevant context
- **Solution**: Adjust similarity search `k` parameter
- **Prevention**: Organize documentation more clearly

### Debugging Techniques

1. **Log State at Each Node**:
```python
def generate_tests_node(state: TestGenerationState) -> TestGenerationState:
    test_type = "cy.prompt()" if state.use_prompt else "Traditional"
    print(f"DEBUG: Generating {test_type} tests")
    print(f"DEBUG: Requirements: {state.requirements}")
```

2. **Inspect LLM Responses**:
```python
response = llm.invoke(prompt)
print(f"DEBUG: Response length: {len(response.content)}")
print(f"DEBUG: First 200 chars: {response.content[:200]}")
```

3. **Validate Generated Files**:
```python
# Check file location matches test type
if state.use_prompt:
    assert "prompt-powered" in filepath
else:
    assert "generated" in filepath
```

## Customization Examples

### Example 1: Add Custom Cypress Commands

Modify the traditional test template:

```python
"""
You have access to these custom commands:
- cy.login(username, password) - Handles authentication
- cy.selectDropdown(selector, value) - Selects dropdown option
- cy.waitForLoader() - Waits for loading spinner

Use these commands when appropriate.
"""
```

### Example 2: Generate Tests with TypeScript

Update both templates and filename generation:

```python
# In prompt template
"""
Generate a TypeScript Cypress test spec that:
- Uses proper TypeScript types
- Includes type imports from 'cypress'
"""

# In filename generation
filename = f"{idx:02d}_{slugify(requirement)}_{timestamp}.cy.ts"
```

### Example 3: Hybrid Test Generation

Create tests combining both approaches:

```python
"""
Generate a test that uses:
- cy.prompt() for navigation and form filling
- Traditional Cypress for critical assertions
"""
```

### Example 4: Multi-Browser Testing

Add browser-specific variants:

```python
BROWSERS = ['chrome', 'firefox', 'edge']

def generate_tests(state: TestGenerationState) -> TestGenerationState:
    for browser in BROWSERS:
        # Generate browser-specific test
        pass
```

## Testing the Skill

### Validation Checklist

When modifying the test generation pipeline, verify:

- [ ] Generated tests are syntactically valid JavaScript
- [ ] File naming follows the expected convention
- [ ] Tests are saved to correct folder (generated vs prompt-powered)
- [ ] Tests execute successfully in Cypress
- [ ] Traditional tests use explicit selectors
- [ ] cy.prompt() tests use natural language steps
- [ ] Requirements are accurately translated to test scenarios
- [ ] Vector store context is properly integrated (if used)
- [ ] Error handling works for malformed requirements
- [ ] `use_prompt` flag correctly determines test type
- [ ] Output directory is created if it doesn't exist
- [ ] Timestamps are correctly formatted

### Test Cases

```bash
# Test 1: Traditional test
python qa_automation.py "Test login page loads correctly"

# Test 2: cy.prompt() test
python qa_automation.py "Test login page loads correctly" --use-prompt

# Test 3: Multiple with cy.prompt
python qa_automation.py "Test login" "Test logout" --use-prompt

# Test 4: With context
python qa_automation.py "Test checkout" --docs ./docs --use-prompt

# Test 5: Generate and run
python qa_automation.py "Test navigation" --run

# Test 6: Custom output
python qa_automation.py "Test dashboard" --out cypress/e2e/custom
```

## Performance Optimization

### Token Usage Optimization

- Keep prompts concise while maintaining clarity
- Use separate templates to avoid sending unused instructions
- Limit vector store retrieval to top 3-5 most relevant documents
- Use `temperature=0` for deterministic generation
- Cache vector store embeddings in `./vector_store`

### Speed Improvements

- Traditional tests: No runtime AI calls, fastest execution
- cy.prompt() tests: Slower due to runtime AI
- Generate tests in parallel for multiple requirements
- Reuse vector store across multiple runs
- Use `gpt-4o-mini` for faster generation
- Export cy.prompt() code to traditional for production

### Cost Optimization

- **Generation cost**: ~$0.01 per test (both types)
- **Runtime cost**: 
  - Traditional: $0
  - cy.prompt(): ~$0.002 per test execution
- **Recommendation**: Use cy.prompt() in dev, traditional in CI/CD

## Additional Resources

- **Cypress Documentation**: https://docs.cypress.io
- **cy.prompt() Documentation**: https://docs.cypress.io/api/commands/prompt
- **LangChain Prompting Guide**: https://python.langchain.com/docs/modules/model_io/prompts
- **LangGraph Workflow Patterns**: https://langchain-ai.github.io/langgraph
- **Vector Store Best Practices**: https://python.langchain.com/docs/modules/data_connection/vectorstores

## Contributing Improvements

When enhancing this skill:

1. Test changes with diverse natural language inputs for both test types
2. Document prompt modifications for both templates
3. Add examples showing both approaches
4. Update validation checklist if adding new features
5. Consider backward compatibility with existing tests
6. Verify both test types work correctly after changes
7. Update documentation to reflect new capabilities