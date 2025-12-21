---
name: langgraph-workflow-development
description: Guide for building and debugging LangGraph workflows for AI orchestration. Use this when creating, modifying, or troubleshooting LangGraph state machines and workflow graphs.
license: MIT
---

# LangGraph Workflow Development Skill

This skill provides specialized knowledge for working with LangGraph workflows in the context of AI-powered test automation. Use this skill when building or modifying the orchestration layer that manages the test generation pipeline.

## When to Use This Skill

Use this skill when you need to:
- Create new LangGraph workflow nodes
- Modify the workflow state schema
- Add conditional branching to the workflow
- Debug workflow execution issues
- Optimize workflow performance
- Add error handling and retry logic
- Integrate new tools or APIs into the workflow

## LangGraph Core Concepts

### State Management

LangGraph uses typed dictionaries to manage state flow:

```python
from typing import TypedDict, Optional, List, Any

class AutomationState(TypedDict):
    # Input parameters
    requirements: List[str]
    output_dir: str
    run_tests: bool
    docs_dir: Optional[str]
    persist_vstore: bool
    
    # Intermediate state
    vectorstore: Optional[Any]
    generated_code: Optional[str]
    
    # Output state
    generated_files: List[str]
    execution_results: Optional[dict]
```

**Best Practices for State Design**:
- Use `TypedDict` for type safety and IDE support
- Mark optional fields with `Optional[Type]`
- Group related fields logically (inputs, intermediate, outputs)
- Use descriptive field names that reflect the workflow domain
- Avoid deeply nested structures - flatten when possible

### Workflow Nodes

Nodes are pure functions that transform state:

```python
def node_name(state: AutomationState) -> AutomationState:
    """
    Brief description of what this node does.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with modifications
    """
    # Validate inputs
    if not state.get("required_field"):
        raise ValueError("Missing required_field")
    
    # Perform transformation
    result = process_data(state["input_data"])
    
    # Update and return state
    state["output_data"] = result
    return state
```

**Node Development Guidelines**:
- Keep nodes focused on single responsibilities
- Always return the complete state object
- Add validation at the start of each node
- Include comprehensive docstrings
- Handle errors gracefully with try-except
- Log important state transitions

### Building the Workflow Graph

```python
from langgraph.graph import StateGraph

# Initialize graph with state schema
workflow = StateGraph(AutomationState)

# Add nodes
workflow.add_node("parse_input", parse_input_node)
workflow.add_node("process_data", process_data_node)
workflow.add_node("generate_output", generate_output_node)

# Define sequential flow
workflow.add_edge("parse_input", "process_data")
workflow.add_edge("process_data", "generate_output")

# Set entry point
workflow.set_entry_point("parse_input")

# Compile the graph
app = workflow.compile()
```

## Common Workflow Patterns

### Pattern 1: Sequential Processing

Simple linear workflow for straightforward pipelines:

```python
workflow = StateGraph(AutomationState)

workflow.add_node("step1", step1_function)
workflow.add_node("step2", step2_function)
workflow.add_node("step3", step3_function)

workflow.add_edge("step1", "step2")
workflow.add_edge("step2", "step3")

workflow.set_entry_point("step1")
```

**When to use**: Simple pipelines with no branching or conditional logic

### Pattern 2: Conditional Branching

Workflow that routes based on state:

```python
def should_use_vectorstore(state: AutomationState) -> str:
    """Decide whether to build vector store."""
    if state.get("docs_dir"):
        return "build_vectorstore"
    return "generate_tests"

workflow = StateGraph(AutomationState)

workflow.add_node("parse_cli", parse_cli)
workflow.add_node("build_vectorstore", build_vectorstore)
workflow.add_node("generate_tests", generate_tests)

# Add conditional edge
workflow.add_conditional_edges(
    "parse_cli",
    should_use_vectorstore,
    {
        "build_vectorstore": "build_vectorstore",
        "generate_tests": "generate_tests"
    }
)

workflow.add_edge("build_vectorstore", "generate_tests")
workflow.set_entry_point("parse_cli")
```

**When to use**: Workflows with optional steps or different execution paths

### Pattern 3: Parallel Processing

Execute multiple nodes concurrently (advanced):

```python
from langgraph.graph import StateGraph
from typing import List

class ParallelState(TypedDict):
    requirements: List[str]
    results: List[dict]

def parallel_process(state: ParallelState) -> ParallelState:
    """Process multiple requirements in parallel."""
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_requirement, req)
            for req in state["requirements"]
        ]
        results = [f.result() for f in futures]
    
    state["results"] = results
    return state
```

**When to use**: Independent operations that can run concurrently

### Pattern 4: Loop with Conditional Exit

Workflow that repeats until a condition is met:

```python
def should_continue(state: AutomationState) -> str:
    """Check if we should retry generation."""
    if state.get("validation_passed"):
        return "complete"
    if state["retry_count"] >= 3:
        return "complete"
    return "generate_tests"

workflow.add_conditional_edges(
    "validate_tests",
    should_continue,
    {
        "generate_tests": "generate_tests",
        "complete": "complete"
    }
)
```

**When to use**: Retry logic or iterative refinement

## Error Handling Strategies

### Strategy 1: Try-Except in Nodes

Handle expected errors within nodes:

```python
def generate_tests(state: AutomationState) -> AutomationState:
    """Generate tests with error handling."""
    try:
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        response = llm.invoke(state["prompt"])
        state["generated_code"] = response.content
        state["error"] = None
        
    except Exception as e:
        state["generated_code"] = None
        state["error"] = str(e)
        print(f"ERROR in generate_tests: {e}")
    
    return state
```

### Strategy 2: Error Recovery Nodes

Dedicated nodes for error handling:

```python
def handle_error(state: AutomationState) -> AutomationState:
    """Handle errors from previous nodes."""
    error = state.get("error")
    
    if "rate_limit" in error:
        print("Rate limit hit, waiting 60 seconds...")
        time.sleep(60)
        state["should_retry"] = True
    else:
        print(f"Unrecoverable error: {error}")
        state["should_retry"] = False
    
    state["error"] = None
    return state

def should_retry(state: AutomationState) -> str:
    """Determine if we should retry after error."""
    if state.get("should_retry"):
        return "retry"
    return "fail"

workflow.add_conditional_edges(
    "error_handler",
    should_retry,
    {"retry": "generate_tests", "fail": "end"}
)
```

### Strategy 3: Validation Nodes

Validate state before proceeding:

```python
def validate_state(state: AutomationState) -> AutomationState:
    """Validate state contains required fields."""
    required_fields = ["requirements", "output_dir"]
    
    for field in required_fields:
        if field not in state or not state[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate types
    if not isinstance(state["requirements"], list):
        raise TypeError("requirements must be a list")
    
    return state
```

## Integration Patterns

### LLM Integration

Best practices for integrating LLMs into workflows:

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

def llm_generate_node(state: AutomationState) -> AutomationState:
    """Generate content using LLM."""
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,  # Deterministic for code generation
        max_tokens=2000,
        timeout=30
    )
    
    # Create prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a test automation expert."),
        ("user", "{requirement}")
    ])
    
    # Create chain
    chain = prompt_template | llm
    
    # Generate for each requirement
    generated = []
    for req in state["requirements"]:
        try:
            response = chain.invoke({"requirement": req})
            generated.append(response.content)
        except Exception as e:
            print(f"Error generating for '{req}': {e}")
            generated.append(None)
    
    state["generated_code"] = generated
    return state
```

**Key Points**:
- Use appropriate temperature (0 for code, higher for creative tasks)
- Set reasonable timeouts
- Handle per-item errors gracefully
- Use chains for reusable prompt logic

### Vector Store Integration

Integrate ChromaDB for context retrieval:

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader

def build_vectorstore(state: AutomationState) -> AutomationState:
    """Build vector store from documentation."""
    docs_dir = state.get("docs_dir")
    
    if not docs_dir:
        state["vectorstore"] = None
        return state
    
    # Check if persisted store exists
    persist_dir = "./vector_store"
    
    if os.path.exists(persist_dir) and not state.get("persist_vstore"):
        # Load existing store
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
    else:
        # Create new store
        loader = DirectoryLoader(docs_dir, glob="**/*")
        documents = loader.load()
        
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_dir
        )
    
    state["vectorstore"] = vectorstore
    return state

def retrieve_context(state: AutomationState) -> AutomationState:
    """Retrieve relevant context for requirements."""
    vectorstore = state.get("vectorstore")
    
    if not vectorstore:
        state["context"] = [""] * len(state["requirements"])
        return state
    
    contexts = []
    for req in state["requirements"]:
        docs = vectorstore.similarity_search(req, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        contexts.append(context)
    
    state["context"] = contexts
    return state
```

### External Tool Integration

Call external tools like Cypress:

```python
import subprocess
from pathlib import Path

def run_cypress(state: AutomationState) -> AutomationState:
    """Execute generated Cypress tests."""
    if not state.get("run_tests"):
        state["execution_results"] = None
        return state
    
    results = []
    for filepath in state["generated_files"]:
        try:
            result = subprocess.run(
                ["npx", "cypress", "run", "--spec", filepath],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            results.append({
                "file": filepath,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0
            })
            
        except subprocess.TimeoutExpired:
            results.append({
                "file": filepath,
                "error": "Test execution timeout"
            })
        except Exception as e:
            results.append({
                "file": filepath,
                "error": str(e)
            })
    
    state["execution_results"] = results
    return state
```

## Debugging Workflows

### Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_node(state: AutomationState) -> AutomationState:
    """Node with debug logging."""
    logging.debug(f"Entering debug_node with state keys: {state.keys()}")
    logging.debug(f"Requirements: {state.get('requirements')}")
    
    # Process
    result = process(state)
    
    logging.debug(f"Exiting debug_node, added keys: {result.keys() - state.keys()}")
    return result
```

### State Inspection

```python
def inspect_state(state: AutomationState) -> AutomationState:
    """Debugging node to inspect state."""
    print("=" * 80)
    print("STATE INSPECTION")
    print("=" * 80)
    
    for key, value in state.items():
        if isinstance(value, (str, int, bool)):
            print(f"{key}: {value}")
        elif isinstance(value, list):
            print(f"{key}: List with {len(value)} items")
        else:
            print(f"{key}: {type(value).__name__}")
    
    print("=" * 80)
    return state

# Add to workflow for debugging
workflow.add_node("inspect", inspect_state)
workflow.add_edge("some_node", "inspect")
workflow.add_edge("inspect", "next_node")
```

### Visualization

Generate visual representation of the workflow:

```python
# After compiling the workflow
app = workflow.compile()

# Generate Mermaid diagram
mermaid_diagram = app.get_graph().draw_mermaid()
print(mermaid_diagram)

# Save to file
with open("workflow_diagram.mmd", "w") as f:
    f.write(mermaid_diagram)
```

## Performance Optimization

### Caching Expensive Operations

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def load_vectorstore(persist_dir: str):
    """Cached vector store loading."""
    embeddings = OpenAIEmbeddings()
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

def use_cached_vectorstore(state: AutomationState) -> AutomationState:
    """Use cached vector store instance."""
    vectorstore = load_vectorstore("./vector_store")
    state["vectorstore"] = vectorstore
    return state
```

### Batch Processing

```python
def batch_generate(state: AutomationState) -> AutomationState:
    """Generate tests in batches for better performance."""
    requirements = state["requirements"]
    batch_size = 5
    
    all_generated = []
    
    for i in range(0, len(requirements), batch_size):
        batch = requirements[i:i + batch_size]
        
        # Process batch
        batch_prompt = create_batch_prompt(batch)
        response = llm.invoke(batch_prompt)
        
        # Parse response into individual tests
        generated = parse_batch_response(response.content, len(batch))
        all_generated.extend(generated)
    
    state["generated_code"] = all_generated
    return state
```

## Testing Workflows

### Unit Testing Nodes

```python
import pytest

def test_parse_cli_node():
    """Test CLI parsing node."""
    # Arrange
    initial_state = {
        "raw_args": ["Test login", "--run"],
        "requirements": [],
        "run_tests": False
    }
    
    # Act
    result = parse_cli(initial_state)
    
    # Assert
    assert result["requirements"] == ["Test login"]
    assert result["run_tests"] is True

def test_generate_tests_node():
    """Test test generation node."""
    state = {
        "requirements": ["Test button click"],
        "output_dir": "/tmp/test",
        "generated_files": []
    }
    
    result = generate_tests(state)
    
    assert len(result["generated_files"]) == 1
    assert result["generated_files"][0].endswith(".cy.js")
```

### Integration Testing

```python
def test_full_workflow():
    """Test complete workflow execution."""
    # Setup
    workflow = create_workflow()
    app = workflow.compile()
    
    initial_state = {
        "requirements": ["Test sample scenario"],
        "output_dir": "./test_output",
        "run_tests": False,
        "docs_dir": None,
        "persist_vstore": False,
        "generated_files": []
    }
    
    # Execute
    final_state = app.invoke(initial_state)
    
    # Verify
    assert len(final_state["generated_files"]) > 0
    assert os.path.exists(final_state["generated_files"][0])
```

## Best Practices Summary

1. **State Design**: Keep state flat and well-typed
2. **Node Functions**: Single responsibility, pure functions
3. **Error Handling**: Graceful degradation, informative errors
4. **Logging**: Strategic logging for debugging
5. **Testing**: Unit test nodes, integration test workflows
6. **Performance**: Cache expensive operations, batch when possible
7. **Documentation**: Clear docstrings and comments

## Common Pitfalls

### Pitfall 1: Mutating Shared Objects

```python
# BAD - Mutates shared list
def bad_node(state: AutomationState) -> AutomationState:
    shared_list = state["shared_list"]
    shared_list.append("new_item")  # Mutates original
    return state

# GOOD - Creates new list
def good_node(state: AutomationState) -> AutomationState:
    state["shared_list"] = state["shared_list"] + ["new_item"]
    return state
```

### Pitfall 2: Missing State Updates

```python
# BAD - Forgets to update state
def bad_node(state: AutomationState) -> AutomationState:
    result = expensive_operation()
    return state  # Lost the result!

# GOOD - Updates state with result
def good_node(state: AutomationState) -> AutomationState:
    result = expensive_operation()
    state["result"] = result
    return state
```

### Pitfall 3: Blocking Operations

```python
# BAD - Blocks for long time
def bad_node(state: AutomationState) -> AutomationState:
    time.sleep(300)  # 5 minute sleep
    return state

# GOOD - Async or timeout
import asyncio

async def good_node(state: AutomationState) -> AutomationState:
    await asyncio.sleep(0.1)  # Non-blocking
    return state
```

## Additional Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangChain Guides**: https://python.langchain.com/docs/use_cases
- **State Machine Patterns**: https://en.wikipedia.org/wiki/Finite-state_machine
