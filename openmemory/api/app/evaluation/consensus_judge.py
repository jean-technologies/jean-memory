"""
Consensus LLM Judge System
=========================

Implements multi-LLM consensus judging with parallel execution, outlier detection,
and intelligent fallback to meet 100% FRD compliance for Task 2.

Key Features:
- Parallel execution of multiple LLM judges
- Configurable consensus modes (single, dual, triple)
- Outlier detection and handling
- Consensus score averaging across all dimensions
- Intelligent fallback chains
- Enhanced metadata storage with individual judge scores
"""

import asyncio
import logging
import os
import statistics
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .llm_judge import (
    LLMJudgeService,
    EvaluationContext,
    JudgeScore,
    ReasoningType,
    LLMProvider
)

logger = logging.getLogger(__name__)


class ConsensusMode(Enum):
    """Consensus judging modes"""
    SINGLE = "single"       # Single judge (original mode)
    DUAL = "dual"          # 2-judge consensus  
    TRIPLE = "triple"      # 3-judge consensus


@dataclass
class IndividualJudgeResult:
    """Result from a single judge in consensus evaluation"""
    provider: LLMProvider
    score: JudgeScore
    success: bool
    error: Optional[str] = None
    latency_ms: float = 0.0


@dataclass
class ConsensusScore:
    """Consensus evaluation result combining multiple judge scores"""
    # Consensus scores (averaged)
    relevance: float
    completeness: float
    reasoning_quality: float
    consistency: float
    overall: float
    
    # Consensus metadata
    consensus_mode: ConsensusMode
    judges_used: List[LLMProvider]
    individual_results: List[IndividualJudgeResult]
    outliers_detected: List[LLMProvider]
    
    # Combined explanation
    consensus_explanation: str
    individual_explanations: List[str]
    
    # Performance metrics
    total_latency_ms: float
    consensus_variance: float  # Measure of judge agreement
    reliability_score: float   # Higher = more reliable consensus
    
    # Original context
    reasoning_type: ReasoningType
    timestamp: datetime
    
    # Fallback information
    requested_judges: int
    actual_judges: int
    fallback_occurred: bool


class ConsensusConfiguration:
    """Configuration for consensus judging system"""
    
    @staticmethod
    def get_consensus_config() -> Dict[str, Any]:
        """Get consensus configuration from environment variables"""
        return {
            # Core consensus settings
            "mode": ConsensusMode(os.getenv("CONSENSUS_MODE", "single")),
            "enabled": os.getenv("CONSENSUS_ENABLED", "false").lower() in ("true", "1", "yes", "on"),
            
            # Provider priority (primary, secondary, tertiary)
            "primary_provider": os.getenv("CONSENSUS_PRIMARY", "auto"),  # auto, gemini, openai
            "secondary_provider": os.getenv("CONSENSUS_SECONDARY", "auto"),
            "tertiary_provider": os.getenv("CONSENSUS_TERTIARY", "auto"),
            
            # Performance settings
            "parallel_timeout": int(os.getenv("CONSENSUS_TIMEOUT", "10")),  # seconds
            "individual_timeout": int(os.getenv("CONSENSUS_JUDGE_TIMEOUT", "5")),  # per judge
            
            # Outlier detection
            "outlier_threshold": float(os.getenv("CONSENSUS_OUTLIER_THRESHOLD", "2.0")),  # std devs
            "outlier_handling": os.getenv("CONSENSUS_OUTLIER_HANDLING", "exclude"),  # exclude, include, weight
            
            # Fallback behavior
            "min_judges": int(os.getenv("CONSENSUS_MIN_JUDGES", "1")),
            "allow_fallback": os.getenv("CONSENSUS_ALLOW_FALLBACK", "true").lower() in ("true", "1", "yes", "on"),
            
            # Cost optimization
            "cost_mode": os.getenv("CONSENSUS_COST_MODE", "balanced"),  # fast, balanced, thorough
            "context_based": os.getenv("CONSENSUS_CONTEXT_BASED", "false").lower() in ("true", "1", "yes", "on"),
        }
    
    @staticmethod
    def get_providers_for_mode(mode: ConsensusMode, config: Dict[str, Any]) -> List[LLMProvider]:
        """Get ordered list of providers for consensus mode"""
        available_providers = []
        
        # Get available providers from judge service
        try:
            from .llm_judge import get_judge_service
            judge_service = get_judge_service()
            
            if judge_service.openai_client:
                available_providers.extend([LLMProvider.OPENAI_GPT5, LLMProvider.OPENAI_GPT4O])
            if judge_service.gemini_model:
                available_providers.extend([LLMProvider.GEMINI_FLASH, LLMProvider.GEMINI_PRO])
                
        except Exception as e:
            logger.warning(f"Could not determine available providers: {e}")
            return [LLMProvider.GEMINI_FLASH]  # Safe fallback
        
        # Apply cost optimization
        if config["cost_mode"] == "fast":
            # Prefer faster/cheaper models
            priority_order = [LLMProvider.GEMINI_FLASH, LLMProvider.OPENAI_GPT4O, 
                            LLMProvider.GEMINI_PRO, LLMProvider.OPENAI_GPT5]
        elif config["cost_mode"] == "thorough":
            # Prefer higher quality models
            priority_order = [LLMProvider.OPENAI_GPT5, LLMProvider.GEMINI_PRO,
                            LLMProvider.OPENAI_GPT4O, LLMProvider.GEMINI_FLASH]
        else:  # balanced
            # Mix of speed and quality
            priority_order = [LLMProvider.OPENAI_GPT5, LLMProvider.GEMINI_FLASH,
                            LLMProvider.GEMINI_PRO, LLMProvider.OPENAI_GPT4O]
        
        # Filter to available providers and apply mode requirements
        selected_providers = []
        for provider in priority_order:
            if provider in available_providers:
                selected_providers.append(provider)
                if len(selected_providers) >= mode_to_count(mode):
                    break
        
        return selected_providers[:mode_to_count(mode)]


def mode_to_count(mode: ConsensusMode) -> int:
    """Convert consensus mode to number of judges"""
    return {
        ConsensusMode.SINGLE: 1,
        ConsensusMode.DUAL: 2,
        ConsensusMode.TRIPLE: 3
    }[mode]


class ConsensusJudgeService:
    """
    Enhanced LLM Judge service with consensus evaluation capabilities.
    
    Supports parallel execution of multiple judges with intelligent fallback,
    outlier detection, and consensus score calculation.
    """
    
    def __init__(self):
        self.base_judge = LLMJudgeService()
        self.config = ConsensusConfiguration.get_consensus_config()
        
        # Validate configuration
        if self.config["mode"] != ConsensusMode.SINGLE and not self.config["enabled"]:
            logger.warning("Consensus mode specified but not enabled - falling back to single judge")
            self.config["mode"] = ConsensusMode.SINGLE
    
    async def evaluate_context(
        self,
        context: EvaluationContext,
        consensus_mode: Optional[ConsensusMode] = None
    ) -> ConsensusScore:
        """
        Evaluate context using consensus judging.
        
        Args:
            context: Evaluation context for judging
            consensus_mode: Override default consensus mode
            
        Returns:
            Consensus score with individual judge results and metadata
        """
        mode = consensus_mode or self.config["mode"]
        start_time = time.perf_counter()
        
        logger.info(f"🎯 Starting consensus evaluation (mode: {mode.value})")
        
        try:
            # Get providers for this consensus mode
            providers = ConsensusConfiguration.get_providers_for_mode(mode, self.config)
            
            if not providers:
                raise ValueError("No providers available for consensus judging")
            
            # Execute parallel judging
            individual_results = await self._execute_parallel_judging(context, providers)
            
            # Process consensus results
            consensus_score = await self._process_consensus_results(
                individual_results, mode, context, start_time
            )
            
            logger.info(f"✅ Consensus evaluation complete: {consensus_score.overall:.1f}/10 "
                       f"({consensus_score.actual_judges}/{consensus_score.requested_judges} judges)")
            
            return consensus_score
            
        except Exception as e:
            logger.error(f"❌ Consensus evaluation failed: {e}")
            # Fallback to single judge if consensus fails
            return await self._fallback_to_single_judge(context, mode, start_time, str(e))
    
    async def _execute_parallel_judging(
        self,
        context: EvaluationContext,
        providers: List[LLMProvider]
    ) -> List[IndividualJudgeResult]:
        """Execute multiple judges in parallel with timeout handling"""
        
        async def evaluate_single_judge(provider: LLMProvider) -> IndividualJudgeResult:
            """Evaluate context with a single judge"""
            judge_start = time.perf_counter()
            
            try:
                # Set individual judge timeout
                timeout = self.config["individual_timeout"]
                score = await asyncio.wait_for(
                    self.base_judge.evaluate_context(context, provider),
                    timeout=timeout
                )
                
                latency = (time.perf_counter() - judge_start) * 1000
                
                return IndividualJudgeResult(
                    provider=provider,
                    score=score,
                    success=True,
                    latency_ms=latency
                )
                
            except asyncio.TimeoutError:
                latency = (time.perf_counter() - judge_start) * 1000
                logger.warning(f"⏰ Judge {provider.value} timed out after {timeout}s")
                return IndividualJudgeResult(
                    provider=provider,
                    score=None,
                    success=False,
                    error=f"Timeout after {timeout}s",
                    latency_ms=latency
                )
                
            except Exception as e:
                latency = (time.perf_counter() - judge_start) * 1000
                logger.warning(f"❌ Judge {provider.value} failed: {e}")
                return IndividualJudgeResult(
                    provider=provider,
                    score=None,
                    success=False,
                    error=str(e),
                    latency_ms=latency
                )
        
        # Execute all judges in parallel
        logger.info(f"🚀 Executing {len(providers)} judges in parallel: {[p.value for p in providers]}")
        
        try:
            # Apply overall timeout to parallel execution
            results = await asyncio.wait_for(
                asyncio.gather(*[evaluate_single_judge(p) for p in providers]),
                timeout=self.config["parallel_timeout"]
            )
            
            # Log individual results
            for result in results:
                if result.success:
                    logger.info(f"✅ {result.provider.value}: {result.score.overall:.1f}/10 ({result.latency_ms:.0f}ms)")
                else:
                    logger.warning(f"❌ {result.provider.value}: {result.error}")
            
            return results
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Parallel judging timed out after {self.config['parallel_timeout']}s")
            # Return partial results if available
            return []
    
    async def _process_consensus_results(
        self,
        individual_results: List[IndividualJudgeResult],
        mode: ConsensusMode,
        context: EvaluationContext,
        start_time: float
    ) -> ConsensusScore:
        """Process individual judge results into consensus score"""
        
        # Filter successful results
        successful_results = [r for r in individual_results if r.success and r.score]
        
        if not successful_results:
            raise ValueError("No successful judge evaluations available")
        
        # Check minimum judges requirement
        min_judges = self.config["min_judges"]
        if len(successful_results) < min_judges:
            if self.config["allow_fallback"]:
                logger.warning(f"Only {len(successful_results)} judges succeeded, minimum is {min_judges} - proceeding with available judges")
            else:
                raise ValueError(f"Insufficient judges: {len(successful_results)} < {min_judges}")
        
        # Detect and handle outliers
        filtered_results, outliers = self._detect_and_handle_outliers(successful_results)
        
        # Calculate consensus scores
        consensus_scores = self._calculate_consensus_scores(filtered_results)
        
        # Calculate reliability metrics
        variance = self._calculate_consensus_variance(filtered_results)
        reliability = self._calculate_reliability_score(filtered_results, variance)
        
        # Synthesize explanations
        consensus_explanation = self._synthesize_explanations(filtered_results)
        
        # Build consensus score object
        total_latency = (time.perf_counter() - start_time) * 1000
        
        return ConsensusScore(
            # Consensus scores
            relevance=consensus_scores["relevance"],
            completeness=consensus_scores["completeness"],
            reasoning_quality=consensus_scores["reasoning_quality"],
            consistency=consensus_scores["consistency"],
            overall=consensus_scores["overall"],
            
            # Metadata
            consensus_mode=mode,
            judges_used=[r.provider for r in filtered_results],
            individual_results=individual_results,
            outliers_detected=outliers,
            
            # Explanations
            consensus_explanation=consensus_explanation,
            individual_explanations=[r.score.explanation for r in filtered_results],
            
            # Performance
            total_latency_ms=total_latency,
            consensus_variance=variance,
            reliability_score=reliability,
            
            # Context
            reasoning_type=context.reasoning_type or ReasoningType.SINGLE_HOP,
            timestamp=datetime.utcnow(),
            
            # Fallback info
            requested_judges=mode_to_count(mode),
            actual_judges=len(filtered_results),
            fallback_occurred=len(filtered_results) < mode_to_count(mode)
        )
    
    def _detect_and_handle_outliers(
        self,
        results: List[IndividualJudgeResult]
    ) -> Tuple[List[IndividualJudgeResult], List[LLMProvider]]:
        """Detect and handle outlier judges based on score variance"""
        
        if len(results) < 3:  # Need at least 3 judges for outlier detection
            return results, []
        
        # Extract overall scores for outlier detection
        overall_scores = [r.score.overall for r in results]
        
        # Calculate mean and standard deviation
        mean_score = statistics.mean(overall_scores)
        std_dev = statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0
        
        # Identify outliers (scores beyond threshold standard deviations)
        threshold = self.config["outlier_threshold"]
        outliers = []
        filtered_results = []
        
        for result in results:
            z_score = abs(result.score.overall - mean_score) / std_dev if std_dev > 0 else 0
            
            if z_score > threshold:
                outliers.append(result.provider)
                logger.warning(f"🔍 Outlier detected: {result.provider.value} "
                             f"(score: {result.score.overall:.1f}, z-score: {z_score:.2f})")
                
                # Handle outlier based on configuration
                if self.config["outlier_handling"] == "include":
                    filtered_results.append(result)
                # else: exclude (default behavior)
            else:
                filtered_results.append(result)
        
        # Ensure we don't filter out all results
        if not filtered_results and results:
            logger.warning("All judges detected as outliers - including all results")
            filtered_results = results
            outliers = []
        
        if outliers:
            logger.info(f"🚫 Excluded {len(outliers)} outlier judges: {[p.value for p in outliers]}")
        
        return filtered_results, outliers
    
    def _calculate_consensus_scores(
        self,
        results: List[IndividualJudgeResult]
    ) -> Dict[str, float]:
        """Calculate consensus scores by averaging across all judges"""
        
        if not results:
            raise ValueError("No results to calculate consensus from")
        
        # Extract scores from all judges
        relevance_scores = [r.score.relevance for r in results]
        completeness_scores = [r.score.completeness for r in results]
        reasoning_scores = [r.score.reasoning_quality for r in results]
        consistency_scores = [r.score.consistency for r in results if r.score.consistency > 0]
        
        # Calculate averages
        consensus = {
            "relevance": statistics.mean(relevance_scores),
            "completeness": statistics.mean(completeness_scores),
            "reasoning_quality": statistics.mean(reasoning_scores),
            "consistency": statistics.mean(consistency_scores) if consistency_scores else 0.0
        }
        
        # Calculate weighted overall score using same weights as base judge
        weights = self.base_judge.score_weights.copy()
        if consensus["consistency"] == 0.0:
            weights.pop("consistency")
            total_weight = sum(weights.values())
            weights = {k: v/total_weight for k, v in weights.items()}
        
        consensus["overall"] = (
            consensus["relevance"] * weights["relevance"] +
            consensus["completeness"] * weights["completeness"] +
            consensus["reasoning_quality"] * weights["reasoning"] +
            consensus["consistency"] * weights.get("consistency", 0)
        )
        
        return consensus
    
    def _calculate_consensus_variance(self, results: List[IndividualJudgeResult]) -> float:
        """Calculate variance in judge scores (lower = more agreement)"""
        if len(results) < 2:
            return 0.0
        
        overall_scores = [r.score.overall for r in results]
        return statistics.variance(overall_scores)
    
    def _calculate_reliability_score(
        self,
        results: List[IndividualJudgeResult],
        variance: float
    ) -> float:
        """Calculate reliability score (0-1, higher = more reliable)"""
        if len(results) < 2:
            return 1.0  # Single judge is perfectly "reliable" to itself
        
        # Reliability inversely related to variance
        # High variance (>4) = low reliability, Low variance (<1) = high reliability
        max_variance = 4.0  # Reasonable maximum for 0-10 scale
        reliability = max(0.0, 1.0 - (variance / max_variance))
        
        # Bonus for more judges (up to 3)
        judge_bonus = min(len(results) - 1, 2) * 0.1
        
        return min(1.0, reliability + judge_bonus)
    
    def _synthesize_explanations(self, results: List[IndividualJudgeResult]) -> str:
        """Synthesize consensus explanation from individual judge explanations"""
        if not results:
            return "No judge explanations available."
        
        if len(results) == 1:
            return results[0].score.explanation
        
        # Extract key themes from explanations
        explanations = [r.score.explanation for r in results]
        providers = [r.provider.value for r in results]
        
        # Build consensus explanation
        consensus_parts = []
        
        # Header with consensus info
        avg_score = statistics.mean([r.score.overall for r in results])
        consensus_parts.append(f"Consensus Score: {avg_score:.1f}/10 (from {len(results)} judges)")
        
        # Individual judge summaries
        consensus_parts.append("\nJudge Perspectives:")
        for i, (provider, explanation) in enumerate(zip(providers, explanations)):
            score = results[i].score.overall
            # Extract first sentence or 100 chars as summary
            summary = explanation.split('.')[0][:100] + "..." if len(explanation) > 100 else explanation.split('.')[0]
            consensus_parts.append(f"• {provider} ({score:.1f}/10): {summary}")
        
        # Common themes (simplified - could be enhanced with NLP)
        consensus_parts.append(f"\nConsensus: The judges {"agree" if self._calculate_consensus_variance(results) < 1.0 else "show mixed opinions"} on this evaluation.")
        
        return "\n".join(consensus_parts)
    
    async def _fallback_to_single_judge(
        self,
        context: EvaluationContext,
        requested_mode: ConsensusMode,
        start_time: float,
        error_msg: str
    ) -> ConsensusScore:
        """Fallback to single judge when consensus fails"""
        logger.warning(f"🔄 Falling back to single judge due to: {error_msg}")
        
        try:
            # Use base judge service for fallback
            single_score = await self.base_judge.evaluate_context(context)
            
            # Convert to consensus format
            fallback_result = IndividualJudgeResult(
                provider=single_score.provider,
                score=single_score,
                success=True
            )
            
            total_latency = (time.perf_counter() - start_time) * 1000
            
            return ConsensusScore(
                # Use single judge scores
                relevance=single_score.relevance,
                completeness=single_score.completeness,
                reasoning_quality=single_score.reasoning_quality,
                consistency=single_score.consistency,
                overall=single_score.overall,
                
                # Fallback metadata
                consensus_mode=ConsensusMode.SINGLE,
                judges_used=[single_score.provider],
                individual_results=[fallback_result],
                outliers_detected=[],
                
                # Single explanation
                consensus_explanation=f"Fallback to single judge due to consensus failure: {error_msg}\n\n{single_score.explanation}",
                individual_explanations=[single_score.explanation],
                
                # Performance
                total_latency_ms=total_latency,
                consensus_variance=0.0,
                reliability_score=0.5,  # Lower reliability due to fallback
                
                # Context
                reasoning_type=context.reasoning_type or ReasoningType.SINGLE_HOP,
                timestamp=datetime.utcnow(),
                
                # Fallback info
                requested_judges=mode_to_count(requested_mode),
                actual_judges=1,
                fallback_occurred=True
            )
            
        except Exception as e:
            logger.error(f"❌ Even single judge fallback failed: {e}")
            raise ValueError(f"Complete evaluation failure: consensus failed ({error_msg}), fallback failed ({e})")


# Singleton instance
_consensus_judge = None

def get_consensus_judge() -> ConsensusJudgeService:
    """Get singleton consensus judge service"""
    global _consensus_judge
    if _consensus_judge is None:
        _consensus_judge = ConsensusJudgeService()
    return _consensus_judge


# Convenience functions for consensus evaluation
async def evaluate_with_consensus(
    query: str,
    memories: List[str],
    response: str,
    consensus_mode: Optional[ConsensusMode] = None,
    reasoning_type: Optional[ReasoningType] = None
) -> ConsensusScore:
    """Evaluate response using consensus judging"""
    context = EvaluationContext(
        query=query,
        retrieved_memories=memories,
        generated_response=response,
        reasoning_type=reasoning_type
    )
    
    judge = get_consensus_judge()
    return await judge.evaluate_context(context, consensus_mode)


async def compare_consensus_vs_single(
    query: str,
    memories: List[str],
    response: str,
    reasoning_type: Optional[ReasoningType] = None
) -> Dict[str, Any]:
    """Compare consensus vs single judge evaluation for reliability analysis"""
    
    # Run single judge evaluation
    single_start = time.perf_counter()
    single_score = await evaluate_with_consensus(
        query, memories, response, ConsensusMode.SINGLE, reasoning_type
    )
    single_time = (time.perf_counter() - single_start) * 1000
    
    # Run consensus evaluation
    consensus_start = time.perf_counter()
    consensus_score = await evaluate_with_consensus(
        query, memories, response, ConsensusMode.TRIPLE, reasoning_type
    )
    consensus_time = (time.perf_counter() - consensus_start) * 1000
    
    return {
        "single_judge": {
            "score": single_score.overall,
            "latency_ms": single_time,
            "variance": 0.0
        },
        "consensus_judge": {
            "score": consensus_score.overall,
            "latency_ms": consensus_time,
            "variance": consensus_score.consensus_variance,
            "judges_used": len(consensus_score.judges_used),
            "reliability": consensus_score.reliability_score
        },
        "comparison": {
            "score_difference": abs(consensus_score.overall - single_score.overall),
            "latency_ratio": consensus_time / single_time if single_time > 0 else float('inf'),
            "variance_reduction": True if consensus_score.consensus_variance < 1.0 else False
        }
    }