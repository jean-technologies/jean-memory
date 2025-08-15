#!/usr/bin/env python3
"""
Test SDK with real user to see memories in UI
"""

from jeanmemory import JeanClient
import requests

print("🔗 Testing Jean Memory SDK with Real User Integration")
print("="*60)

# You'll need to get your real JWT token from browser dev tools
# or use the test user endpoint to get a consistent user ID
real_api_key = "jean_sk_test123"  # Replace with your real API key

try:
    print("1. Initializing SDK...")
    jean = JeanClient(api_key=real_api_key)
    
    print("2. Testing test user creation...")
    try:
        # This should create a consistent test user for your API key
        response = requests.get(
            "https://jean-memory-api-virginia.onrender.com/api/v1/test-user",
            headers={"Authorization": f"Bearer {real_api_key}"}
        )
        if response.status_code == 200:
            test_user_data = response.json()
            print(f"✅ Test user created: {test_user_data['user_token']}")
            user_token = test_user_data['user_token']
        else:
            print(f"⚠️  Test user endpoint returned {response.status_code}, using fallback")
            user_token = "fallback_test_user"
    except Exception as e:
        print(f"⚠️  Using fallback user token due to: {e}")
        user_token = "fallback_test_user"
    
    print(f"3. Using user token: {user_token}")
    
    print("4. Adding memory that should appear in UI...")
    result = jean.tools.add_memory(
        user_token=user_token,
        content="SDK Integration Test - This memory should appear in the Jean Memory UI dashboard",
        tags=["sdk-test", "integration", "ui-visible"]
    )
    print(f"✅ Memory added: {result}")
    
    print("5. Retrieving context to verify storage...")
    context = jean.get_context(
        user_token=user_token,
        message="What integration tests have we run?"
    )
    print(f"✅ Context retrieved: {context.text[:200]}...")
    
    print("6. Searching for the test memory...")
    search_results = jean.tools.search_memory(
        user_token=user_token,
        query="SDK integration test"
    )
    print(f"✅ Search results: {len(search_results.get('memories', []))} memories found")
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print(f"1. Check your Jean Memory UI dashboard")
    print(f"2. Look for user: {user_token}")
    print(f"3. Memory should contain: 'SDK Integration Test'")
    print(f"4. If not visible, check user ID consistency between UI and SDK")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()