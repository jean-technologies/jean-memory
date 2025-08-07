import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get the database URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jean_memory:password@localhost:5432/jean_memory_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def clear_cache():
    from sqlalchemy.orm import clear_mappers
    clear_mappers()
    print("SQLAlchemy mappers cleared.")

if __name__ == "__main__":
    clear_cache()
