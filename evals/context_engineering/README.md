# Context Engineering Evaluations

This directory contains evaluations for Jean Memory's context engineering capabilities - the core intelligence that determines what context to provide and how to present it.

## Overview

Context engineering is critical to Jean Memory's value proposition. Poor context leads to:
- AI responses that lack personal relevance
- Generic responses that could come from any chatbot
- Missed opportunities to leverage user's specific knowledge/preferences

Excellent context engineering results in:
- Highly personalized AI interactions
- Responses that feel like they come from someone who knows you
- Efficient use of context window with high signal-to-noise ratio

## Evaluation Categories

### 1. Context Quality Scoring (`quality_scoring.py`)
Measures the overall quality of generated context packages:

**Metrics:**
- **Relevance** (40%): How well does context match the user query?
- **Completeness** (30%): Are key background details included?
- **Personalization** (20%): Does it reflect user's specific situation?
- **Noise Penalty** (10%): Penalty for irrelevant information

**Target**: > 90% context quality score

### 2. Relevance Testing (`relevance_tests.py`)
Deep evaluation of context relevance across different query types:

**Query Categories:**
- Personal questions ("What are my goals?")
- Technical questions ("Help me with Python")
- Decision-making ("Should I take this job?")
- Creative requests ("Help me write...")

**Evaluation**: Expert human rating + AI-assisted scoring

### 3. Golden Dataset Evaluation (`golden_datasets/`)
Curated test scenarios with expected context outcomes:

**Dataset Structure:**
```json
{
  "scenario_id": "new_conversation_software_engineer",
  "user_message": "Hi, I'm starting a new project and need advice",
  "user_context": {
    "profession": "software_engineer",
    "recent_projects": ["AI chatbot", "React app"],
    "preferences": ["TypeScript", "clean architecture"]
  },
  "expected_context_elements": [
    "User is a software engineer",
    "Has experience with AI and React",
    "Prefers TypeScript and clean architecture"
  ],
  "context_strategy": "new_conversation",
  "quality_threshold": 85
}
```

### 4. Client Contract Testing (`client_contract_tests.py`)
Ensures context responses follow the expected contract and don't inject unwanted personas:

**Tests:**
- `needs_context=false` returns appropriate "no context" message
- New conversations get life narrative when available
- Context format is consistent and parseable
- No AI persona injection ("As an AI assistant...")

## Key Test Scenarios

### Scenario 1: New Conversation Detection
```python
test_cases = [
    {
        "message": "Hello! I'm Jonathan, a software engineer.",
        "is_new_conversation": True,
        "expected_strategy": "life_narrative",
        "expected_elements": ["user background", "professional context"]
    },
    {
        "message": "What did we discuss about my Python project?",
        "is_new_conversation": False,
        "expected_strategy": "targeted_search",
        "expected_elements": ["Python project details", "previous discussion"]
    }
]
```

### Scenario 2: Context Strategy Selection
```python
strategy_tests = [
    {
        "query": "Tell me about my career goals",
        "expected_strategy": "comprehensive_analysis",
        "context_depth": "deep"
    },
    {
        "query": "What's 2+2?",
        "expected_strategy": "no_context",
        "context_depth": "none"
    },
    {
        "query": "Help me with this React component",
        "expected_strategy": "relevant_context", 
        "context_depth": "targeted"
    }
]
```

### Scenario 3: Context Quality Measurement
```python
quality_metrics = {
    "relevance": {
        "high": "Context directly relates to user query",
        "medium": "Context provides useful background",
        "low": "Context is tangentially related",
        "none": "Context is unrelated to query"
    },
    "completeness": {
        "high": "All necessary context included",
        "medium": "Most key context included", 
        "low": "Some important context missing",
        "none": "Critical context missing"
    },
    "personalization": {
        "high": "Highly specific to this user",
        "medium": "Somewhat personalized",
        "low": "Generic with some personal touches",
        "none": "Could apply to anyone"
    }
}
```

## Running Context Engineering Evals

### Basic Usage
```bash
# Run all context engineering evaluations
python -m evals.context_engineering.run_all

# Run specific evaluation
python -m evals.context_engineering.quality_scoring --user-id test-user

# Run with custom dataset
python -m evals.context_engineering.relevance_tests --dataset custom_scenarios.json
```

### Advanced Configuration
```bash
# Run with different context strategies
python -m evals.context_engineering.quality_scoring --strategy deep_analysis

# Test specific client integrations
python -m evals.context_engineering.client_contract_tests --client claude

# Generate detailed reports
python -m evals.context_engineering.run_all --output-format detailed --save-results
```

## Integration with Main System

These evaluations test the actual production orchestrator:

```python
from app.mcp_orchestration import get_smart_orchestrator
from app.tools.orchestration import jean_memory

# Test real orchestrator
orchestrator = get_smart_orchestrator()
context = await orchestrator.orchestrate_smart_context(
    user_message="Help me with my Python project",
    user_id="test-user-123", 
    client_name="claude",
    is_new_conversation=False
)

# Evaluate context quality
quality_score = evaluate_context_quality(context, expected_elements)
```

## Expected Outcomes

### Phase 1: Baseline Measurement
- Establish current context quality scores
- Identify common failure patterns
- Create golden dataset of 100+ scenarios

### Phase 2: Optimization
- Improve context quality scores to >90%
- Reduce irrelevant context by 50%
- Optimize for different conversation types

### Phase 3: Advanced Intelligence
- Implement context adaptation based on conversation flow
- Add proactive context suggestions
- Build context quality feedback loops

## Contributing

When adding new context engineering evaluations:

1. **Create clear test scenarios** with expected outcomes
2. **Include diverse query types** (personal, technical, creative, etc.)
3. **Add both automated and human evaluation** methods
4. **Document scoring methodology** clearly
5. **Test edge cases** (empty context, very long context, etc.)

The goal is to make Jean Memory's context engineering so intelligent that users feel like they're talking to someone who truly knows them.