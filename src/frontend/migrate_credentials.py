#!/usr/bin/env python3
"""
Credential Migration Script
--------------------------
This script migrates user credentials from the JSON file to a SQLite database.
It reads the existing user_credentials.json file and creates a new SQLite database.
"""

import os
import json
import sqlite3
from contextlib import closing

# File paths
JSON_PATH = os.path.join(os.path.dirname(__file__), 'user_credentials.json')
DB_PATH = os.path.join(os.path.dirname(__file__), 'user_credentials.db')

def migrate_credentials():
    """Migrate credentials from JSON file to SQLite database"""
    # Check if JSON file exists
    if not os.path.exists(JSON_PATH):
        print(f"JSON file not found at {JSON_PATH}")
        return False
    
    try:
        # Load credentials from JSON
        with open(JSON_PATH, 'r') as file:
            credentials = json.load(file)
        
        # Create SQLite database and table
        with sqlite3.connect(DB_PATH) as conn:
            with closing(conn.cursor()) as cursor:
                # Create users table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
                """)
                
                # Insert users from JSON
                for username, user_data in credentials.items():
                    cursor.execute(
                        "INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)", 
                        (username, user_data["password"], user_data["role"])
                    )
                conn.commit()
                
        print(f"Successfully migrated {len(credentials)} users to SQLite database at {DB_PATH}")
        
        # Create backup of the JSON file
        backup_path = f"{JSON_PATH}.bak"
        os.rename(JSON_PATH, backup_path)
        print(f"Created backup of original JSON file at {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    print("Starting credential migration from JSON to SQLite...")
    migrate_credentials()