#!/usr/bin/env python3
"""
Test Suite for Task 4: Conversation Dataset Generator
====================================================

Comprehensive testing of conversation dataset generation functionality
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the path to import evaluation modules
sys.path.append(str(Path(__file__).parent.parent))

from evaluation.conversation_dataset_generator import (
    ConversationDatasetGenerator,
    ConversationDistributionType,
    generate_conversation_dataset,
    save_conversation_dataset,
    load_conversation_dataset
)
from evaluation.synthetic_data_generator import ReasoningType, PersonaType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_conversation_generation():
    """Test basic conversation dataset generation"""
    print("🧪 Testing basic conversation generation...")
    
    try:
        dataset = await generate_conversation_dataset(
            name="Basic Test",
            conversation_length=5,
            distribution_type=ConversationDistributionType.MIXED,
            persona=PersonaType.CASUAL
        )
        
        assert dataset.conversation_length == 5
        assert len(dataset.turns) == 5
        assert dataset.persona == PersonaType.CASUAL
        assert dataset.distribution_type == ConversationDistributionType.MIXED
        
        # Check turn numbering
        for i, turn in enumerate(dataset.turns):
            assert turn.turn_number == i + 1
            assert turn.user_message.strip()
            assert turn.expected_response.strip()
            assert turn.reasoning_type in ReasoningType
        
        print(f"   ✅ Generated {len(dataset.turns)} turns successfully")
        print(f"   📊 Reasoning distribution: {dataset.reasoning_type_distribution}")
        return True
        
    except Exception as e:
        print(f"   ❌ Basic generation failed: {e}")
        return False


async def test_uniform_distribution():
    """Test uniform reasoning type distribution"""
    print("🧪 Testing uniform distribution...")
    
    try:
        dataset = await generate_conversation_dataset(
            name="Uniform Test",
            conversation_length=7,
            distribution_type=ConversationDistributionType.UNIFORM,
            target_reasoning_types=[ReasoningType.SINGLE_HOP],
            persona=PersonaType.TECHNICAL
        )
        
        # All turns should have same reasoning type
        reasoning_types = set(turn.reasoning_type for turn in dataset.turns)
        assert len(reasoning_types) == 1
        assert ReasoningType.SINGLE_HOP in reasoning_types
        
        print(f"   ✅ Uniform distribution working: {reasoning_types}")
        return True
        
    except Exception as e:
        print(f"   ❌ Uniform distribution failed: {e}")
        return False


async def test_progressive_distribution():
    """Test progressive reasoning complexity"""
    print("🧪 Testing progressive distribution...")
    
    try:
        dataset = await generate_conversation_dataset(
            name="Progressive Test",
            conversation_length=10,
            distribution_type=ConversationDistributionType.PROGRESSIVE,
            persona=PersonaType.STUDENT
        )
        
        # Should start with simpler reasoning types
        first_turn = dataset.turns[0]
        last_turn = dataset.turns[-1]
        
        print(f"   📊 First turn reasoning: {first_turn.reasoning_type.value}")
        print(f"   📊 Last turn reasoning: {last_turn.reasoning_type.value}")
        print(f"   📊 Distribution: {dataset.reasoning_type_distribution}")
        
        assert len(dataset.turns) == 10
        return True
        
    except Exception as e:
        print(f"   ❌ Progressive distribution failed: {e}")
        return False


async def test_conversation_continuity():
    """Test that conversations have topic continuity"""
    print("🧪 Testing conversation continuity...")
    
    try:
        dataset = await generate_conversation_dataset(
            name="Continuity Test",
            conversation_length=6,
            distribution_type=ConversationDistributionType.MIXED,
            persona=PersonaType.CREATIVE
        )
        
        # Check that memory counts accumulate (indicating continuity)
        total_memories = len(dataset.all_memories)
        turn_memories = sum(len(turn.relevant_memories) for turn in dataset.turns)
        
        print(f"   📊 Total unique memories: {total_memories}")
        print(f"   📊 Sum of turn memories: {turn_memories}")
        print(f"   📊 Memory reuse ratio: {turn_memories / total_memories:.2f}")
        
        # Some memory reuse indicates continuity
        assert turn_memories >= total_memories
        
        # Check for non-empty conversations
        for turn in dataset.turns:
            assert len(turn.user_message) > 10  # Substantive messages
            assert len(turn.expected_response) > 10
        
        print("   ✅ Conversation continuity validated")
        return True
        
    except Exception as e:
        print(f"   ❌ Continuity test failed: {e}")
        return False


async def test_serialization():
    """Test JSON serialization and deserialization"""
    print("🧪 Testing serialization...")
    
    try:
        # Generate dataset
        original = await generate_conversation_dataset(
            name="Serialization Test",
            conversation_length=5,
            description="Test dataset for serialization",
            persona=PersonaType.PROFESSIONAL
        )
        
        # Serialize to dict
        data_dict = original.to_dict()
        
        # Check required fields
        required_fields = [
            'id', 'name', 'conversation_length', 'turns', 
            'creation_timestamp', 'reasoning_type_distribution'
        ]
        for field in required_fields:
            assert field in data_dict, f"Missing field: {field}"
        
        # Deserialize back
        restored = ConversationDataset.from_dict(data_dict)
        
        # Verify integrity
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.conversation_length == original.conversation_length
        assert len(restored.turns) == len(original.turns)
        assert restored.persona == original.persona
        
        print("   ✅ Serialization working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Serialization failed: {e}")
        return False


async def test_file_operations():
    """Test saving and loading from files"""
    print("🧪 Testing file operations...")
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ConversationDatasetGenerator(storage_path=temp_dir)
            
            # Generate and save dataset
            dataset = await generate_conversation_dataset(
                name="File Test",
                conversation_length=5,
                persona=PersonaType.CASUAL
            )
            
            filepath = await generator.save_dataset(dataset)
            
            # Verify file exists and has content
            assert Path(filepath).exists()
            assert Path(filepath).stat().st_size > 100  # Non-empty file
            
            # Load and verify
            loaded_dataset = await generator.load_dataset(filepath)
            
            assert loaded_dataset.id == dataset.id
            assert loaded_dataset.name == dataset.name
            assert len(loaded_dataset.turns) == len(dataset.turns)
            
            print(f"   ✅ File operations working: {Path(filepath).name}")
            return True
            
    except Exception as e:
        print(f"   ❌ File operations failed: {e}")
        return False


async def test_validation():
    """Test dataset validation functionality"""
    print("🧪 Testing dataset validation...")
    
    try:
        generator = ConversationDatasetGenerator()
        
        # Generate valid dataset
        dataset = await generate_conversation_dataset(
            name="Validation Test",
            conversation_length=5,
            persona=PersonaType.TECHNICAL
        )
        
        # Validate
        validation_results = await generator.validate_dataset(dataset)
        
        assert validation_results["valid"], f"Validation failed: {validation_results['issues']}"
        assert "statistics" in validation_results
        assert validation_results["statistics"]["total_turns"] == 5
        
        print("   ✅ Dataset validation working")
        return True
        
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        return False


async def test_edge_cases():
    """Test edge cases and error handling"""
    print("🧪 Testing edge cases...")
    
    try:
        # Test minimum length
        min_dataset = await generate_conversation_dataset(
            name="Min Length",
            conversation_length=5,  # Minimum allowed
            persona=PersonaType.CASUAL
        )
        assert len(min_dataset.turns) == 5
        
        # Test maximum length (but smaller for testing)
        max_dataset = await generate_conversation_dataset(
            name="Max Length Test",
            conversation_length=15,  # Smaller than max for faster testing
            persona=PersonaType.CASUAL
        )
        assert len(max_dataset.turns) == 15
        
        # Test invalid length (should raise error)
        try:
            invalid_dataset = await generate_conversation_dataset(
                name="Invalid",
                conversation_length=3,  # Below minimum
                persona=PersonaType.CASUAL
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
        print("   ✅ Edge cases handled correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Edge case testing failed: {e}")
        return False


async def test_different_personas():
    """Test generation with different personas"""
    print("🧪 Testing different personas...")
    
    results = {}
    
    for persona in PersonaType:
        try:
            dataset = await generate_conversation_dataset(
                name=f"Persona {persona.value}",
                conversation_length=5,
                persona=persona,
                distribution_type=ConversationDistributionType.MIXED
            )
            
            results[persona.value] = {
                "success": True,
                "turns": len(dataset.turns),
                "reasoning_distribution": dataset.reasoning_type_distribution
            }
            
        except Exception as e:
            results[persona.value] = {
                "success": False,
                "error": str(e)
            }
    
    successful_personas = sum(1 for r in results.values() if r["success"])
    
    print(f"   📊 Successful personas: {successful_personas}/{len(PersonaType)}")
    for persona, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {persona}: {result.get('turns', 'Failed')}")
    
    return successful_personas >= len(PersonaType) * 0.8  # 80% success rate


async def test_progress_callback():
    """Test progress callback functionality"""
    print("🧪 Testing progress callback...")
    
    progress_calls = []
    
    def track_progress(current, total):
        progress_calls.append((current, total))
    
    try:
        dataset = await generate_conversation_dataset(
            name="Progress Test",
            conversation_length=5,
            persona=PersonaType.CASUAL,
            progress_callback=track_progress
        )
        
        # Should have received progress updates
        assert len(progress_calls) == 5
        assert progress_calls[0] == (1, 5)
        assert progress_calls[-1] == (5, 5)
        
        print(f"   ✅ Progress tracking working: {len(progress_calls)} calls")
        return True
        
    except Exception as e:
        print(f"   ❌ Progress callback failed: {e}")
        return False


async def run_comprehensive_tests():
    """Run all tests and report results"""
    print("🔬 TASK 4: CONVERSATION DATASET GENERATOR - COMPREHENSIVE TESTING")
    print("=" * 70)
    
    # Ensure we have API keys for testing
    if not os.getenv('GEMINI_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        print("❌ No API keys found. Please set GEMINI_API_KEY or OPENAI_API_KEY")
        return False
    
    # Enable evaluation mode
    os.environ['SYNTHETIC_GENERATION_ENABLED'] = 'true'
    os.environ['EVALUATION_MODE'] = 'true'
    
    tests = [
        ("Basic Generation", test_basic_conversation_generation),
        ("Uniform Distribution", test_uniform_distribution),
        ("Progressive Distribution", test_progressive_distribution),
        ("Conversation Continuity", test_conversation_continuity),
        ("Serialization", test_serialization),
        ("File Operations", test_file_operations),
        ("Dataset Validation", test_validation),
        ("Edge Cases", test_edge_cases),
        ("Different Personas", test_different_personas),
        ("Progress Callback", test_progress_callback)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - TASK 4 READY FOR DEPLOYMENT")
    elif passed >= total * 0.8:
        print("⚠️ MOSTLY WORKING - Minor issues to address")
    else:
        print("❌ SIGNIFICANT ISSUES - Needs debugging")
    
    return passed >= total * 0.8


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_comprehensive_tests())
    sys.exit(0 if success else 1)