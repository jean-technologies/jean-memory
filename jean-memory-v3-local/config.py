"""
Jean Memory V3 Local Service Configuration
"""

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

class JeanMemoryV3Config(BaseSettings):
    """Configuration for Jean Memory V3 Local Service"""
    
    # Service Configuration
    host: str = Field(default="localhost", description="Service host")
    port: int = Field(default=8766, description="Service port")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Data Directory
    data_dir: Path = Field(default=Path("./data"), description="Local data directory")
    
    # FAISS Configuration
    faiss_index_type: str = Field(default="IndexFlatIP", description="FAISS index type")
    faiss_distance_strategy: str = Field(default="cosine", description="Distance strategy")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Local embedding model")
    embedding_dim: int = Field(default=384, description="Embedding dimensions")
    
    # Local Neo4j Configuration  
    neo4j_host: str = Field(default="localhost", description="Neo4j host")
    neo4j_port: int = Field(default=7688, description="Neo4j port (different from cloud)")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="local_password", description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")
    
    # Docker Configuration
    enable_docker: bool = Field(default=False, description="Enable Docker for Neo4j (requires Docker installed)")
    enable_neo4j: bool = Field(default=False, description="Enable Neo4j features (requires running Neo4j instance)")
    
    # Cloud Sync Configuration (Optional)
    cloud_api_url: Optional[str] = Field(default=None, description="Jean Memory V2 Cloud API URL")
    cloud_api_key: Optional[str] = Field(default=None, description="Cloud API key")
    sync_enabled: bool = Field(default=False, description="Enable background sync")
    sync_interval: int = Field(default=300, description="Sync interval in seconds")
    
    # Jean Memory V2 Integration
    jean_memory_v2_api_url: Optional[str] = Field(default="https://api.jeanmemory.com", description="Jean Memory V2 API URL")
    jean_memory_v2_api_key: Optional[str] = Field(default=None, description="Jean Memory V2 API key")
    
    # OpenAI Configuration (for embeddings fallback and entity extraction)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    
    # Google Cloud Configuration
    google_cloud_project: Optional[str] = Field(default=None, description="Google Cloud project ID")
    google_application_credentials: Optional[str] = Field(default=None, description="Path to Google service account JSON")
    google_adk_memory_bank_id: Optional[str] = Field(default=None, description="Google ADK Memory Bank ID")
    vertex_ai_location: str = Field(default="us-central1", description="Vertex AI region/location")
    
    # Performance Settings
    max_local_memories: int = Field(default=50000, description="Maximum local memories")
    batch_size: int = Field(default=100, description="Processing batch size")
    memory_ttl_days: int = Field(default=30, description="Local memory TTL in days")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global configuration instance
config = JeanMemoryV3Config()

def get_config() -> JeanMemoryV3Config:
    """Get the global configuration instance"""
    return config

def get_data_paths() -> dict:
    """Get all data directory paths"""
    base_dir = config.data_dir
    base_dir.mkdir(exist_ok=True)
    
    paths = {
        "faiss": base_dir / "faiss",
        "neo4j": base_dir / "neo4j", 
        "models": base_dir / "models",
        "logs": base_dir / "logs",
        "temp": base_dir / "temp"
    }
    
    # Create all directories
    for path in paths.values():
        path.mkdir(exist_ok=True)
    
    return paths

def get_mem0_config() -> dict:
    """Get mem0 configuration for FAISS backend"""
    paths = get_data_paths()
    
    mem0_config = {
        "vector_store": {
            "provider": "faiss",
            "config": {
                "collection_name": "jean_memory_v3_local",
                "path": str(paths["faiss"])
            }
        },
        "embedder": {
            "provider": "sentence_transformers",
            "config": {
                "model": config.embedding_model
            }
        }
    }
    
    # Add OpenAI API key if available (required by mem0)
    if config.openai_api_key:
        mem0_config["llm"] = {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
                "api_key": config.openai_api_key
            }
        }
    
    return mem0_config

def get_neo4j_config() -> dict:
    """Get Neo4j configuration for local instance"""
    return {
        "uri": f"bolt://{config.neo4j_host}:{config.neo4j_port}",
        "user": config.neo4j_user,
        "password": config.neo4j_password,
        "database": config.neo4j_database
    }

def get_google_cloud_config() -> dict:
    """Get Google Cloud configuration for ADK integration"""
    return {
        "project_id": config.google_cloud_project,
        "credentials_path": config.google_application_credentials,
        "memory_bank_id": config.google_adk_memory_bank_id,
        "location": config.vertex_ai_location,
        "enabled": bool(config.google_cloud_project and config.google_adk_memory_bank_id)
    }

def get_docker_neo4j_config() -> dict:
    """Get Docker configuration for local Neo4j"""
    paths = get_data_paths()
    
    return {
        "image": "neo4j:5.26-community",
        "container_name": "jean-memory-v3-neo4j",
        "ports": {
            "7474": "7475",  # HTTP (avoid conflict with cloud)
            "7687": str(config.neo4j_port)  # Bolt
        },
        "environment": {
            "NEO4J_AUTH": f"{config.neo4j_user}/{config.neo4j_password}",
            "NEO4J_PLUGINS": '["apoc"]',
            "NEO4J_apoc_export_file_enabled": "true",
            "NEO4J_apoc_import_file_enabled": "true",
            "NEO4J_dbms_security_procedures_unrestricted": "apoc.*"
        },
        "volumes": {
            str(paths["neo4j"] / "data"): "/data",
            str(paths["neo4j"] / "logs"): "/logs"
        }
    }