"""
Jean Memory V3 Testing Configuration
Provides pytest fixtures and configuration for the testing suite.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.memory_service import JeanMemoryV3Service
from services.stm_service import STMService
from services.ltm_service import LTMService
from services.memory_shuttle import MemoryShuttle
from config import Config


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=Config)
    config.NEO4J_URI = "bolt://localhost:7687"
    config.NEO4J_USER = "neo4j"
    config.NEO4J_PASSWORD = "testpassword"
    config.OPENAI_API_KEY = "test-api-key"
    config.FAISS_INDEX_PATH = "/tmp/test_faiss"
    config.STM_CAPACITY = 100
    config.LTM_THRESHOLD = 0.8
    config.MEMORY_RETENTION_DAYS = 30
    config.LOG_LEVEL = "DEBUG"
    return config


@pytest.fixture
def mock_stm_service():
    """Create a mock STM service for testing."""
    service = Mock(spec=STMService)
    service.add_memory = AsyncMock(return_value={"id": "test-stm-id", "status": "added"})
    service.get_recent_memories = AsyncMock(return_value=[])
    service.search_memories = AsyncMock(return_value=[])
    service.get_capacity_info = AsyncMock(return_value={"current": 50, "max": 100})
    return service


@pytest.fixture
def mock_ltm_service():
    """Create a mock LTM service for testing."""
    service = Mock(spec=LTMService)
    service.store_memory = AsyncMock(return_value={"id": "test-ltm-id", "status": "stored"})
    service.search_memories = AsyncMock(return_value=[])
    service.get_memory_by_id = AsyncMock(return_value=None)
    service.update_memory = AsyncMock(return_value={"id": "test-ltm-id", "status": "updated"})
    service.delete_memory = AsyncMock(return_value={"status": "deleted"})
    return service


@pytest.fixture
def mock_memory_shuttle():
    """Create a mock memory shuttle for testing."""
    shuttle = Mock(spec=MemoryShuttle)
    shuttle.transfer_to_ltm = AsyncMock(return_value={"transferred": 5})
    shuttle.consolidate_memories = AsyncMock(return_value={"consolidated": 3})
    return shuttle


@pytest.fixture
def mock_jean_memory_service(mock_config, mock_stm_service, mock_ltm_service, mock_memory_shuttle):
    """Create a mock Jean Memory V3 service for testing."""
    service = Mock(spec=JeanMemoryV3Service)
    service.config = mock_config
    service.stm_service = mock_stm_service
    service.ltm_service = mock_ltm_service
    service.memory_shuttle = mock_memory_shuttle
    service.add_memory = AsyncMock(return_value={"id": "test-memory-id", "status": "added"})
    service.search_memories = AsyncMock(return_value=[])
    service.get_health = AsyncMock(return_value={"status": "healthy", "services": {"stm": True, "ltm": True}})
    return service


@pytest.fixture
def test_memory_data():
    """Provide test memory data."""
    return {
        "content": "This is a test memory for unit testing",
        "user_id": "test-user-123",
        "metadata": {
            "source": "test",
            "timestamp": "2024-01-01T12:00:00Z",
            "category": "testing"
        }
    }


@pytest.fixture
def test_search_query():
    """Provide test search query data."""
    return {
        "query": "test memory",
        "user_id": "test-user-123",
        "limit": 10,
        "filters": {"category": "testing"}
    }


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for API testing."""
    from api.routes import app
    return TestClient(app)


# Pytest configuration
pytest_plugins = ["pytest_asyncio"]

# Async test configuration
pytestmark = pytest.mark.asyncio

# Configure async mode
asyncio_mode = "auto"