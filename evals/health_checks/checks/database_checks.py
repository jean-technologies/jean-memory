"""
Database connectivity and health checks for Jean Memory
Tests PostgreSQL, Qdrant, and Neo4j connections
"""

import asyncio
import os
import sys
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Add the API directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../openmemory/api'))

from .base import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)

class DatabaseHealthCheck(HealthCheck):
    """Comprehensive database health checks"""
    
    def __init__(self):
        super().__init__("Database Layer")
    
    async def run_checks(self, level: str = "critical") -> HealthCheckResult:
        """Run database connectivity checks"""
        result = HealthCheckResult(self.name)
        
        # PostgreSQL checks
        await self._check_postgresql(result)
        
        # Qdrant checks  
        await self._check_qdrant(result)
        
        # Neo4j checks
        await self._check_neo4j(result)
        
        return result
    
    async def _check_postgresql(self, result: HealthCheckResult) -> None:
        """Check PostgreSQL database connectivity and basic operations"""
        try:
            from app.database import get_database_url, engine
            from sqlalchemy import text
            
            # Test 1: Database URL configuration
            try:
                db_url = get_database_url()
                if not db_url:
                    result.add_check("PostgreSQL - Configuration", False, "DATABASE_URL not configured")
                    return
                result.add_check("PostgreSQL - Configuration", True, "DATABASE_URL configured")
            except Exception as e:
                result.add_check("PostgreSQL - Configuration", False, f"Config error: {e}")
                return
            
            # Test 2: Database connection
            try:
                from sqlalchemy import create_engine
                test_engine = create_engine(db_url)
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                result.add_check("PostgreSQL - Connection", True, "Successfully connected")
            except Exception as e:
                result.add_check("PostgreSQL - Connection", False, f"Connection failed: {e}")
                return
            
            # Test 3: Check critical tables exist
            try:
                with test_engine.connect() as conn:
                    # Check users table
                    conn.execute(text("SELECT COUNT(*) FROM users LIMIT 1"))
                    result.add_check("PostgreSQL - Users Table", True, "Users table accessible")
                    
                    # Check memories table  
                    conn.execute(text("SELECT COUNT(*) FROM memories LIMIT 1"))
                    result.add_check("PostgreSQL - Memories Table", True, "Memories table accessible")
                    
                    # Check apps table
                    conn.execute(text("SELECT COUNT(*) FROM apps LIMIT 1"))
                    result.add_check("PostgreSQL - Apps Table", True, "Apps table accessible")
                    
            except Exception as e:
                result.add_check("PostgreSQL - Schema", False, f"Schema validation failed: {e}")
                
        except ImportError as e:
            result.add_check("PostgreSQL - Import", False, f"Import failed: {e}")
        except Exception as e:
            result.add_check("PostgreSQL - General", False, f"Unexpected error: {e}")
    
    async def _check_qdrant(self, result: HealthCheckResult) -> None:
        """Check Qdrant vector database connectivity"""
        try:
            # Test 1: Environment configuration
            qdrant_host = os.getenv('QDRANT_HOST')
            if not qdrant_host:
                result.add_check("Qdrant - Configuration", False, "QDRANT_HOST not configured")
                return
            result.add_check("Qdrant - Configuration", True, f"QDRANT_HOST: {qdrant_host}")
            
            # Test 2: Import qdrant client
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.http.exceptions import UnexpectedResponse
                result.add_check("Qdrant - Import", True, "Qdrant client imported successfully")
            except ImportError as e:
                result.add_check("Qdrant - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic connectivity
            try:
                client = QdrantClient(host=qdrant_host, port=6333)
                collections = client.get_collections()
                result.add_check("Qdrant - Connection", True, f"Connected, found {len(collections.collections)} collections")
            except Exception as e:
                result.add_check("Qdrant - Connection", False, f"Connection failed: {e}")
                return
            
            # Test 4: Test collection operations (non-destructive)
            try:
                # Try to get info about collections
                info = client.get_collections()
                collection_names = [c.name for c in info.collections]
                result.add_check("Qdrant - Collections", True, f"Collections: {collection_names}")
            except Exception as e:
                result.add_check("Qdrant - Collections", False, f"Collection query failed: {e}")
                
        except Exception as e:
            result.add_check("Qdrant - General", False, f"Unexpected error: {e}")
    
    async def _check_neo4j(self, result: HealthCheckResult) -> None:
        """Check Neo4j graph database connectivity"""
        try:
            # Test 1: Environment configuration
            neo4j_uri = os.getenv('NEO4J_URI')
            neo4j_user = os.getenv('NEO4J_USER')
            neo4j_password = os.getenv('NEO4J_PASSWORD')
            
            if not neo4j_uri:
                result.add_check("Neo4j - Configuration", False, "NEO4J_URI not configured")
                return
            if not neo4j_user:
                result.add_check("Neo4j - Configuration", False, "NEO4J_USER not configured")
                return  
            if not neo4j_password:
                result.add_check("Neo4j - Configuration", False, "NEO4J_PASSWORD not configured")
                return
                
            result.add_check("Neo4j - Configuration", True, f"Neo4j configured: {neo4j_uri}")
            
            # Test 2: Import neo4j driver
            try:
                from neo4j import GraphDatabase
                result.add_check("Neo4j - Import", True, "Neo4j driver imported successfully")
            except ImportError as e:
                result.add_check("Neo4j - Import", False, f"Import failed: {e}")
                return
            
            # Test 3: Basic connectivity  
            try:
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                with driver.session() as session:
                    result_query = session.run("RETURN 1 as test")
                    record = result_query.single()
                    if record and record["test"] == 1:
                        result.add_check("Neo4j - Connection", True, "Successfully connected")
                    else:
                        result.add_check("Neo4j - Connection", False, "Connection test failed")
                driver.close()
            except Exception as e:
                result.add_check("Neo4j - Connection", False, f"Connection failed: {e}")
                return
                
            # Test 4: Check database info
            try:
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                with driver.session() as session:
                    # Get node count (non-destructive)
                    node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                    node_count = node_result.single()["node_count"]
                    
                    # Get relationship count
                    rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")  
                    rel_count = rel_result.single()["rel_count"]
                    
                    result.add_check("Neo4j - Database Info", True, 
                                   f"Nodes: {node_count}, Relationships: {rel_count}")
                driver.close()
            except Exception as e:
                result.add_check("Neo4j - Database Info", False, f"Database query failed: {e}")
                
        except Exception as e:
            result.add_check("Neo4j - General", False, f"Unexpected error: {e}")