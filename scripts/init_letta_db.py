#!/usr/bin/env python3
"""
Create all Letta tables in the database (run once after setup_postgres_for_letta.py).
Requires pgvector in Postgres: brew install pgvector, then brew services restart postgresql@15.

  python scripts/init_letta_db.py

Then start the server with: ./run_server.sh
"""
import asyncio
import os
import sys

# Load .env before importing letta so LETTA_PG_URI is set
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
env_path = os.path.join(project_dir, ".env")
if os.path.isfile(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from letta.database_utils import get_database_uri_for_context
from letta.settings import settings
from letta.orm.base import Base

# Import all ORM models so they are registered on Base.metadata
import letta.orm  # noqa: F401


async def main() -> None:
    async_pg_uri = get_database_uri_for_context(settings.letta_pg_uri, "async")
    connect_args = {}
    if "localhost" in async_pg_uri or "127.0.0.1" in async_pg_uri:
        connect_args["ssl"] = False

    # Create pgvector extension as superuser (letta user cannot)
    user = os.environ.get("PGUSER", os.environ.get("USER", "postgres"))
    pw = os.environ.get("PGPASSWORD", "")
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    superuser_uri = f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/letta" if pw else f"postgresql+asyncpg://{user}@{host}:{port}/letta"
    if "localhost" in superuser_uri:
        superuser_connect = {**connect_args, "ssl": False}
    else:
        superuser_connect = connect_args or None
    try:
        super_engine = create_async_engine(superuser_uri, connect_args=superuser_connect)
        async with super_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await super_engine.dispose()
    except Exception as e:
        if "not available" in str(e).lower() or "does not exist" in str(e).lower():
            print(
                "pgvector required. Use Postgres 17/18 (brew install postgresql@17).",
                file=sys.stderr,
            )
        raise

    # Create tables as letta user
    engine = create_async_engine(async_pg_uri, connect_args=connect_args or None)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # messages.sequence_id uses FetchedValue() but needs a Postgres default (no Alembic)
        await conn.execute(text("CREATE SEQUENCE IF NOT EXISTS messages_sequence_id_seq"))
        await conn.execute(
            text("ALTER TABLE messages ALTER COLUMN sequence_id SET DEFAULT nextval('messages_sequence_id_seq')")
        )

    await engine.dispose()
    print("Letta tables created. Start the server with: ./run_server.sh")


if __name__ == "__main__":
    asyncio.run(main())
