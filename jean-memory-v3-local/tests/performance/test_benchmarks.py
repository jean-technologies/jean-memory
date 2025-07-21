"""
Performance benchmark tests for Jean Memory V3
Tests memory operations under various loads and measures performance metrics
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
import statistics
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.stm_service import STMService, STMMemory
from services.ltm_service import LTMService
from services.memory_shuttle import MemoryShuttle
from services.memory_service import JeanMemoryV3Service
from config import JeanMemoryV3Config


@pytest.mark.performance
class TestMemoryPerformanceBenchmarks:
    """Performance benchmark tests for memory operations"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for performance tests"""
        config = Mock(spec=JeanMemoryV3Config)
        config.openai_api_key = "test-key"
        config.max_local_memories = 10000  # Higher limit for performance testing
        config.jean_memory_v2_api_url = "https://api.test.com"
        config.jean_memory_v2_api_key = "test-ltm-key"
        config.neo4j_host = "localhost"
        config.neo4j_port = 7687
        config.neo4j_user = "neo4j"
        config.neo4j_password = "testpass"
        config.data_dir = "/tmp/test_perf"
        return config
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="memory_creation")
    async def test_stm_memory_creation_performance(self, benchmark, mock_config):
        """Benchmark STM memory creation performance"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test_perf/faiss",
                 "neo4j": "/tmp/test_perf/neo4j",
                 "models": "/tmp/test_perf/models",
                 "logs": "/tmp/test_perf/logs",
                 "temp": "/tmp/test_perf/temp"
             }), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory:
            
            # Setup fast mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            mock_memory_instance = Mock()
            mock_memory_instance.add = Mock(return_value={"id": "perf_mem"})
            mock_memory.return_value = mock_memory_instance
            
            # Initialize service
            stm = STMService()
            await stm.initialize()
            
            # Benchmark function
            async def create_memory():
                return await stm.add_memory(
                    content="Performance test memory content",
                    user_id="perf_user",
                    metadata={"test": "performance"}
                )
            
            # Run benchmark
            result = await benchmark.pedantic(create_memory, rounds=100, iterations=1)
            
            assert result is not None
            await stm.cleanup()
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="memory_search")
    async def test_stm_memory_search_performance(self, benchmark, mock_config):
        """Benchmark STM memory search performance"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test_perf/faiss",
                 "neo4j": "/tmp/test_perf/neo4j",
                 "models": "/tmp/test_perf/models",
                 "logs": "/tmp/test_perf/logs",
                 "temp": "/tmp/test_perf/temp"
             }), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory:
            
            # Setup mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 100, "edges": 50})
            mock_graph.return_value = mock_graph_instance
            
            mock_memory_instance = Mock()
            mock_memory_instance.search = Mock(return_value=[
                {"memory": "Performance test memory 1", "score": 0.9},
                {"memory": "Performance test memory 2", "score": 0.8},
                {"memory": "Performance test memory 3", "score": 0.7}
            ])
            mock_memory.return_value = mock_memory_instance
            
            # Initialize service and add some test data
            stm = STMService()
            await stm.initialize()
            
            # Add test memories to search through
            for i in range(10):
                memory = STMMemory(
                    f"perf_mem_{i}",
                    f"Performance test memory {i}",
                    "perf_user"
                )
                stm.memories[f"perf_mem_{i}"] = memory
            stm.user_memories["perf_user"] = [f"perf_mem_{i}" for i in range(10)]
            
            # Benchmark function
            async def search_memories():
                return await stm.search_memories(
                    query="performance test",
                    user_id="perf_user",
                    limit=10
                )
            
            # Run benchmark
            result = await benchmark.pedantic(search_memories, rounds=50, iterations=1)
            
            assert len(result) > 0
            await stm.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations_performance(self, mock_config):
        """Test performance under concurrent memory operations"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test_perf/faiss",
                 "neo4j": "/tmp/test_perf/neo4j",
                 "models": "/tmp/test_perf/models",
                 "logs": "/tmp/test_perf/logs",
                 "temp": "/tmp/test_perf/temp"
             }), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory:
            
            # Setup fast mocks
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            mock_memory_instance = Mock()
            mock_memory_instance.add = Mock(return_value={"id": "concurrent_mem"})
            mock_memory_instance.search = Mock(return_value=[
                {"memory": "Concurrent test memory", "score": 0.9}
            ])
            mock_memory.return_value = mock_memory_instance
            
            # Initialize service
            stm = STMService()
            await stm.initialize()
            
            # Test concurrent operations
            concurrent_tasks = 50
            start_time = time.time()
            
            async def create_and_search(task_id):
                # Create memory
                memory = await stm.add_memory(
                    content=f"Concurrent test memory {task_id}",
                    user_id=f"concurrent_user_{task_id % 5}",  # 5 different users
                    metadata={"task_id": task_id, "test": "concurrent"}
                )
                
                # Search for memory
                results = await stm.search_memories(
                    query="concurrent test",
                    user_id=f"concurrent_user_{task_id % 5}",
                    limit=5
                )
                
                return {"memory": memory, "search_results": results}
            
            # Run concurrent tasks
            tasks = [create_and_search(i) for i in range(concurrent_tasks)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify all operations completed successfully
            assert len(results) == concurrent_tasks
            for result in results:
                assert result["memory"] is not None
                assert isinstance(result["search_results"], list)
            
            # Performance assertions
            avg_time_per_operation = total_time / concurrent_tasks
            operations_per_second = concurrent_tasks / total_time
            
            print(f"\nConcurrent Performance Results:")
            print(f"Total concurrent operations: {concurrent_tasks}")
            print(f"Total time: {total_time:.2f} seconds")
            print(f"Average time per operation: {avg_time_per_operation:.3f} seconds")
            print(f"Operations per second: {operations_per_second:.2f}")
            
            # Performance benchmarks (adjust based on expected performance)
            assert avg_time_per_operation < 1.0  # Should complete in under 1 second per operation
            assert operations_per_second > 10  # Should handle at least 10 ops/second
            
            await stm.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_shuttle_throughput_performance(self, mock_config):
        """Test Memory Shuttle throughput performance"""
        
        with patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test_perf/faiss",
                 "neo4j": "/tmp/test_perf/neo4j",
                 "models": "/tmp/test_perf/models",
                 "logs": "/tmp/test_perf/logs",
                 "temp": "/tmp/test_perf/temp"
             }), \
             patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory, \
             patch('httpx.AsyncClient') as mock_http:
            
            # Setup mocks for performance
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            mock_memory_instance = Mock()
            mock_memory_instance.add = Mock(return_value={"id": "shuttle_mem"})
            mock_memory.return_value = mock_memory_instance
            
            # Setup fast HTTP client for LTM
            mock_http_instance = Mock()
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            
            upload_response = Mock()
            upload_response.status_code = 200
            upload_response.json.return_value = {"id": "ltm_mem", "status": "created"}
            
            async def mock_request(method, url, **kwargs):
                if url == "/health":
                    return health_response
                elif url == "/memories/" and method == "POST":
                    await asyncio.sleep(0.001)  # Simulate network latency
                    return upload_response
                return Mock(status_code=404)
            
            mock_http_instance.request = AsyncMock(side_effect=mock_request)
            mock_http_instance.get = AsyncMock(return_value=health_response)
            mock_http_instance.aclose = AsyncMock()
            mock_http.return_value = mock_http_instance
            
            # Initialize services
            stm = STMService()
            await stm.initialize()
            
            ltm = LTMService()
            await ltm.initialize()
            
            shuttle = MemoryShuttle(stm, ltm)
            
            # Add test memories to STM
            num_memories = 25
            start_time = time.time()
            
            for i in range(num_memories):
                await stm.add_memory(
                    content=f"Shuttle performance test memory {i}",
                    user_id="shuttle_perf_user",
                    metadata={"test": "shuttle_performance", "index": i}
                )
            
            memory_creation_time = time.time() - start_time
            
            # Test shuttle upload performance
            upload_start_time = time.time()
            upload_result = await shuttle.force_upload_user_memories("shuttle_perf_user")
            upload_time = time.time() - upload_start_time
            
            # Performance metrics
            memories_per_second_creation = num_memories / memory_creation_time
            
            print(f"\nMemory Shuttle Performance Results:")
            print(f"Memories created: {num_memories}")
            print(f"Memory creation time: {memory_creation_time:.2f} seconds")
            print(f"Memory creation rate: {memories_per_second_creation:.2f} memories/second")
            print(f"Upload time: {upload_time:.2f} seconds")
            print(f"Upload result: {upload_result}")
            
            # Performance assertions
            assert memories_per_second_creation > 5  # Should create at least 5 memories/second
            assert upload_time < 10  # Upload should complete in reasonable time
            
            # Cleanup
            await shuttle.stop()
            await stm.cleanup()
            await ltm.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_service_end_to_end_performance(self, mock_config):
        """Test complete V3 service end-to-end performance"""
        
        with patch('services.memory_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_config', return_value=mock_config), \
             patch('services.ltm_service.get_config', return_value=mock_config), \
             patch('services.stm_service.get_data_paths', return_value={
                 "faiss": "/tmp/test_perf/faiss",
                 "neo4j": "/tmp/test_perf/neo4j",
                 "models": "/tmp/test_perf/models",
                 "logs": "/tmp/test_perf/logs",
                 "temp": "/tmp/test_perf/temp"
             }), \
             patch('services.stm_service.GraphService') as mock_graph, \
             patch('services.stm_service.Memory') as mock_memory, \
             patch('httpx.AsyncClient') as mock_http, \
             patch('services.memory_service.GoogleADKMemoryService') as mock_google, \
             patch('services.memory_service.HybridMemoryOrchestrator') as mock_hybrid, \
             patch('services.memory_service.InMemorySessionService') as mock_session, \
             patch('services.memory_service.create_memory_service') as mock_create_memory:
            
            # Setup all mocks for fast operation
            mock_graph_instance = Mock()
            mock_graph_instance.initialize = AsyncMock()
            mock_graph_instance.add_memory_to_graph = AsyncMock()
            mock_graph_instance.is_ready = Mock(return_value=True)
            mock_graph_instance.cleanup = AsyncMock()
            mock_graph_instance.get_graph_stats = AsyncMock(return_value={"nodes": 0, "edges": 0})
            mock_graph.return_value = mock_graph_instance
            
            mock_memory_instance = Mock()
            mock_memory_instance.add = Mock(return_value={"id": "e2e_mem"})
            mock_memory_instance.search = Mock(return_value=[
                {"memory": "End-to-end test memory", "score": 0.95}
            ])
            mock_memory.return_value = mock_memory_instance
            
            # Setup other service mocks
            mock_google_instance = Mock()
            mock_google_instance.initialize = AsyncMock()
            mock_google_instance.initialized = True
            mock_google.return_value = mock_google_instance
            
            mock_hybrid_instance = Mock()
            mock_hybrid_instance.initialize = AsyncMock()
            mock_hybrid_instance.initialized = True
            mock_hybrid.return_value = mock_hybrid_instance
            
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock ADK Memory service
            mock_adk_memory = Mock()
            search_result = Mock()
            search_result.memories = [
                {
                    "id": "e2e_mem_1",
                    "content": "End-to-end test memory",
                    "score": 0.95,
                    "metadata_": {"source": "stm"}
                }
            ]
            search_result.source = "stm"
            search_result.execution_time_ms = 50
            
            mock_adk_memory.add_memory = AsyncMock(return_value={"id": "e2e_mem_1", "status": "added"})
            mock_adk_memory.search_memories = AsyncMock(return_value=search_result)
            mock_create_memory.return_value = mock_adk_memory
            
            # HTTP mock
            mock_http_instance = Mock()
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            mock_http_instance.get = AsyncMock(return_value=health_response)
            mock_http_instance.aclose = AsyncMock()
            mock_http.return_value = mock_http_instance
            
            # Performance test
            num_operations = 20
            
            # Initialize V3 service
            init_start_time = time.time()
            v3_service = JeanMemoryV3Service()
            await v3_service.initialize()
            init_time = time.time() - init_start_time
            
            # Test add/search cycle performance
            operation_times = []
            
            for i in range(num_operations):
                op_start_time = time.time()
                
                # Add memory
                add_result = await v3_service.add_memory(
                    content=f"E2E performance test memory {i}",
                    user_id="e2e_perf_user",
                    metadata={"test": "e2e_performance", "index": i}
                )
                
                # Search for memory
                search_result = await v3_service.search_memories(
                    query="e2e performance",
                    user_id="e2e_perf_user",
                    limit=5
                )
                
                op_time = time.time() - op_start_time
                operation_times.append(op_time)
            
            # Calculate performance metrics
            total_operation_time = sum(operation_times)
            avg_operation_time = statistics.mean(operation_times)
            min_operation_time = min(operation_times)
            max_operation_time = max(operation_times)
            operations_per_second = num_operations / total_operation_time
            
            print(f"\nEnd-to-End Performance Results:")
            print(f"Service initialization time: {init_time:.2f} seconds")
            print(f"Total operations: {num_operations}")
            print(f"Total operation time: {total_operation_time:.2f} seconds")
            print(f"Average operation time: {avg_operation_time:.3f} seconds")
            print(f"Min operation time: {min_operation_time:.3f} seconds")
            print(f"Max operation time: {max_operation_time:.3f} seconds")
            print(f"Operations per second: {operations_per_second:.2f}")
            
            # Performance assertions
            assert init_time < 5.0  # Service should initialize quickly
            assert avg_operation_time < 0.5  # Average operation should be fast
            assert operations_per_second > 2  # Should handle at least 2 ops/second
            
            # Cleanup
            await v3_service.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])