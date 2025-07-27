import asyncio
import logging
import os
import sys
from sqlalchemy.orm import Session

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
from app.models import Memory
from app.services.entity_extraction import extract_and_store_entities

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def backfill_all_entities():
    """
    Simple, sequential backfill for all memories that need entity extraction.
    Uses a single database session like successful previous backfills.
    """
    logger.info("🚀 Starting entity backfill - sequential processing")
    
    db = SessionLocal()
    try:
        # Get total count first
        total_count = db.query(Memory).filter(Memory.entities == None).count()
        logger.info(f"Found {total_count} memories that need entity extraction")
        
        if total_count == 0:
            logger.info("✅ No memories need processing")
            return
        
        processed = 0
        failed = 0
        
        # Process memories one at a time, sequentially
        while True:
            # Get a single memory to process
            memory = db.query(Memory).filter(Memory.entities == None).first()
            
            if not memory:
                logger.info("✅ All memories processed!")
                break
                
            try:
                logger.info(f"Processing memory {memory.id} ({processed + 1}/{total_count})")
                
                # Call the function with the correct parameters
                await extract_and_store_entities(db, str(memory.id))
                
                processed += 1
                
                # Log progress every 50 memories
                if processed % 50 == 0:
                    logger.info(f"📊 Progress: {processed} processed, {failed} failed")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process memory {memory.id}: {e}")
                failed += 1
                
                # If we can't process this memory, mark it so we don't get stuck
                try:
                    memory.entities = {"error": "failed_extraction"}
                    db.commit()
                except:
                    db.rollback()
        
        logger.info(f"🎉 Backfill complete! {processed} successful, {failed} failed")
        
    finally:
        db.close()

async def main():
    """Main function - just run the backfill."""
    await backfill_all_entities()

if __name__ == "__main__":
    # Simple usage: python scripts/utils/backfill_entities.py
    asyncio.run(main()) 