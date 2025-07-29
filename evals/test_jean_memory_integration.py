#!/usr/bin/env python3
"""
Test Jean Memory system integration with evaluations
Tests the actual jean_memory tool and orchestrator
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "openmemory" / "api"))

async def test_jean_memory_tool():
    """Test the actual jean_memory tool"""
    print("🧪 Testing Jean Memory Tool Integration")
    print("=" * 50)
    
    try:
        # Import the actual jean_memory tool
        from app.tools.orchestration import jean_memory
        from app.context import user_id_var, client_name_var, background_tasks_var
        from fastapi import BackgroundTasks
        
        test_user_id = "eval-test-user-001"
        test_client = "eval-test-client"
        
        # Set up context variables
        user_token = user_id_var.set(test_user_id)
        client_token = client_name_var.set(test_client)
        bg_tasks = BackgroundTasks()
        bg_token = background_tasks_var.set(bg_tasks)
        
        test_cases = [
            {
                "message": "Hi, I'm testing the system",
                "is_new": True,
                "needs_context": True,
                "description": "New conversation with context",
                "max_time": 5.0
            },
            {
                "message": "What's 2 + 2?",
                "is_new": False,
                "needs_context": False,
                "description": "No context needed",
                "max_time": 2.0
            },
            {
                "message": "Help me with my Python project",
                "is_new": False,
                "needs_context": True,
                "description": "Continuing conversation with context",
                "max_time": 4.0
            }
        ]
        
        results = []
        
        try:
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n{i}. {test_case['description']}")
                print(f"   Message: \"{test_case['message']}\"")
                print(f"   New: {test_case['is_new']}, Needs Context: {test_case['needs_context']}")
                
                start_time = time.time()
                
                try:
                    context = await jean_memory(
                        user_message=test_case['message'],
                        is_new_conversation=test_case['is_new'],
                        needs_context=test_case['needs_context']
                    )
                    
                    response_time = time.time() - start_time
                    success = True
                    error = None
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    context = ""
                    success = False
                    error = str(e)
                
                # Evaluate result
                time_ok = response_time <= test_case['max_time']
                context_provided = bool(context and context.strip())
                
                if success and time_ok and (context_provided or not test_case['needs_context']):
                    status = "✅ PASS"
                elif success:
                    status = "⚠️ PARTIAL"
                else:
                    status = "❌ FAIL"
                
                print(f"   Result: {status}")
                print(f"   Response Time: {response_time:.2f}s (target: {test_case['max_time']}s)")
                print(f"   Context Length: {len(context) if context else 0} chars")
                
                if error:
                    print(f"   Error: {error}")
                elif context:
                    preview = context[:100] + "..." if len(context) > 100 else context
                    print(f"   Context Preview: {preview}")
                
                results.append({
                    'test_case': test_case,
                    'success': success,
                    'response_time': response_time,
                    'context_length': len(context) if context else 0,
                    'time_ok': time_ok,
                    'context_provided': context_provided,
                    'error': error
                })
        
        finally:
            # Reset context variables
            user_id_var.reset(user_token)
            client_name_var.reset(client_token)
            background_tasks_var.reset(bg_token)
        
        # Calculate summary
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['success'])
        time_compliant = sum(1 for r in results if r['time_ok'])
        
        print(f"\n📊 JEAN MEMORY TOOL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}/{total_tests}")
        print(f"   Time Compliant: {time_compliant}/{total_tests}")
        print(f"   Overall: {'✅ PASS' if successful_tests == total_tests else '❌ FAIL'}")
        
        return successful_tests == total_tests
        
    except ImportError as e:
        print(f"❌ Cannot import Jean Memory components: {e}")
        print("   This test requires the full Jean Memory system to be available")
        return False
    except Exception as e:
        print(f"❌ Jean Memory tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_orchestrator_directly():
    """Test the orchestrator directly"""
    print("\n🧪 Testing Smart Orchestrator Integration")
    print("=" * 50)
    
    try:
        from app.mcp_orchestration import get_smart_orchestrator
        
        orchestrator = get_smart_orchestrator()
        
        test_cases = [
            {
                "message": "I'm a software engineer at Google",
                "user_id": "eval-test-user-002",
                "client": "claude",
                "is_new": False,
                "description": "Professional information",
                "expected_strategy": "targeted_search"
            },
            {
                "message": "What are my career goals?",
                "user_id": "eval-test-user-002", 
                "client": "claude",
                "is_new": False,
                "description": "Personal query",
                "expected_strategy": "comprehensive_analysis"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['description']}")
            print(f"   Message: \"{test_case['message']}\"")
            
            start_time = time.time()
            
            try:
                context = await orchestrator.orchestrate_smart_context(
                    user_message=test_case['message'],
                    user_id=test_case['user_id'],
                    client_name=test_case['client'],
                    is_new_conversation=test_case['is_new']
                )
                
                response_time = time.time() - start_time
                success = True
                error = None
                
            except Exception as e:
                response_time = time.time() - start_time
                context = ""
                success = False
                error = str(e)
            
            # Evaluate result
            time_ok = response_time <= 5.0  # Allow 5 seconds for orchestrator
            context_provided = bool(context and context.strip())
            
            status = "✅ PASS" if success and time_ok else "❌ FAIL"
            
            print(f"   Result: {status}")
            print(f"   Response Time: {response_time:.2f}s")
            print(f"   Context Length: {len(context) if context else 0} chars")
            
            if error:
                print(f"   Error: {error}")
            elif context:
                preview = context[:100] + "..." if len(context) > 100 else context
                print(f"   Context Preview: {preview}")
            
            results.append({
                'success': success,
                'response_time': response_time,
                'time_ok': time_ok,
                'context_provided': context_provided,
                'error': error
            })
        
        # Calculate summary
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['success'])
        
        print(f"\n📊 ORCHESTRATOR RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}/{total_tests}")
        print(f"   Overall: {'✅ PASS' if successful_tests == total_tests else '❌ FAIL'}")
        
        return successful_tests == total_tests
        
    except ImportError as e:
        print(f"❌ Cannot import orchestrator: {e}")
        return False
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_memory_triage_real():
    """Test memory triage with real AI system"""
    print("\n🧠 Testing Real Memory Triage")
    print("=" * 50)
    
    try:
        from app.mcp_orchestration import get_smart_orchestrator
        
        orchestrator = get_smart_orchestrator()
        
        test_messages = [
            ("I'm a product manager at Stripe", "REMEMBER", "Professional info"),
            ("What time is it?", "SKIP", "Simple question"),
            ("I prefer TypeScript over JavaScript", "REMEMBER", "Technical preference"),
            ("Thanks for the help!", "SKIP", "Acknowledgment")
        ]
        
        results = []
        
        for message, expected, description in test_messages:
            print(f"\n• {description}: \"{message}\"")
            
            try:
                start_time = time.time()
                analysis = await orchestrator._ai_memory_analysis(message)
                response_time = time.time() - start_time
                
                actual = "REMEMBER" if analysis['should_remember'] else "SKIP"
                correct = actual == expected
                
                status = "✅" if correct else "❌"
                print(f"  {status} Expected: {expected} | Got: {actual} ({response_time:.2f}s)")
                
                if analysis.get('content'):
                    print(f"     Content: {analysis['content'][:50]}...")
                
                results.append(correct)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                results.append(False)
        
        # Calculate accuracy
        correct_count = sum(results)
        total_count = len(results)
        accuracy = correct_count / total_count * 100
        
        print(f"\n📊 REAL TRIAGE RESULTS:")
        print(f"   Accuracy: {accuracy:.1f}% ({correct_count}/{total_count})")
        print(f"   Status: {'✅ PASS' if accuracy >= 75 else '❌ FAIL'}")
        
        return accuracy >= 75
        
    except ImportError as e:
        print(f"❌ Cannot import memory analysis: {e}")
        return False
    except Exception as e:
        print(f"❌ Real triage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run Jean Memory integration tests"""
    print("🚀 JEAN MEMORY SYSTEM INTEGRATION TESTS")
    print("Testing actual Jean Memory components")
    print("=" * 80)
    
    # Test each component
    tool_passed = await test_jean_memory_tool()
    orchestrator_passed = await test_orchestrator_directly()
    triage_passed = await test_memory_triage_real()
    
    # Overall results
    print(f"\n🎯 INTEGRATION TEST RESULTS:")
    print("=" * 50)
    print(f"Jean Memory Tool: {'✅ PASS' if tool_passed else '❌ FAIL'}")
    print(f"Smart Orchestrator: {'✅ PASS' if orchestrator_passed else '❌ FAIL'}")
    print(f"Real Memory Triage: {'✅ PASS' if triage_passed else '❌ FAIL'}")
    
    overall_passed = tool_passed and orchestrator_passed and triage_passed
    print(f"\nOverall Integration: {'🎉 ALL PASSED' if overall_passed else '⚠️ SOME FAILED'}")
    
    if overall_passed:
        print("\n✅ Jean Memory system is ready for evaluation framework!")
        print("   All core components are working correctly")
        print("   Can proceed with full evaluation suite")
    else:
        print("\n⚠️ Some integration issues found")
        print("   Evaluation framework can still run with available components")
    
    return 0 if overall_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)