"""
Basic unit tests to verify testing infrastructure
"""

import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_basic_functionality():
    """Test basic functionality works"""
    assert 1 + 1 == 2

def test_imports_work():
    """Test that we can import our services"""
    try:
        from config import JeanMemoryV3Config
        assert JeanMemoryV3Config is not None
    except ImportError as e:
        pytest.fail(f"Failed to import config: {e}")

def test_stm_memory_class():
    """Test STMMemory class can be imported and instantiated"""
    try:
        from services.stm_service import STMMemory
        
        memory = STMMemory(
            id="test_id",
            content="Test content",
            user_id="user123"
        )
        
        assert memory.id == "test_id"
        assert memory.content == "Test content"
        assert memory.user_id == "user123"
        
    except ImportError as e:
        pytest.fail(f"Failed to import STMMemory: {e}")

@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality works"""
    async def simple_async():
        return "async works"
    
    result = await simple_async()
    assert result == "async works"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])