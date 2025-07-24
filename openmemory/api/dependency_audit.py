#!/usr/bin/env python3
"""
Dependency audit to ensure all jean-memory dependencies are present
"""

# Dependencies from jean-memory setup.py
JEAN_MEMORY_DEPS = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0", 
    "sqlalchemy>=2.0.36",
    "python-dotenv>=1.0.0",
    "alembic>=1.14.0",
    "psycopg2-binary>=2.9.10",
    "python-multipart>=0.0.12",
    "setuptools>=75.0.0",
    "fastapi-pagination>=0.12.30",
    "mem0ai[graph]>=0.1.107",
    "aiohttp>=3.11.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.25.0",
    "httpx>=0.28.0",
    "pytest-cov>=6.0.0",
    "tenacity>=9.1.2",
    "supabase>=2.5.0,<3.0.0",
    "feedparser>=6.0.11",
    "python-dateutil>=2.9.0",
    "google-generativeai>=0.8.0",
    "beautifulsoup4>=4.12.3",
    "psutil>=6.1.0",
    "starlette>=0.40.0",
    "sse-starlette>=2.1.3",
    "posthog>=3.8.0",
    "email-validator>=2.2.0",
    "stripe>=12.2.0",
    "twilio>=9.6.5",
    "anthropic>=0.40.0",
    "redis>=5.2.0",
    "neo4j>=5.28.0",
    "pgvector>=0.3.6",
    "graphiti-core>=0.13.0",
    "openai>=1.58.0",
    "qdrant-client>=1.12.0",
    "numpy>=1.24.0",  # This was missing!
]

def parse_requirements():
    """Parse current requirements.txt"""
    with open('requirements.txt', 'r') as f:
        lines = f.readlines()
    
    current_deps = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            current_deps.append(line)
    
    return current_deps

def normalize_package_name(dep):
    """Extract package name from dependency string"""
    if '>=' in dep:
        return dep.split('>=')[0].strip()
    elif '==' in dep:
        return dep.split('==')[0].strip()
    elif '[' in dep:
        return dep.split('[')[0].strip()
    return dep.strip()

def main():
    print("=== Jean Memory Dependency Audit ===\n")
    
    current_deps = parse_requirements()
    current_packages = {normalize_package_name(dep) for dep in current_deps}
    jean_memory_packages = {normalize_package_name(dep) for dep in JEAN_MEMORY_DEPS}
    
    missing = jean_memory_packages - current_packages
    extra = current_packages - jean_memory_packages
    
    if missing:
        print("❌ MISSING DEPENDENCIES (required by jean_memory):")
        for dep in sorted(missing):
            # Find the full requirement from jean-memory
            for full_dep in JEAN_MEMORY_DEPS:
                if normalize_package_name(full_dep) == dep:
                    print(f"   {full_dep}")
                    break
        print()
    
    if extra:
        print("ℹ️  EXTRA DEPENDENCIES (not in jean-memory, but needed by jean-memory-app):")
        for dep in sorted(extra):
            # Find the full requirement from current requirements
            for full_dep in current_deps:
                if normalize_package_name(full_dep) == dep:
                    print(f"   {full_dep}")
                    break
        print()
    
    if not missing:
        print("✅ All jean-memory dependencies are present!")
    else:
        print(f"❌ {len(missing)} dependencies missing - PRODUCTION DEPLOYMENT WILL FAIL")
        
        print("\n=== REQUIRED ACTION ===")
        print("Add these lines to requirements.txt:")
        for dep in sorted(missing):
            for full_dep in JEAN_MEMORY_DEPS:
                if normalize_package_name(full_dep) == dep:
                    print(f"{full_dep}")
                    break
    
    return len(missing) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)