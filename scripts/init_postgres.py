import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import asyncio
import os
import sys

# Adiciona raiz ao path para importar backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_USER = "postgres"
DB_PASS = "110812"
DB_HOST = "localhost"
DB_PORT = "5432"
TARGET_DB = "monitor_prod"

def create_database():
    """Connect to default 'postgres' db and create 'monitor_prod' if needed."""
    print(f"🔌 Conectando ao PostgreSQL local ({DB_USER})...")
    try:
        con = psycopg2.connect(
            dbname="postgres", user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{TARGET_DB}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"🆕 Criando banco de dados '{TARGET_DB}'...")
            cur.execute(f"CREATE DATABASE {TARGET_DB}")
            print("✅ Banco criado com sucesso.")
        else:
            print(f"ℹ️ Banco '{TARGET_DB}' já existe.")
            
        cur.close()
        con.close()
        return True
    except Exception as e:
        print(f"❌ Falha ao conectar/criar banco: {e}")
        print("Verifique se o PostgreSQL está rodando e a senha está correta.")
        return False

async def create_schema():
    """Use SQLAlchemy to create tables in the new DB."""
    print("🏗️ Criando tabelas (Schema)...")
    
    # Configura URL para o database.py usar
    pg_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{TARGET_DB}"
    os.environ["DATABASE_URL"] = pg_url
    
    try:
        from backend.app.database import engine, Base
        from backend.app import models # Importar models para registrar no Base
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tabelas criadas com sucesso.")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar schema: {e}")
        return False

if __name__ == "__main__":
    if create_database():
        # Precisa rodar async
        asyncio.run(create_schema())
