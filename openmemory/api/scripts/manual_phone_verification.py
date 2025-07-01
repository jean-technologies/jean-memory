#!/usr/bin/env python3
"""
Script to manually verify a user's phone number.

This script will:
1. Find the user by phone number
2. Set phone_verified = True
3. Clear any pending verification codes
4. Reset verification attempts
5. Enable SMS

Usage:
    python scripts/manual_phone_verification.py +14146874123
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def manually_verify_phone(phone_number: str):
    """Manually verify a user's phone number"""
    
    logger.info(f"Looking for user with phone number: {phone_number}")
    
    db = SessionLocal()
    try:
        # Find user by phone number
        user = db.query(User).filter(User.phone_number == phone_number).first()
        
        if not user:
            logger.error(f"❌ No user found with phone number: {phone_number}")
            return False
        
        logger.info(f"✅ Found user: {user.email} (ID: {user.user_id})")
        logger.info(f"   Current verification status: {user.phone_verified}")
        logger.info(f"   Current verification attempts: {user.phone_verification_attempts}")
        logger.info(f"   SMS enabled: {user.sms_enabled}")
        
        # Check current metadata
        if user.metadata_ and 'sms_verification' in user.metadata_:
            verification_data = user.metadata_['sms_verification']
            logger.info(f"   Pending verification code: {verification_data.get('code')}")
            logger.info(f"   Code expires at: {verification_data.get('expires_at')}")
        else:
            logger.info("   No pending verification code found")
        
        # Update verification status
        user.phone_verified = True
        user.phone_verified_at = datetime.now(timezone.utc)
        user.sms_enabled = True
        user.phone_verification_attempts = 0
        
        # Clear any pending verification codes from metadata
        if user.metadata_ and 'sms_verification' in user.metadata_:
            del user.metadata_['sms_verification']
            logger.info("   Cleared pending verification code")
        
        # Commit changes
        db.commit()
        
        logger.info("🎉 SUCCESS: Phone number manually verified!")
        logger.info(f"   ✅ phone_verified = {user.phone_verified}")
        logger.info(f"   ✅ phone_verified_at = {user.phone_verified_at}")
        logger.info(f"   ✅ sms_enabled = {user.sms_enabled}")
        logger.info(f"   ✅ phone_verification_attempts = {user.phone_verification_attempts}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/manual_phone_verification.py <phone_number>")
        print("Example: python scripts/manual_phone_verification.py +14146874123")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    
    # Basic validation
    if not phone_number.startswith('+') or len(phone_number) < 12:
        logger.error("❌ Invalid phone number format. Must be in E.164 format (e.g., +14146874123)")
        sys.exit(1)
    
    logger.info("🔧 Manual Phone Verification Tool")
    logger.info("="*50)
    
    success = manually_verify_phone(phone_number)
    
    if success:
        logger.info("="*50)
        logger.info("✅ Verification complete! The user can now:")
        logger.info("   • Send SMS commands to Jean Memory")
        logger.info("   • Use all SMS features")
        logger.info("   • No longer see verification errors")
        sys.exit(0)
    else:
        logger.info("="*50)
        logger.error("❌ Manual verification failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()