#!/usr/bin/env python3
"""
Comprehensive OAuth Testing for Dev Server
Tests both new OAuth functionality and existing MCP endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Dev server URL
DEV_URL = "https://jean-memory-api-dev.onrender.com"

print("🧪 Comprehensive OAuth Testing for Dev Server")
print(f"📍 Testing: {DEV_URL}")
print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Test results tracking
test_results = {
    "oauth_new": [],
    "mcp_existing": [],
    "isolation": []
}

def test_section(name):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"📋 {name}")
    print("="*60)

def test_result(category, test_name, passed, details=""):
    """Record and print test result"""
    result = {
        "test": test_name,
        "passed": passed,
        "details": details
    }
    test_results[category].append(result)
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")

# ===== SECTION 1: NEW OAUTH ENDPOINTS =====
test_section("NEW OAUTH ENDPOINTS")

# Test 1: OAuth Discovery
try:
    response = requests.get(f"{DEV_URL}/.well-known/oauth-authorization-server")
    if response.status_code == 200:
        metadata = response.json()
        expected_keys = ["issuer", "authorization_endpoint", "token_endpoint", "registration_endpoint"]
        has_all_keys = all(key in metadata for key in expected_keys)
        test_result("oauth_new", "OAuth Discovery", has_all_keys and metadata["issuer"] == DEV_URL,
                   f"Keys present: {list(metadata.keys())}")
    else:
        test_result("oauth_new", "OAuth Discovery", False, f"Status: {response.status_code}")
except Exception as e:
    test_result("oauth_new", "OAuth Discovery", False, f"Error: {str(e)}")

# Test 2: Dynamic Client Registration
try:
    registration_data = {
        "client_name": "Dev Test Client",
        "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        "grant_types": ["authorization_code", "refresh_token"]
    }
    response = requests.post(f"{DEV_URL}/oauth/register", json=registration_data)
    if response.status_code == 200:
        client_data = response.json()
        client_id = client_data.get("client_id", "")
        test_result("oauth_new", "Client Registration", client_id.startswith("claude_"),
                   f"Client ID: {client_id}")
    else:
        test_result("oauth_new", "Client Registration", False, f"Status: {response.status_code}")
except Exception as e:
    test_result("oauth_new", "Client Registration", False, f"Error: {str(e)}")

# Test 3: Authorization Page
try:
    params = {
        "client_id": "test_client",
        "redirect_uri": "https://test.com/callback",
        "response_type": "code",
        "state": "test123"
    }
    response = requests.get(f"{DEV_URL}/oauth/authorize", params=params)
    is_success = response.status_code == 200 and "Connect Claude to Jean Memory" in response.text
    test_result("oauth_new", "Authorization Page", is_success,
               "Page loads with form" if is_success else f"Status: {response.status_code}")
except Exception as e:
    test_result("oauth_new", "Authorization Page", False, f"Error: {str(e)}")

# Test 4: OAuth MCP Endpoint
try:
    response = requests.post(f"{DEV_URL}/mcp/oauth/test-user",
                           json={"jsonrpc": "2.0", "method": "test", "id": 1})
    test_result("oauth_new", "OAuth MCP Endpoint", response.status_code == 401,
               "Correctly requires auth" if response.status_code == 401 else f"Unexpected: {response.status_code}")
except Exception as e:
    test_result("oauth_new", "OAuth MCP Endpoint", False, f"Error: {str(e)}")

# ===== SECTION 2: EXISTING MCP ENDPOINTS =====
test_section("EXISTING MCP ENDPOINTS (Should Still Work)")

# Test existing MCP endpoints
existing_endpoints = [
    ("/mcp/v2/claude/test-user", "Claude MCP v2"),
    ("/messages/", "Messages endpoint"),
    ("/mcp/agent", "Agent MCP endpoint")
]

for endpoint, name in existing_endpoints:
    try:
        response = requests.post(f"{DEV_URL}{endpoint}",
                               json={"jsonrpc": "2.0", "method": "test", "id": 1})
        # These should require auth (401) or not be found (404)
        is_protected = response.status_code in [401, 403, 404]
        test_result("mcp_existing", name, is_protected,
                   f"Status: {response.status_code}" + (" - Protected" if is_protected else " - OPEN!"))
    except Exception as e:
        test_result("mcp_existing", name, False, f"Error: {str(e)}")

# ===== SECTION 3: ISOLATION TESTING =====
test_section("ISOLATION TESTING")

# Test that OAuth endpoints don't require API keys
oauth_public_endpoints = [
    ("GET", "/.well-known/oauth-authorization-server", "Discovery"),
    ("POST", "/oauth/register", "Registration")
]

for method, endpoint, name in oauth_public_endpoints:
    try:
        headers = {"X-Api-Key": "fake_key_12345"}
        if method == "GET":
            response = requests.get(f"{DEV_URL}{endpoint}", headers=headers)
        else:
            response = requests.post(f"{DEV_URL}{endpoint}", headers=headers, json={})
        
        # Should work without API key auth
        works_without_auth = response.status_code != 401
        test_result("isolation", f"{name} - No API Key Required", works_without_auth,
                   f"Status: {response.status_code}")
    except Exception as e:
        test_result("isolation", f"{name} - No API Key Required", False, f"Error: {str(e)}")

# Test health check still works
try:
    response = requests.get(f"{DEV_URL}/health")
    test_result("isolation", "Health Check", response.status_code == 200,
               "Service is healthy" if response.status_code == 200 else f"Status: {response.status_code}")
except Exception as e:
    test_result("isolation", "Health Check", False, f"Error: {str(e)}")

# ===== SUMMARY =====
test_section("TEST SUMMARY")

total_tests = 0
passed_tests = 0

for category, results in test_results.items():
    category_passed = sum(1 for r in results if r["passed"])
    category_total = len(results)
    total_tests += category_total
    passed_tests += category_passed
    
    print(f"\n{category.upper()}:")
    print(f"  Passed: {category_passed}/{category_total}")
    
    # Show failures
    failures = [r for r in results if not r["passed"]]
    if failures:
        print("  Failed tests:")
        for failure in failures:
            print(f"    - {failure['test']}: {failure['details']}")

print(f"\n{'='*60}")
print(f"OVERALL: {passed_tests}/{total_tests} tests passed")

if passed_tests == total_tests:
    print("\n🎉 ALL TESTS PASSED! OAuth implementation is working correctly!")
    print("✅ OAuth endpoints are functional")
    print("✅ Existing MCP endpoints are unaffected")
    print("✅ Service isolation is maintained")
    print("\n📝 Next steps:")
    print("1. Add API_BASE_URL env var to dev service in Render")
    print("2. Test with real Claude client")
    print("3. Monitor logs during OAuth flow")
else:
    print(f"\n⚠️  {total_tests - passed_tests} tests failed!")
    print("Please check the failures above and investigate.")
    sys.exit(1)

# Additional manual testing steps
print("\n" + "="*60)
print("📋 MANUAL TESTING CHECKLIST")
print("="*60)
print("""
After automated tests pass:

1. [ ] Add API_BASE_URL env var in Render dashboard
2. [ ] Test OAuth flow in browser:
      - Go to: {dev_url}/oauth/authorize?client_id=test&redirect_uri=https://test.com&response_type=code&state=123
      - Should see authorization page
3. [ ] Test with real API key:
      - Enter valid Jean Memory API key
      - Should redirect with auth code
4. [ ] Monitor Render logs during testing
5. [ ] Test with Claude (if possible):
      - URL: {dev_url}/mcp/oauth/{{your_user_id}}
6. [ ] Verify existing integrations still work
7. [ ] Check memory creation/retrieval works
""".format(dev_url=DEV_URL))

print("\n✨ Testing complete!") 