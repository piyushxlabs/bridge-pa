import os
import sys
import argparse
import asyncio
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Load configuration from environment or use defaults
POSTGRESQL_CONNECTION_STRING = os.getenv(
    "POSTGRESQL_CONNECTION_STRING", 
    "postgresql://postgres:postgres@localhost:5432/pa_agent_db"
)

def fix_connection_string(conn_str: str) -> str:
    if conn_str.startswith("postgresql+asyncpg://"):
        conn_str = conn_str.replace("postgresql+asyncpg://", "postgresql://")
    if conn_str.count('@') > 1:
        # URL-encode all '@' symbols except the last one which separates credentials from host
        parts = conn_str.rsplit('@', 1)
        parts[0] = parts[0].replace('@', '%40')
        conn_str = '@'.join(parts)
    return conn_str

POSTGRESQL_CONNECTION_STRING = fix_connection_string(POSTGRESQL_CONNECTION_STRING)

# Set correct event loop policy for Windows to avoid ProactorEventLoop error with psycopg
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Global async connection pool
_pool = None

async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Creates and returns an AsyncPostgresSaver using the configured PostgreSQL connection string.
    """
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=POSTGRESQL_CONNECTION_STRING,
            max_size=20,
            kwargs={"autocommit": True, "prepare_threshold": 0},
            open=False
        )
        await _pool.open()
    return AsyncPostgresSaver(_pool)

async def setup_checkpointer():
    """
    Initializes the PostgreSQL database with the necessary LangGraph checkpoint tables.
    """
    print(f"Connecting to: {POSTGRESQL_CONNECTION_STRING}")
    checkpointer = await get_checkpointer()
    print("Setting up LangGraph checkpoint tables...")
    await checkpointer.setup()
    print("Checkpoint tables created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize PostgreSQL Checkpointer")
    parser.add_argument("--setup", action="store_true", help="Setup LangGraph checkpoint tables")
    args = parser.parse_args()

    if args.setup:
        # Check if python-dotenv is needed for local CLI execution
        try:
            from dotenv import load_dotenv
            load_dotenv()
            POSTGRESQL_CONNECTION_STRING = os.getenv(
                "POSTGRESQL_CONNECTION_STRING", 
                "postgresql://postgres:postgres@localhost:5432/pa_agent_db"
            )
            POSTGRESQL_CONNECTION_STRING = fix_connection_string(POSTGRESQL_CONNECTION_STRING)
        except ImportError:
            pass
            
        asyncio.run(setup_checkpointer())
