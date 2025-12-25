"""
Migration: Add connected_clients column to equipments table
"""
import sqlite3
import os

DB_PATH = "monitor.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add connected_clients column
        cursor.execute("ALTER TABLE equipments ADD COLUMN connected_clients INTEGER DEFAULT 0")
        conn.commit()
        print("[SUCCESS] ✅ Column 'connected_clients' added to 'equipments' table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("[INFO] ℹ️  Column 'connected_clients' already exists")
        else:
            print(f"[ERROR] ❌ {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🔄 MIGRATION: Add connected_clients column")
    print("="*60)
    migrate()
    print("="*60)
