#!/usr/bin/env python3
"""
OpenAI API Key Setup Helper

This script helps you set your OpenAI API key for the R&D environment.
"""

import os
import sys

def set_openai_key():
    """Set OpenAI API key in environment"""
    
    print("🔑 OpenAI API Key Setup")
    print("=" * 40)
    
    # Check if already set
    current_key = os.getenv("OPENAI_API_KEY")
    if current_key and current_key != "your_openai_api_key_here":
        print(f"✅ OpenAI API key is already set: {current_key[:10]}...")
        return True
    
    print("❌ OpenAI API key is not set.")
    print("\n💡 To use the unified memory system, you need an OpenAI API key.")
    print("   You can get one from: https://platform.openai.com/api-keys")
    
    print(f"\n📝 To set your OpenAI API key, run:")
    print(f"   export OPENAI_API_KEY='your-actual-api-key-here'")
    print(f"   # Then run your R&D test again")
    
    print(f"\n🔄 Or add it to your .env file:")
    print(f"   echo 'OPENAI_API_KEY=your-actual-api-key-here' >> .env")
    
    return False

def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        from openai import OpenAI
        
        client = OpenAI()
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ OpenAI API connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_openai_connection()
    else:
        set_openai_key() 