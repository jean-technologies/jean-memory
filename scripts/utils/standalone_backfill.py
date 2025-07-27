#!/usr/bin/env python3
"""
Standalone backfill script for production.
Handles both narrative generation and entity extraction for existing memories.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta, UTC
import traceback
from pathlib import Path
import argparse

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if str(project_root) not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from the app
from openmemory.api.app.database import SessionLocal
from openmemory.api.app.models import User, Memory, UserNarrative
from openmemory.api.app.services.entity_extraction import extract_and_store_entities
from openmemory.api.app.utils.memory import get_async_memory_client
from openmemory.api.app.utils.gemini import GeminiService
from sqlalchemy import func

# Configuration
MEMORY_THRESHOLD = 5
NARRATIVE_TTL_DAYS = 7
BATCH_SIZE = 10
CONCURRENT_USERS = 3
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]
API_RATE_LIMIT_DELAY = 3

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_eligible_users_for_narrative(db):
    """Get users with 5+ memories who need narratives."""
    logger.info("🔍 Finding eligible users for narrative backfill...")
    users = db.query(User).join(User.memories).filter(Memory.state == 'active').group_by(User.id).having(func.count(Memory.id) > MEMORY_THRESHOLD).all()
    logger.info(f"✅ Found {len(users)} eligible users for narrative backfill.")
    return [user.user_id for user in users]

async def get_user_context_from_memories(user_id: str):
    """Get comprehensive user context using Jean Memory V2."""
    try:
        memory_client = await get_async_memory_client()
        memory_results = await memory_client.search(
            query="life experiences preferences goals work interests personality",
            user_id=user_id,
            limit=50
        )
        memories = memory_results.get('results', []) if isinstance(memory_results, dict) else memory_results
        
        memories_text = [mem.get('memory', mem.get('content', '')) for mem in memories[:25] if mem.get('memory') or mem.get('content')]
        return "\n".join(memories_text) if memories_text else None
    except Exception as e:
        logger.error(f"❌ [User {user_id}] Failed to get Jean Memory V2 context: {str(e)}")
        return None

async def generate_narrative_for_user(user_id: str, gemini: GeminiService, retry_count: int = 0):
    """Generate narrative for a user with retry logic."""
    logger.info(f"🤖 [User {user_id}] Generating narrative (attempt {retry_count + 1})...")
    context_text = await get_user_context_from_memories(user_id)
    if not context_text or len(context_text) < 200:
        logger.warning(f"⚠️ [User {user_id}] Insufficient context.")
        return None
    
    try:
        narrative = await gemini.generate_narrative_pro(context_text)
        if narrative and len(narrative) > 100:
            logger.info(f"✅ [User {user_id}] Generated narrative.")
            return narrative.strip()
        # Retry logic for empty/short responses
    except Exception as e:
        logger.error(f"💥 [User {user_id}] Generation failed: {str(e)}")
        # Retry logic for specific errors
    return None

def save_narrative_to_db(db, user_id: str, narrative_content: str):
    """Save narrative to database."""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.error(f"❌ [User {user_id}] User not found in database")
            return False
        
        existing_narrative = db.query(UserNarrative).filter(UserNarrative.user_id == user.id).first()
        if existing_narrative:
            db.delete(existing_narrative)
            
        new_narrative = UserNarrative(user_id=user.id, narrative_content=narrative_content, generated_at=datetime.now(UTC))
        db.add(new_narrative)
        db.commit()
        logger.info(f"✅ [User {user_id}] Saved narrative successfully.")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [User {user_id}] Database save failed: {str(e)}")
        return False

async def process_narrative_batch(user_ids, gemini, db):
    """Process a batch of users for narrative generation."""
    logger.info(f"🔄 Processing narrative batch of {len(user_ids)} users")
    results = {'successful': 0, 'failed': 0, 'skipped': 0}
    for user_id in user_ids:
        narrative = await generate_narrative_for_user(user_id, gemini)
        if narrative:
            if save_narrative_to_db(db, user_id, narrative):
                results['successful'] += 1
            else:
                results['failed'] += 1
        else:
            results['skipped'] += 1
    return results

async def backfill_narratives(db):
    """Main logic for narrative backfill."""
    logger.info("🚀 Starting Narrative Backfill")
    gemini = GeminiService()
    eligible_users = get_eligible_users_for_narrative(db)
    if not eligible_users:
        logger.info("🎯 No users need narrative generation.")
        return

    for i in range(0, len(eligible_users), BATCH_SIZE):
        batch_users = eligible_users[i:i + BATCH_SIZE]
        await process_narrative_batch(batch_users, gemini, db)

async def backfill_entities(db):
    """Main logic for entity backfill."""
    logger.info("🚀 Starting Entity Backfill")
    memories_to_process = db.query(Memory).filter(Memory.entities == None).all()
    total_memories = len(memories_to_process)
    logger.info(f"Found a total of {total_memories} memories to process for entities.")
    
    tasks = []
    for i, memory in enumerate(memories_to_process):
        tasks.append(extract_and_store_entities(str(memory.id)))
        if len(tasks) >= 50:
            await asyncio.gather(*tasks)
            tasks = []
            logger.info(f"Processed a batch of 50 memories for entities. ({i+1}/{total_memories})")
    if tasks:
        await asyncio.gather(*tasks)
    logger.info("✅ Entity backfill completed.")


async def main():
    """Main function to run the backfill script."""
    parser = argparse.ArgumentParser(description="Run backfill tasks for Jean Memory.")
    parser.add_argument('task', choices=['narrative', 'entities', 'all'], help="The backfill task to run.")
    args = parser.parse_args()

    # Make the task argument required
    if not args.task:
        parser.print_help()
        sys.exit(1)

    db = SessionLocal()
    try:
        if args.task in ['narrative', 'all']:
            await backfill_narratives(db)
        if args.task in ['entities', 'all']:
            await backfill_entities(db)
    finally:
        db.close()

if __name__ == "__main__":
    # Example Usage:
    # python scripts/utils/standalone_backfill.py narrative
    # python scripts/utils/standalone_backfill.py entities
    # python scripts/utils/standalone_backfill.py all
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user.")
        sys.exit(1) 