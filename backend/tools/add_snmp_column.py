import sqlite3
import os

db_path = 'monitor.db'

if not os.path.exists(db_path):
    print("Banco de dados nao encontrado.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE equipments ADD COLUMN snmp_interface_index INTEGER DEFAULT 1")
    conn.commit()
    print("[MIGRATION] Coluna 'snmp_interface_index' adicionada com sucesso à tabela 'equipments'.")
except Exception as e:
    if "duplicate column name" in str(e):
        print("[MIGRATION] Coluna 'snmp_interface_index' ja existe.")
    else:
        print(f"[MIGRATION] Erro ao adicionar coluna: {e}")

conn.close()
