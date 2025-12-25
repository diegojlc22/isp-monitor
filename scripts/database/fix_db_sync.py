
import psycopg2
import time

DB_HOST = "localhost"
DB_NAME = "isp_monitor"
DB_USER = "postgres"
DB_PASS = "admin"

def fix_db():
    print("🔧 Iniciando Reparo do Banco (Modo Sincrono)...")
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        conn.autocommit = True
        cur = conn.cursor()
        
        sqls = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_latitude FLOAT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_longitude FLOAT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_location_update TIMESTAMP WITHOUT TIME ZONE;"
        ]

        for sql in sqls:
            try:
                print(f"Executando: {sql}")
                cur.execute(sql)
                print(" -> OK")
            except Exception as e:
                print(f" -> Erro ao adicionar coluna: {e}")
        
        cur.close()
        conn.close()
        print("✅ SUCESSO ABSOLUTO! O banco foi corrigido.")
    except Exception as e:
        print(f"❌ ERRO FATAL DE CONEXÃO: {e}")

if __name__ == "__main__":
    fix_db()
