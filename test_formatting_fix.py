#!/usr/bin/env python3
"""
Test the formatting fix locally before pushing to production
"""

import sys
from pathlib import Path

# Add API path for imports
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root / "openmemory" / "api"))

def test_format_layered_context():
    """Test the _format_layered_context function with mock data"""
    
    # Mock the orchestrator's formatting function
    class MockOrchestrator:
        def _format_layered_context(self, context_results, plan):
            """Copy of the actual function for testing"""
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"🎨 [Format] Starting format with context_results type: {type(context_results)}")
            logger.debug(f"🎨 [Format] Context results keys: {list(context_results.keys()) if isinstance(context_results, dict) else 'Not a dict'}")
            
            if not context_results or isinstance(context_results, Exception):
                logger.warning(f"🎨 [Format] Empty or exception context_results: {context_results}")
                return ""

            context_parts = []
            context_strategy = plan.get("context_strategy", "targeted_search")
            
            if context_strategy == "comprehensive_analysis":
                # COMPREHENSIVE ANALYSIS: Show detailed, comprehensive information
                comprehensive_memories = context_results.get('comprehensive_memories', {})
                
                if comprehensive_memories:
                    # Group memories by relevance/type for better organization
                    memory_list = list(comprehensive_memories.values())
                    
                    # Show comprehensive context in structured format
                    if len(memory_list) > 15:
                        # Split into multiple sections for very comprehensive analysis
                        professional_info = [m for m in memory_list if any(keyword in m.lower() for keyword in ['work', 'project', 'build', 'develop', 'engineer', 'company'])]
                        personal_info = [m for m in memory_list if any(keyword in m.lower() for keyword in ['prefer', 'love', 'like', 'value', 'interest'])]
                        technical_info = [m for m in memory_list if any(keyword in m.lower() for keyword in ['python', 'javascript', 'ml', 'ai', 'code', 'tech'])]
                        other_info = [m for m in memory_list if m not in professional_info + personal_info + technical_info]
                        
                        if professional_info:
                            context_parts.append(f"Professional Background: {'; '.join(professional_info[:8])}")
                        if technical_info:
                            context_parts.append(f"Technical Expertise: {'; '.join(technical_info[:6])}")
                        if personal_info:
                            context_parts.append(f"Personal Preferences: {'; '.join(personal_info[:4])}")
                        if other_info:
                            context_parts.append(f"Additional Context: {'; '.join(other_info[:4])}")
                    else:
                        # For moderate amounts, show all in comprehensive format
                        context_parts.append(f"Comprehensive Context: {'; '.join(memory_list)}")
            
            elif context_strategy == "deep_understanding":
                # NEW CONVERSATIONS: Let AI intelligence determine what's most important to show
                ai_context = context_results.get('ai_guided_context', [])
                
                if ai_context:
                    # For new conversations, show more context but let the AI's search decisions guide what's shown
                    # The AI planner already determined what was most relevant to search for
                    comprehensive_context = ai_context[:12]  # Show up to 12 most relevant pieces
                    
                    if len(comprehensive_context) > 6:
                        # Split into two logical groups if we have enough context
                        primary_context = comprehensive_context[:6]
                        secondary_context = comprehensive_context[6:]
                        
                        context_parts.append(f"Core Context: {'; '.join(primary_context)}")
                        context_parts.append(f"Additional Context: {'; '.join(secondary_context)}")
                    else:
                        context_parts.append(f"Relevant Context: {'; '.join(comprehensive_context)}")
                        
            else:
                # CONTINUING CONVERSATIONS: Lean, targeted context only
                
                # Check for system directives first
                behavioral = context_results.get('behavioral', [])
                if behavioral:
                    priority_behavioral = [b for b in behavioral if 'SYSTEM DIRECTIVE' in b or 'prefer' in b.lower()]
                    if priority_behavioral:
                        context_parts.append(f"Preferences: {'; '.join(priority_behavioral[:1])}")
                
                # Show relevant context
                query_specific = context_results.get('query_specific', [])
                relevant_memories = context_results.get('relevant_memories', {})
                ai_context = context_results.get('ai_guided_context', [])
                
                if query_specific:
                    context_parts.append(f"Relevant: {'; '.join(query_specific[:2])}")
                elif relevant_memories:
                    mem_list = list(relevant_memories.values())[:2]
                    if mem_list:
                        context_parts.append(f"Relevant: {'; '.join(mem_list)}")
                elif ai_context:
                    context_parts.append(f"Relevant: {'; '.join(ai_context[:2])}")

            if not context_parts:
                logger.warning(f"🎨 [Format] No context parts found! Strategy: {context_strategy}, Context keys: {list(context_results.keys())}")
                return ""

            # Simple, clean formatting
            final_context = ""
            if context_strategy == "comprehensive_analysis":
                final_context = f"---\n[Jean Memory Context - Comprehensive Analysis]\n" + "\n".join(context_parts) + "\n---"
            elif context_strategy == "deep_understanding":
                final_context = f"---\n[Jean Memory Context - New Conversation]\n" + "\n".join(context_parts) + "\n---"
            else:
                final_context = f"---\n[Jean Memory Context]\n" + "\n".join(context_parts) + "\n---"
            
            logger.info(f"🎨 [Format] Generated context length: {len(final_context)} chars")
            return final_context
    
    # Test scenarios
    print("🧪 TESTING FORMATTING FUNCTION")
    print("=" * 50)
    
    orchestrator = MockOrchestrator()
    
    # Test 1: Relevant context (what's failing in production)
    print("\n🧪 Test 1: Relevant Context (Production Scenario)")
    context_results = {
        "relevant_memories": {
            "1": "User loves frogs",
            "2": "User's favorite animals are dogs and frogs", 
            "3": "User is a morning person",
            "4": "User ate alligator in Florida once"
        }
    }
    plan = {"context_strategy": "relevant_context"}
    
    result = orchestrator._format_layered_context(context_results, plan)
    print(f"✅ Result length: {len(result)} chars")
    print(f"✅ Result preview: {result[:100]}...")
    
    # Test 2: Empty context
    print("\n🧪 Test 2: Empty Context")
    empty_context = {"relevant_memories": {}}
    result2 = orchestrator._format_layered_context(empty_context, plan)
    print(f"✅ Empty result length: {len(result2)} chars")
    
    # Test 3: Deep understanding
    print("\n🧪 Test 3: Deep Understanding")
    deep_context = {
        "ai_guided_context": [
            "User is building Jean Memory", 
            "User prefers irreverent thinking",
            "User values focus as most misallocated resource"
        ]
    }
    deep_plan = {"context_strategy": "deep_understanding"}
    result3 = orchestrator._format_layered_context(deep_context, deep_plan)
    print(f"✅ Deep result length: {len(result3)} chars")
    print(f"✅ Deep result preview: {result3[:100]}...")
    
    # Test 4: What's happening in production
    print("\n🧪 Test 4: Production Issue Simulation")
    # This simulates what the search function returns
    production_context = {"relevant_memories": {}}  # Empty dict like in production
    production_plan = {"context_strategy": "relevant_context"}
    result4 = orchestrator._format_layered_context(production_context, production_plan)
    print(f"❌ Production issue result length: {len(result4)} chars")
    
    if len(result4) == 0:
        print("💡 FOUND THE ISSUE: Empty relevant_memories dict returns 0 chars!")
    
    return len(result) > 0 and len(result3) > 0

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    success = test_format_layered_context()
    
    if success:
        print("\n✅ FORMATTING FUNCTION WORKS CORRECTLY")
        print("The issue is that relevant_memories is empty in production")
    else:
        print("\n❌ FORMATTING FUNCTION HAS ISSUES")