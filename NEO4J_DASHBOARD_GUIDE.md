# Neo4j Dashboard Visualization Guide

## 🌐 Accessing Your Neo4j Browser Dashboard

### Step 1: Connect to Neo4j Browser
1. **Open your web browser** and navigate to: **https://browser.neo4j.io/**
2. **Click "Connect"** and enter your connection details:
   - **Connection URL**: `neo4j+s://6ff1aa85.databases.neo4j.io`
   - **Username**: `neo4j`
   - **Password**: `C3eGPnhmr3wfLAGyGDS1JzWIkaJakvlDhEDJguSjZ-Y`

### Step 2: Explore Your Current Database

Once connected, you'll see a query interface. Try these queries:

#### 🔍 **Basic Database Overview**
```cypher
// See all node types and counts
MATCH (n) 
RETURN labels(n) as NodeType, count(n) as Count
ORDER BY Count DESC
```

#### 🔗 **View All Relationships**
```cypher
// See all relationship types and counts
MATCH ()-[r]->() 
RETURN type(r) as RelationshipType, count(r) as Count
ORDER BY Count DESC
```

#### 📊 **Current Data Visualization**
```cypher
// Show a sample of your current graph
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 25
```

## 🎯 Enhanced Memory Visualization

Since your enhanced memories aren't migrated yet, here are your options:

### Option 1: View Enhanced Preprocessing Results Locally
Your enhanced memories are in: `sample_30_preprocessed_v2.json`

**Key Improvements to Look For:**
- **Temporal Context**: "Ongoing routine as of [date]" vs bare dates
- **Confidence Levels**: 28 medium confidence (up from 21), 0 low confidence (down from 8)
- **Better Keywords**: More meaningful temporal keywords

### Option 2: Cypher Queries for Future Memory Data

Once your enhanced memories are migrated, use these queries:

#### 🧠 **Memory-Specific Queries**
```cypher
// Find all memory nodes
MATCH (n) 
WHERE any(label IN labels(n) WHERE label CONTAINS 'Memory' OR label CONTAINS 'Episode')
RETURN n
LIMIT 50
```

#### ⏰ **Temporal Context Analysis**
```cypher
// Show memories with enhanced temporal contexts
MATCH (n)
WHERE n.temporal_context IS NOT NULL
RETURN n.content, n.temporal_context, n.confidence
ORDER BY n.confidence DESC
LIMIT 20
```

#### 🔄 **Routine & Habit Patterns**
```cypher
// Find ongoing activities and routines
MATCH (n)
WHERE n.temporal_context CONTAINS 'Ongoing'
RETURN n.content, n.temporal_context, n.confidence
ORDER BY n.created_at DESC
```

#### 🎯 **High-Confidence Memories**
```cypher
// Show high and medium confidence memories
MATCH (n)
WHERE n.confidence IN ['high', 'medium']
RETURN n.content, n.temporal_context, n.reasoning, n.confidence
ORDER BY 
  CASE n.confidence 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    ELSE 3 
  END
```

## 🎨 Dashboard Features

### Graph Visualization Controls
- **Zoom**: Mouse wheel or +/- buttons
- **Pan**: Click and drag
- **Node Selection**: Click on nodes to see properties
- **Relationship Inspection**: Click on edges to see details
- **Layout Options**: Different graph layout algorithms

### Query Results
- **Table View**: See data in rows and columns
- **Graph View**: Visual node-and-edge representation
- **Text View**: Raw query results
- **Export**: Download results as CSV or JSON

## 🚀 Next Steps for Enhanced Memory Visualization

1. **Resolve Migration Issue**: The database conflict needs to be resolved first
2. **Migrate Enhanced Data**: Load your `sample_30_preprocessed_v2.json` 
3. **Explore Enhanced Patterns**: Use the temporal context queries above
4. **Build Custom Dashboards**: Create saved queries for your specific use cases

## 📊 Alternative Visualization: Local Analysis

Until migration works, analyze your enhanced results locally:

```bash
# View enhanced preprocessing statistics
python3 -c "
import json
with open('sample_30_preprocessed_v2.json', 'r') as f:
    data = json.load(f)

print('Enhanced Memory Analysis:')
print(f'Total memories: {len(data["memories"])}')
print(f'High confidence: {data["high_confidence_count"]}')
print(f'Medium confidence: {data["medium_confidence_count"]}')

# Show sample enhanced contexts
for i, memory in enumerate(data['memories'][:5]):
    print(f'\n{i+1}. "{memory["memory_text"]}"')
    print(f'   Context: {memory["temporal_context"]}')
    print(f'   Confidence: {memory["confidence"]}')
"
```

Your enhanced temporal context extraction is working perfectly - the visualization will be amazing once we get the migration resolved! 