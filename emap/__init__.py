import os

# Import the original SQLite implementation as the default
from .db import NetlistDB as SQLiteNetlistDB

# Import PostgreSQL implementation when needed
try:
    from .db_postgres import NetlistDB as PostgreSQLNetlistDB
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from . import rewrites
from . import extracts


def NetlistDB(schema_file: str, db_file_or_config=None, cnt: int = 0, backend: str = None):
    """
    NetlistDB factory function that routes to the appropriate backend.

    Args:
        schema_file: Path to the database schema file
        db_file_or_config: For SQLite: db file path. For PostgreSQL: config dict or 'postgres'.
        cnt: Initial counter value
        backend: Database backend ('sqlite' or 'postgres'). If None, auto-detect.

    Returns:
        NetlistDB instance
    """
    if backend is None:
        # Auto-detect backend
        if isinstance(db_file_or_config, dict) or db_file_or_config == 'postgres':
            backend = 'postgres'
        else:
            backend = os.environ.get('EMAP_DB_BACKEND', 'sqlite')

    # Auto-select appropriate schema file
    base_dir = os.path.dirname(schema_file) if os.path.dirname(schema_file) else os.path.dirname(__file__)

    if backend == 'sqlite':
        # Use SQLite-specific schema
        sqlite_schema = os.path.join(base_dir, 'schema_sqlite.sql')
        if os.path.exists(sqlite_schema):
            schema_file = sqlite_schema

        db_file = db_file_or_config if isinstance(db_file_or_config, str) else ":memory:"
        return SQLiteNetlistDB(schema_file, db_file, cnt)
    elif backend == 'postgres':
        if not POSTGRES_AVAILABLE:
            raise ImportError("PostgreSQL backend not available. Missing dependencies or implementation.")

        # Auto-generate PostgreSQL schema from SQLite schema if needed
        postgres_schema = os.path.join(base_dir, 'schema_postgres.sql')
        sqlite_schema = os.path.join(base_dir, 'schema_sqlite.sql')

        # If we have SQLite schema but no PostgreSQL schema, generate it
        if os.path.exists(sqlite_schema) and not os.path.exists(postgres_schema):
            try:
                from .schema_converter import generate_postgres_schema
                generate_postgres_schema(sqlite_schema, postgres_schema)
            except ImportError:
                pass  # Fall back to using provided schema

        # Use PostgreSQL schema if it exists
        if os.path.exists(postgres_schema):
            schema_file = postgres_schema

        db_config = db_file_or_config if isinstance(db_file_or_config, dict) else None
        return PostgreSQLNetlistDB(schema_file, db_config, cnt)
    else:
        raise ValueError(f"Unsupported backend: {backend}. Must be 'sqlite' or 'postgres'")


# For backward compatibility, also expose the original class name
__all__ = ['NetlistDB', 'rewrites', 'extracts']