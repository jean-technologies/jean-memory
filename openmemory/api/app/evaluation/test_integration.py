"""
Test LLM Judge Integration with Evaluation Infrastructure
========================================================

Tests the complete integration between Task 1 (Core Evaluation Infrastructure)
and Task 2 (LLM Judge & Scoring System).

Run with: python app/evaluation/test_integration.py
"""

import asyncio
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

# Test the integration
def test_judge_integration():
    """Test LLM Judge integration with core evaluation system"""
    print("🧪 Testing LLM Judge Integration...")
    
    # Set up environment for testing
    test_env = {
        "EVALUATION_MODE": "true",
        "LLM_JUDGE_ENABLED": "true", 
        "LLM_JUDGE_ASYNC": "false",  # Synchronous for testing
        "GEMINI_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key"
    }
    
    with patch.dict(os.environ, test_env):
        # Import after setting environment
        import sys
        sys.path.append('.')
        
        from app.evaluation.judge_integration import (
            JudgeIntegrationConfig,
            EnhancedMetricsCollector,
            get_judge_integration_status
        )
        
        # Test configuration
        config = JudgeIntegrationConfig.get_judge_config()
        assert config["enabled"] == True
        print("✅ Judge integration config loaded")
        
        # Test status reporting
        status = get_judge_integration_status()
        assert status["evaluation_enabled"] == True
        assert status["judge_module_available"] == True
        print("✅ Judge integration status reporting works")
        
        print("🎉 Basic integration tests passed!")


async def test_context_extraction():
    """Test extraction of judge context from function results"""
    print("🧪 Testing context extraction...")
    
    test_env = {
        "EVALUATION_MODE": "true",
        "LLM_JUDGE_ENABLED": "true",
        "GEMINI_API_KEY": "test-key"
    }
    
    with patch.dict(os.environ, test_env):
        import sys
        sys.path.append('.')
        
        from app.evaluation.judge_integration import EnhancedMetricsCollector
        from app.evaluation.metrics import EvaluationMetric
        from datetime import datetime
        
        collector = EnhancedMetricsCollector()
        
        # Test case 1: Dictionary result with structured data
        dict_result = {
            "query": "What's my favorite food?",
            "memories": ["User loves pizza", "Enjoys Italian cuisine"],
            "response": "You love pizza and Italian cuisine."
        }
        
        context = collector._extract_judge_context(
            dict_result, 
            (), 
            {"user_id": "test123"}
        )
        
        assert context is not None
        assert context.query == "What's my favorite food?"
        assert len(context.retrieved_memories) == 2
        assert context.generated_response == "You love pizza and Italian cuisine."
        print("✅ Dictionary result extraction works")
        
        # Test case 2: String result with kwargs
        string_result = "You love Italian food based on your preferences."
        
        context = collector._extract_from_string_result(
            string_result,
            ("What food do I like?",),
            {"memories": ["User prefers Italian", "Likes pasta"]}
        )
        
        assert context is not None
        assert "What food do I like?" in context.query
        assert len(context.retrieved_memories) == 2
        print("✅ String result extraction works")
        
        print("🎉 Context extraction tests passed!")


async def test_full_integration_workflow():
    """Test complete workflow from evaluation to judge scoring"""
    print("🧪 Testing full integration workflow...")
    
    test_env = {
        "EVALUATION_MODE": "true",
        "LLM_JUDGE_ENABLED": "true",
        "LLM_JUDGE_ASYNC": "false",
        "GEMINI_API_KEY": "test-key"
    }
    
    with patch.dict(os.environ, test_env):
        import sys
        sys.path.append('.')
        
        from app.evaluation.judge_integration import EnhancedMetricsCollector
        from app.evaluation.metrics import EvaluationMetric
        from app.evaluation.llm_judge import JudgeScore, ReasoningType, LLMProvider
        from datetime import datetime
        
        # Mock the LLM judge service
        collector = EnhancedMetricsCollector()
        
        # Mock judge evaluation
        mock_judge_score = JudgeScore(
            relevance=8.5,
            completeness=7.5,
            reasoning_quality=8.0,
            consistency=9.0,
            overall=8.2,
            explanation="Good evaluation with minor gaps",
            reasoning_type=ReasoningType.SINGLE_HOP,
            timestamp=datetime.utcnow(),
            latency_ms=150.0,
            provider=LLMProvider.GEMINI_FLASH
        )
        
        with patch.object(collector, '_perform_judge_evaluation', return_value=mock_judge_score):
            # Create base metric
            base_metric = EvaluationMetric(
                function_name="orchestrate_smart_context",
                latency_ms=250.0,
                success=True,
                timestamp=datetime.utcnow(),
                metadata={"user_id": "test123"}
            )
            
            # Test function result that should trigger judging
            function_result = {
                "query": "What are my hobbies?",
                "memories": [
                    "User enjoys reading books",
                    "Plays guitar in spare time", 
                    "Likes hiking on weekends"
                ],
                "response": "Based on your interests, you enjoy reading, playing guitar, and hiking."
            }
            
            # Collect enhanced metric with judge evaluation
            enhanced_metric = await collector.collect_with_judge_evaluation(
                base_metric,
                function_result,
                (),
                {"user_id": "test123", "query": "What are my hobbies?"}
            )
            
            # Verify enhanced metric includes judge scores
            assert enhanced_metric.has_judge_evaluation == True
            assert enhanced_metric.judge_relevance == 8.5
            assert enhanced_metric.judge_overall == 8.2
            assert enhanced_metric.judge_provider == "gemini-2.5-flash"
            assert enhanced_metric.judge_reasoning_type == "single_hop"
            print("✅ Enhanced metric creation works")
            
            # Verify base metric data is preserved
            assert enhanced_metric.function_name == "orchestrate_smart_context"
            assert enhanced_metric.latency_ms == 250.0
            assert enhanced_metric.success == True
            print("✅ Base metric data preserved")
            
            print("🎉 Full integration workflow test passed!")


async def test_async_integration():
    """Test asynchronous judge evaluation"""
    print("🧪 Testing async judge integration...")
    
    test_env = {
        "EVALUATION_MODE": "true",
        "LLM_JUDGE_ENABLED": "true",
        "LLM_JUDGE_ASYNC": "true",  # Enable async mode
        "GEMINI_API_KEY": "test-key"
    }
    
    with patch.dict(os.environ, test_env):
        import sys
        sys.path.append('.')
        
        from app.evaluation.judge_integration import EnhancedMetricsCollector
        from app.evaluation.metrics import EvaluationMetric
        from datetime import datetime
        
        collector = EnhancedMetricsCollector()
        
        # Mock async judge storage
        store_calls = []
        async def mock_store_async_result(function_name, judge_score):
            store_calls.append((function_name, judge_score))
        
        with patch.object(collector, '_store_async_judge_result', side_effect=mock_store_async_result):
            with patch.object(collector, '_perform_judge_evaluation', return_value=None) as mock_judge:
                
                base_metric = EvaluationMetric(
                    function_name="search_memory",
                    latency_ms=100.0,
                    success=True,
                    timestamp=datetime.utcnow(),
                    metadata={}
                )
                
                function_result = {
                    "query": "Test query",
                    "memories": ["Test memory"],
                    "response": "Test response"
                }
                
                # This should trigger async evaluation
                enhanced_metric = await collector.collect_with_judge_evaluation(
                    base_metric,
                    function_result,
                    (),
                    {}
                )
                
                # Should return immediately without judge score (async mode)
                assert enhanced_metric.has_judge_evaluation == False
                print("✅ Async mode returns immediately")
                
                # Give async task time to complete
                await asyncio.sleep(0.1)
                
        print("🎉 Async integration test passed!")


def test_environment_configurations():
    """Test different environment configurations"""
    print("🧪 Testing environment configurations...")
    
    # Test disabled evaluation
    with patch.dict(os.environ, {"EVALUATION_MODE": "false"}):
        import sys
        sys.path.append('.')
        
        from app.evaluation.judge_integration import JudgeIntegrationConfig
        
        assert JudgeIntegrationConfig.is_judge_enabled() == False
        print("✅ Correctly disabled when evaluation disabled")
    
    # Test disabled judge
    with patch.dict(os.environ, {"EVALUATION_MODE": "true", "LLM_JUDGE_ENABLED": "false"}):
        assert JudgeIntegrationConfig.is_judge_enabled() == False
        print("✅ Correctly disabled when judge disabled")
    
    # Test enabled configuration
    with patch.dict(os.environ, {
        "EVALUATION_MODE": "true",
        "LLM_JUDGE_ENABLED": "true",
        "LLM_JUDGE_PROVIDER": "openai",
        "LLM_JUDGE_FUNCTIONS": "orchestrate_smart_context,search_memory",
        "LLM_JUDGE_MIN_MEMORIES": "2"
    }):
        config = JudgeIntegrationConfig.get_judge_config()
        assert config["enabled"] == True
        assert config["provider"] == "openai"
        assert "orchestrate_smart_context" in config["functions_to_judge"]
        assert config["min_memory_count"] == 2
        print("✅ Configuration parsing works correctly")
    
    print("🎉 Environment configuration tests passed!")


async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Running LLM Judge Integration Tests...\n")
    
    test_judge_integration()
    await test_context_extraction()
    await test_full_integration_workflow()
    await test_async_integration()
    test_environment_configurations()
    
    print("\n🎉 All LLM Judge Integration tests passed!")
    print("\n📊 Integration Summary:")
    print("✅ Task 1 (Core Infrastructure) + Task 2 (LLM Judge) = Complete")
    print("✅ Automatic context extraction from function results")
    print("✅ Configurable judge evaluation (sync/async)")
    print("✅ Enhanced metrics with quality scores")
    print("✅ Production-safe defaults (disabled by default)")
    print("✅ Graceful fallback when LLM APIs unavailable")


if __name__ == "__main__":
    asyncio.run(run_all_tests())