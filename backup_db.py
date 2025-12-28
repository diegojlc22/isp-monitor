
import os
import datetime
import subprocess

DATABASE_NAME = "isp_monitor"
BACKUP_DIR = "backups"

def backup_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{DATABASE_NAME}_{timestamp}.sql")
    
    # Using pg_dump
    # Note: Requires pg_dump in PATH or specify full path
    command = f"pg_dump -U postgres -h localhost {DATABASE_NAME} > {backup_file}"
    
    # Set PGPASSWORD environment variable just for this command
    env = os.environ.copy()
    env["PGPASSWORD"] = "110812"
    
    try:
        # Use shell=True for redirection to work easily
        subprocess.run(command, shell=True, env=env, check=True)
        print(f"✅ Backup created: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    backup_database()
