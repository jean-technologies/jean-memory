#!/usr/bin/env python3
"""
Comprehensive Evaluation Runner for Jean Memory
Runs all evaluation suites and provides consolidated metrics and results
"""

import asyncio
import json
import logging
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add project paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "openmemory" / "api"))
sys.path.insert(0, str(current_dir / "utils"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveEvaluationRunner:
    """Runs all evaluation suites and consolidates results"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.start_time = None
        self.end_time = None
        self.results = {
            'context_engineering': {},
            'memory_intelligence': {},
            'performance': {},
            'overall_metrics': {},
            'summary': {}
        }
        
    async def run_all_evaluations(self, quick_mode: bool = False) -> Dict[str, Any]:
        """Run all evaluation suites and return consolidated results"""
        self.start_time = time.time()
        logger.info("🚀 Starting comprehensive Jean Memory evaluation suite...")
        
        try:
            # Run each evaluation category
            await self._run_context_engineering_evaluations(quick_mode)
            await self._run_memory_intelligence_evaluations(quick_mode)
            await self._run_performance_evaluations(quick_mode)
            
            # Calculate overall metrics
            self._calculate_overall_metrics()
            
            # Generate summary
            self._generate_summary()
            
            self.end_time = time.time()
            self.results['execution_time'] = self.end_time - self.start_time
            
            logger.info(f"✅ Comprehensive evaluation completed in {self.results['execution_time']:.2f}s")
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive evaluation failed: {e}", exc_info=True)
            self.results['error'] = str(e)
            self.results['success'] = False
            return self.results
    
    async def _run_context_engineering_evaluations(self, quick_mode: bool):
        """Run context engineering evaluation suite"""
        logger.info("📊 Running Context Engineering Evaluations...")
        
        try:
            from context_engineering.quality_scoring import ContextQualityScoringEvaluator, create_context_quality_scenarios
            
            # Configure evaluator
            config = {
                'quality_threshold': self.config.get('context_quality_threshold', 75.0)
            }
            evaluator = ContextQualityScoringEvaluator(config)
            
            # Load scenarios (subset for quick mode)
            scenarios = create_context_quality_scenarios()
            if quick_mode:
                scenarios = scenarios[:3]  # First 3 scenarios for quick test
            
            # Run evaluation
            start_time = time.time()
            results = await evaluator.run_evaluation(scenarios)
            execution_time = time.time() - start_time
            
            # Get summary statistics
            summary = evaluator.get_summary_stats()
            
            # Store results
            self.results['context_engineering'] = {
                'evaluator': 'ContextQualityScoringEvaluator',
                'scenarios_tested': len(scenarios),
                'execution_time': execution_time,
                'summary': summary,
                'detailed_results': [r.to_dict() for r in results],
                'success': True
            }
            
            logger.info(f"  ✅ Context Engineering: {summary['passed']}/{summary['total_tests']} passed ({summary['pass_rate']:.1f}%)")
            
        except Exception as e:
            logger.error(f"  ❌ Context Engineering evaluation failed: {e}")
            self.results['context_engineering'] = {
                'error': str(e),
                'success': False,
                'execution_time': 0
            }
    
    async def _run_memory_intelligence_evaluations(self, quick_mode: bool):
        """Run memory intelligence evaluation suite"""
        logger.info("🧠 Running Memory Intelligence Evaluations...")
        
        try:
            from memory_intelligence.triage_accuracy import MemoryTriageAccuracyEvaluator, create_default_scenarios
            
            # Configure evaluator
            config = {
                'accuracy_threshold': self.config.get('triage_accuracy_threshold', 90.0)
            }
            evaluator = MemoryTriageAccuracyEvaluator(config)
            
            # Load scenarios (subset for quick mode)
            scenarios = create_default_scenarios()
            if quick_mode:
                scenarios = scenarios[:5]  # First 5 scenarios for quick test
            
            # Run evaluation
            start_time = time.time()
            results = await evaluator.run_evaluation(scenarios)
            execution_time = time.time() - start_time
            
            # Get detailed metrics
            metrics = evaluator._calculate_metrics()
            summary = evaluator.get_summary_stats()
            
            # Store results
            self.results['memory_intelligence'] = {
                'evaluator': 'MemoryTriageAccuracyEvaluator',
                'scenarios_tested': len(scenarios),
                'execution_time': execution_time,
                'metrics': metrics,
                'summary': summary,
                'confusion_matrix': {
                    'true_positives': evaluator.true_positives,
                    'true_negatives': evaluator.true_negatives,
                    'false_positives': evaluator.false_positives,
                    'false_negatives': evaluator.false_negatives
                },
                'misclassified_count': len(evaluator.misclassified_messages),
                'detailed_results': [r.to_dict() for r in results],
                'success': True
            }
            
            logger.info(f"  ✅ Memory Intelligence: {metrics['accuracy']:.1f}% accuracy, {metrics['f1_score']:.1f}% F1 score")
            
        except Exception as e:
            logger.error(f"  ❌ Memory Intelligence evaluation failed: {e}")
            self.results['memory_intelligence'] = {
                'error': str(e),
                'success': False,
                'execution_time': 0
            }
    
    async def _run_performance_evaluations(self, quick_mode: bool):
        """Run performance evaluation suite"""
        logger.info("⚡ Running Performance Evaluations...")
        
        try:
            # Import performance evaluator components
            sys.path.insert(0, str(current_dir / "performance"))
            from fast_path_benchmarks import FastPathBenchmarkEvaluator, create_fast_path_scenarios
            
            # Configure evaluator
            config = {
                'target_time': self.config.get('fast_path_target', 3.0),
                'warmup_runs': 1 if quick_mode else 2
            }
            evaluator = FastPathBenchmarkEvaluator(config)
            
            # Load scenarios (subset for quick mode)
            scenarios = create_fast_path_scenarios()
            if quick_mode:
                scenarios = scenarios[:3]  # First 3 scenarios for quick test
            
            # Run evaluation
            start_time = time.time()
            results = await evaluator.run_evaluation(scenarios)
            execution_time = time.time() - start_time
            
            # Get performance statistics
            perf_stats = evaluator._calculate_performance_stats()
            summary = evaluator.get_summary_stats()
            
            # Store results
            self.results['performance'] = {
                'evaluator': 'FastPathBenchmarkEvaluator',
                'scenarios_tested': len(scenarios),
                'execution_time': execution_time,
                'performance_stats': perf_stats,
                'summary': summary,
                'failed_scenarios_count': len(evaluator.failed_scenarios),
                'detailed_results': [r.to_dict() for r in results],
                'success': True
            }
            
            logger.info(f"  ✅ Performance: {perf_stats['target_met_pct']:.1f}% met target, P95: {perf_stats['p95_latency']:.2f}s")
            
        except Exception as e:
            logger.error(f"  ⚠️ Performance evaluation failed (may require system setup): {e}")
            # For performance tests, we'll create a mock result if real system isn't available
            self.results['performance'] = {
                'error': str(e),
                'success': False,
                'execution_time': 0,
                'note': 'Performance tests require full system setup'
            }
    
    def _calculate_overall_metrics(self):
        """Calculate overall system metrics across all evaluation categories"""
        logger.info("📊 Calculating overall system metrics...")
        
        overall_metrics = {
            'system_health_score': 0.0,
            'categories_tested': 0,
            'categories_passed': 0,
            'total_tests_run': 0,
            'total_tests_passed': 0,
            'evaluation_coverage': {},
            'key_metrics': {}
        }
        
        # Process each category
        for category, results in self.results.items():
            if category in ['context_engineering', 'memory_intelligence', 'performance']:
                if results.get('success', False):
                    overall_metrics['categories_tested'] += 1
                    
                    # Extract test counts
                    summary = results.get('summary', {})
                    total_tests = summary.get('total_tests', 0)
                    passed_tests = summary.get('passed', 0)
                    
                    overall_metrics['total_tests_run'] += total_tests
                    overall_metrics['total_tests_passed'] += passed_tests
                    
                    # Category-specific metrics
                    if category == 'context_engineering':
                        pass_rate = summary.get('pass_rate', 0)
                        avg_score = summary.get('average_score', 0)
                        overall_metrics['key_metrics']['context_quality_pass_rate'] = pass_rate
                        overall_metrics['key_metrics']['context_quality_avg_score'] = avg_score
                        if pass_rate >= 80:
                            overall_metrics['categories_passed'] += 1
                    
                    elif category == 'memory_intelligence':
                        metrics = results.get('metrics', {})
                        accuracy = metrics.get('accuracy', 0)
                        f1_score = metrics.get('f1_score', 0)
                        overall_metrics['key_metrics']['memory_triage_accuracy'] = accuracy
                        overall_metrics['key_metrics']['memory_triage_f1_score'] = f1_score
                        if accuracy >= 85:
                            overall_metrics['categories_passed'] += 1
                    
                    elif category == 'performance':
                        perf_stats = results.get('performance_stats', {})
                        target_met_pct = perf_stats.get('target_met_pct', 0)
                        p95_latency = perf_stats.get('p95_latency', 0)
                        overall_metrics['key_metrics']['fast_path_target_met_pct'] = target_met_pct
                        overall_metrics['key_metrics']['fast_path_p95_latency'] = p95_latency
                        if target_met_pct >= 80:
                            overall_metrics['categories_passed'] += 1
        
        # Calculate overall system health score
        if overall_metrics['categories_tested'] > 0:
            category_score = (overall_metrics['categories_passed'] / overall_metrics['categories_tested']) * 100
            
            if overall_metrics['total_tests_run'] > 0:
                test_score = (overall_metrics['total_tests_passed'] / overall_metrics['total_tests_run']) * 100
                overall_metrics['system_health_score'] = (category_score * 0.6 + test_score * 0.4)
            else:
                overall_metrics['system_health_score'] = category_score
        
        # Evaluation coverage
        overall_metrics['evaluation_coverage'] = {
            'context_engineering': self.results.get('context_engineering', {}).get('success', False),
            'memory_intelligence': self.results.get('memory_intelligence', {}).get('success', False),
            'performance': self.results.get('performance', {}).get('success', False)
        }
        
        self.results['overall_metrics'] = overall_metrics
        
        logger.info(f"  📊 Overall System Health Score: {overall_metrics['system_health_score']:.1f}/100")
        logger.info(f"  📈 Categories Passed: {overall_metrics['categories_passed']}/{overall_metrics['categories_tested']}")
    
    def _generate_summary(self):
        """Generate executive summary of evaluation results"""
        logger.info("📋 Generating evaluation summary...")
        
        overall = self.results['overall_metrics']
        
        # Determine overall status
        health_score = overall['system_health_score']
        if health_score >= 90:
            status = "EXCELLENT"
            status_emoji = "🎉"
        elif health_score >= 75:
            status = "GOOD"
            status_emoji = "✅"
        elif health_score >= 60:
            status = "FAIR"
            status_emoji = "⚠️"
        else:
            status = "NEEDS_IMPROVEMENT"
            status_emoji = "❌"
        
        # Key findings
        findings = []
        key_metrics = overall.get('key_metrics', {})
        
        # Context Engineering findings
        if 'context_quality_pass_rate' in key_metrics:
            pass_rate = key_metrics['context_quality_pass_rate']
            if pass_rate >= 90:
                findings.append("✅ Context quality exceeds 90% pass rate target")
            elif pass_rate >= 75:
                findings.append("⚠️ Context quality meets 75% threshold but below 90% target")
            else:
                findings.append("❌ Context quality below 75% threshold - needs improvement")
        
        # Memory Intelligence findings
        if 'memory_triage_accuracy' in key_metrics:
            accuracy = key_metrics['memory_triage_accuracy']
            if accuracy >= 95:
                findings.append("✅ Memory triage accuracy exceeds 95% target")
            elif accuracy >= 85:
                findings.append("⚠️ Memory triage accuracy meets 85% threshold but below 95% target")
            else:
                findings.append("❌ Memory triage accuracy below 85% threshold - needs improvement")
        
        # Performance findings
        if 'fast_path_p95_latency' in key_metrics:
            p95_latency = key_metrics['fast_path_p95_latency']
            if p95_latency <= 3.0:
                findings.append("✅ Fast path latency meets <3s P95 target")
            elif p95_latency <= 5.0:
                findings.append("⚠️ Fast path latency above 3s target but under 5s")
            else:
                findings.append("❌ Fast path latency significantly above 3s target")
        
        # Recommendations
        recommendations = []
        if health_score < 75:
            recommendations.append("Focus on failing evaluation categories")
            recommendations.append("Review detailed results for specific improvement areas")
        
        if key_metrics.get('context_quality_pass_rate', 100) < 80:
            recommendations.append("Improve context relevance and quality scoring")
        
        if key_metrics.get('memory_triage_accuracy', 100) < 90:
            recommendations.append("Optimize memory triage decision algorithms")
            recommendations.append("Review misclassified examples in golden dataset")
        
        if key_metrics.get('fast_path_p95_latency', 0) > 3.0:
            recommendations.append("Optimize fast path performance for <3s target")
            recommendations.append("Consider caching or async optimization strategies")
        
        summary = {
            'overall_status': status,
            'status_emoji': status_emoji,
            'system_health_score': health_score,
            'evaluation_timestamp': datetime.now().isoformat(),
            'total_execution_time': self.results.get('execution_time', 0),
            'categories_evaluated': overall['categories_tested'],
            'key_findings': findings,
            'recommendations': recommendations,
            'next_steps': [
                "Address high-priority recommendations",
                "Run full evaluation suite in production environment",
                "Set up continuous monitoring for key metrics",
                "Expand golden datasets based on real usage patterns"
            ]
        }
        
        self.results['summary'] = summary
    
    def print_results(self, detailed: bool = False):
        """Print formatted results to console"""
        summary = self.results.get('summary', {})
        overall = self.results.get('overall_metrics', {})
        
        print("\n" + "="*80)
        print("🎯 JEAN MEMORY COMPREHENSIVE EVALUATION RESULTS")
        print("="*80)
        
        # Overall status
        status_emoji = summary.get('status_emoji', '❓')
        status = summary.get('overall_status', 'UNKNOWN')
        health_score = summary.get('system_health_score', 0)
        
        print(f"{status_emoji} Overall Status: {status} ({health_score:.1f}/100)")
        print(f"⏱️  Total Execution Time: {summary.get('total_execution_time', 0):.2f}s")
        print(f"📊 Categories Evaluated: {summary.get('categories_evaluated', 0)}")
        
        # Category results
        print(f"\n📈 CATEGORY RESULTS:")
        print("-" * 40)
        
        for category in ['context_engineering', 'memory_intelligence', 'performance']:
            result = self.results.get(category, {})
            if result.get('success'):
                emoji = "✅"
                if category == 'context_engineering':
                    summary_stats = result.get('summary', {})
                    detail = f"{summary_stats.get('pass_rate', 0):.1f}% pass rate"
                elif category == 'memory_intelligence':
                    metrics = result.get('metrics', {})
                    detail = f"{metrics.get('accuracy', 0):.1f}% accuracy"
                elif category == 'performance':
                    perf_stats = result.get('performance_stats', {})
                    detail = f"P95: {perf_stats.get('p95_latency', 0):.2f}s"
                else:
                    detail = "Completed"
            else:
                emoji = "❌"
                detail = "Failed or skipped"
            
            category_name = category.replace('_', ' ').title()
            print(f"{emoji} {category_name:20} | {detail}")
        
        # Key findings
        findings = summary.get('key_findings', [])
        if findings:
            print(f"\n🔍 KEY FINDINGS:")
            print("-" * 40)
            for finding in findings:
                print(f"  {finding}")
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            print("-" * 40)
            for rec in recommendations:
                print(f"  • {rec}")
        
        # Detailed results
        if detailed:
            print(f"\n📊 DETAILED METRICS:")
            print("-" * 40)
            key_metrics = overall.get('key_metrics', {})
            for metric, value in key_metrics.items():
                formatted_metric = metric.replace('_', ' ').title()
                if isinstance(value, float):
                    print(f"  {formatted_metric}: {value:.2f}")
                else:
                    print(f"  {formatted_metric}: {value}")
    
    def save_results(self, filepath: str):
        """Save results to JSON file"""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"📁 Results saved to {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to save results to {filepath}: {e}")

async def main():
    """Main evaluation runner"""
    parser = argparse.ArgumentParser(description='Run comprehensive Jean Memory evaluations')
    parser.add_argument('--quick', action='store_true', help='Run quick evaluation with subset of tests')
    parser.add_argument('--detailed', action='store_true', help='Show detailed results')
    parser.add_argument('--output-file', help='Save results to JSON file')
    parser.add_argument('--context-threshold', type=float, default=75.0, help='Context quality threshold')
    parser.add_argument('--triage-threshold', type=float, default=90.0, help='Memory triage accuracy threshold')
    parser.add_argument('--performance-target', type=float, default=3.0, help='Fast path performance target (seconds)')
    
    args = parser.parse_args()
    
    # Configure evaluation
    config = {
        'context_quality_threshold': args.context_threshold,
        'triage_accuracy_threshold': args.triage_threshold,
        'fast_path_target': args.performance_target
    }
    
    # Run evaluations
    runner = ComprehensiveEvaluationRunner(config)
    
    print("🚀 Starting Jean Memory Comprehensive Evaluation Suite...")
    if args.quick:
        print("⚡ Running in QUICK mode (subset of tests)")
    
    results = await runner.run_all_evaluations(quick_mode=args.quick)
    
    # Print results
    runner.print_results(detailed=args.detailed)
    
    # Save results if requested
    if args.output_file:
        runner.save_results(args.output_file)
    
    # Return appropriate exit code
    overall_status = results.get('summary', {}).get('overall_status', 'UNKNOWN')
    if overall_status in ['EXCELLENT', 'GOOD']:
        print("\n🎉 Evaluation suite PASSED!")
        return 0
    elif overall_status == 'FAIR':
        print("\n⚠️ Evaluation suite completed with WARNINGS")
        return 1
    else:
        print("\n❌ Evaluation suite FAILED")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)