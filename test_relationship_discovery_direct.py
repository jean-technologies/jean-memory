#!/usr/bin/env python3
"""
Direct test of relationship discovery fix
Tests the exact Neo4j relationship query that was fixed
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def test_relationship_discovery_direct():
    """Test the exact relationship discovery logic that was fixed"""
    
    print("🧪 Direct Relationship Discovery Test")
    print("=" * 50)
    
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'fasho93fasho'))
    
    with driver.session() as session:
        user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
        
        # Test the exact GraphRAG relationship query with fitness entities
        entities = ['fitness', 'activities', 'gym', 'workout']
        
        print(f"🎯 Testing with entities: {entities}")
        print(f"👤 User ID: {user_id}")
        
        # The exact query from GraphRAG pipeline
        cypher_query = """
        MATCH (n:Memory {user_id: $user_id})
        WHERE any(entity IN $entities WHERE n.text CONTAINS entity)
        WITH n
        MATCH (n)-[r]-(m:Memory {user_id: $user_id})
        WHERE any(entity IN $entities WHERE m.text CONTAINS entity)
        RETURN n, r, m
        LIMIT 50
        """
        
        print(f"\n🔍 Running GraphRAG relationship query...")
        result = session.run(cypher_query, user_id=user_id, entities=entities)
        
        # Process results using the FIXED logic
        nodes = []
        relationships = []
        
        record_count = 0
        for record in result:
            record_count += 1
            
            # Add nodes
            if record['n']:
                nodes.append({
                    "id": record['n'].element_id,
                    "text": record['n']['text'][:50] + "..."
                })
            if record['m']:
                nodes.append({
                    "id": record['m'].element_id,
                    "text": record['m']['text'][:50] + "..."
                })
            
            # FIXED: Check for None explicitly instead of truthy check
            if record['r'] is not None:
                relationships.append({
                    "type": record['r'].type,
                    "start": record['n'].element_id if record['n'] else None,
                    "end": record['m'].element_id if record['m'] else None
                })
                
                if record_count <= 3:  # Show first 3 relationships
                    print(f"  ✅ Found relationship: {record['r'].type}")
                    print(f"     From: {record['n']['text'][:40]}...")
                    print(f"     To:   {record['m']['text'][:40]}...")
        
        # Deduplicate nodes
        unique_nodes = []
        seen_ids = set()
        for node in nodes:
            if node['id'] not in seen_ids:
                seen_ids.add(node['id'])
                unique_nodes.append(node)
        
        print(f"\n📊 RESULTS:")
        print(f"  Records processed: {record_count}")
        print(f"  Unique nodes: {len(unique_nodes)}")
        print(f"  Relationships found: {len(relationships)}")
        
        if relationships:
            rel_types = [r['type'] for r in relationships]
            unique_types = list(set(rel_types))
            print(f"  Relationship types: {unique_types}")
            print(f"  TEMPORAL_NEIGHBOR: {rel_types.count('TEMPORAL_NEIGHBOR')}")
            print(f"  RELATED_TOPIC: {rel_types.count('RELATED_TOPIC')}")
            print(f"  🎉 SUCCESS: Relationship discovery is WORKING!")
        else:
            print(f"  ❌ FAILED: No relationships discovered")
        
        # Compare with previous bug (simulate old logic)
        print(f"\n🔄 Comparing with previous buggy logic...")
        old_relationships = []
        result2 = session.run(cypher_query, user_id=user_id, entities=entities)
        
        for record in result2:
            # OLD BUGGY LOGIC: if record['r']:
            if record['r']:  # This would fail because bool(relationship) == False
                old_relationships.append({
                    "type": record['r'].type
                })
        
        print(f"  Old logic would find: {len(old_relationships)} relationships")
        print(f"  New logic found: {len(relationships)} relationships")
        print(f"  Improvement: +{len(relationships) - len(old_relationships)} relationships")
        
        # Test a simple fitness relationship query
        print(f"\n🏋️ Testing fitness-specific relationships...")
        fitness_query = """
        MATCH (n:Memory {user_id: $user_id})-[r]->(m:Memory {user_id: $user_id})
        WHERE n.text CONTAINS 'fitness' OR n.text CONTAINS 'gym'
        RETURN type(r) as rel_type, count(*) as count
        ORDER BY count DESC
        """
        
        result3 = session.run(fitness_query, user_id=user_id)
        print(f"  Fitness-related relationship types:")
        for record in result3:
            print(f"    {record['rel_type']}: {record['count']}")
    
    driver.close()

if __name__ == "__main__":
    test_relationship_discovery_direct() 