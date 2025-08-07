import os
import sys
import asyncio
import uuid
import psycopg2

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'openmemory', 'api')))

from app.auth import hash_api_key

# Get the database URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jean_memory:password@localhost:5432/jean_memory_db")

async def create_local_api_key(email: str, key_name: str):
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_row = cur.fetchone()

        if not user_row:
            user_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO users (id, user_id, email, name) VALUES (%s, %s, %s, %s)",
                (user_id, user_id, email, "Local User")
            )
            print(f"User with email {email} not found. Created a new user.")
        else:
            user_id = user_row[0]

        api_key = f"jean_sk_local_{os.urandom(24).hex()}"
        hashed_key = hash_api_key(api_key)

        cur.execute(
            "INSERT INTO api_keys (id, user_id, name, key_hash) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), user_id, key_name, hashed_key)
        )
        conn.commit()

        print(f"API Key created for {email}:")
        print(api_key)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_local_api_key.py <email> <key_name>")
        sys.exit(1)

    email = sys.argv[1]
    key_name = sys.argv[2]
    asyncio.run(create_local_api_key(email, key_name))
