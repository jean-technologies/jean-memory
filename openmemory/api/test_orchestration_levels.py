#!/usr/bin/env python3
"""
Test script to verify orchestration level decision logic.
Tests the 4-level architecture:
1. No search (needs_context=false)
2. Simple search (fallback/error cases)  
3. Gemini Flash deeper search (relevant_context, deep_understanding)
4. Gemini 2.5 Pro super deep search (comprehensive_analysis -> deep_memory_query)
"""

import asyncio
import os
import sys
import logging

# Add the api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.utils.mcp_modules.ai_service import MCPAIService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_planner_decisions():
    """Test what strategy the AI planner chooses for different queries"""
    
    ai_service = MCPAIService()
    
    test_cases = [
        # Should trigger Level 4 (comprehensive_analysis)
        "what are my values",
        "what do I believe in", 
        "tell me about my philosophy",
        "who am I based on my memories",
        "what would I say about politics",
        "comprehensive analysis of my personality",
        "tell me everything about my background",
        
        # Should trigger Level 3 (deep_understanding)
        "tell me about my recent work",
        "what do you know about my projects", 
        "analyze my preferences",
        "explain my work patterns",
        
        # Should trigger Level 2 (relevant_context)
        "what's my email address",
        "remind me about that meeting",
        "what did I say about X",
        
        # Edge cases
        "thanks",
        "ok got it",
    ]
    
    logger.info("🧪 Testing AI Planner Decision Logic")
    logger.info("=" * 60)
    
    for query in test_cases:
        try:
            plan = await ai_service.create_context_plan(query)
            strategy = plan.get("context_strategy", "unknown")
            
            # Map strategy to level
            level_map = {
                "comprehensive_analysis": "🚀 Level 4 (Deep + Docs)",
                "deep_understanding": "🔥 Level 3 (Gemini Flash Deep)", 
                "relevant_context": "💬 Level 2 (Gemini Flash)",
                "unknown": "❓ Unknown"
            }
            
            level = level_map.get(strategy, f"❓ {strategy}")
            
            print(f"Query: '{query}'")
            print(f"  Strategy: {strategy}")
            print(f"  Level: {level}")
            print(f"  Search queries: {plan.get('search_queries', [])}")
            print()
            
        except Exception as e:
            logger.error(f"Error testing '{query}': {e}")
            print(f"Query: '{query}' - ERROR: {e}")
            print()

if __name__ == "__main__":
    # Test if we can import required modules
    try:
        asyncio.run(test_ai_planner_decisions())
    except ImportError as e:
        print(f"Import error - make sure you're in the right directory: {e}")
    except Exception as e:
        print(f"Test failed: {e}")