#!/usr/bin/env python3
"""
LLM Performance Testing for Jean Memory AI Planning
Tests actual response times for context planning prompts
"""

import asyncio
import time
import statistics
import json
import os
from typing import List, Dict
import sys
from pathlib import Path

# Add API path for imports
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root / "openmemory" / "api"))

async def test_ai_planning_performance():
    """Test actual LLM performance for context planning"""
    
    test_messages = [
        "can you remember that i have brown hair and brown eyes",
        "what's going on here - looking at Jean Memory API logs", 
        "Help me plan my career transition",
        "Continue working on the Python API we discussed",
        "Debug this memory storage issue"
    ]
    
    results = {
        'gemini_flash': [],
        'claude_haiku': [],
        'openai_gpt4o_mini': []
    }
    
    print("🧪 JEAN MEMORY LLM PERFORMANCE TESTING")
    print("=" * 60)
    print(f"Testing {len(test_messages)} context planning scenarios")
    print("Models: Gemini Flash (current) vs Claude Haiku vs OpenAI GPT-4o-mini")
    print()
    
    # Test each LLM with same prompts
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧪 Test {i}/{len(test_messages)}: '{message[:45]}...'")
        
        # Test Gemini Flash (current)
        try:
            start_time = time.time()
            gemini_result = await test_gemini_flash_planning(message)
            gemini_time = time.time() - start_time
            results['gemini_flash'].append(gemini_time)
            print(f"  ✅ Gemini Flash: {gemini_time:.2f}s")
        except Exception as e:
            print(f"  ❌ Gemini Flash: FAILED - {e}")
            results['gemini_flash'].append(999)
        
        await asyncio.sleep(0.5)  # Rate limiting
        
        # Test Claude Haiku
        try:
            start_time = time.time()
            claude_result = await test_claude_haiku_planning(message)
            claude_time = time.time() - start_time
            results['claude_haiku'].append(claude_time)
            print(f"  ✅ Claude Haiku: {claude_time:.2f}s")
        except Exception as e:
            print(f"  ❌ Claude Haiku: FAILED - {e}")
            results['claude_haiku'].append(999)
        
        await asyncio.sleep(0.5)  # Rate limiting
        
        # Test OpenAI GPT-4o-mini
        try:
            start_time = time.time()
            openai_result = await test_openai_planning(message)
            openai_time = time.time() - start_time
            results['openai_gpt4o_mini'].append(openai_time)
            print(f"  ✅ OpenAI GPT-4o-mini: {openai_time:.2f}s")
        except Exception as e:
            print(f"  ❌ OpenAI GPT-4o-mini: FAILED - {e}")
            results['openai_gpt4o_mini'].append(999)
        
        await asyncio.sleep(1)  # Rate limiting between tests
    
    # Calculate statistics
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE RESULTS SUMMARY")
    print("=" * 60)
    
    current_avg = None
    fastest_model = None
    fastest_time = float('inf')
    
    for model, times in results.items():
        # Filter out failed attempts
        valid_times = [t for t in times if t < 999]
        
        if not valid_times:
            print(f"\n❌ {model.upper()}: ALL TESTS FAILED")
            continue
            
        avg_time = statistics.mean(valid_times)
        median_time = statistics.median(valid_times)
        min_time = min(valid_times)
        max_time = max(valid_times)
        success_rate = len(valid_times) / len(times) * 100
        
        if model == 'gemini_flash':
            current_avg = avg_time
            
        if avg_time < fastest_time:
            fastest_time = avg_time
            fastest_model = model
        
        print(f"\n📈 {model.upper()}:")
        print(f"  Average:      {avg_time:.2f}s")
        print(f"  Median:       {median_time:.2f}s") 
        print(f"  Range:        {min_time:.2f}s - {max_time:.2f}s")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Calculate improvement potential vs current
        if current_avg and model != 'gemini_flash':
            improvement = ((current_avg - avg_time) / current_avg) * 100
            if improvement > 5:
                print(f"  🚀 {improvement:.1f}% FASTER than Gemini Flash")
            elif improvement < -5:
                print(f"  🐌 {abs(improvement):.1f}% SLOWER than Gemini Flash")
            else:
                print(f"  ≈ Similar performance to Gemini Flash")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS")
    print("=" * 60)
    
    if fastest_model and current_avg:
        improvement = ((current_avg - fastest_time) / current_avg) * 100
        print(f"\n🏆 FASTEST MODEL: {fastest_model.upper()}")
        print(f"💰 POTENTIAL SAVINGS: {improvement:.1f}% faster ({current_avg - fastest_time:.2f}s per call)")
        
        # Calculate daily savings based on production usage
        daily_calls = 1000  # Estimate based on logs
        daily_savings = (current_avg - fastest_time) * daily_calls
        print(f"📊 DAILY TIME SAVINGS: {daily_savings:.0f} seconds ({daily_savings/60:.1f} minutes)")
        
        if improvement > 20:
            print(f"🚨 STRONG RECOMMENDATION: Switch to {fastest_model}")
        elif improvement > 10:
            print(f"✅ RECOMMENDATION: Consider switching to {fastest_model}")
        else:
            print(f"💭 SUGGESTION: Current model is competitive")
    
    return results

async def test_gemini_flash_planning(message: str) -> dict:
    """Test Gemini Flash with actual context planning prompt"""
    try:
        from app.utils.gemini import GeminiService
        
        gemini = GeminiService()
        
        prompt = f"""
        Analyze this user message for optimal context retrieval strategy:
        Message: "{message}"
        
        Create targeted search terms that will find the MOST RELEVANT memories.
        
        Return JSON:
        {{
            "context_strategy": "relevant_context|recent_context|comprehensive_context",
            "search_queries": ["term1", "term2", "term3"],
            "should_save_memory": true,
            "memorable_content": "extracted facts if should_save_memory is true"
        }}
        """
        
        return await gemini.generate_response(prompt, response_format="text")
    except Exception as e:
        raise Exception(f"Gemini Flash failed: {e}")

async def test_claude_haiku_planning(message: str) -> dict:
    """Test Claude Haiku with same prompt"""
    import httpx
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not set")
    
    prompt = f"""
    Analyze this user message for optimal context retrieval strategy:
    Message: "{message}"
    
    Create targeted search terms that will find the MOST RELEVANT memories.
    
    Return JSON:
    {{
        "context_strategy": "relevant_context|recent_context|comprehensive_context", 
        "search_queries": ["term1", "term2", "term3"],
        "should_save_memory": true,
        "memorable_content": "extracted facts if should_save_memory is true"
    }}
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Claude API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return result.get('content', [{}])[0].get('text', '')

async def test_openai_planning(message: str) -> dict:
    """Test OpenAI GPT-4o-mini with same prompt"""
    import httpx
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY not set")
    
    prompt = f"""
    Analyze this user message for optimal context retrieval strategy:
    Message: "{message}"
    
    Create targeted search terms that will find the MOST RELEVANT memories.
    
    Return JSON:
    {{
        "context_strategy": "relevant_context|recent_context|comprehensive_context",
        "search_queries": ["term1", "term2", "term3"], 
        "should_save_memory": true,
        "memorable_content": "extracted facts if should_save_memory is true"
    }}
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return result['choices'][0]['message']['content']

if __name__ == "__main__":
    print("Starting LLM Performance Testing...")
    try:
        results = asyncio.run(test_ai_planning_performance())
        
        # Save results
        timestamp = int(time.time())
        results_file = f"llm_performance_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()