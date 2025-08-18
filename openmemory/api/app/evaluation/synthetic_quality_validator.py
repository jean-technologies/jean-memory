"""
Synthetic Test Data Quality Validator
===================================

Quality validation system that uses Task 2's LLM judge to evaluate
generated synthetic test cases before they are used in evaluation.

Ensures generated test cases meet quality thresholds and are suitable
for measuring Jean Memory performance.

Part of Task 3: Synthetic Test Data Generator
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import Task 1-2 infrastructure
from .llm_judge import (
    LLMJudgeService, 
    ReasoningType, 
    LLMProvider,
    evaluate_single_response
)
from .consensus_judge import (
    ConsensusJudgeService,
    ConsensusMode,
    evaluate_with_consensus
)
from .synthetic_data_generator import (
    SyntheticTestCase, 
    DifficultyLevel,
    PersonaType,
    ConversationDecisionPath
)

logger = logging.getLogger(__name__)


@dataclass
class QualityValidationResult:
    """Result of quality validation for a synthetic test case"""
    test_case_id: str
    passed: bool
    overall_score: float
    
    # Individual quality dimensions
    coherence_score: float      # Does the scenario make sense?
    realism_score: float        # Is this a realistic conversation?
    difficulty_score: float     # Does it match the intended difficulty?
    reasoning_score: float      # Does it test the target reasoning type?
    
    # Validation details
    validation_timestamp: datetime
    validator_model: str
    feedback: str
    issues_found: List[str]
    
    # Quality thresholds used
    min_overall_score: float
    consensus_enabled: bool
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "test_case_id": self.test_case_id,
            "passed": self.passed,
            "overall_score": self.overall_score,
            "coherence_score": self.coherence_score,
            "realism_score": self.realism_score,
            "difficulty_score": self.difficulty_score,
            "reasoning_score": self.reasoning_score,
            "validation_timestamp": self.validation_timestamp.isoformat(),
            "validator_model": self.validator_model,
            "feedback": self.feedback,
            "issues_found": self.issues_found,
            "min_overall_score": self.min_overall_score,
            "consensus_enabled": self.consensus_enabled
        }


class SyntheticQualityValidator:
    """
    Quality validation service for synthetic test cases.
    Uses Task 2's LLM judge infrastructure for evaluation.
    """
    
    def __init__(self):
        """Initialize with quality validation settings"""
        self.judge_service = LLMJudgeService()
        self.consensus_service = ConsensusJudgeService()
        
        # Quality thresholds from environment
        import os
        self.min_overall_score = float(os.getenv("SYNTHETIC_MIN_OVERALL_SCORE", "7.0"))
        self.min_coherence_score = float(os.getenv("SYNTHETIC_MIN_COHERENCE_SCORE", "8.0"))
        self.min_realism_score = float(os.getenv("SYNTHETIC_MIN_REALISM_SCORE", "7.5"))
        self.min_difficulty_score = float(os.getenv("SYNTHETIC_MIN_DIFFICULTY_SCORE", "6.5"))
        self.min_reasoning_score = float(os.getenv("SYNTHETIC_MIN_REASONING_SCORE", "8.0"))
        
        # Use consensus validation for higher quality
        self.use_consensus = os.getenv("SYNTHETIC_USE_CONSENSUS_VALIDATION", "true").lower() == "true"
        self.consensus_mode = ConsensusMode(os.getenv("SYNTHETIC_CONSENSUS_MODE", "dual"))
        
        logger.info(f"🔍 Synthetic Quality Validator initialized")
        logger.info(f"   Min overall score: {self.min_overall_score}")
        logger.info(f"   Use consensus: {self.use_consensus} ({self.consensus_mode.value if self.use_consensus else 'N/A'})")
    
    async def validate_test_case(self, test_case: SyntheticTestCase) -> QualityValidationResult:
        """Validate a single synthetic test case for quality"""
        
        logger.info(f"🔍 Validating test case {test_case.id[:8]} ({test_case.reasoning_type.value})")
        
        try:
            # Create validation prompt
            validation_prompt = self._create_validation_prompt(test_case)
            
            # Use consensus validation if enabled, otherwise single judge
            if self.use_consensus:
                validation_response = await self._validate_with_consensus(validation_prompt, test_case)
            else:
                validation_response = await self._validate_with_single_judge(validation_prompt, test_case)
            
            # Parse validation response
            validation_data = json.loads(validation_response)
            
            # Calculate overall score and determine pass/fail
            overall_score = self._calculate_overall_score(validation_data)
            passed = self._determine_pass_fail(validation_data, overall_score)
            
            result = QualityValidationResult(
                test_case_id=test_case.id,
                passed=passed,
                overall_score=overall_score,
                coherence_score=validation_data["coherence_score"],
                realism_score=validation_data["realism_score"],
                difficulty_score=validation_data["difficulty_score"],
                reasoning_score=validation_data["reasoning_score"],
                validation_timestamp=datetime.now(),
                validator_model=validation_data.get("model_used", "unknown"),
                feedback=validation_data["feedback"],
                issues_found=validation_data.get("issues_found", []),
                min_overall_score=self.min_overall_score,
                consensus_enabled=self.use_consensus
            )
            
            # Update test case with validation results
            test_case.quality_score = overall_score
            test_case.validation_notes = result.feedback
            
            logger.info(f"{'✅' if passed else '❌'} Test case {test_case.id[:8]} - Score: {overall_score:.1f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to validate test case {test_case.id[:8]}: {e}")
            # Return failed validation
            return QualityValidationResult(
                test_case_id=test_case.id,
                passed=False,
                overall_score=0.0,
                coherence_score=0.0,
                realism_score=0.0,
                difficulty_score=0.0,
                reasoning_score=0.0,
                validation_timestamp=datetime.now(),
                validator_model="error",
                feedback=f"Validation failed: {str(e)}",
                issues_found=[f"Validation error: {str(e)}"],
                min_overall_score=self.min_overall_score,
                consensus_enabled=self.use_consensus
            )
    
    def _create_validation_prompt(self, test_case: SyntheticTestCase) -> str:
        """Create validation prompt for the test case"""
        
        memories_text = "\n".join([f"- {mem.content} (timestamp: {mem.timestamp})" for mem in test_case.memories])
        
        prompt = f"""You are a quality validator for synthetic test data used in AI memory evaluation.

TASK: Evaluate the quality of this synthetic test case across multiple dimensions.

TEST CASE DETAILS:
- ID: {test_case.id}
- Reasoning Type: {test_case.reasoning_type.value}
- Difficulty: {test_case.difficulty.value}
- Persona: {test_case.persona.value}
- Decision Path: {test_case.decision_path.value}

MEMORIES:
{memories_text}

QUERY: {test_case.query}

EXPECTED RESPONSE: {test_case.expected_response}

EVALUATION DIMENSIONS:

1. COHERENCE (0-10): Do the memories, query, and expected response form a coherent scenario?
   - Are memories logically consistent with each other?
   - Does the query make sense given the memories?
   - Is the expected response appropriate for the query and memories?

2. REALISM (0-10): How realistic is this conversation scenario?
   - Would a real user have these memories?
   - Is the query something a real user would ask?
   - Does it feel natural or artificially constructed?

3. DIFFICULTY (0-10): Does the scenario match the intended difficulty level ({test_case.difficulty.value})?
   - Easy: Simple, straightforward reasoning
   - Medium: Moderate complexity with some nuance
   - Hard: Complex reasoning requiring sophisticated analysis

4. REASONING TYPE (0-10): Does this effectively test {test_case.reasoning_type.value} reasoning?
   - Single-hop: Direct fact retrieval from one memory
   - Multi-hop: Connecting information across multiple memories
   - Temporal: Time-based reasoning and chronological understanding
   - Adversarial: Handling conflicting or contradictory information
   - Commonsense: Integration of general world knowledge

SPECIAL REQUIREMENTS FOR {test_case.reasoning_type.value.upper()}:
{self._get_reasoning_type_requirements(test_case.reasoning_type)}

OUTPUT FORMAT (JSON):
{{
    "coherence_score": 8.5,
    "coherence_explanation": "Detailed explanation of coherence assessment",
    "realism_score": 7.0,
    "realism_explanation": "Detailed explanation of realism assessment",
    "difficulty_score": 8.0,
    "difficulty_explanation": "Detailed explanation of difficulty assessment",
    "reasoning_score": 9.0,
    "reasoning_explanation": "Detailed explanation of reasoning type assessment",
    "feedback": "Overall quality assessment and specific suggestions",
    "issues_found": ["Issue 1", "Issue 2"],
    "strengths": ["Strength 1", "Strength 2"],
    "model_used": "validator-model-name"
}}

Provide honest, detailed evaluation. Be critical but constructive."""

        return prompt
    
    def _get_reasoning_type_requirements(self, reasoning_type: ReasoningType) -> str:
        """Get specific requirements for each reasoning type"""
        requirements = {
            ReasoningType.SINGLE_HOP: """
- Must require exactly ONE memory lookup
- Query should be answerable from a single memory
- No cross-memory synthesis required
- Direct fact retrieval only""",
            
            ReasoningType.MULTI_HOP: """
- Must require connecting 2+ memories
- No single memory contains the complete answer
- Clear logical chain between memories
- Demonstrates synthesis across information sources""",
            
            ReasoningType.TEMPORAL: """
- Must involve time-based reasoning
- Memories should have meaningful temporal relationships
- Query requires understanding of timing/sequence
- Response should demonstrate temporal awareness""",
            
            ReasoningType.ADVERSARIAL: """
- Must contain conflicting information
- Query should expose the conflicts
- Response should handle conflicts intelligently
- Tests robustness against contradictions""",
            
            ReasoningType.COMMONSENSE: """
- Must require general world knowledge
- Memories alone insufficient for complete answer
- Query requires inference beyond stored facts
- Tests integration of background knowledge"""
        }
        return requirements.get(reasoning_type, "")
    
    async def _validate_with_consensus(self, prompt: str, test_case: SyntheticTestCase) -> str:
        """Validate using consensus judging for higher reliability"""
        try:
            # Create a mock evaluation context for consensus validation
            mock_memories = [{"content": mem.content} for mem in test_case.memories]
            
            result = await evaluate_with_consensus(
                query=test_case.query,
                memories=mock_memories,
                response=test_case.expected_response,
                reasoning_type=test_case.reasoning_type,
                consensus_mode=self.consensus_mode
            )
            
            # Convert consensus result to validation format
            # Scale scores from 0-10 to 0-10 (they should already be in this range)
            validation_response = {
                "coherence_score": result.consistency if hasattr(result, 'consistency') else result.overall,
                "coherence_explanation": f"Consensus coherence evaluation based on consistency: {result.explanation[:200]}",
                "realism_score": result.relevance if hasattr(result, 'relevance') else result.overall,
                "realism_explanation": "Consensus realism assessment based on relevance scoring",
                "difficulty_score": result.reasoning_quality if hasattr(result, 'reasoning_quality') else result.overall,
                "difficulty_explanation": "Consensus difficulty assessment based on reasoning quality",
                "reasoning_score": result.overall,
                "reasoning_explanation": f"Consensus reasoning type assessment: {result.explanation[:200]}",
                "feedback": result.explanation,
                "issues_found": [f"Outlier: {p.value}" for p in getattr(result, 'outliers_detected', [])],
                "strengths": ["Consensus validation completed", f"Used {len(getattr(result, 'judges_used', []))} judges"],
                "model_used": f"consensus-{self.consensus_mode.value}"
            }
            
            return json.dumps(validation_response)
            
        except Exception as e:
            logger.warning(f"⚠️ Consensus validation failed, falling back to single judge: {e}")
            return await self._validate_with_single_judge(prompt, test_case)
    
    async def _validate_with_single_judge(self, prompt: str, test_case: SyntheticTestCase) -> str:
        """Validate using single LLM judge"""
        try:
            # Use Gemini Pro for quality validation (higher quality than Flash)
            response = await self.judge_service._call_gemini(prompt, LLMProvider.GEMINI_PRO)
            return response
        except Exception as e:
            logger.warning(f"⚠️ Gemini Pro validation failed, trying OpenAI: {e}")
            try:
                response = await self.judge_service._call_openai(prompt, LLMProvider.OPENAI_GPT5)
                return response
            except Exception as e2:
                logger.error(f"❌ All validation providers failed: {e2}")
                raise
    
    def _calculate_overall_score(self, validation_data: Dict) -> float:
        """Calculate weighted overall score"""
        weights = {
            "coherence_score": 0.3,
            "realism_score": 0.25,
            "difficulty_score": 0.2,
            "reasoning_score": 0.25
        }
        
        overall = sum(
            validation_data[key] * weight 
            for key, weight in weights.items()
            if key in validation_data
        )
        
        return round(overall, 2)
    
    def _determine_pass_fail(self, validation_data: Dict, overall_score: float) -> bool:
        """Determine if test case passes quality thresholds"""
        if overall_score < self.min_overall_score:
            return False
        
        # Check individual thresholds
        thresholds = {
            "coherence_score": self.min_coherence_score,
            "realism_score": self.min_realism_score,
            "difficulty_score": self.min_difficulty_score,
            "reasoning_score": self.min_reasoning_score
        }
        
        for key, min_score in thresholds.items():
            if validation_data.get(key, 0) < min_score:
                return False
        
        return True
    
    async def validate_batch(
        self, 
        test_cases: List[SyntheticTestCase],
        fail_fast: bool = False
    ) -> Tuple[List[SyntheticTestCase], List[QualityValidationResult]]:
        """
        Validate a batch of test cases.
        Returns: (passed_test_cases, all_validation_results)
        """
        
        logger.info(f"🔍 Validating batch of {len(test_cases)} test cases")
        
        # Validate in parallel for efficiency
        validation_tasks = [self.validate_test_case(tc) for tc in test_cases]
        validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        passed_test_cases = []
        all_results = []
        
        for i, result in enumerate(validation_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Validation {i} failed: {result}")
                continue
            
            all_results.append(result)
            
            if result.passed:
                passed_test_cases.append(test_cases[i])
            elif fail_fast:
                logger.warning(f"⚠️ Fail-fast enabled, stopping validation at failed case {i}")
                break
        
        pass_rate = len(passed_test_cases) / len(test_cases) * 100
        logger.info(f"✅ Validation complete: {len(passed_test_cases)}/{len(test_cases)} passed ({pass_rate:.1f}%)")
        
        return passed_test_cases, all_results
    
    async def validate_and_regenerate(
        self,
        test_cases: List[SyntheticTestCase],
        max_regeneration_attempts: int = 2
    ) -> List[SyntheticTestCase]:
        """
        Validate test cases and regenerate failed ones up to max attempts.
        Returns only test cases that pass validation.
        """
        from .synthetic_data_generator import get_synthetic_generator
        
        validated_cases = []
        generator = get_synthetic_generator()
        
        for test_case in test_cases:
            current_case = test_case
            attempts = 0
            
            while attempts <= max_regeneration_attempts:
                validation_result = await self.validate_test_case(current_case)
                
                if validation_result.passed:
                    validated_cases.append(current_case)
                    break
                
                if attempts < max_regeneration_attempts:
                    logger.info(f"🔄 Regenerating failed test case {current_case.id[:8]} (attempt {attempts + 1})")
                    try:
                        current_case = await generator.generate_test_case(
                            current_case.reasoning_type,
                            current_case.difficulty,
                            current_case.persona,
                            current_case.decision_path
                        )
                        attempts += 1
                    except Exception as e:
                        logger.error(f"❌ Regeneration failed: {e}")
                        break
                else:
                    logger.warning(f"⚠️ Test case {current_case.id[:8]} failed validation after {max_regeneration_attempts} regeneration attempts")
                    break
        
        logger.info(f"✅ Validation and regeneration complete: {len(validated_cases)}/{len(test_cases)} test cases passed")
        return validated_cases


# Global validator instance
_quality_validator = None

def get_quality_validator() -> SyntheticQualityValidator:
    """Get global quality validator instance"""
    global _quality_validator
    if _quality_validator is None:
        _quality_validator = SyntheticQualityValidator()
    return _quality_validator


# Convenience functions
async def validate_single_test_case(test_case: SyntheticTestCase) -> QualityValidationResult:
    """Validate a single test case (convenience function)"""
    validator = get_quality_validator()
    return await validator.validate_test_case(test_case)


async def validate_test_batch(test_cases: List[SyntheticTestCase]) -> Tuple[List[SyntheticTestCase], List[QualityValidationResult]]:
    """Validate a batch of test cases (convenience function)"""
    validator = get_quality_validator()
    return await validator.validate_batch(test_cases)


async def generate_and_validate_batch(
    count: int = 10,
    reasoning_types: Optional[List[ReasoningType]] = None,
    max_regeneration_attempts: int = 2
) -> List[SyntheticTestCase]:
    """Generate and validate a batch of test cases with automatic regeneration"""
    from .synthetic_data_generator import get_synthetic_generator
    
    generator = get_synthetic_generator()
    validator = get_quality_validator()
    
    # Generate initial batch
    test_cases = await generator.generate_batch(count, reasoning_types)
    
    # Validate and regenerate as needed
    validated_cases = await validator.validate_and_regenerate(test_cases, max_regeneration_attempts)
    
    return validated_cases