# Memory Intelligence Evaluations

This directory contains evaluations for Jean Memory's intelligent memory triage and synthesis capabilities.

## Overview

Memory intelligence is crucial for Jean Memory's effectiveness. The system must:
- **Accurately triage** which messages are worth remembering vs skipping
- **Synthesize memories** by combining related information intelligently  
- **Prioritize memories** based on importance and relevance
- **Maintain factual consistency** when processing and combining memories

Poor memory intelligence leads to:
- Information overload from saving irrelevant messages
- Loss of important personal information
- Fragmented memories that don't build coherent understanding
- Inconsistent or contradictory stored information

Excellent memory intelligence results in:
- High-quality, curated personal knowledge base
- Efficient storage with high signal-to-noise ratio
- Rich, interconnected understanding of the user
- Consistent and reliable memory retrieval

## Evaluation Categories

### 1. Memory Triage Accuracy (`triage_accuracy.py`)
Tests the binary classification accuracy of remember vs skip decisions:

**Target**: > 95% accuracy on golden dataset

**Metrics:**
- **True Positives**: Correctly identified memorable messages
- **True Negatives**: Correctly identified skippable messages  
- **False Positives**: Incorrectly saved non-memorable messages
- **False Negatives**: Incorrectly skipped memorable messages
- **Precision**: TP / (TP + FP) - quality of remember decisions
- **Recall**: TP / (TP + FN) - coverage of memorable content
- **F1 Score**: Harmonic mean of precision and recall

### 2. Memory Synthesis Quality (`synthesis_quality.py`)
Evaluates how well the system combines and synthesizes related memories:

**Metrics:**
- **Factual Consistency**: Synthesized memories are factually accurate
- **Completeness**: Important details are preserved during synthesis
- **Coherence**: Synthesized memories read naturally and logically
- **Deduplication**: Redundant information is properly combined
- **Relationship Detection**: Related memories are properly connected

### 3. Priority Classification (`priority_classification.py`)
Tests the system's ability to classify memory importance:

**Priority Levels:**
- **High**: Core personal facts, explicit remember requests, major life events
- **Medium**: Preferences, interests, work projects, goals
- **Low**: Casual mentions, temporary states, context-dependent info

### 4. Golden Dataset Evaluation (`golden_memories.json`)
Curated dataset of messages with expert-labeled classifications:

**Dataset Structure:**
```json
{
  "message_id": "msg_001",
  "user_message": "I'm a software engineer at Google working on search algorithms",
  "expected_decision": "REMEMBER",
  "expected_priority": "HIGH", 
  "expected_content": "User is a software engineer at Google, works on search algorithms",
  "reasoning": "Clear professional information that defines user's role and expertise",
  "tags": ["professional", "factual", "current_job"],
  "difficulty": "easy"
}
```

## Key Test Categories

### Category 1: Clear Memorable Content
Messages that should obviously be remembered:
```python
clear_memorable = [
    "My name is John Smith and I'm a product manager at Apple",
    "I live in San Francisco and I'm originally from Chicago", 
    "I have a degree in Computer Science from Stanford",
    "My goal is to start my own tech company within 5 years",
    "Please remember that I prefer direct communication style"
]
```

### Category 2: Clear Non-Memorable Content  
Messages that should obviously be skipped:
```python
clear_skippable = [
    "What time is it?",
    "How do I install Python?", 
    "Thanks for the help!",
    "What's the weather like today?",
    "Can you explain quantum physics?"
]
```

### Category 3: Ambiguous Cases
Messages that require intelligent analysis:
```python
ambiguous_cases = [
    "I'm working on a React project" # Could be memorable if it's their main project
    "I really like this coffee shop" # Memorable if it's a strong preference
    "My meeting went well today" # Not memorable unless it was important
    "I'm feeling stressed about work" # Could be memorable if it's a pattern
]
```

### Category 4: Context-Dependent Cases
Messages where decision depends on conversation context:
```python
context_dependent = [
    "Yes, exactly!" # Only memorable if confirming important info
    "That's interesting" # Usually not memorable unless specific context
    "I agree" # Depends on what they're agreeing with
    "Not really" # Depends on the question being answered
]
```

## Memory Synthesis Test Scenarios

### Scenario 1: Professional Information Synthesis
```python
related_memories = [
    "I work as a software engineer",
    "I'm at Google in the search team", 
    "I've been coding for 8 years",
    "I specialize in Python and Go"
]
expected_synthesis = "User is a software engineer at Google on the search team, with 8 years of coding experience, specializing in Python and Go"
```

### Scenario 2: Preference Consolidation
```python
preference_memories = [
    "I prefer coffee over tea",
    "I like my coffee black, no sugar",
    "I usually get coffee from Blue Bottle",
    "I drink coffee every morning"
]
expected_synthesis = "User prefers coffee over tea, drinks it black without sugar, usually from Blue Bottle, every morning"
```

### Scenario 3: Goal and Aspiration Synthesis
```python
goal_memories = [
    "I want to start my own company",
    "I'm interested in AI and machine learning",
    "I'm saving money for my startup",
    "I plan to launch within 2 years"
]
expected_synthesis = "User plans to start their own AI/ML company within 2 years and is currently saving money for it"
```

## Running Memory Intelligence Evals

### Basic Usage
```bash
# Run all memory intelligence evaluations
python -m evals.memory_intelligence.run_all

# Run specific evaluation
python -m evals.memory_intelligence.triage_accuracy --dataset golden_memories.json

# Test synthesis quality
python -m evals.memory_intelligence.synthesis_quality --user-id test-user
```

### Advanced Configuration
```bash
# Run with different triage thresholds
python -m evals.memory_intelligence.triage_accuracy --threshold 0.8

# Test specific message categories
python -m evals.memory_intelligence.triage_accuracy --category ambiguous

# Generate detailed error analysis
python -m evals.memory_intelligence.run_all --detailed-errors --save-misclassified
```

## Integration with Real System

These evaluations test the actual AI memory analysis:

```python
from app.mcp_orchestration import get_smart_orchestrator

orchestrator = get_smart_orchestrator()

# Test memory triage decision
analysis = await orchestrator._ai_memory_analysis("I'm a software engineer at Google")
decision = analysis['should_remember']  # True/False
content = analysis['content']  # Extracted memorable content

# Evaluate against golden standard
accuracy = evaluate_triage_decision(
    message="I'm a software engineer at Google",
    actual_decision="REMEMBER",
    expected_decision="REMEMBER"
)
```

## Expected Performance Targets

Based on the V2 Testing Strategy:

### Phase 1: Baseline (Current)
- **Triage Accuracy**: Measure current performance
- **False Positive Rate**: < 20% (not saving too much junk)
- **False Negative Rate**: < 10% (not missing important info)

### Phase 2: Optimization (Target)
- **Triage Accuracy**: > 95% on golden dataset
- **Synthesis Quality**: > 90% factual consistency
- **Priority Classification**: > 85% accuracy

### Phase 3: Advanced Intelligence
- **Contextual Triage**: Adapt decisions based on conversation flow
- **Proactive Synthesis**: Automatically connect related memories
- **Learning from Feedback**: Improve from user corrections

## Golden Dataset Curation

The golden dataset is curated through:

1. **Expert Labeling**: Domain experts manually classify messages
2. **Inter-Annotator Agreement**: Multiple experts label same messages
3. **User Feedback**: Real user corrections and preferences
4. **Edge Case Collection**: Difficult cases that challenge the system
5. **Regular Updates**: Dataset evolves with system improvements

## Contributing

When adding memory intelligence evaluations:

1. **Use representative data** from real conversations
2. **Include edge cases** and ambiguous scenarios  
3. **Provide clear reasoning** for expected classifications
4. **Test both accuracy and speed** of memory operations
5. **Document failure modes** and common errors

The goal is to build memory intelligence so accurate that users trust Jean Memory to automatically curate their personal knowledge base.