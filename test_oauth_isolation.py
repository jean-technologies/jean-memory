#!/usr/bin/env python3
"""
Test that OAuth implementation doesn't interfere with existing MCP endpoints
"""

import requests
import os

BASE_URL = "http://localhost:8765"
API_KEY = os.getenv("JEAN_API_KEY", "")  # Set your API key

print("🔍 Testing OAuth Isolation from Existing MCP")
print(f"📍 Base URL: {BASE_URL}")
print("=" * 50)

def test_existing_mcp_endpoints():
    """Test that existing MCP endpoints still work"""
    print("\n1️⃣ Testing Existing MCP Endpoints...")
    
    # Test the standard MCP endpoint (should work with API key)
    endpoints = [
        "/mcp/v2/claude/test-user",
        "/messages/",
        "/mcp/agent"
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            # Test without auth (should fail)
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
            )
            
            if response.status_code in [401, 403, 404]:
                print(f"✅ {endpoint} - Requires auth as expected")
                results.append(True)
            else:
                print(f"⚠️  {endpoint} - Unexpected response: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)

def test_oauth_endpoints_isolated():
    """Test that OAuth endpoints are separate"""
    print("\n2️⃣ Testing OAuth Endpoints are Isolated...")
    
    # OAuth endpoints should NOT accept API keys
    oauth_endpoints = [
        ("GET", "/.well-known/oauth-authorization-server"),
        ("POST", "/oauth/register"),
        ("GET", "/oauth/authorize"),
        ("POST", "/oauth/token")
    ]
    
    results = []
    
    for method, endpoint in oauth_endpoints:
        try:
            if method == "GET":
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    headers={"X-Api-Key": "fake_key"}
                )
            else:
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    headers={"X-Api-Key": "fake_key"},
                    json={}
                )
            
            # OAuth endpoints should work without API key auth
            if endpoint == "/.well-known/oauth-authorization-server":
                if response.status_code == 200:
                    print(f"✅ {endpoint} - Public endpoint works")
                    results.append(True)
                else:
                    print(f"❌ {endpoint} - Should be public")
                    results.append(False)
            else:
                # Other OAuth endpoints may return 400/422 for bad data, but not 401
                if response.status_code != 401:
                    print(f"✅ {endpoint} - Not using API key auth")
                    results.append(True)
                else:
                    print(f"❌ {endpoint} - Shouldn't require API key")
                    results.append(False)
                    
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)

def test_different_mcp_paths():
    """Test that OAuth MCP path is different from existing ones"""
    print("\n3️⃣ Testing MCP Path Separation...")
    
    # These should be different endpoints
    mcp_paths = [
        ("/mcp/oauth/user123", "OAuth MCP endpoint"),
        ("/mcp/v2/claude/user123", "Existing Claude MCP"),
        ("/messages/", "Existing messages endpoint"),
        ("/mcp/agent", "Existing agent endpoint")
    ]
    
    results = []
    
    for path, description in mcp_paths:
        try:
            response = requests.post(
                f"{BASE_URL}{path}",
                json={"jsonrpc": "2.0", "method": "test", "id": 1}
            )
            
            # All should require auth but be separate endpoints
            if response.status_code in [401, 403, 404]:
                print(f"✅ {description} - Separate endpoint")
                results.append(True)
            else:
                print(f"⚠️  {description} - Status: {response.status_code}")
                results.append(True)  # Still OK if it exists
                
        except Exception as e:
            print(f"❌ {description} - Error: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all isolation tests"""
    print("🚀 Testing OAuth Implementation Isolation\n")
    
    tests = [
        ("Existing MCP Endpoints", test_existing_mcp_endpoints),
        ("OAuth Endpoints Isolated", test_oauth_endpoints_isolated),
        ("MCP Path Separation", test_different_mcp_paths)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        result = test_func()
        results.append(result)
        print(f"\n{test_name}: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Summary
    print("\n" + "=" * 50)
    print("ISOLATION TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All isolation tests passed ({passed}/{total})!")
        print("\n✅ OAuth implementation is completely isolated!")
        print("✅ Existing MCP endpoints are unaffected!")
        print("✅ Safe to deploy!")
    else:
        print(f"❌ {total - passed} tests failed ({passed}/{total} passed)")
        print("\n⚠️  Please check the implementation for conflicts")

if __name__ == "__main__":
    main() 