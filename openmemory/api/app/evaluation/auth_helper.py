"""
Secure Token Capture and Storage System for Jean Memory Evaluation Framework

This module provides secure token management for accessing production services
during automated testing. Tokens are extracted manually from authenticated
browser sessions and stored locally with encryption.

Usage:
    python -m app.evaluation.auth_helper --setup
    python -m app.evaluation.auth_helper --validate
"""

import os
import json
import base64
import getpass
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import asyncio
import aiohttp
import argparse


class SecureTokenManager:
    """Secure local token management with encryption"""
    
    def __init__(self, token_file: str = ".jean_memory_token"):
        self.token_file = Path(token_file)
        self.api_base_url = "https://jean-memory-api-virginia.onrender.com"
        
    def _get_encryption_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _encrypt_token(self, token_data: Dict[str, Any], password: str) -> bytes:
        """Encrypt token data with password"""
        salt = os.urandom(16)
        key = self._get_encryption_key(password, salt)
        fernet = Fernet(key)
        
        token_json = json.dumps(token_data).encode()
        encrypted_token = fernet.encrypt(token_json)
        
        # Prepend salt to encrypted data
        return salt + encrypted_token
    
    def _decrypt_token(self, encrypted_data: bytes, password: str) -> Dict[str, Any]:
        """Decrypt token data with password"""
        salt = encrypted_data[:16]
        encrypted_token = encrypted_data[16:]
        
        key = self._get_encryption_key(password, salt)
        fernet = Fernet(key)
        
        token_json = fernet.decrypt(encrypted_token)
        return json.loads(token_json.decode())
    
    def store_token(self, token: str, description: str = "Jean Memory Auth Token") -> bool:
        """Store token securely with encryption"""
        try:
            password = getpass.getpass("Enter password to encrypt token: ")
            confirm_password = getpass.getpass("Confirm password: ")
            
            if password != confirm_password:
                print("❌ Passwords don't match!")
                return False
            
            if len(password) < 8:
                print("❌ Password must be at least 8 characters long!")
                return False
            
            token_data = {
                "token": token,
                "description": description,
                "created_at": __import__('datetime').datetime.now().isoformat(),
                "api_base_url": self.api_base_url
            }
            
            encrypted_data = self._encrypt_token(token_data, password)
            
            with open(self.token_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.token_file, 0o600)
            
            print(f"✅ Token stored securely in {self.token_file}")
            print("⚠️  Remember your password - it cannot be recovered!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to store token: {e}")
            return False
    
    def load_token(self, password: Optional[str] = None) -> Optional[str]:
        """Load and decrypt stored token"""
        try:
            if not self.token_file.exists():
                print(f"❌ Token file {self.token_file} not found")
                return None
            
            if password is None:
                password = getpass.getpass("Enter password to decrypt token: ")
            
            with open(self.token_file, 'rb') as f:
                encrypted_data = f.read()
            
            token_data = self._decrypt_token(encrypted_data, password)
            return token_data["token"]
            
        except Exception as e:
            print(f"❌ Failed to load token: {e}")
            return None
    
    def token_exists(self) -> bool:
        """Check if token file exists"""
        return self.token_file.exists()
    
    async def validate_token(self, token: Optional[str] = None) -> bool:
        """Validate token against Jean Memory API"""
        try:
            if token is None:
                token = self.load_token()
                if token is None:
                    return False
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Test with a simple API endpoint
                async with session.get(
                    f"{self.api_base_url}/api/v1/memories/",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        print("✅ Token validation successful!")
                        return True
                    elif response.status == 401:
                        print("❌ Token is invalid or expired")
                        return False
                    else:
                        print(f"⚠️  Unexpected response status: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
            return False


def interactive_token_setup():
    """Interactive token extraction guide"""
    print("=" * 60)
    print("🔐 Jean Memory Token Extraction Guide")
    print("=" * 60)
    print()
    print("This tool will help you capture an authentication token from your")
    print("Jean Memory session for use in automated testing.")
    print()
    print("STEPS:")
    print("1. Open your browser and go to https://jeanmemory.com")
    print("2. Sign in to your account if not already signed in")
    print("3. Open Developer Tools (F12 or Cmd+Option+I)")
    print("4. Go to the Network tab")
    print("5. Refresh the page or perform any action")
    print("6. Look for requests to jean-memory-api-virginia.onrender.com")
    print("7. Click on any API request")
    print("8. In the Request Headers section, find 'Authorization: Bearer <token>'")
    print("9. Copy the token part (everything after 'Bearer ')")
    print()
    print("⚠️  SECURITY NOTE:")
    print("- This token grants access to your Jean Memory account")
    print("- It will be encrypted and stored locally only")
    print("- Never share this token with others")
    print("- The token may expire and need to be refreshed")
    print()
    
    token = input("Paste your authentication token here: ").strip()
    
    if not token:
        print("❌ No token provided!")
        return False
    
    if len(token) < 20:  # Basic sanity check
        print("❌ Token seems too short. Please check and try again.")
        return False
    
    manager = SecureTokenManager()
    return manager.store_token(token)


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Jean Memory Token Management")
    parser.add_argument("--setup", action="store_true", help="Set up token extraction")
    parser.add_argument("--validate", action="store_true", help="Validate stored token")
    parser.add_argument("--check", action="store_true", help="Check if token exists")
    
    args = parser.parse_args()
    
    manager = SecureTokenManager()
    
    if args.setup:
        success = interactive_token_setup()
        if success:
            print("\n🎉 Token setup completed successfully!")
            print("You can now run automated tests with authentication.")
        return
    
    if args.validate:
        print("🔍 Validating stored token...")
        is_valid = await manager.validate_token()
        if is_valid:
            print("✅ Token is valid and working!")
        else:
            print("❌ Token validation failed. You may need to extract a new token.")
        return
    
    if args.check:
        if manager.token_exists():
            print("✅ Token file exists")
        else:
            print("❌ No token file found. Run with --setup to extract a token.")
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())