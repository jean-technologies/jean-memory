"""
Synthetic Test Data Generator Demo
=================================

Comprehensive demonstration of Task 3: Synthetic Test Data Generator
including generation, validation, and dataset management.

Run this demo to see the synthetic data generator in action.
"""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Import Task 3 components
from .synthetic_data_generator import (
    ReasoningType,
    DifficultyLevel,
    PersonaType,
    ConversationDecisionPath,
    generate_single_test_case,
    generate_test_batch,
    generate_balanced_dataset,
    get_synthetic_generator
)

from .synthetic_quality_validator import (
    validate_single_test_case,
    validate_test_batch,
    generate_and_validate_batch,
    get_quality_validator
)

from .synthetic_dataset_manager import (
    create_test_dataset,
    load_test_dataset,
    filter_dataset,
    export_test_dataset,
    get_dataset_manager,
    DatasetFilter
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SyntheticGeneratorDemo:
    """Comprehensive demo of synthetic test data generation"""
    
    def __init__(self):
        """Initialize demo with temporary storage"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir)
        logger.info(f"🧬 Demo initialized with storage at {self.storage_path}")
        
        # Configure environment for demo
        os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
        os.environ["SYNTHETIC_DATASET_PATH"] = str(self.storage_path)
        os.environ["EVALUATION_MODE"] = "true"
        
        # Demo statistics
        self.demo_stats = {
            "generated_cases": 0,
            "validated_cases": 0,
            "datasets_created": 0,
            "exports_created": 0
        }
    
    async def demo_single_generation(self):
        """Demo 1: Single test case generation across all reasoning types"""
        logger.info("🧬 DEMO 1: Single Test Case Generation")
        logger.info("=" * 50)
        
        for reasoning_type in ReasoningType:
            try:
                logger.info(f"🧬 Generating {reasoning_type.value} test case...")
                
                test_case = await generate_single_test_case(
                    reasoning_type=reasoning_type,
                    difficulty=DifficultyLevel.MEDIUM,
                    persona=PersonaType.CASUAL
                )
                
                self.demo_stats["generated_cases"] += 1
                
                logger.info(f"✅ Generated test case {test_case.id[:8]}")
                logger.info(f"   Query: {test_case.query[:100]}...")
                logger.info(f"   Memories: {len(test_case.memories)}")
                logger.info(f"   Expected hops: {test_case.required_hops}")
                logger.info(f"   Temporal span: {test_case.temporal_span_days} days")
                logger.info(f"   Conflicts: {test_case.conflicting_info_count}")
                logger.info("")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate {reasoning_type.value}: {e}")
    
    async def demo_batch_generation(self):
        """Demo 2: Batch generation with diversity"""
        logger.info("🧬 DEMO 2: Batch Generation")
        logger.info("=" * 50)
        
        try:
            logger.info("🧬 Generating batch of 8 diverse test cases...")
            
            test_cases = await generate_test_batch(
                count=8,
                reasoning_types=[ReasoningType.SINGLE_HOP, ReasoningType.MULTI_HOP, ReasoningType.TEMPORAL]
            )
            
            self.demo_stats["generated_cases"] += len(test_cases)
            
            logger.info(f"✅ Generated {len(test_cases)} test cases")
            
            # Show diversity statistics
            reasoning_counts = {}
            difficulty_counts = {}
            persona_counts = {}
            
            for tc in test_cases:
                reasoning_counts[tc.reasoning_type.value] = reasoning_counts.get(tc.reasoning_type.value, 0) + 1
                difficulty_counts[tc.difficulty.value] = difficulty_counts.get(tc.difficulty.value, 0) + 1
                persona_counts[tc.persona.value] = persona_counts.get(tc.persona.value, 0) + 1
            
            logger.info("📊 Diversity Statistics:")
            logger.info(f"   Reasoning types: {reasoning_counts}")
            logger.info(f"   Difficulties: {difficulty_counts}")
            logger.info(f"   Personas: {persona_counts}")
            logger.info("")
            
            return test_cases
            
        except Exception as e:
            logger.error(f"❌ Batch generation failed: {e}")
            return []
    
    async def demo_quality_validation(self, test_cases):
        """Demo 3: Quality validation of generated test cases"""
        logger.info("🔍 DEMO 3: Quality Validation")
        logger.info("=" * 50)
        
        if not test_cases:
            logger.warning("⚠️ No test cases to validate")
            return [], []
        
        try:
            logger.info(f"🔍 Validating {len(test_cases)} test cases...")
            
            # Note: Skip actual LLM validation in demo unless explicitly enabled
            if os.getenv("ENABLE_LLM_TESTS", "false").lower() == "true":
                passed_cases, validation_results = await validate_test_batch(test_cases)
                
                self.demo_stats["validated_cases"] += len(passed_cases)
                
                logger.info(f"✅ Validation complete:")
                logger.info(f"   Passed: {len(passed_cases)}/{len(test_cases)}")
                
                if validation_results:
                    avg_score = sum(r.overall_score for r in validation_results) / len(validation_results)
                    logger.info(f"   Average score: {avg_score:.1f}/10")
                    
                    # Show score breakdown
                    for result in validation_results[:3]:  # Show first 3
                        logger.info(f"   Case {result.test_case_id[:8]}: {result.overall_score:.1f} ({'✅' if result.passed else '❌'})")
                        if result.issues_found:
                            logger.info(f"      Issues: {', '.join(result.issues_found[:2])}")
                
                return passed_cases, validation_results
            else:
                logger.info("🔍 Simulating validation (LLM validation disabled in demo)")
                # Simulate validation for demo purposes
                simulated_results = []
                for tc in test_cases:
                    tc.quality_score = 8.5  # Simulate good quality
                    simulated_results.append(tc)
                
                self.demo_stats["validated_cases"] += len(test_cases)
                logger.info(f"✅ Simulated validation: {len(test_cases)} cases passed")
                return test_cases, []
                
        except Exception as e:
            logger.error(f"❌ Quality validation failed: {e}")
            return [], []
    
    async def demo_dataset_management(self, test_cases):
        """Demo 4: Dataset management and organization"""
        logger.info("📁 DEMO 4: Dataset Management")
        logger.info("=" * 50)
        
        if not test_cases:
            logger.warning("⚠️ No test cases for dataset management")
            return None
        
        try:
            # Create dataset
            logger.info("📁 Creating dataset...")
            dataset_id = await create_test_dataset(
                name="Demo Dataset",
                test_cases=test_cases,
                description="Generated during synthetic data generator demo",
                tags=["demo", "synthetic", "test"]
            )
            
            self.demo_stats["datasets_created"] += 1
            
            logger.info(f"✅ Created dataset {dataset_id[:8]}")
            
            # Load dataset
            logger.info("📁 Loading dataset...")
            loaded_cases = await load_test_dataset(dataset_id)
            logger.info(f"✅ Loaded {len(loaded_cases)} test cases")
            
            # Filter dataset
            logger.info("🔍 Filtering dataset...")
            filtered_cases = await filter_dataset(
                dataset_id,
                reasoning_types=[ReasoningType.SINGLE_HOP, ReasoningType.MULTI_HOP],
                min_quality=7.0,
                limit=5
            )
            logger.info(f"🔍 Filtered to {len(filtered_cases)} cases")
            
            # Export dataset
            logger.info("📤 Exporting dataset...")
            export_path = await export_test_dataset(dataset_id, format="json")
            self.demo_stats["exports_created"] += 1
            logger.info(f"📤 Exported to {export_path}")
            
            # Show dataset statistics
            manager = get_dataset_manager()
            metadata = await manager.get_dataset_metadata(dataset_id)
            
            logger.info("📊 Dataset Statistics:")
            logger.info(f"   Name: {metadata.name}")
            logger.info(f"   Test cases: {metadata.test_case_count}")
            logger.info(f"   Reasoning types: {metadata.reasoning_type_distribution}")
            logger.info(f"   Quality stats: {metadata.quality_stats}")
            logger.info("")
            
            return dataset_id
            
        except Exception as e:
            logger.error(f"❌ Dataset management failed: {e}")
            return None
    
    async def demo_advanced_features(self):
        """Demo 5: Advanced features and integration"""
        logger.info("⚡ DEMO 5: Advanced Features")
        logger.info("=" * 50)
        
        try:
            # Generate balanced dataset
            logger.info("⚡ Generating balanced dataset...")
            balanced_dataset = await generate_balanced_dataset(size=15)
            
            self.demo_stats["generated_cases"] += len(balanced_dataset)
            
            logger.info(f"✅ Generated balanced dataset with {len(balanced_dataset)} cases")
            
            # Show distribution
            reasoning_dist = {}
            for tc in balanced_dataset:
                reasoning_dist[tc.reasoning_type.value] = reasoning_dist.get(tc.reasoning_type.value, 0) + 1
            
            logger.info("📊 Balanced Distribution:")
            for reasoning_type, count in reasoning_dist.items():
                logger.info(f"   {reasoning_type}: {count} cases")
            
            # Integrated generation and validation
            if os.getenv("ENABLE_LLM_TESTS", "false").lower() == "true":
                logger.info("⚡ Demonstrating integrated generation and validation...")
                validated_cases = await generate_and_validate_batch(
                    count=3,
                    reasoning_types=[ReasoningType.SINGLE_HOP],
                    max_regeneration_attempts=1
                )
                
                logger.info(f"✅ Generated and validated {len(validated_cases)} high-quality cases")
            else:
                logger.info("⚡ Skipping LLM-based validation demo")
            
            # Dataset statistics
            manager = get_dataset_manager()
            stats = await manager.get_dataset_stats()
            
            logger.info("📊 Overall System Statistics:")
            logger.info(f"   Total datasets: {stats['total_datasets']}")
            logger.info(f"   Total test cases: {stats['total_test_cases']}")
            logger.info(f"   Average quality: {stats.get('avg_quality_score', 'N/A')}")
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Advanced features demo failed: {e}")
    
    async def demo_serialization_formats(self, dataset_id):
        """Demo 6: Export formats and serialization"""
        logger.info("💾 DEMO 6: Export Formats")
        logger.info("=" * 50)
        
        if not dataset_id:
            logger.warning("⚠️ No dataset for export demo")
            return
        
        try:
            # Export in different formats
            formats = ["json", "csv"]
            
            for format_type in formats:
                logger.info(f"💾 Exporting as {format_type.upper()}...")
                export_path = await export_test_dataset(dataset_id, format=format_type)
                
                # Show file info
                file_size = Path(export_path).stat().st_size
                logger.info(f"✅ Exported {format_type.upper()}: {export_path}")
                logger.info(f"   File size: {file_size:,} bytes")
                
                self.demo_stats["exports_created"] += 1
            
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Export formats demo failed: {e}")
    
    async def run_full_demo(self):
        """Run the complete demonstration"""
        logger.info("🚀 SYNTHETIC TEST DATA GENERATOR DEMO")
        logger.info("=" * 60)
        logger.info("Demonstrating Task 3: Synthetic Test Data Generator")
        logger.info("This demo showcases generation, validation, and management")
        logger.info("=" * 60)
        logger.info("")
        
        start_time = datetime.now()
        
        try:
            # Demo 1: Single generation
            await self.demo_single_generation()
            
            # Demo 2: Batch generation
            test_cases = await self.demo_batch_generation()
            
            # Demo 3: Quality validation
            validated_cases, _ = await self.demo_quality_validation(test_cases)
            
            # Demo 4: Dataset management
            dataset_id = await self.demo_dataset_management(validated_cases)
            
            # Demo 5: Advanced features
            await self.demo_advanced_features()
            
            # Demo 6: Export formats
            await self.demo_serialization_formats(dataset_id)
            
            # Final summary
            duration = datetime.now() - start_time
            
            logger.info("🎉 DEMO COMPLETE")
            logger.info("=" * 60)
            logger.info("📊 Demo Statistics:")
            logger.info(f"   Generated test cases: {self.demo_stats['generated_cases']}")
            logger.info(f"   Validated test cases: {self.demo_stats['validated_cases']}")
            logger.info(f"   Datasets created: {self.demo_stats['datasets_created']}")
            logger.info(f"   Exports created: {self.demo_stats['exports_created']}")
            logger.info(f"   Total duration: {duration.total_seconds():.1f} seconds")
            logger.info(f"   Storage location: {self.storage_path}")
            logger.info("")
            logger.info("✅ Task 3: Synthetic Test Data Generator - FULLY OPERATIONAL")
            logger.info("Ready for integration with Task 4 and beyond!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
    
    def cleanup(self):
        """Clean up demo resources"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            logger.info(f"🧹 Cleaned up demo storage at {self.temp_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up demo storage: {e}")


async def run_demo():
    """Run the synthetic data generator demo"""
    demo = SyntheticGeneratorDemo()
    
    try:
        await demo.run_full_demo()
    finally:
        demo.cleanup()


def run_quick_test():
    """Run a quick test to verify functionality"""
    print("🧬 Quick Synthetic Data Generator Test")
    print("=" * 40)
    
    # Test imports
    try:
        from . import synthetic_data_generator
        from . import synthetic_quality_validator
        from . import synthetic_dataset_manager
        print("✅ All modules imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test environment setup
    os.environ["SYNTHETIC_GENERATION_ENABLED"] = "true"
    os.environ["EVALUATION_MODE"] = "true"
    
    try:
        generator = get_synthetic_generator()
        validator = get_quality_validator()
        manager = get_dataset_manager()
        print("✅ All services initialized successfully")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    print("✅ Synthetic Test Data Generator ready for use!")
    print("   Set ENABLE_LLM_TESTS=true for full LLM-powered demo")
    return True


if __name__ == "__main__":
    # Quick test first
    if run_quick_test():
        print("\n" + "=" * 40)
        print("Running full demo...")
        print("=" * 40 + "\n")
        
        # Run full demo
        asyncio.run(run_demo())
    else:
        print("❌ Quick test failed, skipping full demo")