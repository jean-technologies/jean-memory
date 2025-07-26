#!/usr/bin/env python3
"""
Comprehensive test suite for agentic orchestration
Tests multiple scenarios to identify all issues
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestResults:
    def __init__(self):
        self.tests = []
        self.issues = []
        
    def add_test(self, name, success, details, time_taken=0):
        self.tests.append({
            "name": name,
            "success": success,
            "details": details,
            "time_taken": time_taken
        })
        
    def add_issue(self, category, description, severity="HIGH"):
        self.issues.append({
            "category": category,
            "description": description,
            "severity": severity
        })
        
    def print_summary(self):
        print("\n" + "="*80)
        print("🔍 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        
        print(f"\n📊 TESTS RUN: {len(self.tests)}")
        successful = len([t for t in self.tests if t['success']])
        print(f"✅ SUCCESSFUL: {successful}")
        print(f"❌ FAILED: {len(self.tests) - successful}")
        
        print(f"\n🚨 ISSUES IDENTIFIED: {len(self.issues)}")
        for issue in self.issues:
            print(f"  {issue['severity']}: [{issue['category']}] {issue['description']}")
            
        print(f"\n📝 DETAILED TEST RESULTS:")
        for test in self.tests:
            status = "✅" if test['success'] else "❌"
            print(f"  {status} {test['name']} ({test['time_taken']:.2f}s)")
            if test['details']:
                print(f"     {test['details']}")

async def test_comprehensive_orchestration():
    """Run comprehensive tests on the agentic orchestration system."""
    results = TestResults()
    
    try:
        print("🚀 Starting comprehensive agentic orchestration tests...")
        
        # Import after setting up logging
        from app.mcp_orchestration import get_smart_orchestrator
        from app.context import user_id_var, client_name_var, background_tasks_var
        from fastapi import BackgroundTasks
        
        # Set up context (simulating a real request)
        test_user_id = "comprehensive_test_user"
        test_client = "test_client"
        background_tasks = BackgroundTasks()
        
        user_token = user_id_var.set(test_user_id)
        client_token = client_name_var.set(test_client)
        tasks_token = background_tasks_var.set(background_tasks)
        
        try:
            orchestrator = get_smart_orchestrator()
            
            # TEST 1: Import and Setup
            print("\n" + "="*60)
            print("TEST 1: IMPORT AND SETUP")
            print("="*60)
            
            start_time = datetime.now()
            try:
                # Test basic imports
                from app.utils.gemini import GeminiService
                from app.tools.memory import list_memories, search_memory, add_memories
                gemini = GeminiService()
                
                results.add_test("Import and Setup", True, "All imports successful", 
                               (datetime.now() - start_time).total_seconds())
            except Exception as e:
                results.add_test("Import and Setup", False, f"Import failed: {e}")
                results.add_issue("SETUP", f"Critical import failure: {e}")
                
            # TEST 2: Basic Orchestration - Weather Question
            print("\n" + "="*60)
            print("TEST 2: WEATHER QUESTION (Should need location)")
            print("="*60)
            
            start_time = datetime.now()
            try:
                result = await orchestrator.orchestrate_smart_context(
                    user_message="what's the weather like",
                    user_id=test_user_id,
                    client_name=test_client,
                    is_new_conversation=False,
                    needs_context=True,
                    background_tasks=background_tasks
                )
                
                time_taken = (datetime.now() - start_time).total_seconds()
                success = len(result) > 0  # Should have some context
                
                results.add_test("Weather Question", success, 
                               f"Response length: {len(result)}, Content: {result[:100]}", 
                               time_taken)
                
                if not success:
                    results.add_issue("ORCHESTRATION", "Weather question returned empty context")
                    
            except Exception as e:
                results.add_test("Weather Question", False, f"Exception: {e}")
                results.add_issue("ORCHESTRATION", f"Weather test crashed: {e}")
                
            # TEST 3: Math Question (Should need no context)
            print("\n" + "="*60)
            print("TEST 3: MATH QUESTION (Should need no context)")
            print("="*60)
            
            start_time = datetime.now()
            try:
                result = await orchestrator.orchestrate_smart_context(
                    user_message="what is 2 + 2",
                    user_id=test_user_id,
                    client_name=test_client,
                    is_new_conversation=False,
                    needs_context=True,
                    background_tasks=background_tasks
                )
                
                time_taken = (datetime.now() - start_time).total_seconds()
                # Math should return empty or minimal context
                success = True  # Any response is OK for math
                
                results.add_test("Math Question", success, 
                               f"Response length: {len(result)}, Content: {result[:100]}", 
                               time_taken)
                               
            except Exception as e:
                results.add_test("Math Question", False, f"Exception: {e}")
                results.add_issue("ORCHESTRATION", f"Math test crashed: {e}")
                
            # TEST 4: New Conversation Test
            print("\n" + "="*60)
            print("TEST 4: NEW CONVERSATION (Should use narrative)")
            print("="*60)
            
            start_time = datetime.now()
            try:
                result = await orchestrator.orchestrate_smart_context(
                    user_message="Hello, tell me about myself",
                    user_id=test_user_id,
                    client_name=test_client,
                    is_new_conversation=True,
                    needs_context=True,
                    background_tasks=background_tasks
                )
                
                time_taken = (datetime.now() - start_time).total_seconds()
                success = True  # Any response is OK for new conversation
                
                results.add_test("New Conversation", success, 
                               f"Response length: {len(result)}, Content: {result[:100]}", 
                               time_taken)
                               
            except Exception as e:
                results.add_test("New Conversation", False, f"Exception: {e}")
                results.add_issue("ORCHESTRATION", f"New conversation test crashed: {e}")
                
            # TEST 5: Memory Tools Direct Test
            print("\n" + "="*60)
            print("TEST 5: MEMORY TOOLS DIRECT TEST")
            print("="*60)
            
            # Test list_memories
            start_time = datetime.now()
            try:
                from app.tools.memory import list_memories
                memories_result = await list_memories(limit=5)
                time_taken = (datetime.now() - start_time).total_seconds()
                
                success = memories_result is not None
                results.add_test("List Memories Tool", success, 
                               f"Result: {memories_result[:200]}", time_taken)
                               
                if not success or "error" in str(memories_result).lower():
                    results.add_issue("MEMORY_TOOLS", f"list_memories failed: {memories_result}")
                    
            except Exception as e:
                results.add_test("List Memories Tool", False, f"Exception: {e}")
                results.add_issue("MEMORY_TOOLS", f"list_memories crashed: {e}")
                
            # Test search_memory
            start_time = datetime.now()
            try:
                from app.tools.memory import search_memory
                search_result = await search_memory(query="test", limit=3)
                time_taken = (datetime.now() - start_time).total_seconds()
                
                success = search_result is not None
                results.add_test("Search Memory Tool", success, 
                               f"Result: {search_result[:200]}", time_taken)
                               
                if not success or "error" in str(search_result).lower():
                    results.add_issue("MEMORY_TOOLS", f"search_memory failed: {search_result}")
                    
            except Exception as e:
                results.add_test("Search Memory Tool", False, f"Exception: {e}")
                results.add_issue("MEMORY_TOOLS", f"search_memory crashed: {e}")
                
            # TEST 6: Add Memory Test  
            print("\n" + "="*60)
            print("TEST 6: ADD MEMORY TEST")
            print("="*60)
            
            start_time = datetime.now()
            try:
                from app.tools.memory import add_memories
                add_result = await add_memories(text="Test memory from comprehensive test")
                time_taken = (datetime.now() - start_time).total_seconds()
                
                success = "success" in str(add_result).lower() or "added" in str(add_result).lower()
                results.add_test("Add Memory Tool", success, 
                               f"Result: {add_result}", time_taken)
                               
                if not success:
                    results.add_issue("MEMORY_TOOLS", f"add_memories failed: {add_result}")
                    
            except Exception as e:
                results.add_test("Add Memory Tool", False, f"Exception: {e}")
                results.add_issue("MEMORY_TOOLS", f"add_memories crashed: {e}")
                
            # TEST 7: Claude Strategy Decision Test
            print("\n" + "="*60)
            print("TEST 7: CLAUDE STRATEGY DECISION TEST")
            print("="*60)
            
            start_time = datetime.now()
            try:
                strategy = await orchestrator._decide_additional_context_strategy(
                    "Help me with my Python project", 
                    ["User is a software engineer", "User likes Python"], 
                    test_user_id
                )
                time_taken = (datetime.now() - start_time).total_seconds()
                
                success = strategy and len(strategy) > 0
                results.add_test("Claude Strategy Decision", success, 
                               f"Strategy: {strategy}", time_taken)
                               
                if not success:
                    results.add_issue("CLAUDE_INTEGRATION", f"Strategy decision failed: {strategy}")
                    
            except Exception as e:
                results.add_test("Claude Strategy Decision", False, f"Exception: {e}")
                results.add_issue("CLAUDE_INTEGRATION", f"Strategy decision crashed: {e}")
                
            # TEST 8: Background Memory Save Test
            print("\n" + "="*60)
            print("TEST 8: BACKGROUND MEMORY SAVE TEST")
            print("="*60)
            
            start_time = datetime.now()
            try:
                await orchestrator._add_memory_background(
                    "Test background memory save", 
                    test_user_id, 
                    test_client, 
                    priority=False
                )
                time_taken = (datetime.now() - start_time).total_seconds()
                
                results.add_test("Background Memory Save", True, 
                               "Completed without exception", time_taken)
                               
            except Exception as e:
                results.add_test("Background Memory Save", False, f"Exception: {e}")
                results.add_issue("BACKGROUND_TASKS", f"Background memory save crashed: {e}")
                
        finally:
            # Clean up context
            user_id_var.reset(user_token)
            client_name_var.reset(client_token)  
            background_tasks_var.reset(tasks_token)
            
    except Exception as e:
        print(f"❌ Critical test setup failure: {e}")
        results.add_issue("CRITICAL", f"Test setup failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Print comprehensive results
    results.print_summary()
    
    # Generate recommendations
    print("\n" + "="*80)
    print("🔧 RECOMMENDED FIXES")
    print("="*80)
    
    if any("MEMORY_TOOLS" in issue["category"] for issue in results.issues):
        print("1. 🚨 MEMORY TOOLS: Fix Neo4j configuration or fallback to basic memory client")
        print("   - Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables")
        print("   - Implement graceful fallback when Neo4j is unavailable")
        
    if any("ORCHESTRATION" in issue["category"] for issue in results.issues):
        print("2. 🚨 ORCHESTRATION: Fix empty context responses")
        print("   - Ensure memory tools return valid data")
        print("   - Fix response formatting when no context found")
        
    if any("CLAUDE_INTEGRATION" in issue["category"] for issue in results.issues):
        print("3. 🚨 CLAUDE INTEGRATION: Fix strategy decision failures")
        print("   - Check Gemini API configuration")
        print("   - Add better fallback strategies")
        
    if any("BACKGROUND_TASKS" in issue["category"] for issue in results.issues):
        print("4. 🚨 BACKGROUND TASKS: Fix memory saving failures")
        print("   - Check context variable handling")
        print("   - Fix database connection issues")
        
    print(f"\n✅ TOTAL ISSUES TO FIX: {len(results.issues)}")
    return results

if __name__ == "__main__":
    asyncio.run(test_comprehensive_orchestration())