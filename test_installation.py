#!/usr/bin/env python3
"""
Test script to verify jean-memory-v2 installation works correctly
Run this after installing via pip install git+https://github.com/jonathan-politzki/jean-memory-v2.git
"""

def test_basic_imports():
    """Test that all major imports work"""
    print("🧪 Testing basic imports...")
    
    try:
        # Core imports
        from jean_memory_v2 import JeanMemoryV2, JeanMemoryConfig
        print("✅ Core classes imported successfully")
        
        # API imports
        from jean_memory_v2 import JeanMemoryAPI, add_memory, search_memories
        print("✅ API classes imported successfully")
        
        # Models
        from jean_memory_v2 import AddMemoryRequest, SearchMemoriesRequest
        print("✅ Model classes imported successfully")
        
        # Utilities
        from jean_memory_v2 import DatabaseCleaner, SearchResult
        print("✅ Utility classes imported successfully")
        
        # Exceptions
        from jean_memory_v2 import JeanMemoryError, ConfigurationError
        print("✅ Exception classes imported successfully")
        
        print("🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_version_info():
    """Test that version information is accessible"""
    print("\n📋 Testing version information...")
    
    try:
        import jean_memory_v2
        print(f"✅ Version: {jean_memory_v2.__version__}")
        print(f"✅ Author: {jean_memory_v2.__author__}")
        return True
    except Exception as e:
        print(f"❌ Version info failed: {e}")
        return False

def test_config_creation():
    """Test basic config creation (without actual API keys)"""
    print("\n⚙️ Testing config creation...")
    
    try:
        from jean_memory_v2 import JeanMemoryConfig
        
        # Test creating config with minimal parameters
        config = JeanMemoryConfig(
            openai_api_key="test_key",
            qdrant_host="localhost",
            qdrant_port=6333,
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password"
        )
        
        print("✅ Config created successfully")
        print(f"   - OpenAI API Key: {'***' + config.openai_api_key[-4:] if len(config.openai_api_key) > 4 else 'set'}")
        print(f"   - Qdrant Host: {config.qdrant_host}")
        print(f"   - Neo4j URI: {config.neo4j_uri}")
        return True
        
    except Exception as e:
        print(f"❌ Config creation failed: {e}")
        return False

def main():
    """Run all installation tests"""
    print("🚀 Jean Memory V2 Installation Test")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_version_info,
        test_config_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Installation test PASSED! Jean Memory V2 is ready to use.")
        return True
    else:
        print("❌ Installation test FAILED! Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)