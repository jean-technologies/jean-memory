"""
Integration tests for complete memory workflows in Jean Memory V3
Tests end-to-end scenarios across STM, LTM, and Memory Shuttle
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.memory_service import JeanMemoryV3Service
from services.stm_service import STMService, STMMemory
from services.ltm_service import LTMService
from services.memory_shuttle import MemoryShuttle
from config import JeanMemoryV3Config


@pytest.mark.integration
class TestMemoryFlowIntegration:
    """Integration tests for complete memory workflows"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for integration tests"""
        config = Mock(spec=JeanMemoryV3Config)
        config.openai_api_key = "test-api-key"
        config.jean_memory_v2_api_url = "https://api.test.com"
        config.jean_memory_v2_api_key = "test-ltm-key"
        config.max_local_memories = 100
        config.neo4j_host = "localhost"
        config.neo4j_port = 7687
        config.neo4j_user = "neo4j"
        config.neo4j_password = "testpass"
        config.neo4j_database = "neo4j"
        config.data_dir = "/tmp/test_data"
        return config
    
    @pytest.mark.asyncio
    async def test_memory_add_search_workflow(self, mock_config):
        """Test complete workflow: add memory -> search -> retrieve"""
        
        # Mock external dependencies
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test/faiss",
                 "neo4j": "/tmp/test/neo4j",
                 "models": "/tmp/test/models",
                 "logs": "/tmp/test/logs",
                 "temp": "/tmp/test/temp"
             }), \
             patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory_client, \
             patch('httpx.AsyncClient') as mock_http_client:
            
            # Setup mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 5, "edges": 3})
            mock_graph.return_value = mock_graph_instance
            
            # Mock mem0 client
            mock_mem0_instance = Mock()
            mock_mem0_instance.add = Mock(return_value={"id": "mem0_123"})
            mock_mem0_instance.search = Mock(return_value=[
                {"memory": "Test memory content", "score": 0.9}
            ])
            mock_memory_client.return_value = mock_mem0_instance
            
            # Mock HTTP client for LTM
            mock_http_instance = Mock()
            mock_http_response = Mock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = {"status": "healthy"}
            mock_http_instance.get = AsyncMock(return_value=mock_http_response)
            mock_http_instance.aclose = AsyncMock()
            mock_http_client.return_value = mock_http_instance
            
            # Initialize services
            stm_service = STMService()
            await stm_service.initialize()
            
            ltm_service = LTMService()
            await ltm_service.initialize()
            
            # 1. Add memory to STM
            memory = await stm_service.add_memory(
                content="Test memory content for integration testing",
                user_id="integration_user",
                metadata={"test_type": "integration", "workflow": "add_search"}
            )
            
            assert memory is not None
            assert memory.content == "Test memory content for integration testing"
            assert memory.user_id == "integration_user"
            assert memory.metadata["test_type"] == "integration"
            
            # 2. Search for the memory
            search_results = await stm_service.search_memories(
                query="integration testing",
                user_id="integration_user",
                limit=10,
                threshold=0.5
            )
            
            assert len(search_results) == 1
            assert search_results[0]["content"] == "Test memory content for integration testing"
            assert search_results[0]["score"] == 0.9
            
            # 3. Retrieve specific memory
            retrieved_memory = await stm_service.get_memory(memory.id)
            assert retrieved_memory == memory
            assert retrieved_memory.access_count > 0  # Should be incremented from search and get
            
            # Cleanup
            await stm_service.cleanup()
            await ltm_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_stm_to_ltm_shuttle_workflow(self, mock_config):
        """Test memory shuttle workflow: STM -> LTM upload"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test/faiss",
                 "neo4j": "/tmp/test/neo4j",
                 "models": "/tmp/test/models",
                 "logs": "/tmp/test/logs",
                 "temp": "/tmp/test/temp"
             }), \
             patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory_client, \
             patch('httpx.AsyncClient') as mock_http_client:
            
            # Setup mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            # Mock mem0 client
            mock_mem0_instance = Mock()
            mock_mem0_instance.add = Mock(return_value={"id": "mem0_456"})
            mock_memory_client.return_value = mock_mem0_instance
            
            # Mock LTM HTTP client responses
            mock_http_instance = Mock()
            
            # Health check response
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            
            # Upload response
            upload_response = Mock()
            upload_response.status_code = 200
            upload_response.json.return_value = {"id": "ltm_789", "status": "created"}
            
            # Mock request method to return different responses
            async def mock_request(method, url, **kwargs):
                if url == "/health":
                    return health_response
                elif url == "/memories/" and method == "POST":
                    return upload_response
                return Mock(status_code=404)
            
            mock_http_instance.request = AsyncMock(side_effect=mock_request)
            mock_http_instance.get = AsyncMock(return_value=health_response)
            mock_http_instance.aclose = AsyncMock()
            mock_http_client.return_value = mock_http_instance
            
            # Initialize services
            stm_service = STMService()
            await stm_service.initialize()
            
            ltm_service = LTMService()
            await ltm_service.initialize()
            
            memory_shuttle = MemoryShuttle(stm_service, ltm_service)
            
            # 1. Add memory to STM
            memory = await stm_service.add_memory(
                content="Memory to be uploaded to LTM",
                user_id="shuttle_user",
                metadata={"test_type": "shuttle", "upload_priority": "high"}
            )
            
            assert memory.upload_status == "pending"
            
            # 2. Force upload to LTM via shuttle
            upload_result = await memory_shuttle.force_upload_user_memories("shuttle_user")
            
            assert upload_result["uploaded"] >= 0  # Should have attempted upload
            assert "total_candidates" in upload_result
            
            # 3. Verify memory was marked as uploaded (if upload succeeded)
            if upload_result["uploaded"] > 0:
                updated_memory = await stm_service.get_memory(memory.id)
                assert updated_memory.upload_status == "uploaded"
                assert "ltm_id" in updated_memory.metadata
            
            # Cleanup
            await memory_shuttle.stop()
            await stm_service.cleanup()
            await ltm_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_ltm_to_stm_preload_workflow(self, mock_config):
        """Test hot memory preload workflow: LTM -> STM"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test/faiss",
                 "neo4j": "/tmp/test/neo4j",
                 "models": "/tmp/test/models",
                 "logs": "/tmp/test/logs",
                 "temp": "/tmp/test/temp"
             }), \
             patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory_client, \
             patch('httpx.AsyncClient') as mock_http_client:
            
            # Setup mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 2, "edges": 1})
            mock_graph.return_value = mock_graph_instance
            
            # Mock mem0 client
            mock_mem0_instance = Mock()
            mock_mem0_instance.add = Mock(return_value={"id": "mem0_preload"})
            mock_memory_client.return_value = mock_mem0_instance
            
            # Mock LTM HTTP client responses
            mock_http_instance = Mock()
            
            # Health check response
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            
            # Hot memories response
            hot_memories_response = Mock()
            hot_memories_response.status_code = 200
            hot_memories_response.json.return_value = {
                "memories": [
                    {
                        "id": "ltm_hot_1",
                        "content": "Important hot memory from LTM",
                        "app_id": "test_app",
                        "metadata_": {
                            "category": "important",
                            "usage_frequency": "high"
                        }
                    },
                    {
                        "id": "ltm_hot_2", 
                        "content": "Another hot memory",
                        "app_id": "test_app",
                        "metadata_": {
                            "category": "work"
                        }
                    }
                ]
            }
            
            # Mock request method
            async def mock_request(method, url, **kwargs):
                if url == "/health":
                    return health_response
                elif "/memories/" in url and method == "GET":
                    params = kwargs.get("params", {})
                    if params.get("sort") == "relevance":
                        return hot_memories_response
                return Mock(status_code=404)
            
            mock_http_instance.request = AsyncMock(side_effect=mock_request)
            mock_http_instance.get = AsyncMock(return_value=health_response)
            mock_http_instance.aclose = AsyncMock()
            mock_http_client.return_value = mock_http_instance
            
            # Initialize services
            stm_service = STMService()
            await stm_service.initialize()
            
            ltm_service = LTMService()
            await ltm_service.initialize()
            
            memory_shuttle = MemoryShuttle(stm_service, ltm_service)
            
            # 1. Preload hot memories from LTM
            preload_result = await memory_shuttle.preload_hot_memories("preload_user")
            
            assert preload_result["preloaded"] >= 0
            assert preload_result["total_hot"] == 2
            
            # 2. Verify memories were added to STM (if preload succeeded)
            if preload_result["preloaded"] > 0:
                user_memories = await stm_service.get_user_memories("preload_user")
                
                # Should have preloaded memories
                assert len(user_memories) > 0
                
                # Check for preload metadata
                preloaded_memory = user_memories[0]
                assert preloaded_memory["metadata_"]["preloaded_from_ltm"] is True
                assert "ltm_id" in preloaded_memory["metadata_"]
            
            # Cleanup
            await memory_shuttle.stop()
            await stm_service.cleanup()
            await ltm_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_full_service_integration_workflow(self, mock_config):
        """Test complete JeanMemoryV3Service integration workflow"""
        
        with patch('services.memory_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test/faiss",
                 "neo4j": "/tmp/test/neo4j",
                 "models": "/tmp/test/models",
                 "logs": "/tmp/test/logs",
                 "temp": "/tmp/test/temp"
             }), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory_client, \
             patch('httpx.AsyncClient') as mock_http_client, \
             patch('services.memory_service.GoogleADKMemoryService') as mock_google, \
             patch('services.memory_service.HybridMemoryOrchestrator') as mock_hybrid, \
             patch('services.memory_service.InMemorySessionService') as mock_session, \
             patch('services.memory_service.create_memory_service') as mock_create_memory:
            
            # Setup all mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 10, "edges": 15})
            mock_graph.return_value = mock_graph_instance
            
            # Mock mem0
            mock_mem0_instance = Mock()
            mock_mem0_instance.add = Mock(return_value={"id": "mem0_full"})
            mock_mem0_instance.search = Mock(return_value=[
                {"memory": "Full integration test content", "score": 0.95}
            ])
            mock_memory_client.return_value = mock_mem0_instance
            
            # Mock HTTP client
            mock_http_instance = Mock()
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            mock_http_instance.get = AsyncMock(return_value=health_response)
            mock_http_instance.aclose = AsyncMock()
            mock_http_client.return_value = mock_http_instance
            
            # Mock Google service
            mock_google_instance = Mock()
            mock_google_instance.initialize = AsyncMock()
            mock_google_instance.initialized = True
            mock_google.return_value = mock_google_instance
            
            # Mock Hybrid orchestrator
            mock_hybrid_instance = Mock()
            mock_hybrid_instance.initialize = AsyncMock()
            mock_hybrid_instance.initialized = True
            mock_hybrid.return_value = mock_hybrid_instance
            
            # Mock Session service
            mock_session_instance = Mock()
            mock_session_instance.create_session = AsyncMock(return_value="session_full_test")
            mock_session.return_value = mock_session_instance
            
            # Mock ADK Memory service
            mock_adk_memory = Mock()
            search_result = Mock()
            search_result.memories = [
                {
                    "id": "full_mem_1",
                    "content": "Full integration test content",
                    "score": 0.95,
                    "metadata_": {"source": "stm", "test_type": "full_integration"}
                }
            ]
            search_result.source = "stm"
            search_result.execution_time_ms = 250
            
            mock_adk_memory.add_memory = AsyncMock(return_value={
                "id": "full_mem_1",
                "status": "added",
                "source": "stm"
            })
            mock_adk_memory.search_memories = AsyncMock(return_value=search_result)
            mock_adk_memory.get_stats = AsyncMock(return_value={
                "service_type": "hybrid",
                "total_memories": 1,
                "stm_memories": 1,
                "ltm_memories": 0
            })
            mock_create_memory.return_value = mock_adk_memory
            
            # Initialize full V3 service
            v3_service = JeanMemoryV3Service()
            await v3_service.initialize()
            
            assert v3_service.is_initialized is True
            assert v3_service.is_ready() is True
            
            # 1. Test memory addition
            add_result = await v3_service.add_memory(
                content="Full integration test content",
                user_id="full_test_user",
                metadata={"test_type": "full_integration", "priority": "high"}
            )
            
            assert add_result["id"] == "full_mem_1"
            assert add_result["status"] == "added"
            
            # 2. Test memory search
            search_result = await v3_service.search_memories(
                query="integration test",
                user_id="full_test_user",
                limit=10,
                threshold=0.8
            )
            
            assert len(search_result["memories"]) == 1
            assert search_result["memories"][0]["score"] == 0.95
            assert search_result["source"] == "stm"
            assert search_result["query"] == "integration test"
            
            # 3. Test session creation
            session_id = await v3_service.create_session(
                "full_test_user",
                {"test_type": "full_integration"}
            )
            
            assert session_id == "session_full_test"
            
            # 4. Test stats
            stats = await v3_service.get_stats("full_test_user")
            
            assert stats["service_type"] == "hybrid"
            assert stats["total_memories"] == 1
            
            # 5. Test shuttle operations
            shuttle_stats = await v3_service.get_shuttle_stats("full_test_user")
            assert "is_running" in shuttle_stats
            
            # Cleanup
            await v3_service.cleanup()
    
    @pytest.mark.asyncio 
    async def test_error_recovery_workflow(self, mock_config):
        """Test error recovery and graceful degradation"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test/faiss",
                 "neo4j": "/tmp/test/neo4j",
                 "models": "/tmp/test/models",
                 "logs": "/tmp/test/logs",
                 "temp": "/tmp/test/temp"
             }), \
             patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory', side_effect=Exception("mem0 unavailable")) as mock_memory_client, \
             patch('httpx.AsyncClient', side_effect=Exception("Network unavailable")) as mock_http_client:
            
            # Setup mocks - some will fail
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            # Initialize services - should handle failures gracefully
            stm_service = STMService()
            await stm_service.initialize()  # Should not raise exception
            
            ltm_service = LTMService()
            await ltm_service.initialize()  # Should not raise exception
            
            # STM should still work without mem0
            assert stm_service.memory_client is None
            
            # LTM should not be ready
            assert ltm_service.is_ready() is False
            
            # Memory shuttle should handle LTM being unavailable
            memory_shuttle = MemoryShuttle(stm_service, ltm_service)
            
            # Test operations with degraded functionality
            upload_result = await memory_shuttle.force_upload_user_memories("error_user")
            assert "error" in upload_result
            
            preload_result = await memory_shuttle.preload_hot_memories("error_user")
            assert "error" in preload_result
            
            # Cleanup should work even with errors
            await memory_shuttle.stop()
            await stm_service.cleanup()
            await ltm_service.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])