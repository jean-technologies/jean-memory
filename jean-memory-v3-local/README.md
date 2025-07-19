# Jean Memory V3 Local Service

A local Python service that provides browser-based "Mini-Me" capabilities using:
- **FAISS** for high-performance vector storage and search
- **Local Neo4j** for graph operations and temporal reasoning
- **mem0** for unified memory management
- **Graphiti** for advanced entity extraction and relationships

## Architecture

```
Browser → FastAPI Service (localhost:8766) → FAISS + Neo4j → Background Sync to Cloud
```

## Features

- **True Local Storage**: FAISS vector database with cosine similarity
- **Graph Intelligence**: Local Neo4j with APOC for relationship mapping
- **Instant Search**: Sub-100ms semantic search on local memories
- **Background Sync**: Automatic synchronization to Jean Memory V2 cloud
- **Offline Capable**: Full functionality without internet connection
- **Privacy First**: Data stays local until explicitly synced

## Installation

```bash
cd jean-memory-v3-local
pip install -r requirements.txt
```

## Usage

```bash
# Start the local service
python main.py

# Service will be available at http://localhost:8766
```

## API Endpoints

- `POST /api/v3/memories/` - Create memory locally
- `GET /api/v3/memories/search` - Search local memories  
- `POST /api/v3/sync` - Sync to cloud
- `GET /api/v3/status` - Service health and stats

## Configuration

The service automatically configures:
- FAISS vector store in `./data/faiss/`
- Local Neo4j via Docker on port 7688
- Background sync to your Jean Memory V2 instance