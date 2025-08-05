#!/usr/bin/env python3
"""
Test script to validate the new proxy logic locally
"""

import sys
import os
sys.path.insert(0, 'openmemory/api')

def test_proxy_imports():
    """Test that our new proxy code imports correctly"""
    print("🧪 Testing Local Proxy Implementation")
    print("=" * 50)
    
    try:
        # Test that we can import the new proxy
        from app.mcp_claude_simple import oauth_mcp_router, validate_origin, proxy_to_v2_logic
        print("✅ Successfully imported new proxy components")
        
        # Test that handle_request_logic is still available  
        from app.routing.mcp import handle_request_logic
        print("✅ Successfully imported V2 logic")
        
        # Test that OAuth is still working
        from app.oauth_simple_new import get_current_user
        print("✅ Successfully imported OAuth functionality")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_origin_validation():
    """Test the origin validation function"""
    print("\n🔒 Testing origin validation...")
    
    try:
        from app.mcp_claude_simple import validate_origin
        
        # Mock request class
        class MockRequest:
            def __init__(self, origin=None):
                self.headers = {"origin": origin} if origin else {}
                
            def get(self, key):
                return self.headers.get(key)
        
        # Test valid origins
        valid_origins = [
            "https://claude.ai",
            "https://app.claude.ai", 
            "https://jean-memory-api-virginia.onrender.com"
        ]
        
        for origin in valid_origins:
            request = MockRequest(origin)
            if validate_origin(request):
                print(f"✅ {origin} - valid")
            else:
                print(f"❌ {origin} - should be valid")
                return False
        
        # Test invalid origin
        request = MockRequest("https://evil.com")
        if not validate_origin(request):
            print("✅ https://evil.com - correctly rejected")
        else:
            print("❌ https://evil.com - should be rejected")
            return False
            
        # Test no origin (should be allowed)
        request = MockRequest(None)
        if validate_origin(request):
            print("✅ No origin - correctly allowed")
        else:
            print("❌ No origin - should be allowed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing origin validation: {e}")
        return False

if __name__ == "__main__":
    print("Testing new OAuth proxy implementation locally...\n")
    
    imports_ok = test_proxy_imports()
    validation_ok = test_origin_validation()
    
    if imports_ok and validation_ok:
        print("\n🎯 Local Test Summary:")
        print("✅ All imports successful")
        print("✅ Origin validation working")
        print("✅ Ready for deployment")
        sys.exit(0)
    else:
        print("\n❌ Local tests failed - fix issues before deploying")
        sys.exit(1)