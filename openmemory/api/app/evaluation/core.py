"""
Core Evaluation Infrastructure
===============================

Provides decorator-based monitoring that can be toggled on/off without 
impacting production performance.
"""

import asyncio
import functools
import logging
import os
import time
import tracemalloc
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from datetime import datetime

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class EvaluationMode:
    """
    Manages evaluation mode state based on environment variable.
    
    PRODUCTION SAFETY: Defaults to disabled, requires explicit opt-in.
    """
    
    # Cache the evaluation mode to avoid repeated env var lookups
    _cached_mode = None
    _cache_timestamp = None
    
    @staticmethod
    def is_enabled() -> bool:
        """
        Check if evaluation mode is enabled via environment variable.
        
        PERFORMANCE OPTIMIZATION: Result is cached to avoid repeated env lookups.
        Cache expires after 60 seconds to allow runtime changes during development.
        """
        # In production, this will always be False unless explicitly enabled
        # The default is "false" to ensure zero impact in production
        
        # Use cached value if available and fresh (for performance)
        if EvaluationMode._cached_mode is not None:
            if EvaluationMode._cache_timestamp:
                cache_age = time.time() - EvaluationMode._cache_timestamp
                if cache_age < 60:  # Cache for 60 seconds
                    return EvaluationMode._cached_mode
        
        # Check environment variable (defaults to false for production safety)
        mode = os.getenv("EVALUATION_MODE", "false").lower() in ("true", "1", "yes", "on")
        
        # Cache the result
        EvaluationMode._cached_mode = mode
        EvaluationMode._cache_timestamp = time.time()
        
        return mode
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get evaluation configuration from environment."""
        return {
            "enabled": EvaluationMode.is_enabled(),
            "async_processing": os.getenv("EVALUATION_ASYNC", "true").lower() in ("true", "1", "yes", "on"),
            "max_memory_overhead_mb": int(os.getenv("EVALUATION_MAX_MEMORY_MB", "50")),
            "timeout_seconds": float(os.getenv("EVALUATION_TIMEOUT_SECONDS", "5.0")),
            "storage_backend": os.getenv("EVALUATION_STORAGE", "json"),  # json, postgres, redis
            "log_level": os.getenv("EVALUATION_LOG_LEVEL", "INFO")
        }


class EvaluationContext:
    """
    Context information for evaluation execution.
    """
    
    def __init__(self, function_name: str, args: tuple, kwargs: dict):
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs
        self.start_time = time.perf_counter()
        self.start_memory = None
        self.metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": kwargs.get("user_id"),
            "client_name": kwargs.get("client_name"),
            "is_new_conversation": kwargs.get("is_new_conversation")
        }
        
        # Track memory if enabled
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            self.start_memory = sum(stat.size for stat in snapshot.statistics('lineno'))
    
    def complete(self, result: Any = None, error: Exception = None) -> Dict[str, Any]:
        """Complete the evaluation context and return metrics."""
        end_time = time.perf_counter()
        metrics = {
            "function_name": self.function_name,
            "latency_ms": (end_time - self.start_time) * 1000,
            "success": error is None,
            "metadata": self.metadata
        }
        
        # Add error info if present
        if error:
            metrics["error"] = {
                "type": type(error).__name__,
                "message": str(error)
            }
        
        # Calculate memory usage if tracking
        if self.start_memory is not None and tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            end_memory = sum(stat.size for stat in snapshot.statistics('lineno'))
            metrics["memory_delta_mb"] = (end_memory - self.start_memory) / (1024 * 1024)
        
        return metrics


class EvaluationDecorator:
    """
    Main decorator for adding evaluation to functions without modifying their behavior.
    """
    
    def __init__(self, name: Optional[str] = None, capture_result: bool = False):
        """
        Initialize evaluation decorator.
        
        Args:
            name: Optional custom name for the function (defaults to function.__name__)
            capture_result: Whether to capture function result for evaluation (default False)
        """
        self.name = name
        self.capture_result = capture_result
        self._metrics_collector = None
    
    def _get_metrics_collector(self):
        """Lazy initialization of metrics collector."""
        if self._metrics_collector is None:
            from .metrics import MetricsCollector
            self._metrics_collector = MetricsCollector()
        return self._metrics_collector
    
    def __call__(self, func: F) -> F:
        """
        Decorate a function with evaluation monitoring.
        """
        function_name = self.name or func.__name__
        
        # Handle both sync and async functions
        if asyncio.iscoroutinefunction(func):
            return self._decorate_async(func, function_name)
        else:
            return self._decorate_sync(func, function_name)
    
    def _decorate_sync(self, func: F, function_name: str) -> F:
        """Decorate synchronous function."""
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Fast path: skip evaluation if disabled
            if not EvaluationMode.is_enabled():
                return func(*args, **kwargs)
            
            context = EvaluationContext(function_name, args, kwargs)
            result = None
            error = None
            
            try:
                # Execute original function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                # Collect metrics asynchronously if enabled
                if EvaluationMode.get_config()["async_processing"]:
                    self._submit_metrics_async(context, result if self.capture_result else None, error)
                else:
                    self._submit_metrics_sync(context, result if self.capture_result else None, error)
        
        return wrapper
    
    def _decorate_async(self, func: F, function_name: str) -> F:
        """Decorate asynchronous function."""
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Fast path: skip evaluation if disabled
            if not EvaluationMode.is_enabled():
                return await func(*args, **kwargs)
            
            context = EvaluationContext(function_name, args, kwargs)
            result = None
            error = None
            
            try:
                # Execute original function
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                # Collect metrics asynchronously
                if EvaluationMode.get_config()["async_processing"]:
                    # Fire and forget - don't await to avoid blocking
                    asyncio.create_task(
                        self._submit_metrics_async_coroutine(
                            context, 
                            result if self.capture_result else None, 
                            error
                        )
                    )
                else:
                    await self._submit_metrics_async_coroutine(
                        context,
                        result if self.capture_result else None,
                        error
                    )
        
        return wrapper
    
    def _submit_metrics_sync(self, context: EvaluationContext, result: Any, error: Exception):
        """Submit metrics synchronously."""
        try:
            metrics = context.complete(result, error)
            collector = self._get_metrics_collector()
            collector.collect(metrics)
        except Exception as e:
            logger.error(f"Failed to submit evaluation metrics: {e}")
    
    def _submit_metrics_async(self, context: EvaluationContext, result: Any, error: Exception):
        """Submit metrics asynchronously in a separate thread."""
        import threading
        
        def _submit():
            try:
                metrics = context.complete(result, error)
                collector = self._get_metrics_collector()
                collector.collect(metrics)
            except Exception as e:
                logger.error(f"Failed to submit evaluation metrics: {e}")
        
        thread = threading.Thread(target=_submit, daemon=True)
        thread.start()
    
    async def _submit_metrics_async_coroutine(self, context: EvaluationContext, result: Any, error: Exception):
        """Submit metrics asynchronously as a coroutine."""
        try:
            config = EvaluationMode.get_config()
            timeout = config["timeout_seconds"]
            
            async def _submit():
                metrics = context.complete(result, error)
                collector = self._get_metrics_collector()
                await collector.collect_async(metrics)
            
            # Apply timeout to prevent hanging
            await asyncio.wait_for(_submit(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Evaluation metrics submission timed out for {context.function_name}")
        except Exception as e:
            logger.error(f"Failed to submit evaluation metrics: {e}")


# Production optimization: Create a no-op decorator for when evaluation is disabled
class NoOpDecorator:
    """
    No-operation decorator that returns the original function unchanged.
    Used in production when evaluation is disabled for ZERO overhead.
    """
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, func):
        return func


# PRODUCTION OPTIMIZATION: Pre-compute evaluation state at module import
_EVALUATION_ENABLED_AT_IMPORT = os.getenv("EVALUATION_MODE", "false").lower() in ("true", "1", "yes", "on")

# Singleton no-op decorator instance for maximum performance
_NO_OP_DECORATOR = NoOpDecorator()


# Convenience decorator factory with production optimization
def evaluate(name: Optional[str] = None, capture_result: bool = False) -> Union[EvaluationDecorator, NoOpDecorator]:
    """
    Factory function for creating evaluation decorators.
    
    PRODUCTION OPTIMIZATION: Returns no-op decorator if evaluation is disabled
    at import time, ensuring ZERO overhead in production.
    
    Args:
        name: Optional custom name for the function
        capture_result: Whether to capture function result for evaluation
    
    Returns:
        EvaluationDecorator instance if enabled, NoOpDecorator if disabled
    
    Example:
        @evaluate()
        async def my_function():
            pass
        
        @evaluate(name="custom_name", capture_result=True)
        def another_function():
            pass
    """
    # PRODUCTION OPTIMIZATION: Use pre-computed state to avoid env var lookup
    # This makes the decorator selection a simple boolean check
    if not _EVALUATION_ENABLED_AT_IMPORT:
        return _NO_OP_DECORATOR  # Return singleton for zero allocation overhead
    
    return EvaluationDecorator(name=name, capture_result=capture_result)