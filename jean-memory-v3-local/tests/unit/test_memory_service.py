"""
Unit tests for Main JeanMemoryV3Service
Tests all methods and behaviors of the main orchestrating service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.memory_service import JeanMemoryV3Service, MemoryService
from config import JeanMemoryV3Config


class TestJeanMemoryV3Service:
    """Test JeanMemoryV3Service class functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = Mock(spec=JeanMemoryV3Config)
        config.openai_api_key = "test-key"
        config.google_cloud_project = "test-project"
        return config
    
    @pytest.fixture
    def mock_stm_service(self):
        """Create mock STM service"""
        stm = Mock()
        stm.initialize = AsyncMock()
        stm.is_ready = Mock(return_value=True)
        stm.cleanup = AsyncMock()
        return stm
    
    @pytest.fixture
    def mock_ltm_service(self):
        """Create mock LTM service"""
        ltm = Mock()
        ltm.initialize = AsyncMock()
        ltm.is_ready = Mock(return_value=True)
        ltm.cleanup = AsyncMock()
        return ltm
    
    @pytest.fixture
    def mock_memory_shuttle(self):
        """Create mock memory shuttle"""
        shuttle = Mock()
        shuttle.start = AsyncMock()
        shuttle.stop = AsyncMock()
        shuttle.is_running = True
        shuttle.force_upload_user_memories = AsyncMock(return_value={"uploaded": 5})
        shuttle.preload_hot_memories = AsyncMock(return_value={"preloaded": 3})
        shuttle.get_shuttle_stats = AsyncMock(return_value={"is_running": True})
        return shuttle
    
    @pytest.fixture
    def mock_google_service(self):
        """Create mock Google ADK service"""
        google = Mock()
        google.initialize = AsyncMock()
        google.initialized = True
        return google
    
    @pytest.fixture
    def mock_hybrid_orchestrator(self):
        """Create mock hybrid orchestrator"""
        orchestrator = Mock()
        orchestrator.initialize = AsyncMock()
        orchestrator.initialized = True
        return orchestrator
    
    @pytest.fixture
    def mock_session_service(self):
        """Create mock session service"""
        session = Mock()
        session.create_session = AsyncMock(return_value="session123")
        session.get_session = AsyncMock()
        session.update_session_state = AsyncMock(return_value=True)
        return session
    
    @pytest.fixture
    def mock_adk_memory_service(self):
        """Create mock ADK memory service"""
        adk_memory = Mock()
        adk_memory.add_memory = AsyncMock(return_value={"id": "mem123", "status": "added"})
        adk_memory.search_memories = AsyncMock()
        adk_memory.get_memory = AsyncMock(return_value={"id": "mem123", "content": "test"})
        adk_memory.delete_memory = AsyncMock(return_value=True)
        adk_memory.get_stats = AsyncMock(return_value={"service_type": "hybrid", "total_memories": 100})
        return adk_memory
    
    @pytest.fixture
    async def memory_service(self, mock_config):
        """Create JeanMemoryV3Service instance with mocked dependencies"""
        with patch('services.memory_service.get_config', return_value=mock_config):
            service = JeanMemoryV3Service()
            return service
    
    def test_memory_service_initialization(self, memory_service, mock_config):
        """Test memory service initialization"""
        assert memory_service.config == mock_config
        assert memory_service.stm_service is None
        assert memory_service.ltm_service is None
        assert memory_service.memory_shuttle is None
        assert memory_service.google_service is None
        assert memory_service.hybrid_orchestrator is None
        assert memory_service.session_service is None
        assert memory_service.cloud_session_service is None
        assert memory_service.memory_service is None
        assert memory_service.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_full_initialization_success(self, memory_service, mock_stm_service, mock_ltm_service,
                                              mock_memory_shuttle, mock_google_service, 
                                              mock_hybrid_orchestrator, mock_session_service,
                                              mock_adk_memory_service):
        """Test successful full system initialization"""
        
        with patch('services.memory_service.STMService', return_value=mock_stm_service), \
             patch('services.memory_service.LTMService', return_value=mock_ltm_service), \
             patch('services.memory_service.MemoryShuttle', return_value=mock_memory_shuttle), \
             patch('services.memory_service.GoogleADKMemoryService', return_value=mock_google_service), \
             patch('services.memory_service.HybridMemoryOrchestrator', return_value=mock_hybrid_orchestrator), \
             patch('services.memory_service.InMemorySessionService', return_value=mock_session_service), \
             patch('services.memory_service.create_memory_service', return_value=mock_adk_memory_service), \
             patch.object(memory_service, '_log_system_status') as mock_log:
            
            await memory_service.initialize()
            
            # Verify all services were initialized
            assert memory_service.stm_service == mock_stm_service
            assert memory_service.ltm_service == mock_ltm_service
            assert memory_service.memory_shuttle == mock_memory_shuttle
            assert memory_service.google_service == mock_google_service
            assert memory_service.hybrid_orchestrator == mock_hybrid_orchestrator
            assert memory_service.session_service == mock_session_service
            assert memory_service.memory_service == mock_adk_memory_service
            assert memory_service.is_initialized is True
            
            # Verify initialization calls
            mock_stm_service.initialize.assert_called_once()
            mock_ltm_service.initialize.assert_called_once()
            mock_memory_shuttle.start.assert_called_once()
            mock_google_service.initialize.assert_called_once()
            mock_hybrid_orchestrator.initialize.assert_called_once()
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_with_ltm_ready(self, memory_service, mock_stm_service, 
                                                mock_ltm_service, mock_memory_shuttle,
                                                mock_google_service, mock_hybrid_orchestrator,
                                                mock_session_service, mock_adk_memory_service):
        """Test initialization when LTM is ready (creates cloud session service)"""
        
        mock_ltm_service.is_ready.return_value = True
        mock_cloud_session = Mock()
        
        with patch('services.memory_service.STMService', return_value=mock_stm_service), \
             patch('services.memory_service.LTMService', return_value=mock_ltm_service), \
             patch('services.memory_service.MemoryShuttle', return_value=mock_memory_shuttle), \
             patch('services.memory_service.GoogleADKMemoryService', return_value=mock_google_service), \
             patch('services.memory_service.HybridMemoryOrchestrator', return_value=mock_hybrid_orchestrator), \
             patch('services.memory_service.InMemorySessionService', return_value=mock_session_service), \
             patch('services.memory_service.CloudSessionService', return_value=mock_cloud_session), \
             patch('services.memory_service.create_memory_service', return_value=mock_adk_memory_service), \
             patch.object(memory_service, '_log_system_status'):
            
            await memory_service.initialize()
            
            assert memory_service.cloud_session_service == mock_cloud_session
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, memory_service, mock_stm_service):
        """Test initialization failure handling"""
        
        mock_stm_service.initialize.side_effect = Exception("STM initialization failed")
        
        with patch('services.memory_service.STMService', return_value=mock_stm_service):
            with pytest.raises(Exception, match="STM initialization failed"):
                await memory_service.initialize()
            
            assert memory_service.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_log_system_status(self, memory_service, mock_stm_service, mock_ltm_service,
                                    mock_memory_shuttle, mock_google_service, 
                                    mock_hybrid_orchestrator, mock_session_service,
                                    mock_adk_memory_service):
        """Test system status logging"""
        
        # Setup services
        memory_service.stm_service = mock_stm_service
        memory_service.ltm_service = mock_ltm_service
        memory_service.memory_shuttle = mock_memory_shuttle
        memory_service.google_service = mock_google_service
        memory_service.hybrid_orchestrator = mock_hybrid_orchestrator
        memory_service.session_service = mock_session_service
        memory_service.memory_service = mock_adk_memory_service
        
        # Should not raise exception
        await memory_service._log_system_status()
        
        # Verify stats were called
        mock_adk_memory_service.get_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_memory_success(self, memory_service, mock_adk_memory_service):
        """Test successful memory addition"""
        memory_service.memory_service = mock_adk_memory_service
        
        result = await memory_service.add_memory(
            content="Test memory",
            user_id="user123",
            metadata={"category": "test"}
        )
        
        assert result == {"id": "mem123", "status": "added"}
        mock_adk_memory_service.add_memory.assert_called_once_with(
            content="Test memory",
            user_id="user123",
            metadata={"category": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_add_memory_not_initialized(self, memory_service):
        """Test memory addition when service not initialized"""
        memory_service.memory_service = None
        
        with pytest.raises(Exception, match="Memory service not initialized"):
            await memory_service.add_memory("test", "user123")
    
    @pytest.mark.asyncio
    async def test_search_memories_success(self, memory_service, mock_adk_memory_service):
        """Test successful memory search"""
        memory_service.memory_service = mock_adk_memory_service
        
        # Mock search result
        search_result = Mock()
        search_result.memories = [
            {"id": "mem1", "content": "Memory 1", "score": 0.8},
            {"id": "mem2", "content": "Memory 2", "score": 0.2}  # Below threshold
        ]
        search_result.source = "hybrid"
        search_result.execution_time_ms = 150
        
        mock_adk_memory_service.search_memories.return_value = search_result
        
        result = await memory_service.search_memories(
            query="test query",
            user_id="user123",
            limit=10,
            threshold=0.5
        )
        
        assert len(result["memories"]) == 1  # Only one above threshold
        assert result["memories"][0]["id"] == "mem1"
        assert result["total"] == 1
        assert result["source"] == "hybrid"
        assert result["execution_time_ms"] == 150
        assert result["query"] == "test query"
    
    @pytest.mark.asyncio
    async def test_search_memories_not_initialized(self, memory_service):
        """Test memory search when service not initialized"""
        memory_service.memory_service = None
        
        with pytest.raises(Exception, match="Memory service not initialized"):
            await memory_service.search_memories("query", "user123")
    
    @pytest.mark.asyncio
    async def test_get_memory_success(self, memory_service, mock_adk_memory_service):
        """Test successful memory retrieval"""
        memory_service.memory_service = mock_adk_memory_service
        
        result = await memory_service.get_memory("mem123", "user123")
        
        assert result == {"id": "mem123", "content": "test"}
        mock_adk_memory_service.get_memory.assert_called_once_with("mem123", "user123")
    
    @pytest.mark.asyncio
    async def test_get_memory_not_initialized(self, memory_service):
        """Test memory retrieval when service not initialized"""
        memory_service.memory_service = None
        
        result = await memory_service.get_memory("mem123", "user123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_memory_success(self, memory_service, mock_adk_memory_service):
        """Test successful memory deletion"""
        memory_service.memory_service = mock_adk_memory_service
        
        result = await memory_service.delete_memory("mem123", "user123")
        
        assert result is True
        mock_adk_memory_service.delete_memory.assert_called_once_with("mem123", "user123")
    
    @pytest.mark.asyncio
    async def test_delete_memory_not_initialized(self, memory_service):
        """Test memory deletion when service not initialized"""
        memory_service.memory_service = None
        
        result = await memory_service.delete_memory("mem123", "user123")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_stats_success(self, memory_service, mock_adk_memory_service):
        """Test successful stats retrieval"""
        memory_service.memory_service = mock_adk_memory_service
        
        result = await memory_service.get_stats("user123")
        
        assert result == {"service_type": "hybrid", "total_memories": 100}
        mock_adk_memory_service.get_stats.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_get_stats_not_initialized(self, memory_service):
        """Test stats retrieval when service not initialized"""
        memory_service.memory_service = None
        
        result = await memory_service.get_stats()
        
        assert result == {"error": "Memory service not initialized"}
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, memory_service, mock_session_service):
        """Test successful session creation"""
        memory_service.session_service = mock_session_service
        
        result = await memory_service.create_session("user123", {"type": "chat"})
        
        assert result == "session123"
        mock_session_service.create_session.assert_called_once_with("user123", {"type": "chat"})
    
    @pytest.mark.asyncio
    async def test_create_session_not_initialized(self, memory_service):
        """Test session creation when service not initialized"""
        memory_service.session_service = None
        
        with pytest.raises(Exception, match="Session service not initialized"):
            await memory_service.create_session("user123")
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, memory_service, mock_session_service):
        """Test successful session retrieval"""
        memory_service.session_service = mock_session_service
        
        mock_session = Mock()
        mock_session.to_dict.return_value = {"id": "session123", "user_id": "user123"}
        mock_session_service.get_session.return_value = mock_session
        
        result = await memory_service.get_session("session123")
        
        assert result == {"id": "session123", "user_id": "user123"}
        mock_session_service.get_session.assert_called_once_with("session123")
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, memory_service, mock_session_service):
        """Test session retrieval when session not found"""
        memory_service.session_service = mock_session_service
        mock_session_service.get_session.return_value = None
        
        result = await memory_service.get_session("session123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_session_not_initialized(self, memory_service):
        """Test session retrieval when service not initialized"""
        memory_service.session_service = None
        
        result = await memory_service.get_session("session123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_session_state_success(self, memory_service, mock_session_service):
        """Test successful session state update"""
        memory_service.session_service = mock_session_service
        
        result = await memory_service.update_session_state("session123", "key", "value")
        
        assert result is True
        mock_session_service.update_session_state.assert_called_once_with("session123", "key", "value")
    
    @pytest.mark.asyncio
    async def test_update_session_state_not_initialized(self, memory_service):
        """Test session state update when service not initialized"""
        memory_service.session_service = None
        
        result = await memory_service.update_session_state("session123", "key", "value")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_force_sync_to_ltm_success(self, memory_service, mock_memory_shuttle):
        """Test successful force sync to LTM"""
        memory_service.memory_shuttle = mock_memory_shuttle
        
        result = await memory_service.force_sync_to_ltm("user123")
        
        assert result == {"uploaded": 5}
        mock_memory_shuttle.force_upload_user_memories.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_force_sync_to_ltm_not_initialized(self, memory_service):
        """Test force sync when shuttle not initialized"""
        memory_service.memory_shuttle = None
        
        result = await memory_service.force_sync_to_ltm("user123")
        
        assert result == {"error": "Memory shuttle not initialized"}
    
    @pytest.mark.asyncio
    async def test_preload_hot_memories_success(self, memory_service, mock_memory_shuttle):
        """Test successful hot memory preloading"""
        memory_service.memory_shuttle = mock_memory_shuttle
        
        result = await memory_service.preload_hot_memories("user123")
        
        assert result == {"preloaded": 3}
        mock_memory_shuttle.preload_hot_memories.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_preload_hot_memories_not_initialized(self, memory_service):
        """Test hot memory preloading when shuttle not initialized"""
        memory_service.memory_shuttle = None
        
        result = await memory_service.preload_hot_memories("user123")
        
        assert result == {"error": "Memory shuttle not initialized"}
    
    @pytest.mark.asyncio
    async def test_get_shuttle_stats_success(self, memory_service, mock_memory_shuttle):
        """Test successful shuttle stats retrieval"""
        memory_service.memory_shuttle = mock_memory_shuttle
        
        result = await memory_service.get_shuttle_stats("user123")
        
        assert result == {"is_running": True}
        mock_memory_shuttle.get_shuttle_stats.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_get_shuttle_stats_not_initialized(self, memory_service):
        """Test shuttle stats when shuttle not initialized"""
        memory_service.memory_shuttle = None
        
        result = await memory_service.get_shuttle_stats()
        
        assert result == {"error": "Memory shuttle not initialized"}
    
    def test_is_ready_true(self, memory_service, mock_adk_memory_service, mock_stm_service):
        """Test is_ready when service is ready"""
        memory_service.is_initialized = True
        memory_service.memory_service = mock_adk_memory_service
        memory_service.stm_service = mock_stm_service
        
        assert memory_service.is_ready() is True
    
    def test_is_ready_false_not_initialized(self, memory_service):
        """Test is_ready when not initialized"""
        memory_service.is_initialized = False
        
        assert memory_service.is_ready() is False
    
    def test_is_ready_false_no_memory_service(self, memory_service):
        """Test is_ready when memory service missing"""
        memory_service.is_initialized = True
        memory_service.memory_service = None
        
        assert memory_service.is_ready() is False
    
    def test_is_ready_false_no_stm_service(self, memory_service, mock_adk_memory_service):
        """Test is_ready when STM service missing"""
        memory_service.is_initialized = True
        memory_service.memory_service = mock_adk_memory_service
        memory_service.stm_service = None
        
        assert memory_service.is_ready() is False
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, memory_service, mock_memory_shuttle, 
                                  mock_stm_service, mock_ltm_service):
        """Test successful cleanup"""
        memory_service.memory_shuttle = mock_memory_shuttle
        memory_service.stm_service = mock_stm_service
        memory_service.ltm_service = mock_ltm_service
        
        await memory_service.cleanup()
        
        mock_memory_shuttle.stop.assert_called_once()
        mock_stm_service.cleanup.assert_called_once()
        mock_ltm_service.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_partial_services(self, memory_service, mock_stm_service):
        """Test cleanup with only some services initialized"""
        memory_service.memory_shuttle = None
        memory_service.stm_service = mock_stm_service
        memory_service.ltm_service = None
        
        # Should not raise exception
        await memory_service.cleanup()
        
        mock_stm_service.cleanup.assert_called_once()
    
    def test_legacy_alias(self):
        """Test that MemoryService is an alias for JeanMemoryV3Service"""
        assert MemoryService == JeanMemoryV3Service


@pytest.mark.asyncio
async def test_integration_scenarios():
    """Test integration scenarios with realistic service interactions"""
    
    # Test initialization order matters
    with patch('services.memory_service.get_config') as mock_config:
        mock_config.return_value.openai_api_key = "test-key"
        
        service = JeanMemoryV3Service()
        
        # Mock all the service classes to track initialization order
        init_order = []
        
        def track_init(name):
            def wrapper(*args, **kwargs):
                init_order.append(name)
                mock = Mock()
                mock.initialize = AsyncMock()
                mock.start = AsyncMock()
                mock.is_ready = Mock(return_value=True)
                mock.initialized = True
                mock.is_running = True
                return mock
            return wrapper
        
        with patch('services.memory_service.STMService', side_effect=track_init('STM')), \
             patch('services.memory_service.LTMService', side_effect=track_init('LTM')), \
             patch('services.memory_service.MemoryShuttle', side_effect=track_init('Shuttle')), \
             patch('services.memory_service.GoogleADKMemoryService', side_effect=track_init('Google')), \
             patch('services.memory_service.HybridMemoryOrchestrator', side_effect=track_init('Hybrid')), \
             patch('services.memory_service.InMemorySessionService', side_effect=track_init('Session')), \
             patch('services.memory_service.create_memory_service', return_value=Mock()), \
             patch.object(service, '_log_system_status'):
            
            await service.initialize()
            
            # Verify initialization order
            expected_order = ['STM', 'LTM', 'Shuttle', 'Google', 'Hybrid', 'Session']
            assert init_order == expected_order


if __name__ == "__main__":
    pytest.main([__file__, "-v"])