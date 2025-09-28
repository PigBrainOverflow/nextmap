import os
from typing import Dict, Any, Optional

# Import the new unified interface
from .db_interface import NetlistDB as UnifiedNetlistDB

# Import the legacy implementations for backward compatibility
from .db import NetlistDB as PostgreSQLNetlistDB
from .db_sqlite import NetlistDB as SQLiteNetlistDB
from .db_postgres import NetlistDB as PostgreSQLNetlistDBCompat

from . import rewrites
from . import extracts


def create_netlist_db(schema_file: str, backend: str = None, **config) -> UnifiedNetlistDB:
    """
    Factory function to create a NetlistDB instance with the specified backend.

    Args:
        schema_file: Path to the database schema file
        backend: Database backend ('sqlite' or 'postgres'). If None, auto-detect from environment.
        **config: Backend-specific configuration options

    Returns:
        NetlistDB instance using the specified backend
    """
    if backend is None:
        # Auto-detect backend from environment
        backend = os.environ.get('EMAP_DB_BACKEND', 'sqlite')

    if backend not in ('sqlite', 'postgres'):
        raise ValueError(f"Unsupported backend: {backend}. Must be 'sqlite' or 'postgres'")

    return UnifiedNetlistDB(schema_file, backend=backend, **config)


def NetlistDB(schema_file: str, db_file_or_config=None, cnt: int = 0, backend: str = None):
    """
    Backward-compatible NetlistDB factory function.

    Args:
        schema_file: Path to the database schema file
        db_file_or_config: For SQLite: db file path. For PostgreSQL: config dict. If None, use defaults.
        cnt: Initial counter value
        backend: Database backend. If None, auto-detect.

    Returns:
        NetlistDB instance
    """
    if backend is None:
        # Auto-detect backend
        if isinstance(db_file_or_config, dict):
            backend = 'postgres'
        elif isinstance(db_file_or_config, str) or db_file_or_config is None:
            backend = os.environ.get('EMAP_DB_BACKEND', 'sqlite')
        else:
            backend = 'sqlite'

    if backend == 'sqlite':
        db_file = db_file_or_config if isinstance(db_file_or_config, str) else ":memory:"
        return SQLiteNetlistDB(schema_file, db_file, cnt)
    elif backend == 'postgres':
        db_config = db_file_or_config if isinstance(db_file_or_config, dict) else None
        return PostgreSQLNetlistDBCompat(schema_file, db_config, cnt)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


# For backward compatibility, also expose the original class name
__all__ = ['NetlistDB', 'create_netlist_db', 'rewrites', 'extracts']