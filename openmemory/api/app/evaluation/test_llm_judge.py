"""
Test LLM Judge & Scoring System
===============================

Comprehensive tests for the LLM Judge system to verify:
- Output reliability and consistency
- Scoring accuracy across reasoning types
- Error handling and fallback behavior
- Integration with evaluation infrastructure

Run with: python -m pytest app/evaluation/test_llm_judge.py -v
"""

import asyncio
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict

from .llm_judge import (
    LLMJudgeService, 
    EvaluationContext, 
    JudgeScore, 
    ReasoningType, 
    LLMProvider,
    evaluate_single_response,
    evaluate_conversation_consistency,
    get_judge_service
)


class TestLLMJudgeService:
    """Test suite for LLM Judge Service"""
    
    @pytest.fixture
    def judge_service(self):
        """Create judge service with mocked LLM providers"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "OPENAI_API_KEY": "test-key"}):
            service = LLMJudgeService()
            
            # Mock Gemini
            service.gemini_model = MagicMock()
            service.gemini_pro_model = MagicMock()
            
            # Mock OpenAI
            service.openai_client = AsyncMock()
            
            return service
    
    @pytest.fixture
    def sample_context(self):
        """Sample evaluation context for testing"""
        return EvaluationContext(
            query="What are my favorite Italian restaurants?",
            retrieved_memories=[
                "User loves Italian food, especially pasta carbonara",
                "Had amazing dinner at Da Vinci's last week",
                "Prefers authentic Italian restaurants over chains"
            ],
            generated_response="Based on your preferences, you enjoy authentic Italian restaurants like Da Vinci's where you had a great dinner last week. You particularly love pasta carbonara and prefer authentic places over chain restaurants.",
            reasoning_type=ReasoningType.SINGLE_HOP
        )
    
    def test_reasoning_type_inference(self, judge_service):
        """Test automatic reasoning type inference from queries"""
        test_cases = [
            ("What's my name?", ReasoningType.SINGLE_HOP),
            ("When did I last visit Paris?", ReasoningType.TEMPORAL),
            ("How does my workout routine compare to last year?", ReasoningType.MULTI_HOP),
            ("What's the relationship between my sleep and productivity?", ReasoningType.MULTI_HOP),
            ("I said I like coffee but also said I avoid caffeine - what's the contradiction?", ReasoningType.ADVERSARIAL),
        ]
        
        for query, expected_type in test_cases:
            inferred = judge_service._infer_reasoning_type(query)
            assert inferred == expected_type, f"Query: '{query}' expected {expected_type}, got {inferred}"
    
    def test_evaluation_prompt_creation(self, judge_service, sample_context):
        """Test evaluation prompt creation for different reasoning types"""
        prompt = judge_service._create_evaluation_prompt(sample_context)
        
        # Check prompt contains key elements
        assert sample_context.query in prompt
        assert "RETRIEVED MEMORIES:" in prompt
        assert "AI RESPONSE:" in prompt
        assert "RELEVANCE (0-10)" in prompt
        assert "COMPLETENESS (0-10)" in prompt
        assert "REASONING QUALITY (0-10)" in prompt
        assert "RESPOND WITH VALID JSON" in prompt
    
    def test_memory_formatting(self, judge_service):
        """Test memory formatting for prompts"""
        memories = ["Memory 1 content", "Memory 2 content"]
        formatted = judge_service._format_memories(memories)
        
        assert "Memory 1: Memory 1 content" in formatted
        assert "Memory 2: Memory 2 content" in formatted
        
        # Test empty memories
        empty_formatted = judge_service._format_memories([])
        assert empty_formatted == "No memories retrieved."
    
    def test_conversation_history_formatting(self, judge_service):
        """Test conversation history formatting"""
        history = [
            {"role": "user", "content": "What's my favorite food?"},
            {"role": "assistant", "content": "Based on your memories, you love Italian food."},
            {"role": "user", "content": "Tell me about my last trip"}
        ]
        
        formatted = judge_service._format_conversation_history(history)
        assert "Turn 1 (user):" in formatted
        assert "Turn 2 (assistant):" in formatted
        assert "Turn 3 (user):" in formatted
    
    @pytest.mark.asyncio
    async def test_gemini_call_success(self, judge_service):
        """Test successful Gemini API call"""
        mock_response = MagicMock()
        mock_response.text = '{"relevance": 8.5, "completeness": 7.0, "reasoning_quality": 8.0, "explanation": "Good evaluation"}'
        
        judge_service.gemini_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        result = await judge_service._call_gemini("test prompt", LLMProvider.GEMINI_FLASH)
        assert '"relevance": 8.5' in result
    
    @pytest.mark.asyncio
    async def test_openai_call_success(self, judge_service):
        """Test successful OpenAI API call"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"relevance": 9.0, "completeness": 8.5, "reasoning_quality": 8.5, "explanation": "Excellent evaluation"}'
        
        judge_service.openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await judge_service._call_openai("test prompt", LLMProvider.OPENAI_GPT5)
        assert '"relevance": 9.0' in result
    
    @pytest.mark.asyncio
    async def test_llm_call_retry_logic(self, judge_service):
        """Test retry logic for failed LLM calls"""
        # Mock first two calls to fail, third to succeed
        judge_service.gemini_model.generate_content_async = AsyncMock(
            side_effect=[Exception("API Error"), Exception("Rate Limited"), 
                        MagicMock(text='{"relevance": 7.0}')]
        )
        
        result = await judge_service._call_llm("test prompt", LLMProvider.GEMINI_FLASH)
        assert '"relevance": 7.0' in result
        assert judge_service.gemini_model.generate_content_async.call_count == 3
    
    def test_judge_response_parsing(self, judge_service, sample_context):
        """Test parsing of LLM judge responses"""
        raw_response = """{
            "relevance": 8.5,
            "completeness": 7.0,
            "reasoning_quality": 8.0,
            "consistency": null,
            "explanation": "Good semantic matching with minor gaps",
            "key_strengths": ["Accurate memory retrieval", "Good synthesis"],
            "key_weaknesses": ["Could be more specific"],
            "improvement_suggestions": ["Add more details"]
        }"""
        
        score = judge_service._parse_judge_response(raw_response, sample_context, LLMProvider.GEMINI_FLASH)
        
        assert score.relevance == 8.5
        assert score.completeness == 7.0
        assert score.reasoning_quality == 8.0
        assert score.consistency == 0.0  # null converted to 0.0
        assert score.provider == LLMProvider.GEMINI_FLASH
        assert score.reasoning_type == ReasoningType.SINGLE_HOP
        assert "Good semantic matching" in score.explanation
    
    def test_overall_score_calculation(self, judge_service, sample_context):
        """Test weighted overall score calculation"""
        raw_response = """{
            "relevance": 10.0,
            "completeness": 8.0,
            "reasoning_quality": 6.0,
            "consistency": null,
            "explanation": "Test response"
        }"""
        
        score = judge_service._parse_judge_response(raw_response, sample_context, LLMProvider.GEMINI_FLASH)
        
        # Calculate expected overall (without consistency)
        weights = judge_service.score_weights.copy()
        weights.pop("consistency")
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        expected_overall = (
            10.0 * normalized_weights["relevance"] +
            8.0 * normalized_weights["completeness"] +
            6.0 * normalized_weights["reasoning"]
        )
        
        assert abs(score.overall - expected_overall) < 0.01
    
    def test_invalid_json_handling(self, judge_service, sample_context):
        """Test handling of invalid JSON responses"""
        with pytest.raises(ValueError, match="Invalid judge response format"):
            judge_service._parse_judge_response("Invalid JSON", sample_context, LLMProvider.GEMINI_FLASH)
    
    def test_fallback_score_creation(self, judge_service, sample_context):
        """Test fallback score creation for errors"""
        fallback = judge_service._create_fallback_score(
            sample_context, 
            LLMProvider.GEMINI_FLASH, 
            "API timeout"
        )
        
        assert fallback.relevance == 0.0
        assert fallback.overall == 0.0
        assert "API timeout" in fallback.explanation
        assert fallback.provider == LLMProvider.GEMINI_FLASH
    
    @pytest.mark.asyncio
    async def test_evaluate_context_integration(self, judge_service, sample_context):
        """Test full context evaluation workflow"""
        mock_response = MagicMock()
        mock_response.text = """{
            "relevance": 8.5,
            "completeness": 7.5,
            "reasoning_quality": 8.0,
            "consistency": null,
            "explanation": "Good evaluation",
            "key_strengths": ["Accurate"],
            "key_weaknesses": ["Minor gaps"],
            "improvement_suggestions": ["Add details"]
        }"""
        
        judge_service.gemini_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        score = await judge_service.evaluate_context(sample_context)
        
        assert isinstance(score, JudgeScore)
        assert score.relevance == 8.5
        assert score.latency_ms > 0  # Should have timing data
    
    @pytest.mark.asyncio 
    async def test_batch_evaluation(self, judge_service):
        """Test batch evaluation of multiple contexts"""
        contexts = [
            EvaluationContext(
                query="Query 1", 
                retrieved_memories=["Memory 1"], 
                generated_response="Response 1"
            ),
            EvaluationContext(
                query="Query 2", 
                retrieved_memories=["Memory 2"], 
                generated_response="Response 2"
            )
        ]
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"relevance": 8.0, "completeness": 7.0, "reasoning_quality": 8.0, "explanation": "Test"}'
        judge_service.gemini_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        scores = await judge_service.evaluate_batch(contexts)
        
        assert len(scores) == 2
        assert all(isinstance(score, JudgeScore) for score in scores)
    
    def test_aggregate_metrics_calculation(self, judge_service):
        """Test calculation of aggregate metrics from scores"""
        scores = [
            JudgeScore(
                relevance=8.0, completeness=7.0, reasoning_quality=8.5, consistency=9.0,
                overall=8.0, explanation="Good", reasoning_type=ReasoningType.SINGLE_HOP,
                timestamp=None, latency_ms=100.0, provider=LLMProvider.GEMINI_FLASH
            ),
            JudgeScore(
                relevance=9.0, completeness=8.0, reasoning_quality=7.5, consistency=8.0,
                overall=8.5, explanation="Excellent", reasoning_type=ReasoningType.MULTI_HOP,
                timestamp=None, latency_ms=150.0, provider=LLMProvider.OPENAI_GPT5
            )
        ]
        
        metrics = judge_service.calculate_aggregate_metrics(scores)
        
        assert metrics["count"] == 2
        assert metrics["valid_count"] == 2
        assert metrics["success_rate"] == 1.0
        assert abs(metrics["avg_relevance"] - 8.5) < 0.01
        assert abs(metrics["avg_overall"] - 8.25) < 0.01
        assert metrics["avg_latency_ms"] == 125.0
        
        # Check provider breakdown
        assert LLMProvider.GEMINI_FLASH.value in metrics["provider_breakdown"]
        assert LLMProvider.OPENAI_GPT5.value in metrics["provider_breakdown"]
        
        # Check reasoning type breakdown
        assert ReasoningType.SINGLE_HOP.value in metrics["reasoning_type_breakdown"]
        assert ReasoningType.MULTI_HOP.value in metrics["reasoning_type_breakdown"]


class TestLLMJudgeReliability:
    """Test judge reliability and consistency"""
    
    @pytest.fixture
    def realistic_test_cases(self):
        """Realistic test cases for reliability testing"""
        return [
            {
                "query": "What's my favorite programming language?",
                "memories": ["User prefers Python for data science", "Enjoys JavaScript for web development"],
                "good_response": "Based on your preferences, you use Python for data science work and JavaScript for web development projects.",
                "bad_response": "You like cooking pasta and playing tennis.",
                "expected_relevance_good": (8.0, 10.0),
                "expected_relevance_bad": (0.0, 3.0)
            },
            {
                "query": "When did I last exercise?",
                "memories": ["Went for a run on Monday morning", "Hit the gym on Friday evening"],
                "good_response": "You last exercised on Friday evening when you went to the gym, and before that on Monday morning when you went for a run.",
                "bad_response": "You should exercise more often for better health.",
                "expected_relevance_good": (7.0, 10.0),
                "expected_relevance_bad": (0.0, 4.0)
            }
        ]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_judge_reliability_with_real_llm(self, realistic_test_cases):
        """Test judge reliability with actual LLM calls (requires API keys)"""
        # Skip if no API keys available
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
            pytest.skip("No LLM API keys available for integration test")
        
        judge = get_judge_service()
        
        for test_case in realistic_test_cases:
            # Test good response
            good_score = await evaluate_single_response(
                query=test_case["query"],
                memories=test_case["memories"],
                response=test_case["good_response"]
            )
            
            # Test bad response  
            bad_score = await evaluate_single_response(
                query=test_case["query"],
                memories=test_case["memories"],
                response=test_case["bad_response"]
            )
            
            # Verify good response scores higher than bad response
            assert good_score.relevance > bad_score.relevance, f"Good response should score higher relevance: {good_score.relevance} vs {bad_score.relevance}"
            assert good_score.overall > bad_score.overall, f"Good response should score higher overall: {good_score.overall} vs {bad_score.overall}"
            
            # Check score ranges
            min_good, max_good = test_case["expected_relevance_good"]
            min_bad, max_bad = test_case["expected_relevance_bad"]
            
            assert min_good <= good_score.relevance <= 10.0, f"Good relevance {good_score.relevance} not in expected range [{min_good}, 10.0]"
            assert 0.0 <= bad_score.relevance <= max_bad, f"Bad relevance {bad_score.relevance} not in expected range [0.0, {max_bad}]"


class TestConvenienceFunctions:
    """Test convenience functions for common evaluation patterns"""
    
    @pytest.mark.asyncio
    async def test_evaluate_single_response(self):
        """Test single response evaluation convenience function"""
        with patch('app.evaluation.llm_judge.get_judge_service') as mock_get_service:
            mock_judge = AsyncMock()
            mock_score = JudgeScore(
                relevance=8.0, completeness=7.0, reasoning_quality=8.0, consistency=0.0,
                overall=7.8, explanation="Test", reasoning_type=ReasoningType.SINGLE_HOP,
                timestamp=None, latency_ms=100.0, provider=LLMProvider.GEMINI_FLASH
            )
            mock_judge.evaluate_context = AsyncMock(return_value=mock_score)
            mock_get_service.return_value = mock_judge
            
            score = await evaluate_single_response(
                query="Test query",
                memories=["Test memory"],
                response="Test response"
            )
            
            assert score == mock_score
            mock_judge.evaluate_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_evaluate_conversation_consistency(self):
        """Test conversation consistency evaluation"""
        with patch('app.evaluation.llm_judge.get_judge_service') as mock_get_service:
            mock_judge = AsyncMock()
            mock_score = JudgeScore(
                relevance=8.0, completeness=7.0, reasoning_quality=8.0, consistency=9.0,
                overall=8.2, explanation="Consistent", reasoning_type=ReasoningType.TEMPORAL,
                timestamp=None, latency_ms=120.0, provider=LLMProvider.GEMINI_FLASH
            )
            mock_judge.evaluate_context = AsyncMock(return_value=mock_score)
            mock_get_service.return_value = mock_judge
            
            score = await evaluate_conversation_consistency(
                query="Test query",
                memories=["Test memory"],
                response="Test response",
                conversation_history=[{"role": "user", "content": "Previous message"}],
                session_id="test-session"
            )
            
            assert score == mock_score
            # Verify consistency evaluation was requested
            call_args = mock_judge.evaluate_context.call_args[0][0]
            assert call_args.conversation_history is not None
            assert call_args.session_id == "test-session"
            assert call_args.reasoning_type == ReasoningType.TEMPORAL


if __name__ == "__main__":
    # Run basic tests without pytest
    import sys
    
    async def run_basic_tests():
        """Run basic functionality tests"""
        print("🧪 Testing LLM Judge Service...")
        
        # Test with mocked service
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test", "OPENAI_API_KEY": "test"}):
            judge = LLMJudgeService()
            
            # Test reasoning type inference
            test_queries = [
                "What's my name?",
                "When did I last visit Paris?", 
                "How does my sleep affect my productivity?",
                "I said I like coffee but avoid caffeine - what's wrong?"
            ]
            
            for query in test_queries:
                reasoning_type = judge._infer_reasoning_type(query)
                print(f"✅ Query: '{query}' → {reasoning_type.value}")
            
            # Test prompt creation
            context = EvaluationContext(
                query="What's my favorite food?",
                retrieved_memories=["User loves pizza", "Enjoys Italian cuisine"],
                generated_response="You love pizza and Italian cuisine in general."
            )
            
            prompt = judge._create_evaluation_prompt(context)
            assert "RELEVANCE (0-10)" in prompt
            assert "COMPLETENESS (0-10)" in prompt
            print("✅ Evaluation prompt created successfully")
            
            # Test JSON parsing
            sample_response = """{
                "relevance": 8.5,
                "completeness": 7.0,
                "reasoning_quality": 8.0,
                "consistency": null,
                "explanation": "Good evaluation"
            }"""
            
            score = judge._parse_judge_response(sample_response, context, LLMProvider.GEMINI_FLASH)
            assert score.relevance == 8.5
            assert score.overall > 0
            print("✅ JSON response parsing works")
            
            print("🎉 All basic tests passed!")
    
    # Run the basic tests
    asyncio.run(run_basic_tests())