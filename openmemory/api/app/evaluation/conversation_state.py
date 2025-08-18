"""
Conversation State Management for Test Runner

Manages conversation context and memory accumulation across test turns,
ensuring consistent state for sequential conversation testing.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .conversation_dataset_generator import ConversationDataset, ConversationTurn, Memory
from .llm_judge import ReasoningType


logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """
    Maintains conversation state across multiple turns.
    
    Tracks accumulated memories, conversation history, and context
    for consistent test execution.
    """
    
    # Dataset information
    dataset_id: str
    dataset_name: str
    conversation_length: int
    
    # Current state
    current_turn: int = 0
    is_new_conversation: bool = True
    
    # Memory accumulation
    accumulated_memories: List[Memory] = field(default_factory=list)
    turn_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Context management
    user_id: str = ""
    conversation_start_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize conversation state"""
        if self.conversation_start_time is None:
            self.conversation_start_time = datetime.now()
    
    def add_memories_for_turn(self, memories: List[Memory]) -> None:
        """
        Add memories that should be available for current turn.
        
        Args:
            memories: List of memories to add to conversation context
        """
        # Add new memories to accumulated set (avoid duplicates)
        for memory in memories:
            if not any(existing.content == memory.content for existing in self.accumulated_memories):
                self.accumulated_memories.append(memory)
        
        logger.debug(f"Turn {self.current_turn}: Added {len(memories)} memories, "
                    f"total accumulated: {len(self.accumulated_memories)}")
    
    def record_turn_result(
        self, 
        turn: ConversationTurn, 
        actual_response: str, 
        response_time_ms: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Record the result of executing a conversation turn.
        
        Args:
            turn: The conversation turn that was executed
            actual_response: The actual response from jean_memory
            response_time_ms: Response time in milliseconds
            success: Whether the turn was successful
            error: Error message if turn failed
        """
        turn_record = {
            "turn_number": turn.turn_number,
            "user_message": turn.user_message,
            "expected_response": turn.expected_response,
            "actual_response": actual_response,
            "reasoning_type": turn.reasoning_type.value,
            "difficulty": turn.difficulty.value,
            "response_time_ms": response_time_ms,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "memories_available": len(self.accumulated_memories),
            "test_case_id": turn.test_case_id
        }
        
        self.turn_history.append(turn_record)
        logger.debug(f"Recorded turn {turn.turn_number} result: success={success}, "
                    f"response_time={response_time_ms:.1f}ms")
    
    def advance_turn(self) -> None:
        """Advance to next conversation turn"""
        self.current_turn += 1
        # After first turn, no longer a new conversation
        if self.current_turn > 1:
            self.is_new_conversation = False
        
        logger.debug(f"Advanced to turn {self.current_turn}, "
                    f"is_new_conversation={self.is_new_conversation}")
    
    def is_conversation_complete(self) -> bool:
        """Check if conversation is complete"""
        return self.current_turn >= self.conversation_length
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of conversation execution.
        
        Returns:
            Summary dictionary with execution statistics
        """
        successful_turns = sum(1 for turn in self.turn_history if turn["success"])
        total_response_time = sum(turn["response_time_ms"] for turn in self.turn_history)
        avg_response_time = total_response_time / len(self.turn_history) if self.turn_history else 0
        
        reasoning_type_counts = {}
        for turn in self.turn_history:
            reasoning_type = turn["reasoning_type"]
            reasoning_type_counts[reasoning_type] = reasoning_type_counts.get(reasoning_type, 0) + 1
        
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "conversation_length": self.conversation_length,
            "turns_executed": len(self.turn_history),
            "successful_turns": successful_turns,
            "success_rate": successful_turns / len(self.turn_history) if self.turn_history else 0,
            "total_response_time_ms": total_response_time,
            "avg_response_time_ms": avg_response_time,
            "total_memories_accumulated": len(self.accumulated_memories),
            "reasoning_type_distribution": reasoning_type_counts,
            "conversation_start_time": self.conversation_start_time.isoformat() if self.conversation_start_time else None,
            "conversation_duration_seconds": (datetime.now() - self.conversation_start_time).total_seconds() if self.conversation_start_time else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "conversation_length": self.conversation_length,
            "current_turn": self.current_turn,
            "is_new_conversation": self.is_new_conversation,
            "user_id": self.user_id,
            "conversation_start_time": self.conversation_start_time.isoformat() if self.conversation_start_time else None,
            "accumulated_memories": [
                {
                    "content": mem.content,
                    "timestamp": mem.timestamp.isoformat(),
                    "metadata": mem.metadata,
                    "importance": mem.importance
                }
                for mem in self.accumulated_memories
            ],
            "turn_history": self.turn_history
        }


class ConversationStateManager:
    """
    Manages conversation states across multiple test runs.
    
    Provides utilities for creating, managing, and persisting conversation states.
    """
    
    def __init__(self):
        self.active_states: Dict[str, ConversationState] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_conversation_state(
        self, 
        dataset: ConversationDataset, 
        user_id: str
    ) -> ConversationState:
        """
        Create new conversation state for dataset.
        
        Args:
            dataset: Conversation dataset to execute
            user_id: User ID for API calls
            
        Returns:
            ConversationState ready for test execution
        """
        state = ConversationState(
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            conversation_length=dataset.conversation_length,
            user_id=user_id,
            current_turn=1,  # Start at turn 1
            is_new_conversation=True
        )
        
        # Store active state
        self.active_states[dataset.id] = state
        
        self.logger.info(f"Created conversation state for dataset '{dataset.name}' "
                        f"({dataset.conversation_length} turns)")
        
        return state
    
    def get_conversation_state(self, dataset_id: str) -> Optional[ConversationState]:
        """Get active conversation state by dataset ID"""
        return self.active_states.get(dataset_id)
    
    def cleanup_conversation_state(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Clean up conversation state and return final summary.
        
        Args:
            dataset_id: ID of dataset to clean up
            
        Returns:
            Final conversation summary or None if state not found
        """
        state = self.active_states.pop(dataset_id, None)
        if state:
            summary = state.get_conversation_summary()
            self.logger.info(f"Cleaned up conversation state for {dataset_id}, "
                           f"success_rate={summary['success_rate']:.1%}")
            return summary
        return None
    
    def get_all_active_states(self) -> List[ConversationState]:
        """Get all currently active conversation states"""
        return list(self.active_states.values())
    
    def clear_all_states(self) -> None:
        """Clear all active conversation states"""
        count = len(self.active_states)
        self.active_states.clear()
        self.logger.info(f"Cleared {count} active conversation states")


# Global state manager instance
_state_manager: Optional[ConversationStateManager] = None


def get_conversation_state_manager() -> ConversationStateManager:
    """Get global conversation state manager"""
    global _state_manager
    if _state_manager is None:
        _state_manager = ConversationStateManager()
    return _state_manager