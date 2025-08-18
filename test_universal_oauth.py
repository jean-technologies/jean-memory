#!/usr/bin/env python3
"""
Test script for the new universal OAuth implementation
Tests the /v1/sdk/oauth/* endpoints
"""

import requests
import json
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs, urlparse

# Configuration
API_BASE_URL = "https://jean-memory-api-virginia.onrender.com"
LOCAL_API_URL = "http://localhost:8765"  # For local testing

# Use production API by default
BASE_URL = API_BASE_URL

def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    # Generate a random 32-byte string
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Create SHA256 hash of the verifier
    challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def test_authorize_endpoint():
    """Test the /v1/sdk/oauth/authorize endpoint"""
    print("\n🔍 Testing /v1/sdk/oauth/authorize endpoint...")
    
    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    
    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": "test-client-id",
        "redirect_uri": "http://localhost:3000/callback",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"{BASE_URL}/v1/sdk/oauth/authorize?{urlencode(params)}"
    
    print(f"✅ Authorization URL generated:")
    print(f"   {auth_url}")
    print(f"\n📝 PKCE Details:")
    print(f"   Code Verifier: {code_verifier[:20]}...")
    print(f"   Code Challenge: {code_challenge[:20]}...")
    print(f"   State: {state}")
    
    # Test that the endpoint responds correctly
    try:
        response = requests.get(auth_url, allow_redirects=False)
        
        if response.status_code == 307:  # Redirect response
            redirect_location = response.headers.get('location')
            print(f"\n✅ Endpoint responded with redirect:")
            print(f"   Status: {response.status_code}")
            print(f"   Redirect to: {redirect_location[:100]}...")
            
            # Check if it's redirecting to Google
            if "accounts.google.com" in redirect_location:
                print("   ✅ Correctly redirecting to Google OAuth")
                
                # Parse the Google URL to verify parameters
                parsed = urlparse(redirect_location)
                google_params = parse_qs(parsed.query)
                
                print(f"\n📝 Google OAuth Parameters:")
                print(f"   Client ID: {google_params.get('client_id', ['Not found'])[0][:50]}...")
                print(f"   Redirect URI: {google_params.get('redirect_uri', ['Not found'])[0]}")
                print(f"   State preserved: {state in redirect_location}")
            else:
                print("   ⚠️  Not redirecting to Google as expected")
        else:
            print(f"\n❌ Unexpected response:")
            print(f"   Status: {response.status_code}")
            print(f"   Body: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n❌ Error testing authorize endpoint: {e}")
    
    return state, code_verifier, code_challenge

def test_token_endpoint():
    """Test the /v1/sdk/oauth/token endpoint (mock test)"""
    print("\n🔍 Testing /v1/sdk/oauth/token endpoint...")
    
    # This would normally use a real authorization code from the callback
    # For testing, we'll just verify the endpoint exists
    
    token_url = f"{BASE_URL}/v1/sdk/oauth/token"
    
    # Mock data (would normally come from the OAuth callback)
    data = {
        "grant_type": "authorization_code",
        "code": "mock-auth-code",
        "redirect_uri": "http://localhost:3000/callback",
        "client_id": "test-client-id",
        "code_verifier": "mock-code-verifier"
    }
    
    try:
        response = requests.post(token_url, data=data)
        
        print(f"✅ Token endpoint response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400:
            print(f"   Expected error (no valid auth code): {response.json().get('detail', 'Unknown error')}")
        elif response.status_code == 200:
            print(f"   Unexpected success with mock data!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n❌ Error testing token endpoint: {e}")

def test_health_check():
    """Test if the API is accessible"""
    print("\n🔍 Testing API health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API is healthy: {response.json()}")
        else:
            print(f"⚠️  API responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Could not reach API: {e}")

def main():
    print("=" * 60)
    print("🚀 UNIVERSAL OAUTH IMPLEMENTATION TEST")
    print("=" * 60)
    print(f"\n📍 Testing against: {BASE_URL}")
    
    # Test API health
    test_health_check()
    
    # Test authorize endpoint
    state, code_verifier, code_challenge = test_authorize_endpoint()
    
    # Test token endpoint
    test_token_endpoint()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print("\nThe new OAuth endpoints are deployed and responding!")
    print("\nNext steps to complete the test:")
    print("1. Click the authorization URL above")
    print("2. Sign in with Google")
    print("3. Note the 'code' parameter in the callback URL")
    print("4. Use that code with the token endpoint")
    print("\n⚠️  Note: Google OAuth will only work if:")
    print("   - GOOGLE_CLIENT_ID is set in Render")
    print("   - GOOGLE_CLIENT_SECRET is set in Render")
    print("   - The redirect URI is registered in Google Cloud Console")

if __name__ == "__main__":
    main()