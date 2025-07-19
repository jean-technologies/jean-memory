#!/usr/bin/env python3
"""
Jean Memory V3 Local Service
Main entry point for the local memory service
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_config, get_data_paths
from services.docker_manager import DockerManager
from services.memory_service import MemoryService
from api.routes import router, set_memory_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("jean_memory_v3.log")
    ]
)
logger = logging.getLogger(__name__)

class JeanMemoryV3App:
    """Main application class for Jean Memory V3 Local Service"""
    
    def __init__(self):
        self.config = get_config()
        self.app = None
        self.docker_manager = None
        self.memory_service = None
        self.shutdown_event = asyncio.Event()
        
    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application"""
        
        app = FastAPI(
            title="Jean Memory V3 Local Service",
            description="Local memory service with FAISS + Neo4j backend",
            version="3.0.0",
            docs_url="/docs" if self.config.debug else None,
            redoc_url="/redoc" if self.config.debug else None
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://localhost:3001", 
                "https://jeanmemory.com",
                "https://*.jeanmemory.com"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Include API routes
        app.include_router(router, prefix="/api/v3")
        
        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Check if services are running
                docker_status = "unknown"
                memory_status = "unknown"
                
                if self.docker_manager:
                    docker_status = "running" if await self.docker_manager.is_neo4j_running() else "stopped"
                
                if self.memory_service:
                    memory_status = "ready" if self.memory_service.is_ready() else "initializing"
                
                return {
                    "status": "healthy",
                    "version": "3.0.0",
                    "services": {
                        "docker": docker_status,
                        "memory": memory_status
                    },
                    "data_dir": str(self.config.data_dir)
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail="Service unhealthy")
        
        # Root endpoint
        @app.get("/")
        async def root():
            """Root endpoint with service information"""
            return {
                "name": "Jean Memory V3 Local Service",
                "version": "3.0.0",
                "description": "Local memory service with FAISS + Neo4j backend",
                "docs_url": "/docs" if self.config.debug else None,
                "health_url": "/health"
            }
        
        return app
    
    async def startup(self):
        """Initialize all services on startup"""
        logger.info("🚀 Starting Jean Memory V3 Local Service...")
        
        try:
            # Ensure data directories exist
            data_paths = get_data_paths()
            logger.info(f"📁 Data directory: {self.config.data_dir}")
            
            # Initialize Docker manager
            logger.info("🐳 Initializing Docker manager...")
            self.docker_manager = DockerManager()
            
            # Start Neo4j if not running
            if not await self.docker_manager.is_neo4j_running():
                logger.info("🔧 Starting local Neo4j...")
                await self.docker_manager.start_neo4j()
                
                # Wait for Neo4j to be ready
                await self.docker_manager.wait_for_neo4j()
                logger.info("✅ Neo4j is ready")
            else:
                logger.info("✅ Neo4j is already running")
            
            # Initialize memory service
            logger.info("🧠 Initializing memory service...")
            self.memory_service = MemoryService()
            await self.memory_service.initialize()
            
            # Set memory service for API routes
            set_memory_service(self.memory_service)
            
            logger.info("✅ Memory service initialized")
            
            logger.info("🎉 Jean Memory V3 Local Service started successfully!")
            logger.info(f"🌐 Service available at http://{self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        logger.info("🔄 Shutting down Jean Memory V3 Local Service...")
        
        try:
            # Cleanup memory service
            if self.memory_service:
                await self.memory_service.cleanup()
                logger.info("✅ Memory service cleaned up")
            
            # Note: We don't stop Neo4j on shutdown to preserve data
            # It will continue running as a daemon
            
            logger.info("✅ Shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the application"""
        # Create FastAPI app
        self.app = self.create_app()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Initialize services
        await self.startup()
        
        # Configure uvicorn
        uvicorn_config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info" if self.config.debug else "warning",
            reload=False  # Disable reload for production
        )
        
        # Create server
        server = uvicorn.Server(uvicorn_config)
        
        # Run server with graceful shutdown
        server_task = asyncio.create_task(server.serve())
        shutdown_task = asyncio.create_task(self.shutdown_event.wait())
        
        try:
            # Wait for either server to complete or shutdown signal
            done, pending = await asyncio.wait(
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
        finally:
            await self.shutdown()

async def main():
    """Main entry point"""
    app = JeanMemoryV3App()
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)