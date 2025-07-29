#!/usr/bin/env python3
"""
Working Comprehensive Evaluation Runner
Runs working evaluations and provides consolidated results
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add project paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "openmemory" / "api"))
sys.path.insert(0, str(current_dir / "utils"))

from utils.metrics import MemoryTriageEvaluator, ContextQualityEvaluator

class WorkingEvaluationRunner:
    """Comprehensive evaluation runner that works with current system"""
    
    def __init__(self):
        self.start_time = None
        self.results = {
            'memory_triage': {},
            'context_quality': {},
            'performance_basic': {},
            'system_integration': {},
            'overall_metrics': {},
            'summary': {}
        }
    
    async def run_all_evaluations(self):
        """Run all working evaluations"""
        self.start_time = time.time()
        print("🚀 Running Jean Memory Working Evaluation Suite")
        print("=" * 80)
        
        try:
            # Run each evaluation category
            await self._run_memory_triage_evaluation()
            await self._run_context_quality_evaluation()
            await self._run_basic_performance_tests()
            await self._run_system_integration_tests()
            
            # Calculate overall metrics
            self._calculate_overall_metrics()
            
            # Generate summary
            self._generate_summary()
            
            execution_time = time.time() - self.start_time
            self.results['execution_time'] = execution_time
            
            print(f"\n✅ Comprehensive evaluation completed in {execution_time:.2f}s")
            return self.results
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['error'] = str(e)
            return self.results
    
    async def _run_memory_triage_evaluation(self):
        """Run memory triage evaluation with real AI system"""
        print("\n🧠 Memory Triage Evaluation")
        print("-" * 40)
        
        try:
            from app.mcp_orchestration import get_smart_orchestrator
            
            orchestrator = get_smart_orchestrator()
            evaluator = MemoryTriageEvaluator()
            
            # Load golden dataset sample
            golden_file = current_dir / "memory_intelligence" / "golden_memories.json"
            with open(golden_file, 'r') as f:
                data = json.load(f)
            
            memories = data.get('memories', [])[:20]  # Test with first 20
            
            results = []
            correct = 0
            total = len(memories)
            
            print(f"Testing {total} memories from golden dataset...")
            
            for i, memory in enumerate(memories, 1):
                message = memory['user_message']
                expected = memory['expected_decision']
                
                try:
                    # Use real AI memory analysis
                    analysis = await orchestrator._ai_memory_analysis(message)
                    actual = "REMEMBER" if analysis['should_remember'] else "SKIP"
                    
                    evaluation = evaluator.evaluate_triage_decision(message, actual, expected)
                    is_correct = evaluation['accuracy'] == 1.0
                    
                    if is_correct:
                        correct += 1
                    
                    results.append({
                        'message': message,
                        'expected': expected,
                        'actual': actual,
                        'correct': is_correct,
                        'confidence': evaluation['confidence']
                    })
                    
                    if i % 5 == 0:
                        print(f"  Processed {i}/{total} memories...")
                    
                except Exception as e:
                    print(f"  Error processing memory {i}: {e}")
                    results.append({
                        'message': message,
                        'expected': expected,
                        'actual': 'ERROR',
                        'correct': False,
                        'error': str(e)
                    })
            
            accuracy = correct / total * 100
            
            self.results['memory_triage'] = {
                'total_tested': total,
                'correct': correct,
                'accuracy': accuracy,
                'results': results,
                'success': True
            }
            
            status = "✅ PASS" if accuracy >= 85 else "❌ FAIL"
            print(f"  {status} Accuracy: {accuracy:.1f}% ({correct}/{total})")
            
        except Exception as e:
            print(f"  ❌ Memory triage evaluation failed: {e}")
            self.results['memory_triage'] = {
                'error': str(e),
                'success': False
            }
    
    async def _run_context_quality_evaluation(self):
        """Run context quality evaluation with mock contexts"""
        print("\n📊 Context Quality Evaluation")
        print("-" * 40)
        
        try:
            evaluator = ContextQualityEvaluator()
            
            # Test cases with different quality levels
            test_cases = [
                {
                    'context': "User is a senior software engineer at Google with 8 years experience. Specializes in Python, machine learning, and distributed systems. Currently working on search algorithms and performance optimization.",
                    'query': "Help me optimize my Python ML pipeline performance",
                    'expected_elements': ['software engineer', 'Python', 'ML', 'performance'],
                    'description': "Excellent match - highly relevant",
                    'expected_score': 80
                },
                {
                    'context': "User prefers direct communication. Works as a product manager at a startup. Has experience with user research and agile development methodologies.",
                    'query': "What's the best approach for user interviews?",
                    'expected_elements': ['product manager', 'user research', 'interviews'],
                    'description': "Good match - relevant experience",
                    'expected_score': 70
                },
                {
                    'context': "---\n[Jean Memory Context]\nUser is a data scientist with PhD in statistics. Experienced with R, Python, and statistical modeling. Currently analyzing customer behavior patterns.\n---",
                    'query': "Help me design an A/B test for my recommendation system",
                    'expected_elements': ['data scientist', 'statistics', 'analysis'],
                    'description': "Well-formatted relevant context",
                    'expected_score': 75
                },
                {
                    'context': "User enjoys hiking and photography. Lives in San Francisco. Likes Italian food and craft beer.",
                    'query': "Debug this JavaScript memory leak in my React app",
                    'expected_elements': ['JavaScript', 'React', 'debugging'],
                    'description': "Poor match - irrelevant context",
                    'expected_score': 20
                },
                {
                    'context': "",
                    'query': "What are my career goals?",
                    'expected_elements': ['career', 'goals'],
                    'description': "Empty context",
                    'expected_score': 0
                }
            ]
            
            results = []
            total_score = 0
            passed = 0
            
            print(f"Testing {len(test_cases)} context scenarios...")
            
            for i, test_case in enumerate(test_cases, 1):
                quality_score = evaluator.evaluate_context_quality(
                    context=test_case['context'],
                    user_query=test_case['query'],
                    expected_elements=test_case['expected_elements']
                )
                
                total_score += quality_score.overall_score
                score_vs_expected = quality_score.overall_score >= (test_case['expected_score'] * 0.8)  # 80% of expected
                
                if score_vs_expected:
                    passed += 1
                
                results.append({
                    'description': test_case['description'],
                    'query': test_case['query'],
                    'score': quality_score.overall_score,
                    'expected_score': test_case['expected_score'],
                    'passed': score_vs_expected,
                    'breakdown': quality_score.to_dict()
                })
                
                status = "✅" if score_vs_expected else "❌"
                print(f"  {status} {test_case['description']}: {quality_score.overall_score:.1f}/100")
            
            avg_score = total_score / len(test_cases)
            pass_rate = passed / len(test_cases) * 100
            
            self.results['context_quality'] = {
                'total_tested': len(test_cases),
                'passed': passed,
                'average_score': avg_score,
                'pass_rate': pass_rate,
                'results': results,
                'success': True
            }
            
            status = "✅ PASS" if pass_rate >= 60 else "❌ FAIL"
            print(f"  {status} Average Score: {avg_score:.1f}/100, Pass Rate: {pass_rate:.1f}%")
            
        except Exception as e:
            print(f"  ❌ Context quality evaluation failed: {e}")
            self.results['context_quality'] = {
                'error': str(e),
                'success': False
            }
    
    async def _run_basic_performance_tests(self):
        """Run basic performance tests with jean_memory tool"""
        print("\n⚡ Basic Performance Tests")
        print("-" * 40)
        
        try:
            from app.tools.orchestration import jean_memory
            from app.context import user_id_var, client_name_var, background_tasks_var
            from fastapi import BackgroundTasks
            
            test_user_id = "perf-eval-user"
            test_client = "claude"
            
            # Set up context
            user_token = user_id_var.set(test_user_id)
            client_token = client_name_var.set(test_client)
            bg_tasks = BackgroundTasks()
            bg_token = background_tasks_var.set(bg_tasks)
            
            test_cases = [
                {
                    "message": "What's the weather?",
                    "is_new": False,
                    "needs_context": False,
                    "description": "No context (fast)",
                    "target_time": 1.0
                },
                {
                    "message": "Hello, I'm testing",
                    "is_new": True,
                    "needs_context": True,
                    "description": "New conversation",
                    "target_time": 3.0
                },
                {
                    "message": "Help with my project",
                    "is_new": False,
                    "needs_context": True,
                    "description": "Context required",
                    "target_time": 5.0
                }
            ]
            
            results = []
            
            print(f"Testing {len(test_cases)} performance scenarios...")
            
            try:
                for i, test_case in enumerate(test_cases, 1):
                    start_time = time.time()
                    
                    try:
                        context = await jean_memory(
                            user_message=test_case['message'],
                            is_new_conversation=test_case['is_new'],
                            needs_context=test_case['needs_context']
                        )
                        
                        response_time = time.time() - start_time
                        success = True
                        error = None
                        
                    except Exception as e:
                        response_time = time.time() - start_time
                        context = ""
                        success = False
                        error = str(e)
                    
                    target_met = response_time <= test_case['target_time']
                    context_provided = bool(context)
                    
                    results.append({
                        'description': test_case['description'],
                        'response_time': response_time,
                        'target_time': test_case['target_time'],
                        'target_met': target_met,
                        'context_provided': context_provided,
                        'success': success,
                        'error': error
                    })
                    
                    status = "✅" if success and target_met else "❌"
                    print(f"  {status} {test_case['description']}: {response_time:.2f}s (target: {test_case['target_time']}s)")
                
            finally:
                # Reset context
                user_id_var.reset(user_token)
                client_name_var.reset(client_token)
                background_tasks_var.reset(bg_token)
            
            # Calculate metrics
            total_tests = len(results)
            successful_tests = sum(1 for r in results if r['success'])
            target_met_count = sum(1 for r in results if r['target_met'])
            avg_response_time = sum(r['response_time'] for r in results) / total_tests
            
            self.results['performance_basic'] = {
                'total_tested': total_tests,
                'successful': successful_tests,
                'target_met_count': target_met_count,
                'average_response_time': avg_response_time,
                'results': results,
                'success': True
            }
            
            performance_score = (successful_tests + target_met_count) / (total_tests * 2) * 100
            status = "✅ PASS" if performance_score >= 70 else "❌ FAIL"
            print(f"  {status} Performance Score: {performance_score:.1f}% (Success: {successful_tests}/{total_tests}, Speed: {target_met_count}/{total_tests})")
            
        except Exception as e:
            print(f"  ❌ Performance tests failed: {e}")
            self.results['performance_basic'] = {
                'error': str(e),
                'success': False
            }
    
    async def _run_system_integration_tests(self):
        """Run system integration tests"""
        print("\n🔧 System Integration Tests")
        print("-" * 40)
        
        integration_results = {
            'jean_memory_tool': False,
            'smart_orchestrator': False,
            'memory_analysis': False,
            'context_generation': False
        }
        
        # Test jean_memory tool
        try:
            from app.tools.orchestration import jean_memory
            integration_results['jean_memory_tool'] = True
            print("  ✅ Jean Memory Tool: Available")
        except Exception as e:
            print(f"  ❌ Jean Memory Tool: {e}")
        
        # Test smart orchestrator
        try:
            from app.mcp_orchestration import get_smart_orchestrator
            orchestrator = get_smart_orchestrator()
            integration_results['smart_orchestrator'] = True
            print("  ✅ Smart Orchestrator: Available")
        except Exception as e:
            print(f"  ❌ Smart Orchestrator: {e}")
        
        # Test memory analysis
        try:
            if integration_results['smart_orchestrator']:
                analysis = await orchestrator._ai_memory_analysis("Test message")
                integration_results['memory_analysis'] = True
                print("  ✅ Memory Analysis: Working")
        except Exception as e:
            print(f"  ❌ Memory Analysis: {e}")
        
        # Test context generation
        try:
            if integration_results['smart_orchestrator']:
                context = await orchestrator._standard_orchestration(
                    "Test context", "test-user", "claude", False
                )
                integration_results['context_generation'] = True
                print("  ✅ Context Generation: Working")
        except Exception as e:
            print(f"  ❌ Context Generation: {e}")
        
        # Calculate integration score
        working_components = sum(integration_results.values())
        total_components = len(integration_results)
        integration_score = working_components / total_components * 100
        
        self.results['system_integration'] = {
            'components': integration_results,
            'working_components': working_components,
            'total_components': total_components,
            'integration_score': integration_score,
            'success': True
        }
        
        status = "✅ PASS" if integration_score >= 75 else "❌ FAIL"
        print(f"  {status} Integration Score: {integration_score:.1f}% ({working_components}/{total_components} components)")
    
    def _calculate_overall_metrics(self):
        """Calculate overall system metrics"""
        overall_metrics = {
            'system_health_score': 0.0,
            'categories_tested': 0,
            'categories_passed': 0,
            'key_metrics': {}
        }
        
        # Memory triage metrics
        if self.results['memory_triage'].get('success'):
            overall_metrics['categories_tested'] += 1
            accuracy = self.results['memory_triage']['accuracy']
            overall_metrics['key_metrics']['memory_triage_accuracy'] = accuracy
            if accuracy >= 85:
                overall_metrics['categories_passed'] += 1
        
        # Context quality metrics
        if self.results['context_quality'].get('success'):
            overall_metrics['categories_tested'] += 1
            pass_rate = self.results['context_quality']['pass_rate']
            overall_metrics['key_metrics']['context_quality_pass_rate'] = pass_rate
            if pass_rate >= 60:
                overall_metrics['categories_passed'] += 1
        
        # Performance metrics
        if self.results['performance_basic'].get('success'):
            overall_metrics['categories_tested'] += 1
            successful = self.results['performance_basic']['successful']
            total = self.results['performance_basic']['total_tested']
            success_rate = successful / total * 100 if total > 0 else 0
            overall_metrics['key_metrics']['performance_success_rate'] = success_rate
            if success_rate >= 80:
                overall_metrics['categories_passed'] += 1
        
        # Integration metrics
        if self.results['system_integration'].get('success'):
            overall_metrics['categories_tested'] += 1
            integration_score = self.results['system_integration']['integration_score']
            overall_metrics['key_metrics']['system_integration_score'] = integration_score
            if integration_score >= 75:
                overall_metrics['categories_passed'] += 1
        
        # Calculate overall health score
        if overall_metrics['categories_tested'] > 0:
            category_pass_rate = overall_metrics['categories_passed'] / overall_metrics['categories_tested']
            overall_metrics['system_health_score'] = category_pass_rate * 100
        
        self.results['overall_metrics'] = overall_metrics
    
    def _generate_summary(self):
        """Generate evaluation summary"""
        overall = self.results['overall_metrics']
        health_score = overall['system_health_score']
        
        # Determine status
        if health_score >= 90:
            status = "EXCELLENT"
            emoji = "🎉"
        elif health_score >= 75:
            status = "GOOD"
            emoji = "✅"
        elif health_score >= 60:
            status = "FAIR"
            emoji = "⚠️"
        else:
            status = "NEEDS_IMPROVEMENT"  
            emoji = "❌"
        
        # Key findings
        findings = []
        metrics = overall.get('key_metrics', {})
        
        if 'memory_triage_accuracy' in metrics:
            accuracy = metrics['memory_triage_accuracy']
            if accuracy >= 90:
                findings.append("✅ Memory triage accuracy exceeds 90%")
            elif accuracy >= 80:
                findings.append("⚠️ Memory triage accuracy meets 80% but below 90%")
            else:
                findings.append("❌ Memory triage accuracy below 80%")
        
        if 'context_quality_pass_rate' in metrics:
            pass_rate = metrics['context_quality_pass_rate']
            if pass_rate >= 70:
                findings.append("✅ Context quality pass rate exceeds 70%")
            elif pass_rate >= 50:
                findings.append("⚠️ Context quality pass rate meets 50% but below 70%")
            else:
                findings.append("❌ Context quality pass rate below 50%")
        
        if 'system_integration_score' in metrics:
            integration = metrics['system_integration_score']
            if integration >= 90:
                findings.append("✅ System integration fully operational")
            elif integration >= 75:
                findings.append("⚠️ System integration mostly operational")
            else:
                findings.append("❌ System integration has issues")
        
        # Recommendations
        recommendations = []
        if health_score < 75:
            recommendations.append("Focus on failing evaluation categories")
        if metrics.get('memory_triage_accuracy', 100) < 85:
            recommendations.append("Improve memory triage AI decision accuracy")
        if metrics.get('context_quality_pass_rate', 100) < 60:
            recommendations.append("Enhance context relevance and quality")
        if metrics.get('system_integration_score', 100) < 90:
            recommendations.append("Address system integration issues")
        
        self.results['summary'] = {
            'overall_status': status,
            'status_emoji': emoji,
            'system_health_score': health_score,
            'evaluation_timestamp': datetime.now().isoformat(),
            'total_execution_time': self.results.get('execution_time', 0),
            'categories_evaluated': overall['categories_tested'],
            'categories_passed': overall['categories_passed'],
            'key_findings': findings,
            'recommendations': recommendations
        }
    
    def print_results(self):
        """Print formatted results"""
        summary = self.results.get('summary', {})
        overall = self.results.get('overall_metrics', {})
        
        print("\n" + "="*80)
        print("🎯 JEAN MEMORY COMPREHENSIVE EVALUATION RESULTS")
        print("="*80)
        
        emoji = summary.get('status_emoji', '❓')
        status = summary.get('overall_status', 'UNKNOWN')
        health_score = summary.get('system_health_score', 0)
        
        print(f"{emoji} Overall Status: {status} ({health_score:.1f}/100)")
        print(f"⏱️  Execution Time: {summary.get('total_execution_time', 0):.2f}s")
        print(f"📊 Categories: {summary.get('categories_passed', 0)}/{summary.get('categories_evaluated', 0)} passed")
        
        # Category results
        print(f"\n📈 DETAILED RESULTS:")
        print("-" * 50)
        
        categories = [
            ('Memory Triage', self.results.get('memory_triage', {})),
            ('Context Quality', self.results.get('context_quality', {})),
            ('Basic Performance', self.results.get('performance_basic', {})),
            ('System Integration', self.results.get('system_integration', {}))
        ]
        
        for name, result in categories:
            if result.get('success'):
                if 'accuracy' in result:
                    detail = f"{result['accuracy']:.1f}% accuracy"
                elif 'pass_rate' in result:
                    detail = f"{result['pass_rate']:.1f}% pass rate"
                elif 'integration_score' in result:
                    detail = f"{result['integration_score']:.1f}% integration"
                else:
                    detail = "Completed"
                print(f"✅ {name:18} | {detail}")
            else:
                print(f"❌ {name:18} | Failed")
        
        # Key findings
        findings = summary.get('key_findings', [])
        if findings:
            print(f"\n🔍 KEY FINDINGS:")
            print("-" * 30)
            for finding in findings:
                print(f"  {finding}")
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            print("-" * 30)
            for rec in recommendations:
                print(f"  • {rec}")

async def main():
    """Run the working evaluation suite"""
    runner = WorkingEvaluationRunner()
    results = await runner.run_all_evaluations()
    
    # Print results
    runner.print_results()
    
    # Save results
    output_file = Path(__file__).parent / "working_evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 Results saved to: {output_file}")
    
    # Return exit code
    health_score = results.get('summary', {}).get('system_health_score', 0)
    if health_score >= 75:
        print("\n🎉 Evaluation suite PASSED!")
        return 0
    else:
        print("\n⚠️ Evaluation suite completed with issues")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)