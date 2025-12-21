import sqlite3
import os

DB_PATH = "monitor.db"

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found. It will be created on first run.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add last_latency to equipments
    try:
        cursor.execute("ALTER TABLE equipments ADD COLUMN last_latency INTEGER")
        print("Added last_latency to equipments.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("last_latency already exists in equipments.")
        else:
            print(f"Error adding last_latency: {e}")

    # Add latency_ms to ping_logs
    try:
        cursor.execute("ALTER TABLE ping_logs ADD COLUMN latency_ms INTEGER")
        print("Added latency_ms to ping_logs.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("latency_ms already exists in ping_logs.")
        else:
            print(f"Error adding latency_ms: {e}")

    # Create network_links table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_tower_id INTEGER,
                target_tower_id INTEGER,
                type VARCHAR,
                FOREIGN KEY(source_tower_id) REFERENCES towers(id),
                FOREIGN KEY(target_tower_id) REFERENCES towers(id)
            )
        """)
        print("Ensured network_links table exists.")
    except Exception as e:
        print(f"Error creating network_links: {e}")

    # Add SSH cols to equipments
    try:
        cursor.execute("ALTER TABLE equipments ADD COLUMN ssh_user VARCHAR DEFAULT 'admin'")
        cursor.execute("ALTER TABLE equipments ADD COLUMN ssh_password VARCHAR")
        cursor.execute("ALTER TABLE equipments ADD COLUMN ssh_port INTEGER DEFAULT 22")
        print("Added SSH columns to equipments.")
    except sqlite3.OperationalError:
        pass # Already exists

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
