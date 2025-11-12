#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
"""
import sqlite3
import psycopg2
from pathlib import Path
import sys

def migrate():
    sqlite_db = Path("data/full_intelligence.db")
    pg_url = "postgresql://postgres:@localhost:5432/comversa_rag"
    
    if not sqlite_db.exists():
        print(f"❌ SQLite database not found: {sqlite_db}")
        return
    
    print(f"📊 Migrating from {sqlite_db} to PostgreSQL")
    print()
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(str(sqlite_db))
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get all tables
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    print(f"📋 Tables to migrate: {len(tables)}")
    for table in tables:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = sqlite_cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    print()
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(pg_url)
        pg_cursor = pg_conn.cursor()
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return
    
    # Migrate each table
    print()
    print("🔄 Migrating data...")
    for table in tables:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = sqlite_cursor.fetchone()[0]
        
        if count == 0:
            print(f"  ⊘ {table}: skipped (empty)")
            continue
        
        try:
            # Get schema
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in sqlite_cursor.fetchall()]
            
            # Read all data
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            # Create table in PostgreSQL if not exists
            col_names = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))
            
            # Insert data
            insert_query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
            pg_cursor.executemany(insert_query, rows)
            pg_conn.commit()
            
            print(f"  ✅ {table}: {count} rows migrated")
        except Exception as e:
            print(f"  ❌ {table}: {str(e)[:100]}")
            pg_conn.rollback()
    
    print()
    print("✅ Migration complete!")
    
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
