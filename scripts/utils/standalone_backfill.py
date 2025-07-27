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
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
import time

# --- Path Setup ---
# This ensures the script can find the application's modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
api_root = os.path.join(project_root, 'openmemory', 'api')
if api_root not in sys.path:
    sys.path.insert(0, api_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from the app as if we were in the api directory
from app.database import SessionLocal
from app.models import User, Memory, UserNarrative
from app.services.entity_extraction import extract_and_store_entities
from app.utils.memory import get_async_memory_client
from app.utils.gemini import GeminiService

# Configuration
MEMORY_THRESHOLD = 5
NARRATIVE_TTL_DAYS = 7
BATCH_SIZE = 10
ENTITY_BATCH_SIZE = 5  # Smaller batch size for entity processing to prevent connection issues
CONCURRENT_USERS = 3
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]
API_RATE_LIMIT_DELAY = 3
CONNECTION_RETRY_DELAY = 10  # Delay between connection retry attempts

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

def get_batch_session_with_retry(max_retries=3):
    """Create a new database session with retry logic for connection failures."""
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            # Test the connection
            db.execute("SELECT 1")
            return db
        except OperationalError as e:
            if "Max client connections reached" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Connection pool exhausted (attempt {attempt + 1}/{max_retries}). Waiting {CONNECTION_RETRY_DELAY}s before retry...")
                time.sleep(CONNECTION_RETRY_DELAY)
                continue
            else:
                logger.error(f"Failed to create database session after {attempt + 1} attempts: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating database session: {e}")
            if attempt < max_retries - 1:
                time.sleep(CONNECTION_RETRY_DELAY)
                continue
            raise
    
    raise Exception(f"Failed to create database session after {max_retries} attempts")

async def process_entity_batch(memory_ids):
    """Process a small batch of memories for entity extraction with its own database session."""
    db = None
    try:
        # Create a fresh database session for this batch
        db = get_batch_session_with_retry()
        
        batch_results = {'successful': 0, 'failed': 0}
        
        for memory_id in memory_ids:
            try:
                logger.info(f"Processing memory {memory_id} for entity extraction...")
                await extract_and_store_entities(db, str(memory_id))
                batch_results['successful'] += 1
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to process memory {memory_id}: {e}")
                batch_results['failed'] += 1
                # Continue with next memory instead of failing the entire batch
                
        logger.info(f"✅ Batch completed: {batch_results['successful']} successful, {batch_results['failed']} failed")
        return batch_results
        
    finally:
        # Always ensure the database session is properly closed
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")

async def backfill_entities():
    """Main logic for entity backfill with improved connection management."""
    logger.info("🚀 Starting Entity Backfill")
    
    total_processed = 0
    total_successful = 0
    total_failed = 0
    
    while True:
        # Create a temporary session just to get the next batch of memory IDs
        temp_db = None
        try:
            temp_db = get_batch_session_with_retry()
            
            # Get memory IDs that need processing (not the full objects to save memory)
            memories_to_process = temp_db.query(Memory.id).filter(Memory.entities == None).limit(50).all()
            memory_ids = [mem.id for mem in memories_to_process]
            
        except Exception as e:
            logger.error(f"Failed to get batch of memories: {e}")
            break
        finally:
            if temp_db:
                temp_db.close()
        
        if not memory_ids:
            logger.info("✅ No more memories to process. Entity backfill completed.")
            logger.info(f"📊 Final stats: {total_successful} successful, {total_failed} failed, {total_processed} total processed")
            break
            
        logger.info(f"Found {len(memory_ids)} memories to process in this batch.")
        
        # Process memories in small sub-batches with their own database sessions
        for i in range(0, len(memory_ids), ENTITY_BATCH_SIZE):
            batch_memory_ids = memory_ids[i:i + ENTITY_BATCH_SIZE]
            logger.info(f"Processing sub-batch {i//ENTITY_BATCH_SIZE + 1}: {len(batch_memory_ids)} memories")
            
            try:
                batch_results = await process_entity_batch(batch_memory_ids)
                total_successful += batch_results['successful']
                total_failed += batch_results['failed']
                total_processed += len(batch_memory_ids)
                
                # Brief pause between batches to allow other connections
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to process batch: {e}")
                total_failed += len(batch_memory_ids)
                total_processed += len(batch_memory_ids)
                
                # Wait a bit longer if we encounter errors to let connection issues resolve
                await asyncio.sleep(5)
        
        logger.info(f"📊 Progress: {total_successful} successful, {total_failed} failed, {total_processed} total processed")


async def main():
    """Main function to run the backfill script."""
    parser = argparse.ArgumentParser(description="Run backfill tasks for Jean Memory.")
    parser.add_argument('task', choices=['narrative', 'entities', 'all'], help="The backfill task to run.")
    args = parser.parse_args()

    # Make the task argument required
    if not args.task:
        parser.print_help()
        sys.exit(1)

    try:
        if args.task in ['narrative', 'all']:
            # For narratives, we still use a single session since it's less intensive
            db = SessionLocal()
            try:
                await backfill_narratives(db)
            finally:
                db.close()
                
        if args.task in ['entities', 'all']:
            # For entities, we use the improved connection management
            await backfill_entities()
            
    except Exception as e:
        logger.error(f"Critical error in main: {e}")
        sys.exit(1)

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