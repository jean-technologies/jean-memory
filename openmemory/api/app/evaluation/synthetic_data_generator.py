"""
Synthetic Test Data Generator for Jean Memory Evaluation
======================================================

LLM-powered system that generates diverse conversation scenarios, memory sequences,
and test cases covering all LoCoMo reasoning types for comprehensive evaluation coverage.

Part of Task 3: Synthetic Test Data Generator
"""

import asyncio
import json
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field

# Import Task 1-2 infrastructure
from .llm_judge import ReasoningType, LLMProvider, LLMJudgeService
from .core import evaluate

logger = logging.getLogger(__name__)


# Pydantic models for structured output
class SyntheticMemory(BaseModel):
    """Memory for synthetic test case"""
    content: str = Field(description="Memory content, max 100 characters")
    days_ago: int = Field(description="Days ago this memory was created")
    importance: float = Field(description="Importance score")


class SyntheticTestCaseSchema(BaseModel):
    """Schema for synthetic test case generation"""
    scenario_description: str = Field(description="Brief scenario description, max 50 characters")
    memories: List[SyntheticMemory] = Field(description="List of relevant memories")
    query: str = Field(description="User's question or query, max 100 characters")
    expected_response: str = Field(description="AI's expected response, max 150 characters")
    reasoning_explanation: str = Field(description="Why this tests the reasoning type, max 50 characters")


class MultiHopSyntheticTestCaseSchema(SyntheticTestCaseSchema):
    """Extended schema for multi-hop reasoning"""
    hop_sequence: List[str] = Field(description="Step-by-step reasoning sequence")


class TemporalSyntheticTestCaseSchema(SyntheticTestCaseSchema):
    """Extended schema for temporal reasoning"""
    temporal_span_days: int = Field(description="Time span covered by memories in days")
    temporal_relationships: List[str] = Field(description="Temporal relationships between memories")


class AdversarialSyntheticTestCaseSchema(SyntheticTestCaseSchema):
    """Extended schema for adversarial reasoning"""
    conflicting_info_count: int = Field(description="Number of conflicting pieces of information")
    resolution_strategy: str = Field(description="How the AI should resolve conflicts")


class CommonsenseSyntheticTestCaseSchema(SyntheticTestCaseSchema):
    """Extended schema for commonsense reasoning"""
    commonsense_required: List[str] = Field(description="Types of commonsense knowledge required")


class DifficultyLevel(Enum):
    """Test case difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ConversationDecisionPath(Enum):
    """Jean Memory decision paths to test"""
    NEW_CONVERSATION = "new_conversation"  # Start fresh conversation
    GENERIC_KNOWLEDGE = "generic_knowledge"  # No relevant memories
    CONTEXTUAL_CONVERSATION = "contextual_conversation"  # Memory-driven response


class PersonaType(Enum):
    """User persona types for diverse conversation generation"""
    PROFESSIONAL = "professional"  # Business person, entrepreneur
    STUDENT = "student"  # Academic, learner
    CREATIVE = "creative"  # Artist, writer, designer
    TECHNICAL = "technical"  # Engineer, developer, scientist
    CASUAL = "casual"  # General user, personal conversations


@dataclass
class Memory:
    """Individual memory for injection"""
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    importance: float = 0.5  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
            "importance": self.importance
        }


@dataclass
class SyntheticTestCase:
    """Generated test case with all metadata"""
    id: str
    reasoning_type: ReasoningType
    difficulty: DifficultyLevel
    persona: PersonaType
    decision_path: ConversationDecisionPath
    
    # Test content
    query: str
    memories: List[Memory]
    expected_response: str
    expected_memory_count: int
    
    # Generation metadata
    generation_timestamp: datetime
    generator_model: str
    quality_score: Optional[float] = None
    validation_notes: Optional[str] = None
    
    # LoCoMo specific requirements
    required_hops: Optional[int] = None  # For multi-hop reasoning
    temporal_span_days: Optional[int] = None  # For temporal reasoning
    conflicting_info_count: Optional[int] = None  # For adversarial
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            "id": self.id,
            "reasoning_type": self.reasoning_type.value,
            "difficulty": self.difficulty.value,
            "persona": self.persona.value,
            "decision_path": self.decision_path.value,
            "query": self.query,
            "memories": [mem.to_dict() for mem in self.memories],
            "expected_response": self.expected_response,
            "expected_memory_count": self.expected_memory_count,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "generator_model": self.generator_model,
            "quality_score": self.quality_score,
            "validation_notes": self.validation_notes,
            "required_hops": self.required_hops,
            "temporal_span_days": self.temporal_span_days,
            "conflicting_info_count": self.conflicting_info_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyntheticTestCase':
        """Create instance from dictionary"""
        memories = [Memory(
            content=mem["content"],
            timestamp=datetime.fromisoformat(mem["timestamp"]),
            metadata=mem.get("metadata", {}),
            importance=mem.get("importance", 0.5)
        ) for mem in data["memories"]]
        
        return cls(
            id=data["id"],
            reasoning_type=ReasoningType(data["reasoning_type"]),
            difficulty=DifficultyLevel(data["difficulty"]),
            persona=PersonaType(data["persona"]),
            decision_path=ConversationDecisionPath(data["decision_path"]),
            query=data["query"],
            memories=memories,
            expected_response=data["expected_response"],
            expected_memory_count=data["expected_memory_count"],
            generation_timestamp=datetime.fromisoformat(data["generation_timestamp"]),
            generator_model=data["generator_model"],
            quality_score=data.get("quality_score"),
            validation_notes=data.get("validation_notes"),
            required_hops=data.get("required_hops"),
            temporal_span_days=data.get("temporal_span_days"),
            conflicting_info_count=data.get("conflicting_info_count")
        )


class SyntheticDataGeneratorService:
    """
    Core service for generating synthetic test data using LLM providers.
    Integrates with Task 1-2 infrastructure for quality validation.
    """
    
    def __init__(self):
        """Initialize with LLM providers from Task 2"""
        self.judge_service = LLMJudgeService()
        self.generation_enabled = os.getenv("SYNTHETIC_GENERATION_ENABLED", "false").lower() == "true"
        self.default_provider = os.getenv("SYNTHETIC_GENERATOR_PROVIDER", "auto")
        self.batch_size = int(os.getenv("SYNTHETIC_BATCH_SIZE", "10"))
        self.quality_threshold = float(os.getenv("SYNTHETIC_QUALITY_THRESHOLD", "7.0"))
        
        # Persona-specific conversation styles
        self.persona_styles = {
            PersonaType.PROFESSIONAL: "Business-focused, goal-oriented, discusses meetings, projects, career growth",
            PersonaType.STUDENT: "Learning-focused, asks questions, discusses courses, study habits, academic goals",
            PersonaType.CREATIVE: "Art-focused, discusses projects, inspiration, creative process, exhibitions",
            PersonaType.TECHNICAL: "Technology-focused, discusses code, systems, tools, technical challenges",
            PersonaType.CASUAL: "Personal conversations, daily life, hobbies, relationships, general interests"
        }
        
        logger.info(f"🧬 Synthetic Data Generator initialized - Enabled: {self.generation_enabled}")
    
    async def generate_test_case(
        self,
        reasoning_type: ReasoningType,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        persona: PersonaType = PersonaType.CASUAL,
        decision_path: ConversationDecisionPath = ConversationDecisionPath.CONTEXTUAL_CONVERSATION
    ) -> SyntheticTestCase:
        """Generate a single synthetic test case"""
        
        if not self.generation_enabled:
            raise ValueError("Synthetic generation disabled. Set SYNTHETIC_GENERATION_ENABLED=true")
        
        test_case_id = str(uuid.uuid4())
        logger.info(f"🧬 Generating test case {test_case_id[:8]} - {reasoning_type.value}/{difficulty.value}")
        
        # Generate based on reasoning type
        if reasoning_type == ReasoningType.SINGLE_HOP:
            return await self._generate_single_hop(test_case_id, difficulty, persona, decision_path)
        elif reasoning_type == ReasoningType.MULTI_HOP:
            return await self._generate_multi_hop(test_case_id, difficulty, persona, decision_path)
        elif reasoning_type == ReasoningType.TEMPORAL:
            return await self._generate_temporal(test_case_id, difficulty, persona, decision_path)
        elif reasoning_type == ReasoningType.ADVERSARIAL:
            return await self._generate_adversarial(test_case_id, difficulty, persona, decision_path)
        elif reasoning_type == ReasoningType.COMMONSENSE:
            return await self._generate_commonsense(test_case_id, difficulty, persona, decision_path)
        else:
            raise ValueError(f"Unsupported reasoning type: {reasoning_type}")
    
    async def _generate_single_hop(
        self, 
        test_id: str, 
        difficulty: DifficultyLevel, 
        persona: PersonaType,
        decision_path: ConversationDecisionPath
    ) -> SyntheticTestCase:
        """Generate single-hop reasoning test case (direct fact retrieval)"""
        
        persona_style = self.persona_styles[persona]
        complexity = self._get_complexity_description(difficulty)
        
        prompt = f"""Generate a synthetic test case for SINGLE-HOP reasoning evaluation.

REQUIREMENTS:
- Reasoning Type: Single-hop (direct fact retrieval from one memory)
- Difficulty: {difficulty.value} ({complexity})
- Persona: {persona.value} ({persona_style})

CONSTRAINTS:
- scenario_description: Max 50 characters
- memories: 1-3 items, content max 100 characters each
- query: Max 100 characters
- expected_response: Max 150 characters
- reasoning_explanation: Max 50 characters

TASK: Create a realistic conversation where user asks for ONE specific fact directly available in memories.

BE CONCISE. Avoid verbose descriptions."""

        try:
            # Use structured output for reliable JSON generation
            data = await self.judge_service._call_gemini_structured(
                prompt, 
                SyntheticTestCaseSchema, 
                LLMProvider.GEMINI_FLASH
            )
            
            # Convert to our format (data is now a Pydantic object)
            memories = []
            for mem_data in data.memories:
                # Ensure days_ago is valid (≥ 1)
                days_ago = max(1, mem_data.days_ago)
                # Clamp importance to valid range
                importance = max(0.0, min(1.0, mem_data.importance))
                
                timestamp = datetime.now() - timedelta(days=days_ago)
                memory = Memory(
                    content=mem_data.content,
                    timestamp=timestamp,
                    importance=importance
                )
                memories.append(memory)
            
            return SyntheticTestCase(
                id=test_id,
                reasoning_type=ReasoningType.SINGLE_HOP,
                difficulty=difficulty,
                persona=persona,
                decision_path=decision_path,
                query=data.query,
                memories=memories,
                expected_response=data.expected_response,
                expected_memory_count=len(memories),
                generation_timestamp=datetime.now(),
                generator_model="gemini-2.5-flash",
                required_hops=1
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to generate single-hop test case: {e}")
            raise
    
    async def _generate_multi_hop(
        self, 
        test_id: str, 
        difficulty: DifficultyLevel, 
        persona: PersonaType,
        decision_path: ConversationDecisionPath
    ) -> SyntheticTestCase:
        """Generate multi-hop reasoning test case (cross-memory synthesis)"""
        
        persona_style = self.persona_styles[persona]
        complexity = self._get_complexity_description(difficulty)
        
        # Determine hops based on difficulty
        hops = {"easy": 2, "medium": 3, "hard": 4}[difficulty.value]
        
        prompt = f"""Generate a synthetic test case for MULTI-HOP reasoning evaluation.

REQUIREMENTS:
- Reasoning Type: Multi-hop (requires connecting {hops} different memories)
- Difficulty: {difficulty.value} ({complexity})
- Persona: {persona.value} ({persona_style})

CONSTRAINTS:
- scenario_description: Max 50 characters
- memories: {hops + 1} to {hops + 2} items, content max 100 characters each
- query: Max 100 characters
- expected_response: Max 150 characters
- reasoning_explanation: Max 50 characters
- hop_sequence: {hops} items, max 30 characters each

TASK: Create conversation where user query requires connecting information across {hops} memories.

BE CONCISE. Avoid verbose descriptions."""

        try:
            # Use structured output for reliable JSON generation
            data = await self.judge_service._call_gemini_structured(
                prompt, 
                MultiHopSyntheticTestCaseSchema, 
                LLMProvider.GEMINI_FLASH
            )
            
            # Convert to our format (data is now a Pydantic object)
            memories = []
            for mem_data in data.memories:
                # Ensure days_ago is valid (≥ 1)
                days_ago = max(1, mem_data.days_ago)
                # Clamp importance to valid range
                importance = max(0.0, min(1.0, mem_data.importance))
                
                timestamp = datetime.now() - timedelta(days=days_ago)
                memory = Memory(
                    content=mem_data.content,
                    timestamp=timestamp,
                    importance=importance
                )
                memories.append(memory)
            
            return SyntheticTestCase(
                id=test_id,
                reasoning_type=ReasoningType.MULTI_HOP,
                difficulty=difficulty,
                persona=persona,
                decision_path=decision_path,
                query=data.query,
                memories=memories,
                expected_response=data.expected_response,
                expected_memory_count=len(memories),
                generation_timestamp=datetime.now(),
                generator_model="gemini-2.5-flash",
                required_hops=hops,
                validation_notes=f"Hop sequence: {'; '.join(data.hop_sequence)}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to generate multi-hop test case: {e}")
            raise
    
    async def _generate_temporal(
        self, 
        test_id: str, 
        difficulty: DifficultyLevel, 
        persona: PersonaType,
        decision_path: ConversationDecisionPath
    ) -> SyntheticTestCase:
        """Generate temporal reasoning test case (time-based context)"""
        
        persona_style = self.persona_styles[persona]
        complexity = self._get_complexity_description(difficulty)
        
        # Determine temporal span based on difficulty
        span_days = {"easy": 14, "medium": 60, "hard": 365}[difficulty.value]
        
        prompt = f"""Generate a synthetic test case for TEMPORAL reasoning evaluation.

REQUIREMENTS:
- Reasoning Type: Temporal (time-based reasoning over {span_days} days)
- Difficulty: {difficulty.value} ({complexity})
- Persona: {persona.value} ({persona_style})
- Decision Path: {decision_path.value}

TASK:
Create a realistic conversation scenario where:
1. User has 3-5 memories spread across {span_days} days
2. User asks a query that requires understanding temporal relationships
3. Answer requires reasoning about timing, sequences, or time-based patterns
4. Expected response demonstrates temporal awareness and chronological understanding

TEMPORAL REQUIREMENTS:
- Memories must have meaningful time relationships (before/after, during, progression)
- Query requires temporal reasoning (when, before/after, progression, trends)
- Answer should reference temporal context explicitly
- Time gaps should be meaningful to the reasoning

TEMPORAL PATTERNS TO INCLUDE:
- Chronological sequences (A happened before B which led to C)
- Temporal trends (improvement/decline over time)
- Time-sensitive contexts (seasonal, project timelines, life phases)
- Causal relationships with time delays

DIFFICULTY SCALING:
- Easy (14 days): Simple before/after relationships
- Medium (60 days): Trends and progressions over weeks
- Hard (365 days): Complex temporal patterns over months/seasons

OUTPUT FORMAT: Return ONLY valid JSON, no additional text, backticks, or formatting:
{{
    "scenario_description": "Description of the temporal reasoning required",
    "memories": [
        {{
            "content": "Memory content here",
            "days_ago": 30,
            "importance": 0.8,
            "temporal_context": "How this fits in the timeline"
        }}
    ],
    "query": "User's question requiring temporal reasoning",
    "expected_response": "AI's response showing temporal understanding",
    "temporal_relationships": ["Memory A (day X) led to Memory B (day Y)..."],
    "reasoning_explanation": "Why this requires temporal reasoning"
}}

CRITICAL: Respond with ONLY the JSON object. Do not include any explanatory text, backticks, or formatting markers."""

        try:
            # Use structured output for reliable JSON generation - will auto-select appropriate schema
            data = await self.judge_service._call_gemini_structured(
                prompt, 
                SyntheticTestCaseSchema, 
                LLMProvider.GEMINI_FLASH
            )
            
            # Convert to our format with realistic timestamps
            memories = []
            for mem_data in data.memories:
                # Ensure days_ago is valid (≥ 1)
                days_ago = max(1, mem_data.days_ago)
                # Clamp importance to valid range
                importance = max(0.0, min(1.0, mem_data.importance))
                
                timestamp = datetime.now() - timedelta(days=days_ago)
                memory = Memory(
                    content=mem_data.content,
                    timestamp=timestamp,
                    importance=importance,
                    metadata={"temporal_context": getattr(mem_data, "temporal_context", "")}
                )
                memories.append(memory)
            
            # Sort memories by timestamp for temporal validation
            memories.sort(key=lambda m: m.timestamp)
            
            return SyntheticTestCase(
                id=test_id,
                reasoning_type=ReasoningType.TEMPORAL,
                difficulty=difficulty,
                persona=persona,
                decision_path=decision_path,
                query=data.query,
                memories=memories,
                expected_response=data.expected_response,
                expected_memory_count=len(memories),
                generation_timestamp=datetime.now(),
                generator_model="gemini-2.5-flash",
                temporal_span_days=span_days,
                validation_notes=f"Temporal relationships: {'; '.join(getattr(data, 'temporal_relationships', []))}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to generate temporal test case: {e}")
            raise
    
    async def _generate_adversarial(
        self, 
        test_id: str, 
        difficulty: DifficultyLevel, 
        persona: PersonaType,
        decision_path: ConversationDecisionPath
    ) -> SyntheticTestCase:
        """Generate adversarial reasoning test case (conflicting information)"""
        
        persona_style = self.persona_styles[persona]
        complexity = self._get_complexity_description(difficulty)
        
        # Determine conflict count based on difficulty
        conflicts = {"easy": 1, "medium": 2, "hard": 3}[difficulty.value]
        
        prompt = f"""Generate a synthetic test case for ADVERSARIAL reasoning evaluation.

REQUIREMENTS:
- Reasoning Type: Adversarial (conflicting information handling)
- Difficulty: {difficulty.value} ({complexity})
- Persona: {persona.value} ({persona_style})
- Decision Path: {decision_path.value}
- Conflicts: {conflicts} conflicting pieces of information

TASK:
Create a realistic conversation scenario where:
1. User has 4-6 memories with {conflicts} direct conflicts or contradictions
2. User asks a query that forces the AI to handle conflicting information
3. Answer requires resolving conflicts through recency, importance, or context
4. Expected response demonstrates conflict resolution reasoning

ADVERSARIAL REQUIREMENTS:
- Include {conflicts} clear contradictions between memories
- Conflicts should be realistic (changed plans, updated preferences, corrected information)
- Query should touch on the conflicted information
- Expected response should handle conflicts intelligently (prefer recent, acknowledge uncertainty)

CONFLICT TYPES:
- Temporal conflicts (old vs new information)
- Preference conflicts (changed minds, evolving tastes)
- Factual conflicts (corrected information, updated details)
- Contextual conflicts (different situations, changing circumstances)

DIFFICULTY SCALING:
- Easy (1 conflict): Simple old vs new information
- Medium (2 conflicts): Multiple contradictions requiring prioritization
- Hard (3 conflicts): Complex web of conflicting information

OUTPUT FORMAT: Return ONLY valid JSON, no additional text, backticks, or formatting:
{{
    "scenario_description": "Description of the conflicts and resolution needed",
    "memories": [
        {{
            "content": "Memory content here",
            "days_ago": 15,
            "importance": 0.6,
            "conflict_type": "What type of conflict this represents"
        }}
    ],
    "query": "User's question that exposes the conflicts",
    "expected_response": "AI's response showing conflict resolution",
    "conflicts_identified": ["Conflict 1: Memory A vs Memory B about X"],
    "resolution_strategy": "How the AI should resolve conflicts (recency, importance, etc.)",
    "reasoning_explanation": "Why this tests adversarial reasoning"
}}

CRITICAL: Respond with ONLY the JSON object. Do not include any explanatory text, backticks, or formatting markers."""

        try:
            # Use structured output for reliable JSON generation - will auto-select appropriate schema
            data = await self.judge_service._call_gemini_structured(
                prompt, 
                SyntheticTestCaseSchema, 
                LLMProvider.GEMINI_FLASH
            )
            
            # Convert to our format
            memories = []
            for mem_data in data.memories:
                # Ensure days_ago is valid (≥ 1)
                days_ago = max(1, mem_data.days_ago)
                # Clamp importance to valid range
                importance = max(0.0, min(1.0, mem_data.importance))
                
                timestamp = datetime.now() - timedelta(days=days_ago)
                memory = Memory(
                    content=mem_data.content,
                    timestamp=timestamp,
                    importance=importance,
                    metadata={"conflict_type": getattr(mem_data, "conflict_type", "")}
                )
                memories.append(memory)
            
            return SyntheticTestCase(
                id=test_id,
                reasoning_type=ReasoningType.ADVERSARIAL,
                difficulty=difficulty,
                persona=persona,
                decision_path=decision_path,
                query=data.query,
                memories=memories,
                expected_response=data.expected_response,
                expected_memory_count=len(memories),
                generation_timestamp=datetime.now(),
                generator_model="gemini-2.5-flash",
                conflicting_info_count=conflicts,
                validation_notes=f"Conflicts: {'; '.join(getattr(data, 'conflicts_identified', []))}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to generate adversarial test case: {e}")
            raise
    
    async def _generate_commonsense(
        self, 
        test_id: str, 
        difficulty: DifficultyLevel, 
        persona: PersonaType,
        decision_path: ConversationDecisionPath
    ) -> SyntheticTestCase:
        """Generate commonsense reasoning test case (background knowledge integration)"""
        
        persona_style = self.persona_styles[persona]
        complexity = self._get_complexity_description(difficulty)
        
        prompt = f"""Generate a synthetic test case for COMMONSENSE reasoning evaluation.

REQUIREMENTS:
- Reasoning Type: Commonsense (background knowledge integration)
- Difficulty: {difficulty.value} ({complexity})
- Persona: {persona.value} ({persona_style})
- Decision Path: {decision_path.value}

TASK:
Create a realistic conversation scenario where:
1. User has 2-4 memories with incomplete or implicit information
2. User asks a query that requires common sense knowledge to complete the picture
3. Answer requires combining memories with general world knowledge
4. Expected response demonstrates reasoning beyond just stored memories

COMMONSENSE REQUIREMENTS:
- Memories should have gaps that require common sense to fill
- Query should require inference using general knowledge
- Answer should demonstrate logical reasoning with world knowledge
- Should feel natural and not artificially contrived

COMMONSENSE PATTERNS:
- Inferring unstated implications (if A then probably B)
- Filling knowledge gaps with reasonable assumptions
- Understanding context-dependent meanings
- Applying general principles to specific situations

DIFFICULTY SCALING:
- Easy: Simple logical implications and common knowledge
- Medium: Moderate inference with cultural/social knowledge
- Hard: Complex reasoning requiring specialized common sense

OUTPUT FORMAT: Return ONLY valid JSON, no additional text, backticks, or formatting:
{{
    "scenario_description": "Description of the commonsense reasoning required",
    "memories": [
        {{
            "content": "Memory content with implicit information",
            "days_ago": 20,
            "importance": 0.7,
            "implicit_info": "What common sense knowledge is needed"
        }}
    ],
    "query": "User's question requiring commonsense reasoning",
    "expected_response": "AI's response showing commonsense integration",
    "commonsense_required": ["Type 1: General knowledge about X", "Type 2: Logical inference about Y"],
    "reasoning_explanation": "Why this requires commonsense reasoning"
}}

CRITICAL: Respond with ONLY the JSON object. Do not include any explanatory text, backticks, or formatting markers."""

        try:
            # Use structured output for reliable JSON generation - will auto-select appropriate schema
            data = await self.judge_service._call_gemini_structured(
                prompt, 
                SyntheticTestCaseSchema, 
                LLMProvider.GEMINI_FLASH
            )
            
            # Convert to our format
            memories = []
            for mem_data in data.memories:
                # Ensure days_ago is valid (≥ 1)
                days_ago = max(1, mem_data.days_ago)
                # Clamp importance to valid range
                importance = max(0.0, min(1.0, mem_data.importance))
                
                timestamp = datetime.now() - timedelta(days=days_ago)
                memory = Memory(
                    content=mem_data.content,
                    timestamp=timestamp,
                    importance=importance,
                    metadata={"implicit_info": getattr(mem_data, "implicit_info", "")}
                )
                memories.append(memory)
            
            return SyntheticTestCase(
                id=test_id,
                reasoning_type=ReasoningType.COMMONSENSE,
                difficulty=difficulty,
                persona=persona,
                decision_path=decision_path,
                query=data.query,
                memories=memories,
                expected_response=data.expected_response,
                expected_memory_count=len(memories),
                generation_timestamp=datetime.now(),
                generator_model="gemini-2.5-flash",
                validation_notes=f"Commonsense required: {'; '.join(getattr(data, 'commonsense_required', []))}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to generate commonsense test case: {e}")
            raise
    
    def _get_complexity_description(self, difficulty: DifficultyLevel) -> str:
        """Get complexity description for prompts"""
        return {
            DifficultyLevel.EASY: "Simple, straightforward scenarios",
            DifficultyLevel.MEDIUM: "Moderate complexity with some nuance",
            DifficultyLevel.HARD: "Complex scenarios requiring sophisticated reasoning"
        }[difficulty]
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON response with error handling and cleaning"""
        try:
            # First, try direct parsing
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from response if it contains extra text
            try:
                # Look for JSON block between ```json and ``` or { and }
                import re
                
                # Pattern 1: JSON in code block
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # Pattern 2: Extract complete JSON object from response
                # Find the first opening brace and last closing brace
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx+1]
                    
                    # Clean up common JSON issues
                    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Remove trailing commas
                    json_str = re.sub(r'([^\\])\\([^"\\/bfnrtu])', r'\1\\\\\2', json_str)  # Fix unescaped backslashes
                    
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # Try to fix common quote issues
                        json_str = re.sub(r'([^\\])"([^",:}\]]+)"', r'\1"\2"', json_str)
                        return json.loads(json_str)
                
                # If still can't parse, create a valid fallback
                logger.warning(f"⚠️ Could not parse JSON, creating fallback structure")
                logger.warning(f"⚠️ Problematic response was: {response[:300]}...")
                
                # Try to extract key information from text
                query_match = re.search(r'"query":\s*"([^"]+)"', response)
                response_match = re.search(r'"expected_response":\s*"([^"]+)"', response)
                
                query = query_match.group(1) if query_match else "What can you tell me about my interests?"
                expected_resp = response_match.group(1) if response_match else "Based on your memories, you have various interests and activities."
                
                return {
                    "scenario_description": "Fallback scenario due to JSON parsing issues",
                    "memories": [
                        {"content": "User has shown interest in various activities", "days_ago": 7, "importance": 0.7},
                        {"content": "User enjoys learning new things", "days_ago": 14, "importance": 0.6}
                    ],
                    "query": query,
                    "expected_response": expected_resp,
                    "reasoning_explanation": "Fallback case generated due to JSON parsing issues"
                }
                
            except Exception as e:
                logger.error(f"❌ Complete JSON parsing failure: {e}")
                # Return a minimal valid structure
                return {
                    "scenario_description": "Error in generation",
                    "memories": [{"content": "Default memory content", "days_ago": 1, "importance": 0.5}],
                    "query": "What can you tell me?",
                    "expected_response": "I can help you with information based on your memories.",
                    "reasoning_explanation": "Error recovery case"
                }
    
    async def generate_batch(
        self,
        count: int = 10,
        reasoning_types: Optional[List[ReasoningType]] = None,
        difficulties: Optional[List[DifficultyLevel]] = None,
        personas: Optional[List[PersonaType]] = None
    ) -> List[SyntheticTestCase]:
        """Generate a batch of diverse test cases"""
        
        if not self.generation_enabled:
            raise ValueError("Synthetic generation disabled. Set SYNTHETIC_GENERATION_ENABLED=true")
        
        # Default to all types if not specified
        reasoning_types = reasoning_types or list(ReasoningType)
        difficulties = difficulties or list(DifficultyLevel)
        personas = personas or list(PersonaType)
        
        logger.info(f"🧬 Generating batch of {count} test cases")
        
        test_cases = []
        tasks = []
        
        for i in range(count):
            # Randomly select parameters for diversity
            reasoning_type = random.choice(reasoning_types)
            difficulty = random.choice(difficulties)
            persona = random.choice(personas)
            decision_path = random.choice(list(ConversationDecisionPath))
            
            task = self.generate_test_case(reasoning_type, difficulty, persona, decision_path)
            tasks.append(task)
        
        # Generate in parallel for efficiency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Failed to generate test case {i}: {result}")
            else:
                test_cases.append(result)
        
        logger.info(f"✅ Generated {len(test_cases)} / {count} test cases successfully")
        return test_cases


# Global service instance
_synthetic_generator = None

def get_synthetic_generator() -> SyntheticDataGeneratorService:
    """Get global synthetic data generator instance"""
    global _synthetic_generator
    if _synthetic_generator is None:
        _synthetic_generator = SyntheticDataGeneratorService()
    return _synthetic_generator


# Convenience functions
async def generate_single_test_case(
    reasoning_type: ReasoningType,
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
    persona: PersonaType = PersonaType.CASUAL
) -> SyntheticTestCase:
    """Generate a single test case (convenience function)"""
    generator = get_synthetic_generator()
    return await generator.generate_test_case(reasoning_type, difficulty, persona)


async def generate_test_batch(
    count: int = 10,
    reasoning_types: Optional[List[ReasoningType]] = None
) -> List[SyntheticTestCase]:
    """Generate a batch of test cases (convenience function)"""
    generator = get_synthetic_generator()
    return await generator.generate_batch(count, reasoning_types)


async def generate_balanced_dataset(size: int = 50) -> List[SyntheticTestCase]:
    """Generate a balanced dataset across all reasoning types and difficulties"""
    generator = get_synthetic_generator()
    
    # Calculate distribution
    reasoning_types = list(ReasoningType)
    difficulties = list(DifficultyLevel)
    personas = list(PersonaType)
    
    per_type = size // len(reasoning_types)
    remainder = size % len(reasoning_types)
    
    test_cases = []
    
    for i, reasoning_type in enumerate(reasoning_types):
        type_count = per_type + (1 if i < remainder else 0)
        
        type_cases = await generator.generate_batch(
            count=type_count,
            reasoning_types=[reasoning_type],
            difficulties=difficulties,
            personas=personas
        )
        test_cases.extend(type_cases)
    
    # Shuffle for randomization
    random.shuffle(test_cases)
    
    logger.info(f"✅ Generated balanced dataset: {len(test_cases)} test cases")
    return test_cases