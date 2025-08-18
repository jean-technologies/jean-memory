"""
Conversation Dataset Generator for Jean Memory Evaluation
========================================================

Creates realistic multi-turn conversation datasets by sequencing synthetic test cases
from Task 3, with configurable conversation length and reasoning type distribution.

Part of Task 4: Conversation Dataset Generator
"""

import asyncio
import json
import logging
import os
import random
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

# Import Task 3 infrastructure
from .synthetic_data_generator import (
    SyntheticDataGeneratorService,
    SyntheticTestCase,
    Memory,
    ReasoningType,
    DifficultyLevel,
    PersonaType,
    ConversationDecisionPath,
    get_synthetic_generator
)
from .synthetic_quality_validator import validate_single_test_case

logger = logging.getLogger(__name__)


class ConversationDistributionType(Enum):
    """Controls how reasoning types are distributed across conversation"""
    UNIFORM = "uniform"  # Single reasoning type throughout
    MIXED = "mixed"      # Varied reasoning types across turns
    PROGRESSIVE = "progressive"  # Start simple, get more complex


@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    turn_number: int
    user_message: str
    expected_response: str
    reasoning_type: ReasoningType
    difficulty: DifficultyLevel
    relevant_memories: List[Memory]
    test_case_id: str
    

@dataclass
class ConversationDataset:
    """Complete conversation dataset with metadata"""
    id: str
    name: str
    description: str
    
    # Configuration
    conversation_length: int
    distribution_type: ConversationDistributionType
    target_reasoning_types: List[ReasoningType]
    persona: PersonaType
    
    # Content
    turns: List[ConversationTurn]
    all_memories: List[Memory]  # All memories that could be referenced
    
    # Metadata
    creation_timestamp: datetime
    generator_version: str
    total_test_cases: int
    reasoning_type_distribution: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conversation_length": self.conversation_length,
            "distribution_type": self.distribution_type.value,
            "target_reasoning_types": [rt.value for rt in self.target_reasoning_types],
            "persona": self.persona.value,
            "turns": [
                {
                    "turn_number": turn.turn_number,
                    "user_message": turn.user_message,
                    "expected_response": turn.expected_response,
                    "reasoning_type": turn.reasoning_type.value,
                    "difficulty": turn.difficulty.value,
                    "relevant_memories": [mem.to_dict() for mem in turn.relevant_memories],
                    "test_case_id": turn.test_case_id
                }
                for turn in self.turns
            ],
            "all_memories": [mem.to_dict() for mem in self.all_memories],
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "generator_version": self.generator_version,
            "total_test_cases": self.total_test_cases,
            "reasoning_type_distribution": self.reasoning_type_distribution
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationDataset':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            conversation_length=data["conversation_length"],
            distribution_type=ConversationDistributionType(data["distribution_type"]),
            target_reasoning_types=[ReasoningType(rt) for rt in data["target_reasoning_types"]],
            persona=PersonaType(data["persona"]),
            turns=[
                ConversationTurn(
                    turn_number=turn_data["turn_number"],
                    user_message=turn_data["user_message"],
                    expected_response=turn_data["expected_response"],
                    reasoning_type=ReasoningType(turn_data["reasoning_type"]),
                    difficulty=DifficultyLevel(turn_data["difficulty"]),
                    relevant_memories=[
                        Memory(
                            content=mem["content"],
                            timestamp=datetime.fromisoformat(mem["timestamp"]),
                            metadata=mem.get("metadata", {}),
                            importance=mem.get("importance", 0.5)
                        )
                        for mem in turn_data["relevant_memories"]
                    ],
                    test_case_id=turn_data["test_case_id"]
                )
                for turn_data in data["turns"]
            ],
            all_memories=[
                Memory(
                    content=mem["content"],
                    timestamp=datetime.fromisoformat(mem["timestamp"]),
                    metadata=mem.get("metadata", {}),
                    importance=mem.get("importance", 0.5)
                )
                for mem in data["all_memories"]
            ],
            creation_timestamp=datetime.fromisoformat(data["creation_timestamp"]),
            generator_version=data["generator_version"],
            total_test_cases=data["total_test_cases"],
            reasoning_type_distribution=data["reasoning_type_distribution"]
        )


class ConversationDatasetGenerator:
    """Generates conversation datasets using Task 3 synthetic data generator"""
    
    def __init__(self, storage_path: str = "./test_datasets", require_generator: bool = True):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        if require_generator:
            self.generator = get_synthetic_generator()
        else:
            self.generator = None
            
        self.generator_version = "1.0.0"
        
    async def generate_conversation_dataset(
        self,
        name: str,
        conversation_length: int,
        distribution_type: ConversationDistributionType = ConversationDistributionType.MIXED,
        target_reasoning_types: Optional[List[ReasoningType]] = None,
        persona: PersonaType = PersonaType.CASUAL,
        description: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> ConversationDataset:
        """
        Generate a complete conversation dataset
        
        Args:
            name: Dataset name
            conversation_length: Number of turns (5-35)
            distribution_type: How to distribute reasoning types
            target_reasoning_types: Specific reasoning types to include
            persona: User persona for consistency
            description: Dataset description
            progress_callback: Called with (current, total) for progress
            
        Returns:
            ConversationDataset with all turns and metadata
        """
        if conversation_length < 5 or conversation_length > 35:
            raise ValueError("Conversation length must be between 5 and 35 turns")
            
        if target_reasoning_types is None:
            target_reasoning_types = list(ReasoningType)
            
        dataset_id = str(uuid.uuid4())
        
        # Determine reasoning type sequence based on distribution
        reasoning_sequence = self._create_reasoning_sequence(
            conversation_length, distribution_type, target_reasoning_types
        )
        
        # Generate conversation with topic continuity
        turns = []
        all_memories = []
        conversation_context = {
            "topic": None,
            "previous_memories": [],
            "conversation_history": []
        }
        
        for turn_num in range(conversation_length):
            if progress_callback:
                progress_callback(turn_num + 1, conversation_length)
                
            reasoning_type = reasoning_sequence[turn_num]
            
            # Determine difficulty progression
            difficulty = self._determine_difficulty(turn_num, conversation_length)
            
            # Generate turn with context from previous turns
            turn = await self._generate_conversation_turn(
                turn_num + 1,
                reasoning_type,
                difficulty,
                persona,
                conversation_context
            )
            
            turns.append(turn)
            all_memories.extend(turn.relevant_memories)
            
            # Update conversation context for next turn
            conversation_context["conversation_history"].append({
                "turn": turn_num + 1,
                "query": turn.user_message,
                "response": turn.expected_response,
                "reasoning_type": reasoning_type
            })
            conversation_context["previous_memories"].extend(turn.relevant_memories)
            
            # Small delay to avoid overwhelming the LLM providers
            await asyncio.sleep(0.1)
        
        # Calculate reasoning type distribution
        reasoning_distribution = {}
        for reasoning_type in ReasoningType:
            count = sum(1 for turn in turns if turn.reasoning_type == reasoning_type)
            if count > 0:
                reasoning_distribution[reasoning_type.value] = count
        
        return ConversationDataset(
            id=dataset_id,
            name=name,
            description=description or f"Generated conversation dataset with {conversation_length} turns",
            conversation_length=conversation_length,
            distribution_type=distribution_type,
            target_reasoning_types=target_reasoning_types,
            persona=persona,
            turns=turns,
            all_memories=all_memories,
            creation_timestamp=datetime.now(),
            generator_version=self.generator_version,
            total_test_cases=len(turns),
            reasoning_type_distribution=reasoning_distribution
        )
    
    def _create_reasoning_sequence(
        self,
        length: int,
        distribution_type: ConversationDistributionType,
        target_types: List[ReasoningType]
    ) -> List[ReasoningType]:
        """Create sequence of reasoning types for conversation"""
        
        if distribution_type == ConversationDistributionType.UNIFORM:
            # Pick one reasoning type and use throughout
            chosen_type = random.choice(target_types)
            return [chosen_type] * length
            
        elif distribution_type == ConversationDistributionType.MIXED:
            # Randomly distribute but ensure all types are represented
            sequence = []
            for i in range(length):
                sequence.append(random.choice(target_types))
            return sequence
            
        elif distribution_type == ConversationDistributionType.PROGRESSIVE:
            # Start with simple reasoning, progress to complex
            complexity_order = [
                ReasoningType.SINGLE_HOP,
                ReasoningType.COMMONSENSE,
                ReasoningType.TEMPORAL,
                ReasoningType.MULTI_HOP,
                ReasoningType.ADVERSARIAL
            ]
            
            # Filter to only target types, maintain order
            available_types = [rt for rt in complexity_order if rt in target_types]
            if not available_types:
                available_types = target_types
                
            sequence = []
            for i in range(length):
                # Progress through complexity
                complexity_index = min(i // (length // len(available_types)), len(available_types) - 1)
                sequence.append(available_types[complexity_index])
            
            return sequence
        
        else:
            raise ValueError(f"Unknown distribution type: {distribution_type}")
    
    def _determine_difficulty(self, turn_num: int, total_turns: int) -> DifficultyLevel:
        """Determine difficulty based on conversation progress"""
        progress = turn_num / total_turns
        
        if progress < 0.3:
            return DifficultyLevel.EASY
        elif progress < 0.7:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.HARD
    
    async def _generate_conversation_turn(
        self,
        turn_number: int,
        reasoning_type: ReasoningType,
        difficulty: DifficultyLevel,
        persona: PersonaType,
        conversation_context: Dict[str, Any]
    ) -> ConversationTurn:
        """Generate a single conversation turn with context continuity"""
        
        # Try to generate with requested reasoning type, fallback to simpler types if blocked
        fallback_types = [reasoning_type, ReasoningType.SINGLE_HOP]
        test_case = None
        
        for attempt_type in fallback_types:
            try:
                test_case = await self.generator.generate_test_case(
                    reasoning_type=attempt_type,
                    difficulty=difficulty,
                    persona=persona
                )
                if attempt_type != reasoning_type:
                    logger.warning(f"⚠️ Fell back from {reasoning_type.value} to {attempt_type.value} due to safety filters")
                reasoning_type = attempt_type  # Update to actual type used
                break
            except ValueError as e:
                if "Content blocked" in str(e) or "finish_reason" in str(e):
                    logger.warning(f"⚠️ Safety filter blocked {attempt_type.value}, trying fallback...")
                    continue
                else:
                    raise  # Re-raise non-safety errors
        
        if test_case is None:
            raise ValueError("All reasoning types blocked by safety filters")
        
        # If we have previous memories, potentially reference them for continuity
        if conversation_context["previous_memories"] and turn_number > 1:
            # Add some previous memories to create conversation continuity
            additional_memories = random.sample(
                conversation_context["previous_memories"],
                min(2, len(conversation_context["previous_memories"]))
            )
            test_case.memories.extend(additional_memories)
        
        # Create a more conversational query if we have context
        if conversation_context["conversation_history"] and turn_number > 1:
            # Modify the query to feel more like a continuation
            original_query = test_case.query
            if not any(word in original_query.lower() for word in ["and", "also", "what about", "tell me more"]):
                # Make it feel more conversational
                conversational_starters = [
                    "Also, ",
                    "And ",
                    "What about ",
                    "Tell me more about ",
                    "I'm also curious about "
                ]
                starter = random.choice(conversational_starters)
                test_case.query = starter + original_query.lower()
        
        return ConversationTurn(
            turn_number=turn_number,
            user_message=test_case.query,
            expected_response=test_case.expected_response,
            reasoning_type=reasoning_type,
            difficulty=difficulty,
            relevant_memories=test_case.memories,
            test_case_id=test_case.id
        )
    
    async def save_dataset(self, dataset: ConversationDataset) -> str:
        """Save dataset to JSON file with timestamp-based naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{dataset.name.replace(' ', '_')}_{timestamp}.json"
        filepath = self.storage_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved conversation dataset to {filepath}")
        return str(filepath)
    
    async def load_dataset(self, filepath: str) -> ConversationDataset:
        """Load dataset from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return ConversationDataset.from_dict(data)
    
    async def validate_dataset(self, dataset: ConversationDataset) -> Dict[str, Any]:
        """Validate conversation dataset quality and coherence"""
        validation_results = {
            "valid": True,
            "issues": [],
            "statistics": {
                "total_turns": len(dataset.turns),
                "reasoning_distribution": dataset.reasoning_type_distribution,
                "avg_memories_per_turn": sum(len(turn.relevant_memories) for turn in dataset.turns) / len(dataset.turns),
                "persona_consistency": dataset.persona.value
            }
        }
        
        # Check conversation length
        if len(dataset.turns) != dataset.conversation_length:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Turn count mismatch: expected {dataset.conversation_length}, got {len(dataset.turns)}")
        
        # Check turn numbering
        for i, turn in enumerate(dataset.turns):
            if turn.turn_number != i + 1:
                validation_results["valid"] = False
                validation_results["issues"].append(f"Turn numbering error at position {i}: expected {i+1}, got {turn.turn_number}")
        
        # Check for empty content
        for turn in dataset.turns:
            if not turn.user_message.strip():
                validation_results["valid"] = False
                validation_results["issues"].append(f"Empty user message in turn {turn.turn_number}")
            if not turn.expected_response.strip():
                validation_results["valid"] = False
                validation_results["issues"].append(f"Empty expected response in turn {turn.turn_number}")
        
        return validation_results


# Global instance
_conversation_generator = None

def get_conversation_generator() -> ConversationDatasetGenerator:
    """Get shared conversation dataset generator instance"""
    global _conversation_generator
    if _conversation_generator is None:
        _conversation_generator = ConversationDatasetGenerator()
    return _conversation_generator


# Convenience functions
async def generate_conversation_dataset(
    name: str,
    conversation_length: int,
    distribution_type: ConversationDistributionType = ConversationDistributionType.MIXED,
    target_reasoning_types: Optional[List[ReasoningType]] = None,
    persona: PersonaType = PersonaType.CASUAL,
    description: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> ConversationDataset:
    """Generate conversation dataset (convenience function)"""
    generator = get_conversation_generator()
    return await generator.generate_conversation_dataset(
        name=name,
        conversation_length=conversation_length,
        distribution_type=distribution_type,
        target_reasoning_types=target_reasoning_types,
        persona=persona,
        description=description,
        progress_callback=progress_callback
    )


async def save_conversation_dataset(dataset: ConversationDataset) -> str:
    """Save conversation dataset (convenience function)"""
    generator = get_conversation_generator()
    return await generator.save_dataset(dataset)


async def load_conversation_dataset(filepath: str) -> ConversationDataset:
    """Load conversation dataset (convenience function)"""
    generator = get_conversation_generator()
    return await generator.load_dataset(filepath)