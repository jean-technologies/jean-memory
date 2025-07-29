# Jean Memory Evaluation Framework

This directory contains comprehensive evaluations for Jean Memory's intelligent orchestration and agentic memory systems.

## Framework Overview

Our evaluation strategy is based on the [V2 Testing Strategy](../docs/new/JEAN_MEMORY_TESTING_STRATEGY_V2.md) and focuses on four key areas:

### 1. Performance Metrics (Target P95)
- **Fast Path Latency**: < 3 seconds (user-facing response)
- **Deep Analysis Latency**: < 60 seconds (background processing)
- **Timeout Resilience**: 100% (graceful degradation)

### 2. Quality Metrics
- **Context Quality Score**: > 90% (relevance and usefulness)
- **Memory Triage Accuracy**: > 95% (remember vs skip decisions)
- **Client Contract Adherence**: 100% (no persona injection)

## Directory Structure

```
evals/
├── README.md                          # This file
├── context_engineering/               # Context quality and relevance tests
│   ├── README.md
│   ├── golden_datasets/              # Curated test scenarios
│   ├── quality_scoring.py            # Context quality evaluation
│   └── relevance_tests.py            # Context relevance evaluation
├── memory_intelligence/              # Memory triage and synthesis tests
│   ├── README.md
│   ├── triage_accuracy.py           # Remember vs Skip accuracy
│   ├── synthesis_quality.py         # Memory combination quality
│   └── golden_memories.json         # Labeled memory examples
├── performance/                      # Latency and resilience tests
│   ├── README.md
│   ├── fast_path_benchmarks.py     # < 3 second response tests
│   ├── resilience_tests.py         # Failure simulation tests
│   └── load_testing.py             # System under load tests
├── agentic_behavior/                # Proactive memory and intelligence tests
│   ├── README.md
│   ├── proactive_memory.py         # Background analysis quality
│   ├── connection_synthesis.py     # Memory relationship building
│   └── adaptive_context.py         # Context adaptation tests
└── utils/                          # Shared evaluation utilities
    ├── __init__.py
    ├── eval_framework.py           # Base evaluation classes
    ├── metrics.py                  # Scoring and measurement tools
    └── test_data_generator.py      # Synthetic data generation
```

## Key Evaluation Types

### 1. Context Engineering Evals
Test the quality and relevance of context provided to AI models:
- **Relevance Scoring**: How well does context match the user query?
- **Completeness**: Does context include necessary background information?
- **Noise Ratio**: How much irrelevant information is included?
- **Personalization**: Does context reflect user's specific preferences/history?

### 2. Memory Intelligence Evals
Evaluate the smart triage and synthesis of memories:
- **Triage Accuracy**: Binary classification (remember vs skip) against golden dataset
- **Synthesis Quality**: How well are related memories combined and summarized?
- **Factual Consistency**: Are synthesized memories factually accurate?
- **Priority Classification**: Are important memories properly prioritized?

### 3. Performance Evals
Measure system performance under various conditions:
- **Fast Path Latency**: Time to first response
- **Deep Analysis Completion**: Background processing time
- **Failure Recovery**: Graceful degradation when components fail
- **Concurrent Load**: Performance under multiple simultaneous requests

### 4. Agentic Behavior Evals
Test proactive and intelligent behavior:
- **Proactive Memory Saving**: Automatically identifying valuable information
- **Context Adaptation**: Adjusting context strategy based on conversation type
- **Memory Connection**: Building relationships between related memories
- **Learning Over Time**: Improving performance with more data

## Running Evaluations

### Quick Start
```bash
# Run all evaluations
python -m evals.run_all

# Run specific category
python -m evals.context_engineering.quality_scoring
python -m evals.memory_intelligence.triage_accuracy

# Run with specific test user
python -m evals.context_engineering.quality_scoring --user-id test-user-123
```

### Continuous Integration
Evaluations are integrated into the CI/CD pipeline:
- **PR Checks**: Basic performance and quality thresholds
- **Daily Runs**: Full evaluation suite with detailed reporting
- **Regression Detection**: Alert on quality/performance degradation

## Evaluation Metrics

### Context Quality Score (0-100)
```python
context_score = (
    relevance_score * 0.4 +      # How relevant to the query
    completeness_score * 0.3 +    # Includes necessary context
    personalization_score * 0.2 + # Reflects user's specific context
    noise_penalty * 0.1           # Penalty for irrelevant information
)
```

### Memory Triage Accuracy (0-100)
```python
triage_accuracy = (
    correct_remember_decisions + correct_skip_decisions
) / total_decisions * 100
```

### Performance Score (0-100)
```python
performance_score = (
    fast_path_score * 0.5 +       # < 3s response time
    resilience_score * 0.3 +      # Graceful failure handling
    throughput_score * 0.2        # Concurrent request handling
)
```

## Contributing

When adding new evaluations:

1. **Follow the structure**: Place tests in appropriate category folders
2. **Include documentation**: Add README.md explaining the evaluation
3. **Use golden datasets**: Include curated test data with expected outcomes
4. **Add CI integration**: Ensure tests run in continuous integration
5. **Document metrics**: Clearly explain scoring methodology

## Integration with Testing Strategy

This evaluation framework directly implements the testing suites from our V2 strategy:

- **Suite 1 (Performance)** → `performance/` directory
- **Suite 2 (Quality)** → `context_engineering/` + `memory_intelligence/`
- **Suite 3 (Resilience)** → `performance/resilience_tests.py`
- **Suite 4 (Client Contract)** → `context_engineering/client_contract_tests.py`

Each evaluation provides actionable insights for improving Jean Memory's intelligence and reliability.