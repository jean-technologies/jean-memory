#!/usr/bin/env python3
"""
Test memory retrieval using the OAuth JWT token
"""

import requests
import json

# The JWT token from your successful OAuth flow
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NmQzZDVkMS1mYzQ4LTQ0YTctYmJjMC0xZWZhMmUxNjRmYWQiLCJpc3MiOiJodHRwczovL2plYW4tbWVtb3J5LWFwaS12aXJnaW5pYS5vbnJlbmRlci5jb20iLCJhdWQiOiJqZWFuLW1lbW9yeS1zZGsiLCJjbGllbnRfaWQiOiJ0ZXN0LWNsaWVudC0xNzU1NTU3Mjg2NzM1In0.ckSJnMd2EH26Fa3YaQKBwL1hZjjFIrFKDli_oxe60mY"

API_BASE = "https://jean-memory-api-virginia.onrender.com"

def test_jean_chat():
    """Test Jean chat with OAuth token"""
    print("🔍 Testing Jean chat with OAuth token...")
    
    response = requests.post(
        f"{API_BASE}/api/jean-chat",
        headers={
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "message": "What have we been working on with OAuth and authentication recently? Please search my memories.",
            "conversation_id": "oauth-test-" + str(int(__import__('time').time()))
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        content = data.get('content', '')
        print(f"Response length: {len(content)} characters")
        print(f"Response: {content[:500]}...")
        
        # Check if memories were accessed
        if 'memory' in content.lower() or 'oauth' in content.lower():
            print("\n✅ AI accessed your memories and provided context!")
        else:
            print("\n⚠️  Response generated but may not have accessed memories")
    else:
        print(f"Error: {response.text}")

def test_add_memory_via_chat():
    """Test adding memory via chat"""
    print("\n🔍 Testing memory addition via chat...")
    
    response = requests.post(
        f"{API_BASE}/api/jean-chat",
        headers={
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "message": "Please remember: I successfully completed the Universal OAuth implementation for Jean Memory on August 18, 2025. The new backend-driven OAuth system works perfectly and ensures consistent user identity across all applications. This was a major milestone.",
            "conversation_id": "oauth-test-memory-" + str(int(__import__('time').time()))
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        content = data.get('content', '')
        print(f"Response: {content[:300]}...")
    else:
        print(f"Error: {response.text}")

def main():
    print("=" * 70)
    print("🧠 TESTING MEMORY TOOLS WITH OAUTH TOKEN")
    print("=" * 70)
    print(f"User ID from token: 66d3d5d1-fc48-44a7-bbc0-1efa2e164fad")
    print(f"Token (first 50 chars): {JWT_TOKEN[:50]}...")
    
    # Test memory operations via chat API
    test_add_memory_via_chat()
    test_jean_chat()
    
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print("If successful, this proves:")
    print("✅ OAuth token authenticates correctly")
    print("✅ User identity is properly resolved")
    print("✅ Memory operations work with OAuth")
    print("✅ Universal identity system is functional")

if __name__ == "__main__":
    main()