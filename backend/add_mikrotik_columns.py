import sqlite3
import os

db_path = 'monitor.db'

if not os.path.exists(db_path):
    print("Banco de dados nao encontrado.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

columns = [
    ("is_mikrotik", "BOOLEAN DEFAULT 0"),
    ("mikrotik_interface", "TEXT"),
    ("api_port", "INTEGER DEFAULT 8728")
]

for col, dtype in columns:
    try:
        cursor.execute(f"ALTER TABLE equipments ADD COLUMN {col} {dtype}")
        conn.commit()
        print(f"[MIGRATION] Coluna '{col}' adicionada com sucesso.")
    except Exception as e:
        if "duplicate column name" in str(e):
            print(f"[MIGRATION] Coluna '{col}' ja existe.")
        else:
            print(f"[MIGRATION] Erro ao adicionar coluna '{col}': {e}")

conn.close()
