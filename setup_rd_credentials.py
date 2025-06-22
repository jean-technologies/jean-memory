#!/usr/bin/env python3
"""
R&D Credentials Setup Helper

This script helps you configure your R&D environment with the correct credentials
for accessing production Supabase data while developing locally.
"""

import os
import re
from pathlib import Path

def find_supabase_credentials():
    """Try to find Supabase credentials in various config files"""
    print("🔍 Looking for existing Supabase credentials...")
    
    credentials = {}
    search_paths = [
        "openmemory/api/.env",
        "openmemory/.env", 
        ".env.local",
        ".env.production",
        "render.yaml"
    ]
    
    for path in search_paths:
        if Path(path).exists():
            print(f"   Checking {path}...")
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    
                # Look for Supabase URL
                url_match = re.search(r'SUPABASE_URL[=:]\s*([^\s\n]+)', content)
                if url_match and 'supabase.co' in url_match.group(1):
                    credentials['url'] = url_match.group(1).strip('"\'')
                    print(f"      ✅ Found SUPABASE_URL: {credentials['url']}")
                
                # Look for Service Key
                key_match = re.search(r'SUPABASE_SERVICE_KEY[=:]\s*([^\s\n]+)', content)
                if key_match and len(key_match.group(1)) > 20:
                    credentials['service_key'] = key_match.group(1).strip('"\'')
                    print(f"      ✅ Found SUPABASE_SERVICE_KEY: {credentials['service_key'][:20]}...")
                    
            except Exception as e:
                print(f"      ❌ Error reading {path}: {e}")
    
    return credentials

def update_rd_env(supabase_url, supabase_service_key):
    """Update the .env file with proper R&D credentials"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found. Run: cp rd_environment.env .env")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace placeholders
    content = content.replace('https://your-project.supabase.co', supabase_url)
    content = content.replace('your_supabase_service_key_here', supabase_service_key)
    
    # Write back
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Updated .env with your Supabase credentials")
    return True

def main():
    print("🚀 R&D Credentials Setup")
    print("=" * 50)
    
    # Try to find existing credentials
    found_creds = find_supabase_credentials()
    
    if found_creds.get('url') and found_creds.get('service_key'):
        print(f"\n🎉 Found your Supabase credentials!")
        print(f"   URL: {found_creds['url']}")
        print(f"   Service Key: {found_creds['service_key'][:20]}...")
        
        response = input("\nUse these credentials for R&D? (y/n): ").strip().lower()
        if response == 'y':
            if update_rd_env(found_creds['url'], found_creds['service_key']):
                print("\n✅ R&D environment configured!")
                print("   Next steps:")
                print("   1. Run: python rd_setup.py --check")
                print("   2. Run: python rd_quickstart.py --auto")
                return
    else:
        print(f"\n⚠️ Could not automatically find your Supabase credentials.")
    
    print(f"\n📝 Manual Setup Required:")
    print(f"   1. Go to your Supabase dashboard: https://supabase.com/dashboard")
    print(f"   2. Select your project")
    print(f"   3. Go to Settings > API")
    print(f"   4. Copy your Project URL and Service Role Key")
    print(f"   5. Edit .env file and replace:")
    print(f"      - SUPABASE_URL=https://your-project.supabase.co")
    print(f"      - SUPABASE_SERVICE_KEY=your_supabase_service_key_here")
    
    print(f"\n🔧 Alternative: Set environment variables directly:")
    print(f"   export SUPABASE_URL='https://your-project.supabase.co'")
    print(f"   export SUPABASE_SERVICE_KEY='your_service_key'")
    print(f"   python rd_quickstart.py --auto")

if __name__ == "__main__":
    main() 