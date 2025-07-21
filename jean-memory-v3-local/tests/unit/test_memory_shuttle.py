"""
Unit tests for Memory Shuttle Service
Tests all methods and behaviors of MemoryShuttle and ShuttleConfig classes.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.memory_shuttle import MemoryShuttle, ShuttleConfig
from services.stm_service import STMMemory


class TestShuttleConfig:
    """Test ShuttleConfig dataclass"""
    
    def test_shuttle_config_defaults(self):
        """Test default configuration values"""
        config = ShuttleConfig()
        
        assert config.batch_size == 10
        assert config.batch_timeout_seconds == 30
        assert config.max_batch_size_mb == 5.0
        assert config.min_salience_score == 0.3
        assert config.max_pending_uploads == 100
        assert config.preload_hot_memories == 20
        assert config.preload_interval_minutes == 60
        assert config.upload_interval_seconds == 60
        assert config.download_interval_seconds == 300
        assert config.enable_dedup is True
        assert config.dedup_similarity_threshold == 0.95
    
    def test_shuttle_config_custom_values(self):
        """Test custom configuration values"""
        config = ShuttleConfig(
            batch_size=20,
            min_salience_score=0.5,
            enable_dedup=False
        )
        
        assert config.batch_size == 20
        assert config.min_salience_score == 0.5
        assert config.enable_dedup is False
        # Other values should remain defaults
        assert config.preload_hot_memories == 20


class TestMemoryShuttle:
    """Test MemoryShuttle class functionality"""
    
    @pytest.fixture
    def mock_stm_service(self):
        """Create mock STM service"""
        stm = Mock()
        stm.get_upload_candidates = AsyncMock(return_value=[])
        stm.add_memory = AsyncMock()
        stm.mark_uploaded = AsyncMock()
        stm.user_memories = {"user123": ["mem1", "mem2"]}
        stm.memories = {}
        return stm
    
    @pytest.fixture
    def mock_ltm_service(self):
        """Create mock LTM service"""
        ltm = Mock()
        ltm.is_ready = Mock(return_value=True)
        ltm.upload_memory = AsyncMock(return_value={"id": "ltm123", "status": "created"})
        ltm.get_hot_memories = AsyncMock(return_value=[])
        ltm.get_user_memories = AsyncMock(return_value=[])
        return ltm
    
    @pytest.fixture
    def memory_shuttle(self, mock_stm_service, mock_ltm_service):
        """Create MemoryShuttle instance with mocked services"""
        return MemoryShuttle(mock_stm_service, mock_ltm_service)
    
    @pytest.fixture
    def sample_stm_memory(self):
        """Create sample STM memory for testing"""
        return STMMemory(
            id="stm123",
            content="Test memory content",
            user_id="user123",
            metadata={"category": "test"}
        )
    
    def test_memory_shuttle_initialization(self, memory_shuttle, mock_stm_service, mock_ltm_service):
        """Test Memory Shuttle initialization"""
        assert memory_shuttle.stm == mock_stm_service
        assert memory_shuttle.ltm == mock_ltm_service
        assert isinstance(memory_shuttle.config, ShuttleConfig)
        assert memory_shuttle.is_running is False
        assert memory_shuttle.upload_queue == {}
        assert memory_shuttle.last_upload == {}
        assert memory_shuttle.last_preload == {}
        assert memory_shuttle.upload_task is None
        assert memory_shuttle.preload_task is None
        assert "uploads_completed" in memory_shuttle.stats
        assert "uploads_failed" in memory_shuttle.stats
    
    @pytest.mark.asyncio
    async def test_start_shuttle(self, memory_shuttle):
        """Test starting the Memory Shuttle"""
        # Mock the worker methods to avoid running background tasks
        with patch.object(memory_shuttle, '_upload_worker') as mock_upload, \
             patch.object(memory_shuttle, '_preload_worker') as mock_preload:
            
            mock_upload.return_value = asyncio.Future()
            mock_upload.return_value.set_result(None)
            mock_preload.return_value = asyncio.Future() 
            mock_preload.return_value.set_result(None)
            
            await memory_shuttle.start()
            
            assert memory_shuttle.is_running is True
            assert memory_shuttle.upload_task is not None
            assert memory_shuttle.preload_task is not None
    
    @pytest.mark.asyncio
    async def test_start_shuttle_already_running(self, memory_shuttle):
        """Test starting shuttle when already running"""
        memory_shuttle.is_running = True
        
        # Should return early without creating tasks
        await memory_shuttle.start()
        
        assert memory_shuttle.upload_task is None
        assert memory_shuttle.preload_task is None
    
    @pytest.mark.asyncio
    async def test_stop_shuttle(self, memory_shuttle):
        """Test stopping the Memory Shuttle"""
        # Start first to create tasks
        with patch.object(memory_shuttle, '_upload_worker') as mock_upload, \
             patch.object(memory_shuttle, '_preload_worker') as mock_preload:
            
            mock_upload.return_value = asyncio.Future()
            mock_upload.return_value.set_result(None)
            mock_preload.return_value = asyncio.Future()
            mock_preload.return_value.set_result(None)
            
            await memory_shuttle.start()
            
            # Now stop
            await memory_shuttle.stop()
            
            assert memory_shuttle.is_running is False
    
    @pytest.mark.asyncio
    async def test_stop_shuttle_not_running(self, memory_shuttle):
        """Test stopping shuttle when not running"""
        # Should return early
        await memory_shuttle.stop()
        
        assert memory_shuttle.is_running is False
    
    @pytest.mark.asyncio
    async def test_queue_for_upload(self, memory_shuttle):
        """Test queuing memory for upload"""
        await memory_shuttle.queue_for_upload("user123", "mem123")
        
        assert "user123" in memory_shuttle.upload_queue
        assert "mem123" in memory_shuttle.upload_queue["user123"]
        
        # Test duplicate prevention
        await memory_shuttle.queue_for_upload("user123", "mem123")
        assert memory_shuttle.upload_queue["user123"].count("mem123") == 1
        
        # Test multiple memories for same user
        await memory_shuttle.queue_for_upload("user123", "mem456")
        assert len(memory_shuttle.upload_queue["user123"]) == 2
    
    @pytest.mark.asyncio
    async def test_force_upload_user_memories_success(self, memory_shuttle, mock_stm_service, sample_stm_memory):
        """Test forced upload of user memories"""
        # Setup mock to return upload candidates
        mock_stm_service.get_upload_candidates.return_value = [sample_stm_memory]
        
        with patch.object(memory_shuttle, '_upload_memory', return_value=True) as mock_upload:
            result = await memory_shuttle.force_upload_user_memories("user123")
            
            assert result["uploaded"] == 1
            assert result["failed"] == 0
            assert result["total_candidates"] == 1
            mock_upload.assert_called_once_with(sample_stm_memory)
    
    @pytest.mark.asyncio
    async def test_force_upload_user_memories_ltm_not_ready(self, memory_shuttle, mock_ltm_service):
        """Test forced upload when LTM is not ready"""
        mock_ltm_service.is_ready.return_value = False
        
        result = await memory_shuttle.force_upload_user_memories("user123")
        
        assert "error" in result
        assert result["uploaded"] == 0
    
    @pytest.mark.asyncio
    async def test_force_upload_user_memories_mixed_results(self, memory_shuttle, mock_stm_service):
        """Test forced upload with mixed success/failure"""
        # Create multiple memories
        memory1 = STMMemory("mem1", "Content 1", "user123")
        memory2 = STMMemory("mem2", "Content 2", "user123")
        mock_stm_service.get_upload_candidates.return_value = [memory1, memory2]
        
        # Mock alternating success/failure
        with patch.object(memory_shuttle, '_upload_memory', side_effect=[True, False]):
            result = await memory_shuttle.force_upload_user_memories("user123")
            
            assert result["uploaded"] == 1
            assert result["failed"] == 1
            assert result["total_candidates"] == 2
    
    @pytest.mark.asyncio
    async def test_preload_hot_memories_success(self, memory_shuttle, mock_ltm_service, mock_stm_service):
        """Test preloading hot memories from LTM"""
        # Mock hot memories from LTM
        hot_memories = [
            {
                "id": "ltm1",
                "content": "Hot memory 1",
                "app_id": "test_app",
                "metadata_": {"category": "important"}
            },
            {
                "id": "ltm2", 
                "content": "Hot memory 2",
                "app_id": "test_app",
                "metadata_": {"category": "work"}
            }
        ]
        mock_ltm_service.get_hot_memories.return_value = hot_memories
        
        # Mock STM to not find existing memories
        with patch.object(memory_shuttle, '_find_stm_memory_by_content', return_value=None):
            # Mock STM add_memory to return STMMemory objects
            stm_memory1 = STMMemory("stm1", "Hot memory 1", "user123")
            stm_memory2 = STMMemory("stm2", "Hot memory 2", "user123")
            mock_stm_service.add_memory.side_effect = [stm_memory1, stm_memory2]
            
            result = await memory_shuttle.preload_hot_memories("user123")
            
            assert result["preloaded"] == 2
            assert result["total_hot"] == 2
            assert mock_stm_service.add_memory.call_count == 2
            assert mock_stm_service.mark_uploaded.call_count == 2
            assert "user123" in memory_shuttle.last_preload
    
    @pytest.mark.asyncio
    async def test_preload_hot_memories_skip_existing(self, memory_shuttle, mock_ltm_service, mock_stm_service):
        """Test preloading skips memories already in STM"""
        hot_memories = [{"id": "ltm1", "content": "Existing memory"}]
        mock_ltm_service.get_hot_memories.return_value = hot_memories
        
        # Mock finding existing memory in STM
        existing_memory = STMMemory("stm1", "Existing memory", "user123")
        with patch.object(memory_shuttle, '_find_stm_memory_by_content', return_value=existing_memory):
            result = await memory_shuttle.preload_hot_memories("user123")
            
            assert result["preloaded"] == 0
            assert result["total_hot"] == 1
            mock_stm_service.add_memory.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_preload_hot_memories_ltm_not_ready(self, memory_shuttle, mock_ltm_service):
        """Test preloading when LTM is not ready"""
        mock_ltm_service.is_ready.return_value = False
        
        result = await memory_shuttle.preload_hot_memories("user123")
        
        assert "error" in result
        assert result["preloaded"] == 0
    
    @pytest.mark.asyncio
    async def test_upload_memory_success(self, memory_shuttle, mock_ltm_service, mock_stm_service, sample_stm_memory):
        """Test successful single memory upload"""
        ltm_result = {"id": "ltm123", "status": "created"}
        mock_ltm_service.upload_memory.return_value = ltm_result
        
        success = await memory_shuttle._upload_memory(sample_stm_memory)
        
        assert success is True
        mock_ltm_service.upload_memory.assert_called_once_with(
            content=sample_stm_memory.content,
            user_id=sample_stm_memory.user_id,
            app_id=sample_stm_memory.app_id,
            metadata=sample_stm_memory.metadata
        )
        mock_stm_service.mark_uploaded.assert_called_once_with(sample_stm_memory.id, "ltm123")
        assert memory_shuttle.stats["uploads_completed"] == 1
    
    @pytest.mark.asyncio
    async def test_upload_memory_failure(self, memory_shuttle, mock_ltm_service, sample_stm_memory):
        """Test failed memory upload"""
        mock_ltm_service.upload_memory.return_value = None
        
        success = await memory_shuttle._upload_memory(sample_stm_memory)
        
        assert success is False
        assert memory_shuttle.stats["uploads_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_upload_memory_exception(self, memory_shuttle, mock_ltm_service, sample_stm_memory):
        """Test memory upload with exception"""
        mock_ltm_service.upload_memory.side_effect = Exception("Upload failed")
        
        success = await memory_shuttle._upload_memory(sample_stm_memory)
        
        assert success is False
        assert memory_shuttle.stats["uploads_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_deduplicate_memories(self, memory_shuttle, mock_ltm_service):
        """Test memory deduplication"""
        # Setup recent LTM memories
        recent_ltm = [
            {"content": "Duplicate content"},
            {"content": "Another duplicate"}
        ]
        mock_ltm_service.get_user_memories.return_value = recent_ltm
        
        # Create STM memories with some duplicates
        memory1 = STMMemory("mem1", "Unique content", "user123")
        memory2 = STMMemory("mem2", "Duplicate content", "user123")  # Duplicate
        memory3 = STMMemory("mem3", "Another unique", "user123")
        
        memories = [memory1, memory2, memory3]
        
        unique_memories = await memory_shuttle._deduplicate_memories("user123", memories)
        
        assert len(unique_memories) == 2
        assert memory1 in unique_memories
        assert memory2 not in unique_memories  # Should be filtered out
        assert memory3 in unique_memories
        assert memory_shuttle.stats["dedup_saves"] == 1
    
    @pytest.mark.asyncio
    async def test_deduplicate_memories_exception(self, memory_shuttle, mock_ltm_service):
        """Test deduplication with exception returns original list"""
        mock_ltm_service.get_user_memories.side_effect = Exception("LTM error")
        
        memory1 = STMMemory("mem1", "Content", "user123")
        memories = [memory1]
        
        result = await memory_shuttle._deduplicate_memories("user123", memories)
        
        assert result == memories  # Should return original list
    
    @pytest.mark.asyncio
    async def test_find_stm_memory_by_content(self, memory_shuttle, mock_stm_service):
        """Test finding STM memory by content"""
        # Setup STM service with memories
        memory1 = STMMemory("mem1", "Content 1", "user123")
        memory2 = STMMemory("mem2", "Content 2", "user123")
        
        mock_stm_service.user_memories = {"user123": ["mem1", "mem2"]}
        mock_stm_service.memories = {"mem1": memory1, "mem2": memory2}
        
        # Test finding existing memory
        found = await memory_shuttle._find_stm_memory_by_content("user123", "Content 1")
        assert found == memory1
        
        # Test not finding memory
        not_found = await memory_shuttle._find_stm_memory_by_content("user123", "Non-existent")
        assert not_found is None
        
        # Test user with no memories
        empty = await memory_shuttle._find_stm_memory_by_content("user456", "Content 1")
        assert empty is None
    
    @pytest.mark.asyncio
    async def test_upload_batch(self, memory_shuttle, mock_ltm_service):
        """Test uploading a batch of memories"""
        memory1 = STMMemory("mem1", "Content 1", "user123")
        memory2 = STMMemory("mem2", "Content 2", "user123")
        memories = [memory1, memory2]
        
        # Mock deduplication to return all memories
        with patch.object(memory_shuttle, '_deduplicate_memories', return_value=memories), \
             patch.object(memory_shuttle, '_upload_memory', return_value=True):
            
            await memory_shuttle._upload_batch("user123", memories)
            
            assert "user123" in memory_shuttle.last_upload
            assert isinstance(memory_shuttle.last_upload["user123"], datetime)
    
    @pytest.mark.asyncio
    async def test_upload_batch_ltm_not_ready(self, memory_shuttle, mock_ltm_service):
        """Test batch upload when LTM is not ready"""
        mock_ltm_service.is_ready.return_value = False
        
        memory1 = STMMemory("mem1", "Content 1", "user123")
        memories = [memory1]
        
        # Should return early without processing
        await memory_shuttle._upload_batch("user123", memories)
        
        assert "user123" not in memory_shuttle.last_upload
    
    @pytest.mark.asyncio
    async def test_get_shuttle_stats_global(self, memory_shuttle, mock_ltm_service):
        """Test getting global shuttle statistics"""
        # Set some stats
        memory_shuttle.stats["uploads_completed"] = 10
        memory_shuttle.stats["uploads_failed"] = 2
        memory_shuttle.is_running = True
        
        stats = await memory_shuttle.get_shuttle_stats()
        
        assert stats["is_running"] is True
        assert stats["global_stats"]["uploads_completed"] == 10
        assert stats["global_stats"]["uploads_failed"] == 2
        assert "config" in stats
        assert stats["ltm_connected"] is True
        assert "user_stats" not in stats
    
    @pytest.mark.asyncio
    async def test_get_shuttle_stats_user_specific(self, memory_shuttle):
        """Test getting user-specific shuttle statistics"""
        # Setup user data
        memory_shuttle.upload_queue["user123"] = ["mem1", "mem2"]
        memory_shuttle.last_upload["user123"] = datetime(2024, 1, 1, 12, 0, 0)
        memory_shuttle.last_preload["user123"] = datetime(2024, 1, 1, 13, 0, 0)
        
        stats = await memory_shuttle.get_shuttle_stats("user123")
        
        assert "user_stats" in stats
        assert stats["user_stats"]["pending_uploads"] == 2
        assert stats["user_stats"]["last_upload"] == "2024-01-01T12:00:00"
        assert stats["user_stats"]["last_preload"] == "2024-01-01T13:00:00"
    
    @pytest.mark.asyncio
    async def test_get_shuttle_stats_user_no_data(self, memory_shuttle):
        """Test getting stats for user with no data"""
        stats = await memory_shuttle.get_shuttle_stats("user456")
        
        assert stats["user_stats"]["pending_uploads"] == 0
        assert stats["user_stats"]["last_upload"] is None
        assert stats["user_stats"]["last_preload"] is None


@pytest.mark.asyncio
async def test_shuttle_workers_integration():
    """Test integration of shuttle workers with realistic scenarios"""
    
    # Create mock services
    mock_stm = Mock()
    mock_ltm = Mock()
    
    mock_stm.user_memories = {"user123": ["mem1"]}
    mock_stm.get_upload_candidates = AsyncMock(return_value=[])
    mock_ltm.is_ready = Mock(return_value=True)
    
    shuttle = MemoryShuttle(mock_stm, mock_ltm)
    shuttle.config.upload_interval_seconds = 0.1  # Fast for testing
    shuttle.config.preload_interval_minutes = 0.001  # Very fast for testing
    
    # Test upload worker cycle
    with patch.object(shuttle, '_upload_batch') as mock_upload_batch:
        # Add some upload queue items
        shuttle.upload_queue["user123"] = ["mem1"]
        
        # Run one cycle of the upload worker
        upload_task = asyncio.create_task(shuttle._upload_worker())
        
        # Let it run briefly
        await asyncio.sleep(0.05)
        shuttle.is_running = False  # Stop the worker
        
        try:
            await upload_task
        except asyncio.CancelledError:
            pass
    
    # Test preload worker cycle  
    with patch.object(shuttle, 'preload_hot_memories') as mock_preload:
        mock_preload.return_value = {"preloaded": 0}
        
        # Run one cycle of the preload worker
        preload_task = asyncio.create_task(shuttle._preload_worker())
        
        # Let it run briefly
        await asyncio.sleep(0.05)
        shuttle.is_running = False  # Stop the worker
        
        try:
            await preload_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])