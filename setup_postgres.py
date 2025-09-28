#!/usr/bin/env python3
"""
Setup script for postgres database for nextmap testing
"""

import psycopg2
import sys

def try_create_database():
    """Try different connection methods to create the database"""

    import os
    current_user = os.getenv('USER', 'jbalkind')

    # Connection configs to try in order
    connection_configs = [
        # Try peer authentication with current user (Unix socket)
        {
            'database': 'postgres',  # Connect to default db first
            'user': current_user,
        },
        # Try peer authentication (Unix socket) with postgres user
        {
            'database': 'postgres',  # Connect to default db first
            'user': 'postgres',
        },
        # Try localhost with current user
        {
            'database': 'postgres',
            'user': current_user,
            'host': 'localhost',
            'port': '5432',
        },
        # Try localhost with no password
        {
            'database': 'postgres',
            'user': 'postgres',
            'host': 'localhost',
            'port': '5432',
        },
        # Try with empty password
        {
            'database': 'postgres',
            'user': 'postgres',
            'host': 'localhost',
            'port': '5432',
            'password': '',
        }
    ]

    for i, config in enumerate(connection_configs):
        try:
            print(f"Trying connection method {i+1}...")
            conn = psycopg2.connect(**config)
            conn.autocommit = True
            cur = conn.cursor()

            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'nextmap_test'")
            if cur.fetchone():
                print("Database 'nextmap_test' already exists!")
            else:
                # Create the database
                cur.execute("CREATE DATABASE nextmap_test")
                print("Created database 'nextmap_test' successfully!")

            cur.close()
            conn.close()
            return config  # Return the working config

        except psycopg2.OperationalError as e:
            print(f"Connection method {i+1} failed: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error with method {i+1}: {e}")
            continue

    print("All connection methods failed!")
    return None

if __name__ == "__main__":
    working_config = try_create_database()
    if working_config:
        print(f"\nWorking configuration: {working_config}")
        print("You can now run test_cbc_demo.py")
    else:
        print("\nCould not connect to postgres. You may need to:")
        print("1. Set a password for the postgres user")
        print("2. Modify pg_hba.conf authentication settings")
        print("3. Or run postgres setup commands as the postgres system user")