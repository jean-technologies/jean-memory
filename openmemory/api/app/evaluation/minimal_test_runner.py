"""
Minimal Test Runner for Conversation Datasets

Loads conversation datasets from Task 4, executes them via the MCP client,
and collects evaluation metrics using Tasks 1-2 infrastructure.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple

# Task 1: Core evaluation infrastructure
from .core import evaluate
from .metrics import MetricsCollector, EvaluationMetric

# Task 2: LLM judge integration
from .llm_judge import evaluate_single_response, ReasoningType, JudgeScore

# Task 4: Conversation dataset structures
from .conversation_dataset_generator import ConversationDataset, ConversationTurn

# Task 5: Authentication
from .config import is_authenticated

# Task 6: MCP client
from .minimal_mcp_client import call_jean_memory, MCPResponse, MCPError

# Local: Conversation state management
from .conversation_state import ConversationState, get_conversation_state_manager


logger = logging.getLogger(__name__)


class ConversationTestResult:
    """Results from executing a single conversation test"""
    
    def __init__(
        self,
        dataset_id: str,
        dataset_name: str,
        conversation_length: int,
        user_id: str
    ):
        self.dataset_id = dataset_id
        self.dataset_name = dataset_name
        self.conversation_length = conversation_length
        self.user_id = user_id
        
        # Execution tracking
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        
        # Turn results
        self.turn_results: List[Dict[str, Any]] = []
        self.judge_scores: List[JudgeScore] = []
        
        # Summary metrics
        self.success_count = 0
        self.total_turns = 0
        self.total_response_time_ms = 0
        self.avg_judge_score = 0.0
        
        # Errors
        self.errors: List[str] = []
    
    def add_turn_result(
        self,
        turn: ConversationTurn,
        mcp_response: Optional[MCPResponse],
        judge_score: Optional[JudgeScore],
        response_time_ms: float,
        error: Optional[str] = None
    ) -> None:
        """Add results from executing a conversation turn"""
        
        success = error is None and mcp_response is not None and mcp_response.is_success
        actual_response = ""
        
        if mcp_response and mcp_response.summary_text:
            actual_response = mcp_response.summary_text
        elif error:
            actual_response = f"Error: {error}"
        
        turn_result = {
            "turn_number": turn.turn_number,
            "user_message": turn.user_message,
            "expected_response": turn.expected_response,
            "actual_response": actual_response,
            "reasoning_type": turn.reasoning_type.value,
            "difficulty": turn.difficulty.value,
            "response_time_ms": response_time_ms,
            "success": success,
            "error": error,
            "test_case_id": turn.test_case_id,
            "judge_score": judge_score.overall if judge_score else 0.0,
            "memories_count": len(mcp_response.memories) if mcp_response else 0
        }
        
        self.turn_results.append(turn_result)
        if judge_score:
            self.judge_scores.append(judge_score)
        
        # Update summary metrics
        self.total_turns += 1
        if success:
            self.success_count += 1
        self.total_response_time_ms += response_time_ms
        
        if error:
            self.errors.append(f"Turn {turn.turn_number}: {error}")
    
    def finalize(self) -> Dict[str, Any]:
        """Finalize test results and return summary"""
        self.end_time = datetime.now()
        
        # Calculate averages
        if self.judge_scores:
            self.avg_judge_score = sum(score.overall for score in self.judge_scores) / len(self.judge_scores)
        
        avg_response_time = self.total_response_time_ms / self.total_turns if self.total_turns > 0 else 0
        success_rate = self.success_count / self.total_turns if self.total_turns > 0 else 0
        
        execution_time = (self.end_time - self.start_time).total_seconds()
        
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "user_id": self.user_id,
            "execution_summary": {
                "total_turns": self.total_turns,
                "successful_turns": self.success_count,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "avg_judge_score": self.avg_judge_score,
                "total_execution_time_seconds": execution_time,
                "errors_count": len(self.errors)
            },
            "turn_results": self.turn_results,
            "errors": self.errors,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }


class MinimalTestRunner:
    """
    Test runner for conversation datasets.
    
    Executes conversation datasets sequentially, maintaining conversation state
    and collecting metrics via Task 1-2 infrastructure.
    """
    
    def __init__(
        self,
        datasets_directory: str = "./test_datasets",
        user_id: Optional[str] = None,
        enable_judge: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        self.datasets_directory = Path(datasets_directory)
        self.user_id = user_id or "fa97efb5-410d-4806-b137-8cf13b6cb464"  # Default test user
        self.enable_judge = enable_judge
        self.progress_callback = progress_callback
        
        # State management
        self.state_manager = get_conversation_state_manager()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.test_results: List[Dict[str, Any]] = []
    
    def load_conversation_datasets(self) -> List[ConversationDataset]:
        """
        Load all conversation datasets from the datasets directory.
        
        Returns:
            List of ConversationDataset objects
        """
        datasets = []
        
        if not self.datasets_directory.exists():
            self.logger.warning(f"Datasets directory not found: {self.datasets_directory}")
            return datasets
        
        # Look for conversation dataset JSON files
        for json_file in self.datasets_directory.glob("conversation_*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                dataset = ConversationDataset.from_dict(data)
                datasets.append(dataset)
                
                self.logger.info(f"Loaded dataset: {dataset.name} ({dataset.conversation_length} turns)")
                
            except Exception as e:
                self.logger.error(f"Failed to load dataset {json_file.name}: {e}")
        
        self.logger.info(f"Loaded {len(datasets)} conversation datasets")
        return datasets
    
    @evaluate(name="execute_conversation_turn", capture_result=True)
    async def execute_conversation_turn(
        self,
        turn: ConversationTurn,
        state: ConversationState
    ) -> Dict[str, Any]:
        """
        Execute a single conversation turn with evaluation decorator.
        
        Args:
            turn: Conversation turn to execute
            state: Current conversation state
            
        Returns:
            Execution result with timing and response data
        """
        start_time = time.time()
        error = None
        mcp_response = None
        judge_score = None
        
        try:
            # Add memories for this turn to conversation state
            state.add_memories_for_turn(turn.relevant_memories)
            
            # Call jean_memory via MCP client
            mcp_response = await call_jean_memory(
                user_message=turn.user_message,
                user_id=state.user_id,
                is_new_conversation=state.is_new_conversation,
                needs_context=True,
                speed="balanced",
                format="enhanced"
            )
            
            # Judge the response if enabled
            if self.enable_judge and mcp_response and mcp_response.is_success:
                try:
                    # Convert memories to format expected by judge
                    memories_for_judge = [
                        {"content": mem.content} 
                        for mem in state.accumulated_memories
                    ]
                    
                    judge_score = await evaluate_single_response(
                        query=turn.user_message,
                        memories=memories_for_judge,
                        response=mcp_response.summary_text or "",
                        reasoning_type=turn.reasoning_type
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Judge evaluation failed for turn {turn.turn_number}: {e}")
                    judge_score = None
            
        except MCPError as e:
            error = f"MCP Error: {str(e)}"
            self.logger.error(f"Turn {turn.turn_number} MCP error: {e}")
            
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            self.logger.error(f"Turn {turn.turn_number} unexpected error: {e}")
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Record turn result in conversation state
        actual_response = ""
        if mcp_response and mcp_response.summary_text:
            actual_response = mcp_response.summary_text
        elif error:
            actual_response = f"Error: {error}"
        
        state.record_turn_result(
            turn=turn,
            actual_response=actual_response,
            response_time_ms=response_time_ms,
            success=error is None and mcp_response is not None and mcp_response.is_success,
            error=error
        )
        
        return {
            "turn_number": turn.turn_number,
            "user_message": turn.user_message,
            "response_time_ms": response_time_ms,
            "success": error is None,
            "error": error,
            "mcp_response": mcp_response,
            "judge_score": judge_score,
            "memories_available": len(state.accumulated_memories)
        }
    
    async def execute_conversation_dataset(
        self,
        dataset: ConversationDataset
    ) -> ConversationTestResult:
        """
        Execute a complete conversation dataset.
        
        Args:
            dataset: Conversation dataset to execute
            
        Returns:
            ConversationTestResult with all execution results
        """
        self.logger.info(f"Starting execution of dataset: {dataset.name}")
        
        # Create conversation state
        state = self.state_manager.create_conversation_state(dataset, self.user_id)
        
        # Create result tracker
        test_result = ConversationTestResult(
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            conversation_length=dataset.conversation_length,
            user_id=self.user_id
        )
        
        # Execute each turn sequentially
        for turn in dataset.turns:
            self.logger.info(f"Executing turn {turn.turn_number}/{dataset.conversation_length}: "
                           f"{turn.user_message[:50]}...")
            
            # Progress callback
            if self.progress_callback:
                self.progress_callback(
                    turn.turn_number, 
                    dataset.conversation_length, 
                    f"Turn {turn.turn_number}: {turn.reasoning_type.value}"
                )
            
            # Execute turn with evaluation decorator
            turn_execution = await self.execute_conversation_turn(turn, state)
            
            # Add to test results
            test_result.add_turn_result(
                turn=turn,
                mcp_response=turn_execution.get("mcp_response"),
                judge_score=turn_execution.get("judge_score"),
                response_time_ms=turn_execution.get("response_time_ms", 0),
                error=turn_execution.get("error")
            )
            
            # Advance conversation state
            state.advance_turn()
            
            self.logger.info(f"Turn {turn.turn_number} completed: "
                           f"success={turn_execution.get('success', False)}, "
                           f"time={turn_execution.get('response_time_ms', 0):.1f}ms")
        
        # Clean up conversation state
        conversation_summary = self.state_manager.cleanup_conversation_state(dataset.id)
        
        self.logger.info(f"Dataset '{dataset.name}' execution completed: "
                        f"success_rate={test_result.success_count}/{test_result.total_turns}")
        
        return test_result
    
    @evaluate(name="run_conversation_test_suite", capture_result=True)
    async def run_test_suite(
        self,
        dataset_filter: Optional[str] = None,
        max_datasets: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run the complete conversation test suite.
        
        Args:
            dataset_filter: Optional filter for dataset names (substring match)
            max_datasets: Maximum number of datasets to execute
            
        Returns:
            Complete test suite results
        """
        # Check prerequisites
        if not is_authenticated():
            raise RuntimeError("Authentication required. Please run token setup first.")
        
        # Load datasets
        datasets = self.load_conversation_datasets()
        
        if not datasets:
            raise RuntimeError(f"No conversation datasets found in {self.datasets_directory}")
        
        # Apply filters
        if dataset_filter:
            datasets = [d for d in datasets if dataset_filter.lower() in d.name.lower()]
            self.logger.info(f"Filtered to {len(datasets)} datasets matching '{dataset_filter}'")
        
        if max_datasets:
            datasets = datasets[:max_datasets]
            self.logger.info(f"Limited to {max_datasets} datasets")
        
        self.logger.info(f"Starting test suite with {len(datasets)} datasets")
        
        # Execute all datasets
        suite_start_time = time.time()
        all_results = []
        
        for i, dataset in enumerate(datasets, 1):
            self.logger.info(f"Dataset {i}/{len(datasets)}: {dataset.name}")
            
            try:
                test_result = await self.execute_conversation_dataset(dataset)
                result_summary = test_result.finalize()
                all_results.append(result_summary)
                
            except Exception as e:
                self.logger.error(f"Dataset {dataset.name} failed: {e}")
                # Create error result
                error_result = {
                    "dataset_id": dataset.id,
                    "dataset_name": dataset.name,
                    "error": str(e),
                    "execution_summary": {
                        "total_turns": 0,
                        "successful_turns": 0,
                        "success_rate": 0,
                        "errors_count": 1
                    }
                }
                all_results.append(error_result)
        
        suite_duration = time.time() - suite_start_time
        
        # Calculate suite-level metrics
        total_turns = sum(result["execution_summary"]["total_turns"] for result in all_results)
        successful_turns = sum(result["execution_summary"]["successful_turns"] for result in all_results)
        suite_success_rate = successful_turns / total_turns if total_turns > 0 else 0
        
        # Get average judge scores
        judge_scores = []
        for result in all_results:
            if "avg_judge_score" in result.get("execution_summary", {}):
                score = result["execution_summary"]["avg_judge_score"]
                if score > 0:
                    judge_scores.append(score)
        
        avg_judge_score = sum(judge_scores) / len(judge_scores) if judge_scores else 0
        
        suite_summary = {
            "suite_execution_summary": {
                "datasets_executed": len(all_results),
                "datasets_successful": len([r for r in all_results if r["execution_summary"]["success_rate"] > 0]),
                "total_turns": total_turns,
                "successful_turns": successful_turns,
                "suite_success_rate": suite_success_rate,
                "avg_judge_score": avg_judge_score,
                "total_execution_time_seconds": suite_duration,
                "user_id": self.user_id
            },
            "dataset_results": all_results,
            "execution_timestamp": datetime.now().isoformat()
        }
        
        # Store results
        self.test_results.append(suite_summary)
        
        self.logger.info(f"Test suite completed: {len(datasets)} datasets, "
                        f"success_rate={suite_success_rate:.1%}, "
                        f"avg_judge_score={avg_judge_score:.1f}/10")
        
        return suite_summary


# Convenience functions
async def run_conversation_test(
    datasets_directory: str = "./test_datasets",
    user_id: Optional[str] = None,
    dataset_filter: Optional[str] = None,
    max_datasets: Optional[int] = None,
    enable_judge: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """
    Run conversation tests with default settings.
    
    Args:
        datasets_directory: Directory containing conversation datasets
        user_id: User ID for API calls
        dataset_filter: Filter datasets by name substring
        max_datasets: Maximum number of datasets to run
        enable_judge: Whether to enable LLM judge evaluation
        progress_callback: Optional progress callback function
        
    Returns:
        Complete test suite results
    """
    runner = MinimalTestRunner(
        datasets_directory=datasets_directory,
        user_id=user_id,
        enable_judge=enable_judge,
        progress_callback=progress_callback
    )
    
    return await runner.run_test_suite(
        dataset_filter=dataset_filter,
        max_datasets=max_datasets
    )


def simple_progress_callback(current: int, total: int, description: str) -> None:
    """Simple progress callback that prints to console"""
    percentage = (current / total) * 100
    print(f"Progress: {current}/{total} ({percentage:.1f}%) - {description}")