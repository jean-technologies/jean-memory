"""
LLM Judge Demo Script
====================

Demonstrates the LLM Judge & Scoring System with real API calls.
Shows evaluation across different reasoning types and providers.

Usage:
    # Set environment variables first
    export GEMINI_API_KEY="your-gemini-key"
    export OPENAI_API_KEY="your-openai-key"  
    export EVALUATION_MODE="true"
    export LLM_JUDGE_ENABLED="true"
    
    # Run demo
    python app/evaluation/demo_llm_judge.py
"""

import asyncio
import json
import os
import sys
from typing import List, Dict
import time

# Add current directory to path
sys.path.append('.')

# Check if required modules are available
try:
    from app.evaluation.llm_judge import (
        evaluate_single_response,
        evaluate_conversation_consistency,
        get_judge_service,
        ReasoningType,
        LLMProvider
    )
    from app.evaluation.judge_integration import get_judge_integration_status
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


class LLMJudgeDemo:
    """Comprehensive demo of LLM Judge capabilities"""
    
    def __init__(self):
        self.test_cases = self._create_test_cases()
        
    def _create_test_cases(self) -> List[Dict]:
        """Create diverse test cases covering all reasoning types"""
        return [
            {
                "name": "Single-hop: Simple fact retrieval",
                "reasoning_type": ReasoningType.SINGLE_HOP,
                "query": "What's my favorite programming language?",
                "memories": [
                    "User prefers Python for data science projects",
                    "Enjoys JavaScript for web development",
                    "Recently started learning Rust"
                ],
                "good_response": "Based on your preferences, you use Python for data science and JavaScript for web development, with recent interest in Rust.",
                "bad_response": "You should learn more programming languages to advance your career."
            },
            {
                "name": "Multi-hop: Cross-memory synthesis",
                "reasoning_type": ReasoningType.MULTI_HOP,
                "query": "How does my sleep schedule affect my productivity?",
                "memories": [
                    "User goes to bed around 11 PM most nights",
                    "Wakes up at 6:30 AM feeling refreshed",
                    "Most productive work happens in the morning between 8-11 AM",
                    "Afternoon productivity drops significantly after lunch",
                    "Had trouble sleeping last week and noticed reduced focus"
                ],
                "good_response": "Your consistent 11 PM to 6:30 AM sleep schedule (7.5 hours) appears to support your high morning productivity from 8-11 AM. When you had sleep troubles last week, you noticed reduced focus, suggesting your regular sleep pattern is crucial for maintaining your peak morning work performance.",
                "bad_response": "You sleep at night and work during the day. That's normal."
            },
            {
                "name": "Temporal: Time-based reasoning",
                "reasoning_type": ReasoningType.TEMPORAL,
                "query": "How has my exercise routine changed over the last month?",
                "memories": [
                    "Three weeks ago: Started going to gym 3x per week",
                    "Two weeks ago: Added morning runs on weekends", 
                    "Last week: Missed gym twice due to work deadlines",
                    "This week: Back to regular gym schedule plus yoga class",
                    "Yesterday: Completed first 5K run"
                ],
                "good_response": "Your exercise routine has evolved significantly over the past month. You started with 3x weekly gym sessions three weeks ago, added weekend runs two weeks ago, had a setback last week due to work (missing gym twice), but bounced back this week with regular gym plus yoga. Yesterday's 5K completion shows clear progression from your weekend running habit.",
                "bad_response": "You exercise sometimes and sometimes you don't. You should be more consistent."
            },
            {
                "name": "Adversarial: Conflicting information",
                "reasoning_type": ReasoningType.ADVERSARIAL,
                "query": "I said I don't like coffee but also mentioned loving espresso - what's the contradiction?",
                "memories": [
                    "User said: 'I don't drink coffee, it makes me too jittery'",
                    "User mentioned: 'I love a good espresso after dinner'",
                    "User noted: 'I avoid caffeine in the morning'",
                    "User stated: 'My favorite drink is herbal tea'"
                ],
                "good_response": "There's an apparent contradiction between saying you don't drink coffee due to jitters and avoiding morning caffeine, while also loving espresso after dinner. This could be resolved if you only enjoy espresso occasionally in the evening when caffeine sensitivity is lower, or if you distinguish between regular coffee and espresso. Your preference for herbal tea suggests you generally avoid caffeine but make exceptions for special espresso occasions.",
                "bad_response": "You like espresso and coffee. There's no contradiction."
            }
        ]
    
    async def run_demo(self):
        """Run comprehensive LLM Judge demonstration"""
        print("🚀 LLM Judge & Scoring System Demo")
        print("=" * 50)
        
        # Check system status
        await self._check_system_status()
        
        # Test different providers if available
        await self._test_providers()
        
        # Run reasoning type tests
        await self._test_reasoning_types()
        
        # Test consistency evaluation
        await self._test_consistency_evaluation()
        
        # Performance analysis
        await self._analyze_performance()
        
        print("\n🎉 Demo completed successfully!")
    
    async def _check_system_status(self):
        """Check LLM Judge system status and configuration"""
        print("\n📊 System Status Check")
        print("-" * 30)
        
        try:
            status = get_judge_integration_status()
            print(f"✅ Evaluation enabled: {status['evaluation_enabled']}")
            print(f"✅ Judge module available: {status['judge_module_available']}")
            print(f"✅ Judge enabled: {status['judge_enabled']}")
            
            if 'judge_providers' in status:
                providers = status['judge_providers']
                print(f"✅ Gemini available: {providers['gemini_available']}")
                print(f"✅ OpenAI available: {providers['openai_available']}")
                print(f"✅ Default provider: {providers['default_provider']}")
            
            if not status['judge_enabled']:
                print("⚠️ LLM Judge is disabled. Set LLM_JUDGE_ENABLED=true to enable.")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return False
    
    async def _test_providers(self):
        """Test different LLM providers"""
        print("\n🤖 Provider Testing")
        print("-" * 30)
        
        judge_service = get_judge_service()
        available_providers = []
        
        # Check which providers are available
        if judge_service.openai_client:
            available_providers.extend([LLMProvider.OPENAI_GPT5, LLMProvider.OPENAI_GPT4O])
        if judge_service.gemini_model:
            available_providers.extend([LLMProvider.GEMINI_FLASH, LLMProvider.GEMINI_PRO])
        
        print(f"Available providers: {[p.value for p in available_providers]}")
        
        if not available_providers:
            print("⚠️ No LLM providers available - check API keys")
            return
        
        # Test each provider with a simple case
        test_case = self.test_cases[0]  # Simple single-hop case
        
        for provider in available_providers[:2]:  # Test max 2 providers to save API calls
            try:
                print(f"\nTesting {provider.value}...")
                start_time = time.time()
                
                score = await evaluate_single_response(
                    query=test_case["query"],
                    memories=test_case["memories"],
                    response=test_case["good_response"],
                    reasoning_type=test_case["reasoning_type"],
                    provider=provider
                )
                
                latency = time.time() - start_time
                print(f"✅ {provider.value}: Overall {score.overall:.1f}/10 ({latency:.2f}s)")
                print(f"   Relevance: {score.relevance:.1f}, Completeness: {score.completeness:.1f}")
                
            except Exception as e:
                print(f"❌ {provider.value} failed: {e}")
    
    async def _test_reasoning_types(self):
        """Test evaluation across different reasoning types"""
        print("\n🧠 Reasoning Type Evaluation")
        print("-" * 30)
        
        results = []
        
        for test_case in self.test_cases:
            print(f"\n📝 {test_case['name']}")
            
            try:
                # Test good response
                good_score = await evaluate_single_response(
                    query=test_case["query"],
                    memories=test_case["memories"],
                    response=test_case["good_response"],
                    reasoning_type=test_case["reasoning_type"]
                )
                
                # Test bad response  
                bad_score = await evaluate_single_response(
                    query=test_case["query"],
                    memories=test_case["memories"],
                    response=test_case["bad_response"],
                    reasoning_type=test_case["reasoning_type"]
                )
                
                print(f"   Good response: {good_score.overall:.1f}/10")
                print(f"   Bad response:  {bad_score.overall:.1f}/10")
                print(f"   Score difference: {good_score.overall - bad_score.overall:.1f}")
                
                # Verify good > bad
                if good_score.overall > bad_score.overall:
                    print("   ✅ Judge correctly identified better response")
                else:
                    print("   ⚠️ Judge scoring unexpected")
                
                results.append({
                    "reasoning_type": test_case["reasoning_type"].value,
                    "good_score": good_score.overall,
                    "bad_score": bad_score.overall,
                    "discrimination": good_score.overall - bad_score.overall
                })
                
            except Exception as e:
                print(f"   ❌ Evaluation failed: {e}")
        
        # Summary analysis
        if results:
            print(f"\n📈 Reasoning Type Summary")
            avg_discrimination = sum(r["discrimination"] for r in results) / len(results)
            print(f"   Average score discrimination: {avg_discrimination:.1f} points")
            print(f"   Best discrimination: {max(r['discrimination'] for r in results):.1f}")
            print(f"   Worst discrimination: {min(r['discrimination'] for r in results):.1f}")
    
    async def _test_consistency_evaluation(self):
        """Test conversation consistency evaluation"""
        print("\n💬 Consistency Evaluation")
        print("-" * 30)
        
        # Create conversation context
        conversation_history = [
            {"role": "user", "content": "I love hiking and spend most weekends outdoors"},
            {"role": "assistant", "content": "That's great! Hiking is excellent exercise and a wonderful way to connect with nature."},
            {"role": "user", "content": "I also enjoy photography during my hikes"},
            {"role": "assistant", "content": "Combining hiking with photography is perfect - you can capture beautiful landscapes and wildlife."}
        ]
        
        memories = [
            "User enjoys hiking and outdoor activities",
            "Spends weekends hiking in local trails",
            "Takes photos during hiking trips"
        ]
        
        # Test consistent response
        consistent_query = "What outdoor activities do I enjoy?"
        consistent_response = "Based on our conversation and your memories, you love hiking and often combine it with photography during your weekend outdoor adventures."
        
        try:
            consistent_score = await evaluate_conversation_consistency(
                query=consistent_query,
                memories=memories,
                response=consistent_response,
                conversation_history=conversation_history,
                session_id="demo-session"
            )
            
            print(f"✅ Consistent response score: {consistent_score.overall:.1f}/10")
            print(f"   Consistency rating: {consistent_score.consistency:.1f}/10")
            
            # Test inconsistent response
            inconsistent_response = "You prefer indoor activities like reading and watching movies."
            
            inconsistent_score = await evaluate_conversation_consistency(
                query=consistent_query,
                memories=memories,
                response=inconsistent_response,
                conversation_history=conversation_history,
                session_id="demo-session"
            )
            
            print(f"❌ Inconsistent response score: {inconsistent_score.overall:.1f}/10") 
            print(f"   Consistency rating: {inconsistent_score.consistency:.1f}/10")
            
            consistency_diff = consistent_score.consistency - inconsistent_score.consistency
            print(f"   Consistency discrimination: {consistency_diff:.1f} points")
            
        except Exception as e:
            print(f"❌ Consistency evaluation failed: {e}")
    
    async def _analyze_performance(self):
        """Analyze judge performance and reliability"""
        print("\n⚡ Performance Analysis")
        print("-" * 30)
        
        # Test multiple evaluations of the same case for consistency
        test_case = self.test_cases[1]  # Multi-hop case
        
        print("Testing judge consistency (3 runs of same evaluation)...")
        
        scores = []
        latencies = []
        
        for i in range(3):
            try:
                start_time = time.time()
                
                score = await evaluate_single_response(
                    query=test_case["query"],
                    memories=test_case["memories"],
                    response=test_case["good_response"],
                    reasoning_type=test_case["reasoning_type"]
                )
                
                latency = time.time() - start_time
                scores.append(score.overall)
                latencies.append(latency)
                
                print(f"   Run {i+1}: {score.overall:.1f}/10 ({latency:.2f}s)")
                
            except Exception as e:
                print(f"   Run {i+1}: Failed - {e}")
        
        if scores:
            avg_score = sum(scores) / len(scores)
            score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            avg_latency = sum(latencies) / len(latencies)
            
            print(f"\n📊 Consistency Analysis:")
            print(f"   Average score: {avg_score:.1f}/10")
            print(f"   Score variance: {score_variance:.2f}")
            print(f"   Average latency: {avg_latency:.2f}s")
            print(f"   Consistency rating: {'Good' if score_variance < 0.5 else 'Moderate' if score_variance < 1.0 else 'Poor'}")


async def main():
    """Main demo function"""
    # Check environment
    required_env = ["EVALUATION_MODE", "LLM_JUDGE_ENABLED"]
    api_keys = ["GEMINI_API_KEY", "OPENAI_API_KEY"]
    
    print("🔧 Environment Check")
    print("-" * 20)
    
    for env_var in required_env:
        value = os.getenv(env_var)
        print(f"{env_var}: {value or 'NOT SET'}")
    
    for key in api_keys:
        value = os.getenv(key)
        print(f"{key}: {'SET' if value else 'NOT SET'}")
    
    # Check if any API key is available
    if not any(os.getenv(key) for key in api_keys):
        print("\n❌ No API keys found!")
        print("Set GEMINI_API_KEY and/or OPENAI_API_KEY to run demo with real LLM calls.")
        print("\nTo run without API keys (mock mode):")
        print("export EVALUATION_MODE=true")
        print("export LLM_JUDGE_ENABLED=true")
        return
    
    # Run demo
    demo = LLMJudgeDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())