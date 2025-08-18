#!/usr/bin/env python3
"""
Verify the complete OAuth implementation
"""

import requests
import time

API_BASE = "https://jean-memory-api-virginia.onrender.com"

def test_cors_fix():
    """Test if CORS is working for localhost:8888"""
    print("🔍 Testing CORS configuration...")
    
    # Test preflight request (OPTIONS)
    options_response = requests.options(
        f"{API_BASE}/v1/sdk/oauth/token",
        headers={
            "Origin": "http://localhost:8888",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    
    print(f"OPTIONS request status: {options_response.status_code}")
    print(f"CORS headers:")
    for header, value in options_response.headers.items():
        if "access-control" in header.lower():
            print(f"  {header}: {value}")
    
    # Test POST request with Origin header
    post_response = requests.post(
        f"{API_BASE}/v1/sdk/oauth/token",
        headers={
            "Origin": "http://localhost:8888",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "authorization_code",
            "code": "test",
            "redirect_uri": "http://localhost:8888/test",
            "client_id": "test",
            "code_verifier": "test"
        }
    )
    
    print(f"\nPOST request status: {post_response.status_code}")
    print(f"Response: {post_response.text}")
    print(f"CORS headers in response:")
    for header, value in post_response.headers.items():
        if "access-control" in header.lower():
            print(f"  {header}: {value}")

def test_endpoints():
    """Test OAuth endpoints availability"""
    print("\n🔍 Testing OAuth endpoints...")
    
    # Test authorize endpoint
    auth_response = requests.get(
        f"{API_BASE}/v1/sdk/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": "test",
            "redirect_uri": "http://localhost:8888/test",
            "state": "test",
            "code_challenge": "test",
            "code_challenge_method": "S256"
        },
        allow_redirects=False
    )
    
    print(f"Authorize endpoint status: {auth_response.status_code}")
    if auth_response.status_code == 307:
        redirect_to = auth_response.headers.get('location', 'No location header')
        print(f"  Redirects to: {redirect_to[:100]}...")
        if "accounts.google.com" in redirect_to:
            print("  ✅ Correctly redirects to Google OAuth")
        else:
            print("  ❌ Unexpected redirect target")

def main():
    print("=" * 60)
    print("🔧 OAUTH IMPLEMENTATION VERIFICATION")
    print("=" * 60)
    
    # Test endpoints first
    test_endpoints()
    
    # Test CORS
    test_cors_fix()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("\nIf CORS is working, you should see:")
    print("✅ access-control-allow-origin: http://localhost:8888")
    print("✅ access-control-allow-methods includes POST")
    print("\nThen retry the test at: http://localhost:8888/test_oauth_flow.html")

if __name__ == "__main__":
    main()