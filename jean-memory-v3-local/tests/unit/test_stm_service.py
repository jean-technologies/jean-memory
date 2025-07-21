"""
Unit tests for STM (Short-Term Memory) Service
Tests all methods and behaviors of STMService and STMMemory classes.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.stm_service import STMService, STMMemory
from config import JeanMemoryV3Config


class TestSTMMemory:
    """Test STMMemory class functionality"""
    
    def test_stm_memory_initialization(self):
        """Test STMMemory object creation with default values"""
        memory = STMMemory(
            id="test_id",
            content="Test content",
            user_id="user123"
        )
        
        assert memory.id == "test_id"
        assert memory.content == "Test content"
        assert memory.user_id == "user123"
        assert memory.app_id == "jean_memory_v3_stm"
        assert memory.metadata == {}
        assert memory.state == "active"
        assert memory.source == "stm"
        assert memory.access_count == 0
        assert memory.salience_score == 0.0
        assert memory.upload_status == "pending"
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.last_accessed, datetime)
    
    def test_stm_memory_custom_initialization(self):
        """Test STMMemory with custom values"""
        metadata = {"category": "test", "tags": ["unit", "test"]}
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        
        memory = STMMemory(
            id="custom_id",
            content="Custom content",
            user_id="user456",
            app_id="custom_app",
            metadata=metadata,
            created_at=created_at,
            state="inactive"
        )
        
        assert memory.app_id == "custom_app"
        assert memory.metadata == metadata
        assert memory.created_at == created_at
        assert memory.state == "inactive"
    
    def test_to_v2_format(self):
        """Test conversion to V2 API format"""
        metadata = {"category": "test"}
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        
        memory = STMMemory(
            id="test_id",
            content="Test content",
            user_id="user123",
            metadata=metadata,
            created_at=created_at
        )
        
        v2_format = memory.to_v2_format()
        
        assert v2_format["id"] == "test_id"
        assert v2_format["content"] == "Test content"
        assert v2_format["created_at"] == int(created_at.timestamp())
        assert v2_format["state"] == "active"
        assert v2_format["app_id"] == "jean_memory_v3_stm"
        assert v2_format["app_name"] == "Jean Memory V3 STM"
        assert v2_format["categories"] == []
        assert v2_format["metadata_"]["source"] == "stm"
        assert v2_format["metadata_"]["category"] == "test"
        assert "last_accessed" in v2_format["metadata_"]
        assert "access_count" in v2_format["metadata_"]
        assert "salience_score" in v2_format["metadata_"]
        assert "upload_status" in v2_format["metadata_"]
    
    def test_update_access(self):
        """Test access tracking updates"""
        memory = STMMemory("test_id", "Test content", "user123")
        
        original_last_accessed = memory.last_accessed
        original_access_count = memory.access_count
        
        # Wait a tiny bit to ensure time difference
        import time
        time.sleep(0.001)
        
        memory.update_access()
        
        assert memory.last_accessed > original_last_accessed
        assert memory.access_count == original_access_count + 1
    
    def test_calculate_salience_recent_memory(self):
        """Test salience calculation for recent memory"""
        memory = STMMemory("test_id", "Test content", "user123")
        memory.access_count = 5
        
        salience = memory.calculate_salience()
        
        # Recent memory should have high recency score
        assert 0.0 <= salience <= 1.0
        assert salience > 0.5  # Should be high for recent memory
        assert memory.salience_score == salience
    
    def test_calculate_salience_old_memory(self):
        """Test salience calculation for old memory"""
        old_time = datetime.now() - timedelta(days=10)  # 10 days old
        memory = STMMemory(
            "test_id", 
            "Test content", 
            "user123",
            created_at=old_time
        )
        memory.access_count = 1
        
        salience = memory.calculate_salience()
        
        # Old memory should have lower salience
        assert 0.0 <= salience <= 1.0
        assert salience < 0.5  # Should be lower for old memory


class TestSTMService:
    """Test STMService class functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = Mock(spec=JeanMemoryV3Config)
        config.max_local_memories = 1000
        config.openai_api_key = "test-key"
        config.data_dir = Path("/tmp/test")
        return config
    
    @pytest.fixture
    def mock_graph_service(self):
        """Create mock graph service"""
        graph_service = Mock()
        graph_service.initialize = AsyncMock()
        graph_service.add_memory_to_graph = AsyncMock()
        graph_service.delete_memory_from_graph = AsyncMock()
        graph_service.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
        graph_service.is_ready = Mock(return_value=True)
        graph_service.cleanup = AsyncMock()
        return graph_service
    
    @pytest.fixture
    def mock_memory_client(self):
        """Create mock mem0 Memory client"""
        client = Mock()
        client.add = Mock(return_value={"id": "mem0_id", "status": "success"})
        client.search = Mock(return_value=[
            {"memory": "Test content", "score": 0.8},
            {"memory": "Another memory", "score": 0.6}
        ])
        client.delete = Mock(return_value=True)
        return client
    
    @pytest_asyncio.fixture
    async def stm_service(self, mock_config, mock_graph_service):
        """Create STMService instance with mocked dependencies"""
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": Path("/tmp/test/faiss"),
                 "neo4j": Path("/tmp/test/neo4j"),
                 "models": Path("/tmp/test/models"),
                 "logs": Path("/tmp/test/logs"),
                 "temp": Path("/tmp/test/temp")
             }), \
             patch('services.stm_service.GraphService', return_value=mock_graph_service):
            
            service = STMService()
            service.graph_service = mock_graph_service
            return service
    
    @pytest.mark.asyncio
    async def test_stm_service_initialization(self, stm_service, mock_graph_service):
        """Test STM service initialization"""
        # Mock the memory client initialization
        mock_memory_client = Mock()
        
        with patch.object(stm_service, '_initialize_stm_memory_client') as mock_init_mem, \
             patch.object(stm_service, '_setup_resource_governor') as mock_setup_gov:
            
            mock_init_mem.return_value = None
            mock_setup_gov.return_value = None
            
            await stm_service.initialize()
            
            assert stm_service.is_initialized is True
            mock_graph_service.initialize.assert_called_once()
            mock_init_mem.assert_called_once()
            mock_setup_gov.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_memory_string_content(self, stm_service, mock_memory_client, mock_graph_service):
        """Test adding memory with string content"""
        stm_service.memory_client = mock_memory_client
        stm_service.is_initialized = True
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = Mock()
            mock_loop.return_value.run_in_executor = mock_executor
            mock_executor.return_value = {"id": "mem0_id"}
            
            memory = await stm_service.add_memory(
                content="Test memory content",
                user_id="user123",
                metadata={"category": "test"}
            )
            
            assert isinstance(memory, STMMemory)
            assert memory.content == "Test memory content"
            assert memory.user_id == "user123"
            assert memory.metadata["category"] == "test"
            assert memory.id.startswith("stm_user123_")
            
            # Check storage
            assert memory.id in stm_service.memories
            assert "user123" in stm_service.user_memories
            assert memory.id in stm_service.user_memories["user123"]
            
            # Check graph service call
            mock_graph_service.add_memory_to_graph.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_memory_list_content(self, stm_service, mock_memory_client, mock_graph_service):
        """Test adding memory with list content"""
        stm_service.memory_client = mock_memory_client
        stm_service.is_initialized = True
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = Mock()
            mock_loop.return_value.run_in_executor = mock_executor
            mock_executor.return_value = {"id": "mem0_id"}
            
            # Test with list of strings
            memory = await stm_service.add_memory(
                content=["First part", "Second part"],
                user_id="user123"
            )
            
            assert memory.content == "First part Second part"
    
    @pytest.mark.asyncio
    async def test_add_memory_dict_content(self, stm_service, mock_memory_client, mock_graph_service):
        """Test adding memory with dictionary content"""
        stm_service.memory_client = mock_memory_client
        stm_service.is_initialized = True
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = Mock()
            mock_loop.return_value.run_in_executor = mock_executor
            mock_executor.return_value = {"id": "mem0_id"}
            
            # Test with list of dicts
            memory = await stm_service.add_memory(
                content=[
                    {"content": "First message"},
                    {"content": "Second message"}
                ],
                user_id="user123"
            )
            
            assert memory.content == "First message Second message"
    
    @pytest.mark.asyncio
    async def test_search_memories(self, stm_service, mock_memory_client):
        """Test memory search functionality"""
        stm_service.memory_client = mock_memory_client
        stm_service.is_initialized = True
        
        # Add some memories to search through
        memory1 = STMMemory("mem1", "Test content", "user123")
        memory2 = STMMemory("mem2", "Another memory", "user123")
        stm_service.memories["mem1"] = memory1
        stm_service.memories["mem2"] = memory2
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = Mock()
            mock_loop.return_value.run_in_executor = mock_executor
            mock_executor.return_value = [
                {"memory": "Test content", "score": 0.8},
                {"memory": "Another memory", "score": 0.6}
            ]
            
            results = await stm_service.search_memories(
                query="test query",
                user_id="user123",
                limit=10,
                threshold=0.5
            )
            
            assert len(results) == 2
            assert results[0]["content"] == "Test content"
            assert results[0]["score"] == 0.8
            assert results[1]["content"] == "Another memory"
            assert results[1]["score"] == 0.6
            
            # Check that access was updated
            assert memory1.access_count == 1
            assert memory2.access_count == 1
    
    @pytest.mark.asyncio
    async def test_search_memories_with_threshold(self, stm_service, mock_memory_client):
        """Test memory search with score threshold"""
        stm_service.memory_client = mock_memory_client
        stm_service.is_initialized = True
        
        memory1 = STMMemory("mem1", "Test content", "user123")
        stm_service.memories["mem1"] = memory1
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = Mock()
            mock_loop.return_value.run_in_executor = mock_executor
            mock_executor.return_value = [
                {"memory": "Test content", "score": 0.3}  # Below threshold
            ]
            
            results = await stm_service.search_memories(
                query="test query",
                user_id="user123",
                threshold=0.5
            )
            
            assert len(results) == 0  # Filtered out by threshold
    
    @pytest.mark.asyncio
    async def test_get_memory(self, stm_service):
        """Test getting specific memory"""
        memory = STMMemory("test_id", "Test content", "user123")
        stm_service.memories["test_id"] = memory
        
        retrieved = await stm_service.get_memory("test_id")
        
        assert retrieved == memory
        assert memory.access_count == 1  # Access should be tracked
        
        # Test non-existent memory
        none_result = await stm_service.get_memory("nonexistent")
        assert none_result is None
    
    @pytest.mark.asyncio
    async def test_get_user_memories(self, stm_service):
        """Test getting all memories for a user"""
        # Create test memories
        memory1 = STMMemory("mem1", "Content 1", "user123")
        memory2 = STMMemory("mem2", "Content 2", "user123")
        memory3 = STMMemory("mem3", "Content 3", "user456")  # Different user
        
        stm_service.memories.update({
            "mem1": memory1,
            "mem2": memory2,
            "mem3": memory3
        })
        
        stm_service.user_memories = {
            "user123": ["mem1", "mem2"],
            "user456": ["mem3"]
        }
        
        results = await stm_service.get_user_memories("user123")
        
        assert len(results) == 2
        assert any(r["id"] == "mem1" for r in results)
        assert any(r["id"] == "mem2" for r in results)
        assert not any(r["id"] == "mem3" for r in results)
        
        # Check access tracking
        assert memory1.access_count == 1
        assert memory2.access_count == 1
        assert memory3.access_count == 0  # Not accessed
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, stm_service, mock_memory_client, mock_graph_service):
        """Test memory deletion"""
        stm_service.memory_client = mock_memory_client
        memory = STMMemory("test_id", "Test content", "user123")
        
        stm_service.memories["test_id"] = memory
        stm_service.user_memories["user123"] = ["test_id"]
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = Mock()
            mock_loop.return_value.run_in_executor = mock_executor
            mock_executor.return_value = True
            
            result = await stm_service.delete_memory("test_id")
            
            assert result is True
            assert "test_id" not in stm_service.memories
            assert "test_id" not in stm_service.user_memories["user123"]
            
            mock_graph_service.delete_memory_from_graph.assert_called_once_with("test_id")
    
    @pytest.mark.asyncio
    async def test_get_upload_candidates(self, stm_service):
        """Test getting memories ready for upload to LTM"""
        # Create memories with different salience scores
        old_memory = STMMemory("old", "Old content", "user123", 
                              created_at=datetime.now() - timedelta(days=5))
        recent_memory = STMMemory("recent", "Recent content", "user123")
        recent_memory.access_count = 10  # High usage
        
        stm_service.memories.update({
            "old": old_memory,
            "recent": recent_memory
        })
        stm_service.user_memories["user123"] = ["old", "recent"]
        
        candidates = await stm_service.get_upload_candidates("user123")
        
        assert len(candidates) == 2
        # Should be sorted by salience (recent with high usage first)
        assert candidates[0].id == "recent"
        assert candidates[1].id == "old"
    
    @pytest.mark.asyncio
    async def test_mark_uploaded(self, stm_service):
        """Test marking memory as uploaded"""
        memory = STMMemory("test_id", "Test content", "user123")
        stm_service.memories["test_id"] = memory
        
        await stm_service.mark_uploaded("test_id", "ltm_id_123")
        
        assert memory.upload_status == "uploaded"
        assert memory.metadata["ltm_id"] == "ltm_id_123"
    
    @pytest.mark.asyncio
    async def test_get_stats_user_specific(self, stm_service, mock_graph_service):
        """Test getting statistics for specific user"""
        memory1 = STMMemory("mem1", "Content 1", "user123")
        memory2 = STMMemory("mem2", "Content 2", "user123")
        memory3 = STMMemory("mem3", "Content 3", "user456")
        
        stm_service.memories.update({
            "mem1": memory1,
            "mem2": memory2,
            "mem3": memory3
        })
        
        stm_service.user_memories = {
            "user123": ["mem1", "mem2"],
            "user456": ["mem3"]
        }
        
        stats = await stm_service.get_stats("user123")
        
        assert stats["total_memories"] == 2
        assert stats["source"] == "stm"
        assert "average_salience" in stats
        assert "graph_stats" in stats
    
    @pytest.mark.asyncio
    async def test_get_stats_global(self, stm_service, mock_graph_service):
        """Test getting global statistics"""
        memory1 = STMMemory("mem1", "Content 1", "user123")
        memory2 = STMMemory("mem2", "Content 2", "user456")
        
        stm_service.memories.update({
            "mem1": memory1,
            "mem2": memory2
        })
        
        stats = await stm_service.get_stats()
        
        assert stats["total_memories"] == 2
        assert stats["max_memories"] == 1000  # From mock config
        assert stats["source"] == "stm"
    
    def test_is_ready(self, stm_service, mock_graph_service):
        """Test service readiness check"""
        # Not initialized
        assert stm_service.is_ready() is False
        
        # Initialized but no memory client
        stm_service.is_initialized = True
        stm_service.memory_client = None
        assert stm_service.is_ready() is False
        
        # Fully ready
        stm_service.memory_client = Mock()
        mock_graph_service.is_ready.return_value = True
        assert stm_service.is_ready() is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, stm_service, mock_graph_service):
        """Test service cleanup"""
        # Add some data
        memory = STMMemory("test_id", "Test content", "user123")
        stm_service.memories["test_id"] = memory
        stm_service.user_memories["user123"] = ["test_id"]
        stm_service.memory_client = Mock()
        
        await stm_service.cleanup()
        
        assert len(stm_service.memories) == 0
        assert len(stm_service.user_memories) == 0
        assert stm_service.memory_client is None
        mock_graph_service.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in various scenarios"""
    
    # Test memory client initialization failure
    with patch('services.stm_service.get_config') as mock_config, \
         patch('services.stm_service.get_data_paths') as mock_paths, \
         patch('services.stm_service.GraphService') as mock_graph:
        
        mock_config.return_value.max_local_memories = 1000
        mock_config.return_value.openai_api_key = "test-key"
        mock_paths.return_value = {"faiss": Path("/tmp/test/faiss")}
        
        graph_service = Mock()
        graph_service.initialize = AsyncMock()
        mock_graph.return_value = graph_service
        
        service = STMService()
        
        # Mock mem0 to raise exception
        with patch('services.stm_service.Memory', side_effect=Exception("mem0 failed")):
            # Should not raise exception, should handle gracefully
            await service._initialize_stm_memory_client()
            assert service.memory_client is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])