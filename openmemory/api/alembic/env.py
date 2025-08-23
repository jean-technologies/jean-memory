from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import your models here
from app.database import Base
from app.models import *  # Import all your models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = os.getenv("DATABASE_URL", "sqlite:///./openmemory.db")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    import time
    import logging
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = os.getenv("DATABASE_URL", "sqlite:///./openmemory.db")
    
    # Add connection pool settings to reduce connection usage
    configuration["sqlalchemy.pool_pre_ping"] = True
    configuration["sqlalchemy.pool_recycle"] = 300
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Retry connection with backoff for connection pool exhaustion
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with connectable.connect() as connection:
                context.configure(
                    connection=connection, target_metadata=target_metadata
                )

                with context.begin_transaction():
                    context.run_migrations()
            break  # Success, exit retry loop
        except Exception as e:
            if "Max client connections reached" in str(e) and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # 10, 20, 30 seconds
                logging.warning(f"Database connection pool exhausted, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise  # Re-raise if not connection pool issue or final attempt


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
