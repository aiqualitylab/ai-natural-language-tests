---
name: langgraph-workflow-development
description: Guide for building and debugging LangGraph workflows for AI orchestration with dual-mode test generation. Use this when creating, modifying, or troubleshooting LangGraph state machines and workflow graphs for traditional and cy.prompt() test generation.
license: MIT
---

# LangGraph Workflow Development Skill

This skill provides specialized knowledge for working with LangGraph workflows in the context of AI-powered test automation with dual-mode support (traditional Cypress tests and self-healing cy.prompt() tests). Use this skill when building or modifying the orchestration layer that manages the test generation pipeline.

## When to Use This Skill

Use this skill when you need to:
- Create new LangGraph workflow nodes for dual-mode test generation
- Modify the workflow state schema to support both test types
- Add conditional branching based on test type selection
- Debug workflow execution issues in either mode
- Optimize workflow performance for different test types
- Add error handling and retry logic for both modes
- Integrate new tools or APIs into the dual-mode workflow
- Understand state flow with the `use_prompt` flag

## LangGraph Core Concepts

### State Management with Dual-Mode Support

LangGraph uses dataclasses to manage state flow with test type selection:

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class TestGenerationState:
    """State for test generation workflow with dual-mode support"""
    # Input parameters
    requirements: List[str]
    output_dir: str
    use_prompt: bool              # KEY: Toggle between traditional and cy.prompt
    docs_context: Optional[str]
    run_tests: bool
    
    # Output state
    generated_tests: List[Dict[str, Any]]
    error: Optional[str]
```

**Key Addition**: The `use_prompt` boolean flag determines whether to generate traditional Cypress tests or self-healing cy.prompt() tests. This flag flows through the entire workflow.

**Best Practices for Dual-Mode State Design**:
- Use `@dataclass` for clean, typed state management
- The `use_prompt` flag should be immutable after CLI parsing
- Mark optional fields with `Optional[Type]`
- Group related fields logically (inputs, outputs)
- Use descriptive field names that reflect both modes
- Document which fields are affected by `use_prompt`

### Workflow Nodes with Dual-Mode Logic

Nodes are pure functions that transform state and respect the test type:

```python
def parse_cli_node(state: TestGenerationState) -> TestGenerationState:
    """
    Parse CLI arguments - initial node with test type identification.
    """
    test_type = "cy.prompt()" if state.use_prompt else "Traditional"
    print(f"Generating {len(state.requirements)} test(s) - Type: {test_type}")
    return state
```

**Node Development Guidelines for Dual Mode**:
- Keep nodes focused on single responsibilities
- Always return the complete state object
- Use `state.use_prompt` to determine behavior
- Add validation at the start of each node
- Include comprehensive docstrings mentioning test types
- Handle errors gracefully with try-except
- Log test type for debugging

### Building the Dual-Mode Workflow Graph

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
    
    # Define edges (sequential flow)
    workflow.set_entry_point("parse_cli")
    workflow.add_edge("parse_cli", "load_context")
    workflow.add_edge("load_context", "generate_tests")
    workflow.add_edge("generate_tests", "run_cypress")
    workflow.add_edge("run_cypress", END)
    
    return workflow.compile()
```

## Common Workflow Patterns

### Pattern 1: Sequential Processing with Mode Selection

Linear workflow that adapts based on test type:

```python
def generate_tests_node(state: TestGenerationState) -> TestGenerationState:
    """Generate tests based on selected mode"""
    generator = HybridTestGenerator()
    generated = []
    
    for idx, requirement in enumerate(state.requirements, 1):
        try:
            # Generate test - mode selected by use_prompt flag
            content = generator.generate_test_content(
                requirement=requirement,
                context=state.docs_context or "",
                use_prompt=state.use_prompt  # KEY parameter
            )
            
            # Save test to appropriate folder
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

**When to use**: All dual-mode workflows need this pattern

### Pattern 2: Conditional Test Execution

Workflow that routes test execution based on test type:

```python
def run_cypress_node(state: TestGenerationState) -> TestGenerationState:
    """Run Cypress tests if requested, targeting correct folder"""
    if not state.run_tests or not state.generated_tests:
        return state
    
    # Choose spec pattern based on test type
    if state.use_prompt:
        tests = "cypress/e2e/prompt-powered/**/*.cy.js"
    else:
        tests = "cypress/e2e/generated/**/*.cy.js"
    
    cmd = f"npx cypress run --spec '{tests}'"
    
    try:
        os.system(cmd)
    except Exception as e:
        state.error = str(e)
    
    return state
```

**When to use**: When test execution depends on test type

### Pattern 3: Prompt Template Selection

Dynamic template selection based on mode:

```python
def generate_test_content(
    self,
    requirement: str,
    context: str = "",
    use_prompt: bool = False
) -> str:
    """Generate test content using appropriate template"""
    
    # Select template based on mode
    if use_prompt:
        template = self.create_prompt_powered_test_prompt()
    else:
        template = self.create_traditional_test_prompt()
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | self.llm
    
    response = chain.invoke({
        "requirement": requirement,
        "context": context or "No additional context provided"
    })
    
    # Extract and clean code
    content = response.content
    if "```javascript" in content:
        content = content.split("```javascript")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    return content
```

**When to use**: Core generation logic with mode-specific prompts

### Pattern 4: File Organization by Test Type

Organize output files based on test type:

```python
def save_test_file(
    self,
    content: str,
    requirement: str,
    output_dir: str,
    use_prompt: bool,
    index: int
) -> Dict[str, Any]:
    """Save test file to appropriate folder"""
    
    # Conditional for folder selection
    if use_prompt:
        folder = f"{output_dir}/prompt-powered"
    else:
        folder = f"{output_dir}/generated"
    
    # Create folder if needed
    os.makedirs(folder, exist_ok=True)
    
    # Generate filename
    slug = self.slugify(requirement)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{index:02d}_{slug}_{timestamp}.cy.js"
    filepath = f"{folder}/{filename}"
    
    # Write file with header comment
    with open(filepath, 'w') as f:
        test_type = 'cy.prompt()' if use_prompt else 'Traditional'
        f.write(f"// Requirement: {requirement}\n")
        f.write(f"// Test Type: {test_type}\n\n")
        f.write(content)
    
    return {
        "requirement": requirement,
        "filepath": filepath,
        "filename": filename,
        "test_type": test_type
    }
```

**When to use**: File operations that depend on test type

## Error Handling Strategies

### Strategy 1: Mode-Specific Error Handling

Handle errors specific to each test type:

```python
def generate_tests_node(state: TestGenerationState) -> TestGenerationState:
    """Generate tests with mode-specific error handling"""
    generator = HybridTestGenerator()
    generated = []
    
    for requirement in state.requirements:
        try:
            content = generator.generate_test_content(
                requirement=requirement,
                context=state.docs_context,
                use_prompt=state.use_prompt
            )
            
            # Validate generated content
            if state.use_prompt:
                # Check for cy.prompt() syntax
                if 'cy.prompt' not in content:
                    raise ValueError("cy.prompt() not found in generated test")
            else:
                # Check for traditional Cypress commands
                if 'cy.get' not in content and 'cy.visit' not in content:
                    raise ValueError("No Cypress commands found")
            
            result = generator.save_test_file(
                content=content,
                requirement=requirement,
                output_dir=state.output_dir,
                use_prompt=state.use_prompt,
                index=len(generated) + 1
            )
            
            generated.append(result)
            
        except Exception as e:
            test_type = "cy.prompt()" if state.use_prompt else "traditional"
            print(f"Error generating {test_type} test: {e}")
            state.error = str(e)
    
    state.generated_tests = generated
    return state
```

### Strategy 2: Configuration Validation

Validate required configuration for cy.prompt():

```python
def validate_config_node(state: TestGenerationState) -> TestGenerationState:
    """Validate configuration based on test type"""
    
    if state.use_prompt:
        # Check Cypress config for cy.prompt support
        config_path = "./cypress.config.js"
        
        if not os.path.exists(config_path):
            state.error = "cypress.config.js not found"
            return state
        
        with open(config_path, 'r') as f:
            config_content = f.read()
            
        if 'experimentalCypressPrompt' not in config_content:
            print("Warning: experimentalCypressPrompt not enabled")
    
    return state
```

### Strategy 3: Graceful Degradation

Fallback to traditional tests if cy.prompt fails:

```python
def generate_with_fallback(state: TestGenerationState) -> TestGenerationState:
    """Generate with fallback to traditional if cy.prompt fails"""
    
    if state.use_prompt:
        try:
            result = generate_prompt_tests(state)
        except Exception as e:
            print(f"cy.prompt generation failed: {e}")
            print("Falling back to traditional tests")
            state.use_prompt = False
            result = generate_traditional_tests(state)
    else:
        result = generate_traditional_tests(state)
    
    return result
```

## Integration Patterns

### LLM Integration with Dual Templates

Best practices for integrating LLMs with mode-specific prompts:

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class HybridTestGenerator:
    """Generate both traditional and cy.prompt() tests"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0  # Deterministic for code generation
        )
    
    def create_traditional_test_prompt(self) -> str:
        """Prompt for traditional Cypress tests"""
        return """You are an expert Cypress test automation engineer.

Generate a complete Cypress test file.

REQUIREMENT: {requirement}
CONTEXT: {context}

GUIDELINES:
- Use Cypress best practices
- Use explicit selectors
- Include clear assertions
- Return ONLY JavaScript code

Generate ONLY the test code, no explanations."""
    
    def create_prompt_powered_test_prompt(self) -> str:
        """Prompt for cy.prompt() tests"""
        return """You are an expert with cy.prompt() expertise.

Generate a Cypress test using cy.prompt().

REQUIREMENT: {requirement}
CONTEXT: {context}

GUIDELINES FOR cy.prompt():
- Use natural language step arrays
- Example: "Visit the login page", "Click submit"
- Add critical assertions with traditional Cypress

Generate ONLY the test code, no explanations."""
    
    def generate_test_content(
        self,
        requirement: str,
        context: str = "",
        use_prompt: bool = False
    ) -> str:
        """Generate test using appropriate template"""
        
        # Select template
        template = (
            self.create_prompt_powered_test_prompt()
            if use_prompt
            else self.create_traditional_test_prompt()
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "requirement": requirement,
            "context": context or "No additional context"
        })
        
        return self._clean_response(response.content)
    
    def _clean_response(self, content: str) -> str:
        """Remove markdown code blocks"""
        if "```javascript" in content:
            content = content.split("```javascript")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content
```

**Key Points**:
- Maintain separate prompt templates for each mode
- Use temperature=0 for deterministic code generation
- Clean responses consistently regardless of mode
- Handle both template types with same method signature

### Vector Store Integration (Mode-Agnostic)

Vector store works the same for both test types:

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

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
                    with open(file_path, 'r') as f:
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

**Note**: Vector store context is used identically for both test types.

### External Tool Integration with Mode Awareness

Execute Cypress tests based on test type:

```python
import subprocess

def run_cypress_node(state: TestGenerationState) -> TestGenerationState:
    """Execute generated Cypress tests with mode awareness"""
    if not state.run_tests or not state.generated_tests:
        return state
    
    # Determine spec pattern based on test type
    if state.use_prompt:
        spec_pattern = "cypress/e2e/prompt-powered/**/*.cy.js"
        test_type = "cy.prompt()"
    else:
        spec_pattern = "cypress/e2e/generated/**/*.cy.js"
        test_type = "traditional"
    
    cmd = f"npx cypress run --spec '{spec_pattern}'"
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=300
        )
        
        state.execution_results = {
            "exit_code": result.returncode,
            "test_type": test_type,
            "passed": result.returncode == 0
        }
        
    except Exception as e:
        state.error = str(e)
    
    return state
```

## Debugging Workflows

### Enable Mode-Specific Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

def debug_node(state: TestGenerationState) -> TestGenerationState:
    """Node with debug logging including test type"""
    test_type = "cy.prompt()" if state.use_prompt else "Traditional"
    logging.debug(f"Test type: {test_type}")
    logging.debug(f"Requirements: {state.requirements}")
    
    result = process(state)
    
    logging.debug(f"Generated: {len(result.generated_tests)} tests")
    return result
```

### State Inspection with Mode Info

```python
def inspect_state(state: TestGenerationState) -> TestGenerationState:
    """Debugging node to inspect state with test type"""
    test_type = "cy.prompt()" if state.use_prompt else "Traditional"
    print(f"Test Type: {test_type}")
    print(f"Requirements: {state.requirements}")
    print(f"Generated Tests: {len(state.generated_tests)}")
    return state
```

## Performance Optimization

### Mode-Specific Optimizations

```python
def optimized_generate(state: TestGenerationState) -> TestGenerationState:
    """Optimized generation based on test type"""
    
    if state.use_prompt:
        # cy.prompt tests: Runtime AI calls happen during execution
        generator = HybridTestGenerator()
        generator.llm.temperature = 0
    else:
        # Traditional tests: No runtime AI, generation must be perfect
        generator = HybridTestGenerator()
        generator.llm.temperature = 0
        generator.llm.max_tokens = 2000
    
    return state
```

### Caching by Test Type

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_prompt_template(use_prompt: bool) -> str:
    """Cached prompt template retrieval"""
    generator = HybridTestGenerator()
    if use_prompt:
        return generator.create_prompt_powered_test_prompt()
    else:
        return generator.create_traditional_test_prompt()
```

## Testing Workflows

### Unit Testing Dual-Mode Nodes

```python
def test_parse_cli_traditional():
    """Test CLI parsing for traditional mode"""
    state = TestGenerationState(
        requirements=["Test login"],
        output_dir="cypress/e2e",
        use_prompt=False,
        docs_context=None,
        generated_tests=[],
        run_tests=False,
        error=None
    )
    
    result = parse_cli_node(state)
    assert result.use_prompt is False


def test_generate_tests_traditional():
    """Test traditional test generation"""
    state = TestGenerationState(
        requirements=["Test button click"],
        output_dir="/tmp/test",
        use_prompt=False,
        docs_context=None,
        generated_tests=[],
        run_tests=False,
        error=None
    )
    
    result = generate_tests_node(state)
    assert "generated" in result.generated_tests[0]['filepath']
```

## Best Practices Summary

1. **State Design**: Include `use_prompt` flag for mode selection
2. **Node Functions**: Respect test type throughout workflow
3. **Error Handling**: Handle mode-specific errors gracefully
4. **Logging**: Include test type in all log messages
5. **Testing**: Unit test both modes separately
6. **Performance**: Optimize based on test type characteristics

## Common Pitfalls

### Pitfall 1: Ignoring use_prompt Flag

```python
# BAD - Doesn't check test type
def bad_save(state):
    folder = f"{state.output_dir}/tests"  # Wrong!
    return state

# GOOD - Respects test type
def good_save(state):
    if state.use_prompt:
        folder = f"{state.output_dir}/prompt-powered"
    else:
        folder = f"{state.output_dir}/generated"
    return state
```

### Pitfall 2: Wrong Template Selection

```python
# BAD - Always uses same template
def bad_generate(state):
    template = TRADITIONAL_TEMPLATE  # Ignores mode!
    return state

# GOOD - Selects appropriate template
def good_generate(state):
    template = (
        PROMPT_TEMPLATE if state.use_prompt 
        else TRADITIONAL_TEMPLATE
    )
    return state
```

### Pitfall 3: Modifying use_prompt During Workflow

```python
# BAD - Changes test type mid-workflow
def bad_node(state):
    state.use_prompt = not state.use_prompt  # Don't do this!
    return state

# GOOD - use_prompt is immutable after CLI parsing
def good_node(state):
    test_type = "cy.prompt()" if state.use_prompt else "Traditional"
    # Work with the chosen type
    return state
```

## Additional Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangChain Guides**: https://python.langchain.com/docs/use_cases
- **Cypress cy.prompt() Docs**: https://docs.cypress.io/api/commands/prompt
- **State Machine Patterns**: https://en.wikipedia.org/wiki/Finite-state_machine