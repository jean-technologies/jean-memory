#!/usr/bin/env python3
"""
Analyze all imports used in jean_memory module to ensure dependencies are covered
"""

import os
import re
from collections import defaultdict

def extract_imports_from_file(filepath):
    """Extract all import statements from a Python file"""
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all import statements
        import_patterns = [
            r'^import\s+([^\s#]+)',
            r'^from\s+([^\s#]+)\s+import',
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1).split('.')[0]  # Get top-level module
                    if not module.startswith('.') and module != '__future__':
                        imports.add(module)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return imports

def get_all_imports():
    """Get all imports from jean_memory module"""
    jean_memory_dir = "jean_memory"
    all_imports = set()
    
    for root, dirs, files in os.walk(jean_memory_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                imports = extract_imports_from_file(filepath)
                all_imports.update(imports)
    
    return all_imports

def is_stdlib_module(module_name):
    """Check if a module is part of Python standard library"""
    stdlib_modules = {
        'os', 'sys', 'json', 'time', 'datetime', 'logging', 'asyncio', 'pathlib',
        'typing', 'collections', 'functools', 'itertools', 'uuid', 'hashlib',
        'random', 'string', 're', 'math', 'statistics', 'decimal', 'fractions',
        'pickle', 'copy', 'weakref', 'gc', 'traceback', 'warnings', 'contextlib',
        'abc', 'inspect', 'importlib', 'pkgutil', 'zipfile', 'tempfile', 'shutil',
        'glob', 'fnmatch', 'csv', 'base64', 'binascii', 'struct', 'socket',
        'ssl', 'urllib', 'http', 'email', 'mimetypes', 'encodings', 'codecs',
        'locale', 'gettext', 'argparse', 'configparser', 'subprocess', 'threading',
        'multiprocessing', 'concurrent', 'queue', 'sched', 'signal', 'operator',
        'keyword', 'heapq', 'bisect', 'array', 'enum', 'types', 'numbers',
        'io', 'sqlite3', 'zlib', 'gzip', 'bz2', 'lzma', 'tarfile', 'zipimport',
        'platform', 'ctypes', 'distutils', 'venv', 'ensurepip'
    }
    return module_name in stdlib_modules

def main():
    print("=== Jean Memory Import Analysis ===\n")
    
    all_imports = get_all_imports()
    
    # Separate standard library from third-party
    stdlib_imports = {mod for mod in all_imports if is_stdlib_module(mod)}
    third_party_imports = all_imports - stdlib_imports
    
    print("📦 Third-party packages used in jean_memory:")
    for module in sorted(third_party_imports):
        print(f"   {module}")
    
    print(f"\n📚 Standard library modules: {len(stdlib_imports)}")
    print(f"📦 Third-party packages: {len(third_party_imports)}")
    
    # Check which third-party packages might not be in requirements
    current_deps = []
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                pkg_name = line.split('>=')[0].split('==')[0].split('[')[0].strip()
                current_deps.append(pkg_name)
    
    # Map common import names to package names
    import_to_package = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'sqlalchemy': 'sqlalchemy',
        'dotenv': 'python-dotenv',
        'alembic': 'alembic',
        'psycopg2': 'psycopg2-binary',
        'multipart': 'python-multipart',
        'setuptools': 'setuptools',
        'fastapi_pagination': 'fastapi-pagination',
        'mem0': 'mem0ai',
        'aiohttp': 'aiohttp',
        'pytest': 'pytest',
        'pytest_asyncio': 'pytest-asyncio',
        'httpx': 'httpx',
        'pytest_cov': 'pytest-cov',
        'tenacity': 'tenacity',
        'supabase': 'supabase',
        'feedparser': 'feedparser',
        'dateutil': 'python-dateutil',
        'google': 'google-generativeai',
        'bs4': 'beautifulsoup4',
        'psutil': 'psutil',
        'starlette': 'starlette',
        'sse_starlette': 'sse-starlette',
        'posthog': 'posthog',
        'email_validator': 'email-validator',
        'stripe': 'stripe',
        'twilio': 'twilio',
        'anthropic': 'anthropic',
        'redis': 'redis',
        'neo4j': 'neo4j',
        'pgvector': 'pgvector',
        'graphiti_core': 'graphiti-core',
        'openai': 'openai',
        'qdrant_client': 'qdrant-client',
        'numpy': 'numpy',
        'pydantic': 'pydantic',  # Comes with fastapi
        'mcp': 'mcp',
    }
    
    potentially_missing = []
    for import_name in third_party_imports:
        package_name = import_to_package.get(import_name, import_name)
        if package_name not in current_deps and import_name not in ['app', 'jean_memory']:
            potentially_missing.append(import_name)
    
    if potentially_missing:
        print(f"\n⚠️  Potentially missing packages:")
        for module in sorted(potentially_missing):
            print(f"   {module}")
    else:
        print(f"\n✅ All third-party imports appear to be covered by requirements.txt")
    
    return len(potentially_missing) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)