#!/usr/bin/env python3
"""
Comprehensive System Check for Unified Memory Architecture

This script verifies the complete integration of:
1. mem0 for vector embeddings (Qdrant)
2. mem0 for graph relationships (Neo4j)
3. Graphiti for temporal episodes (Neo4j)
4. PostgreSQL metadata connections
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedMemorySystemCheck:
    """Comprehensive system check for unified memory architecture"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "integration_tests": {},
            "recommendations": []
        }
    
    async def check_mem0_vector(self) -> Dict[str, Any]:
        """Check mem0 vector storage (Qdrant)"""
        logger.info("🔍 Checking mem0 Vector Storage (Qdrant)...")
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            from qdrant_client import QdrantClient
            
            # Connect to Qdrant
            client = QdrantClient(host="localhost", port=6333)
            
            # Check collections
            collections = client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            result["details"]["collections"] = collection_names
            result["details"]["total_collections"] = len(collection_names)
            
            # Check unified memory collection
            if "unified_memory_mem0" in collection_names:
                collection_info = client.get_collection("unified_memory_mem0")
                result["details"]["unified_collection"] = {
                    "points_count": collection_info.points_count,
                    "vector_size": collection_info.config.params.vectors.size,
                    "status": "active"
                }
                
                # Sample some points
                if collection_info.points_count > 0:
                    points = client.scroll("unified_memory_mem0", limit=5)
                    result["details"]["sample_points"] = len(points[0])
                    
                    # Check payload structure
                    if points[0]:
                        sample_payload = points[0][0].payload
                        result["details"]["payload_fields"] = list(sample_payload.keys())
                
                result["status"] = "healthy"
            else:
                result["issues"].append("unified_memory_mem0 collection not found")
                result["status"] = "warning"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Qdrant connection error: {str(e)}")
        
        return result
    
    async def check_mem0_graph(self) -> Dict[str, Any]:
        """Check mem0 graph storage (Neo4j)"""
        logger.info("🔍 Checking mem0 Graph Storage (Neo4j)...")
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            from neo4j import GraphDatabase
            
            # Neo4j connection
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            username = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "your-neo4j-password")
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session() as session:
                # Check node counts
                node_result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                node_counts = {}
                for record in node_result:
                    label = record["labels"][0] if record["labels"] else "Unknown"
                    node_counts[label] = record["count"]
                
                result["details"]["node_counts"] = node_counts
                
                # Check relationship counts
                rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                rel_counts = {}
                for record in rel_result:
                    rel_counts[record["type"]] = record["count"]
                
                result["details"]["relationship_counts"] = rel_counts
                
                # Check for mem0 specific patterns
                mem0_check = session.run("""
                    MATCH (m:Memory)
                    RETURN count(m) as memory_count
                """)
                memory_count = mem0_check.single()["memory_count"]
                
                if memory_count > 0:
                    result["details"]["mem0_memories"] = memory_count
                    result["status"] = "healthy"
                else:
                    result["issues"].append("No Memory nodes found in Neo4j")
                    result["status"] = "warning"
            
            driver.close()
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Neo4j connection error: {str(e)}")
        
        return result
    
    async def check_graphiti(self) -> Dict[str, Any]:
        """Check Graphiti temporal episodes"""
        logger.info("🔍 Checking Graphiti Temporal Episodes...")
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            from graphiti_core import Graphiti
            
            # Initialize Graphiti
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "your-neo4j-password")
            
            graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
            
            # Check for episodes
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            
            with driver.session() as session:
                # Check episode nodes
                episode_result = session.run("""
                    MATCH (e:Episode)
                    RETURN count(e) as count, 
                           collect(DISTINCT e.name)[..5] as sample_names
                """)
                episode_data = episode_result.single()
                
                result["details"]["episode_count"] = episode_data["count"]
                result["details"]["sample_episodes"] = episode_data["sample_names"]
                
                # Check entity nodes
                entity_result = session.run("""
                    MATCH (n)
                    WHERE n:Person OR n:Activity OR n:Project
                    RETURN labels(n)[0] as type, count(n) as count
                """)
                
                entity_counts = {}
                for record in entity_result:
                    entity_counts[record["type"]] = record["count"]
                
                result["details"]["entity_counts"] = entity_counts
                
                if episode_data["count"] > 0:
                    result["status"] = "healthy"
                else:
                    result["issues"].append("No episodes found in Graphiti")
                    result["status"] = "warning"
            
            driver.close()
            await graphiti.close()
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Graphiti error: {str(e)}")
        
        return result
    
    async def check_postgresql_metadata(self) -> Dict[str, Any]:
        """Check PostgreSQL metadata connections"""
        logger.info("�� Checking PostgreSQL Metadata...")
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Connect to production database
            conn = psycopg2.connect(
                host='db.masapxpxcwvsjpuymbmd.supabase.co',
                port=5432,
                database='postgres',
                user='postgres',
                password='jeanmemorytypefasho'
            )
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check memories table
            cursor.execute("""
                SELECT COUNT(*) as total_memories,
                       COUNT(DISTINCT user_id) as unique_users,
                       MIN(created_at) as earliest_memory,
                       MAX(created_at) as latest_memory
                FROM memories
                WHERE deleted_at IS NULL
            """)
            memory_stats = cursor.fetchone()
            result["details"]["memory_stats"] = dict(memory_stats)
            
            # Check metadata structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'memories'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            result["details"]["memory_columns"] = [col['column_name'] for col in columns]
            
            # Check if metadata column exists
            has_metadata = any(col['column_name'] == 'metadata' for col in columns)
            if has_metadata:
                # Sample metadata
                cursor.execute("""
                    SELECT metadata 
                    FROM memories 
                    WHERE metadata IS NOT NULL 
                    AND metadata != '{}'::jsonb
                    LIMIT 5
                """)
                sample_metadata = cursor.fetchall()
                result["details"]["sample_metadata_count"] = len(sample_metadata)
            
            cursor.close()
            conn.close()
            
            result["status"] = "healthy"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"PostgreSQL error: {str(e)}")
        
        return result
    
    async def test_integration(self) -> Dict[str, Any]:
        """Test integration between components"""
        logger.info("🔍 Testing Component Integration...")
        
        result = {
            "mem0_qdrant_sync": "unknown",
            "mem0_neo4j_sync": "unknown",
            "graphiti_neo4j_sync": "unknown",
            "postgresql_tracking": "unknown"
        }
        
        try:
            # Test mem0 integration
            from unified_memory_ingestion import initialize_mem0
            
            memory = await initialize_mem0()
            
            # Test a simple search
            test_results = memory.search("test query", user_id="test_user", limit=5)
            
            if isinstance(test_results, dict) and 'results' in test_results:
                result["mem0_qdrant_sync"] = "working"
                if 'relations' in test_results:
                    result["mem0_neo4j_sync"] = "working"
            
            # Check if Graphiti and mem0 share the same Neo4j instance
            from neo4j import GraphDatabase
            
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            username = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "your-neo4j-password")
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session() as session:
                # Check for both Memory nodes (mem0) and Episode nodes (Graphiti)
                check_result = session.run("""
                    MATCH (m:Memory)
                    WITH count(m) as memory_count
                    MATCH (e:Episode)
                    RETURN memory_count, count(e) as episode_count
                """)
                
                data = check_result.single()
                if data and data["memory_count"] > 0 and data["episode_count"] > 0:
                    result["graphiti_neo4j_sync"] = "working"
            
            driver.close()
            
        except Exception as e:
            logger.error(f"Integration test error: {e}")
        
        return result
    
    async def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on system check"""
        recommendations = []
        
        # Check component statuses
        components = self.results.get("components", {})
        
        # Qdrant recommendations
        qdrant_status = components.get("mem0_vector", {})
        if qdrant_status.get("status") == "error":
            recommendations.append("🚨 CRITICAL: Qdrant is not accessible. Ensure Qdrant is running on localhost:6333")
        elif qdrant_status.get("details", {}).get("unified_collection", {}).get("points_count", 0) == 0:
            recommendations.append("⚠️ No vectors in unified_memory_mem0 collection. Run ingestion pipeline.")
        
        # Neo4j recommendations
        neo4j_status = components.get("mem0_graph", {})
        if neo4j_status.get("status") == "error":
            recommendations.append("🚨 CRITICAL: Neo4j is not accessible. Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        
        # Graphiti recommendations
        graphiti_status = components.get("graphiti", {})
        if graphiti_status.get("status") == "warning":
            recommendations.append("⚠️ No Graphiti episodes found. Consider creating temporal episodes for better context")
        
        # Integration recommendations
        integration = self.results.get("integration_tests", {})
        if integration.get("mem0_neo4j_sync") != "working":
            recommendations.append("⚠️ mem0 graph integration may not be working properly")
        
        # PostgreSQL recommendations
        pg_status = components.get("postgresql_metadata", {})
        if pg_status.get("status") == "healthy":
            memory_stats = pg_status.get("details", {}).get("memory_stats", {})
            if memory_stats:
                recommendations.append(f"✅ Production database has {memory_stats.get('total_memories', 0)} memories from {memory_stats.get('unique_users', 0)} users")
        
        return recommendations
    
    async def run_full_check(self):
        """Run complete system check"""
        print("🚀 UNIFIED MEMORY SYSTEM CHECK")
        print("=" * 80)
        
        # Check all components
        self.results["components"]["mem0_vector"] = await self.check_mem0_vector()
        self.results["components"]["mem0_graph"] = await self.check_mem0_graph()
        self.results["components"]["graphiti"] = await self.check_graphiti()
        self.results["components"]["postgresql_metadata"] = await self.check_postgresql_metadata()
        
        # Test integration
        self.results["integration_tests"] = await self.test_integration()
        
        # Generate recommendations
        self.results["recommendations"] = await self.generate_recommendations()
        
        # Display results
        self._display_results()
        
        # Save results
        output_file = Path("system_check_results.json")
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Full results saved to: {output_file}")
    
    def _display_results(self):
        """Display check results in a readable format"""
        print("\n📊 COMPONENT STATUS:")
        print("-" * 40)
        
        for component, status in self.results["components"].items():
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "error": "❌",
                "unknown": "❓"
            }.get(status.get("status", "unknown"), "❓")
            
            print(f"{status_emoji} {component}: {status.get('status', 'unknown')}")
            
            if status.get("issues"):
                for issue in status["issues"]:
                    print(f"   - {issue}")
            
            # Show key details
            details = status.get("details", {})
            if component == "mem0_vector" and "unified_collection" in details:
                uc = details["unified_collection"]
                print(f"   - Points: {uc.get('points_count', 0)}")
                print(f"   - Vector size: {uc.get('vector_size', 0)}")
            elif component == "mem0_graph" and "node_counts" in details:
                print(f"   - Nodes: {details['node_counts']}")
            elif component == "graphiti" and "episode_count" in details:
                print(f"   - Episodes: {details['episode_count']}")
                print(f"   - Entities: {details.get('entity_counts', {})}")
        
        print("\n🔗 INTEGRATION STATUS:")
        print("-" * 40)
        
        for test, status in self.results["integration_tests"].items():
            status_emoji = "✅" if status == "working" else "❌"
            print(f"{status_emoji} {test}: {status}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        
        for rec in self.results["recommendations"]:
            print(f"{rec}")

async def main():
    """Run system check"""
    checker = UnifiedMemorySystemCheck()
    await checker.run_full_check()

if __name__ == "__main__":
    asyncio.run(main())
