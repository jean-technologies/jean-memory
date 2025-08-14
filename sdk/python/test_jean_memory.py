#!/usr/bin/env python3
"""
Basic test for Jean Memory Python SDK
Run with: python test_jean_memory.py
"""

import sys
import os

# Add the package to Python path for testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jean_memory import JeanMemoryClient, JeanMemoryError


def test_sdk():
    """Test Jean Memory Python SDK functionality"""
    print("🧪 Testing Jean Memory Python SDK...\n")

    # Test 1: Client initialization
    print("1. Testing client initialization...")
    
    try:
        # Should fail without API key
        JeanMemoryClient("")
        print("❌ Should have failed without API key")
    except ValueError:
        print("✅ Correctly rejected empty API key")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        # Should fail with invalid API key format
        JeanMemoryClient("invalid-key")
        print("❌ Should have failed with invalid API key format")
    except ValueError:
        print("✅ Correctly rejected invalid API key format")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        # Should succeed with valid format
        client = JeanMemoryClient("jean_sk_test123")
        print("✅ Client initialization successful")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")

    # Test 2: Method validation
    print("\n2. Testing method validation...")
    
    client = JeanMemoryClient("jean_sk_test123", api_base="https://httpbin.org")

    try:
        client.store_memory("")
        print("❌ Should have failed with empty content")
    except ValueError:
        print("✅ Correctly rejected empty memory content")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        client.store_memory("   ")
        print("❌ Should have failed with whitespace-only content")
    except ValueError:
        print("✅ Correctly rejected whitespace-only content")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        client.retrieve_memories("")
        print("❌ Should have failed with empty query")
    except ValueError:
        print("✅ Correctly rejected empty search query")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        client.retrieve_memories("test", limit=0)
        print("❌ Should have failed with invalid limit")
    except ValueError:
        print("✅ Correctly rejected invalid limit")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        client.retrieve_memories("test", limit=101)
        print("❌ Should have failed with limit too high")
    except ValueError:
        print("✅ Correctly rejected limit too high")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        client.list_memories(offset=-1)
        print("❌ Should have failed with negative offset")
    except ValueError:
        print("✅ Correctly rejected negative offset")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        client.get_context("")
        print("❌ Should have failed with empty context query")
    except ValueError:
        print("✅ Correctly rejected empty context query")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    try:
        client.delete_memory("")
        print("❌ Should have failed with empty memory ID")
    except ValueError:
        print("✅ Correctly rejected empty memory ID")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 3: Context generation for empty results
    print("\n3. Testing context generation...")
    
    try:
        # Mock client with no memories
        class MockClient(JeanMemoryClient):
            def retrieve_memories(self, query, limit=10):
                return []
        
        mock_client = MockClient("jean_sk_test123")
        context = mock_client.get_context("test query")
        
        if context == "No relevant context found.":
            print("✅ Context generation for empty results works")
        else:
            print(f"❌ Unexpected context result: {context}")
    except Exception as e:
        print(f"❌ Context generation failed: {e}")

    # Test 4: Session and headers
    print("\n4. Testing session setup...")
    
    try:
        client = JeanMemoryClient("jean_sk_test123")
        
        # Check session headers
        expected_headers = {
            'Authorization': 'Bearer jean_sk_test123',
            'Content-Type': 'application/json',
            'User-Agent': 'JeanMemory-Python-SDK/1.0.1'
        }
        
        for key, value in expected_headers.items():
            if client.session.headers.get(key) == value:
                print(f"✅ Header {key} correctly set")
            else:
                print(f"❌ Header {key} incorrect: {client.session.headers.get(key)}")
                
    except Exception as e:
        print(f"❌ Session setup failed: {e}")

    print("\n🎉 SDK tests completed!")


if __name__ == "__main__":
    test_sdk()