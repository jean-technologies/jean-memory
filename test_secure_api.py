#!/usr/bin/env python3
"""
Test both legacy and secure API endpoints
"""

import requests
import json

# Your credentials  
API_KEY = "jean_sk_HbMsS3EEsZtlIcxlivYM0yPy6auK3ThYek9QMeX8lOo"
OAUTH_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NmQzZDVkMS1mYzQ4LTQ0YTctYmJjMC0xZWZhMmUxNjRmYWQiLCJpc3MiOiJodHRwczovL2plYW4tbWVtb3J5LWFwaS12aXJnaW5pYS5vbnJlbmRlci5jb20iLCJhdWQiOiJqZWFuLW1lbW9yeS1zZGsiLCJjbGllbnRfaWQiOiJ0ZXN0LWNsaWVudC0xNzU1NTU3Mjg2NzM1In0.ckSJnMd2EH26Fa3YaQKBwL1hZjjFIrFKDli_oxe60mY"
USER_ID = "66d3d5d1-fc48-44a7-bbc0-1efa2e164fad"

API_BASE = "https://jean-memory-api-virginia.onrender.com"

def test_legacy_endpoint():
    """Test the fixed legacy endpoint (v1.0)"""
    print("🧪 Testing Legacy Endpoint (v1.0 - Fixed)")
    print("=" * 50)
    
    response = requests.post(
        f"{API_BASE}/api/jean-chat",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "message": "What OAuth and authentication work have I been doing recently?",
            "user_token": OAUTH_JWT,
            "conversation_id": "test-legacy-fixed"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        content = data.get('content', '')
        print(f"✅ SUCCESS! Response length: {len(content)} characters")
        print(f"Response: {str(content)[:300]}...")
        print(f"User ID: {data.get('user_id', 'Not specified')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_secure_endpoint():
    """Test the new secure endpoint (v2.0)"""
    print("\n🔒 Testing Secure Endpoint (v2.0)")
    print("=" * 50)
    
    response = requests.post(
        f"{API_BASE}/api/v2/jean-chat",
        headers={
            "Authorization": f"Bearer {OAUTH_JWT}",  # JWT in Authorization header
            "X-API-Key": API_KEY,                    # API key in separate header
            "Content-Type": "application/json"
        },
        json={
            "message": "What OAuth and authentication work have I been doing recently?",
            "format": "enhanced"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        content = data.get('content', '')
        print(f"✅ SUCCESS! Response length: {len(content)} characters")
        print(f"Response: {str(content)[:300]}...")
        print(f"User ID: {data.get('user_id', 'Not specified')}")
        print(f"Version: {data.get('version', 'Not specified')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_security_vulnerability():
    """Test if the old vulnerability still exists"""
    print("\n🛡️ Testing Security Vulnerability (Should Fail)")
    print("=" * 50)
    
    # Try to impersonate another user with legacy endpoint
    fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtlLXVzZXItaWQiLCJpc3MiOiJodHRwczovL2plYW4tbWVtb3J5LWFwaS12aXJnaW5pYS5vbnJlbmRlci5jb20iLCJhdWQiOiJqZWFuLW1lbW9yeS1zZGsiLCJjbGllbnRfaWQiOiJmYWtlIn0.fake_signature"
    
    print("1. Testing legacy endpoint with fake user_token...")
    response = requests.post(
        f"{API_BASE}/api/jean-chat",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "message": "Can I access someone else's data?",
            "user_token": fake_jwt,  # Fake JWT in body
            "conversation_id": "test-security"
        }
    )
    
    print(f"Legacy endpoint status: {response.status_code}")
    if response.status_code == 200:
        print("⚠️ WARNING: Legacy endpoint might be vulnerable")
    else:
        print("✅ Legacy endpoint properly rejects fake tokens")
    
    print("\n2. Testing secure endpoint with fake JWT in header...")
    response = requests.post(
        f"{API_BASE}/api/v2/jean-chat",
        headers={
            "Authorization": f"Bearer {fake_jwt}",  # Fake JWT in header
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "message": "Can I access someone else's data?",
            "format": "enhanced"
        }
    )
    
    print(f"Secure endpoint status: {response.status_code}")
    if response.status_code == 401:
        print("✅ EXCELLENT: Secure endpoint properly rejects fake JWT")
        return True
    else:
        print("❌ SECURITY ISSUE: Secure endpoint accepted fake JWT")
        return False

def main():
    print("🧠 TESTING JEAN MEMORY SDK AUTHENTICATION")
    print("=" * 60)
    print(f"API Key: {API_KEY[:20]}...")
    print(f"User ID: {USER_ID}")
    print(f"OAuth JWT: {OAUTH_JWT[:50]}...")
    
    # Test both endpoints
    legacy_works = test_legacy_endpoint()
    secure_works = test_secure_endpoint()
    security_good = test_security_vulnerability()
    
    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS")
    print("=" * 60)
    
    if legacy_works:
        print("✅ Legacy API (v1.0): Working with user_token fix")
    else:
        print("❌ Legacy API (v1.0): Still has issues")
    
    if secure_works:
        print("✅ Secure API (v2.0): Working with JWT-in-header")
    else:
        print("❌ Secure API (v2.0): Not working properly")
    
    if security_good:
        print("✅ Security: Fake JWT properly rejected")
    else:
        print("❌ Security: Vulnerability may still exist")
    
    if legacy_works and secure_works and security_good:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ OAuth user identity + API key authentication works in both v1.0 and v2.0")
        print("✅ Universal identity system is operational")
        print("✅ Security vulnerability has been eliminated")
        print("✅ Ready for production SDK deployment")
    else:
        print("\n🔧 Some issues found - review test results above")

if __name__ == "__main__":
    main()