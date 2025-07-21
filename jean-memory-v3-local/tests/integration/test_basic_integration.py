"""
Basic integration tests to verify integration testing setup
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.stm_service import STMService, STMMemory
from services.ltm_service import LTMService
from services.memory_shuttle import MemoryShuttle
from config import JeanMemoryV3Config


@pytest.mark.integration
class TestBasicIntegration:
    """Basic integration tests"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        config = Mock(spec=JeanMemoryV3Config)
        config.openai_api_key = "test-key"
        config.max_local_memories = 100
        config.neo4j_host = "localhost"
        config.neo4j_port = 7687
        config.neo4j_user = "neo4j"
        config.neo4j_password = "testpass"
        config.data_dir = "/tmp/test"
        return config
    
    @pytest.mark.asyncio
    async def test_stm_service_basic_integration(self, mock_config):
        """Test basic STM service integration"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test/faiss",
                 "neo4j": "/tmp/test/neo4j",
                 "models": "/tmp/test/models",
                 "logs": "/tmp/test/logs",
                 "temp": "/tmp/test/temp"
             }), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory:
            
            # Setup mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            mock_memory_instance = Mock()
            mock_memory_instance.add = Mock(return_value={"id": "test_mem"})
            mock_memory.return_value = mock_memory_instance
            
            # Test service initialization
            stm = STMService()
            await stm.initialize()
            
            assert stm.is_initialized is True
            mock_graph_instance.initialize.assert_called_once()
            
            # Test memory addition
            memory = await stm.add_memory(
                content="Integration test memory",
                user_id="integration_user",
                metadata={"test": "integration"}
            )
            
            assert memory is not None
            assert memory.content == "Integration test memory"
            assert memory.user_id == "integration_user"
            
            # Test cleanup
            await stm.cleanup()
            mock_graph_instance.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ltm_service_basic_integration(self, mock_config):
        """Test basic LTM service integration"""
        
        with patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Setup HTTP client mock
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.aclose = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Test service initialization
            ltm = LTMService()
            await ltm.initialize()
            
            assert ltm.is_initialized is True
            assert ltm.is_ready() is True
            
            # Test cleanup
            await ltm.cleanup()
            mock_client_instance.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_shuttle_basic_integration(self, mock_config):
        """Test basic Memory Shuttle integration"""
        
        # Create mock services
        mock_stm = Mock()
        mock_stm.get_upload_candidates = AsyncMock(return_value=[])
        mock_stm.user_memories = {"test_user": []}
        
        mock_ltm = Mock()
        mock_ltm.is_ready = Mock(return_value=True)
        
        # Test shuttle creation
        shuttle = MemoryShuttle(mock_stm, mock_ltm)
        
        assert shuttle.stm == mock_stm
        assert shuttle.ltm == mock_ltm
        assert shuttle.is_running is False
        
        # Test start/stop
        await shuttle.start()
        assert shuttle.is_running is True
        
        await shuttle.stop()
        assert shuttle.is_running is False
    
    @pytest.mark.asyncio
    async def test_stm_ltm_shuttle_workflow(self, mock_config):
        """Test basic workflow between STM, LTM, and Shuttle"""
        
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
             patch('services.stm_service.Memory') as mock_memory, \
             patch('httpx.AsyncClient') as mock_http:
            
            # Setup STM mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 1, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            mock_memory_instance = Mock()
            mock_memory_instance.add = Mock(return_value={"id": "workflow_mem"})
            mock_memory.return_value = mock_memory_instance
            
            # Setup LTM mocks
            mock_http_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_http_instance.get = AsyncMock(return_value=mock_response)
            mock_http_instance.aclose = AsyncMock()
            mock_http.return_value = mock_http_instance
            
            # Initialize services
            stm = STMService()
            await stm.initialize()
            
            ltm = LTMService()
            await ltm.initialize()
            
            shuttle = MemoryShuttle(stm, ltm)
            
            # Verify all services are ready
            assert stm.is_initialized is True
            assert ltm.is_ready() is True
            
            # Test workflow
            memory = await stm.add_memory(
                content="Workflow test memory",
                user_id="workflow_user",
                metadata={"workflow": "test"}
            )
            
            assert memory is not None
            
            # Test shuttle stats (should work even if shuttle not started)
            stats = await shuttle.get_shuttle_stats("workflow_user")
            assert "is_running" in stats
            assert stats["is_running"] is False
            
            # Cleanup
            await shuttle.stop()
            await stm.cleanup()
            await ltm.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])