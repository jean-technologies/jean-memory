#!/usr/bin/env python3
"""
Memory Triage Accuracy Evaluation
Tests the accuracy of Jean Memory's remember vs skip decisions
"""

import asyncio
import json
import logging
import argparse
from typing import Dict, List, Any, Tuple
from pathlib import Path
import sys
import os

# Add project paths
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / "openmemory" / "api"))
sys.path.insert(0, str(current_dir.parent / "utils"))

from eval_framework import BaseEvaluator, TestScenario, EvalResult
from metrics import MemoryTriageEvaluator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryTriageAccuracyEvaluator(BaseEvaluator):
    """Evaluates memory triage accuracy using golden dataset"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("memory_triage_accuracy", config)
        self.triage_evaluator = MemoryTriageEvaluator()
        self.accuracy_threshold = config.get('accuracy_threshold', 95.0) if config else 95.0
        
        # Track detailed metrics
        self.true_positives = 0
        self.true_negatives = 0  
        self.false_positives = 0
        self.false_negatives = 0
        self.misclassified_messages = []
        
    async def run_evaluation(self, scenarios: List[TestScenario]) -> List[EvalResult]:
        """Run memory triage accuracy evaluation on all scenarios"""
        logger.info(f"Starting memory triage accuracy evaluation with {len(scenarios)} scenarios")
        
        # Reset metrics
        self.true_positives = 0
        self.true_negatives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.misclassified_messages = []
        
        results = []
        for scenario in scenarios:
            result = await self.run_single_scenario(scenario)
            results.append(result)
            
            # Update metrics based on result
            self._update_confusion_matrix(result)
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        
        # Log summary
        logger.info(f"Memory triage evaluation complete:")
        logger.info(f"  Accuracy: {metrics['accuracy']:.1f}%")
        logger.info(f"  Precision: {metrics['precision']:.1f}%") 
        logger.info(f"  Recall: {metrics['recall']:.1f}%")
        logger.info(f"  F1 Score: {metrics['f1_score']:.1f}%")
        
        return results
    
    async def _execute_scenario(self, scenario: TestScenario) -> Dict[str, Any]:
        """Execute memory triage evaluation for a single scenario"""
        try:
            # Extract input data
            user_message = scenario.input_data['user_message']
            expected_decision = scenario.expected_output['expected_decision']
            user_id = scenario.input_data.get('user_id', 'eval-test-user')
            client_name = scenario.input_data.get('client_name', 'eval-test-client')
            
            # Get actual triage decision from the orchestrator
            triage_result = await self._get_triage_decision(user_message, user_id, client_name)
            
            if not triage_result['success']:
                return {
                    'error': triage_result.get('error', 'Unknown error'),
                    'actual_decision': 'ERROR',
                    'expected_decision': expected_decision,
                    'accuracy': 0.0
                }
            
            actual_decision = triage_result['decision']
            
            # Evaluate triage decision
            evaluation = self.triage_evaluator.evaluate_triage_decision(
                message=user_message,
                decision=actual_decision,
                expected_decision=expected_decision
            )
            
            return {
                'user_message': user_message,
                'actual_decision': actual_decision,
                'expected_decision': expected_decision,
                'accuracy': evaluation['accuracy'],
                'confidence': evaluation['confidence'],
                'message_analysis': evaluation['message_analysis'],
                'response_time': triage_result.get('response_time', 0),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error executing triage scenario {scenario.id}: {e}")
            return {
                'error': str(e),
                'actual_decision': 'ERROR',
                'expected_decision': scenario.expected_output.get('expected_decision', 'UNKNOWN'),
                'accuracy': 0.0
            }
    
    def calculate_score(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Calculate score based on triage accuracy"""
        if 'error' in actual:
            return 0.0
        
        accuracy = actual.get('accuracy', 0.0)
        confidence = actual.get('confidence', 0.5)
        
        # Base score from accuracy (0 or 100)
        base_score = accuracy * 100
        
        # Apply confidence weighting for correct decisions
        if accuracy == 1.0:
            # Boost score for high-confidence correct decisions
            score = base_score + (confidence - 0.5) * 10
        else:
            # Penalty for wrong decisions, especially high-confidence wrong ones
            score = base_score - (confidence * 20)
        
        return max(0, min(100, score))
    
    async def _get_triage_decision(self, user_message: str, user_id: str, client_name: str) -> Dict[str, Any]:
        """Get triage decision from the actual orchestrator"""
        try:
            # Import here to avoid circular dependencies
            from app.mcp_orchestration import get_smart_orchestrator
            from app.context import user_id_var, client_name_var
            import time
            
            # Set context variables
            user_token = user_id_var.set(user_id)
            client_token = client_name_var.set(client_name)
            
            try:
                orchestrator = get_smart_orchestrator()
                
                start_time = time.time()
                analysis = await orchestrator._ai_memory_analysis(user_message)
                end_time = time.time()
                
                decision = "REMEMBER" if analysis['should_remember'] else "SKIP"
                
                return {
                    'decision': decision,
                    'analysis': analysis,
                    'response_time': end_time - start_time,
                    'success': True
                }
                
            finally:
                # Reset context variables
                user_id_var.reset(user_token)
                client_name_var.reset(client_token)
                
        except Exception as e:
            logger.error(f"Error getting triage decision: {e}")
            return {
                'decision': 'ERROR',
                'response_time': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def _update_confusion_matrix(self, result: EvalResult):
        """Update confusion matrix based on evaluation result"""
        if 'error' in result.details:
            return
        
        actual = result.details['actual_decision']
        expected = result.details['expected_decision']
        
        if expected == 'REMEMBER':
            if actual == 'REMEMBER':
                self.true_positives += 1
            else:
                self.false_negatives += 1
                self.misclassified_messages.append({
                    'message': result.details['user_message'],
                    'expected': expected,
                    'actual': actual,
                    'type': 'false_negative'
                })
        else:  # expected == 'SKIP'
            if actual == 'SKIP':
                self.true_negatives += 1
            else:
                self.false_positives += 1
                self.misclassified_messages.append({
                    'message': result.details['user_message'],
                    'expected': expected,
                    'actual': actual,
                    'type': 'false_positive'
                })
    
    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate precision, recall, F1, and accuracy metrics"""
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        
        if total == 0:
            return {'accuracy': 0, 'precision': 0, 'recall': 0, 'f1_score': 0}
        
        accuracy = (self.true_positives + self.true_negatives) / total * 100
        
        # Precision: TP / (TP + FP)
        precision = (self.true_positives / (self.true_positives + self.false_positives) * 100 
                    if (self.true_positives + self.false_positives) > 0 else 0)
        
        # Recall: TP / (TP + FN) 
        recall = (self.true_positives / (self.true_positives + self.false_negatives) * 100
                 if (self.true_positives + self.false_negatives) > 0 else 0)
        
        # F1 Score: 2 * (precision * recall) / (precision + recall)
        f1_score = (2 * precision * recall / (precision + recall) 
                   if (precision + recall) > 0 else 0)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives
        }
    
    def get_confusion_matrix_summary(self) -> str:
        """Get a formatted confusion matrix summary"""
        return f"""
Confusion Matrix:
                 Predicted
                 R    S
Actual    R     {self.true_positives:3d}  {self.false_negatives:3d}
          S     {self.false_positives:3d}  {self.true_negatives:3d}

Legend: R=Remember, S=Skip
"""

def load_golden_memories(filepath: str = None) -> List[TestScenario]:
    """Load golden memory dataset"""
    if not filepath:
        filepath = Path(__file__).parent / "golden_memories.json"
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        scenarios = []
        for item in data.get('memories', []):
            scenario = TestScenario(
                id=item['message_id'],
                description=item.get('reasoning', f"Triage decision for: {item['user_message'][:50]}..."),
                input_data={
                    'user_message': item['user_message'],
                    'user_id': item.get('user_id', 'eval-test-user'),
                    'client_name': item.get('client_name', 'eval-test-client')
                },
                expected_output={
                    'expected_decision': item['expected_decision'],
                    'expected_content': item.get('expected_content', ''),
                    'expected_priority': item.get('expected_priority', 'MEDIUM')
                },
                success_criteria={
                    'min_score': 90.0 if item.get('difficulty') == 'easy' else 70.0
                },
                tags=item.get('tags', [])
            )
            scenarios.append(scenario)
        
        logger.info(f"Loaded {len(scenarios)} golden memory scenarios from {filepath}")
        return scenarios
        
    except Exception as e:
        logger.error(f"Failed to load golden memories from {filepath}: {e}")
        return create_default_scenarios()

def create_default_scenarios() -> List[TestScenario]:
    """Create default test scenarios if golden dataset not available"""
    
    scenarios = [
        # Clear REMEMBER cases
        TestScenario(
            id="clear_remember_profession",
            description="Clear professional information",
            input_data={
                'user_message': "I'm a software engineer at Google working on search algorithms",
            },
            expected_output={'expected_decision': 'REMEMBER'},
            success_criteria={'min_score': 90.0},
            tags=['clear', 'professional', 'remember']
        ),
        
        TestScenario(
            id="clear_remember_personal",
            description="Clear personal information",
            input_data={
                'user_message': "My name is John Smith and I live in San Francisco",
            },
            expected_output={'expected_decision': 'REMEMBER'},
            success_criteria={'min_score': 90.0},
            tags=['clear', 'personal', 'remember']
        ),
        
        TestScenario(
            id="clear_remember_preference",
            description="Clear preference statement",
            input_data={
                'user_message': "I strongly prefer Python over JavaScript for backend development",
            },
            expected_output={'expected_decision': 'REMEMBER'},
            success_criteria={'min_score': 85.0},
            tags=['clear', 'preference', 'remember']
        ),
        
        # Clear SKIP cases
        TestScenario(
            id="clear_skip_question",
            description="Simple factual question",
            input_data={
                'user_message': "What time is it?",
            },
            expected_output={'expected_decision': 'SKIP'},
            success_criteria={'min_score': 90.0},
            tags=['clear', 'question', 'skip']
        ),
        
        TestScenario(
            id="clear_skip_thanks",
            description="Simple acknowledgment",
            input_data={
                'user_message': "Thanks for the help!",
            },
            expected_output={'expected_decision': 'SKIP'},
            success_criteria={'min_score': 90.0},
            tags=['clear', 'acknowledgment', 'skip']
        ),
        
        TestScenario(
            id="clear_skip_general_query",
            description="General knowledge query",
            input_data={
                'user_message': "How do photons interact with matter?",
            },
            expected_output={'expected_decision': 'SKIP'},
            success_criteria={'min_score': 85.0},
            tags=['clear', 'general_knowledge', 'skip']
        ),
        
        # Ambiguous cases
        TestScenario(
            id="ambiguous_project_mention",
            description="Ambiguous project mention",
            input_data={
                'user_message': "I'm working on a React project",
            },
            expected_output={'expected_decision': 'REMEMBER'},  # Lean towards remembering
            success_criteria={'min_score': 70.0},
            tags=['ambiguous', 'project', 'remember']
        ),
        
        TestScenario(
            id="ambiguous_preference",
            description="Ambiguous preference",
            input_data={
                'user_message': "I like this approach better",
            },
            expected_output={'expected_decision': 'SKIP'},  # Too vague without context
            success_criteria={'min_score': 60.0},
            tags=['ambiguous', 'preference', 'skip']
        )
    ]
    
    return scenarios

async def main():
    """Main evaluation function"""
    parser = argparse.ArgumentParser(description='Run memory triage accuracy evaluation')
    parser.add_argument('--dataset', help='Path to golden memories JSON file')
    parser.add_argument('--output-file', help='Path to save results JSON file')
    parser.add_argument('--accuracy-threshold', type=float, default=95.0, help='Accuracy threshold for pass/fail')
    parser.add_argument('--category', help='Filter scenarios by tag category')
    parser.add_argument('--detailed-errors', action='store_true', help='Show detailed error analysis')
    
    args = parser.parse_args()
    
    # Load scenarios
    scenarios = load_golden_memories(args.dataset)
    
    # Filter by category if specified
    if args.category:
        scenarios = [s for s in scenarios if args.category in s.tags]
        logger.info(f"Filtered to {len(scenarios)} scenarios with tag '{args.category}'")
    
    # Configure evaluator
    config = {
        'accuracy_threshold': args.accuracy_threshold
    }
    
    evaluator = MemoryTriageAccuracyEvaluator(config)
    
    # Run evaluation
    logger.info("Starting memory triage accuracy evaluation...")
    results = await evaluator.run_evaluation(scenarios)
    
    # Calculate detailed metrics
    metrics = evaluator._calculate_metrics()
    
    # Print summary
    summary = evaluator.get_summary_stats()
    print("\n" + "="*60)
    print("MEMORY TRIAGE ACCURACY EVALUATION RESULTS")
    print("="*60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Accuracy: {metrics['accuracy']:.1f}%")
    print(f"Precision: {metrics['precision']:.1f}%")
    print(f"Recall: {metrics['recall']:.1f}%")
    print(f"F1 Score: {metrics['f1_score']:.1f}%")
    print(f"Average Execution Time: {summary['average_execution_time']:.2f}s")
    
    # Print confusion matrix
    print(evaluator.get_confusion_matrix_summary())
    
    # Show misclassified messages if requested
    if args.detailed_errors and evaluator.misclassified_messages:
        print("\nMISCLASSIFIED MESSAGES:")
        print("-" * 40)
        for error in evaluator.misclassified_messages:
            print(f"{error['type'].upper()}: {error['message']}")
            print(f"  Expected: {error['expected']}, Got: {error['actual']}")
            print()
    
    # Save results if requested
    if args.output_file:
        # Add metrics to results
        results_with_metrics = {
            'metrics': metrics,
            'misclassified': evaluator.misclassified_messages
        }
        evaluator.config.update(results_with_metrics)
        evaluator.save_results(args.output_file)
        print(f"Results saved to {args.output_file}")
    
    # Return exit code based on accuracy threshold
    if metrics['accuracy'] >= args.accuracy_threshold:
        print(f"🎉 Memory triage accuracy evaluation PASSED! ({metrics['accuracy']:.1f}% >= {args.accuracy_threshold}%)")
        return 0
    else:
        print(f"⚠️ Memory triage accuracy evaluation FAILED! ({metrics['accuracy']:.1f}% < {args.accuracy_threshold}%)")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)