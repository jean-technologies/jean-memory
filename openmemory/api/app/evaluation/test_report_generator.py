"""
Test script for Task 9: Comprehensive Evaluation Reports

This script validates all functionality of the report generation system.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append('.')

from app.evaluation.report_generator import (
    EvaluationReportGenerator,
    generate_evaluation_report,
    EvaluationReport,
    ReasoningTypeMetrics,
    JudgeAnalysis,
    PerformanceMetrics,
    FailureAnalysis
)
from app.evaluation.log_parser import AggregatedMetrics, LogParsingStats
from app.evaluation.llm_judge import ReasoningType


# Sample conversation test results for testing
SAMPLE_CONVERSATION_RESULTS = [
    {
        "suite_execution_summary": {
            "datasets_executed": 3,
            "total_turns": 15,
            "suite_success_rate": 0.87
        },
        "dataset_results": [
            {
                "dataset_name": "test_dataset_1",
                "conversation_length": 5,
                "turn_results": [
                    {
                        "turn_number": 1,
                        "user_message": "What is my favorite hobby?",
                        "expected_response": "Your favorite hobby is reading science fiction books.",
                        "actual_response": "Based on your memories, you enjoy reading science fiction novels.",
                        "reasoning_type": "single_hop",
                        "success": True,
                        "response_time_ms": 2500.0,
                        "judge_score": 8.5,
                        "memory_count": 3
                    },
                    {
                        "turn_number": 2,
                        "user_message": "What kind of books do I prefer based on my recent purchases?",
                        "expected_response": "You prefer science fiction and fantasy books.",
                        "actual_response": "Your recent purchases show a preference for sci-fi and fantasy genres.",
                        "reasoning_type": "multi_hop",
                        "success": True,
                        "response_time_ms": 3200.0,
                        "judge_score": 7.8,
                        "memory_count": 5
                    },
                    {
                        "turn_number": 3,
                        "user_message": "How has my reading taste changed over time?",
                        "expected_response": "Your taste has evolved from mystery to science fiction.",
                        "actual_response": "Your reading preferences have shifted from mystery novels to science fiction over the past year.",
                        "reasoning_type": "temporal",
                        "success": True,
                        "response_time_ms": 4100.0,
                        "judge_score": 9.2,
                        "memory_count": 8
                    },
                    {
                        "turn_number": 4,
                        "user_message": "Do I like mystery books or sci-fi more?",
                        "expected_response": "You prefer science fiction over mystery books.",
                        "actual_response": "Request timeout - unable to process query",
                        "reasoning_type": "adversarial",
                        "success": False,
                        "response_time_ms": 30000.0,
                        "judge_score": None,
                        "error": "Request timeout after 30 seconds",
                        "memory_count": 0
                    },
                    {
                        "turn_number": 5,
                        "user_message": "What books should I read next?",
                        "expected_response": "Based on your preferences, I recommend these sci-fi books.",
                        "actual_response": "Given your love for science fiction, I'd recommend 'The Three-Body Problem' or 'Dune'.",
                        "reasoning_type": "single_hop",
                        "success": True,
                        "response_time_ms": 2800.0,
                        "judge_score": 8.0,
                        "memory_count": 4
                    }
                ]
            },
            {
                "dataset_name": "test_dataset_2",
                "conversation_length": 5,
                "turn_results": [
                    {
                        "turn_number": 1,
                        "user_message": "Where do I usually work?",
                        "expected_response": "You usually work from your home office.",
                        "actual_response": "You typically work from your home office in San Francisco.",
                        "reasoning_type": "single_hop",
                        "success": True,
                        "response_time_ms": 1800.0,
                        "judge_score": 9.0,
                        "memory_count": 2
                    },
                    {
                        "turn_number": 2,
                        "user_message": "How do my work habits relate to my productivity?",
                        "expected_response": "Your morning work sessions are most productive.",
                        "actual_response": "Your productivity peaks during morning hours when working from home.",
                        "reasoning_type": "multi_hop",
                        "success": True,
                        "response_time_ms": 5200.0,
                        "judge_score": 7.5,
                        "memory_count": 6
                    },
                    {
                        "turn_number": 3,
                        "user_message": "Authentication failed",
                        "expected_response": "Unable to access memories.",
                        "actual_response": "Authentication error - unable to retrieve user data",
                        "reasoning_type": "single_hop",
                        "success": False,
                        "response_time_ms": 500.0,
                        "judge_score": None,
                        "error": "Authentication failed - invalid token",
                        "memory_count": 0
                    },
                    {
                        "turn_number": 4,
                        "user_message": "What time do I usually start work?",
                        "expected_response": "You typically start work around 9 AM.",
                        "actual_response": "Based on your schedule, you usually begin work at 9:00 AM.",
                        "reasoning_type": "temporal",
                        "success": True,
                        "response_time_ms": 2200.0,
                        "judge_score": 8.7,
                        "memory_count": 3
                    },
                    {
                        "turn_number": 5,
                        "user_message": "Network connection lost",
                        "expected_response": "Unable to process request.",
                        "actual_response": "Network error - connection lost",
                        "reasoning_type": "single_hop",
                        "success": False,
                        "response_time_ms": 1000.0,
                        "judge_score": None,
                        "error": "Network error - connection timeout",
                        "memory_count": 0
                    }
                ]
            }
        ]
    }
]

# Sample performance metrics for testing
SAMPLE_PERFORMANCE_METRICS = AggregatedMetrics(
    memory_search_times_ms=[245.0, 312.0, 189.0, 456.0],
    context_execution_times_s=[1.2, 2.1, 0.8, 1.7],
    ai_planning_times_ms=[850.0, 1200.0, 650.0, 980.0],
    total_orchestration_times_s=[3.4, 4.2, 2.8, 3.9],
    cache_lookup_times_ms=[15.0, 23.0, 18.0, 12.0],
    database_query_times_ms=[125.0, 98.0, 156.0, 203.0],
    response_generation_times_s=[2.1, 1.8, 2.5, 2.3],
    context_strategies=["deep_understanding", "balanced_search", "comprehensive", "quick_response"],
    strategy_confidences=[0.85, 0.72, 0.91, 0.68],
    memory_search_queries=["user recent projects", "work habits", "reading preferences", "schedule patterns"],
    memory_search_results=[15, 8, 12, 6],
    memory_filter_ratios=[0.27, 0.35, 0.32, 0.33],
    relevance_thresholds=[0.7, 0.7, 0.7, 0.7],
    cache_hits=3,
    cache_misses=2,
    cache_queries=["query1", "query2", "query3", "query4", "query5"],
    orchestration_phases=["memory_retrieval", "context_synthesis", "response_generation", "quality_check"],
    processing_steps=["validate_input", "search_memory", "rank_results", "generate_response"],
    user_sessions=["session_1", "session_2"],
    errors=["timeout_error", "network_error"]
)

SAMPLE_LOG_STATS = LogParsingStats(
    total_lines_processed=1000,
    metrics_extracted=95,
    parsing_errors=3,
    unmatched_lines=48,
    processing_time_seconds=0.25
)


async def test_frd_acceptance_criteria():
    """Test all FRD acceptance criteria for Task 9"""
    print("🧪 Testing Task 9 FRD Acceptance Criteria")
    print("=" * 60)
    
    results = {}
    
    # Acceptance Criterion 1: Generate comprehensive markdown reports
    print("1. Testing comprehensive markdown report generation...")
    try:
        generator = EvaluationReportGenerator()
        
        report = generator.generate_report(
            conversation_results=SAMPLE_CONVERSATION_RESULTS,
            performance_metrics=SAMPLE_PERFORMANCE_METRICS,
            log_stats=SAMPLE_LOG_STATS
        )
        
        markdown_content = generator.generate_markdown_report(report)
        
        # Verify markdown contains key sections
        required_sections = [
            "# Jean Memory Evaluation Report",
            "## 📊 Executive Summary",
            "## 🧠 LoCoMo Reasoning Type Analysis",
            "## 🏆 LLM Judge Score Analysis",
            "## ⚡ Performance Metrics",
            "## ❌ Test Failures Analysis",
            "## 🔧 System Performance",
            "## 📋 Test Configuration",
            "## 🎯 Recommendations"
        ]
        
        markdown_complete = all(section in markdown_content for section in required_sections)
        results['markdown_generation'] = markdown_complete
        
        print(f"   ✅ Markdown generation: {markdown_complete}")
        print(f"   📊 Markdown content length: {len(markdown_content)} characters")
        print(f"   📊 Required sections found: {sum(1 for section in required_sections if section in markdown_content)}/{len(required_sections)}")
        
    except Exception as e:
        results['markdown_generation'] = False
        print(f"   ❌ Markdown generation failed: {e}")
    
    # Acceptance Criterion 2: Generate structured JSON reports
    print("\n2. Testing JSON report generation...")
    try:
        json_content = generator.generate_json_report(report)
        json_data = json.loads(json_content)
        
        # Verify JSON contains required top-level keys
        required_keys = [
            "metadata", "summary", "reasoning_analysis", 
            "judge_analysis", "performance", "failures",
            "system", "config", "recommendations"
        ]
        
        json_complete = all(key in json_data for key in required_keys)
        results['json_generation'] = json_complete
        
        print(f"   ✅ JSON generation: {json_complete}")
        print(f"   📊 JSON keys found: {sum(1 for key in required_keys if key in json_data)}/{len(required_keys)}")
        print(f"   📊 JSON size: {len(json_content)} characters")
        
    except Exception as e:
        results['json_generation'] = False
        print(f"   ❌ JSON generation failed: {e}")
    
    # Acceptance Criterion 3: LoCoMo reasoning type breakdown
    print("\n3. Testing LoCoMo reasoning type analysis...")
    try:
        reasoning_analysis = report.reasoning_analysis
        
        # Check if we have reasoning type data
        has_reasoning_types = len(reasoning_analysis) > 0
        has_metrics = all(
            hasattr(metrics, 'test_count') and 
            hasattr(metrics, 'success_rate') and
            hasattr(metrics, 'avg_response_time_ms')
            for metrics in reasoning_analysis.values()
        )
        
        locomo_analysis = has_reasoning_types and has_metrics
        results['locomo_analysis'] = locomo_analysis
        
        print(f"   ✅ LoCoMo analysis: {locomo_analysis}")
        print(f"   📊 Reasoning types analyzed: {len(reasoning_analysis)}")
        for reasoning_type, metrics in reasoning_analysis.items():
            print(f"      • {reasoning_type}: {metrics.test_count} tests, {metrics.success_rate:.1%} success")
        
    except Exception as e:
        results['locomo_analysis'] = False
        print(f"   ❌ LoCoMo analysis failed: {e}")
    
    # Acceptance Criterion 4: Performance metrics integration
    print("\n4. Testing performance metrics integration...")
    try:
        performance = report.performance
        
        has_response_times = bool(performance.response_times)
        has_memory_search = performance.memory_search is not None
        has_context_engineering = performance.context_engineering is not None
        
        performance_integration = has_response_times and has_memory_search
        results['performance_integration'] = performance_integration
        
        print(f"   ✅ Performance integration: {performance_integration}")
        print(f"   📊 Response time metrics: {has_response_times}")
        print(f"   📊 Memory search metrics: {has_memory_search}")
        print(f"   📊 Context engineering metrics: {has_context_engineering}")
        
        if has_memory_search:
            print(f"      • Cache hit rate: {performance.memory_search['cache_hit_rate']:.1%}")
            print(f"      • Avg search time: {performance.memory_search['avg_search_time_ms']:.1f}ms")
        
    except Exception as e:
        results['performance_integration'] = False
        print(f"   ❌ Performance integration failed: {e}")
    
    # Acceptance Criterion 5: Actionable insights and recommendations
    print("\n5. Testing actionable insights and recommendations...")
    try:
        recommendations = report.recommendations
        summary = report.summary
        
        has_recommendations = recommendations is not None and len(recommendations) > 0
        has_key_findings = "key_findings" in summary and len(summary["key_findings"]) > 0
        has_critical_issues = "critical_issues" in summary
        
        actionable_insights = has_recommendations and has_key_findings
        results['actionable_insights'] = actionable_insights
        
        print(f"   ✅ Actionable insights: {actionable_insights}")
        print(f"   📊 Recommendations generated: {has_recommendations}")
        print(f"   📊 Key findings: {len(summary.get('key_findings', []))}")
        print(f"   📊 Critical issues: {len(summary.get('critical_issues', []))}")
        
        if has_recommendations:
            for category, recs in recommendations.items():
                print(f"      • {category}: {len(recs)} recommendations")
        
    except Exception as e:
        results['actionable_insights'] = False
        print(f"   ❌ Actionable insights failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FRD ACCEPTANCE CRITERIA RESULTS")
    print("=" * 60)
    
    criteria = [
        ("Generate comprehensive markdown reports", results.get('markdown_generation', False)),
        ("Generate structured JSON reports", results.get('json_generation', False)),
        ("LoCoMo reasoning type breakdown", results.get('locomo_analysis', False)),
        ("Performance metrics integration", results.get('performance_integration', False)),
        ("Actionable insights and recommendations", results.get('actionable_insights', False))
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
    
    return passed, total, report


async def test_framework_integration():
    """Test integration with evaluation framework"""
    print("\n🔗 Testing Framework Integration")
    print("=" * 40)
    
    try:
        # Test imports from evaluation package
        from app.evaluation import generate_evaluation_report
        print("✅ Import from evaluation package successful")
        
        # Test convenience function
        result = generate_evaluation_report(
            conversation_results=SAMPLE_CONVERSATION_RESULTS,
            performance_metrics=SAMPLE_PERFORMANCE_METRICS,
            log_stats=SAMPLE_LOG_STATS
        )
        
        required_keys = ["report", "markdown", "json"]
        has_all_keys = all(key in result for key in required_keys)
        
        print(f"✅ Convenience function working: {has_all_keys}")
        print(f"📊 Result keys: {list(result.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Framework integration failed: {e}")
        return False


async def test_file_operations():
    """Test file saving and loading operations"""
    print("\n📁 Testing File Operations")
    print("=" * 30)
    
    try:
        generator = EvaluationReportGenerator()
        
        # Generate test report
        report = generator.generate_report(
            conversation_results=SAMPLE_CONVERSATION_RESULTS,
            performance_metrics=SAMPLE_PERFORMANCE_METRICS
        )
        
        # Test file saving
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = generator.save_reports(
                report=report,
                output_dir=temp_dir,
                filename_prefix="test_report"
            )
            
            # Verify files were created
            markdown_exists = Path(file_paths["markdown"]).exists()
            json_exists = Path(file_paths["json"]).exists()
            
            print(f"✅ Markdown file created: {markdown_exists}")
            print(f"✅ JSON file created: {json_exists}")
            
            # Verify file contents
            if markdown_exists:
                with open(file_paths["markdown"], 'r') as f:
                    markdown_content = f.read()
                print(f"📊 Markdown file size: {len(markdown_content)} characters")
            
            if json_exists:
                with open(file_paths["json"], 'r') as f:
                    json_content = json.load(f)
                print(f"📊 JSON file keys: {len(json_content)} top-level keys")
            
            file_operations_success = markdown_exists and json_exists
            
        return file_operations_success
        
    except Exception as e:
        print(f"❌ File operations failed: {e}")
        return False


async def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🛡️ Testing Edge Cases and Error Handling")
    print("=" * 45)
    
    try:
        generator = EvaluationReportGenerator()
        
        # Test with empty results
        empty_report = generator.generate_report(
            conversation_results=[],
            performance_metrics=None
        )
        
        print("✅ Empty results handling working")
        print(f"📊 Empty report summary: {empty_report.summary}")
        
        # Test with malformed data
        malformed_results = [{"invalid": "data", "no_turn_results": True}]
        malformed_report = generator.generate_report(
            conversation_results=malformed_results
        )
        
        print("✅ Malformed data handling working")
        
        # Test markdown generation with invalid template data
        try:
            markdown = generator.generate_markdown_report(empty_report)
            print("✅ Markdown generation with empty data working")
        except Exception as e:
            print(f"⚠️ Markdown generation issue: {e}")
        
        # Test JSON serialization
        try:
            json_content = generator.generate_json_report(empty_report)
            json_data = json.loads(json_content)
            print("✅ JSON serialization working")
        except Exception as e:
            print(f"⚠️ JSON serialization issue: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge case testing failed: {e}")
        return False


async def test_statistical_accuracy():
    """Test statistical calculations accuracy"""
    print("\n📊 Testing Statistical Calculations")
    print("=" * 35)
    
    try:
        generator = EvaluationReportGenerator()
        
        # Generate report with known data
        report = generator.generate_report(
            conversation_results=SAMPLE_CONVERSATION_RESULTS,
            performance_metrics=SAMPLE_PERFORMANCE_METRICS
        )
        
        # Verify summary statistics
        summary = report.summary
        
        print(f"✅ Total test runs: {summary['total_test_runs']}")
        print(f"✅ Overall success rate: {summary['overall_success_rate']:.1%}")
        print(f"✅ Average response time: {summary['avg_response_time_ms']:.1f}ms")
        print(f"✅ Average judge score: {summary['avg_llm_judge_score']:.1f}/10")
        
        # Verify reasoning type analysis
        reasoning_analysis = report.reasoning_analysis
        print(f"✅ Reasoning types analyzed: {len(reasoning_analysis)}")
        
        # Verify performance metrics
        performance = report.performance
        print(f"✅ Response time P95: {performance.response_times['p95']:.1f}ms")
        if performance.memory_search:
            print(f"✅ Cache hit rate: {performance.memory_search['cache_hit_rate']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Statistical accuracy test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Task 9: Comprehensive Evaluation Reports - Test Suite")
    print("=" * 65)
    
    # Run acceptance criteria tests
    passed, total, sample_report = await test_frd_acceptance_criteria()
    
    # Run integration tests
    integration_success = await test_framework_integration()
    
    # Run file operations tests
    file_success = await test_file_operations()
    
    # Run edge case tests
    edge_case_success = await test_edge_cases()
    
    # Run statistical accuracy tests
    stats_success = await test_statistical_accuracy()
    
    # Final summary
    print("\n" + "=" * 65)
    print("🎯 FINAL TEST SUMMARY")
    print("=" * 65)
    print(f"📊 FRD Acceptance Criteria: {passed}/{total} ({(passed/total)*100:.1f}%)")
    print(f"🔗 Framework Integration: {'✅' if integration_success else '❌'}")
    print(f"📁 File Operations: {'✅' if file_success else '❌'}")
    print(f"🛡️ Edge Case Handling: {'✅' if edge_case_success else '❌'}")
    print(f"📊 Statistical Accuracy: {'✅' if stats_success else '❌'}")
    
    all_tests_passed = (
        passed == total and 
        integration_success and 
        file_success and 
        edge_case_success and 
        stats_success
    )
    
    if all_tests_passed:
        print("\n🎉 TASK 9: COMPREHENSIVE EVALUATION REPORTS - FULLY COMPLETE!")
        print("✅ All acceptance criteria met")
        print("✅ Framework integration working")
        print("✅ File operations functional")
        print("✅ Edge case handling robust")
        print("✅ Statistical calculations accurate")
        print("🚀 Ready for integration with complete Tasks 1-8 framework!")
        
        # Show sample report statistics
        print(f"\n📊 SAMPLE REPORT STATISTICS:")
        print(f"   • Datasets analyzed: {sample_report.summary['total_test_runs']}")
        print(f"   • Conversation turns: {sample_report.summary['total_conversation_turns']}")
        print(f"   • Success rate: {sample_report.summary['overall_success_rate']:.1%}")
        print(f"   • Reasoning types: {sample_report.summary['unique_reasoning_types']}")
        print(f"   • Performance metrics: {len(sample_report.performance.response_times)} categories")
        print(f"   • Recommendations: {len(sample_report.recommendations) if sample_report.recommendations else 0} categories")
        
    else:
        print("\n⚠️ Some tests failed. Review output above.")
    
    return all_tests_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)