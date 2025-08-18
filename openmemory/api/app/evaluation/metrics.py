"""
Metrics Collection and Management
==================================

Handles collection, aggregation, and storage of evaluation metrics.
"""

import asyncio
import json
import logging
import os
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Deque
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetric:
    """
    Individual evaluation metric data point.
    """
    function_name: str
    latency_ms: float
    success: bool
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Dict[str, str]] = None
    memory_delta_mb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationMetric':
        """Create from dictionary."""
        return cls(**data)


class MetricsAggregator:
    """
    Aggregates metrics for reporting and analysis.
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize aggregator.
        
        Args:
            window_size: Number of recent metrics to keep for aggregation
        """
        self.window_size = window_size
        self._metrics: Dict[str, Deque[EvaluationMetric]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self._lock = Lock()
    
    def add(self, metric: EvaluationMetric):
        """Add a metric to the aggregator."""
        with self._lock:
            self._metrics[metric.function_name].append(metric)
    
    def get_statistics(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregated statistics for a function or all functions.
        
        Args:
            function_name: Optional function name to filter by
        
        Returns:
            Dictionary of aggregated statistics
        """
        with self._lock:
            if function_name:
                metrics = list(self._metrics.get(function_name, []))
                return self._calculate_stats(function_name, metrics)
            
            # Aggregate all functions
            all_stats = {}
            for fname, metrics in self._metrics.items():
                all_stats[fname] = self._calculate_stats(fname, list(metrics))
            
            # Add overall statistics
            all_metrics = []
            for metrics in self._metrics.values():
                all_metrics.extend(metrics)
            all_stats["_overall"] = self._calculate_stats("_overall", all_metrics)
            
            return all_stats
    
    def _calculate_stats(self, function_name: str, metrics: List[EvaluationMetric]) -> Dict[str, Any]:
        """Calculate statistics for a set of metrics."""
        if not metrics:
            return {
                "function": function_name,
                "count": 0,
                "success_rate": 0.0,
                "latency": {}
            }
        
        latencies = [m.latency_ms for m in metrics]
        success_count = sum(1 for m in metrics if m.success)
        
        stats = {
            "function": function_name,
            "count": len(metrics),
            "success_rate": success_count / len(metrics),
            "latency": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "p50": self._percentile(latencies, 50),
                "p95": self._percentile(latencies, 95),
                "p99": self._percentile(latencies, 99)
            }
        }
        
        # Add memory statistics if available
        memory_deltas = [m.memory_delta_mb for m in metrics if m.memory_delta_mb is not None]
        if memory_deltas:
            stats["memory"] = {
                "mean_mb": statistics.mean(memory_deltas),
                "max_mb": max(memory_deltas),
                "total_mb": sum(memory_deltas)
            }
        
        # Add error breakdown if any
        errors = [m.error for m in metrics if m.error]
        if errors:
            error_types = defaultdict(int)
            for error in errors:
                error_types[error.get("type", "Unknown")] += 1
            stats["errors"] = dict(error_types)
        
        return stats
    
    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        if upper >= len(sorted_data):
            return sorted_data[lower]
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


class MetricsCollector:
    """
    Main metrics collector that handles metric collection and storage.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.aggregator = MetricsAggregator()
        self._storage = None
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_lock = Lock()
        self._flush_interval = 10  # seconds
        self._last_flush = datetime.utcnow()
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage backend based on configuration."""
        from .storage import MetricsStorage
        self._storage = MetricsStorage()
    
    def collect(self, metrics: Dict[str, Any]):
        """
        Collect metrics synchronously.
        
        Args:
            metrics: Dictionary of metrics to collect
        """
        try:
            # Create metric object
            metric = EvaluationMetric(
                function_name=metrics.get("function_name", "unknown"),
                latency_ms=metrics.get("latency_ms", 0.0),
                success=metrics.get("success", True),
                timestamp=metrics.get("metadata", {}).get("timestamp", datetime.utcnow().isoformat()),
                metadata=metrics.get("metadata", {}),
                error=metrics.get("error"),
                memory_delta_mb=metrics.get("memory_delta_mb")
            )
            
            # Add to aggregator for real-time stats
            self.aggregator.add(metric)
            
            # Buffer for storage
            with self._buffer_lock:
                self._buffer.append(metric.to_dict())
                
                # Check if we should flush
                if self._should_flush():
                    self._flush_buffer()
            
            # Log if evaluation logging is enabled
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Collected metric: {metric.function_name} - {metric.latency_ms:.2f}ms")
                
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
    
    async def collect_async(self, metrics: Dict[str, Any]):
        """
        Collect metrics asynchronously.
        
        Args:
            metrics: Dictionary of metrics to collect
        """
        # Run synchronous collection in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.collect, metrics)
    
    def _should_flush(self) -> bool:
        """Check if buffer should be flushed."""
        # Flush if buffer is large or time interval exceeded
        if len(self._buffer) >= 100:
            return True
        
        if (datetime.utcnow() - self._last_flush).total_seconds() > self._flush_interval:
            return True
        
        return False
    
    def _flush_buffer(self):
        """Flush buffered metrics to storage."""
        if not self._buffer:
            return
        
        try:
            # Copy buffer and clear
            metrics_to_store = self._buffer.copy()
            self._buffer.clear()
            self._last_flush = datetime.utcnow()
            
            # Store metrics
            if self._storage:
                self._storage.store_batch(metrics_to_store)
            
            logger.info(f"Flushed {len(metrics_to_store)} metrics to storage")
            
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {e}")
    
    def get_statistics(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current aggregated statistics.
        
        Args:
            function_name: Optional function name to filter by
        
        Returns:
            Dictionary of statistics
        """
        return self.aggregator.get_statistics(function_name)
    
    def flush(self):
        """Force flush of buffered metrics."""
        with self._buffer_lock:
            self._flush_buffer()
    
    def reset(self):
        """Reset all collected metrics."""
        self.aggregator = MetricsAggregator()
        with self._buffer_lock:
            self._buffer.clear()