"""
LLM Judge Integration with Core Evaluation Infrastructure
========================================================

Extends the Task 1 evaluation decorator system to automatically trigger
LLM-based quality evaluation when configured, providing seamless integration
between performance metrics and quality scoring.

Part of Task 2: LLM Judge & Scoring System
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import asdict

from .core import EvaluationMode
from .metrics import EvaluationMetric
from .storage import MetricsStorage

# Import with fallback if not available
try:
    from .llm_judge import (
        LLMJudgeService, 
        EvaluationContext as JudgeContext,
        JudgeScore,
        ReasoningType,
        LLMProvider,
        get_judge_service
    )
    _LLM_JUDGE_AVAILABLE = True
except ImportError:
    _LLM_JUDGE_AVAILABLE = False

logger = logging.getLogger(__name__)


class JudgeIntegrationConfig:
    """Configuration for LLM Judge integration"""
    
    @staticmethod
    def is_judge_enabled() -> bool:
        """Check if LLM judging is enabled via environment variables"""
        import os
        return (
            EvaluationMode.is_enabled() and  # Evaluation must be enabled
            _LLM_JUDGE_AVAILABLE and         # Judge module must be available
            os.getenv("LLM_JUDGE_ENABLED", "false").lower() in ("true", "1", "yes", "on")
        )
    
    @staticmethod
    def get_judge_config() -> Dict[str, Any]:
        """Get LLM judge configuration from environment"""
        import os
        return {
            "enabled": JudgeIntegrationConfig.is_judge_enabled(),
            "provider": os.getenv("LLM_JUDGE_PROVIDER", "auto"),  # auto, gemini, openai
            "async_evaluation": os.getenv("LLM_JUDGE_ASYNC", "true").lower() in ("true", "1", "yes", "on"),
            "timeout_seconds": int(os.getenv("LLM_JUDGE_TIMEOUT", "30")),
            "functions_to_judge": set(os.getenv("LLM_JUDGE_FUNCTIONS", "").split(",")) if os.getenv("LLM_JUDGE_FUNCTIONS") else set(),
            "min_memory_count": int(os.getenv("LLM_JUDGE_MIN_MEMORIES", "1")),  # Only judge if memories retrieved
        }


class JudgeEvaluationMetric(EvaluationMetric):
    """Extended evaluation metric that includes LLM judge scores (single or consensus)"""
    
    def __init__(self, base_metric: EvaluationMetric, judge_score=None, consensus_score=None):
        # Copy all attributes from base metric
        super().__init__(
            function_name=base_metric.function_name,
            latency_ms=base_metric.latency_ms,
            success=base_metric.success,
            timestamp=base_metric.timestamp,
            metadata=base_metric.metadata.copy()
        )
        
        # Add additional fields
        for attr in ['memory_delta_mb', 'error']:
            if hasattr(base_metric, attr):
                setattr(self, attr, getattr(base_metric, attr))
        
        # Handle both single judge and consensus scores
        if consensus_score:
            self._add_consensus_data(consensus_score)
        elif judge_score:
            self._add_single_judge_data(judge_score)
        else:
            self._add_empty_judge_data()
    
    def _add_consensus_data(self, consensus_score):
        """Add consensus judge evaluation data"""
        from .consensus_judge import ConsensusScore, ConsensusMode
        
        self.judge_score = None
        self.consensus_score = consensus_score
        self.has_judge_evaluation = True
        self.is_consensus = True
        
        # Consensus scores
        self.judge_relevance = consensus_score.relevance
        self.judge_completeness = consensus_score.completeness
        self.judge_reasoning_quality = consensus_score.reasoning_quality
        self.judge_consistency = consensus_score.consistency
        self.judge_overall = consensus_score.overall
        self.judge_reasoning_type = consensus_score.reasoning_type.value
        self.judge_latency_ms = consensus_score.total_latency_ms
        
        # Consensus-specific metadata
        self.consensus_mode = consensus_score.consensus_mode.value
        self.judges_used = [p.value for p in consensus_score.judges_used]
        self.judges_count = len(consensus_score.judges_used)
        self.consensus_variance = consensus_score.consensus_variance
        self.reliability_score = consensus_score.reliability_score
        self.outliers_detected = [p.value for p in consensus_score.outliers_detected]
        self.fallback_occurred = consensus_score.fallback_occurred
        
        # Individual judge scores for analysis
        self.individual_judge_scores = []
        for result in consensus_score.individual_results:
            if result.success and result.score:
                self.individual_judge_scores.append({
                    "provider": result.provider.value,
                    "relevance": result.score.relevance,
                    "completeness": result.score.completeness,
                    "reasoning_quality": result.score.reasoning_quality,
                    "consistency": result.score.consistency,
                    "overall": result.score.overall,
                    "latency_ms": result.latency_ms
                })
        
        # Primary provider (first successful judge)
        if consensus_score.judges_used:
            self.judge_provider = consensus_score.judges_used[0].value
        else:
            self.judge_provider = "consensus_failed"
    
    def _add_single_judge_data(self, judge_score):
        """Add single judge evaluation data"""
        self.judge_score = judge_score
        self.consensus_score = None
        self.has_judge_evaluation = True
        self.is_consensus = False
        
        # Single judge scores
        self.judge_relevance = judge_score.relevance
        self.judge_completeness = judge_score.completeness
        self.judge_reasoning_quality = judge_score.reasoning_quality
        self.judge_consistency = judge_score.consistency
        self.judge_overall = judge_score.overall
        self.judge_provider = judge_score.provider.value
        self.judge_reasoning_type = judge_score.reasoning_type.value
        self.judge_latency_ms = judge_score.latency_ms
        
        # Consensus fields (empty for single judge)
        self.consensus_mode = "single"
        self.judges_used = [judge_score.provider.value]
        self.judges_count = 1
        self.consensus_variance = 0.0
        self.reliability_score = 1.0
        self.outliers_detected = []
        self.fallback_occurred = False
        self.individual_judge_scores = []
    
    def _add_empty_judge_data(self):
        """Add empty judge data when no evaluation performed"""
        self.judge_score = None
        self.consensus_score = None
        self.has_judge_evaluation = False
        self.is_consensus = False
        
        # Empty scores
        self.judge_relevance = None
        self.judge_completeness = None
        self.judge_reasoning_quality = None
        self.judge_consistency = None
        self.judge_overall = None
        self.judge_provider = None
        self.judge_reasoning_type = None
        self.judge_latency_ms = None
        
        # Empty consensus fields
        self.consensus_mode = None
        self.judges_used = []
        self.judges_count = 0
        self.consensus_variance = None
        self.reliability_score = None
        self.outliers_detected = []
        self.fallback_occurred = False
        self.individual_judge_scores = []


class EnhancedMetricsCollector:
    """
    Enhanced metrics collector that integrates LLM judging with performance metrics.
    
    Automatically triggers LLM evaluation for functions that return context and memories.
    """
    
    def __init__(self):
        self.config = JudgeIntegrationConfig.get_judge_config()
        self.judge_service = None
        self.consensus_service = None
        
        if self.config["enabled"]:
            try:
                # Try to initialize consensus judge (includes single judge)
                try:
                    from .consensus_judge import get_consensus_judge, ConsensusConfiguration
                    self.consensus_service = get_consensus_judge()
                    self.consensus_config = ConsensusConfiguration.get_consensus_config()
                    logger.info("✅ Consensus LLM Judge integration enabled")
                except ImportError:
                    # Fallback to single judge
                    self.judge_service = get_judge_service()
                    logger.info("✅ Single LLM Judge integration enabled")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize LLM Judge: {e}")
                self.config["enabled"] = False
    
    async def collect_with_judge_evaluation(
        self,
        base_metric: EvaluationMetric,
        function_result: Any = None,
        function_args: tuple = (),
        function_kwargs: dict = None
    ) -> JudgeEvaluationMetric:
        """
        Collect metrics and optionally perform LLM judge evaluation.
        
        Args:
            base_metric: Basic performance metric
            function_result: Result from the evaluated function
            function_args: Original function arguments
            function_kwargs: Original function keyword arguments
        
        Returns:
            Enhanced metric with optional judge scores
        """
        function_kwargs = function_kwargs or {}
        
        # Check if judge evaluation should be performed
        should_judge = self._should_evaluate_with_judge(
            base_metric.function_name, 
            function_result, 
            function_args, 
            function_kwargs
        )
        
        if not should_judge:
            return JudgeEvaluationMetric(base_metric)
        
        # Extract evaluation context from function result/args
        judge_context = self._extract_judge_context(
            function_result, 
            function_args, 
            function_kwargs
        )
        
        if not judge_context:
            logger.debug(f"Could not extract judge context for {base_metric.function_name}")
            return JudgeEvaluationMetric(base_metric)
        
        # Perform LLM judge evaluation (consensus or single)
        judge_score = None
        consensus_score = None
        
        try:
            if self.config["async_evaluation"]:
                # Fire and forget async evaluation
                asyncio.create_task(
                    self._async_judge_evaluation(base_metric.function_name, judge_context)
                )
            else:
                # Synchronous evaluation
                if self.consensus_service:
                    # Use consensus judging
                    consensus_score = await self._perform_consensus_evaluation(judge_context)
                else:
                    # Use single judge
                    judge_score = await self._perform_judge_evaluation(judge_context)
        
        except Exception as e:
            logger.error(f"LLM judge evaluation failed: {e}")
        
        return JudgeEvaluationMetric(base_metric, judge_score, consensus_score)
    
    def _should_evaluate_with_judge(
        self, 
        function_name: str, 
        function_result: Any, 
        function_args: tuple, 
        function_kwargs: dict
    ) -> bool:
        """Determine if function should be evaluated with LLM judge"""
        if not self.config["enabled"]:
            return False
        
        # Check if specific functions are configured for judging
        if self.config["functions_to_judge"]:
            if function_name not in self.config["functions_to_judge"]:
                return False
        
        # Check if we can extract meaningful context
        context = self._extract_judge_context(function_result, function_args, function_kwargs)
        if not context:
            return False
        
        # Check minimum memory requirement
        if len(context.retrieved_memories) < self.config["min_memory_count"]:
            return False
        
        return True
    
    def _extract_judge_context(
        self, 
        function_result: Any, 
        function_args: tuple, 
        function_kwargs: dict
    ) -> Optional[JudgeContext]:
        """
        Extract LLM judge evaluation context from function parameters and results.
        
        This method attempts to intelligently extract:
        - User query
        - Retrieved memories  
        - Generated response
        - Conversation context
        
        From various function signatures and return values.
        """
        try:
            # Strategy 1: Function result contains structured context
            if isinstance(function_result, dict):
                return self._extract_from_dict_result(function_result, function_kwargs)
            
            # Strategy 2: Function result is a string (generated response)
            elif isinstance(function_result, str):
                return self._extract_from_string_result(function_result, function_args, function_kwargs)
            
            # Strategy 3: Function arguments contain context
            else:
                return self._extract_from_function_args(function_args, function_kwargs)
        
        except Exception as e:
            logger.debug(f"Failed to extract judge context: {e}")
            return None
    
    def _extract_from_dict_result(self, result: dict, kwargs: dict) -> Optional[JudgeContext]:
        """Extract context from dictionary result (e.g., orchestration result)"""
        # Look for common patterns in Jean Memory results
        query = (
            result.get("query") or 
            result.get("user_query") or 
            kwargs.get("query") or
            kwargs.get("user_query") or
            kwargs.get("message")
        )
        
        memories = (
            result.get("memories") or
            result.get("retrieved_memories") or
            result.get("context_memories") or
            []
        )
        
        response = (
            result.get("response") or
            result.get("generated_response") or
            result.get("context") or
            result.get("formatted_context") or
            str(result)
        )
        
        if query and memories and response:
            return JudgeContext(
                query=str(query),
                retrieved_memories=[str(m) for m in memories if m],
                generated_response=str(response),
                user_id=kwargs.get("user_id"),
                session_id=kwargs.get("session_id")
            )
        
        return None
    
    def _extract_from_string_result(self, result: str, args: tuple, kwargs: dict) -> Optional[JudgeContext]:
        """Extract context when function returns a string (assumed to be response)"""
        # Extract query from function arguments
        query = None
        for arg in args:
            if isinstance(arg, str) and len(arg) > 10 and "?" in arg:
                query = arg
                break
        
        if not query:
            query = (
                kwargs.get("query") or
                kwargs.get("user_query") or
                kwargs.get("message")
            )
        
        # Extract memories from arguments or kwargs
        memories = []
        for arg in args:
            if isinstance(arg, list) and arg:
                # Assume first non-empty list is memories
                memories = [str(item) for item in arg]
                break
        
        if not memories:
            memories = kwargs.get("memories", [])
        
        if query and memories:
            return JudgeContext(
                query=str(query),
                retrieved_memories=memories,
                generated_response=result,
                user_id=kwargs.get("user_id"),
                session_id=kwargs.get("session_id")
            )
        
        return None
    
    def _extract_from_function_args(self, args: tuple, kwargs: dict) -> Optional[JudgeContext]:
        """Extract context from function arguments when result isn't informative"""
        # This is a fallback - look for query, memories, response in args/kwargs
        query = kwargs.get("query") or kwargs.get("user_query")
        memories = kwargs.get("memories", [])
        response = kwargs.get("response")
        
        if query and memories and response:
            return JudgeContext(
                query=str(query),
                retrieved_memories=[str(m) for m in memories],
                generated_response=str(response),
                user_id=kwargs.get("user_id"),
                session_id=kwargs.get("session_id")
            )
        
        return None
    
    async def _perform_judge_evaluation(self, context: JudgeContext) -> Optional[JudgeScore]:
        """Perform single LLM judge evaluation with timeout"""
        try:
            timeout = self.config["timeout_seconds"]
            return await asyncio.wait_for(
                self.judge_service.evaluate_context(context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"LLM judge evaluation timed out after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"LLM judge evaluation failed: {e}")
            return None
    
    async def _perform_consensus_evaluation(self, context: JudgeContext):
        """Perform consensus LLM judge evaluation with timeout"""
        try:
            from .consensus_judge import ConsensusScore
            timeout = self.consensus_config.get("parallel_timeout", 10)
            return await asyncio.wait_for(
                self.consensus_service.evaluate_context(context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Consensus judge evaluation timed out after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"Consensus judge evaluation failed: {e}")
            return None
    
    async def _async_judge_evaluation(self, function_name: str, context: JudgeContext):
        """Perform asynchronous judge evaluation and store separately"""
        try:
            judge_score = await self._perform_judge_evaluation(context)
            if judge_score:
                # Store judge result separately for async processing
                await self._store_async_judge_result(function_name, judge_score)
        except Exception as e:
            logger.error(f"Async judge evaluation failed for {function_name}: {e}")
    
    async def _store_async_judge_result(self, function_name: str, judge_score: JudgeScore):
        """Store asynchronous judge results"""
        try:
            storage = MetricsStorage()
            
            # Create a judge-specific metric
            judge_metric_data = {
                "function_name": f"{function_name}_judge",
                "timestamp": judge_score.timestamp.isoformat(),
                "judge_relevance": judge_score.relevance,
                "judge_completeness": judge_score.completeness,
                "judge_reasoning_quality": judge_score.reasoning_quality,
                "judge_consistency": judge_score.consistency,
                "judge_overall": judge_score.overall,
                "judge_provider": judge_score.provider.value,
                "judge_reasoning_type": judge_score.reasoning_type.value,
                "judge_latency_ms": judge_score.latency_ms,
                "judge_explanation": judge_score.explanation,
                "type": "llm_judge_result"
            }
            
            storage.store([judge_metric_data])
            logger.debug(f"Stored async judge result for {function_name}")
            
        except Exception as e:
            logger.error(f"Failed to store async judge result: {e}")


# Enhanced decorator that uses the integrated metrics collector
def evaluate_with_judge(name: Optional[str] = None, capture_result: bool = True):
    """
    Enhanced evaluation decorator that includes LLM judge evaluation.
    
    This extends the Task 1 decorator to automatically trigger LLM-based quality
    evaluation when appropriate conditions are met.
    
    Args:
        name: Optional name override for the function
        capture_result: Whether to capture and evaluate function results
    
    Environment Configuration:
        LLM_JUDGE_ENABLED: Enable/disable LLM judging (default: false)
        LLM_JUDGE_PROVIDER: Preferred LLM provider (auto, gemini, openai)
        LLM_JUDGE_ASYNC: Async evaluation mode (default: true)
        LLM_JUDGE_FUNCTIONS: Comma-separated list of functions to judge
        LLM_JUDGE_MIN_MEMORIES: Minimum memories required for judging
    """
    def decorator(func: Callable) -> Callable:
        # Use base evaluation decorator if judge integration disabled
        if not JudgeIntegrationConfig.is_judge_enabled():
            from .core import evaluate
            return evaluate(name, capture_result)(func)
        
        # Create enhanced decorator with judge integration
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            from .core import EvaluationContext
            import time
            
            function_name = name or func.__name__
            start_time = time.perf_counter()
            result = None
            error = None
            
            # Create base evaluation context
            context = EvaluationContext(function_name, args, kwargs)
            
            try:
                # Execute original function
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                # Create base metric
                base_metric = context.complete(result if capture_result else None, error)
                
                # Enhance with judge evaluation
                collector = EnhancedMetricsCollector()
                enhanced_metric = await collector.collect_with_judge_evaluation(
                    base_metric, 
                    result if capture_result else None,
                    args, 
                    kwargs
                )
                
                # Store enhanced metric
                try:
                    storage = MetricsStorage()
                    storage.store([asdict(enhanced_metric)])
                except Exception as e:
                    logger.error(f"Failed to store enhanced metric: {e}")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use base decorator
            from .core import evaluate
            return evaluate(name, capture_result)(func)(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience function to check judge integration status
def get_judge_integration_status() -> Dict[str, Any]:
    """Get current status of LLM judge integration"""
    config = JudgeIntegrationConfig.get_judge_config()
    
    status = {
        "evaluation_enabled": EvaluationMode.is_enabled(),
        "judge_module_available": _LLM_JUDGE_AVAILABLE,
        "judge_enabled": config["enabled"],
        "judge_config": config
    }
    
    if config["enabled"]:
        try:
            judge_service = get_judge_service()
            status["judge_providers"] = {
                "gemini_available": judge_service.gemini_model is not None,
                "openai_available": judge_service.openai_client is not None,
                "default_provider": judge_service.default_provider.value
            }
        except Exception as e:
            status["judge_error"] = str(e)
    
    return status