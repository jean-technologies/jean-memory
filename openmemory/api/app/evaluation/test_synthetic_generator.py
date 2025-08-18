"""
Comprehensive Test Suite for Synthetic Test Data Generator
========================================================

Tests for all components of Task 3: Synthetic Test Data Generator
including generation, validation, and dataset management.

Part of Task 3: Synthetic Test Data Generator
"""

import asyncio
import json
import logging
import os
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

# Import Task 3 components
from .synthetic_data_generator import (
    SyntheticDataGeneratorService,
    SyntheticTestCase,
    Memory,
    ReasoningType,
    DifficultyLevel,
    PersonaType,
    ConversationDecisionPath,
    generate_single_test_case,
    generate_test_batch,
    generate_balanced_dataset
)

from .synthetic_quality_validator import (
    SyntheticQualityValidator,
    QualityValidationResult,
    validate_single_test_case,
    validate_test_batch,
    generate_and_validate_batch
)

from .synthetic_dataset_manager import (
    SyntheticDatasetManager,
    DatasetMetadata,
    DatasetFilter,
    create_test_dataset,
    load_test_dataset,
    filter_dataset
)

# Import Task 1-2 infrastructure
from .llm_judge import ReasoningType, LLMProvider

logger = logging.getLogger(__name__)


class TestSyntheticDataGenerator:
    """Test synthetic data generation service"""
    
    @pytest.fixture
    def generator(self):
        """Create generator service for testing"""
        # Enable generation for tests
        os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
        return SyntheticDataGeneratorService()
    
    @pytest.mark.asyncio
    async def test_generator_initialization(self, generator):
        """Test generator initializes correctly"""
        assert generator.generation_enabled
        assert generator.judge_service is not None
        assert generator.default_provider in ["auto", "gemini", "openai"]
        assert generator.batch_size > 0
        assert generator.quality_threshold > 0
    
    @pytest.mark.asyncio
    async def test_single_hop_generation(self, generator):
        """Test single-hop reasoning test case generation"""
        test_case = await generator.generate_test_case(
            ReasoningType.SINGLE_HOP,
            DifficultyLevel.EASY,
            PersonaType.CASUAL
        )
        
        assert test_case.reasoning_type == ReasoningType.SINGLE_HOP
        assert test_case.difficulty == DifficultyLevel.EASY
        assert test_case.persona == PersonaType.CASUAL
        assert test_case.required_hops == 1
        assert len(test_case.memories) >= 1
        assert len(test_case.query) > 0
        assert len(test_case.expected_response) > 0
        assert test_case.generation_timestamp is not None
    
    @pytest.mark.asyncio
    async def test_multi_hop_generation(self, generator):
        """Test multi-hop reasoning test case generation"""
        test_case = await generator.generate_test_case(
            ReasoningType.MULTI_HOP,
            DifficultyLevel.MEDIUM,
            PersonaType.PROFESSIONAL
        )
        
        assert test_case.reasoning_type == ReasoningType.MULTI_HOP
        assert test_case.difficulty == DifficultyLevel.MEDIUM
        assert test_case.required_hops >= 2
        assert len(test_case.memories) >= test_case.required_hops
        assert "connection" in test_case.validation_notes.lower() or "hop" in test_case.validation_notes.lower()
    
    @pytest.mark.asyncio
    async def test_temporal_generation(self, generator):
        """Test temporal reasoning test case generation"""
        test_case = await generator.generate_test_case(
            ReasoningType.TEMPORAL,
            DifficultyLevel.HARD,
            PersonaType.STUDENT
        )
        
        assert test_case.reasoning_type == ReasoningType.TEMPORAL
        assert test_case.temporal_span_days is not None
        assert test_case.temporal_span_days > 0
        
        # Check that memories have meaningful temporal distribution
        timestamps = [mem.timestamp for mem in test_case.memories]
        time_range = max(timestamps) - min(timestamps)
        assert time_range.days > 0  # Should span multiple days
    
    @pytest.mark.asyncio
    async def test_adversarial_generation(self, generator):
        """Test adversarial reasoning test case generation"""
        test_case = await generator.generate_test_case(
            ReasoningType.ADVERSARIAL,
            DifficultyLevel.MEDIUM,
            PersonaType.TECHNICAL
        )
        
        assert test_case.reasoning_type == ReasoningType.ADVERSARIAL
        assert test_case.conflicting_info_count is not None
        assert test_case.conflicting_info_count > 0
        assert len(test_case.memories) >= test_case.conflicting_info_count + 1
        assert "conflict" in test_case.validation_notes.lower()
    
    @pytest.mark.asyncio
    async def test_commonsense_generation(self, generator):
        """Test commonsense reasoning test case generation"""
        test_case = await generator.generate_test_case(
            ReasoningType.COMMONSENSE,
            DifficultyLevel.EASY,
            PersonaType.CREATIVE
        )
        
        assert test_case.reasoning_type == ReasoningType.COMMONSENSE
        assert len(test_case.memories) >= 2
        assert "commonsense" in test_case.validation_notes.lower() or "knowledge" in test_case.validation_notes.lower()
    
    @pytest.mark.asyncio
    async def test_batch_generation(self, generator):
        """Test batch generation functionality"""
        batch_size = 5
        test_cases = await generator.generate_batch(
            count=batch_size,
            reasoning_types=[ReasoningType.SINGLE_HOP, ReasoningType.MULTI_HOP]
        )
        
        assert len(test_cases) <= batch_size  # May be less due to failures
        assert len(test_cases) > 0  # Should generate at least some
        
        # Check diversity
        reasoning_types = {tc.reasoning_type for tc in test_cases}
        assert len(reasoning_types) <= 2  # Only requested types
        
        # Check uniqueness
        ids = {tc.id for tc in test_cases}
        assert len(ids) == len(test_cases)  # All unique IDs
    
    @pytest.mark.asyncio
    async def test_test_case_serialization(self, generator):
        """Test test case serialization and deserialization"""
        original = await generator.generate_test_case(
            ReasoningType.SINGLE_HOP,
            DifficultyLevel.MEDIUM
        )
        
        # Serialize to dict
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == original.id
        assert data["reasoning_type"] == original.reasoning_type.value
        
        # Deserialize back
        restored = SyntheticTestCase.from_dict(data)
        assert restored.id == original.id
        assert restored.reasoning_type == original.reasoning_type
        assert restored.difficulty == original.difficulty
        assert len(restored.memories) == len(original.memories)
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions"""
        os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
        
        # Test single generation
        test_case = await generate_single_test_case(ReasoningType.SINGLE_HOP)
        assert test_case.reasoning_type == ReasoningType.SINGLE_HOP
        
        # Test batch generation
        batch = await generate_test_batch(count=3)
        assert len(batch) <= 3
        assert len(batch) > 0
        
        # Test balanced dataset
        dataset = await generate_balanced_dataset(size=10)
        assert len(dataset) <= 10
        reasoning_types = {tc.reasoning_type for tc in dataset}
        assert len(reasoning_types) > 1  # Should have variety


class TestSyntheticQualityValidator:
    """Test synthetic data quality validation"""
    
    @pytest.fixture
    def validator(self):
        """Create validator for testing"""
        return SyntheticQualityValidator()
    
    @pytest.fixture
    async def sample_test_case(self):
        """Create a sample test case for validation"""
        memories = [
            Memory("User enjoys reading science fiction books", datetime.now() - timedelta(days=5)),
            Memory("User recently bought a new Kindle device", datetime.now() - timedelta(days=2))
        ]
        
        return SyntheticTestCase(
            id="test-case-001",
            reasoning_type=ReasoningType.SINGLE_HOP,
            difficulty=DifficultyLevel.EASY,
            persona=PersonaType.CASUAL,
            decision_path=ConversationDecisionPath.CONTEXTUAL_CONVERSATION,
            query="What kind of books do I like to read?",
            memories=memories,
            expected_response="Based on your memories, you enjoy reading science fiction books.",
            expected_memory_count=2,
            generation_timestamp=datetime.now(),
            generator_model="test-model"
        )
    
    @pytest.mark.asyncio
    async def test_validator_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator.judge_service is not None
        assert validator.consensus_service is not None
        assert validator.min_overall_score > 0
        assert validator.min_coherence_score > 0
        assert validator.min_realism_score > 0
        assert validator.min_reasoning_score > 0
    
    @pytest.mark.asyncio
    async def test_single_validation(self, validator, sample_test_case):
        """Test validation of a single test case"""
        # Skip actual LLM calls in tests unless explicitly enabled
        if not os.getenv("ENABLE_LLM_TESTS", "false").lower() == "true":
            pytest.skip("LLM tests disabled")
        
        result = await validator.validate_test_case(sample_test_case)
        
        assert isinstance(result, QualityValidationResult)
        assert result.test_case_id == sample_test_case.id
        assert isinstance(result.passed, bool)
        assert 0 <= result.overall_score <= 10
        assert 0 <= result.coherence_score <= 10
        assert 0 <= result.realism_score <= 10
        assert 0 <= result.difficulty_score <= 10
        assert 0 <= result.reasoning_score <= 10
        assert result.validation_timestamp is not None
        assert isinstance(result.feedback, str)
        assert isinstance(result.issues_found, list)
    
    @pytest.mark.asyncio
    async def test_batch_validation(self, validator):
        """Test batch validation functionality"""
        if not os.getenv("ENABLE_LLM_TESTS", "false").lower() == "true":
            pytest.skip("LLM tests disabled")
        
        # Generate small batch for testing
        os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
        test_cases = await generate_test_batch(count=2)
        
        passed_cases, validation_results = await validator.validate_batch(test_cases)
        
        assert len(validation_results) <= len(test_cases)
        assert len(passed_cases) <= len(test_cases)
        assert all(isinstance(r, QualityValidationResult) for r in validation_results)
        assert all(isinstance(tc, SyntheticTestCase) for tc in passed_cases)
    
    @pytest.mark.asyncio
    async def test_validation_result_serialization(self, validator, sample_test_case):
        """Test validation result serialization"""
        if not os.getenv("ENABLE_LLM_TESTS", "false").lower() == "true":
            pytest.skip("LLM tests disabled")
        
        result = await validator.validate_test_case(sample_test_case)
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["test_case_id"] == result.test_case_id
        assert data["passed"] == result.passed
        assert data["overall_score"] == result.overall_score
        assert "validation_timestamp" in data
    
    def test_quality_threshold_logic(self, validator):
        """Test quality threshold determination logic"""
        # Mock validation data
        validation_data = {
            "coherence_score": 8.0,
            "realism_score": 7.5,
            "difficulty_score": 6.5,
            "reasoning_score": 8.5
        }
        
        overall_score = validator._calculate_overall_score(validation_data)
        assert isinstance(overall_score, float)
        assert 0 <= overall_score <= 10
        
        passed = validator._determine_pass_fail(validation_data, overall_score)
        assert isinstance(passed, bool)


class TestSyntheticDatasetManager:
    """Test synthetic dataset management"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def manager(self, temp_storage):
        """Create dataset manager with temporary storage"""
        return SyntheticDatasetManager(storage_path=temp_storage)
    
    @pytest.fixture
    async def sample_test_cases(self):
        """Create sample test cases for dataset testing"""
        memories1 = [Memory("Memory 1", datetime.now() - timedelta(days=1))]
        memories2 = [Memory("Memory 2", datetime.now() - timedelta(days=2))]
        
        return [
            SyntheticTestCase(
                id="case-001",
                reasoning_type=ReasoningType.SINGLE_HOP,
                difficulty=DifficultyLevel.EASY,
                persona=PersonaType.CASUAL,
                decision_path=ConversationDecisionPath.CONTEXTUAL_CONVERSATION,
                query="Query 1",
                memories=memories1,
                expected_response="Response 1",
                expected_memory_count=1,
                generation_timestamp=datetime.now(),
                generator_model="test-model",
                quality_score=8.5
            ),
            SyntheticTestCase(
                id="case-002",
                reasoning_type=ReasoningType.MULTI_HOP,
                difficulty=DifficultyLevel.MEDIUM,
                persona=PersonaType.PROFESSIONAL,
                decision_path=ConversationDecisionPath.CONTEXTUAL_CONVERSATION,
                query="Query 2",
                memories=memories2,
                expected_response="Response 2",
                expected_memory_count=1,
                generation_timestamp=datetime.now(),
                generator_model="test-model",
                quality_score=7.2
            )
        ]
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """Test dataset manager initialization"""
        assert manager.storage_path.exists()
        assert manager.datasets_dir.exists()
        assert manager.metadata_dir.exists()
        assert manager.exports_dir.exists()
        assert isinstance(manager._dataset_cache, dict)
        assert isinstance(manager._metadata_cache, dict)
    
    @pytest.mark.asyncio
    async def test_dataset_creation(self, manager, sample_test_cases):
        """Test dataset creation"""
        dataset_id = await manager.create_dataset(
            name="Test Dataset",
            test_cases=sample_test_cases,
            description="A test dataset",
            tags=["test", "sample"]
        )
        
        assert isinstance(dataset_id, str)
        assert len(dataset_id) > 0
        
        # Check files were created
        dataset_file = manager.datasets_dir / f"{dataset_id}.json"
        metadata_file = manager.metadata_dir / f"{dataset_id}.json"
        
        assert dataset_file.exists()
        assert metadata_file.exists()
        
        # Check cache was updated
        assert dataset_id in manager._dataset_cache
        assert dataset_id in manager._metadata_cache
    
    @pytest.mark.asyncio
    async def test_dataset_loading(self, manager, sample_test_cases):
        """Test dataset loading"""
        dataset_id = await manager.create_dataset("Test Dataset", sample_test_cases)
        
        # Clear cache to test file loading
        manager._dataset_cache.clear()
        
        loaded_cases = await manager.load_dataset(dataset_id)
        
        assert len(loaded_cases) == len(sample_test_cases)
        assert all(isinstance(tc, SyntheticTestCase) for tc in loaded_cases)
        assert loaded_cases[0].id == sample_test_cases[0].id
        assert loaded_cases[1].reasoning_type == sample_test_cases[1].reasoning_type
    
    @pytest.mark.asyncio
    async def test_metadata_loading(self, manager, sample_test_cases):
        """Test metadata loading"""
        dataset_id = await manager.create_dataset(
            "Test Dataset",
            sample_test_cases,
            description="Test description",
            tags=["test"]
        )
        
        # Clear cache
        manager._metadata_cache.clear()
        
        metadata = await manager.get_dataset_metadata(dataset_id)
        
        assert isinstance(metadata, DatasetMetadata)
        assert metadata.name == "Test Dataset"
        assert metadata.description == "Test description"
        assert metadata.test_case_count == len(sample_test_cases)
        assert "test" in metadata.tags
        assert "single_hop" in metadata.reasoning_type_distribution
        assert "multi_hop" in metadata.reasoning_type_distribution
    
    @pytest.mark.asyncio
    async def test_dataset_filtering(self, manager, sample_test_cases):
        """Test dataset filtering"""
        dataset_id = await manager.create_dataset("Test Dataset", sample_test_cases)
        
        # Filter by reasoning type
        filter_criteria = DatasetFilter(
            reasoning_types=[ReasoningType.SINGLE_HOP]
        )
        filtered_cases = await manager.filter_test_cases(dataset_id, filter_criteria)
        
        assert len(filtered_cases) == 1
        assert filtered_cases[0].reasoning_type == ReasoningType.SINGLE_HOP
        
        # Filter by quality score
        filter_criteria = DatasetFilter(min_quality_score=8.0)
        filtered_cases = await manager.filter_test_cases(dataset_id, filter_criteria)
        
        assert len(filtered_cases) == 1  # Only one case has score >= 8.0
        assert filtered_cases[0].quality_score >= 8.0
    
    @pytest.mark.asyncio
    async def test_dataset_export(self, manager, sample_test_cases):
        """Test dataset export functionality"""
        dataset_id = await manager.create_dataset("Test Dataset", sample_test_cases)
        
        # Export as JSON
        export_path = await manager.export_dataset(dataset_id, format="json")
        
        assert Path(export_path).exists()
        assert export_path.endswith(".json")
        
        # Check export content
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        assert "metadata" in export_data
        assert "test_cases" in export_data
        assert len(export_data["test_cases"]) == len(sample_test_cases)
    
    @pytest.mark.asyncio
    async def test_dataset_merging(self, manager, sample_test_cases):
        """Test dataset merging"""
        # Create two datasets
        dataset1_id = await manager.create_dataset("Dataset 1", [sample_test_cases[0]])
        dataset2_id = await manager.create_dataset("Dataset 2", [sample_test_cases[1]])
        
        # Merge them
        merged_id = await manager.merge_datasets(
            [dataset1_id, dataset2_id],
            "Merged Dataset",
            description="Merged from two datasets"
        )
        
        # Check merged dataset
        merged_cases = await manager.load_dataset(merged_id)
        assert len(merged_cases) == 2
        
        merged_metadata = await manager.get_dataset_metadata(merged_id)
        assert merged_metadata.name == "Merged Dataset"
        assert "merged" in merged_metadata.tags
    
    @pytest.mark.asyncio
    async def test_dataset_listing(self, manager, sample_test_cases):
        """Test dataset listing"""
        # Create multiple datasets
        await manager.create_dataset("Dataset 1", [sample_test_cases[0]])
        await manager.create_dataset("Dataset 2", [sample_test_cases[1]])
        
        datasets = await manager.list_datasets()
        
        assert len(datasets) >= 2
        assert all(isinstance(d, DatasetMetadata) for d in datasets)
        
        # Check sorting (newest first)
        if len(datasets) > 1:
            assert datasets[0].creation_timestamp >= datasets[1].creation_timestamp
    
    @pytest.mark.asyncio
    async def test_dataset_stats(self, manager, sample_test_cases):
        """Test overall dataset statistics"""
        await manager.create_dataset("Test Dataset", sample_test_cases)
        
        stats = await manager.get_dataset_stats()
        
        assert isinstance(stats, dict)
        assert "total_datasets" in stats
        assert "total_test_cases" in stats
        assert "reasoning_type_distribution" in stats
        assert "difficulty_distribution" in stats
        assert "avg_quality_score" in stats
        assert stats["total_datasets"] >= 1
        assert stats["total_test_cases"] >= len(sample_test_cases)
    
    @pytest.mark.asyncio
    async def test_dataset_deletion(self, manager, sample_test_cases):
        """Test dataset deletion"""
        dataset_id = await manager.create_dataset("Test Dataset", sample_test_cases)
        
        # Verify it exists
        datasets_before = await manager.list_datasets()
        assert any(d.id == dataset_id for d in datasets_before)
        
        # Delete it
        deleted = await manager.delete_dataset(dataset_id)
        assert deleted
        
        # Verify it's gone
        datasets_after = await manager.list_datasets()
        assert not any(d.id == dataset_id for d in datasets_after)
        
        # Check cache is cleared
        assert dataset_id not in manager._dataset_cache
        assert dataset_id not in manager._metadata_cache


class TestIntegration:
    """Integration tests across all Task 3 components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        if not os.getenv("ENABLE_LLM_TESTS", "false").lower() == "true":
            pytest.skip("LLM tests disabled")
        
        # Enable generation
        os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
        
        # 1. Generate test cases
        test_cases = await generate_test_batch(count=3)
        assert len(test_cases) > 0
        
        # 2. Validate quality
        passed_cases, validation_results = await validate_test_batch(test_cases)
        assert len(validation_results) > 0
        
        # 3. Create dataset
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SyntheticDatasetManager(storage_path=temp_dir)
            dataset_id = await manager.create_dataset(
                "End-to-End Test Dataset",
                passed_cases,
                description="Generated and validated test cases"
            )
            
            # 4. Load and verify
            loaded_cases = await manager.load_dataset(dataset_id)
            assert len(loaded_cases) == len(passed_cases)
            
            # 5. Export dataset
            export_path = await manager.export_dataset(dataset_id)
            assert Path(export_path).exists()
    
    @pytest.mark.asyncio
    async def test_generate_and_validate_integration(self):
        """Test integrated generation and validation"""
        if not os.getenv("ENABLE_LLM_TESTS", "false").lower() == "true":
            pytest.skip("LLM tests disabled")
        
        os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
        
        validated_cases = await generate_and_validate_batch(
            count=2,
            reasoning_types=[ReasoningType.SINGLE_HOP],
            max_regeneration_attempts=1
        )
        
        assert len(validated_cases) <= 2
        assert all(tc.quality_score is not None for tc in validated_cases)
        assert all(tc.quality_score >= 7.0 for tc in validated_cases)  # Default threshold


# Test runner configuration
if __name__ == "__main__":
    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)
    
    # Set up test environment
    os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
    os.environ["EVALUATION_MODE"] = "true"
    
    # Run specific test classes or all tests
    pytest.main([__file__, "-v"])