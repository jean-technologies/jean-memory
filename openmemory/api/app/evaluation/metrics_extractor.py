"""
Metrics Extraction Patterns for Log Analysis

Defines regex patterns and extraction logic for parsing Jean Memory service logs
to extract performance metrics, context strategies, and orchestration details.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Pattern, Union
from enum import Enum


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be extracted from logs"""
    PERFORMANCE = "performance"
    CONTEXT_STRATEGY = "context_strategy"
    MEMORY_SEARCH = "memory_search"
    CACHE_HIT = "cache_hit"
    ORCHESTRATION = "orchestration"
    ERROR = "error"


@dataclass
class ExtractedMetric:
    """Single extracted metric from log analysis"""
    metric_type: MetricType
    timestamp: Optional[datetime]
    value: Union[str, float, int, bool]
    raw_line: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "metric_type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "value": self.value,
            "raw_line": self.raw_line,
            "metadata": self.metadata
        }


@dataclass
class LogParsingStats:
    """Statistics about log parsing process"""
    total_lines_processed: int = 0
    metrics_extracted: int = 0
    parsing_errors: int = 0
    unmatched_lines: int = 0
    processing_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "total_lines_processed": self.total_lines_processed,
            "metrics_extracted": self.metrics_extracted,
            "parsing_errors": self.parsing_errors,
            "unmatched_lines": self.unmatched_lines,
            "processing_time_seconds": self.processing_time_seconds,
            "extraction_rate": self.metrics_extracted / self.total_lines_processed if self.total_lines_processed > 0 else 0
        }


class MetricsExtractor:
    """
    Extracts performance metrics from Jean Memory service logs.
    
    Uses regex patterns to identify and parse different types of metrics
    from log lines, handling various log formats and error conditions.
    """
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        self.stats = LogParsingStats()
        
    def _compile_patterns(self) -> Dict[MetricType, List[Pattern]]:
        """
        Compile regex patterns for different metric types.
        
        Returns:
            Dictionary mapping metric types to compiled regex patterns
        """
        patterns = {
            # Performance metrics with [PERF] tags
            MetricType.PERFORMANCE: [
                # [PERF] Memory search took 245ms (found 12 memories)
                re.compile(r'\[PERF\]\s+Memory search took (\d+(?:\.\d+)?)ms\s*\(found (\d+) memories\)', re.IGNORECASE),
                
                # [PERF] Context execution: 1.2s
                re.compile(r'\[PERF\]\s+Context execution:\s*(\d+(?:\.\d+)?)s', re.IGNORECASE),
                
                # [PERF] AI planning time: 850ms
                re.compile(r'\[PERF\]\s+AI planning time:\s*(\d+(?:\.\d+)?)ms', re.IGNORECASE),
                
                # [PERF] Total orchestration time: 3.4s
                re.compile(r'\[PERF\]\s+Total orchestration time:\s*(\d+(?:\.\d+)?)s', re.IGNORECASE),
                
                # [PERF] Cache lookup: 15ms (hit)
                re.compile(r'\[PERF\]\s+Cache lookup:\s*(\d+(?:\.\d+)?)ms\s*\((hit|miss)\)', re.IGNORECASE),
                
                # [PERF] Database query took 125ms
                re.compile(r'\[PERF\]\s+Database query took\s*(\d+(?:\.\d+)?)ms', re.IGNORECASE),
                
                # [PERF] Response generation: 2.1s
                re.compile(r'\[PERF\]\s+Response generation:\s*(\d+(?:\.\d+)?)s', re.IGNORECASE),
            ],
            
            # Context engineering strategy selection
            MetricType.CONTEXT_STRATEGY: [
                # Context strategy: deep_understanding (confidence: 0.85)
                re.compile(r'Context strategy:\s*(\w+)\s*\(confidence:\s*(\d+(?:\.\d+)?)\)', re.IGNORECASE),
                
                # Selected context approach: balanced_search
                re.compile(r'Selected context approach:\s*(\w+)', re.IGNORECASE),
                
                # Context engineering mode: comprehensive
                re.compile(r'Context engineering mode:\s*(\w+)', re.IGNORECASE),
                
                # Using context strategy: quick_facts
                re.compile(r'Using context strategy:\s*(\w+)', re.IGNORECASE),
            ],
            
            # Memory search patterns
            MetricType.MEMORY_SEARCH: [
                # Searching memories with query: "user preferences"
                re.compile(r'Searching memories with query:\s*["\']([^"\']+)["\']', re.IGNORECASE),
                
                # Memory search returned 15 results
                re.compile(r'Memory search returned\s*(\d+)\s*results?', re.IGNORECASE),
                
                # Filtering memories: 45 -> 12 relevant
                re.compile(r'Filtering memories:\s*(\d+)\s*->\s*(\d+)\s*relevant', re.IGNORECASE),
                
                # Memory relevance scoring completed (threshold: 0.7)
                re.compile(r'Memory relevance scoring completed\s*\(threshold:\s*(\d+(?:\.\d+)?)\)', re.IGNORECASE),
            ],
            
            # Cache hit/miss patterns
            MetricType.CACHE_HIT: [
                # Cache hit for query hash: abc123def
                re.compile(r'Cache (hit|miss) for query hash:\s*(\w+)', re.IGNORECASE),
                
                # Memory cache: HIT (query: "user projects")
                re.compile(r'Memory cache:\s*(HIT|MISS)\s*\(query:\s*["\']([^"\']+)["\']\)', re.IGNORECASE),
                
                # Context cache hit: reducing computation time
                re.compile(r'Context cache (hit|miss):', re.IGNORECASE),
            ],
            
            # Orchestration patterns
            MetricType.ORCHESTRATION: [
                # Starting orchestration for user: fa97efb5-410d-4806-b137-8cf13b6cb464
                re.compile(r'Starting orchestration for user:\s*([a-f0-9-]+)', re.IGNORECASE),
                
                # Orchestration phase: memory_retrieval
                re.compile(r'Orchestration phase:\s*(\w+)', re.IGNORECASE),
                
                # Orchestration completed successfully in 4.2s
                re.compile(r'Orchestration completed\s+(\w+)\s+in\s+(\d+(?:\.\d+)?)s', re.IGNORECASE),
                
                # Processing step: context_synthesis (2/5)
                re.compile(r'Processing step:\s*(\w+)\s*\((\d+)/(\d+)\)', re.IGNORECASE),
            ],
            
            # Error patterns
            MetricType.ERROR: [
                # ERROR: Memory search failed
                re.compile(r'ERROR:\s*(.+)', re.IGNORECASE),
                
                # [ERROR] Context generation timeout
                re.compile(r'\[ERROR\]\s*(.+)', re.IGNORECASE),
                
                # Exception in orchestration: TimeoutError
                re.compile(r'Exception in orchestration:\s*(\w+)', re.IGNORECASE),
            ]
        }
        
        return patterns
    
    def extract_timestamp(self, log_line: str) -> Optional[datetime]:
        """
        Extract timestamp from log line.
        
        Args:
            log_line: Raw log line
            
        Returns:
            Parsed datetime or None if not found
        """
        # Common timestamp patterns
        timestamp_patterns = [
            # 2025-08-16T16:20:51.406
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?)',
            
            # 2025-08-16 16:20:51.406
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d{3})?)',
            
            # Aug 16 16:20:51
            r'([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, log_line)
            if match:
                timestamp_str = match.group(1)
                
                try:
                    # Try ISO format first
                    if 'T' in timestamp_str:
                        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    elif '-' in timestamp_str:
                        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        # Handle other formats as needed
                        return None
                except ValueError:
                    continue
        
        return None
    
    def extract_metrics_from_line(self, log_line: str) -> List[ExtractedMetric]:
        """
        Extract metrics from a single log line.
        
        Args:
            log_line: Single line from log file
            
        Returns:
            List of extracted metrics (can be empty)
        """
        metrics = []
        timestamp = self.extract_timestamp(log_line)
        
        # Try each metric type
        for metric_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = pattern.search(log_line)
                if match:
                    try:
                        metric = self._parse_metric_match(
                            metric_type, match, log_line, timestamp
                        )
                        if metric:
                            metrics.append(metric)
                    except Exception as e:
                        logger.warning(f"Failed to parse metric from line: {log_line[:100]}... Error: {e}")
                        self.stats.parsing_errors += 1
        
        return metrics
    
    def _parse_metric_match(
        self,
        metric_type: MetricType,
        match: re.Match,
        log_line: str,
        timestamp: Optional[datetime]
    ) -> Optional[ExtractedMetric]:
        """
        Parse a regex match into an ExtractedMetric.
        
        Args:
            metric_type: Type of metric being extracted
            match: Regex match object
            log_line: Original log line
            timestamp: Extracted timestamp
            
        Returns:
            ExtractedMetric or None if parsing fails
        """
        groups = match.groups()
        metadata = {}
        
        if metric_type == MetricType.PERFORMANCE:
            # Handle different performance metric patterns
            if "Memory search took" in log_line:
                # [PERF] Memory search took 245ms (found 12 memories)
                value = float(groups[0])  # Time in ms
                metadata = {
                    "metric_name": "memory_search_time_ms",
                    "memories_found": int(groups[1]) if len(groups) > 1 else None
                }
            elif "Context execution" in log_line:
                # [PERF] Context execution: 1.2s
                value = float(groups[0])  # Time in seconds
                metadata = {"metric_name": "context_execution_time_s"}
            elif "AI planning time" in log_line:
                # [PERF] AI planning time: 850ms
                value = float(groups[0])  # Time in ms
                metadata = {"metric_name": "ai_planning_time_ms"}
            elif "Total orchestration time" in log_line:
                # [PERF] Total orchestration time: 3.4s
                value = float(groups[0])  # Time in seconds
                metadata = {"metric_name": "total_orchestration_time_s"}
            elif "Cache lookup" in log_line:
                # [PERF] Cache lookup: 15ms (hit)
                value = float(groups[0])  # Time in ms
                metadata = {
                    "metric_name": "cache_lookup_time_ms",
                    "cache_result": groups[1].lower() if len(groups) > 1 else None
                }
            elif "Database query took" in log_line:
                # [PERF] Database query took 125ms
                value = float(groups[0])  # Time in ms
                metadata = {"metric_name": "database_query_time_ms"}
            elif "Response generation" in log_line:
                # [PERF] Response generation: 2.1s
                value = float(groups[0])  # Time in seconds
                metadata = {"metric_name": "response_generation_time_s"}
            else:
                return None
        
        elif metric_type == MetricType.CONTEXT_STRATEGY:
            # Context strategy selection
            if len(groups) >= 2:
                # Context strategy: deep_understanding (confidence: 0.85)
                value = groups[0]  # Strategy name
                metadata = {
                    "strategy": groups[0],
                    "confidence": float(groups[1]) if groups[1] else None
                }
            else:
                # Simple strategy selection
                value = groups[0]
                metadata = {"strategy": groups[0]}
        
        elif metric_type == MetricType.MEMORY_SEARCH:
            if "query:" in log_line:
                # Searching memories with query: "user preferences"
                value = groups[0]  # Query string
                metadata = {"query": groups[0]}
            elif "returned" in log_line:
                # Memory search returned 15 results
                value = int(groups[0])  # Number of results
                metadata = {"results_count": int(groups[0])}
            elif "Filtering memories" in log_line:
                # Filtering memories: 45 -> 12 relevant
                value = {
                    "total": int(groups[0]),
                    "relevant": int(groups[1])
                }
                metadata = {
                    "total_memories": int(groups[0]),
                    "relevant_memories": int(groups[1]),
                    "filter_ratio": int(groups[1]) / int(groups[0]) if int(groups[0]) > 0 else 0
                }
            elif "threshold" in log_line:
                # Memory relevance scoring completed (threshold: 0.7)
                value = float(groups[0])  # Threshold value
                metadata = {"relevance_threshold": float(groups[0])}
            else:
                return None
        
        elif metric_type == MetricType.CACHE_HIT:
            if len(groups) >= 2:
                # Cache hit/miss with additional info
                value = groups[0].lower() == "hit"  # Boolean hit/miss
                metadata = {
                    "cache_result": groups[0].lower(),
                    "query_hash": groups[1] if "hash" in log_line else None,
                    "query": groups[1] if "query" in log_line else None
                }
            else:
                # Simple hit/miss
                value = groups[0].lower() == "hit"
                metadata = {"cache_result": groups[0].lower()}
        
        elif metric_type == MetricType.ORCHESTRATION:
            if "Starting orchestration" in log_line:
                # Starting orchestration for user: fa97efb5-410d-4806-b137-8cf13b6cb464
                value = groups[0]  # User ID
                metadata = {"user_id": groups[0], "event": "start"}
            elif "Orchestration phase" in log_line:
                # Orchestration phase: memory_retrieval
                value = groups[0]  # Phase name
                metadata = {"phase": groups[0]}
            elif "completed" in log_line and len(groups) >= 2:
                # Orchestration completed successfully in 4.2s
                value = float(groups[1])  # Time in seconds
                metadata = {
                    "status": groups[0],
                    "duration_s": float(groups[1]),
                    "event": "complete"
                }
            elif "Processing step" in log_line and len(groups) >= 3:
                # Processing step: context_synthesis (2/5)
                value = groups[0]  # Step name
                metadata = {
                    "step": groups[0],
                    "current": int(groups[1]),
                    "total": int(groups[2]),
                    "progress": int(groups[1]) / int(groups[2])
                }
            else:
                return None
        
        elif metric_type == MetricType.ERROR:
            # Error messages
            value = groups[0]  # Error message
            metadata = {"error_message": groups[0]}
        
        else:
            return None
        
        return ExtractedMetric(
            metric_type=metric_type,
            timestamp=timestamp,
            value=value,
            raw_line=log_line.strip(),
            metadata=metadata
        )
    
    def reset_stats(self) -> None:
        """Reset parsing statistics"""
        self.stats = LogParsingStats()
    
    def get_stats(self) -> LogParsingStats:
        """Get current parsing statistics"""
        return self.stats