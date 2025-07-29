#!/usr/bin/env python3
"""
Standalone evaluation test that works without the full Jean Memory system
Tests the evaluation framework with mock orchestrator responses
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "openmemory" / "api"))
sys.path.insert(0, str(current_dir / "utils"))

from utils.eval_framework import BaseEvaluator, TestScenario, EvalResult
from utils.metrics import MemoryTriageEvaluator

class MockTriageEvaluator(BaseEvaluator):
    """Mock evaluator that simulates memory triage without real system"""
    
    def __init__(self):
        super().__init__("mock_triage_evaluator")
        self.triage_evaluator = MemoryTriageEvaluator()
    
    async def run_evaluation(self, scenarios):
        """Run mock evaluation"""
        print(f"🧠 Running mock memory triage evaluation with {len(scenarios)} scenarios...")
        
        results = []
        for scenario in scenarios:
            result = await self.run_single_scenario(scenario)
            results.append(result)
        
        return results
    
    async def _execute_scenario(self, scenario):
        """Mock execution that simulates AI triage decision"""
        user_message = scenario.input_data['user_message']
        expected_decision = scenario.expected_output['expected_decision']
        
        print(f"  Processing: \"{user_message}\" -> Expected: {expected_decision}")
        
        # Simulate AI decision using heuristic rules (mock the real AI)
        mock_decision = self._mock_ai_decision(user_message)
        
        # Evaluate the decision
        evaluation = self.triage_evaluator.evaluate_triage_decision(
            message=user_message,
            decision=mock_decision,
            expected_decision=expected_decision
        )
        
        print(f"  Result: Got {mock_decision}, Accuracy: {evaluation['accuracy']}")
        
        return {
            'user_message': user_message,
            'mock_decision': mock_decision,
            'expected_decision': expected_decision,
            'accuracy': evaluation['accuracy'],
            'confidence': evaluation['confidence'],
            'success': True
        }
    
    def _mock_ai_decision(self, message):
        """Mock AI decision using simple heuristics"""
        message_lower = message.lower()
        
        # Strong remember indicators
        remember_indicators = [
            'i am', 'i\'m', 'my name is', 'i work', 'i live', 'i like', 'i prefer',
            'i studied', 'i graduated', 'my goal', 'remember that', 'important'
        ]
        
        # Strong skip indicators  
        skip_indicators = [
            'what is', 'how do', 'can you', 'help me', 'explain', 'tell me',
            'thanks', 'thank you', 'got it', 'okay', 'yes', 'no'
        ]
        
        remember_score = sum(1 for indicator in remember_indicators if indicator in message_lower)
        skip_score = sum(1 for indicator in skip_indicators if indicator in message_lower)
        
        if remember_score > skip_score:
            return "REMEMBER"
        elif skip_score > remember_score:
            return "SKIP"
        else:
            # Tie-breaker: personal pronouns and length
            if ('i ' in message_lower or 'my ' in message_lower) and len(message) > 20:
                return "REMEMBER"
            else:
                return "SKIP"
    
    def calculate_score(self, actual, expected):
        """Calculate score based on accuracy"""
        return actual.get('accuracy', 0) * 100

async def test_memory_triage_standalone():
    """Test memory triage evaluation in standalone mode"""
    print("🧪 Testing Memory Triage Evaluation (Standalone Mode)")
    print("=" * 60)
    
    # Create test scenarios
    scenarios = [
        TestScenario(
            id="prof_info",
            description="Professional information",
            input_data={'user_message': "I'm a software engineer at Google"},
            expected_output={'expected_decision': 'REMEMBER'},
            success_criteria={'min_score': 80},
            tags=['professional']
        ),
        TestScenario(
            id="personal_info",
            description="Personal information", 
            input_data={'user_message': "My name is John and I live in SF"},
            expected_output={'expected_decision': 'REMEMBER'},
            success_criteria={'min_score': 80},
            tags=['personal']
        ),
        TestScenario(
            id="simple_question",
            description="Simple question",
            input_data={'user_message': "What time is it?"},
            expected_output={'expected_decision': 'SKIP'},
            success_criteria={'min_score': 80},
            tags=['question']
        ),
        TestScenario(
            id="help_request",
            description="Help request",
            input_data={'user_message': "Can you help me with Python?"},
            expected_output={'expected_decision': 'SKIP'},
            success_criteria={'min_score': 80},
            tags=['help_request']
        ),
        TestScenario(
            id="preference",
            description="Preference statement", 
            input_data={'user_message': "I prefer Python over JavaScript"},
            expected_output={'expected_decision': 'REMEMBER'},
            success_criteria={'min_score': 80},
            tags=['preference']
        )
    ]
    
    # Run evaluation
    evaluator = MockTriageEvaluator()
    results = await evaluator.run_evaluation(scenarios)
    
    # Calculate metrics
    correct_decisions = sum(1 for r in results if r.details.get('accuracy', 0) == 1.0)
    total_decisions = len(results)
    accuracy = correct_decisions / total_decisions * 100 if total_decisions > 0 else 0
    
    # Print results
    print(f"\n📊 RESULTS:")
    print("-" * 40)
    for result in results:
        details = result.details
        status = "✅" if details.get('accuracy', 0) == 1.0 else "❌"
        print(f"{status} {result.test_name}")
        print(f"   Message: \"{details.get('user_message', '')}\"")
        print(f"   Expected: {details.get('expected_decision', '')} | Got: {details.get('mock_decision', '')}")
        print(f"   Confidence: {details.get('confidence', 0):.2f}")
    
    print(f"\n📈 SUMMARY:")
    print(f"   Accuracy: {accuracy:.1f}% ({correct_decisions}/{total_decisions})")
    print(f"   Status: {'✅ PASS' if accuracy >= 80 else '❌ FAIL'}")
    
    return accuracy >= 80

async def test_context_quality_mock():
    """Test context quality evaluation with mock data"""
    print("\n🧪 Testing Context Quality Evaluation (Mock Mode)")
    print("=" * 60)
    
    from utils.metrics import ContextQualityEvaluator
    
    evaluator = ContextQualityEvaluator()
    
    # Test scenarios with mock context
    test_cases = [
        {
            'context': "User is a software engineer at Google working on AI projects. Prefers Python and clean architecture.",
            'query': "Help me with my Python project",
            'expected_elements': ['software engineer', 'Python', 'AI projects'],
            'description': "Well-matched context"
        },
        {
            'context': "User enjoys hiking and cooking Italian food.",
            'query': "Help me debug this JavaScript code", 
            'expected_elements': ['JavaScript', 'debugging', 'programming'],
            'description': "Poorly-matched context"
        },
        {
            'context': "---\n[Jean Memory Context]\nUser is a product manager with 5 years experience. Currently working on mobile app features.\n---",
            'query': "What are my current work priorities?",
            'expected_elements': ['product manager', 'mobile app', 'work'],
            'description': "Well-formatted relevant context"
        }
    ]
    
    print("\n📊 CONTEXT QUALITY RESULTS:")
    print("-" * 40)
    
    total_score = 0
    for i, test_case in enumerate(test_cases, 1):
        quality_score = evaluator.evaluate_context_quality(
            context=test_case['context'],
            user_query=test_case['query'],
            expected_elements=test_case['expected_elements']
        )
        
        total_score += quality_score.overall_score
        
        print(f"{i}. {test_case['description']}")
        print(f"   Overall Score: {quality_score.overall_score:.1f}/100")
        print(f"   Relevance: {quality_score.relevance_score:.1f}")
        print(f"   Completeness: {quality_score.completeness_score:.1f}")
        print(f"   Personalization: {quality_score.personalization_score:.1f}")
        print(f"   Noise Penalty: {quality_score.noise_penalty:.1f}")
    
    avg_score = total_score / len(test_cases)
    print(f"\n📈 AVERAGE QUALITY SCORE: {avg_score:.1f}/100")
    print(f"   Status: {'✅ PASS' if avg_score >= 75 else '❌ FAIL'}")
    
    return avg_score >= 75

async def main():
    """Run standalone evaluation tests"""
    print("🚀 JEAN MEMORY EVALUATION FRAMEWORK - STANDALONE TEST")
    print("Testing evaluation components without requiring full system setup")
    print("=" * 80)
    
    try:
        # Test memory triage
        triage_passed = await test_memory_triage_standalone()
        
        # Test context quality
        context_passed = await test_context_quality_mock()
        
        # Overall results
        print(f"\n🎯 OVERALL RESULTS:")
        print("=" * 40)
        print(f"Memory Triage: {'✅ PASS' if triage_passed else '❌ FAIL'}")
        print(f"Context Quality: {'✅ PASS' if context_passed else '❌ FAIL'}")
        
        overall_passed = triage_passed and context_passed
        print(f"\nOverall Status: {'🎉 ALL TESTS PASSED' if overall_passed else '⚠️ SOME TESTS FAILED'}")
        
        if overall_passed:
            print("\n✅ Evaluation framework is working correctly!")
            print("   Ready to test with real Jean Memory system")
        else:
            print("\n❌ Framework needs fixes before proceeding")
        
        return 0 if overall_passed else 1
        
    except Exception as e:
        print(f"\n❌ Standalone test failed: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)