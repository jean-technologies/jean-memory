# Jean Memory Evaluation Framework Implementation Plan

## **Verified SDK Functionality**

Based on the latest SDK documentation and code analysis, here's how the Python SDK works:

### **Authentication Flow**
1. **Production Mode**: OAuth 2.1 PKCE flow via `JeanMemoryAuth` class
2. **Test Mode**: Automatic test user creation when `user_token=None`
3. **API Key Required**: Must start with `jean_sk_`

### **Core Flow**
```python
# SDK calls the jean_memory tool via MCP (Model Context Protocol)
client.get_context(user_token, message) 
    → make_mcp_request() 
    → POST /mcp/{client_name}/messages/{user_id}
    → jean_memory tool (always called)
    → Returns context with metadata
```

### **Key Insights**
- The `jean_memory` tool is **ALWAYS** called for every interaction
- Test mode automatically creates a test user when `user_token=None`
- Task 1 decorators already instrument the `jean_memory` tool
- Background tasks handle memory saving asynchronously

---

## **Recommended Implementation: SDK Evaluation Wrapper**

### **Architecture Overview**
```
┌─────────────────────────────────────────────────────────────┐
│                  Evaluation Framework                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         1. Conversation Dataset Generator            │  │
│  │              (Task 4 - JSON datasets)                │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         2. Python SDK Test Harness                   │  │
│  │         (Task 5 - SDK wrapper)                       │  │
│  │                                                      │  │
│  │  • Load dataset                                      │  │
│  │  • Authenticate (test or OAuth)                      │  │
│  │  • Call client.get_context() for each turn          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Existing Infrastructure (Tasks 1-3)          │  │
│  │                                                      │  │
│  │  • Task 1: Decorators capture metrics automatically  │  │
│  │  • Task 2: LLM Judge scores responses               │  │
│  │  • Task 3: Synthetic data for test cases            │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         3. Performance Report Generator              │  │
│  │              (Task 6 - Markdown output)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         4. CLI Test Runner                           │  │
│  │              (Task 7 - Orchestration)                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## **Implementation Details**

### **Task 4: Conversation Dataset Generator**
```python
# evaluation/conversation_dataset_generator.py
class ConversationDatasetGenerator:
    def __init__(self):
        self.synthetic_generator = SyntheticDataGeneratorService()
    
    def generate_conversation_dataset(
        self,
        length: int,  # 5-35 messages
        reasoning_distribution: str,  # "uniform" or "mixed"
        reasoning_type: ReasoningType = None  # For uniform
    ):
        """Generate a conversation-based test dataset"""
        conversation = []
        
        for turn in range(length):
            # Generate test case using Task 3
            if reasoning_distribution == "uniform":
                test_case = await generate_single_test_case(reasoning_type)
            else:  # mixed
                test_case = await generate_single_test_case(
                    random.choice(list(ReasoningType))
                )
            
            conversation.append({
                "turn": turn + 1,
                "message": test_case.query,
                "is_new_conversation": turn == 0,
                "needs_context": test_case.decision_path != "generic_knowledge",
                "expected_memories": test_case.memories,
                "reasoning_type": test_case.reasoning_type,
                "metadata": test_case.to_dict()
            })
        
        # Save to JSON
        dataset = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "length": length,
            "reasoning_distribution": reasoning_distribution,
            "conversation": conversation
        }
        
        filename = f"./test_datasets/conversation_{dataset['id'][:8]}.json"
        with open(filename, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        return filename
```

### **Task 5: Python SDK Test Harness**
```python
# evaluation/sdk_test_harness.py
class JeanMemoryTestHarness:
    def __init__(self, api_key: str, mode: str = "test"):
        """
        Initialize test harness
        
        Args:
            api_key: Jean Memory API key
            mode: "test" (auto test user) or "production" (OAuth)
        """
        self.client = JeanMemoryClient(api_key)
        self.mode = mode
        self.auth = JeanMemoryAuth(api_key) if mode == "production" else None
        
    async def run_conversation_test(
        self, 
        dataset_path: str,
        user_token: str = None
    ):
        """
        Run conversation through SDK and evaluate
        
        Args:
            dataset_path: Path to JSON conversation dataset
            user_token: OAuth token (optional for test mode)
        """
        # 1. Load dataset
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
        
        # 2. Handle authentication
        if self.mode == "production" and not user_token:
            # Trigger OAuth flow
            user_info = self.auth.authenticate()
            user_token = user_info['access_token']
        # For test mode, user_token remains None (SDK auto-creates test user)
        
        # 3. Run conversation
        results = []
        for turn in dataset['conversation']:
            
            # Call SDK - Task 1 decorators capture metrics automatically
            context_response = await self.client.get_context(
                user_token=user_token,  # None for test mode
                message=turn['message'],
                # SDK doesn't expose is_new_conversation directly,
                # but we can simulate by clearing context between convos
            )
            
            # Task 2: LLM Judge evaluation
            memories_for_judge = [
                {"content": mem.get("content", "")} 
                for mem in turn.get("expected_memories", [])
            ]
            
            judge_score = await evaluate_single_response(
                query=turn['message'],
                memories=memories_for_judge,
                response=context_response.text,
                reasoning_type=ReasoningType[turn['reasoning_type']]
            )
            
            # Collect results
            results.append({
                'turn': turn['turn'],
                'message': turn['message'],
                'response': context_response.text,
                'judge_score': judge_score,
                'latency': context_response.metadata.get('latency_ms', 0)
            })
        
        return results
```

### **Task 6: Performance Report Generator**
```python
# evaluation/report_generator.py
class PerformanceReportGenerator:
    def generate_markdown_report(self, test_results: List[dict], dataset_info: dict):
        """Generate comprehensive markdown report"""
        
        # Calculate statistics
        scores_by_type = defaultdict(list)
        latencies = []
        
        for result in test_results:
            reasoning_type = result.get('reasoning_type', 'unknown')
            scores_by_type[reasoning_type].append(result['judge_score'].overall)
            latencies.append(result.get('latency', 0))
        
        # Calculate percentiles
        p50_latency = np.percentile(latencies, 50)
        p95_latency = np.percentile(latencies, 95)
        
        # Generate report
        report = f"""
# Jean Memory Performance Evaluation Report

**Date**: {datetime.now().isoformat()}
**Dataset**: {dataset_info['id']}
**Conversation Length**: {dataset_info['length']} turns

## Overall Performance

- **Average Score**: {np.mean([r['judge_score'].overall for r in test_results]):.1f}/10
- **P50 Latency**: {p50_latency:.0f}ms
- **P95 Latency**: {p95_latency:.0f}ms

## LoCoMo Reasoning Type Breakdown

| Reasoning Type | Avg Score | Count | Pass Rate |
|---------------|-----------|--------|-----------|
{self._generate_reasoning_table(scores_by_type)}

## Detailed Results

{self._generate_detailed_results(test_results)}

## System Information

- **Evaluation Mode**: {os.getenv('EVALUATION_MODE', 'disabled')}
- **LLM Judge Provider**: {os.getenv('LLM_JUDGE_PROVIDER', 'auto')}
- **Consensus Mode**: {os.getenv('CONSENSUS_MODE', 'single')}

---
Generated by Jean Memory Evaluation Framework v1.0
"""
        
        # Save report
        filename = f"./evaluation_reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w') as f:
            f.write(report)
        
        return filename
```

### **Task 7: CLI Test Runner**
```python
#!/usr/bin/env python3
# run_evaluation.py

import argparse
import asyncio
from evaluation import (
    ConversationDatasetGenerator,
    JeanMemoryTestHarness,
    PerformanceReportGenerator,
    ReasoningType
)

async def main():
    parser = argparse.ArgumentParser(description='Jean Memory Evaluation Framework')
    parser.add_argument('--length', type=int, default=20, help='Conversation length (5-35)')
    parser.add_argument('--type', choices=['uniform', 'mixed'], default='mixed', 
                       help='Reasoning type distribution')
    parser.add_argument('--reasoning', choices=[r.value for r in ReasoningType], 
                       help='Specific reasoning type for uniform distribution')
    parser.add_argument('--mode', choices=['test', 'production'], default='test',
                       help='Testing mode')
    parser.add_argument('--api-key', required=True, help='Jean Memory API key')
    
    args = parser.parse_args()
    
    print("🚀 Jean Memory Evaluation Framework")
    print("=" * 50)
    
    # 1. Generate dataset
    print(f"📊 Generating dataset: {args.length} turns, {args.type} distribution...")
    generator = ConversationDatasetGenerator()
    dataset_path = await generator.generate_conversation_dataset(
        length=args.length,
        reasoning_distribution=args.type,
        reasoning_type=ReasoningType[args.reasoning] if args.reasoning else None
    )
    print(f"✅ Dataset created: {dataset_path}")
    
    # 2. Run test harness
    print(f"🧪 Running conversation test in {args.mode} mode...")
    harness = JeanMemoryTestHarness(args.api_key, mode=args.mode)
    results = await harness.run_conversation_test(dataset_path)
    print(f"✅ Test completed: {len(results)} turns evaluated")
    
    # 3. Generate report
    print("📝 Generating performance report...")
    reporter = PerformanceReportGenerator()
    with open(dataset_path, 'r') as f:
        dataset_info = json.load(f)
    report_path = reporter.generate_markdown_report(results, dataset_info)
    print(f"✅ Report saved: {report_path}")
    
    # 4. Print summary
    avg_score = np.mean([r['judge_score'].overall for r in results])
    print("\n" + "=" * 50)
    print(f"🎯 Overall Score: {avg_score:.1f}/10")
    
    if avg_score >= 8.5:
        print("🏆 EXCELLENT - Jean Memory performing at benchmark level")
    elif avg_score >= 7.0:
        print("✅ GOOD - Jean Memory meeting performance targets")
    else:
        print("⚠️  NEEDS IMPROVEMENT - Review report for details")
    
    return 0 if avg_score >= 7.0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

---

## **Usage Examples**

### **1. Test Mode (Development)**
```bash
# Simple test with automatic test user
./run_evaluation.py --api-key jean_sk_test_123 --length 10 --type mixed

# Uniform single-hop test
./run_evaluation.py --api-key jean_sk_test_123 --length 20 --type uniform --reasoning SINGLE_HOP
```

### **2. Production Mode (Real Users)**
```bash
# OAuth flow for real user testing
./run_evaluation.py --api-key jean_sk_live_456 --mode production --length 30 --type mixed
```

### **3. CI/CD Integration**
```yaml
# .github/workflows/evaluation.yml
- name: Run Jean Memory Evaluation
  env:
    EVALUATION_MODE: "true"
    LLM_JUDGE_ENABLED: "true"
  run: |
    ./run_evaluation.py --api-key ${{ secrets.JEAN_API_KEY }} \
      --length 20 --type mixed
```

---

## **Key Advantages of This Approach**

1. **Zero Production Code Changes**
   - Pure wrapper around existing SDK
   - No modifications to jean_memory tool
   - Task 1 decorators already capture metrics

2. **Authentic Testing**
   - Uses real SDK flow (exactly what users experience)
   - Test mode for development (auto test user)
   - OAuth support for production testing

3. **Leverages Existing Infrastructure**
   - Task 1: Automatic metric capture via decorators
   - Task 2: LLM Judge for quality scoring
   - Task 3: Synthetic data generation

4. **Simple Implementation**
   - ~500 lines of code total
   - No new dependencies
   - Can be implemented in 2-3 days

5. **Flexible & Extensible**
   - Easy to add new reasoning types
   - Can test different conversation patterns
   - Supports both test and production modes

---

## **Implementation Timeline**

- **Day 1**: Task 4 (Dataset Generator) + Task 5 (SDK Harness)
- **Day 2**: Task 6 (Report Generator) + Task 7 (CLI Runner)
- **Day 3**: Integration testing and documentation

---

## **Summary**

This approach treats the Python SDK as a black box, which is exactly how users interact with it. The evaluation framework:

1. Generates conversation datasets using existing Task 3 infrastructure
2. Runs conversations through the SDK (which calls jean_memory tool)
3. Task 1 decorators automatically capture performance metrics
4. Task 2 LLM Judge evaluates response quality
5. Generates comprehensive markdown reports

The beauty is that **everything just works** because:
- The SDK already handles authentication (test mode or OAuth)
- The jean_memory tool is already decorated for metrics
- The LLM Judge is already integrated for quality scoring
- The synthetic generator already creates test cases

This is the most minimal, non-invasive solution that delivers complete evaluation capabilities.