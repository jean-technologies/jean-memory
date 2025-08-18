# Jean Memory - Minimal Evaluation System Design

## 🎯 Purpose
Create a lightweight, practical evaluation system to measure and improve Jean Memory's context engineering performance without building complex evaluation infrastructure.

## 📊 Core Evaluation Metrics

### 1. Context Relevance Score (0-10)
**What it measures**: Is the retrieved context actually relevant to the user's query?
**How to measure**: 
- LLM-based scoring using Gemini Flash
- Compare retrieved context against query intent
- Score based on semantic alignment

### 2. Context Completeness Score (0-10)
**What it measures**: Does the context contain all necessary information?
**How to measure**:
- Check if key entities/dates/facts are present
- Verify temporal context is included when needed
- Ensure relationships are captured

### 3. Response Latency (milliseconds)
**What it measures**: How fast is the context retrieval?
**Targets**:
- Simple queries: <500ms
- Complex queries: <4000ms
- New conversations: <2000ms

### 4. Retrieval Accuracy (F1 Score)
**What it measures**: Precision and recall of memory retrieval
**How to measure**:
- True Positives: Relevant memories retrieved
- False Positives: Irrelevant memories retrieved
- False Negatives: Relevant memories missed

---

## 🧪 Evaluation Dataset Structure

### Test Query Categories (100 queries total)

#### Category 1: Simple Factual Recall (25 queries)
```json
{
  "query": "What's my dog's name?",
  "expected_context": ["dog", "pet", "name"],
  "category": "simple_recall",
  "complexity": 1
}
```

#### Category 2: Temporal Queries (25 queries)
```json
{
  "query": "What did I work on last week?",
  "expected_context": ["work", "projects", "last week", "tasks"],
  "category": "temporal",
  "complexity": 2
}
```

#### Category 3: Relational Queries (25 queries)
```json
{
  "query": "Who did I meet at the conference?",
  "expected_context": ["conference", "meeting", "people", "networking"],
  "category": "relational",
  "complexity": 3
}
```

#### Category 4: Complex Synthesis (25 queries)
```json
{
  "query": "How has my coding style evolved?",
  "expected_context": ["programming", "evolution", "learning", "progress"],
  "category": "synthesis",
  "complexity": 4
}
```

---

## 🛠️ Implementation Plan

### Phase 1: Basic Framework (Week 1)

#### 1. Create Evaluation Dataset
```python
# evaluation/test_queries.json
{
  "queries": [
    {
      "id": "Q001",
      "query": "What's my favorite programming language?",
      "expected_keywords": ["python", "javascript", "programming"],
      "category": "preference",
      "complexity": 1,
      "validation_type": "keyword_match"
    }
  ]
}
```

#### 2. Build Evaluation Runner
```python
# evaluation/runner.py
class ContextEvaluator:
    def __init__(self):
        self.test_queries = load_test_queries()
        self.results = []
    
    def evaluate_query(self, query, expected):
        # Get context from Jean Memory
        start_time = time.time()
        context = jean_memory(query, needs_context=True)
        latency = time.time() - start_time
        
        # Score relevance
        relevance_score = self.score_relevance(context, query)
        
        # Score completeness
        completeness_score = self.score_completeness(context, expected)
        
        return {
            "relevance": relevance_score,
            "completeness": completeness_score,
            "latency_ms": latency * 1000
        }
```

#### 3. LLM-Based Scoring
```python
# evaluation/scoring.py
def score_relevance(context, query):
    prompt = f"""
    Rate the relevance of this context for answering the query.
    Query: {query}
    Context: {context}
    
    Score 0-10 where:
    0-3: Irrelevant or wrong context
    4-6: Partially relevant
    7-9: Highly relevant
    10: Perfect context
    
    Return only the number.
    """
    score = gemini_flash.generate(prompt)
    return float(score)
```

### Phase 2: Automated Testing (Week 2)

#### 1. GitHub Actions Integration
```yaml
# .github/workflows/evaluation.yml
name: Weekly Context Evaluation
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - name: Run Evaluation Suite
        run: python evaluation/runner.py
      
      - name: Generate Report
        run: python evaluation/reporter.py
      
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: evaluation-report
          path: reports/
```

#### 2. Performance Tracking
```python
# evaluation/tracker.py
class PerformanceTracker:
    def track_metrics(self, results):
        metrics = {
            "avg_relevance": mean([r["relevance"] for r in results]),
            "avg_completeness": mean([r["completeness"] for r in results]),
            "p50_latency": percentile([r["latency_ms"] for r in results], 50),
            "p95_latency": percentile([r["latency_ms"] for r in results], 95),
            "success_rate": len([r for r in results if r["relevance"] > 7]) / len(results)
        }
        return metrics
```

### Phase 3: SDK Integration (Week 3)

#### Using React SDK for Real-World Testing
```typescript
// evaluation/sdk-test.tsx
import { JeanMemoryProvider, useJean } from '@jean-technologies/jean-memory-react';

function EvaluationComponent() {
  const { sendMessage, messages } = useJean();
  const testQueries = loadTestQueries();
  
  const runEvaluation = async () => {
    const results = [];
    for (const query of testQueries) {
      const startTime = Date.now();
      await sendMessage(query.text);
      const latency = Date.now() - startTime;
      
      // Collect response and measure quality
      results.push({
        query: query.text,
        latency,
        response: messages[messages.length - 1]
      });
    }
    return results;
  };
}
```

---

## 📈 Evaluation Dashboard

### Key Metrics to Display
1. **Overall Health Score**: Weighted average of all metrics
2. **Trend Charts**: Performance over time
3. **Category Breakdown**: Performance by query type
4. **Latency Distribution**: P50, P95, P99
5. **Failure Analysis**: Common failure patterns

### Simple Markdown Report Format
```markdown
# Jean Memory Evaluation Report
Date: 2024-01-15

## Overall Performance
- **Health Score**: 8.2/10 ↑ 0.3
- **Average Latency**: 1,850ms ↓ 200ms
- **Success Rate**: 85% ↑ 5%

## Category Performance
| Category | Relevance | Completeness | Latency |
|----------|-----------|--------------|---------|
| Simple | 9.2 | 9.5 | 450ms |
| Temporal | 8.1 | 7.8 | 1,200ms |
| Relational | 7.5 | 7.2 | 2,100ms |
| Synthesis | 6.8 | 6.5 | 3,800ms |

## Top Issues
1. Temporal queries missing recent context (15% failure rate)
2. Synthesis queries timeout on complex requests
3. Relational queries incomplete graph traversal
```

---

## 🚀 Quick Start Implementation

### Step 1: Create Test Data (Day 1)
```bash
# Create evaluation directory
mkdir evaluation
cd evaluation

# Create test queries
cat > test_queries.json << EOF
{
  "queries": [
    {"id": 1, "text": "What's my name?", "category": "simple"},
    {"id": 2, "text": "What did I do yesterday?", "category": "temporal"},
    {"id": 3, "text": "Who are my colleagues?", "category": "relational"}
  ]
}
EOF
```

### Step 2: Run Basic Evaluation (Day 2)
```python
# evaluation/quick_eval.py
import json
import time
from jean_memory import jean_memory

def quick_evaluate():
    with open('test_queries.json') as f:
        queries = json.load(f)['queries']
    
    results = []
    for query in queries:
        start = time.time()
        context = jean_memory(query['text'], needs_context=True)
        latency = (time.time() - start) * 1000
        
        results.append({
            'query': query['text'],
            'category': query['category'],
            'latency_ms': latency,
            'context_length': len(context)
        })
    
    # Print summary
    avg_latency = sum(r['latency_ms'] for r in results) / len(results)
    print(f"Average Latency: {avg_latency:.0f}ms")
    print(f"Queries Tested: {len(results)}")
    
    return results

if __name__ == "__main__":
    quick_evaluate()
```

### Step 3: Track Improvements (Day 3)
```python
# evaluation/compare.py
def compare_runs(before, after):
    improvements = {
        'latency': (before['avg_latency'] - after['avg_latency']) / before['avg_latency'] * 100,
        'relevance': after['avg_relevance'] - before['avg_relevance'],
        'completeness': after['avg_completeness'] - before['avg_completeness']
    }
    
    print(f"Latency improved by {improvements['latency']:.1f}%")
    print(f"Relevance improved by {improvements['relevance']:.1f} points")
    print(f"Completeness improved by {improvements['completeness']:.1f} points")
```

---

## 🎯 Success Criteria

### Week 1 Goals
- [ ] 100 test queries created
- [ ] Basic evaluation runner working
- [ ] Baseline metrics established

### Week 2 Goals
- [ ] Automated weekly runs
- [ ] LLM-based scoring implemented
- [ ] Performance tracking active

### Week 3 Goals
- [ ] SDK integration complete
- [ ] Dashboard reporting
- [ ] Improvement trends visible

### Target Metrics (End of Month)
- **Relevance Score**: >8.0/10
- **Completeness Score**: >7.5/10
- **P50 Latency**: <1,500ms
- **P95 Latency**: <4,000ms
- **Success Rate**: >85%

---

## 💡 Why This Approach Works

1. **Minimal Infrastructure**: No complex evaluation frameworks needed
2. **Practical Metrics**: Focus on what users actually experience
3. **Automated Testing**: Weekly runs catch regressions early
4. **SDK Integration**: Test with real user interface
5. **Clear Reporting**: Simple markdown reports anyone can read

This evaluation system provides actionable insights without the overhead of complex evaluation infrastructure. It's designed to be implemented in days, not weeks, and provides immediate value for optimization efforts.