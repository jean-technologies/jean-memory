#!/usr/bin/env python3
"""
Jean Memory V3 Test Runner
Comprehensive test runner for the complete testing suite
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'='*50}")
    print(f"🧪 {description}")
    print(f"{'='*50}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Command: {cmd}")
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    if result.stdout:
        print("\n📊 STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("\n❌ STDERR:")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    """Run the complete Jean Memory V3 test suite"""
    print("🚀 Jean Memory V3 Comprehensive Testing Suite")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    print(f"📁 Working directory: {project_dir}")
    
    # Test categories
    test_results = {}
    
    # 1. Basic Tests
    success = run_command(
        "python -m pytest tests/unit/test_basic.py -v",
        "Basic Infrastructure Tests"
    )
    test_results["basic"] = success
    
    # 2. Unit Tests (selected)
    success = run_command(
        "python -m pytest tests/unit/test_stm_service.py::TestSTMMemory -v",
        "STM Memory Unit Tests"
    )
    test_results["stm_unit"] = success
    
    # 3. Integration Tests
    success = run_command(
        "python -m pytest tests/integration/test_basic_integration.py -v -m integration",
        "Basic Integration Tests"
    )
    test_results["integration"] = success
    
    # 4. Performance Tests (single benchmark)
    success = run_command(
        "python -m pytest tests/performance/test_benchmarks.py::TestMemoryPerformanceBenchmarks::test_concurrent_memory_operations_performance -v -m performance",
        "Performance Benchmark Tests"
    )
    test_results["performance"] = success
    
    # 5. Coverage Report
    success = run_command(
        "python -m pytest tests/unit/test_basic.py --cov=services --cov=api --cov=config --cov-report=term",
        "Test Coverage Report"
    )
    test_results["coverage"] = success
    
    # Print summary
    print("\n" + "="*60)
    print("📋 TEST SUITE SUMMARY")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20}: {status}")
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} test categories passed")
    
    if passed_tests == total_tests:
        print("🎉 All test categories completed successfully!")
        return 0
    else:
        print("⚠️  Some test categories failed. See details above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)