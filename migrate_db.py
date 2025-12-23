import sqlite3
import os

DB_PATH = "monitor.db"

def migrate():
    print("Iniciando migração de banco de dados...")
    
    if not os.path.exists(DB_PATH):
        print("Banco de dados não encontrado. Nada a migrar.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lista de colunas para verificar/adicionar
    # Tabela: (Coluna, Tipo)
    migrations = {
        "equipments": [
            ("parent_id", "INTEGER"),
            ("snmp_community", "TEXT DEFAULT 'public'"),
            ("snmp_version", "INTEGER DEFAULT 2"),
            ("snmp_port", "INTEGER DEFAULT 161"),
            ("last_traffic_in", "REAL"),
            ("last_traffic_out", "REAL")
        ],
        "towers": [
            ("parent_id", "INTEGER")
        ]
    }

    for table, columns in migrations.items():
        print(f"Verificando tabela {table}...")
        try:
            # Pega info das colunas atuais
            cursor.execute(f"PRAGMA table_info({table})")
            existing_cols = [row[1] for row in cursor.fetchall()]
            
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    print(f"  -> Adicionando coluna '{col_name}' em '{table}'...")
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    except sqlite3.OperationalError as e:
                        print(f"     Erro ao adicionar {col_name}: {e}")
                else:
                    print(f"  -> Coluna '{col_name}' já existe.")
                    
        except sqlite3.OperationalError:
            print(f"  Tabela {table} não encontrada ou erro de acesso.")

    conn.commit()
    conn.close()
    print("Migração concluída com sucesso.")

if __name__ == "__main__":
    migrate()
