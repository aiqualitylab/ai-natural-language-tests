---
name: langgraph-workflow-development
description: Guide for LangGraph workflows in AI-powered test automation
LangGraph workflows in AI-powered test automation license: GNU AFFERO GENERAL PUBLIC LICENSE
---

# LangGraph Workflow Development Skill

## Workflow Pipeline

```
Step2FetchData -> Step3SearchPatterns -> Step4GenerateTests -> Step5RunTests(optional) -> END
```

## State Schema

```python
@dataclass
class TestState:
    requirements: List[str]
    output_dir: str
    use_prompt: bool
    approve: bool = False
    framework: str = "cypress"
    url: Optional[str] = None
    run_tests: bool
    llm_provider: str = "openai"
    test_data: Optional[Dict] = None
    context: str = ""
    similar_patterns: List = field(default_factory=list)
    generated_tests: List = field(default_factory=list)
    test_results: Optional[Dict] = None
    run_id: str = ""
```

## Building Workflow

```python
from langgraph.graph import StateGraph, END

def create_workflow() -> StateGraph:
    workflow = StateGraph(TestState)
    
    workflow.add_node("step_2", step_2_fetch_test_data)
    workflow.add_node("step_3", step_3_search_similar_patterns)
    workflow.add_node("step_4", step_4_generate_tests)
    workflow.add_node("step_5", step_5_run_tests)
    
    workflow.set_entry_point("step_2")
    workflow.add_edge("step_2", "step_3")
    workflow.add_edge("step_3", "step_4")
    workflow.add_conditional_edges("step_4", should_run_tests, {"run_tests": "step_5", END: END})
    workflow.add_edge("step_5", END)
    
    return workflow.compile(checkpointer=WORKFLOW_CHECKPOINTER)
```

## Node Pattern

```python
def step_4_generate_tests(state: TestState) -> TestState:
    # Current implementation uses RunnableLambda for prompt generation
    # and BaseOutputParser for code-fence extraction before file save.
    return state
```

## Mode Selection

```python
# Prompt mode applies only when framework supports it (currently Cypress)
use_prompt_mode = state.use_prompt and FRAMEWORK_CONFIG[state.framework]["supports_prompt_mode"]
```

## Context Sources

```python
# URL analysis in step_2 builds test_data and context block
# Similar pattern retrieval in step_3 augments context
# Final context is consumed by step_4 prompt template rendering
```

## Error Handling

```python
def node_with_error_handling(state):
    try:
        result = process(state)
        return result
    except Exception as e:
        state.error = str(e)
        return state
```