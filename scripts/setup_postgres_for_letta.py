#!/usr/bin/env python3
"""
Create the 'letta' role and database for the Letta server (no psql required).
Run with: python scripts/setup_postgres_for_letta.py

Requires PostgreSQL running locally. Uses default connection (current user,
localhost:5432, database 'postgres') so you need superuser or CREATEROLE.
"""
import asyncio
import os
import sys

try:
    import asyncpg
except ImportError:
    print("asyncpg not installed. Run: pip install asyncpg", file=sys.stderr)
    sys.exit(1)


async def main() -> None:
    # Connect as superuser to default DB (peer/trust auth often allows current user)
    user = os.environ.get("PGUSER", os.environ.get("USER", "postgres"))
    try:
        conn = await asyncpg.connect(
            host=os.environ.get("PGHOST", "localhost"),
            port=int(os.environ.get("PGPORT", "5432")),
            user=user,
            database="postgres",
            password=os.environ.get("PGPASSWORD"),
        )
    except Exception as e:
        print(f"Cannot connect to PostgreSQL: {e}", file=sys.stderr)
        print("Ensure PostgreSQL is running and you can connect (e.g. as current user or postgres).", file=sys.stderr)
        sys.exit(1)

    try:
        await conn.execute("CREATE ROLE letta WITH LOGIN PASSWORD 'letta'")
        print("Created role 'letta'.")
    except asyncpg.DuplicateObjectError:
        print("Role 'letta' already exists.")
    except Exception as e:
        print(f"Creating role failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        await conn.execute("CREATE DATABASE letta OWNER letta")
        print("Created database 'letta'.")
    except asyncpg.DuplicateObjectError:
        print("Database 'letta' already exists.")
    except Exception as e:
        print(f"Creating database failed: {e}", file=sys.stderr)
        sys.exit(1)

    await conn.close()

    conn_letta = await asyncpg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        user=user,
        database="letta",
        password=os.environ.get("PGPASSWORD"),
    )
    try:
        await conn_letta.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("Enabled pgvector in database 'letta'.")
    except Exception as e:
        print(f"pgvector not installed: {e}", file=sys.stderr)
        print("Optional: brew install pgvector, then restart Postgres.", file=sys.stderr)
    finally:
        await conn_letta.close()

    print("Done. Start the Letta server with: letta server")


if __name__ == "__main__":
    asyncio.run(main())
