#!/usr/bin/env python3
"""
Minimal test to isolate the User object issue
"""

import requests
import json

API_KEY = "jean_sk_HbMsS3EEsZtlIcxlivYM0yPy6auK3ThYek9QMeX8lOo"
API_BASE = "https://jean-memory-api-virginia.onrender.com"

def test_api_key_only():
    """Test with just API key (should work)"""
    print("🧪 Testing API key only...")
    
    response = requests.post(
        f"{API_BASE}/api/jean-chat",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "message": "Hello test"
            # No user_token - should use API key user
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API key only works! User ID: {data.get('user_id')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_with_user_token():
    """Test with user_token (currently failing)"""
    print("\n🧪 Testing with user_token...")
    
    OAUTH_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NmQzZDVkMS1mYzQ4LTQ0YTctYmJjMC0xZWZhMmUxNjRmYWQiLCJpc3MiOiJodHRwczovL2plYW4tbWVtb3J5LWFwaS12aXJnaW5pYS5vbnJlbmRlci5jb20iLCJhdWQiOiJqZWFuLW1lbW9yeS1zZGsiLCJjbGllbnRfaWQiOiJ0ZXN0LWNsaWVudC0xNzU1NTU3Mjg2NzM1In0.ckSJnMd2EH26Fa3YaQKBwL1hZjjFIrFKDli_oxe60mY"
    
    response = requests.post(
        f"{API_BASE}/api/jean-chat",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "message": "Hello test",
            "user_token": OAUTH_JWT
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User token works! User ID: {data.get('user_id')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    print("🔍 MINIMAL API TEST")
    print("=" * 40)
    
    api_only = test_api_key_only()
    user_token = test_with_user_token()
    
    print("\n📋 RESULTS:")
    print(f"API key only: {'✅' if api_only else '❌'}")
    print(f"With user_token: {'✅' if user_token else '❌'}")
    
    if api_only and not user_token:
        print("\n🔍 The issue is specifically with user_token parsing")
    elif not api_only:
        print("\n🔍 The issue is more fundamental with the endpoint")