#!/usr/bin/env python3
"""
Test script for PostgreSQL migration of NetlistDB
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emap.db import NetlistDB

def test_postgres_connection():
    """Test basic PostgreSQL connection and schema setup"""

    # Configure PostgreSQL connection (adjust these settings as needed)
    db_config = {
        'host': 'localhost',
        'database': 'nextmap_test',
        'user': 'postgres',
        'password': '',  # Set password if needed
        'port': '5432'
    }

    schema_file = os.path.join(os.path.dirname(__file__), 'emap', 'schema.sql')

    try:
        # Test database connection and schema creation
        print("Testing PostgreSQL connection...")
        db = NetlistDB(schema_file, db_config)

        # Test basic operations
        print("Testing basic database operations...")

        # Test table creation was successful
        tables = db.tech_tables
        print(f"Tech tables found: {tables}")

        # Test simple wirevec creation
        print("Testing wirevec creation...")
        wv_id = db._add_wirevec([1, 2, 3])
        print(f"Created wirevec with ID: {wv_id}")

        # Test wirevec retrieval
        retrieved_wv = db._get_wirevec(wv_id)
        print(f"Retrieved wirevec: {retrieved_wv}")
        assert retrieved_wv == [1, 2, 3], f"Expected [1, 2, 3], got {retrieved_wv}"

        # Test input/output operations
        print("Testing input/output operations...")
        db._add_input("test_input", [1, 2])
        db._add_output("test_output", [3, 4])

        # Test database dump
        print("Testing database dump...")
        dump = db.dump_tables()
        print(f"Database dump keys: {list(dump.keys())}")

        db.close()
        print("✅ PostgreSQL migration test passed!")
        return True

    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print("Please install psycopg2: pip install psycopg2-binary")
        return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def print_migration_summary():
    """Print summary of migration changes"""
    print("\n" + "="*50)
    print("PostgreSQL Migration Summary")
    print("="*50)
    print("✅ Replaced sqlite3 with psycopg2")
    print("✅ Updated NetlistDB class structure")
    print("✅ Converted all SQL parameter placeholders (? → %s)")
    print("✅ Updated INSERT OR IGNORE → INSERT ... ON CONFLICT DO NOTHING")
    print("✅ Added proper cursor management")
    print("✅ Updated schema for PostgreSQL data types:")
    print("   - INTEGER AUTOINCREMENT → SERIAL")
    print("   - INTEGER → BIGINT for hash fields")
    print("   - JSON → JSONB for better performance")
    print("   - Enabled ON DELETE CASCADE")
    print("✅ Updated database introspection queries")
    print("✅ Updated build_from_json_cpp for PostgreSQL connection")
    print("\n📋 Requirements:")
    print("   - PostgreSQL server running")
    print("   - psycopg2-binary: pip install psycopg2-binary")
    print("   - Database 'nextmap_test' created (or update db_config)")
    print("   - Proper PostgreSQL user permissions")

if __name__ == "__main__":
    print_migration_summary()
    print("\n🧪 Running PostgreSQL migration test...")
    success = test_postgres_connection()

    if not success:
        print("\n💡 To fix connection issues:")
        print("   1. Ensure PostgreSQL is running")
        print("   2. Create database: createdb nextmap_test")
        print("   3. Update db_config in this script with correct credentials")
        print("   4. Install psycopg2: pip install psycopg2-binary")