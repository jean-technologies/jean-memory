#!/usr/bin/env python3
"""Test script to diagnose SDK authentication issue"""

import requests
import json

API_BASE = "https://jean-memory-api-virginia.onrender.com"
API_KEY = "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"

def test_auth_with_invalid_creds():
    """Test auth endpoint with invalid credentials to see error details"""
    print("\n=== Testing /sdk/auth/login with invalid credentials ===")
    
    url = f"{API_BASE}/sdk/auth/login"
    payload = {
        "email": "test@example.com",
        "password": "wrongpassword123"
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")

def test_direct_mcp_endpoint():
    """Test if we can access the MCP endpoint directly"""
    print("\n=== Testing direct MCP endpoint ===")
    
    url = f"{API_BASE}/mcp/messages/"
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
    }
    
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"URL: {url}")
    print(f"Headers: {json.dumps({k:v[:20]+'...' if len(v)>20 else v for k,v in headers.items()}, indent=2)}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"\nStatus Code: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response (truncated): {str(data)[:200]}...")
    except:
        print(f"Response Text: {response.text[:200]}...")

def test_sdk_endpoints_availability():
    """Check if all SDK endpoints are reachable"""
    print("\n=== Testing SDK endpoints availability ===")
    
    endpoints = [
        ("GET", "/sdk/health"),
        ("POST", "/sdk/validate-developer"),
        ("POST", "/sdk/auth/login"),
        ("POST", "/sdk/chat/enhance")
    ]
    
    for method, endpoint in endpoints:
        url = f"{API_BASE}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json={})
        
        print(f"{method} {endpoint}: {response.status_code}")

if __name__ == "__main__":
    print("🔍 Diagnosing Jean Memory SDK Authentication Issue")
    print("=" * 60)
    
    test_sdk_endpoints_availability()
    test_auth_with_invalid_creds()
    test_direct_mcp_endpoint()
    
    print("\n" + "=" * 60)
    print("📊 Diagnosis complete. Check the output above for clues.")