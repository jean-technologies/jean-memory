import asyncio
import logging
import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import select, func

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from the app
from openmemory.api.app.database import SessionLocal, engine
from openmemory.api.app.models import Memory
from openmemory.api.app.services.entity_extraction import extract_and_store_entities

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def backfill_entities_for_user(db: Session, user_id: str):
    """
    Backfills entities for all memories of a specific user that haven't been processed.
    """
    memories_to_process = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.entities == None
    ).all()
    
    total_memories = len(memories_to_process)
    logger.info(f"Found {total_memories} memories to process for user {user_id}.")

    tasks = []
    for i, memory in enumerate(memories_to_process):
        logger.info(f"Queueing memory {i+1}/{total_memories} (ID: {memory.id}) for entity extraction.")
        tasks.append(extract_and_store_entities(str(memory.id)))

    await asyncio.gather(*tasks)
    logger.info(f"Completed entity extraction for {total_memories} memories for user {user_id}.")

async def backfill_all_users(db: Session):
    """
    Backfills entities for all memories for all users.
    """
    memories_to_process = db.query(Memory).filter(Memory.entities == None).all()
    
    total_memories = len(memories_to_process)
    logger.info(f"Found a total of {total_memories} memories to process across all users.")
    
    tasks = []
    for i, memory in enumerate(memories_to_process):
        logger.info(f"Queueing memory {i+1}/{total_memories} (ID: {memory.id}) for entity extraction.")
        tasks.append(extract_and_store_entities(str(memory.id)))
        
        # Batch processing to avoid overwhelming the system
        if len(tasks) >= 50:
            await asyncio.gather(*tasks)
            tasks = []
            logger.info("Processed a batch of 50 memories.")

    if tasks:
        await asyncio.gather(*tasks)
        logger.info(f"Processed the final batch of {len(tasks)} memories.")

    logger.info("Completed entity extraction for all memories.")


async def main():
    """
    Main function to run the backfill script.
    Can be configured to run for a specific user or for all users.
    """
    logger.info("Starting entity backfill script.")
    db = SessionLocal()
    try:
        # Check for a specific user ID from command line arguments
        if len(sys.argv) > 1:
            user_id_to_process = sys.argv[1]
            logger.info(f"Running backfill for specific user: {user_id_to_process}")
            await backfill_entities_for_user(db, user_id_to_process)
        else:
            logger.info("Running backfill for all users.")
            await backfill_all_users(db)
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    # This allows the script to be run from the command line
    # Example usage:
    # python scripts/utils/backfill_entities.py
    # python scripts/utils/backfill_entities.py <user_id>
    asyncio.run(main()) 