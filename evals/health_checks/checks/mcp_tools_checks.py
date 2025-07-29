"""
MCP tools functionality health checks for Jean Memory
Tests the jean_memory tool and other critical MCP tools
"""

import asyncio
import os
import sys
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Add the API directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../openmemory/api'))

from .base import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)

class MCPToolsHealthCheck(HealthCheck):
    """MCP tools functionality health checks"""
    
    def __init__(self):
        super().__init__("MCP Tools")
        
    def is_critical(self) -> bool:
        """MCP tools are critical for system functionality"""
        return True
    
    async def run_checks(self, level: str = "critical") -> HealthCheckResult:
        """Run MCP tools functionality checks"""
        result = HealthCheckResult(self.name)
        
        # Core MCP infrastructure
        await self._check_mcp_imports(result)
        await self._check_context_system(result)
        
        # jean_memory tool (the heart of the system)
        await self._check_jean_memory_tool(result)
        
        # Other memory tools
        await self._check_memory_tools(result)
        
        # Document tools (if comprehensive)
        if level == "comprehensive":
            await self._check_document_tools(result)
        
        return result
    
    async def _check_mcp_imports(self, result: HealthCheckResult) -> None:
        """Check that MCP-related imports work correctly"""
        try:
            # Test 1: MCP server imports
            try:
                from app.mcp_server import mcp
                result.add_check("MCP - Server Import", True, "MCP server imported successfully")
            except ImportError as e:
                result.add_check("MCP - Server Import", False, f"MCP server import failed: {e}")
                return
            
            # Test 2: MCP orchestration imports
            try:
                from app.mcp_orchestration import get_smart_orchestrator
                result.add_check("MCP - Orchestration Import", True, "MCP orchestration imported successfully")
            except ImportError as e:
                result.add_check("MCP - Orchestration Import", False, f"Orchestration import failed: {e}")
                return
            
            # Test 3: Tool imports
            try:
                from app.tools.orchestration import jean_memory
                from app.tools.memory import add_memories, search_memory, list_memories
                result.add_check("MCP - Tools Import", True, "MCP tools imported successfully")
            except ImportError as e:
                result.add_check("MCP - Tools Import", False, f"Tools import failed: {e}")
                return
                
        except Exception as e:
            result.add_check("MCP - Import General", False, f"Unexpected import error: {e}")
    
    async def _check_context_system(self, result: HealthCheckResult) -> None:
        """Check the context variable system that MCP tools depend on"""
        try:
            # Test 1: Context variables import
            try:
                from app.context import user_id_var, client_name_var, background_tasks_var
                result.add_check("Context - Variables Import", True, "Context variables imported successfully")
            except ImportError as e:
                result.add_check("Context - Variables Import", False, f"Context import failed: {e}")
                return
            
            # Test 2: Test context setting and getting
            try:
                from fastapi import BackgroundTasks
                
                # Set test context
                test_user_id = "health_check_user"
                test_client = "health_check_client"
                background_tasks = BackgroundTasks()
                
                user_token = user_id_var.set(test_user_id)
                client_token = client_name_var.set(test_client)
                tasks_token = background_tasks_var.set(background_tasks)
                
                try:
                    # Verify context is set correctly
                    assert user_id_var.get() == test_user_id
                    assert client_name_var.get() == test_client
                    assert background_tasks_var.get() == background_tasks
                    
                    result.add_check("Context - Variable Setting", True, "Context variables work correctly")
                    
                finally:
                    # Clean up context
                    user_id_var.reset(user_token)
                    client_name_var.reset(client_token)
                    background_tasks_var.reset(tasks_token)
                    
            except Exception as e:
                result.add_check("Context - Variable Setting", False, f"Context system failed: {e}")
                
        except Exception as e:
            result.add_check("Context - General", False, f"Unexpected context error: {e}")
    
    async def _check_jean_memory_tool(self, result: HealthCheckResult) -> None:
        """Check the jean_memory tool - the heart of the system"""
        try:
            # Test 1: Import jean_memory tool
            try:
                from app.tools.orchestration import jean_memory
                result.add_check("jean_memory - Import", True, "jean_memory tool imported successfully")
            except ImportError as e:
                result.add_check("jean_memory - Import", False, f"jean_memory import failed: {e}")
                return
            
            # Test 2: Check orchestrator initialization
            try:
                from app.mcp_orchestration import get_smart_orchestrator
                orchestrator = get_smart_orchestrator()
                if orchestrator:
                    result.add_check("jean_memory - Orchestrator", True, "Smart orchestrator initialized")
                else:
                    result.add_check("jean_memory - Orchestrator", False, "Orchestrator is None")
                    return
            except Exception as e:
                result.add_check("jean_memory - Orchestrator", False, f"Orchestrator init failed: {e}")
                return
            
            # Test 3: Test jean_memory tool execution (lightweight test)
            try:
                from app.context import user_id_var, client_name_var, background_tasks_var
                from fastapi import BackgroundTasks
                
                # Set up test context
                test_user_id = "jean_memory_health_check"
                test_client = "health_check"
                background_tasks = BackgroundTasks()
                
                user_token = user_id_var.set(test_user_id)
                client_token = client_name_var.set(test_client)
                tasks_token = background_tasks_var.set(background_tasks)
                
                try:
                    # Test with a simple question that should not need context
                    response = await jean_memory(
                        user_message="What is 2+2?",
                        is_new_conversation=False,  
                        needs_context=False  # Should return quickly
                    )
                    
                    if response and isinstance(response, str):
                        result.add_check("jean_memory - Execution", True, 
                                       f"Tool executed successfully, response length: {len(response)}")
                    else:
                        result.add_check("jean_memory - Execution", False, 
                                       f"Invalid response: {type(response)}")
                        
                finally:
                    # Clean up context
                    user_id_var.reset(user_token)
                    client_name_var.reset(client_token)
                    background_tasks_var.reset(tasks_token)
                    
            except Exception as e:
                result.add_check("jean_memory - Execution", False, f"Tool execution failed: {e}")
                
        except Exception as e:
            result.add_check("jean_memory - General", False, f"Unexpected jean_memory error: {e}")
    
    async def _check_memory_tools(self, result: HealthCheckResult) -> None:
        """Check the basic memory operation tools"""
        try:
            # Set up test context for memory tools
            from app.context import user_id_var, client_name_var, background_tasks_var
            from fastapi import BackgroundTasks
            
            test_user_id = "memory_tools_health_check"
            test_client = "health_check"
            background_tasks = BackgroundTasks()
            
            user_token = user_id_var.set(test_user_id)
            client_token = client_name_var.set(test_client)
            tasks_token = background_tasks_var.set(background_tasks)
            
            try:
                # Test 1: list_memories tool
                try:
                    from app.tools.memory import list_memories
                    memories_result = await list_memories(limit=1)
                    
                    if memories_result and isinstance(memories_result, str):
                        result.add_check("Memory Tools - list_memories", True, 
                                       "list_memories executed successfully")
                    else:
                        result.add_check("Memory Tools - list_memories", False, 
                                       f"Invalid response: {type(memories_result)}")
                        
                except Exception as e:
                    result.add_check("Memory Tools - list_memories", False, f"list_memories failed: {e}")
                
                # Test 2: search_memory tool
                try:
                    from app.tools.memory import search_memory
                    search_result = await search_memory(query="test", limit=1)
                    
                    if search_result and isinstance(search_result, str):
                        result.add_check("Memory Tools - search_memory", True, 
                                       "search_memory executed successfully")
                    else:
                        result.add_check("Memory Tools - search_memory", False, 
                                       f"Invalid response: {type(search_result)}")
                        
                except Exception as e:
                    result.add_check("Memory Tools - search_memory", False, f"search_memory failed: {e}")
                
                # Test 3: add_memories tool (lightweight test)
                try:
                    from app.tools.memory import add_memories
                    add_result = await add_memories(text="Health check test memory", tags=["health_check"])
                    
                    if add_result and isinstance(add_result, str):
                        result.add_check("Memory Tools - add_memories", True, 
                                       "add_memories executed successfully")
                    else:
                        result.add_check("Memory Tools - add_memories", False, 
                                       f"Invalid response: {type(add_result)}")
                        
                except Exception as e:
                    result.add_check("Memory Tools - add_memories", False, f"add_memories failed: {e}")
                    
            finally:
                # Clean up context
                user_id_var.reset(user_token)
                client_name_var.reset(client_token)
                background_tasks_var.reset(tasks_token)
                
        except Exception as e:
            result.add_check("Memory Tools - General", False, f"Unexpected memory tools error: {e}")
    
    async def _check_document_tools(self, result: HealthCheckResult) -> None:
        """Check document processing tools (comprehensive check only)"""
        try:
            # Test 1: Import document tools
            try:
                from app.tools.documents import store_document
                result.add_check("Document Tools - Import", True, "Document tools imported successfully")
            except ImportError as e:
                result.add_check("Document Tools - Import", False, f"Document tools import failed: {e}")
                return
            
            # Test 2: Test basic document tool functionality
            try:
                from app.context import user_id_var, client_name_var, background_tasks_var
                from fastapi import BackgroundTasks
                
                test_user_id = "document_health_check"
                test_client = "health_check"
                background_tasks = BackgroundTasks()
                
                user_token = user_id_var.set(test_user_id)
                client_token = client_name_var.set(test_client)
                tasks_token = background_tasks_var.set(background_tasks)
                
                try:
                    # Test with minimal document
                    doc_result = await store_document(
                        content="Health check document test",
                        title="Health Check Test",
                        source="health_check"
                    )
                    
                    if doc_result and isinstance(doc_result, str):
                        result.add_check("Document Tools - store_document", True, 
                                       "store_document executed successfully")
                    else:
                        result.add_check("Document Tools - store_document", False, 
                                       f"Invalid response: {type(doc_result)}")
                        
                finally:
                    # Clean up context
                    user_id_var.reset(user_token)
                    client_name_var.reset(client_token)
                    background_tasks_var.reset(tasks_token)
                    
            except Exception as e:
                result.add_check("Document Tools - store_document", False, f"store_document failed: {e}")
                
        except Exception as e:
            result.add_check("Document Tools - General", False, f"Unexpected document tools error: {e}")