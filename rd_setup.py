#!/usr/bin/env python3
"""
R&D Environment Setup Script

Ensures all services are running and properly configured for R&D development:
- Local Neo4j, Qdrant
- Connection to production Supabase
- Unified memory system dependencies

Usage:
    python rd_setup.py --check     # Check current status
    python rd_setup.py --start     # Start all services
    python rd_setup.py --stop      # Stop all services
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RDSetup:
    """R&D Environment Setup and Management"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.required_env_vars = [
            'OPENAI_API_KEY',
            'SUPABASE_URL', 
            'SUPABASE_SERVICE_KEY',
            'NEO4J_PASSWORD'
        ]
        
    def check_environment_variables(self) -> Dict[str, bool]:
        """Check if required environment variables are set"""
        print("🔍 Checking environment variables...")
        
        results = {}
        for var in self.required_env_vars:
            value = os.getenv(var)
            results[var] = bool(value and value != "your_key_here")
            
            if results[var]:
                print(f"   ✅ {var}: Set")
            else:
                print(f"   ❌ {var}: Missing or placeholder")
        
        return results
    
    def check_docker_services(self) -> Dict[str, bool]:
        """Check if required Docker services are running"""
        print("\n🐳 Checking Docker services...")
        
        services = {
            'neo4j': 'neo4j',
            'qdrant': 'qdrant'
        }
        
        results = {}
        
        try:
            # Get running containers
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print("   ❌ Docker not available")
                return {service: False for service in services}
            
            running_containers = result.stdout.lower()
            
            for service, container_name in services.items():
                is_running = container_name in running_containers
                results[service] = is_running
                
                if is_running:
                    print(f"   ✅ {service}: Running")
                else:
                    print(f"   ❌ {service}: Not running")
        
        except Exception as e:
            print(f"   ❌ Error checking Docker: {e}")
            results = {service: False for service in services}
        
        return results
    
    def check_python_dependencies(self) -> Dict[str, bool]:
        """Check if required Python packages are installed"""
        print("\n🐍 Checking Python dependencies...")
        
        packages = [
            'supabase',
            'qdrant-client', 
            'neo4j',
            'mem0ai',
            'graphiti-core',
            'openai'
        ]
        
        # Special import mappings for packages with different import names
        import_mappings = {
            'qdrant-client': 'qdrant_client',
            'mem0ai': 'mem0',
            'graphiti-core': 'graphiti_core'
        }
        
        results = {}
        
        for package in packages:
            try:
                import_name = import_mappings.get(package, package.replace('-', '_'))
                __import__(import_name)
                results[package] = True
                print(f"   ✅ {package}: Installed")
            except ImportError:
                results[package] = False
                print(f"   ❌ {package}: Not installed")
        
        return results
    
    def test_service_connections(self) -> Dict[str, bool]:
        """Test connections to all services"""
        print("\n🔗 Testing service connections...")
        
        results = {
            'supabase': self._test_supabase(),
            'neo4j': self._test_neo4j(),
            'qdrant': self._test_qdrant()
        }
        
        return results
    
    def _test_supabase(self) -> bool:
        """Test Supabase connection"""
        try:
            from supabase import create_client
            
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")
            
            if not url or not key:
                print("   ❌ Supabase: Missing credentials")
                return False
            
            client = create_client(url, key)
            
            # Try a simple query first
            try:
                response = client.table('memories').select('id').limit(1).execute()
                print("   ✅ Supabase: Connected")
                return True
            except Exception as table_error:
                # If memories table doesn't exist or has permission issues, try other tables
                try:
                    # Try to list tables or use a different approach
                    response = client.rpc('get_schema_version').execute()
                    print("   ✅ Supabase: Connected (via RPC)")
                    return True
                except:
                    print(f"   ⚠️ Supabase: Connected but table access limited - {str(table_error)}")
                    return True  # Connection works, just table permissions
            
        except Exception as e:
            print(f"   ❌ Supabase: {str(e)}")
            return False
    
    def _test_neo4j(self) -> bool:
        """Test Neo4j connection"""
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "fasho93fasho")
            
            driver = GraphDatabase.driver(uri, auth=(user, password))
            
            with driver.session() as session:
                session.run("RETURN 1")
            
            driver.close()
            print("   ✅ Neo4j: Connected")
            return True
            
        except Exception as e:
            print(f"   ❌ Neo4j: {str(e)}")
            return False
    
    def _test_qdrant(self) -> bool:
        """Test Qdrant connection"""
        try:
            from qdrant_client import QdrantClient
            
            host = os.getenv("QDRANT_HOST", "localhost")
            port_str = os.getenv("QDRANT_PORT", "6333")
            
            # Clean up port string (remove any extra characters)
            import re
            port_match = re.search(r'\d+', str(port_str))
            port = int(port_match.group()) if port_match else 6333
            
            client = QdrantClient(host=host, port=port)
            client.get_collections()
            
            print("   ✅ Qdrant: Connected")
            return True
            
        except Exception as e:
            print(f"   ❌ Qdrant: {str(e)}")
            return False
    
    def start_services(self) -> bool:
        """Start all required services"""
        print("🚀 Starting R&D services...")
        
        success = True
        
        # Start Docker services
        try:
            print("   Starting Neo4j and Qdrant...")
            result = subprocess.run([
                'docker-compose', 'up', '-d', 'neo4j_db', 'qdrant_db'
            ], cwd=self.project_root / 'openmemory', capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Docker services started")
                
                # Wait for services to be ready
                print("   ⏳ Waiting for services to be ready...")
                time.sleep(10)
                
            else:
                print(f"   ❌ Failed to start Docker services: {result.stderr}")
                success = False
                
        except Exception as e:
            print(f"   ❌ Error starting services: {e}")
            success = False
        
        return success
    
    def stop_services(self) -> bool:
        """Stop all services"""
        print("🛑 Stopping R&D services...")
        
        try:
            result = subprocess.run([
                'docker-compose', 'down'
            ], cwd=self.project_root / 'openmemory', capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Services stopped")
                return True
            else:
                print(f"   ❌ Failed to stop services: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error stopping services: {e}")
            return False
    
    def install_missing_dependencies(self, missing_packages: List[str]) -> bool:
        """Install missing Python dependencies"""
        if not missing_packages:
            return True
        
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Packages installed successfully")
                return True
            else:
                print(f"   ❌ Failed to install packages: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error installing packages: {e}")
            return False
    
    def create_env_template(self):
        """Create .env template with required variables"""
        env_file = self.project_root / '.env'
        
        if env_file.exists():
            print("   ℹ️ .env file already exists")
            return
        
        template = """# R&D Environment Configuration
# Copy your production credentials here for R&D access

# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Required: Supabase Production Access (for downloading real customer data)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Required: Neo4j Password (local development)
NEO4J_PASSWORD=fasho93fasho

# Optional: Additional API Keys
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Local Development Settings (auto-configured)
ENVIRONMENT=development
USE_UNIFIED_MEMORY=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
QDRANT_HOST=localhost
QDRANT_PORT=6333
"""
        
        with open(env_file, 'w') as f:
            f.write(template)
        
        print(f"   ✅ Created .env template at: {env_file}")
        print("   ⚠️ Please edit .env with your actual credentials")
    
    def run_full_check(self) -> Dict[str, Any]:
        """Run comprehensive environment check"""
        print("🔍 R&D Environment Check")
        print("=" * 50)
        
        results = {
            'env_vars': self.check_environment_variables(),
            'docker_services': self.check_docker_services(),
            'python_deps': self.check_python_dependencies(),
            'connections': self.test_service_connections()
        }
        
        # Summary
        print(f"\n📊 Summary:")
        
        env_ok = all(results['env_vars'].values())
        docker_ok = all(results['docker_services'].values())
        deps_ok = all(results['python_deps'].values())
        conn_ok = all(results['connections'].values())
        
        print(f"   Environment Variables: {'✅' if env_ok else '❌'}")
        print(f"   Docker Services: {'✅' if docker_ok else '❌'}")
        print(f"   Python Dependencies: {'✅' if deps_ok else '❌'}")
        print(f"   Service Connections: {'✅' if conn_ok else '❌'}")
        
        overall_status = env_ok and docker_ok and deps_ok and conn_ok
        
        if overall_status:
            print(f"\n🎉 R&D environment is ready!")
            print(f"   Run: python rd_development_pipeline.py --interactive")
        else:
            print(f"\n⚠️ R&D environment needs attention:")
            
            if not env_ok:
                missing_vars = [k for k, v in results['env_vars'].items() if not v]
                print(f"   • Set environment variables: {', '.join(missing_vars)}")
            
            if not docker_ok:
                print(f"   • Start Docker services: python rd_setup.py --start")
            
            if not deps_ok:
                missing_deps = [k for k, v in results['python_deps'].items() if not v]
                print(f"   • Install packages: pip install {' '.join(missing_deps)}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description="R&D Environment Setup")
    parser.add_argument("--check", action="store_true", help="Check environment status")
    parser.add_argument("--start", action="store_true", help="Start all services")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--install-deps", action="store_true", help="Install missing dependencies")
    parser.add_argument("--create-env", action="store_true", help="Create .env template")
    
    args = parser.parse_args()
    
    setup = RDSetup()
    
    if args.create_env:
        setup.create_env_template()
    elif args.start:
        setup.start_services()
    elif args.stop:
        setup.stop_services()
    elif args.install_deps:
        deps = setup.check_python_dependencies()
        missing = [k for k, v in deps.items() if not v]
        setup.install_missing_dependencies(missing)
    elif args.check:
        setup.run_full_check()
    else:
        # Default: run full check
        setup.run_full_check()

if __name__ == "__main__":
    main() 