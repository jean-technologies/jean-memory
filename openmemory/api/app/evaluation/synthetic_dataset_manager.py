"""
Synthetic Test Dataset Management Suite
=====================================

Manages storage, retrieval, and organization of synthetic test cases
for Jean Memory evaluation. Provides dataset versioning, filtering,
and export capabilities.

Part of Task 3: Synthetic Test Data Generator
"""

import asyncio
import json
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
import uuid

# Import Task 3 components
from .synthetic_data_generator import (
    SyntheticTestCase, 
    ReasoningType, 
    DifficultyLevel,
    PersonaType,
    ConversationDecisionPath
)
from .synthetic_quality_validator import QualityValidationResult

logger = logging.getLogger(__name__)


@dataclass
class DatasetMetadata:
    """Metadata for a synthetic dataset"""
    id: str
    name: str
    description: str
    creation_timestamp: datetime
    version: str
    test_case_count: int
    reasoning_type_distribution: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    persona_distribution: Dict[str, int]
    quality_stats: Dict[str, float]
    tags: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "version": self.version,
            "test_case_count": self.test_case_count,
            "reasoning_type_distribution": self.reasoning_type_distribution,
            "difficulty_distribution": self.difficulty_distribution,
            "persona_distribution": self.persona_distribution,
            "quality_stats": self.quality_stats,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DatasetMetadata':
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            creation_timestamp=datetime.fromisoformat(data["creation_timestamp"]),
            version=data["version"],
            test_case_count=data["test_case_count"],
            reasoning_type_distribution=data["reasoning_type_distribution"],
            difficulty_distribution=data["difficulty_distribution"],
            persona_distribution=data["persona_distribution"],
            quality_stats=data["quality_stats"],
            tags=data["tags"]
        )


@dataclass
class DatasetFilter:
    """Filter criteria for dataset queries"""
    reasoning_types: Optional[List[ReasoningType]] = None
    difficulties: Optional[List[DifficultyLevel]] = None
    personas: Optional[List[PersonaType]] = None
    decision_paths: Optional[List[ConversationDecisionPath]] = None
    min_quality_score: Optional[float] = None
    max_quality_score: Optional[float] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: Optional[int] = None
    
    def matches(self, test_case: SyntheticTestCase) -> bool:
        """Check if test case matches filter criteria"""
        if self.reasoning_types and test_case.reasoning_type not in self.reasoning_types:
            return False
        if self.difficulties and test_case.difficulty not in self.difficulties:
            return False
        if self.personas and test_case.persona not in self.personas:
            return False
        if self.decision_paths and test_case.decision_path not in self.decision_paths:
            return False
        if self.min_quality_score and (test_case.quality_score or 0) < self.min_quality_score:
            return False
        if self.max_quality_score and (test_case.quality_score or 10) > self.max_quality_score:
            return False
        if self.created_after and test_case.generation_timestamp < self.created_after:
            return False
        if self.created_before and test_case.generation_timestamp > self.created_before:
            return False
        return True


class SyntheticDatasetManager:
    """
    Manages synthetic test datasets with storage, versioning, and retrieval capabilities.
    Integrates with Task 1-2 storage infrastructure.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize dataset manager"""
        self.storage_path = Path(storage_path or os.getenv("SYNTHETIC_DATASET_PATH", "./synthetic_datasets"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Storage structure
        self.datasets_dir = self.storage_path / "datasets"
        self.metadata_dir = self.storage_path / "metadata"
        self.exports_dir = self.storage_path / "exports"
        
        for dir_path in [self.datasets_dir, self.metadata_dir, self.exports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for performance
        self._dataset_cache: Dict[str, List[SyntheticTestCase]] = {}
        self._metadata_cache: Dict[str, DatasetMetadata] = {}
        
        logger.info(f"📁 Synthetic Dataset Manager initialized at {self.storage_path}")
    
    async def create_dataset(
        self,
        name: str,
        test_cases: List[SyntheticTestCase],
        description: str = "",
        tags: List[str] = None,
        version: str = "1.0"
    ) -> str:
        """Create a new dataset from test cases"""
        
        dataset_id = str(uuid.uuid4())
        tags = tags or []
        
        logger.info(f"📁 Creating dataset '{name}' with {len(test_cases)} test cases")
        
        # Calculate statistics
        metadata = self._calculate_metadata(
            dataset_id, name, description, test_cases, tags, version
        )
        
        # Save test cases
        dataset_file = self.datasets_dir / f"{dataset_id}.json"
        test_cases_data = [tc.to_dict() for tc in test_cases]
        
        with open(dataset_file, 'w') as f:
            json.dump(test_cases_data, f, indent=2)
        
        # Save metadata
        metadata_file = self.metadata_dir / f"{dataset_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Update cache
        self._dataset_cache[dataset_id] = test_cases
        self._metadata_cache[dataset_id] = metadata
        
        logger.info(f"✅ Dataset '{name}' created with ID {dataset_id[:8]}")
        return dataset_id
    
    async def load_dataset(self, dataset_id: str) -> List[SyntheticTestCase]:
        """Load test cases from a dataset"""
        
        # Check cache first
        if dataset_id in self._dataset_cache:
            return self._dataset_cache[dataset_id]
        
        dataset_file = self.datasets_dir / f"{dataset_id}.json"
        if not dataset_file.exists():
            raise ValueError(f"Dataset {dataset_id} not found")
        
        with open(dataset_file, 'r') as f:
            test_cases_data = json.load(f)
        
        test_cases = [SyntheticTestCase.from_dict(data) for data in test_cases_data]
        
        # Cache for future use
        self._dataset_cache[dataset_id] = test_cases
        
        logger.info(f"📁 Loaded dataset {dataset_id[:8]} with {len(test_cases)} test cases")
        return test_cases
    
    async def get_dataset_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get metadata for a dataset"""
        
        # Check cache first
        if dataset_id in self._metadata_cache:
            return self._metadata_cache[dataset_id]
        
        metadata_file = self.metadata_dir / f"{dataset_id}.json"
        if not metadata_file.exists():
            raise ValueError(f"Dataset metadata {dataset_id} not found")
        
        with open(metadata_file, 'r') as f:
            metadata_data = json.load(f)
        
        metadata = DatasetMetadata.from_dict(metadata_data)
        
        # Cache for future use
        self._metadata_cache[dataset_id] = metadata
        
        return metadata
    
    async def list_datasets(self) -> List[DatasetMetadata]:
        """List all available datasets"""
        
        datasets = []
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            dataset_id = metadata_file.stem
            try:
                metadata = await self.get_dataset_metadata(dataset_id)
                datasets.append(metadata)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load metadata for dataset {dataset_id}: {e}")
        
        # Sort by creation time (newest first)
        datasets.sort(key=lambda d: d.creation_timestamp, reverse=True)
        
        return datasets
    
    async def filter_test_cases(
        self, 
        dataset_id: str, 
        filter_criteria: DatasetFilter
    ) -> List[SyntheticTestCase]:
        """Filter test cases from a dataset based on criteria"""
        
        test_cases = await self.load_dataset(dataset_id)
        filtered_cases = []
        
        for test_case in test_cases:
            if filter_criteria.matches(test_case):
                filtered_cases.append(test_case)
                
                # Apply limit if specified
                if filter_criteria.limit and len(filtered_cases) >= filter_criteria.limit:
                    break
        
        logger.info(f"🔍 Filtered {len(filtered_cases)}/{len(test_cases)} test cases from dataset {dataset_id[:8]}")
        return filtered_cases
    
    async def merge_datasets(
        self,
        dataset_ids: List[str],
        new_name: str,
        description: str = "",
        tags: List[str] = None,
        deduplicate: bool = True
    ) -> str:
        """Merge multiple datasets into a new dataset"""
        
        logger.info(f"🔗 Merging {len(dataset_ids)} datasets into '{new_name}'")
        
        all_test_cases = []
        seen_ids = set() if deduplicate else None
        
        for dataset_id in dataset_ids:
            test_cases = await self.load_dataset(dataset_id)
            
            for test_case in test_cases:
                if deduplicate:
                    if test_case.id in seen_ids:
                        continue
                    seen_ids.add(test_case.id)
                
                all_test_cases.append(test_case)
        
        # Create merged dataset
        merged_id = await self.create_dataset(
            name=new_name,
            test_cases=all_test_cases,
            description=description,
            tags=(tags or []) + ["merged"],
            version="1.0"
        )
        
        logger.info(f"✅ Merged dataset created with {len(all_test_cases)} test cases")
        return merged_id
    
    async def export_dataset(
        self,
        dataset_id: str,
        format: str = "json",
        filter_criteria: Optional[DatasetFilter] = None,
        include_metadata: bool = True
    ) -> str:
        """Export dataset to various formats"""
        
        # Load and filter test cases
        if filter_criteria:
            test_cases = await self.filter_test_cases(dataset_id, filter_criteria)
        else:
            test_cases = await self.load_dataset(dataset_id)
        
        metadata = await self.get_dataset_metadata(dataset_id)
        
        # Generate export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{metadata.name}_{timestamp}.{format}"
        export_path = self.exports_dir / filename
        
        if format.lower() == "json":
            export_data = {
                "metadata": metadata.to_dict() if include_metadata else None,
                "test_cases": [tc.to_dict() for tc in test_cases]
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            with open(export_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                headers = [
                    "id", "reasoning_type", "difficulty", "persona", "decision_path",
                    "query", "expected_response", "memory_count", "quality_score",
                    "generation_timestamp"
                ]
                writer.writerow(headers)
                
                # Test cases
                for tc in test_cases:
                    writer.writerow([
                        tc.id, tc.reasoning_type.value, tc.difficulty.value,
                        tc.persona.value, tc.decision_path.value,
                        tc.query, tc.expected_response, tc.expected_memory_count,
                        tc.quality_score, tc.generation_timestamp.isoformat()
                    ])
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"📤 Exported {len(test_cases)} test cases to {export_path}")
        return str(export_path)
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and its metadata"""
        
        dataset_file = self.datasets_dir / f"{dataset_id}.json"
        metadata_file = self.metadata_dir / f"{dataset_id}.json"
        
        deleted = False
        
        if dataset_file.exists():
            dataset_file.unlink()
            deleted = True
        
        if metadata_file.exists():
            metadata_file.unlink()
            deleted = True
        
        # Remove from cache
        self._dataset_cache.pop(dataset_id, None)
        self._metadata_cache.pop(dataset_id, None)
        
        if deleted:
            logger.info(f"🗑️ Deleted dataset {dataset_id[:8]}")
        
        return deleted
    
    async def get_dataset_stats(self) -> Dict:
        """Get overall statistics about all datasets"""
        
        datasets = await self.list_datasets()
        
        total_test_cases = sum(d.test_case_count for d in datasets)
        total_datasets = len(datasets)
        
        # Aggregate statistics
        reasoning_type_totals = {}
        difficulty_totals = {}
        persona_totals = {}
        quality_scores = []
        
        for dataset in datasets:
            for rt, count in dataset.reasoning_type_distribution.items():
                reasoning_type_totals[rt] = reasoning_type_totals.get(rt, 0) + count
            
            for diff, count in dataset.difficulty_distribution.items():
                difficulty_totals[diff] = difficulty_totals.get(diff, 0) + count
            
            for persona, count in dataset.persona_distribution.items():
                persona_totals[persona] = persona_totals.get(persona, 0) + count
            
            if "avg_quality_score" in dataset.quality_stats:
                quality_scores.append(dataset.quality_stats["avg_quality_score"])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "total_datasets": total_datasets,
            "total_test_cases": total_test_cases,
            "avg_test_cases_per_dataset": total_test_cases / total_datasets if total_datasets > 0 else 0,
            "reasoning_type_distribution": reasoning_type_totals,
            "difficulty_distribution": difficulty_totals,
            "persona_distribution": persona_totals,
            "avg_quality_score": avg_quality,
            "storage_path": str(self.storage_path)
        }
    
    def _calculate_metadata(
        self,
        dataset_id: str,
        name: str,
        description: str,
        test_cases: List[SyntheticTestCase],
        tags: List[str],
        version: str
    ) -> DatasetMetadata:
        """Calculate metadata from test cases"""
        
        # Distribution calculations
        reasoning_types = {}
        difficulties = {}
        personas = {}
        quality_scores = []
        
        for tc in test_cases:
            reasoning_types[tc.reasoning_type.value] = reasoning_types.get(tc.reasoning_type.value, 0) + 1
            difficulties[tc.difficulty.value] = difficulties.get(tc.difficulty.value, 0) + 1
            personas[tc.persona.value] = personas.get(tc.persona.value, 0) + 1
            
            if tc.quality_score is not None:
                quality_scores.append(tc.quality_score)
        
        # Quality statistics
        quality_stats = {}
        if quality_scores:
            quality_stats = {
                "avg_quality_score": sum(quality_scores) / len(quality_scores),
                "min_quality_score": min(quality_scores),
                "max_quality_score": max(quality_scores),
                "quality_score_count": len(quality_scores)
            }
        
        return DatasetMetadata(
            id=dataset_id,
            name=name,
            description=description,
            creation_timestamp=datetime.now(),
            version=version,
            test_case_count=len(test_cases),
            reasoning_type_distribution=reasoning_types,
            difficulty_distribution=difficulties,
            persona_distribution=personas,
            quality_stats=quality_stats,
            tags=tags
        )
    
    async def cleanup_storage(self, keep_latest_n: int = 10) -> int:
        """Clean up old datasets, keeping only the latest N"""
        
        datasets = await self.list_datasets()
        
        if len(datasets) <= keep_latest_n:
            return 0
        
        # Sort by creation time and identify old datasets
        datasets.sort(key=lambda d: d.creation_timestamp, reverse=True)
        old_datasets = datasets[keep_latest_n:]
        
        deleted_count = 0
        for dataset in old_datasets:
            if await self.delete_dataset(dataset.id):
                deleted_count += 1
        
        logger.info(f"🧹 Cleaned up {deleted_count} old datasets")
        return deleted_count


# Global dataset manager instance
_dataset_manager = None

def get_dataset_manager() -> SyntheticDatasetManager:
    """Get global dataset manager instance"""
    global _dataset_manager
    if _dataset_manager is None:
        _dataset_manager = SyntheticDatasetManager()
    return _dataset_manager


# Convenience functions
async def create_test_dataset(
    name: str,
    test_cases: List[SyntheticTestCase],
    description: str = "",
    tags: List[str] = None
) -> str:
    """Create a new test dataset (convenience function)"""
    manager = get_dataset_manager()
    return await manager.create_dataset(name, test_cases, description, tags)


async def load_test_dataset(dataset_id: str) -> List[SyntheticTestCase]:
    """Load test cases from a dataset (convenience function)"""
    manager = get_dataset_manager()
    return await manager.load_dataset(dataset_id)


async def filter_dataset(
    dataset_id: str,
    reasoning_types: Optional[List[ReasoningType]] = None,
    difficulties: Optional[List[DifficultyLevel]] = None,
    min_quality: Optional[float] = None,
    limit: Optional[int] = None
) -> List[SyntheticTestCase]:
    """Filter dataset with common criteria (convenience function)"""
    manager = get_dataset_manager()
    filter_criteria = DatasetFilter(
        reasoning_types=reasoning_types,
        difficulties=difficulties,
        min_quality_score=min_quality,
        limit=limit
    )
    return await manager.filter_test_cases(dataset_id, filter_criteria)


async def export_test_dataset(
    dataset_id: str,
    format: str = "json",
    filter_criteria: Optional[DatasetFilter] = None
) -> str:
    """Export dataset to file (convenience function)"""
    manager = get_dataset_manager()
    return await manager.export_dataset(dataset_id, format, filter_criteria)