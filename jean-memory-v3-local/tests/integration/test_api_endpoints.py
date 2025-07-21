"""
Integration tests for API endpoints
Tests the FastAPI routes with real service interactions
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.routes import router
from fastapi import FastAPI
from fastapi.testclient import TestClient

def create_test_app():
    """Create a test FastAPI app with routes"""
    app = FastAPI()
    app.include_router(router)
    return app
from services.memory_service import JeanMemoryV3Service
from config import JeanMemoryV3Config


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app"""
        app = create_test_app()
        return TestClient(app)
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = Mock(spec=JeanMemoryV3Config)
        config.openai_api_key = "test-api-key"
        config.jean_memory_v2_api_url = "https://api.test.com"
        config.jean_memory_v2_api_key = "test-ltm-key"
        config.max_local_memories = 100
        return config
    
    @pytest.fixture
    def mock_v3_service(self):
        """Create mock V3 service"""
        service = Mock(spec=JeanMemoryV3Service)
        service.is_ready = Mock(return_value=True)
        service.add_memory = AsyncMock()
        service.search_memories = AsyncMock()
        service.get_memory = AsyncMock()
        service.delete_memory = AsyncMock()
        service.get_stats = AsyncMock()
        service.force_sync_to_ltm = AsyncMock()
        service.preload_hot_memories = AsyncMock()
        service.get_shuttle_stats = AsyncMock()
        service.create_session = AsyncMock()
        service.get_session = AsyncMock()
        service.update_session_state = AsyncMock()
        return service
    
    def test_health_endpoint_success(self, client, mock_v3_service):
        """Test health endpoint returns success when service is ready"""
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "Jean Memory V3"
            assert "timestamp" in data
            assert "uptime_seconds" in data
    
    def test_health_endpoint_service_not_ready(self, client, mock_v3_service):
        """Test health endpoint when service is not ready"""
        
        mock_v3_service.is_ready.return_value = False
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/health")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data
    
    def test_add_memory_success(self, client, mock_v3_service):
        """Test successful memory addition via API"""
        
        mock_v3_service.add_memory.return_value = {
            "id": "api_mem_123",
            "status": "added",
            "source": "stm"
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.post("/memories/", json={
                "content": "API test memory content",
                "user_id": "api_test_user",
                "metadata": {"test_type": "api_integration"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "api_mem_123"
            assert data["status"] == "added"
            
            # Verify service was called correctly
            mock_v3_service.add_memory.assert_called_once()
            call_args = mock_v3_service.add_memory.call_args
            assert call_args[1]["content"] == "API test memory content"
            assert call_args[1]["user_id"] == "api_test_user"
            assert call_args[1]["metadata"]["test_type"] == "api_integration"
    
    def test_add_memory_missing_fields(self, client, mock_v3_service):
        """Test memory addition with missing required fields"""
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.post("/memories/", json={
                "content": "Missing user_id"
                # user_id is missing
            })
            
            assert response.status_code == 422  # Validation error
    
    def test_add_memory_service_error(self, client, mock_v3_service):
        """Test memory addition when service raises error"""
        
        mock_v3_service.add_memory.side_effect = Exception("Service error")
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.post("/memories/", json={
                "content": "Test content",
                "user_id": "test_user"
            })
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
    
    def test_search_memories_success(self, client, mock_v3_service):
        """Test successful memory search via API"""
        
        mock_v3_service.search_memories.return_value = {
            "memories": [
                {
                    "id": "search_mem_1",
                    "content": "Searchable content 1",
                    "score": 0.9,
                    "metadata_": {"category": "test"}
                },
                {
                    "id": "search_mem_2", 
                    "content": "Searchable content 2",
                    "score": 0.7,
                    "metadata_": {"category": "demo"}
                }
            ],
            "total": 2,
            "source": "stm",
            "execution_time_ms": 150,
            "query": "searchable"
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/memories/search", params={
                "query": "searchable",
                "user_id": "search_user",
                "limit": 10,
                "threshold": 0.5
            })
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["memories"]) == 2
            assert data["total"] == 2
            assert data["source"] == "stm"
            assert data["query"] == "searchable"
            
            # Verify service was called correctly
            mock_v3_service.search_memories.assert_called_once()
            call_args = mock_v3_service.search_memories.call_args
            assert call_args[1]["query"] == "searchable"
            assert call_args[1]["user_id"] == "search_user"
            assert call_args[1]["limit"] == 10
            assert call_args[1]["threshold"] == 0.5
    
    def test_search_memories_missing_params(self, client, mock_v3_service):
        """Test memory search with missing required parameters"""
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/memories/search", params={
                "query": "test"
                # user_id is missing
            })
            
            assert response.status_code == 422  # Validation error
    
    def test_search_memories_with_defaults(self, client, mock_v3_service):
        """Test memory search uses default values for optional parameters"""
        
        mock_v3_service.search_memories.return_value = {
            "memories": [],
            "total": 0,
            "source": "stm",
            "execution_time_ms": 50,
            "query": "test"
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/memories/search", params={
                "query": "test",
                "user_id": "default_user"
            })
            
            assert response.status_code == 200
            
            # Verify default values were used
            call_args = mock_v3_service.search_memories.call_args
            assert call_args[1]["limit"] == 10  # Default limit
            assert call_args[1]["threshold"] == 0.3  # Default threshold
    
    def test_get_memory_success(self, client, mock_v3_service):
        """Test successful memory retrieval by ID"""
        
        mock_v3_service.get_memory.return_value = {
            "id": "get_mem_123",
            "content": "Retrieved memory content", 
            "user_id": "get_user",
            "metadata_": {"category": "retrieved"}
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/memories/get_mem_123", params={
                "user_id": "get_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "get_mem_123"
            assert data["content"] == "Retrieved memory content"
            
            mock_v3_service.get_memory.assert_called_once_with("get_mem_123", "get_user")
    
    def test_get_memory_not_found(self, client, mock_v3_service):
        """Test memory retrieval when memory not found"""
        
        mock_v3_service.get_memory.return_value = None
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/memories/nonexistent", params={
                "user_id": "test_user"
            })
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_delete_memory_success(self, client, mock_v3_service):
        """Test successful memory deletion"""
        
        mock_v3_service.delete_memory.return_value = True
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.delete("/memories/delete_mem_123", params={
                "user_id": "delete_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "deleted" in data["message"].lower()
            
            mock_v3_service.delete_memory.assert_called_once_with("delete_mem_123", "delete_user")
    
    def test_delete_memory_not_found(self, client, mock_v3_service):
        """Test memory deletion when memory not found"""
        
        mock_v3_service.delete_memory.return_value = False
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.delete("/memories/nonexistent", params={
                "user_id": "test_user"
            })
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_get_stats_success(self, client, mock_v3_service):
        """Test successful stats retrieval"""
        
        mock_v3_service.get_stats.return_value = {
            "service_type": "hybrid",
            "total_memories": 150,
            "stm_memories": 50,
            "ltm_memories": 100,
            "active_sessions": 5
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/stats", params={
                "user_id": "stats_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["service_type"] == "hybrid"
            assert data["total_memories"] == 150
            assert data["stm_memories"] == 50
            
            mock_v3_service.get_stats.assert_called_once_with("stats_user")
    
    def test_get_stats_global(self, client, mock_v3_service):
        """Test global stats retrieval without user_id"""
        
        mock_v3_service.get_stats.return_value = {
            "service_type": "hybrid",
            "total_memories": 500,
            "total_users": 25
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_memories"] == 500
            assert data["total_users"] == 25
            
            mock_v3_service.get_stats.assert_called_once_with(None)
    
    def test_force_sync_endpoint(self, client, mock_v3_service):
        """Test force sync to LTM endpoint"""
        
        mock_v3_service.force_sync_to_ltm.return_value = {
            "uploaded": 8,
            "failed": 1,
            "total_candidates": 9
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.post("/memories/sync", params={
                "user_id": "sync_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["uploaded"] == 8
            assert data["failed"] == 1
            assert data["total_candidates"] == 9
            
            mock_v3_service.force_sync_to_ltm.assert_called_once_with("sync_user")
    
    def test_preload_hot_memories_endpoint(self, client, mock_v3_service):
        """Test preload hot memories endpoint"""
        
        mock_v3_service.preload_hot_memories.return_value = {
            "preloaded": 5,
            "total_hot": 7
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.post("/memories/preload", params={
                "user_id": "preload_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["preloaded"] == 5
            assert data["total_hot"] == 7
            
            mock_v3_service.preload_hot_memories.assert_called_once_with("preload_user")
    
    def test_shuttle_stats_endpoint(self, client, mock_v3_service):
        """Test shuttle stats endpoint"""
        
        mock_v3_service.get_shuttle_stats.return_value = {
            "is_running": True,
            "global_stats": {
                "uploads_completed": 25,
                "uploads_failed": 2
            },
            "user_stats": {
                "pending_uploads": 3,
                "last_upload": "2024-01-01T12:00:00"
            }
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/shuttle/stats", params={
                "user_id": "shuttle_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_running"] is True
            assert data["global_stats"]["uploads_completed"] == 25
            assert data["user_stats"]["pending_uploads"] == 3
            
            mock_v3_service.get_shuttle_stats.assert_called_once_with("shuttle_user")
    
    def test_create_session_endpoint(self, client, mock_v3_service):
        """Test session creation endpoint"""
        
        mock_v3_service.create_session.return_value = "session_api_123"
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.post("/sessions/", json={
                "user_id": "session_user",
                "metadata": {"session_type": "api_test"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "session_api_123"
            
            mock_v3_service.create_session.assert_called_once_with(
                "session_user",
                {"session_type": "api_test"}
            )
    
    def test_get_session_endpoint(self, client, mock_v3_service):
        """Test session retrieval endpoint"""
        
        mock_v3_service.get_session.return_value = {
            "id": "session_get_123",
            "user_id": "session_user",
            "created_at": "2024-01-01T12:00:00",
            "state": {"key": "value"}
        }
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/sessions/session_get_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "session_get_123"
            assert data["user_id"] == "session_user"
            assert data["state"]["key"] == "value"
            
            mock_v3_service.get_session.assert_called_once_with("session_get_123")
    
    def test_get_session_not_found(self, client, mock_v3_service):
        """Test session retrieval when session not found"""
        
        mock_v3_service.get_session.return_value = None
        
        with patch('api.routes.memory_service', mock_v3_service):
            response = client.get("/sessions/nonexistent")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_concurrent_requests(self, client, mock_v3_service):
        """Test handling multiple concurrent requests"""
        
        import threading
        import time
        
        # Mock responses with slight delays to simulate real processing
        async def mock_add_memory(*args, **kwargs):
            await asyncio.sleep(0.01)  # Small delay
            return {"id": f"concurrent_{threading.current_thread().ident}", "status": "added"}
        
        mock_v3_service.add_memory = AsyncMock(side_effect=mock_add_memory)
        
        with patch('api.routes.memory_service', mock_v3_service):
            # Send multiple requests concurrently
            import concurrent.futures
            
            def make_request(i):
                return client.post("/memories/", json={
                    "content": f"Concurrent test {i}",
                    "user_id": f"concurrent_user_{i}"
                })
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, i) for i in range(5)]
                responses = [future.result() for future in futures]
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "added"
                assert "concurrent_" in data["id"]
            
            # Service should have been called 5 times
            assert mock_v3_service.add_memory.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])