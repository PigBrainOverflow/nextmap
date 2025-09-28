#!/usr/bin/env python3
"""
Schema converter to automatically generate PostgreSQL schema from SQLite schema.
This ensures we only maintain the SQLite schema and automatically generate PostgreSQL.
"""

import re
import os


def convert_sqlite_to_postgres_schema(sqlite_schema_content: str) -> str:
    """
    Convert SQLite schema to PostgreSQL schema.

    Args:
        sqlite_schema_content: Content of the SQLite schema file

    Returns:
        PostgreSQL-compatible schema content
    """
    postgres_schema = sqlite_schema_content

    # 1. Convert PRIMARY KEY AUTOINCREMENT to SERIAL PRIMARY KEY
    postgres_schema = re.sub(
        r'id\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT',
        'id SERIAL PRIMARY KEY',
        postgres_schema,
        flags=re.IGNORECASE
    )

    # 2. Convert INTEGER hash to BIGINT hash (for better hash storage)
    postgres_schema = re.sub(
        r'hash\s+INTEGER\s+NOT\s+NULL',
        'hash BIGINT NOT NULL',
        postgres_schema,
        flags=re.IGNORECASE
    )

    # 3. Convert JSON to JSONB for better PostgreSQL performance
    postgres_schema = re.sub(
        r'params\s+JSON',
        'params JSONB',
        postgres_schema,
        flags=re.IGNORECASE
    )

    # 4. Enable CASCADE DELETE where commented out
    postgres_schema = re.sub(
        r'FOREIGN KEY \(wirevec\) REFERENCES wirevecs\(id\)\s+-- ON DELETE CASCADE',
        'FOREIGN KEY (wirevec) REFERENCES wirevecs(id) ON DELETE CASCADE',
        postgres_schema,
        flags=re.IGNORECASE
    )

    # 5. Update comments to reflect PostgreSQL-specific optimizations
    postgres_schema = re.sub(
        r'-- no need to process this, just store it',
        '-- PostgreSQL JSONB for better performance',
        postgres_schema
    )

    return postgres_schema


def generate_postgres_schema(sqlite_schema_path: str, postgres_schema_path: str = None) -> str:
    """
    Generate PostgreSQL schema file from SQLite schema file.

    Args:
        sqlite_schema_path: Path to the SQLite schema file
        postgres_schema_path: Path where to save PostgreSQL schema (optional)

    Returns:
        Path to the generated PostgreSQL schema file
    """
    # Read SQLite schema
    with open(sqlite_schema_path, 'r') as f:
        sqlite_content = f.read()

    # Convert to PostgreSQL
    postgres_content = convert_sqlite_to_postgres_schema(sqlite_content)

    # Add header comment
    header = f"""-- Auto-generated PostgreSQL schema from {os.path.basename(sqlite_schema_path)}
-- Do not edit manually - run schema_converter.py to regenerate

"""
    postgres_content = header + postgres_content

    # Determine output path
    if postgres_schema_path is None:
        base_dir = os.path.dirname(sqlite_schema_path)
        postgres_schema_path = os.path.join(base_dir, 'schema_postgres.sql')

    # Write PostgreSQL schema
    with open(postgres_schema_path, 'w') as f:
        f.write(postgres_content)

    print(f"✅ Generated PostgreSQL schema: {postgres_schema_path}")
    return postgres_schema_path


def main():
    """Generate PostgreSQL schema from SQLite schema."""
    import argparse

    parser = argparse.ArgumentParser(description='Convert SQLite schema to PostgreSQL schema')
    parser.add_argument('sqlite_schema', help='Path to SQLite schema file')
    parser.add_argument('--output', '-o', help='Output path for PostgreSQL schema')

    args = parser.parse_args()

    generate_postgres_schema(args.sqlite_schema, args.output)


if __name__ == '__main__':
    main()