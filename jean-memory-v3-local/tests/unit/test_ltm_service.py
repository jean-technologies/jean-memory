"""
Unit tests for LTM (Long-Term Memory) Service
Tests all methods and behaviors of LTMService class.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import httpx
import json

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ltm_service import LTMService
from config import JeanMemoryV3Config


class TestLTMService:
    """Test LTMService class functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = Mock(spec=JeanMemoryV3Config)
        config.jean_memory_v2_api_url = "https://api.test.com"
        config.jean_memory_v2_api_key = "test-api-key"
        return config
    
    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client"""
        client = Mock(spec=httpx.AsyncClient)
        client.aclose = AsyncMock()
        return client
    
    @pytest.fixture
    async def ltm_service(self, mock_config):
        """Create LTMService instance with mocked dependencies"""
        with patch('services.ltm_service.get_config', return_value=mock_config):
            service = LTMService()
            return service
    
    @pytest.mark.asyncio
    async def test_ltm_service_initialization_success(self, ltm_service, mock_http_client):
        """Test successful LTM service initialization"""
        
        # Mock successful health check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_http_client):
            await ltm_service.initialize()
            
            assert ltm_service.is_initialized is True
            assert ltm_service.client is not None
            mock_http_client.get.assert_called_once_with("/health")
    
    @pytest.mark.asyncio
    async def test_ltm_service_initialization_no_api_key(self, mock_config):
        """Test LTM initialization without API key"""
        mock_config.jean_memory_v2_api_key = None
        
        with patch('services.ltm_service.get_config', return_value=mock_config):
            service = LTMService()
            await service.initialize()
            
            assert service.is_initialized is False
            assert service.client is None
    
    @pytest.mark.asyncio
    async def test_ltm_service_initialization_health_check_fails(self, ltm_service, mock_http_client):
        """Test LTM initialization when health check fails"""
        
        # Mock failed health check
        mock_response = Mock()
        mock_response.status_code = 500
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_http_client):
            # Should not raise exception, should handle gracefully
            await ltm_service.initialize()
            
            assert ltm_service.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_upload_memory_success(self, ltm_service):
        """Test successful memory upload to LTM"""
        # Setup service as ready
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        # Mock successful API response
        expected_response = {
            "id": "ltm_memory_123",
            "status": "created",
            "content": "Test memory content"
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_response) as mock_request:
            result = await ltm_service.upload_memory(
                content="Test memory content",
                user_id="user123",
                app_id="test_app",
                metadata={"category": "test"}
            )
            
            assert result == expected_response
            mock_request.assert_called_once_with(
                "POST",
                "/memories/",
                json={
                    "messages": "Test memory content",
                    "user_id": "user123",
                    "metadata": {
                        "category": "test",
                        "source": "jean_memory_v3_stm",
                        "app_id": "test_app",
                        "uploaded_at": result["content"]  # Just checking structure
                    }
                }
            )
            
            # Verify the uploaded_at timestamp was added
            call_args = mock_request.call_args[1]["json"]
            assert "uploaded_at" in call_args["metadata"]
    
    @pytest.mark.asyncio
    async def test_upload_memory_not_ready(self, ltm_service):
        """Test memory upload when LTM is not ready"""
        ltm_service.is_initialized = False
        
        result = await ltm_service.upload_memory(
            content="Test content",
            user_id="user123"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_upload_memory_no_id_returned(self, ltm_service):
        """Test memory upload when API doesn't return ID"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        # Mock API response without ID
        with patch.object(ltm_service, '_make_request', return_value={"status": "error"}):
            result = await ltm_service.upload_memory(
                content="Test content",
                user_id="user123"
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_search_memories_success(self, ltm_service):
        """Test successful memory search"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        expected_response = {
            "memories": [
                {
                    "id": "mem1",
                    "content": "First memory",
                    "score": 0.9
                },
                {
                    "id": "mem2", 
                    "content": "Second memory",
                    "score": 0.7,
                    "metadata_": {"existing": "data"}
                }
            ]
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_response):
            results = await ltm_service.search_memories(
                query="test query",
                user_id="user123",
                limit=10
            )
            
            assert len(results) == 2
            assert results[0]["id"] == "mem1"
            assert results[0]["metadata_"]["source"] == "ltm"
            assert results[1]["metadata_"]["source"] == "ltm"
            assert results[1]["metadata_"]["existing"] == "data"  # Preserves existing metadata
    
    @pytest.mark.asyncio
    async def test_search_memories_not_ready(self, ltm_service):
        """Test search when LTM is not ready"""
        ltm_service.is_initialized = False
        
        results = await ltm_service.search_memories("query", "user123")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_get_memory_success(self, ltm_service):
        """Test getting specific memory"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        expected_memory = {
            "id": "mem123",
            "content": "Memory content",
            "user_id": "user123"
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_memory):
            result = await ltm_service.get_memory("mem123", "user123")
            
            assert result["id"] == "mem123"
            assert result["metadata_"]["source"] == "ltm"
    
    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, ltm_service):
        """Test getting non-existent memory"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        with patch.object(ltm_service, '_make_request', return_value=None):
            result = await ltm_service.get_memory("nonexistent", "user123")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_memories_success(self, ltm_service):
        """Test getting user memories"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        expected_response = {
            "memories": [
                {"id": "mem1", "content": "Memory 1"},
                {"id": "mem2", "content": "Memory 2"}
            ]
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_response):
            results = await ltm_service.get_user_memories(
                user_id="user123",
                limit=50,
                offset=0
            )
            
            assert len(results) == 2
            assert all(mem["metadata_"]["source"] == "ltm" for mem in results)
    
    @pytest.mark.asyncio
    async def test_delete_memory_success(self, ltm_service):
        """Test successful memory deletion"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        with patch.object(ltm_service, '_make_request', return_value={"deleted": True}):
            result = await ltm_service.delete_memory("mem123", "user123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_memory_failure(self, ltm_service):
        """Test failed memory deletion"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        with patch.object(ltm_service, '_make_request', return_value=None):
            result = await ltm_service.delete_memory("mem123", "user123")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_hot_memories(self, ltm_service):
        """Test getting hot memories for STM preloading"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        expected_response = {
            "memories": [
                {"id": "hot1", "content": "Hot memory 1"},
                {"id": "hot2", "content": "Hot memory 2"}
            ]
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_response):
            results = await ltm_service.get_hot_memories("user123", limit=20)
            
            assert len(results) == 2
            assert all(mem["metadata_"]["source"] == "ltm" for mem in results)
            assert all(mem["metadata_"]["is_hot"] is True for mem in results)
    
    @pytest.mark.asyncio
    async def test_get_life_narrative(self, ltm_service):
        """Test getting user's life narrative"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        expected_response = {
            "narrative": "This is the user's life story..."
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_response):
            result = await ltm_service.get_life_narrative("user123")
            
            assert result == "This is the user's life story..."
    
    @pytest.mark.asyncio
    async def test_get_categories(self, ltm_service):
        """Test getting user's memory categories"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        expected_response = {
            "categories": ["work", "personal", "travel"]
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_response):
            result = await ltm_service.get_categories("user123")
            
            assert result == ["work", "personal", "travel"]
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, ltm_service, mock_http_client):
        """Test successful HTTP request"""
        ltm_service.client = mock_http_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        result = await ltm_service._make_request(
            "GET",
            "/test",
            params={"param": "value"},
            json={"data": "test"}
        )
        
        assert result == {"result": "success"}
        mock_http_client.request.assert_called_once_with(
            method="GET",
            url="/test",
            params={"param": "value"},
            json={"data": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_make_request_not_found(self, ltm_service, mock_http_client):
        """Test HTTP request with 404 response"""
        ltm_service.client = mock_http_client
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_http_client.request = AsyncMock(return_value=mock_response)
        
        result = await ltm_service._make_request("GET", "/test")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_make_request_server_error_with_retry(self, ltm_service, mock_http_client):
        """Test HTTP request with server error and retry logic"""
        ltm_service.client = mock_http_client
        ltm_service.max_retries = 2
        ltm_service.retry_delay = 0.01  # Fast retry for testing
        
        # Mock server error then success
        error_response = Mock()
        error_response.status_code = 500
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"result": "success"}
        
        mock_http_client.request = AsyncMock(side_effect=[error_response, success_response])
        
        result = await ltm_service._make_request("GET", "/test")
        
        assert result == {"result": "success"}
        assert mock_http_client.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self, ltm_service, mock_http_client):
        """Test HTTP request when max retries are exceeded"""
        ltm_service.client = mock_http_client
        ltm_service.max_retries = 2
        ltm_service.retry_delay = 0.01
        
        # Mock consistent server errors
        error_response = Mock()
        error_response.status_code = 500
        mock_http_client.request = AsyncMock(return_value=error_response)
        
        result = await ltm_service._make_request("GET", "/test")
        
        assert result is None
        assert mock_http_client.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_make_request_exception_with_retry(self, ltm_service, mock_http_client):
        """Test HTTP request with exception and retry logic"""
        ltm_service.client = mock_http_client
        ltm_service.max_retries = 2
        ltm_service.retry_delay = 0.01
        
        # Mock exception then success
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"result": "success"}
        
        mock_http_client.request = AsyncMock(side_effect=[
            httpx.RequestError("Network error"),
            success_response
        ])
        
        result = await ltm_service._make_request("GET", "/test")
        
        assert result == {"result": "success"}
        assert mock_http_client.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_stats_success(self, ltm_service):
        """Test getting LTM statistics"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        expected_response = {
            "total_memories": 1000,
            "active_memories": 950,
            "categories_count": 15
        }
        
        with patch.object(ltm_service, '_make_request', return_value=expected_response):
            stats = await ltm_service.get_stats("user123")
            
            assert stats["total_memories"] == 1000
            assert stats["connected"] is True
            assert stats["source"] == "ltm"
    
    @pytest.mark.asyncio
    async def test_get_stats_not_ready(self, ltm_service):
        """Test getting stats when LTM is not ready"""
        ltm_service.is_initialized = False
        
        stats = await ltm_service.get_stats()
        
        assert stats["connected"] is False
        assert "error" in stats
        assert stats["source"] == "ltm"
    
    @pytest.mark.asyncio
    async def test_get_stats_api_failure(self, ltm_service):
        """Test getting stats when API fails"""
        ltm_service.is_initialized = True
        ltm_service.client = Mock()
        
        with patch.object(ltm_service, '_make_request', return_value=None):
            stats = await ltm_service.get_stats()
            
            assert stats["connected"] is True
            assert stats["total_memories"] == 0
            assert stats["source"] == "ltm"
    
    def test_is_ready(self, ltm_service):
        """Test service readiness check"""
        # Not initialized
        assert ltm_service.is_ready() is False
        
        # Initialized but no client
        ltm_service.is_initialized = True
        ltm_service.client = None
        assert ltm_service.is_ready() is False
        
        # Fully ready
        ltm_service.client = Mock()
        assert ltm_service.is_ready() is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, ltm_service, mock_http_client):
        """Test service cleanup"""
        ltm_service.client = mock_http_client
        
        await ltm_service.cleanup()
        
        assert ltm_service.client is None
        mock_http_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_no_client(self, ltm_service):
        """Test cleanup when no client exists"""
        ltm_service.client = None
        
        # Should not raise exception
        await ltm_service.cleanup()
        
        assert ltm_service.client is None


@pytest.mark.asyncio
async def test_integration_error_handling():
    """Test error handling across different scenarios"""
    
    # Test service creation with missing config
    with patch('services.ltm_service.get_config') as mock_config:
        mock_config.return_value.jean_memory_v2_api_url = None
        mock_config.return_value.jean_memory_v2_api_key = "test-key"
        
        service = LTMService()
        assert service.base_url == "https://api.jeanmemory.com"  # Default fallback
    
    # Test network timeout handling
    with patch('services.ltm_service.get_config') as mock_config:
        mock_config.return_value.jean_memory_v2_api_url = "https://api.test.com"
        mock_config.return_value.jean_memory_v2_api_key = "test-key"
        
        service = LTMService()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_class.return_value = mock_client
            
            # Should handle timeout gracefully
            await service.initialize()
            assert service.is_initialized is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])