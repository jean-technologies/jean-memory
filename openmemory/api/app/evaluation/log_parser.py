"""
Log Parser for Jean Memory Performance Metrics

Parses Render service logs to extract detailed performance metrics about memory searches,
AI planning, context execution, and cache hits that aren't available in MCP responses.
"""

import io
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, TextIO, Union, Iterator
from collections import defaultdict, Counter

from .metrics_extractor import MetricsExtractor, ExtractedMetric, MetricType, LogParsingStats


logger = logging.getLogger(__name__)


@dataclass
class AggregatedMetrics:
    """Aggregated performance metrics from log analysis"""
    
    # Performance metrics
    memory_search_times_ms: List[float] = field(default_factory=list)
    context_execution_times_s: List[float] = field(default_factory=list)
    ai_planning_times_ms: List[float] = field(default_factory=list)
    total_orchestration_times_s: List[float] = field(default_factory=list)
    cache_lookup_times_ms: List[float] = field(default_factory=list)
    database_query_times_ms: List[float] = field(default_factory=list)
    response_generation_times_s: List[float] = field(default_factory=list)
    
    # Context strategies
    context_strategies: List[str] = field(default_factory=list)
    strategy_confidences: List[float] = field(default_factory=list)
    
    # Memory search patterns
    memory_search_queries: List[str] = field(default_factory=list)
    memory_search_results: List[int] = field(default_factory=list)
    memory_filter_ratios: List[float] = field(default_factory=list)
    relevance_thresholds: List[float] = field(default_factory=list)
    
    # Cache statistics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_queries: List[str] = field(default_factory=list)
    
    # Orchestration patterns
    orchestration_phases: List[str] = field(default_factory=list)
    processing_steps: List[str] = field(default_factory=list)
    user_sessions: List[str] = field(default_factory=list)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    
    # Metadata
    analysis_start_time: Optional[datetime] = None
    analysis_end_time: Optional[datetime] = None
    log_timespan: Optional[timedelta] = None
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics from aggregated metrics"""
        
        def safe_avg(values: List[float]) -> float:
            return sum(values) / len(values) if values else 0.0
        
        def safe_percentile(values: List[float], percentile: float) -> float:
            if not values:
                return 0.0
            sorted_values = sorted(values)
            index = int(len(sorted_values) * percentile / 100)
            return sorted_values[min(index, len(sorted_values) - 1)]
        
        stats = {
            # Performance statistics
            "performance": {
                "memory_search": {
                    "count": len(self.memory_search_times_ms),
                    "avg_time_ms": safe_avg(self.memory_search_times_ms),
                    "p50_time_ms": safe_percentile(self.memory_search_times_ms, 50),
                    "p95_time_ms": safe_percentile(self.memory_search_times_ms, 95),
                    "max_time_ms": max(self.memory_search_times_ms) if self.memory_search_times_ms else 0
                },
                "context_execution": {
                    "count": len(self.context_execution_times_s),
                    "avg_time_s": safe_avg(self.context_execution_times_s),
                    "p50_time_s": safe_percentile(self.context_execution_times_s, 50),
                    "p95_time_s": safe_percentile(self.context_execution_times_s, 95),
                    "max_time_s": max(self.context_execution_times_s) if self.context_execution_times_s else 0
                },
                "ai_planning": {
                    "count": len(self.ai_planning_times_ms),
                    "avg_time_ms": safe_avg(self.ai_planning_times_ms),
                    "p50_time_ms": safe_percentile(self.ai_planning_times_ms, 50),
                    "p95_time_ms": safe_percentile(self.ai_planning_times_ms, 95),
                    "max_time_ms": max(self.ai_planning_times_ms) if self.ai_planning_times_ms else 0
                },
                "total_orchestration": {
                    "count": len(self.total_orchestration_times_s),
                    "avg_time_s": safe_avg(self.total_orchestration_times_s),
                    "p50_time_s": safe_percentile(self.total_orchestration_times_s, 50),
                    "p95_time_s": safe_percentile(self.total_orchestration_times_s, 95),
                    "max_time_s": max(self.total_orchestration_times_s) if self.total_orchestration_times_s else 0
                }
            },
            
            # Context strategy statistics
            "context_strategies": {
                "strategy_distribution": dict(Counter(self.context_strategies)),
                "avg_confidence": safe_avg(self.strategy_confidences),
                "total_strategies": len(self.context_strategies)
            },
            
            # Memory search statistics
            "memory_search": {
                "total_searches": len(self.memory_search_queries),
                "avg_results_per_search": safe_avg([float(x) for x in self.memory_search_results]),
                "avg_filter_ratio": safe_avg(self.memory_filter_ratios),
                "avg_relevance_threshold": safe_avg(self.relevance_thresholds),
                "unique_queries": len(set(self.memory_search_queries))
            },
            
            # Cache statistics
            "cache": {
                "total_cache_operations": self.cache_hits + self.cache_misses,
                "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "unique_cache_queries": len(set(self.cache_queries))
            },
            
            # Orchestration statistics
            "orchestration": {
                "total_phases": len(self.orchestration_phases),
                "phase_distribution": dict(Counter(self.orchestration_phases)),
                "processing_steps": dict(Counter(self.processing_steps)),
                "unique_users": len(set(self.user_sessions))
            },
            
            # Error statistics
            "errors": {
                "total_errors": len(self.errors),
                "error_types": dict(Counter(self.errors))
            },
            
            # Temporal statistics
            "temporal": {
                "analysis_start": self.analysis_start_time.isoformat() if self.analysis_start_time else None,
                "analysis_end": self.analysis_end_time.isoformat() if self.analysis_end_time else None,
                "log_timespan_seconds": self.log_timespan.total_seconds() if self.log_timespan else 0
            }
        }
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "raw_metrics": {
                "memory_search_times_ms": self.memory_search_times_ms,
                "context_execution_times_s": self.context_execution_times_s,
                "ai_planning_times_ms": self.ai_planning_times_ms,
                "total_orchestration_times_s": self.total_orchestration_times_s,
                "cache_lookup_times_ms": self.cache_lookup_times_ms,
                "database_query_times_ms": self.database_query_times_ms,
                "response_generation_times_s": self.response_generation_times_s,
                "context_strategies": self.context_strategies,
                "strategy_confidences": self.strategy_confidences,
                "memory_search_queries": self.memory_search_queries,
                "memory_search_results": self.memory_search_results,
                "memory_filter_ratios": self.memory_filter_ratios,
                "relevance_thresholds": self.relevance_thresholds,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_queries": self.cache_queries,
                "orchestration_phases": self.orchestration_phases,
                "processing_steps": self.processing_steps,
                "user_sessions": self.user_sessions,
                "errors": self.errors
            },
            "statistics": self.calculate_statistics(),
            "metadata": {
                "analysis_start_time": self.analysis_start_time.isoformat() if self.analysis_start_time else None,
                "analysis_end_time": self.analysis_end_time.isoformat() if self.analysis_end_time else None,
                "log_timespan_seconds": self.log_timespan.total_seconds() if self.log_timespan else 0
            }
        }


class LogParser:
    """
    Parses Jean Memory service logs to extract performance metrics.
    
    Handles various log formats and provides streaming parsing capabilities
    for large log files.
    """
    
    def __init__(self, chunk_size: int = 8192):
        """
        Initialize log parser.
        
        Args:
            chunk_size: Size of chunks for streaming large files
        """
        self.extractor = MetricsExtractor()
        self.chunk_size = chunk_size
        
    def parse_log_file(
        self,
        log_file_path: Union[str, Path],
        encoding: str = 'utf-8',
        ignore_errors: bool = True
    ) -> tuple[AggregatedMetrics, LogParsingStats]:
        """
        Parse a complete log file and extract metrics.
        
        Args:
            log_file_path: Path to log file
            encoding: File encoding
            ignore_errors: Whether to ignore encoding/parsing errors
            
        Returns:
            Tuple of (aggregated metrics, parsing statistics)
        """
        log_path = Path(log_file_path)
        
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        
        logger.info(f"Parsing log file: {log_path}")
        start_time = time.time()
        
        self.extractor.reset_stats()
        
        try:
            with open(log_path, 'r', encoding=encoding, errors='ignore' if ignore_errors else 'strict') as f:
                metrics = self._parse_log_stream(f)
        except Exception as e:
            logger.error(f"Failed to parse log file {log_path}: {e}")
            raise
        
        # Update timing statistics
        self.extractor.stats.processing_time_seconds = time.time() - start_time
        
        logger.info(f"Log parsing completed: {self.extractor.stats.metrics_extracted} metrics extracted "
                   f"from {self.extractor.stats.total_lines_processed} lines in "
                   f"{self.extractor.stats.processing_time_seconds:.2f}s")
        
        return metrics, self.extractor.stats
    
    def parse_log_text(
        self,
        log_text: str
    ) -> tuple[AggregatedMetrics, LogParsingStats]:
        """
        Parse log text directly.
        
        Args:
            log_text: Raw log content as string
            
        Returns:
            Tuple of (aggregated metrics, parsing statistics)
        """
        logger.info(f"Parsing log text ({len(log_text)} characters)")
        start_time = time.time()
        
        self.extractor.reset_stats()
        
        # Use StringIO to treat text as file-like object
        log_stream = io.StringIO(log_text)
        metrics = self._parse_log_stream(log_stream)
        
        # Update timing statistics
        self.extractor.stats.processing_time_seconds = time.time() - start_time
        
        logger.info(f"Text parsing completed: {self.extractor.stats.metrics_extracted} metrics extracted "
                   f"from {self.extractor.stats.total_lines_processed} lines")
        
        return metrics, self.extractor.stats
    
    def _parse_log_stream(self, log_stream: TextIO) -> AggregatedMetrics:
        """
        Parse a log stream and aggregate metrics.
        
        Args:
            log_stream: File-like object containing log data
            
        Returns:
            AggregatedMetrics object with all extracted metrics
        """
        metrics = AggregatedMetrics()
        metrics.analysis_start_time = datetime.now()
        
        first_timestamp = None
        last_timestamp = None
        
        for line_number, line in enumerate(log_stream, 1):
            line = line.strip()
            if not line:
                continue
            
            self.extractor.stats.total_lines_processed += 1
            
            try:
                # Extract metrics from this line
                extracted_metrics = self.extractor.extract_metrics_from_line(line)
                
                if not extracted_metrics:
                    self.extractor.stats.unmatched_lines += 1
                    continue
                
                # Process each extracted metric
                for metric in extracted_metrics:
                    self._aggregate_metric(metrics, metric)
                    self.extractor.stats.metrics_extracted += 1
                    
                    # Track timestamp range
                    if metric.timestamp:
                        if first_timestamp is None:
                            first_timestamp = metric.timestamp
                        last_timestamp = metric.timestamp
                
            except Exception as e:
                logger.warning(f"Error processing line {line_number}: {e}")
                self.extractor.stats.parsing_errors += 1
                continue
        
        # Calculate log timespan
        if first_timestamp and last_timestamp:
            metrics.log_timespan = last_timestamp - first_timestamp
        
        metrics.analysis_end_time = datetime.now()
        
        return metrics
    
    def _aggregate_metric(self, aggregated: AggregatedMetrics, metric: ExtractedMetric) -> None:
        """
        Add an extracted metric to the aggregated metrics.
        
        Args:
            aggregated: AggregatedMetrics object to update
            metric: ExtractedMetric to add
        """
        if metric.metric_type == MetricType.PERFORMANCE:
            metric_name = metric.metadata.get("metric_name", "")
            
            if metric_name == "memory_search_time_ms":
                aggregated.memory_search_times_ms.append(float(metric.value))
            elif metric_name == "context_execution_time_s":
                aggregated.context_execution_times_s.append(float(metric.value))
            elif metric_name == "ai_planning_time_ms":
                aggregated.ai_planning_times_ms.append(float(metric.value))
            elif metric_name == "total_orchestration_time_s":
                aggregated.total_orchestration_times_s.append(float(metric.value))
            elif metric_name == "cache_lookup_time_ms":
                aggregated.cache_lookup_times_ms.append(float(metric.value))
            elif metric_name == "database_query_time_ms":
                aggregated.database_query_times_ms.append(float(metric.value))
            elif metric_name == "response_generation_time_s":
                aggregated.response_generation_times_s.append(float(metric.value))
        
        elif metric.metric_type == MetricType.CONTEXT_STRATEGY:
            strategy = metric.metadata.get("strategy", str(metric.value))
            aggregated.context_strategies.append(strategy)
            
            confidence = metric.metadata.get("confidence")
            if confidence is not None:
                aggregated.strategy_confidences.append(float(confidence))
        
        elif metric.metric_type == MetricType.MEMORY_SEARCH:
            if "query" in metric.metadata:
                aggregated.memory_search_queries.append(metric.metadata["query"])
            elif "results_count" in metric.metadata:
                aggregated.memory_search_results.append(int(metric.value))
            elif "filter_ratio" in metric.metadata:
                aggregated.memory_filter_ratios.append(float(metric.metadata["filter_ratio"]))
            elif "relevance_threshold" in metric.metadata:
                aggregated.relevance_thresholds.append(float(metric.value))
        
        elif metric.metric_type == MetricType.CACHE_HIT:
            cache_result = metric.metadata.get("cache_result", "miss")
            if cache_result == "hit":
                aggregated.cache_hits += 1
            else:
                aggregated.cache_misses += 1
            
            query = metric.metadata.get("query")
            if query:
                aggregated.cache_queries.append(query)
        
        elif metric.metric_type == MetricType.ORCHESTRATION:
            phase = metric.metadata.get("phase")
            if phase:
                aggregated.orchestration_phases.append(phase)
            
            step = metric.metadata.get("step")
            if step:
                aggregated.processing_steps.append(step)
            
            user_id = metric.metadata.get("user_id")
            if user_id:
                aggregated.user_sessions.append(user_id)
        
        elif metric.metric_type == MetricType.ERROR:
            error_message = metric.metadata.get("error_message", str(metric.value))
            aggregated.errors.append(error_message)
    
    def parse_log_files_batch(
        self,
        log_file_paths: List[Union[str, Path]],
        combine_results: bool = True
    ) -> Union[tuple[AggregatedMetrics, LogParsingStats], List[tuple[AggregatedMetrics, LogParsingStats]]]:
        """
        Parse multiple log files.
        
        Args:
            log_file_paths: List of paths to log files
            combine_results: Whether to combine results from all files
            
        Returns:
            Combined results if combine_results=True, otherwise list of individual results
        """
        if combine_results:
            combined_metrics = AggregatedMetrics()
            combined_stats = LogParsingStats()
            
            for log_path in log_file_paths:
                try:
                    metrics, stats = self.parse_log_file(log_path)
                    
                    # Combine metrics
                    self._combine_aggregated_metrics(combined_metrics, metrics)
                    
                    # Combine stats
                    combined_stats.total_lines_processed += stats.total_lines_processed
                    combined_stats.metrics_extracted += stats.metrics_extracted
                    combined_stats.parsing_errors += stats.parsing_errors
                    combined_stats.unmatched_lines += stats.unmatched_lines
                    combined_stats.processing_time_seconds += stats.processing_time_seconds
                    
                except Exception as e:
                    logger.error(f"Failed to parse {log_path}: {e}")
                    continue
            
            return combined_metrics, combined_stats
        
        else:
            results = []
            for log_path in log_file_paths:
                try:
                    result = self.parse_log_file(log_path)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to parse {log_path}: {e}")
                    continue
            
            return results
    
    def _combine_aggregated_metrics(self, target: AggregatedMetrics, source: AggregatedMetrics) -> None:
        """Combine two AggregatedMetrics objects"""
        target.memory_search_times_ms.extend(source.memory_search_times_ms)
        target.context_execution_times_s.extend(source.context_execution_times_s)
        target.ai_planning_times_ms.extend(source.ai_planning_times_ms)
        target.total_orchestration_times_s.extend(source.total_orchestration_times_s)
        target.cache_lookup_times_ms.extend(source.cache_lookup_times_ms)
        target.database_query_times_ms.extend(source.database_query_times_ms)
        target.response_generation_times_s.extend(source.response_generation_times_s)
        
        target.context_strategies.extend(source.context_strategies)
        target.strategy_confidences.extend(source.strategy_confidences)
        
        target.memory_search_queries.extend(source.memory_search_queries)
        target.memory_search_results.extend(source.memory_search_results)
        target.memory_filter_ratios.extend(source.memory_filter_ratios)
        target.relevance_thresholds.extend(source.relevance_thresholds)
        
        target.cache_hits += source.cache_hits
        target.cache_misses += source.cache_misses
        target.cache_queries.extend(source.cache_queries)
        
        target.orchestration_phases.extend(source.orchestration_phases)
        target.processing_steps.extend(source.processing_steps)
        target.user_sessions.extend(source.user_sessions)
        
        target.errors.extend(source.errors)


# Convenience functions
def parse_log_file(log_file_path: Union[str, Path]) -> tuple[AggregatedMetrics, LogParsingStats]:
    """
    Convenience function to parse a single log file.
    
    Args:
        log_file_path: Path to log file
        
    Returns:
        Tuple of (aggregated metrics, parsing statistics)
    """
    parser = LogParser()
    return parser.parse_log_file(log_file_path)


def parse_log_text(log_text: str) -> tuple[AggregatedMetrics, LogParsingStats]:
    """
    Convenience function to parse log text.
    
    Args:
        log_text: Raw log content as string
        
    Returns:
        Tuple of (aggregated metrics, parsing statistics)
    """
    parser = LogParser()
    return parser.parse_log_text(log_text)