import sqlite3
import os

db_path = 'monitor.db'

if not os.path.exists(db_path):
    print("Banco de dados nao encontrado.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Desativando modo Mikrotik API em todos os equipamentos...")
    cursor.execute("UPDATE equipments SET is_mikrotik = 0")
    conn.commit()
    changes = cursor.rowcount
    print(f"Sucesso! {changes} equipamentos atualizados para modo SNMP padrão.")
except Exception as e:
    print(f"Erro: {e}")

conn.close()
