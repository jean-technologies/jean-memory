#!/usr/bin/env python3
"""
Test script for Jean Memory Evaluation Infrastructure
======================================================

Tests the evaluation system toggle, performance impact, and metric collection.
"""

import asyncio
import json
import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.evaluation import EvaluationMode, evaluate, MetricsCollector, MetricsStorage


class EvaluationSystemTest:
    """Test harness for the evaluation infrastructure."""
    
    def __init__(self):
        self.results = {
            "toggle_test": None,
            "performance_test": None,
            "metric_collection_test": None,
            "memory_overhead_test": None
        }
    
    async def test_toggle_functionality(self):
        """Test that evaluation can be toggled on/off."""
        print("\n🔧 Testing Evaluation Toggle...")
        
        # Test with evaluation OFF
        os.environ["EVALUATION_MODE"] = "false"
        assert not EvaluationMode.is_enabled(), "Evaluation should be disabled"
        
        @evaluate(name="test_function_off")
        async def test_func_off():
            return "result"
        
        result = await test_func_off()
        assert result == "result", "Function should return normal result"
        
        # Test with evaluation ON
        os.environ["EVALUATION_MODE"] = "true"
        assert EvaluationMode.is_enabled(), "Evaluation should be enabled"
        
        @evaluate(name="test_function_on")
        async def test_func_on():
            return "result"
        
        result = await test_func_on()
        assert result == "result", "Function should return normal result with evaluation"
        
        self.results["toggle_test"] = "✅ PASSED"
        print("  ✅ Toggle functionality working correctly")
    
    async def test_performance_impact(self):
        """Test performance impact when evaluation is enabled/disabled."""
        print("\n⚡ Testing Performance Impact...")
        
        iterations = 1000
        
        @evaluate(name="perf_test_function")
        async def test_func(x):
            # Simulate some work
            await asyncio.sleep(0.001)
            return x * 2
        
        # Test with evaluation OFF
        os.environ["EVALUATION_MODE"] = "false"
        start_time = time.perf_counter()
        for i in range(iterations):
            await test_func(i)
        time_without_eval = time.perf_counter() - start_time
        
        # Test with evaluation ON
        os.environ["EVALUATION_MODE"] = "true"
        start_time = time.perf_counter()
        for i in range(iterations):
            await test_func(i)
        time_with_eval = time.perf_counter() - start_time
        
        overhead_percent = ((time_with_eval - time_without_eval) / time_without_eval) * 100
        
        print(f"  Time without evaluation: {time_without_eval:.3f}s")
        print(f"  Time with evaluation: {time_with_eval:.3f}s")
        print(f"  Overhead: {overhead_percent:.1f}%")
        
        # Check that overhead is reasonable (< 10%)
        if overhead_percent < 10:
            self.results["performance_test"] = f"✅ PASSED (overhead: {overhead_percent:.1f}%)"
            print(f"  ✅ Performance overhead acceptable ({overhead_percent:.1f}%)")
        else:
            self.results["performance_test"] = f"⚠️ WARNING (overhead: {overhead_percent:.1f}%)"
            print(f"  ⚠️ Performance overhead high ({overhead_percent:.1f}%)")
    
    async def test_metric_collection(self):
        """Test that metrics are collected correctly."""
        print("\n📊 Testing Metric Collection...")
        
        os.environ["EVALUATION_MODE"] = "true"
        os.environ["EVALUATION_ASYNC"] = "false"  # Use sync collection for testing
        
        # Create a new decorator instance to ensure we get fresh collector
        from app.evaluation.core import EvaluationDecorator
        test_decorator = EvaluationDecorator(name="metric_test_function")
        
        @test_decorator
        async def test_func(should_fail=False):
            await asyncio.sleep(0.01)
            if should_fail:
                raise ValueError("Test error")
            return "success"
        
        # Run some successful calls
        for _ in range(5):
            await test_func()
        
        # Run some failed calls
        for _ in range(2):
            try:
                await test_func(should_fail=True)
            except ValueError:
                pass
        
        # Get statistics from the decorator's collector
        collector = test_decorator._get_metrics_collector()
        stats = collector.get_statistics("metric_test_function")
        
        assert stats["count"] >= 7, f"Should have at least 7 calls, got {stats['count']}"
        assert 0.6 <= stats["success_rate"] <= 0.8, f"Success rate should be ~71%, got {stats['success_rate']}"
        assert stats["latency"]["mean"] > 10, f"Mean latency should be > 10ms, got {stats['latency']['mean']}"
        
        self.results["metric_collection_test"] = "✅ PASSED"
        print(f"  ✅ Metrics collected correctly")
        print(f"    - Total calls: {stats['count']}")
        print(f"    - Success rate: {stats['success_rate']*100:.1f}%")
        print(f"    - Mean latency: {stats['latency']['mean']:.2f}ms")
    
    async def test_memory_overhead(self):
        """Test memory overhead when evaluation is enabled."""
        print("\n💾 Testing Memory Overhead...")
        
        # Enable memory tracking
        tracemalloc.start()
        
        @evaluate(name="memory_test_function")
        async def test_func(data):
            # Process some data
            result = [x * 2 for x in data]
            await asyncio.sleep(0.001)
            return result
        
        test_data = list(range(1000))
        
        # Baseline memory with evaluation OFF
        os.environ["EVALUATION_MODE"] = "false"
        snapshot1 = tracemalloc.take_snapshot()
        
        for _ in range(100):
            await test_func(test_data)
        
        snapshot2 = tracemalloc.take_snapshot()
        memory_without_eval = sum(stat.size_diff for stat in snapshot2.compare_to(snapshot1, 'lineno'))
        
        # Memory with evaluation ON
        os.environ["EVALUATION_MODE"] = "true"
        snapshot3 = tracemalloc.take_snapshot()
        
        for _ in range(100):
            await test_func(test_data)
        
        snapshot4 = tracemalloc.take_snapshot()
        memory_with_eval = sum(stat.size_diff for stat in snapshot4.compare_to(snapshot3, 'lineno'))
        
        tracemalloc.stop()
        
        overhead_mb = (memory_with_eval - memory_without_eval) / (1024 * 1024)
        
        print(f"  Memory without evaluation: {memory_without_eval / (1024*1024):.2f} MB")
        print(f"  Memory with evaluation: {memory_with_eval / (1024*1024):.2f} MB")
        print(f"  Overhead: {overhead_mb:.2f} MB")
        
        # Check that overhead is < 50MB as per requirements
        if overhead_mb < 50:
            self.results["memory_overhead_test"] = f"✅ PASSED (overhead: {overhead_mb:.2f}MB)"
            print(f"  ✅ Memory overhead acceptable ({overhead_mb:.2f}MB < 50MB)")
        else:
            self.results["memory_overhead_test"] = f"❌ FAILED (overhead: {overhead_mb:.2f}MB)"
            print(f"  ❌ Memory overhead too high ({overhead_mb:.2f}MB > 50MB)")
    
    async def run_all_tests(self):
        """Run all evaluation system tests."""
        print("=" * 60)
        print("Jean Memory Evaluation Infrastructure Test Suite")
        print("=" * 60)
        
        try:
            await self.test_toggle_functionality()
            await self.test_performance_impact()
            await self.test_metric_collection()
            await self.test_memory_overhead()
            
            # Generate test report
            print("\n" + "=" * 60)
            print("Test Results Summary")
            print("=" * 60)
            
            all_passed = True
            for test_name, result in self.results.items():
                print(f"{test_name}: {result or '❌ NOT RUN'}")
                if result and "FAILED" in result:
                    all_passed = False
            
            print("\n" + "=" * 60)
            if all_passed:
                print("✅ All tests passed successfully!")
            else:
                print("❌ Some tests failed. Please review the results.")
            print("=" * 60)
            
            # Test report generation
            storage = MetricsStorage()
            report_path = storage.export_report("test_evaluation_report.md")
            if report_path:
                print(f"\n📄 Evaluation report generated: {report_path}")
            
            return all_passed
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main test runner."""
    tester = EvaluationSystemTest()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())