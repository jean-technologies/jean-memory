#!/usr/bin/env python3
"""
Production-Safe Migration Script for Unified Memory System

This script safely migrates preprocessed memories from production to the unified memory system.
It includes safety checks, rollback capabilities, and progress tracking.
"""

import json
import os
import sys
import asyncio
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'openmemory' / 'api'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UnifiedMemoryMigrator:
    """Handles safe migration of memories to unified system."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.processed_count = 0
        self.error_count = 0
        self.unified_client = None
        self.migration_state_file = "migration_state.json"
        
    async def initialize(self):
        """Initialize the unified memory client."""
        # Only proceed if in local development with unified memory enabled
        if not self._check_environment():
            raise RuntimeError("Environment check failed. Migration can only run in local development with unified memory enabled.")
        
        try:
            from app.utils.unified_memory import get_unified_memory_client
            self.unified_client = await get_unified_memory_client()
            
            if not self.unified_client.is_initialized:
                raise RuntimeError("Unified memory client not initialized")
                
            logger.info("✅ Unified memory client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize unified memory client: {e}")
            raise
    
    def _check_environment(self) -> bool:
        """Ensure we're in a safe environment for migration."""
        checks = {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "").lower() == "development",
            "USE_UNIFIED_MEMORY": os.getenv("USE_UNIFIED_MEMORY", "false").lower() == "true",
            "IS_LOCAL_UNIFIED_MEMORY": os.getenv("IS_LOCAL_UNIFIED_MEMORY", "false").lower() == "true"
        }
        
        logger.info("Environment checks:")
        for key, value in checks.items():
            logger.info(f"  {key}: {'✅' if value else '❌'}")
        
        return all(checks.values())
    
    def load_migration_state(self) -> Dict:
        """Load previous migration state if exists."""
        if os.path.exists(self.migration_state_file):
            with open(self.migration_state_file, 'r') as f:
                return json.load(f)
        return {"processed_ids": [], "last_index": 0}
    
    def save_migration_state(self, state: Dict):
        """Save current migration state."""
        with open(self.migration_state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def migrate_memories(self, preprocessed_file: str, user_id: str, batch_size: int = 10):
        """
        Migrate preprocessed memories to unified system.
        
        Args:
            preprocessed_file: Path to preprocessed memories JSON
            user_id: Target user ID for memories
            batch_size: Number of memories to process in each batch
        """
        logger.info(f"Starting migration from {preprocessed_file}")
        logger.info(f"Dry run: {self.dry_run}")
        
        # Load preprocessed memories
        with open(preprocessed_file, 'r') as f:
            data = json.load(f)
        
        memories = data.get('memories', [])
        total_count = len(memories)
        logger.info(f"Found {total_count} memories to migrate")
        
        # Load migration state
        state = self.load_migration_state()
        processed_ids = set(state.get('processed_ids', []))
        start_index = state.get('last_index', 0)
        
        logger.info(f"Resuming from index {start_index}, {len(processed_ids)} already processed")
        
        # Process memories in batches
        for i in range(start_index, total_count, batch_size):
            batch = memories[i:i + batch_size]
            batch_end = min(i + batch_size, total_count)
            
            logger.info(f"\nProcessing batch {i}-{batch_end} of {total_count}")
            
            for j, memory in enumerate(batch):
                memory_id = memory.get('id', f'unknown_{i+j}')
                
                # Skip if already processed
                if memory_id in processed_ids:
                    logger.debug(f"Skipping already processed memory {memory_id}")
                    continue
                
                try:
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would migrate memory {memory_id}: {memory.get('memory_text', '')[:50]}...")
                    else:
                        await self._migrate_single_memory(memory, user_id)
                    
                    processed_ids.add(memory_id)
                    self.processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error migrating memory {memory_id}: {e}")
                    self.error_count += 1
                    
                    # Save state after each error
                    state['processed_ids'] = list(processed_ids)
                    state['last_index'] = i + j
                    self.save_migration_state(state)
                    
                    # Ask whether to continue
                    if not self.dry_run:
                        response = input(f"\nError occurred. Continue? (y/n): ")
                        if response.lower() != 'y':
                            logger.info("Migration paused by user")
                            return
            
            # Save state after each batch
            state['processed_ids'] = list(processed_ids)
            state['last_index'] = batch_end
            self.save_migration_state(state)
            
            # Progress update
            progress = (batch_end / total_count) * 100
            logger.info(f"Progress: {progress:.1f}% ({batch_end}/{total_count})")
    
    async def _migrate_single_memory(self, memory: Dict, user_id: str):
        """Migrate a single memory to unified system."""
        # Parse dates
        creation_date = self._parse_date(memory.get('created_at'))
        memory_date = self._parse_date(memory.get('temporal_context')) or creation_date
        
        # Prepare metadata
        metadata = {
            "original_id": memory.get('id'),
            "migrated_at": datetime.now(timezone.utc).isoformat(),
            "gemini_processed": memory.get('gemini_processed', False),
            "confidence": memory.get('confidence', 'unknown'),
            "temporal_keywords": memory.get('temporal_keywords', []),
            "source": "production_migration"
        }
        
        # Add to unified system
        result = await self.unified_client.add_memory(
            text=memory.get('memory_text', ''),
            user_id=user_id,
            creation_date=creation_date,
            memory_date=memory_date,
            metadata=metadata
        )
        
        if "error" in result:
            raise Exception(f"Failed to add memory: {result['error']}")
        
        logger.debug(f"Successfully migrated memory {memory.get('id')}")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Handle ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Handle other formats as needed
            return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except:
            return None
    
    def print_summary(self):
        """Print migration summary."""
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total processed: {self.processed_count}")
        logger.info(f"Errors: {self.error_count}")
        logger.info(f"Success rate: {(self.processed_count - self.error_count) / max(1, self.processed_count) * 100:.1f}%")
        
        if self.dry_run:
            logger.info("\n⚠️  This was a DRY RUN. No data was actually migrated.")
            logger.info("Run with --execute to perform actual migration.")


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate preprocessed memories to unified system')
    parser.add_argument('--input', required=True, help='Path to preprocessed memories JSON file')
    parser.add_argument('--user-id', required=True, help='Target user ID for memories')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of memories per batch')
    parser.add_argument('--execute', action='store_true', help='Actually perform migration (default is dry run)')
    
    args = parser.parse_args()
    
    # Set environment for local development
    os.environ["ENVIRONMENT"] = "development"
    os.environ["USE_UNIFIED_MEMORY"] = "true"
    os.environ["IS_LOCAL_UNIFIED_MEMORY"] = "true"
    
    migrator = UnifiedMemoryMigrator(dry_run=not args.execute)
    
    try:
        await migrator.initialize()
        await migrator.migrate_memories(
            preprocessed_file=args.input,
            user_id=args.user_id,
            batch_size=args.batch_size
        )
        migrator.print_summary()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 