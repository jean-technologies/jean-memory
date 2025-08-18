"""
Test script for Task 8: Performance Metrics Extraction

This script validates all functionality of the log parser and metrics extraction system.
"""

import asyncio
import sys
import time
import tempfile
from pathlib import Path

# Add current directory to path for imports
sys.path.append('.')

from app.evaluation.log_parser import LogParser, parse_log_file, parse_log_text
from app.evaluation.metrics_extractor import MetricsExtractor, MetricType


# Sample production logs for testing
SAMPLE_PRODUCTION_LOGS = """
2025-08-16T16:20:51.406 - app.mcp_orchestration - INFO - Starting orchestration for user: fa97efb5-410d-4806-b137-8cf13b6cb464
2025-08-16T16:20:51.407 - app.memory_retrieval - INFO - [PERF] Memory search took 245ms (found 12 memories)
2025-08-16T16:20:51.408 - app.context_engineering - INFO - Context strategy: deep_understanding (confidence: 0.85)
2025-08-16T16:20:51.409 - app.memory_retrieval - INFO - Searching memories with query: "user recent projects"
2025-08-16T16:20:51.410 - app.memory_retrieval - INFO - Memory search returned 15 results
2025-08-16T16:20:51.411 - app.memory_retrieval - INFO - Filtering memories: 45 -> 12 relevant
2025-08-16T16:20:51.412 - app.memory_retrieval - INFO - [PERF] Cache lookup: 15ms (hit)
2025-08-16T16:20:51.413 - app.context_engineering - INFO - Memory cache: HIT (query: "user preferences")
2025-08-16T16:20:51.414 - app.orchestration - INFO - Orchestration phase: memory_retrieval
2025-08-16T16:20:51.415 - app.orchestration - INFO - Processing step: context_synthesis (2/5)
2025-08-16T16:20:51.416 - app.context_engineering - INFO - [PERF] Context execution: 1.2s
2025-08-16T16:20:51.417 - app.ai_planning - INFO - [PERF] AI planning time: 850ms
2025-08-16T16:20:51.418 - app.database - INFO - [PERF] Database query took 125ms
2025-08-16T16:20:51.419 - app.response_gen - INFO - [PERF] Response generation: 2.1s
2025-08-16T16:20:51.420 - app.orchestration - INFO - [PERF] Total orchestration time: 3.4s
2025-08-16T16:20:51.421 - app.orchestration - INFO - Orchestration completed successfully in 3.4s
2025-08-16T16:20:51.422 - app.memory_retrieval - INFO - Memory relevance scoring completed (threshold: 0.7)
2025-08-16T16:20:51.423 - app.context_engineering - INFO - Selected context approach: balanced_search
2025-08-16T16:20:51.424 - app.cache - INFO - Cache miss for query hash: abc123def456
2025-08-16T16:20:51.425 - app.error_handler - ERROR - Memory search failed for invalid query
2025-08-16T16:20:51.426 - app.context_engineering - INFO - Context engineering mode: comprehensive
"""

SAMPLE_LOGS_WITH_ERRORS = """
2025-08-16T16:25:00.000 - app.orchestration - INFO - Starting orchestration for user: test-user-123
2025-08-16T16:25:00.001 - app.memory - INFO - [PERF] Memory search took 500ms (found 0 memories)
Invalid log line without timestamp or proper format
2025-08-16T16:25:00.002 - app.error - [ERROR] Context generation timeout
Malformed [PERF] line without proper metrics
2025-08-16T16:25:00.003 - app.orchestration - INFO - Orchestration phase: error_recovery
2025-08-16T16:25:00.004 - app.cache - INFO - Memory cache: MISS (query: "nonexistent data")
"""


async def test_frd_acceptance_criteria():
    """Test all FRD acceptance criteria"""
    print("🧪 Testing Task 8 FRD Acceptance Criteria")
    print("=" * 60)
    
    results = {}
    
    # Acceptance Criterion 1: Parses performance metrics from [PERF] log lines
    print("1. Testing [PERF] log line parsing...")
    try:
        metrics, stats = parse_log_text(SAMPLE_PRODUCTION_LOGS)
        
        perf_metrics_found = (
            len(metrics.memory_search_times_ms) > 0 or
            len(metrics.context_execution_times_s) > 0 or
            len(metrics.ai_planning_times_ms) > 0 or
            len(metrics.total_orchestration_times_s) > 0
        )
        
        results['perf_parsing'] = perf_metrics_found
        print(f"   ✅ [PERF] parsing: {perf_metrics_found}")
        print(f"   📊 Memory search times: {len(metrics.memory_search_times_ms)}")
        print(f"   📊 Context execution times: {len(metrics.context_execution_times_s)}")
        print(f"   📊 AI planning times: {len(metrics.ai_planning_times_ms)}")
        print(f"   📊 Total orchestration times: {len(metrics.total_orchestration_times_s)}")
        
    except Exception as e:
        results['perf_parsing'] = False
        print(f"   ❌ [PERF] parsing failed: {e}")
    
    # Acceptance Criterion 2: Extracts context strategy (deep_understanding, etc.)
    print("\n2. Testing context strategy extraction...")
    try:
        context_strategies_found = len(metrics.context_strategies) > 0
        
        results['context_strategy'] = context_strategies_found
        print(f"   ✅ Context strategy extraction: {context_strategies_found}")
        print(f"   📊 Strategies found: {metrics.context_strategies}")
        print(f"   📊 Strategy confidences: {metrics.strategy_confidences}")
        
    except Exception as e:
        results['context_strategy'] = False
        print(f"   ❌ Context strategy extraction failed: {e}")
    
    # Acceptance Criterion 3: Counts memory searches and cache hits
    print("\n3. Testing memory search and cache hit counting...")
    try:
        memory_searches_found = len(metrics.memory_search_queries) > 0
        cache_operations_found = (metrics.cache_hits + metrics.cache_misses) > 0
        
        search_and_cache_counting = memory_searches_found and cache_operations_found
        results['search_cache_counting'] = search_and_cache_counting
        
        print(f"   ✅ Memory search counting: {memory_searches_found}")
        print(f"   📊 Search queries: {len(metrics.memory_search_queries)}")
        print(f"   📊 Search results: {metrics.memory_search_results}")
        print(f"   ✅ Cache hit counting: {cache_operations_found}")
        print(f"   📊 Cache hits: {metrics.cache_hits}")
        print(f"   📊 Cache misses: {metrics.cache_misses}")
        
    except Exception as e:
        results['search_cache_counting'] = False
        print(f"   ❌ Search/cache counting failed: {e}")
    
    # Acceptance Criterion 4: Calculates total orchestration time
    print("\n4. Testing orchestration time calculation...")
    try:
        orchestration_metrics = len(metrics.total_orchestration_times_s) > 0
        orchestration_phases = len(metrics.orchestration_phases) > 0
        
        orchestration_calculation = orchestration_metrics and orchestration_phases
        results['orchestration_time'] = orchestration_calculation
        
        print(f"   ✅ Orchestration time calculation: {orchestration_calculation}")
        print(f"   📊 Total orchestration times: {metrics.total_orchestration_times_s}")
        print(f"   📊 Orchestration phases: {metrics.orchestration_phases}")
        
    except Exception as e:
        results['orchestration_time'] = False
        print(f"   ❌ Orchestration time calculation failed: {e}")
    
    # Acceptance Criterion 5: Handles missing or malformed logs gracefully
    print("\n5. Testing graceful handling of malformed logs...")
    try:
        malformed_metrics, malformed_stats = parse_log_text(SAMPLE_LOGS_WITH_ERRORS)
        
        # Should still extract some metrics despite errors
        some_metrics_extracted = malformed_stats.metrics_extracted > 0
        has_parsing_errors = malformed_stats.parsing_errors > 0 or malformed_stats.unmatched_lines > 0
        
        graceful_handling = some_metrics_extracted  # Should work despite errors
        results['graceful_handling'] = graceful_handling
        
        print(f"   ✅ Graceful error handling: {graceful_handling}")
        print(f"   📊 Metrics extracted: {malformed_stats.metrics_extracted}")
        print(f"   📊 Parsing errors: {malformed_stats.parsing_errors}")
        print(f"   📊 Unmatched lines: {malformed_stats.unmatched_lines}")
        print(f"   📊 Total lines processed: {malformed_stats.total_lines_processed}")
        
    except Exception as e:
        results['graceful_handling'] = False
        print(f"   ❌ Graceful handling test failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FRD ACCEPTANCE CRITERIA RESULTS")
    print("=" * 60)
    
    criteria = [
        ("Parses performance metrics from [PERF] log lines", results.get('perf_parsing', False)),
        ("Extracts context strategy (deep_understanding, etc.)", results.get('context_strategy', False)),
        ("Counts memory searches and cache hits", results.get('search_cache_counting', False)),
        ("Calculates total orchestration time", results.get('orchestration_time', False)),
        ("Handles missing or malformed logs gracefully", results.get('graceful_handling', False))
    ]
    
    passed = sum(1 for _, result in criteria if result)
    total = len(criteria)
    
    for criterion, result in criteria:
        status = "✅" if result else "❌"
        print(f"{status} {criterion}")
    
    print("=" * 60)
    print(f"📊 OVERALL: {passed}/{total} criteria met ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL ACCEPTANCE CRITERIA MET!")
    else:
        print("⚠️  Some criteria need attention")
    
    return passed, total, metrics, stats


async def test_framework_integration():
    """Test integration with evaluation framework"""
    print("\n🔗 Testing Framework Integration")
    print("=" * 40)
    
    try:
        # Test imports from evaluation package
        from app.evaluation import (
            LogParser, AggregatedMetrics, parse_log_file, parse_log_text,
            MetricsExtractor, ExtractedMetric, MetricType, LogParsingStats
        )
        print("✅ All imports successful")
        
        # Test that we can create instances
        parser = LogParser()
        extractor = MetricsExtractor()
        print("✅ Instance creation working")
        
        # Test global functions
        test_metrics, test_stats = parse_log_text("Test log line")
        print("✅ Global functions available")
        
        return True
        
    except Exception as e:
        print(f"❌ Framework integration failed: {e}")
        return False


async def test_detailed_metrics_extraction():
    """Test detailed metrics extraction capabilities"""
    print("\n📊 Testing Detailed Metrics Extraction")
    print("=" * 45)
    
    try:
        metrics, stats = parse_log_text(SAMPLE_PRODUCTION_LOGS)
        
        # Test statistics calculation
        statistics = metrics.calculate_statistics()
        
        print("✅ Statistics calculation working")
        print(f"📊 Performance metrics:")
        print(f"   • Memory search count: {statistics['performance']['memory_search']['count']}")
        print(f"   • Avg memory search time: {statistics['performance']['memory_search']['avg_time_ms']:.1f}ms")
        print(f"   • Context execution count: {statistics['performance']['context_execution']['count']}")
        print(f"   • Avg context execution time: {statistics['performance']['context_execution']['avg_time_s']:.1f}s")
        
        print(f"📊 Context strategies:")
        print(f"   • Strategy distribution: {statistics['context_strategies']['strategy_distribution']}")
        print(f"   • Avg confidence: {statistics['context_strategies']['avg_confidence']:.2f}")
        
        print(f"📊 Memory search patterns:")
        print(f"   • Total searches: {statistics['memory_search']['total_searches']}")
        print(f"   • Avg results per search: {statistics['memory_search']['avg_results_per_search']:.1f}")
        
        print(f"📊 Cache performance:")
        print(f"   • Cache hit rate: {statistics['cache']['cache_hit_rate']:.1%}")
        print(f"   • Total cache operations: {statistics['cache']['total_cache_operations']}")
        
        # Test serialization
        metrics_dict = metrics.to_dict()
        print("✅ Metrics serialization working")
        print(f"📊 Serialized data size: {len(str(metrics_dict))} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Detailed extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_file_parsing():
    """Test file-based log parsing"""
    print("\n📁 Testing File-Based Log Parsing")
    print("=" * 35)
    
    try:
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(SAMPLE_PRODUCTION_LOGS)
            temp_log_path = f.name
        
        try:
            # Parse from file
            file_metrics, file_stats = parse_log_file(temp_log_path)
            
            print("✅ File parsing successful")
            print(f"📊 Lines processed: {file_stats.total_lines_processed}")
            print(f"📊 Metrics extracted: {file_stats.metrics_extracted}")
            print(f"📊 Processing time: {file_stats.processing_time_seconds:.3f}s")
            print(f"📊 Extraction rate: {file_stats.metrics_extracted / file_stats.total_lines_processed:.1%}")
            
            # Test batch processing
            parser = LogParser()
            batch_results = parser.parse_log_files_batch([temp_log_path, temp_log_path], combine_results=True)
            combined_metrics, combined_stats = batch_results
            
            print("✅ Batch processing working")
            print(f"📊 Combined metrics count: {combined_stats.metrics_extracted}")
            print(f"📊 Combined lines processed: {combined_stats.total_lines_processed}")
            
            return True
            
        finally:
            # Clean up temp file
            Path(temp_log_path).unlink()
        
    except Exception as e:
        print(f"❌ File parsing failed: {e}")
        return False


async def test_error_resilience():
    """Test error handling and resilience"""
    print("\n🛡️ Testing Error Resilience")
    print("=" * 30)
    
    try:
        # Test with completely invalid log data
        invalid_logs = """
        This is not a log file at all
        No timestamps, no structure
        Just random text that should not crash the parser
        !!!@#$%^&*()
        """
        
        invalid_metrics, invalid_stats = parse_log_text(invalid_logs)
        
        print("✅ Invalid log handling working")
        print(f"📊 Lines processed: {invalid_stats.total_lines_processed}")
        print(f"📊 Unmatched lines: {invalid_stats.unmatched_lines}")
        print(f"📊 Processing completed without crashes")
        
        # Test with missing file
        try:
            parse_log_file("nonexistent_file.log")
            print("❌ Should have failed with missing file")
            return False
        except FileNotFoundError:
            print("✅ Missing file error handling working")
        
        # Test with very large simulated log
        large_log = SAMPLE_PRODUCTION_LOGS * 1000  # Repeat 1000 times
        large_metrics, large_stats = parse_log_text(large_log)
        
        print("✅ Large log handling working")
        print(f"📊 Large log lines: {large_stats.total_lines_processed}")
        print(f"📊 Large log metrics: {large_stats.metrics_extracted}")
        print(f"📊 Processing time: {large_stats.processing_time_seconds:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resilience test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Task 8: Performance Metrics Extraction - Comprehensive Test Suite")
    print("=" * 75)
    
    # Run acceptance criteria tests
    passed, total, sample_metrics, sample_stats = await test_frd_acceptance_criteria()
    
    # Run integration tests
    integration_success = await test_framework_integration()
    
    # Run detailed extraction tests
    detailed_success = await test_detailed_metrics_extraction()
    
    # Run file parsing tests
    file_success = await test_file_parsing()
    
    # Run error resilience tests
    resilience_success = await test_error_resilience()
    
    # Final summary
    print("\n" + "=" * 75)
    print("🎯 FINAL TEST SUMMARY")
    print("=" * 75)
    print(f"📊 FRD Acceptance Criteria: {passed}/{total} ({(passed/total)*100:.1f}%)")
    print(f"🔗 Framework Integration: {'✅' if integration_success else '❌'}")
    print(f"📊 Detailed Extraction: {'✅' if detailed_success else '❌'}")
    print(f"📁 File Parsing: {'✅' if file_success else '❌'}")
    print(f"🛡️ Error Resilience: {'✅' if resilience_success else '❌'}")
    
    all_tests_passed = (
        passed == total and 
        integration_success and 
        detailed_success and 
        file_success and 
        resilience_success
    )
    
    if all_tests_passed:
        print("\n🎉 TASK 8: PERFORMANCE METRICS EXTRACTION - FULLY COMPLETE!")
        print("✅ All acceptance criteria met")
        print("✅ Framework integration working")
        print("✅ Detailed metrics extraction operational")
        print("✅ File-based parsing functional")
        print("✅ Error handling robust")
        print("🚀 Ready for integration with Tasks 1-7!")
        
        # Show sample results
        print(f"\n📊 SAMPLE EXTRACTION RESULTS:")
        print(f"   • Total lines processed: {sample_stats.total_lines_processed}")
        print(f"   • Metrics extracted: {sample_stats.metrics_extracted}")
        print(f"   • Performance metrics: {len(sample_metrics.memory_search_times_ms)} timing measurements")
        print(f"   • Context strategies: {len(sample_metrics.context_strategies)} strategy decisions")
        print(f"   • Cache operations: {sample_metrics.cache_hits + sample_metrics.cache_misses} cache interactions")
        
    else:
        print("\n⚠️ Some tests failed. Review output above.")
    
    return all_tests_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)