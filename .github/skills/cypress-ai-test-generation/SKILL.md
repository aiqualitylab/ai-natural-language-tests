---
name: cypress-ai-test-generation
description: Guide for generating and working with AI-powered Cypress tests from natural language requirements. Use this when creating, modifying, or debugging the natural language to Cypress test conversion pipeline.
license: MIT
---

# Cypress AI Test Generation Skill

This skill provides specialized knowledge for working with the AI-powered Cypress test generation framework. Use this skill when you need to understand or modify how natural language requirements are converted into executable Cypress tests.

## When to Use This Skill

Use this skill when you need to:
- Generate Cypress tests from natural language requirements
- Modify the LangGraph workflow for test generation
- Adjust LLM prompts for better test quality
- Debug issues in the test generation pipeline
- Integrate documentation context into test generation
- Customize the output format of generated tests
- Work with the vector store for additional context

## Architecture Overview

### Workflow Pipeline

The test generation follows a LangGraph-orchestrated pipeline:

```
ParseCLI → BuildVectorStore → GenerateTests → RunCypress
```

**ParseCLI**: Parses command-line arguments including requirements, output directory, and options
**BuildVectorStore**: Optionally indexes documentation for additional context
**GenerateTests**: Uses LLM to convert requirements into Cypress test code
**RunCypress**: Optionally executes the generated tests

### Key Components

1. **State Management**: TypedDict-based state that flows through the workflow
2. **LLM Integration**: OpenAI GPT-4 via LangChain
3. **Vector Store**: ChromaDB for document embeddings and retrieval
4. **Template System**: Structured prompts that guide test generation

## Test Generation Prompt Template

The core prompt template (`CY_PROMPT_TEMPLATE`) is critical for test quality. It should:

```python
CY_PROMPT_TEMPLATE = """
You are a QA automation engineer generating Cypress E2E tests.

Requirement: {requirement}
{context}

Generate a complete Cypress test spec that:
- Uses the Describe-It pattern
- Includes meaningful test descriptions
- Follows Cypress best practices
- Uses proper selectors and assertions
- Includes appropriate waiting strategies
- Is executable and self-contained

Use `cy.visit('https://example.com')` as the base URL.

Return only the JavaScript code, no explanations.
"""
```

### Prompt Engineering Guidelines

When modifying the prompt template:
- **Be specific about output format**: "Return only JavaScript code"
- **Reference the requirement explicitly**: Use `{requirement}` placeholder
- **Include context conditionally**: Use `{context}` for vector store results
- **Define quality criteria**: List specific Cypress best practices
- **Set constraints**: Specify base URL, naming patterns, structure
- **Use imperative language**: "Generate", "Use", "Include"
- **Test iteratively**: Validate with diverse requirements after changes

## Vector Store Integration

### When to Use Vector Stores

Use vector stores when:
- Working with projects that have extensive documentation
- Requirements reference specific API endpoints or features
- Tests need domain-specific context not in the LLM's training
- Consistency with existing patterns is critical

### Vector Store Setup

```python
# Building the vector store
def build_vector_store(state):
    docs_dir = state.get("docs_dir")
    if not docs_dir:
        return state
    
    # Load documents
    loader = DirectoryLoader(docs_dir)
    documents = loader.load()
    
    # Create embeddings and store
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./vector_store"
    )
    
    state["vectorstore"] = vectorstore
    return state
```

### Retrieving Context

```python
# Get relevant context for a requirement
if vectorstore:
    relevant_docs = vectorstore.similarity_search(requirement, k=3)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
else:
    context = ""
```

## Generated Test Standards

### File Naming Convention

Generated tests follow this pattern:
```
{sequence}_{slugified-requirement}_{timestamp}.cy.js
```

Example: `01_test-user-login-with-valid-credentials_20240304_143022.cy.js`

### Test Structure Template

```javascript
// Requirement: [Original natural language requirement]
describe('[Test Suite Name]', () => {
  beforeEach(() => {
    // Common setup
    cy.visit('https://example.com');
  });

  it('[should do something specific]', () => {
    // Arrange
    cy.get('[data-testid="input"]').type('value');
    
    // Act
    cy.get('[data-testid="button"]').click();
    
    // Assert
    cy.get('[data-testid="result"]').should('contain', 'expected');
  });
  
  it('[should handle edge case]', () => {
    // Test implementation
  });
});
```

### Cypress Best Practices to Enforce

1. **Selectors Priority**:
   - `data-testid` attributes (best)
   - Semantic HTML (good)
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

## LangGraph Workflow Patterns

### Defining State Schema

```python
from typing import TypedDict, Optional, List

class AutomationState(TypedDict):
    requirements: List[str]
    output_dir: str
    run_tests: bool
    docs_dir: Optional[str]
    persist_vstore: bool
    vectorstore: Optional[Any]
    generated_files: List[str]
```

### Creating Workflow Nodes

```python
def generate_tests(state: AutomationState) -> AutomationState:
    """Generate Cypress tests from requirements."""
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    generated_files = []
    
    for idx, requirement in enumerate(state["requirements"], 1):
        # Get context from vector store if available
        context = get_context(state.get("vectorstore"), requirement)
        
        # Generate test code
        prompt = CY_PROMPT_TEMPLATE.format(
            requirement=requirement,
            context=context
        )
        response = llm.invoke(prompt)
        
        # Save generated test
        filename = create_filename(idx, requirement)
        filepath = Path(state["output_dir"]) / filename
        filepath.write_text(response.content)
        
        generated_files.append(str(filepath))
    
    state["generated_files"] = generated_files
    return state
```

### Building the Workflow Graph

```python
from langgraph.graph import StateGraph

workflow = StateGraph(AutomationState)

# Add nodes
workflow.add_node("parse_cli", parse_cli)
workflow.add_node("build_vector_store", build_vector_store)
workflow.add_node("generate_tests", generate_tests)
workflow.add_node("run_cypress", run_cypress)

# Define edges
workflow.add_edge("parse_cli", "build_vector_store")
workflow.add_edge("build_vector_store", "generate_tests")
workflow.add_edge("generate_tests", "run_cypress")

# Set entry point
workflow.set_entry_point("parse_cli")
```

## Debugging and Troubleshooting

### Common Issues and Solutions

**Issue**: Generated tests have incorrect selectors
- **Solution**: Add example selectors to the prompt template
- **Prevention**: Include HTML snippets in vector store documentation

**Issue**: Tests are too generic or don't match requirements
- **Solution**: Make requirements more specific and detailed
- **Prevention**: Add more context from documentation

**Issue**: LLM generates explanatory text instead of just code
- **Solution**: Strengthen "Return only JavaScript code" instruction
- **Prevention**: Add few-shot examples to the prompt

**Issue**: Vector store queries return irrelevant context
- **Solution**: Adjust similarity search `k` parameter
- **Prevention**: Organize documentation more clearly

### Debugging Techniques

1. **Log State at Each Node**:
```python
def generate_tests(state: AutomationState) -> AutomationState:
    print(f"DEBUG: Requirements: {state['requirements']}")
    print(f"DEBUG: Output dir: {state['output_dir']}")
    # ... rest of function
```

2. **Inspect LLM Responses**:
```python
response = llm.invoke(prompt)
print(f"DEBUG: LLM response length: {len(response.content)}")
print(f"DEBUG: First 200 chars: {response.content[:200]}")
```

3. **Validate Generated Files**:
```python
import subprocess
result = subprocess.run(
    ["npx", "cypress", "run", "--spec", filepath],
    capture_output=True
)
print(f"DEBUG: Cypress exit code: {result.returncode}")
```

## Customization Examples

### Example 1: Add Custom Cypress Commands

Modify the prompt to include custom commands:

```python
CY_PROMPT_TEMPLATE = """
...
You have access to these custom commands:
- cy.login(username, password) - Handles authentication
- cy.selectDropdown(selector, value) - Selects dropdown option
- cy.waitForLoader() - Waits for loading spinner to disappear

Use these commands when appropriate.
...
"""
```

### Example 2: Generate Tests with TypeScript

Update the template and filename generation:

```python
# In prompt template
"""
Generate a TypeScript Cypress test spec that:
- Uses proper TypeScript types
- Includes type imports from 'cypress'
...
"""

# In filename generation
filename = f"{idx:02d}_{slugify(requirement)}_{timestamp}.cy.ts"
```

### Example 3: Add API Test Generation

Extend the workflow for API tests:

```python
API_PROMPT_TEMPLATE = """
You are a QA automation engineer generating Cypress API tests.

Requirement: {requirement}

Generate a Cypress test that:
- Uses cy.request() for API calls
- Validates response status, headers, and body
- Includes proper error handling
- Tests both success and failure scenarios
...
"""

def generate_api_tests(state: AutomationState) -> AutomationState:
    # Similar to generate_tests but uses API_PROMPT_TEMPLATE
    pass
```

### Example 4: Multi-Browser Test Generation

Add browser-specific test variants:

```python
BROWSERS = ['chrome', 'firefox', 'edge']

def generate_tests(state: AutomationState) -> AutomationState:
    for browser in BROWSERS:
        prompt = CY_PROMPT_TEMPLATE.format(
            requirement=state["requirement"],
            browser=browser,
            context=context
        )
        # Generate browser-specific test
```

## Testing the Skill

### Validation Checklist

When modifying the test generation pipeline, verify:

- [ ] Generated tests are syntactically valid JavaScript
- [ ] File naming follows the expected convention
- [ ] Tests execute successfully in Cypress
- [ ] Requirements are accurately translated to test scenarios
- [ ] Vector store context is properly integrated (if used)
- [ ] Error handling works for malformed requirements
- [ ] Output directory is created if it doesn't exist
- [ ] Timestamps are correctly formatted

### Test Cases

```bash
# Test 1: Single simple requirement
python qa_automation.py "Test login page loads correctly"

# Test 2: Multiple requirements
python qa_automation.py "Test login" "Test logout" "Test registration"

# Test 3: With vector store context
python qa_automation.py "Test checkout process" --docs ./docs --persist-vstore

# Test 4: Generate and run
python qa_automation.py "Test navigation menu" --run

# Test 5: Custom output directory
python qa_automation.py "Test dashboard" --out cypress/e2e/dashboard
```

## Performance Optimization

### Token Usage Optimization

- Keep prompts concise while maintaining clarity
- Limit vector store retrieval to top 3-5 most relevant documents
- Use `temperature=0` for deterministic, efficient generation
- Cache vector store embeddings in `./vector_store`

### Speed Improvements

- Generate tests in parallel for multiple requirements (with rate limiting)
- Reuse vector store across multiple runs with `--persist-vstore`
- Use `gpt-4o-mini` for faster generation when appropriate
- Batch requirements when possible

## Additional Resources

- **Cypress Documentation**: https://docs.cypress.io
- **LangChain Prompting Guide**: https://python.langchain.com/docs/modules/model_io/prompts
- **LangGraph Workflow Patterns**: https://langchain-ai.github.io/langgraph
- **Vector Store Best Practices**: https://python.langchain.com/docs/modules/data_connection/vectorstores

## Contributing Improvements

When enhancing this skill:

1. Test changes with diverse natural language inputs
2. Document prompt modifications in this skill file
3. Add examples to the customization section
4. Update validation checklist if adding new features
5. Consider backward compatibility with existing generated tests
