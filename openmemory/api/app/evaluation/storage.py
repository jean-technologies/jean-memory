"""
Metrics Storage Backend
========================

Handles persistent storage of evaluation metrics.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def store(self, metric: Dict[str, Any]):
        """Store a single metric."""
        pass
    
    @abstractmethod
    def store_batch(self, metrics: List[Dict[str, Any]]):
        """Store multiple metrics."""
        pass
    
    @abstractmethod
    def retrieve(self, start_time: Optional[datetime] = None, 
                 end_time: Optional[datetime] = None,
                 function_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve metrics based on filters."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all stored metrics."""
        pass


class JSONStorageBackend(StorageBackend):
    """
    JSON file-based storage backend for evaluation metrics.
    Simple and portable, suitable for development and testing.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize JSON storage backend.
        
        Args:
            storage_path: Path to storage directory (defaults to ./evaluation_metrics)
        """
        self.storage_path = Path(storage_path or os.getenv(
            "EVALUATION_STORAGE_PATH", 
            "./evaluation_metrics"
        ))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create daily files for metrics
        self._current_file = None
        self._current_date = None
    
    def _get_file_path(self) -> Path:
        """Get the current metrics file path."""
        today = datetime.utcnow().date()
        if today != self._current_date:
            self._current_date = today
            self._current_file = self.storage_path / f"metrics_{today.isoformat()}.jsonl"
        return self._current_file
    
    def store(self, metric: Dict[str, Any]):
        """Store a single metric to JSON file."""
        try:
            file_path = self._get_file_path()
            with open(file_path, "a") as f:
                f.write(json.dumps(metric) + "\n")
        except Exception as e:
            logger.error(f"Failed to store metric to JSON: {e}")
    
    def store_batch(self, metrics: List[Dict[str, Any]]):
        """Store multiple metrics to JSON file."""
        if not metrics:
            return
        
        try:
            file_path = self._get_file_path()
            with open(file_path, "a") as f:
                for metric in metrics:
                    f.write(json.dumps(metric) + "\n")
        except Exception as e:
            logger.error(f"Failed to store metrics batch to JSON: {e}")
    
    def retrieve(self, start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 function_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve metrics from JSON files based on filters."""
        metrics = []
        
        try:
            # Get all metric files
            files = sorted(self.storage_path.glob("metrics_*.jsonl"))
            
            for file_path in files:
                # Check if file is in date range
                file_date_str = file_path.stem.replace("metrics_", "")
                file_date = datetime.fromisoformat(file_date_str).date()
                
                if start_time and file_date < start_time.date():
                    continue
                if end_time and file_date > end_time.date():
                    continue
                
                # Read metrics from file
                with open(file_path, "r") as f:
                    for line in f:
                        try:
                            metric = json.loads(line.strip())
                            
                            # Apply filters
                            if function_name and metric.get("function_name") != function_name:
                                continue
                            
                            metric_time = datetime.fromisoformat(
                                metric.get("timestamp", "2000-01-01T00:00:00")
                            )
                            if start_time and metric_time < start_time:
                                continue
                            if end_time and metric_time > end_time:
                                continue
                            
                            metrics.append(metric)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in metrics file: {line}")
                            
        except Exception as e:
            logger.error(f"Failed to retrieve metrics from JSON: {e}")
        
        return metrics
    
    def clear(self):
        """Clear all stored metrics."""
        try:
            for file_path in self.storage_path.glob("metrics_*.jsonl"):
                file_path.unlink()
            logger.info("Cleared all evaluation metrics")
        except Exception as e:
            logger.error(f"Failed to clear metrics: {e}")


class PostgreSQLStorageBackend(StorageBackend):
    """
    PostgreSQL storage backend for evaluation metrics.
    Suitable for production environments with existing PostgreSQL infrastructure.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize PostgreSQL storage backend.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self._initialized = False
        
        if not self.connection_string:
            logger.warning("PostgreSQL storage backend initialized without connection string")
    
    def _ensure_table(self):
        """Ensure the metrics table exists."""
        # Implementation would create table if not exists
        # For now, this is a placeholder
        pass
    
    def store(self, metric: Dict[str, Any]):
        """Store a single metric to PostgreSQL."""
        # Placeholder for PostgreSQL implementation
        logger.debug(f"PostgreSQL storage not implemented, metric not stored: {metric.get('function_name')}")
    
    def store_batch(self, metrics: List[Dict[str, Any]]):
        """Store multiple metrics to PostgreSQL."""
        # Placeholder for PostgreSQL implementation
        logger.debug(f"PostgreSQL storage not implemented, {len(metrics)} metrics not stored")
    
    def retrieve(self, start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 function_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve metrics from PostgreSQL based on filters."""
        # Placeholder for PostgreSQL implementation
        return []
    
    def clear(self):
        """Clear all stored metrics from PostgreSQL."""
        # Placeholder for PostgreSQL implementation
        logger.debug("PostgreSQL storage clear not implemented")


class MetricsStorage:
    """
    Main storage interface that delegates to appropriate backend.
    """
    
    def __init__(self):
        """Initialize metrics storage with appropriate backend."""
        storage_backend = os.getenv("EVALUATION_STORAGE", "json").lower()
        
        if storage_backend == "postgres":
            self.backend = PostgreSQLStorageBackend()
        else:  # Default to JSON
            self.backend = JSONStorageBackend()
        
        logger.info(f"Initialized evaluation storage with {storage_backend} backend")
    
    def store(self, metric: Dict[str, Any]):
        """Store a single metric."""
        self.backend.store(metric)
    
    def store_batch(self, metrics: List[Dict[str, Any]]):
        """Store multiple metrics."""
        self.backend.store_batch(metrics)
    
    def retrieve(self, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve metrics based on filters."""
        return self.backend.retrieve(**kwargs)
    
    def clear(self):
        """Clear all stored metrics."""
        self.backend.clear()
    
    def export_report(self, output_path: Optional[str] = None) -> str:
        """
        Export evaluation report in markdown format.
        
        Args:
            output_path: Optional path to save report (defaults to evaluation_report.md)
        
        Returns:
            Path to the generated report
        """
        output_path = output_path or "evaluation_report.md"
        
        try:
            # Retrieve all metrics
            metrics = self.retrieve()
            
            if not metrics:
                report = "# Evaluation Report\n\nNo metrics collected yet.\n"
            else:
                # Group metrics by function
                from collections import defaultdict
                by_function = defaultdict(list)
                for metric in metrics:
                    by_function[metric.get("function_name", "unknown")].append(metric)
                
                # Generate report
                report = f"# Jean Memory Evaluation Report\n\n"
                report += f"Generated: {datetime.utcnow().isoformat()}\n"
                report += f"Total Metrics: {len(metrics)}\n\n"
                
                for function_name, function_metrics in by_function.items():
                    report += f"## {function_name}\n\n"
                    
                    # Calculate statistics
                    latencies = [m.get("latency_ms", 0) for m in function_metrics]
                    success_count = sum(1 for m in function_metrics if m.get("success", False))
                    
                    report += f"- **Calls**: {len(function_metrics)}\n"
                    report += f"- **Success Rate**: {success_count/len(function_metrics)*100:.1f}%\n"
                    
                    if latencies:
                        import statistics
                        report += f"- **Latency (ms)**:\n"
                        report += f"  - Mean: {statistics.mean(latencies):.2f}\n"
                        report += f"  - Median: {statistics.median(latencies):.2f}\n"
                        report += f"  - Min: {min(latencies):.2f}\n"
                        report += f"  - Max: {max(latencies):.2f}\n"
                    
                    # Memory stats if available
                    memory_deltas = [m.get("memory_delta_mb") for m in function_metrics 
                                    if m.get("memory_delta_mb") is not None]
                    if memory_deltas:
                        report += f"- **Memory Usage (MB)**:\n"
                        report += f"  - Mean: {statistics.mean(memory_deltas):.2f}\n"
                        report += f"  - Max: {max(memory_deltas):.2f}\n"
                    
                    report += "\n"
            
            # Save report
            with open(output_path, "w") as f:
                f.write(report)
            
            logger.info(f"Generated evaluation report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate evaluation report: {e}")
            return None