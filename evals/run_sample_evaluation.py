#!/usr/bin/env python3
"""
Sample Evaluation Runner
Demonstrates how to run the Jean Memory evaluation framework
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "openmemory" / "api"))
sys.path.insert(0, str(current_dir / "utils"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_context_quality_evaluation():
    """Run a sample context quality evaluation"""
    try:
        from evals.context_engineering.quality_scoring import ContextQualityScoringEvaluator, create_context_quality_scenarios
        
        logger.info("🔍 Running Context Quality Evaluation...")
        
        # Create evaluator
        config = {'quality_threshold': 75.0}
        evaluator = ContextQualityScoringEvaluator(config)
        
        # Load scenarios
        scenarios = create_context_quality_scenarios()[:3]  # Run first 3 for demo
        
        # Run evaluation
        results = await evaluator.run_evaluation(scenarios)
        
        # Print results
        summary = evaluator.get_summary_stats()
        print("\n📊 Context Quality Results:")
        print(f"  Passed: {summary['passed']}/{summary['total_tests']}")
        print(f"  Average Score: {summary['average_score']:.1f}")
        print(f"  Pass Rate: {summary['pass_rate']:.1f}%")
        
        return results
        
    except Exception as e:
        logger.error(f"Context quality evaluation failed: {e}")
        return []

async def run_memory_triage_evaluation():
    """Run a sample memory triage evaluation"""
    try:
        from evals.memory_intelligence.triage_accuracy import MemoryTriageAccuracyEvaluator, create_default_scenarios
        
        logger.info("🧠 Running Memory Triage Evaluation...")
        
        # Create evaluator
        config = {'accuracy_threshold': 90.0}
        evaluator = MemoryTriageAccuracyEvaluator(config)
        
        # Load scenarios
        scenarios = create_default_scenarios()[:5]  # Run first 5 for demo
        
        # Run evaluation
        results = await evaluator.run_evaluation(scenarios)
        
        # Print results
        metrics = evaluator._calculate_metrics()
        print("\n🎯 Memory Triage Results:")
        print(f"  Accuracy: {metrics['accuracy']:.1f}%")
        print(f"  Precision: {metrics['precision']:.1f}%")
        print(f"  Recall: {metrics['recall']:.1f}%")
        print(f"  F1 Score: {metrics['f1_score']:.1f}%")
        
        return results
        
    except Exception as e:
        logger.error(f"Memory triage evaluation failed: {e}")
        return []

async def run_fast_path_evaluation():
    """Run a sample fast path performance evaluation"""
    try:
        # Simple import check and mock evaluation
        logger.info("⚡ Running Fast Path Performance Check...")
        
        # Simulate fast path test
        import time
        from evals.utils.eval_framework import simulate_orchestrator_call
        
        start_time = time.time()
        result = await simulate_orchestrator_call(
            "Hello, I'm testing the fast path",
            "sample-eval-user",
            "claude",
            is_new_conversation=True
        )
        response_time = time.time() - start_time
        
        print("\n⚡ Fast Path Performance:")
        print(f"  Response Time: {response_time:.2f}s")
        print(f"  Target: < 3.0s")
        print(f"  Status: {'✅ PASS' if response_time < 3.0 else '❌ FAIL'}")
        print(f"  Context Length: {len(result.get('context', ''))}")
        
        return [{'response_time': response_time, 'success': result['success']}]
        
    except Exception as e:
        logger.error(f"Fast path evaluation failed: {e}")
        return []

async def main():
    """Run sample evaluations to demonstrate the framework"""
    print("🚀 Jean Memory Evaluation Framework Demo")
    print("=" * 60)
    
    try:
        # Run each evaluation category
        context_results = await run_context_quality_evaluation()
        triage_results = await run_memory_triage_evaluation()
        performance_results = await run_fast_path_evaluation()
        
        # Summary
        print("\n📋 EVALUATION SUMMARY:")
        print("-" * 40)
        print(f"Context Quality Tests: {len(context_results)}")
        print(f"Memory Triage Tests: {len(triage_results)}")
        print(f"Performance Tests: {len(performance_results)}")
        
        total_tests = len(context_results) + len(triage_results) + len(performance_results)
        print(f"\nTotal Tests Run: {total_tests}")
        
        if total_tests > 0:
            print("\n✅ Evaluation framework is working!")
            print("\nNext steps:")
            print("1. Run full evaluations: python -m evals.context_engineering.quality_scoring")
            print("2. Run memory triage: python -m evals.memory_intelligence.triage_accuracy")
            print("3. Run performance tests: python -m evals.performance.fast_path_benchmarks")
        else:
            print("\n⚠️ No tests completed successfully")
            print("Check the logs above for error details")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print("\n❌ Demo failed - check logs for details")

if __name__ == "__main__":
    asyncio.run(main())