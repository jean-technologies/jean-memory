"""
Docker Manager for Jean Memory V3 Local Service
Handles local Neo4j container lifecycle
"""

import asyncio
import logging
import subprocess
import json
from typing import Optional, Dict, Any

from config import get_config, get_docker_neo4j_config

logger = logging.getLogger(__name__)

class DockerManager:
    """Manages Docker containers for local services"""
    
    def __init__(self):
        self.config = get_config()
        self.neo4j_config = get_docker_neo4j_config()
        
    async def is_docker_available(self) -> bool:
        """Check if Docker is available and running"""
        try:
            result = await self._run_command(["docker", "--version"])
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    async def is_neo4j_running(self) -> bool:
        """Check if Neo4j container is running"""
        try:
            result = await self._run_command([
                "docker", "ps", "--filter", 
                f"name={self.neo4j_config['container_name']}", 
                "--format", "{{.Status}}"
            ])
            
            if result.returncode == 0 and result.stdout.strip():
                status = result.stdout.strip()
                return "Up" in status
            return False
            
        except Exception as e:
            logger.error(f"Error checking Neo4j status: {e}")
            return False
    
    async def start_neo4j(self) -> bool:
        """Start Neo4j container"""
        try:
            # Check if Docker is available
            if not await self.is_docker_available():
                raise RuntimeError("Docker is not available. Please install Docker Desktop.")
            
            # Check if container exists but is stopped
            if await self._container_exists():
                logger.info("Starting existing Neo4j container...")
                result = await self._run_command([
                    "docker", "start", self.neo4j_config['container_name']
                ])
                return result.returncode == 0
            
            # Create and start new container
            logger.info("Creating new Neo4j container...")
            docker_cmd = self._build_docker_run_command()
            
            result = await self._run_command(docker_cmd)
            if result.returncode != 0:
                logger.error(f"Failed to start Neo4j: {result.stderr}")
                return False
            
            logger.info("✅ Neo4j container started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Neo4j: {e}")
            return False
    
    async def stop_neo4j(self) -> bool:
        """Stop Neo4j container"""
        try:
            result = await self._run_command([
                "docker", "stop", self.neo4j_config['container_name']
            ])
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error stopping Neo4j: {e}")
            return False
    
    async def wait_for_neo4j(self, timeout: int = 60) -> bool:
        """Wait for Neo4j to be ready"""
        logger.info("Waiting for Neo4j to be ready...")
        
        for i in range(timeout):
            try:
                # Check if container is running
                if not await self.is_neo4j_running():
                    await asyncio.sleep(1)
                    continue
                
                # Try to connect to Neo4j
                result = await self._run_command([
                    "docker", "exec", self.neo4j_config['container_name'],
                    "cypher-shell", "-u", self.config.neo4j_user, 
                    "-p", self.config.neo4j_password,
                    "RETURN 1 as test"
                ])
                
                if result.returncode == 0:
                    logger.info(f"✅ Neo4j ready after {i+1} seconds")
                    return True
                    
            except Exception as e:
                logger.debug(f"Neo4j not ready yet: {e}")
            
            await asyncio.sleep(1)
        
        logger.error(f"❌ Neo4j not ready after {timeout} seconds")
        return False
    
    async def get_neo4j_logs(self, lines: int = 50) -> str:
        """Get Neo4j container logs"""
        try:
            result = await self._run_command([
                "docker", "logs", "--tail", str(lines), 
                self.neo4j_config['container_name']
            ])
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error getting logs: {e}"
    
    async def _container_exists(self) -> bool:
        """Check if Neo4j container exists"""
        try:
            result = await self._run_command([
                "docker", "ps", "-a", "--filter", 
                f"name={self.neo4j_config['container_name']}", 
                "--format", "{{.Names}}"
            ])
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False
    
    def _build_docker_run_command(self) -> list:
        """Build Docker run command for Neo4j"""
        cmd = [
            "docker", "run", "-d",
            "--name", self.neo4j_config['container_name']
        ]
        
        # Add port mappings
        for container_port, host_port in self.neo4j_config['ports'].items():
            cmd.extend(["-p", f"{host_port}:{container_port}"])
        
        # Add environment variables
        for env_key, env_value in self.neo4j_config['environment'].items():
            cmd.extend(["-e", f"{env_key}={env_value}"])
        
        # Add volume mappings
        for host_path, container_path in self.neo4j_config['volumes'].items():
            cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        # Add image
        cmd.append(self.neo4j_config['image'])
        
        return cmd
    
    async def _run_command(self, cmd: list) -> subprocess.CompletedProcess:
        """Run shell command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode('utf-8') if stdout else '',
                stderr=stderr.decode('utf-8') if stderr else ''
            )
            
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)} - {e}")
            raise
    
    async def get_container_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed container information"""
        try:
            result = await self._run_command([
                "docker", "inspect", self.neo4j_config['container_name']
            ])
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return info[0] if info else None
            return None
            
        except Exception as e:
            logger.error(f"Error getting container info: {e}")
            return None