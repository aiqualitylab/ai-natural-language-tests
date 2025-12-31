---
name: langgraph-workflow-development
description: Guide for LangGraph workflows in AI-powered test automation. Covers state management, workflow nodes, and dual-mode test generation with test data options.
license: MIT
---

# LangGraph Workflow Development Skill

Build and debug LangGraph workflows for Cypress test generation.

## Workflow Pipeline

```
ParseCLI -> LoadContext -> GenerateTests -> RunCypress -> END
```

- **ParseCLI**: Parse args, identify test type
- **LoadContext**: Fetch URL data, load JSON, index docs
- **GenerateTests**: AI generates tests based on mode
- **RunCypress**: Execute tests if `--run` flag set

## State Schema

```python
@dataclass
class TestGenerationState:
    requirements: List[str]
    output_dir: str
    use_prompt: bool           # Traditional vs cy.prompt()
    docs_context: Optional[str] # Combined: docs + URL + JSON data
    generated_tests: List[Dict[str, Any]]
    run_tests: bool
    error: Optional[str]
```

**Key fields**:
- `use_prompt`: Determines template and output folder
- `docs_context`: Accumulates all context sources

## Building Workflow

```python
from langgraph.graph import StateGraph, END

def create_workflow() -> StateGraph:
    workflow = StateGraph(TestGenerationState)
    
    workflow.add_node("parse_cli", parse_cli_node)
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("generate_tests", generate_tests_node)
    workflow.add_node("run_cypress", run_cypress_node)
    
    workflow.set_entry_point("parse_cli")
    workflow.add_edge("parse_cli", "load_context")
    workflow.add_edge("load_context", "generate_tests")
    workflow.add_edge("generate_tests", "run_cypress")
    workflow.add_edge("run_cypress", END)
    
    return workflow.compile()
```

## Node Pattern

```python
def generate_tests_node(state: TestGenerationState) -> TestGenerationState:
    generator = HybridTestGenerator()
    
    for idx, req in enumerate(state.requirements, 1):
        content = generator.generate_test_content(
            requirement=req,
            context=state.docs_context or "",
            use_prompt=state.use_prompt  # Selects template
        )
        
        result = generator.save_test_file(
            content=content,
            output_dir=state.output_dir,
            use_prompt=state.use_prompt,  # Selects folder
            index=idx
        )
        state.generated_tests.append(result)
    
    return state
```

## Mode-Specific Logic

```python
# Template selection
if state.use_prompt:
    template = create_prompt_powered_test_prompt()
else:
    template = create_traditional_test_prompt()

# Folder selection
if state.use_prompt:
    folder = f"{output_dir}/prompt-powered"
else:
    folder = f"{output_dir}/generated"

# Test execution
if state.use_prompt:
    spec = "cypress/e2e/prompt-powered/**/*.cy.js"
else:
    spec = "cypress/e2e/generated/**/*.cy.js"
```

## Test Data Integration

Context flows from multiple sources into `docs_context`:

```python
# URL analysis
if args.url:
    context, data, path = generate_test_data_from_url(args.url)
    test_data_context += context

# JSON file
if args.data:
    with open(args.data) as f:
        data = json.load(f)
    test_data_context += f"TEST DATA: {json.dumps(data)}"

# Documentation
if args.docs:
    docs_context = loader.get_relevant_context(vector_store, query)

# Combine all
full_context = (docs_context or "") + test_data_context
```

## Error Handling

```python
def node_with_error_handling(state):
    try:
        # Process
        result = process(state)
        return result
    except Exception as e:
        state.error = str(e)
        return state
```

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Ignoring `use_prompt` | Always check flag for template/folder selection |
| Not combining context | Merge docs + URL + JSON into `docs_context` |
| Modifying `use_prompt` mid-workflow | Keep immutable after CLI parsing |
| Missing fixture save | URL analysis must save to `cypress/fixtures/` |

## Debugging

```python
def debug_state(state):
    print(f"Mode: {'cy.prompt()' if state.use_prompt else 'Traditional'}")
    print(f"Context: {'Yes' if state.docs_context else 'No'}")
    print(f"Generated: {len(state.generated_tests)}")
    return state
```