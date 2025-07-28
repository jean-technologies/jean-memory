"""
Base evaluation framework for Jean Memory
Provides common utilities and base classes for all evaluations
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import sys
import os

# Add the API directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../openmemory/api')))

logger = logging.getLogger(__name__)

@dataclass
class EvalResult:
    """Standard result format for all evaluations"""
    test_name: str
    score: float  # 0-100
    passed: bool
    details: Dict[str, Any]
    execution_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'score': self.score,
            'passed': self.passed,
            'details': self.details,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }

@dataclass 
class TestScenario:
    """Standard test scenario format"""
    id: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    success_criteria: Dict[str, Any]
    tags: List[str] = None

class BaseEvaluator(ABC):
    """Base class for all Jean Memory evaluators"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.results: List[EvalResult] = []
        
    @abstractmethod
    async def run_evaluation(self, scenarios: List[TestScenario]) -> List[EvalResult]:
        """Run the evaluation on given scenarios"""
        pass
    
    @abstractmethod
    def calculate_score(self, actual: Any, expected: Any) -> float:
        """Calculate score for a single test case"""
        pass
        
    async def run_single_scenario(self, scenario: TestScenario) -> EvalResult:
        """Run evaluation on a single scenario with timing and error handling"""
        start_time = time.time()
        
        try:
            logger.info(f"Running scenario: {scenario.id} - {scenario.description}")
            
            # Run the actual evaluation logic
            actual_output = await self._execute_scenario(scenario)
            
            # Calculate score
            score = self.calculate_score(actual_output, scenario.expected_output)
            
            # Check success criteria
            passed = self._check_success_criteria(actual_output, scenario.success_criteria)
            
            # Collect detailed results
            details = {
                'scenario_id': scenario.id,
                'input': scenario.input_data,
                'expected': scenario.expected_output,
                'actual': actual_output,
                'success_criteria': scenario.success_criteria
            }
            
            execution_time = time.time() - start_time
            
            result = EvalResult(
                test_name=f"{self.name}_{scenario.id}",
                score=score,
                passed=passed,
                details=details,
                execution_time=execution_time,
                timestamp=datetime.now(),
                metadata={'evaluator': self.name, 'tags': scenario.tags}
            )
            
            self.results.append(result)
            
            logger.info(f"Scenario {scenario.id} completed: score={score:.1f}, passed={passed}, time={execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Scenario {scenario.id} failed: {e}")
            
            result = EvalResult(
                test_name=f"{self.name}_{scenario.id}",
                score=0.0,
                passed=False,
                details={'error': str(e), 'scenario_id': scenario.id},
                execution_time=execution_time,
                timestamp=datetime.now(),
                metadata={'evaluator': self.name, 'error': True}
            )
            
            self.results.append(result)
            return result
    
    @abstractmethod
    async def _execute_scenario(self, scenario: TestScenario) -> Any:
        """Execute the specific evaluation logic for a scenario"""
        pass
    
    def _check_success_criteria(self, actual: Any, criteria: Dict[str, Any]) -> bool:
        """Check if actual output meets success criteria"""
        try:
            for criterion, expected_value in criteria.items():
                if criterion == 'min_score':
                    if isinstance(actual, dict) and 'score' in actual:
                        if actual['score'] < expected_value:
                            return False
                elif criterion == 'contains_elements':
                    if isinstance(actual, str):
                        for element in expected_value:
                            if element.lower() not in actual.lower():
                                return False
                elif criterion == 'response_time':
                    if isinstance(actual, dict) and 'response_time' in actual:
                        if actual['response_time'] > expected_value:
                            return False
                elif criterion == 'not_contains':
                    if isinstance(actual, str):
                        for element in expected_value:
                            if element.lower() in actual.lower():
                                return False
            
            return True
        except Exception as e:
            logger.warning(f"Error checking success criteria: {e}")
            return False
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all results"""
        if not self.results:
            return {'total': 0}
        
        scores = [r.score for r in self.results]
        execution_times = [r.execution_time for r in self.results]
        passed_count = sum(1 for r in self.results if r.passed)
        
        return {
            'total_tests': len(self.results),
            'passed': passed_count,
            'failed': len(self.results) - passed_count,
            'pass_rate': passed_count / len(self.results) * 100,
            'average_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'average_execution_time': sum(execution_times) / len(execution_times),
            'total_execution_time': sum(execution_times)
        }
    
    def save_results(self, filepath: str):
        """Save results to JSON file"""
        results_data = {
            'evaluator': self.name,
            'config': self.config,
            'summary': self.get_summary_stats(),
            'results': [r.to_dict() for r in self.results],
            'generated_at': datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Results saved to {filepath}")

class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        
    @property
    def elapsed_time(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0

def load_test_scenarios(filepath: str) -> List[TestScenario]:
    """Load test scenarios from JSON file"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        scenarios = []
        for item in data.get('scenarios', []):
            scenario = TestScenario(
                id=item['id'],
                description=item['description'],
                input_data=item['input_data'],
                expected_output=item['expected_output'],
                success_criteria=item['success_criteria'],
                tags=item.get('tags', [])
            )
            scenarios.append(scenario)
        
        logger.info(f"Loaded {len(scenarios)} test scenarios from {filepath}")
        return scenarios
        
    except Exception as e:
        logger.error(f"Failed to load test scenarios from {filepath}: {e}")
        return []

def create_test_user_context() -> Dict[str, Any]:
    """Create a test user context for evaluations"""
    return {
        'user_id': 'eval-test-user-001',
        'client_name': 'eval-test-client',
        'memories': [
            "User is a software engineer working at a tech startup",
            "Prefers Python and TypeScript for development",
            "Currently working on an AI chatbot project",
            "Enjoys clean architecture and test-driven development",
            "Lives in San Francisco, originally from New York",
            "Graduated from Stanford with a CS degree",
            "Interested in machine learning and natural language processing"
        ],
        'preferences': {
            'communication_style': 'direct and technical',
            'detail_level': 'comprehensive',
            'response_format': 'structured with examples'
        }
    }

async def simulate_orchestrator_call(user_message: str, user_id: str, client_name: str, 
                                   is_new_conversation: bool = False) -> Dict[str, Any]:
    """Simulate a call to the orchestrator for testing purposes"""
    try:
        # Import here to avoid circular dependencies
        from app.mcp_orchestration import get_smart_orchestrator
        
        orchestrator = get_smart_orchestrator()
        
        start_time = time.time()
        context = await orchestrator.orchestrate_smart_context(
            user_message=user_message,
            user_id=user_id,
            client_name=client_name,
            is_new_conversation=is_new_conversation
        )
        end_time = time.time()
        
        return {
            'context': context,
            'response_time': end_time - start_time,
            'success': True
        }
        
    except Exception as e:
        return {
            'context': '',
            'response_time': 0.0,
            'success': False,
            'error': str(e)
        }