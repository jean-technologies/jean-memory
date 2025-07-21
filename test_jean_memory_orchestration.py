#!/usr/bin/env python3
"""
Test script for the new Jean Memory intelligent orchestration system.
Tests the lightning-fast context relevance checking and smart quality scoring.

Run from: /Users/jonathanpolitzki/Desktop/Jean Memory/your-memory/openmemory/api/
"""

import asyncio
import os
import sys
import time
import json
from typing import Dict, Any

# Add the API directory to Python path
API_DIR = "/Users/jonathanpolitzki/Desktop/Jean Memory/your-memory/openmemory/api"
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

# Test configuration
TEST_USER_ID = os.environ.get("TEST_USER_ID", "test-user-orchestration-123")
TEST_CLIENT_NAME = os.environ.get("TEST_CLIENT_NAME", "test_orchestration_client")

# Mock environment setup for testing
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

async def test_lightning_fast_context_check():
    """Test the lightning-fast context relevance checking logic."""
    print("🚀 Testing Lightning Fast Context Check...")
    
    try:
        from app.mcp_orchestration import SmartContextOrchestrator
        orchestrator = SmartContextOrchestrator()
        
        test_cases = [
            # Should exit FAST - heuristic catches (< 1ms)
            {"message": "hello", "expected": False, "reason_contains": "heuristic_greeting"},
            {"message": "thanks", "expected": False, "reason_contains": "heuristic_greeting"}, 
            {"message": "ok", "expected": False, "reason_contains": "heuristic_greeting"},
            {"message": "what is python", "expected": False, "reason_contains": "heuristic_factual"},
            {"message": "how do I install numpy", "expected": False, "reason_contains": "heuristic_factual"},
            
            # Should need context - heuristic catches (< 1ms)  
            {"message": "remember when we discussed my project", "expected": True, "reason_contains": "heuristic_personal"},
            {"message": "tell me about my work", "expected": True, "reason_contains": "heuristic_personal"},
            {"message": "i'm building a new app", "expected": True, "reason_contains": "heuristic_personal"},
            
            # Borderline cases - will use AI check (< 2s)
            {"message": "how should I approach this problem?", "expected": None, "reason_contains": "flash_ai"},
            {"message": "what do you think about this idea?", "expected": None, "reason_contains": "flash_ai"},
        ]
        
        total_time = 0
        fast_exits = 0
        
        for i, test_case in enumerate(test_cases, 1):
            message = test_case["message"]
            expected = test_case["expected"]
            
            print(f"  Test {i}: '{message}'")
            
            start_time = time.time()
            try:
                should_provide, reason = await orchestrator._lightning_fast_context_check(message)
                duration = time.time() - start_time
                total_time += duration
                
                print(f"    ✅ Result: {should_provide} ({reason}) in {duration*1000:.1f}ms")
                
                # Check if it's a fast exit (< 10ms for heuristics)
                if duration < 0.01:
                    fast_exits += 1
                    print(f"    ⚡ FAST EXIT!")
                
                # Validate expectations for definite cases
                if expected is not None and should_provide != expected:
                    print(f"    ❌ FAILED: Expected {expected}, got {should_provide}")
                    return False
                    
                # Check reason contains expected substring
                if not any(substr in reason for substr in test_case["reason_contains"]):
                    print(f"    ⚠️  Unexpected reason: {reason}")
                
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
                return False
        
        avg_time = total_time / len(test_cases) * 1000
        print(f"\n  📊 Results:")
        print(f"    • Average time: {avg_time:.1f}ms")
        print(f"    • Fast exits: {fast_exits}/{len(test_cases)}")
        print(f"    • Total time: {total_time:.2f}s")
        
        return True
        
    except ImportError as e:
        print(f"    ❌ Import error: {e}")
        print("    Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}")
        return False

async def test_context_quality_scoring():
    """Test the smart context quality scoring system."""
    print("\n🎯 Testing Context Quality Scoring...")
    
    try:
        from app.mcp_orchestration import SmartContextOrchestrator
        orchestrator = SmartContextOrchestrator()
        
        test_cases = [
            {
                "name": "High Quality Context",
                "user_message": "Tell me about my Python machine learning projects",
                "context_results": {
                    "ai_guided_context": [
                        "User is working on a machine learning project using Python and TensorFlow",
                        "Has experience with Python data science libraries like pandas and scikit-learn", 
                        "Recently asked about neural network architectures for image classification",
                        "Prefers using Jupyter notebooks for machine learning experiments"
                    ]
                },
                "expected": True
            },
            {
                "name": "Poor Quality Context",
                "user_message": "What's the weather like today?",
                "context_results": {
                    "relevant_memories": {
                        "1": "User likes to read books about history",
                        "2": "Had dinner at Italian restaurant last week",
                        "3": "Prefers tea over coffee in the morning"
                    }
                },
                "expected": False
            },
            {
                "name": "No Context Items",
                "user_message": "Hello there",
                "context_results": {},
                "expected": False
            },
            {
                "name": "Too Few Results",
                "user_message": "Help me with coding",
                "context_results": {
                    "ai_guided_context": ["User knows some JavaScript"]
                },
                "expected": False
            }
        ]
        
        for test_case in test_cases:
            name = test_case["name"]
            user_message = test_case["user_message"]
            context_results = test_case["context_results"]
            expected = test_case["expected"]
            
            print(f"  Testing: {name}")
            print(f"    Message: '{user_message}'")
            
            is_quality, reason = orchestrator._evaluate_context_quality(context_results, user_message)
            
            print(f"    ✅ Result: {is_quality} ({reason})")
            
            if is_quality != expected:
                print(f"    ❌ FAILED: Expected {expected}, got {is_quality}")
                return False
            else:
                print(f"    ✅ PASSED")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

async def test_jean_memory_tool_integration():
    """Test the jean_memory tool integration with our new orchestration."""
    print("\n🌟 Testing jean_memory Tool Integration...")
    
    try:
        # Mock the context variables for testing
        from app.context import user_id_var, client_name_var
        from fastapi import BackgroundTasks
        
        # Set context
        user_token = user_id_var.set(TEST_USER_ID)
        client_token = client_name_var.set(TEST_CLIENT_NAME)
        
        try:
            from app.tools.orchestration import jean_memory
            
            test_cases = [
                {
                    "name": "Simple Greeting - Should Exit Fast",
                    "message": "hello",
                    "is_new_conversation": False,
                    "expect_empty": True
                },
                {
                    "name": "Personal Question - Should Provide Context", 
                    "message": "what did we discuss about my coding projects?",
                    "is_new_conversation": False,
                    "expect_empty": False
                },
                {
                    "name": "New Conversation - Should Use Deep Analysis",
                    "message": "Hi, I'm Jonathan and I work on AI systems",
                    "is_new_conversation": True,
                    "expect_empty": False
                }
            ]
            
            for test_case in test_cases:
                name = test_case["name"]
                message = test_case["message"]
                is_new_conversation = test_case["is_new_conversation"]
                expect_empty = test_case["expect_empty"]
                
                print(f"  Testing: {name}")
                print(f"    Message: '{message}'")
                print(f"    New conversation: {is_new_conversation}")
                
                start_time = time.time()
                
                try:
                    result = await jean_memory(message, is_new_conversation)
                    duration = time.time() - start_time
                    
                    is_empty = len(result.strip()) == 0
                    
                    print(f"    ✅ Duration: {duration:.2f}s")
                    print(f"    📊 Result length: {len(result)} chars")
                    print(f"    📝 Is empty: {is_empty}")
                    
                    if expect_empty and not is_empty:
                        print(f"    ❌ FAILED: Expected empty result but got: {result[:100]}...")
                        return False
                    elif not expect_empty and is_empty:
                        print(f"    ❌ FAILED: Expected context but got empty result")
                        return False
                    else:
                        print(f"    ✅ PASSED")
                    
                    if result:
                        print(f"    💬 Preview: {result[:150]}...")
                    
                except asyncio.TimeoutError:
                    print(f"    ⏰ TIMEOUT after {time.time() - start_time:.2f}s")
                    return False
                except Exception as e:
                    print(f"    ❌ ERROR: {e}")
                    return False
                
                print()
        
        finally:
            # Clean up context
            user_id_var.reset(user_token)
            client_name_var.reset(client_token)
        
        return True
        
    except ImportError as e:
        print(f"    ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

async def main():
    """Run all orchestration tests."""
    print("🧪 JEAN MEMORY ORCHESTRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_lightning_fast_context_check,
        test_context_quality_scoring,
        test_jean_memory_tool_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_func.__name__} PASSED\n")
            else:
                print(f"❌ {test_func.__name__} FAILED\n")
        except Exception as e:
            print(f"💥 {test_func.__name__} CRASHED: {e}\n")
    
    print("=" * 50)
    print(f"🏁 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Jean Memory orchestration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    exit(0 if success else 1)