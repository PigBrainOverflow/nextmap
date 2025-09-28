"""
Database configuration module for EMAP.

This module provides utilities for configuring database backends.
Users can set environment variables or use this module to configure the database backend.
"""

import os
from typing import Dict, Any, Optional


class DatabaseConfig:
    """Database configuration management"""

    @staticmethod
    def set_sqlite_backend(db_file: str = ":memory:"):
        """Configure SQLite backend"""
        os.environ['EMAP_DB_BACKEND'] = 'sqlite'
        os.environ['EMAP_SQLITE_FILE'] = db_file
        print(f"Database backend set to SQLite with file: {db_file}")

    @staticmethod
    def set_postgres_backend(database: str = 'nextmap_temp',
                           host: Optional[str] = None,
                           port: Optional[int] = None,
                           user: Optional[str] = None,
                           password: Optional[str] = None):
        """Configure PostgreSQL backend"""
        os.environ['EMAP_DB_BACKEND'] = 'postgres'
        os.environ['EMAP_POSTGRES_DATABASE'] = database

        if host:
            os.environ['EMAP_POSTGRES_HOST'] = host
        if port:
            os.environ['EMAP_POSTGRES_PORT'] = str(port)
        if user:
            os.environ['EMAP_POSTGRES_USER'] = user
        if password:
            os.environ['EMAP_POSTGRES_PASSWORD'] = password

        print(f"Database backend set to PostgreSQL with database: {database}")

    @staticmethod
    def get_current_backend() -> str:
        """Get currently configured backend"""
        return os.environ.get('EMAP_DB_BACKEND', 'sqlite')

    @staticmethod
    def get_sqlite_config() -> Dict[str, Any]:
        """Get SQLite configuration from environment"""
        return {
            'db_file': os.environ.get('EMAP_SQLITE_FILE', ':memory:')
        }

    @staticmethod
    def get_postgres_config() -> Dict[str, Any]:
        """Get PostgreSQL configuration from environment"""
        config = {
            'database': os.environ.get('EMAP_POSTGRES_DATABASE', 'nextmap_temp')
        }

        if 'EMAP_POSTGRES_HOST' in os.environ:
            config['host'] = os.environ['EMAP_POSTGRES_HOST']
        if 'EMAP_POSTGRES_PORT' in os.environ:
            config['port'] = int(os.environ['EMAP_POSTGRES_PORT'])
        if 'EMAP_POSTGRES_USER' in os.environ:
            config['user'] = os.environ['EMAP_POSTGRES_USER']
        if 'EMAP_POSTGRES_PASSWORD' in os.environ:
            config['password'] = os.environ['EMAP_POSTGRES_PASSWORD']

        # If no user specified, use current system user
        if 'user' not in config:
            import getpass
            config['user'] = getpass.getuser()

        return config

    @staticmethod
    def print_current_config():
        """Print current database configuration"""
        backend = DatabaseConfig.get_current_backend()
        print(f"Current database backend: {backend}")

        if backend == 'sqlite':
            config = DatabaseConfig.get_sqlite_config()
            print(f"SQLite file: {config['db_file']}")
        elif backend == 'postgres':
            config = DatabaseConfig.get_postgres_config()
            print(f"PostgreSQL config: {config}")


# Example usage functions
def use_sqlite_memory():
    """Configure to use in-memory SQLite database"""
    DatabaseConfig.set_sqlite_backend()

def use_sqlite_file(filename: str):
    """Configure to use file-based SQLite database"""
    DatabaseConfig.set_sqlite_backend(filename)

def use_postgres_local(database: str = 'nextmap_temp'):
    """Configure to use local PostgreSQL database"""
    DatabaseConfig.set_postgres_backend(database=database)

def use_postgres_remote(host: str, port: int, database: str, user: str, password: str = None):
    """Configure to use remote PostgreSQL database"""
    DatabaseConfig.set_postgres_backend(
        database=database,
        host=host,
        port=port,
        user=user,
        password=password
    )


if __name__ == "__main__":
    # Print current configuration
    DatabaseConfig.print_current_config()

    print("\nExample configurations:")
    print("1. In-memory SQLite:")
    print("   from database_config import use_sqlite_memory")
    print("   use_sqlite_memory()")

    print("\n2. File-based SQLite:")
    print("   from database_config import use_sqlite_file")
    print("   use_sqlite_file('my_database.db')")

    print("\n3. Local PostgreSQL:")
    print("   from database_config import use_postgres_local")
    print("   use_postgres_local('my_database')")

    print("\n4. Remote PostgreSQL:")
    print("   from database_config import use_postgres_remote")
    print("   use_postgres_remote('localhost', 5432, 'my_db', 'user', 'password')")