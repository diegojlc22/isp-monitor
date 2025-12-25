"""
Migration: Add equipment_type column to equipments table
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
        # Add equipment_type column
        cursor.execute("ALTER TABLE equipments ADD COLUMN equipment_type TEXT DEFAULT 'station'")
        conn.commit()
        print("[SUCCESS] ✅ Column 'equipment_type' added to 'equipments' table")
        print("[INFO] Default value: 'station'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("[INFO] ℹ️  Column 'equipment_type' already exists")
        else:
            print(f"[ERROR] ❌ {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🔄 MIGRATION: Add equipment_type column")
    print("="*60)
    migrate()
    print("="*60)
