import os
import asyncio
from dotenv import load_dotenv
import qdrant_client
import asyncpg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
load_dotenv()

# Qdrant Config
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "unified_memory_mem0")

# Postgres Config
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DBNAME = os.getenv("PG_DBNAME")
PG_TABLE_NAME = "memories"  # Your memories table

# --- Main Migration Logic ---

async def migrate_vectors():
    """
    Migrates vectors from a Qdrant collection to a pgvector column in PostgreSQL.
    """
    logger.info("🚀 Starting vector migration from Qdrant to pgvector...")

    # 1. Connect to Qdrant
    try:
        qdrant = qdrant_client.QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        logger.info(f"✅ Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
        # Verify collection exists
        qdrant.get_collection(collection_name=QDRANT_COLLECTION_NAME)
        logger.info(f"✅ Found Qdrant collection: '{QDRANT_COLLECTION_NAME}'")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant or find collection: {e}")
        return

    # 2. Connect to PostgreSQL
    pg_conn = None
    try:
        pg_conn = await asyncpg.connect(
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DBNAME,
            host=PG_HOST,
            port=PG_PORT
        )
        logger.info(f"✅ Connected to PostgreSQL database '{PG_DBNAME}'")
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        if pg_conn:
            await pg_conn.close()
        return

    # 3. Fetch data from Qdrant and update PostgreSQL
    updated_count = 0
    failed_count = 0
    next_offset = None
    
    try:
        while True:
            records, next_offset = qdrant.scroll(
                collection_name=QDRANT_COLLECTION_NAME,
                limit=100,  # Process in batches of 100
                offset=next_offset,
                with_payload=True,
                with_vectors=True,
            )

            if not records:
                break

            for record in records:
                try:
                    # Assumption: The linking ID is in the payload's 'id' field,
                    # which corresponds to the 'mem0_id' in your Postgres table.
                    # Adjust 'mem0_id_in_payload' if the key is different (e.g., 'hash', 'memory_id')
                    mem0_id_in_payload = record.payload.get("id")

                    if not mem0_id_in_payload:
                        logger.warning(f"⚠️ Skipping record ID {record.id}: 'id' not found in Qdrant payload.")
                        failed_count += 1
                        continue

                    vector = record.vector
                    
                    # Update the corresponding row in PostgreSQL
                    await pg_conn.execute(
                        f"""
                        UPDATE {PG_TABLE_NAME}
                        SET vector = $1
                        WHERE mem0_id = $2
                        """,
                        str(vector),  # pgvector expects a string representation
                        mem0_id_in_payload
                    )
                    updated_count += 1
                    logger.info(f"Updated vector for mem0_id: {mem0_id_in_payload}")

                except Exception as e:
                    logger.error(f"❌ Failed to process record {record.id}: {e}")
                    failed_count += 1
            
            if next_offset is None:
                break

    except Exception as e:
        logger.error(f"❌ An error occurred during the migration scroll: {e}")
    finally:
        if pg_conn:
            await pg_conn.close()
            logger.info("PostgreSQL connection closed.")

    logger.info("🎉 Migration complete!")
    logger.info(f"📈 Successfully updated {updated_count} records.")
    logger.info(f"📉 Failed to update {failed_count} records.")

if __name__ == "__main__":
    asyncio.run(migrate_vectors()) 