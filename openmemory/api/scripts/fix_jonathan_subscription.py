#!/usr/bin/env python3
"""
Quick script to fix Jonathan's subscription tier in the database
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.models import User, SubscriptionTier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_jonathan_subscription():
    """Fix Jonathan's subscription to PRO"""
    logger.info("🔧 Fixing Jonathan's subscription tier...")
    
    with SessionLocal() as db:
        # Find users with None subscription_tier
        users_without_tier = db.query(User).filter(User.subscription_tier == None).all()
        
        logger.info(f"Found {len(users_without_tier)} users without subscription tier:")
        for user in users_without_tier:
            logger.info(f"  - {user.user_id} ({user.email})")
        
        # Ask which user to fix (for safety)
        print("\nWhich user should get PRO subscription?")
        for i, user in enumerate(users_without_tier):
            print(f"{i+1}. {user.user_id} ({user.email or 'No email'})")
        
        try:
            choice = int(input("Enter choice (1-{}): ".format(len(users_without_tier))))
            if 1 <= choice <= len(users_without_tier):
                user_to_fix = users_without_tier[choice-1]
                
                # Update subscription
                user_to_fix.subscription_tier = SubscriptionTier.PRO
                user_to_fix.subscription_status = 'active'
                db.commit()
                
                logger.info(f"✅ Updated {user_to_fix.user_id} to PRO subscription!")
                logger.info(f"   Email: {user_to_fix.email}")
                logger.info(f"   Tier: {user_to_fix.subscription_tier}")
                logger.info(f"   Status: {user_to_fix.subscription_status}")
                
            else:
                logger.error("Invalid choice")
                return False
                
        except (ValueError, KeyboardInterrupt):
            logger.info("Cancelled")
            return False
    
    return True

if __name__ == "__main__":
    success = fix_jonathan_subscription()
    sys.exit(0 if success else 1)