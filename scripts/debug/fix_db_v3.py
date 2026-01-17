
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_database():
    conn_params = {
        "host": "127.0.0.1",
        "port": 5432,
        "database": "isp_monitor",
        "user": "postgres",
        "password": "110812"
    }
    
    queries = [
        # 1. Adicionar coluna ai_overrides se não existir
        """
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='ai_overrides') THEN
                ALTER TABLE equipments ADD COLUMN ai_overrides JSONB DEFAULT '{}';
                RAISE NOTICE 'Coluna ai_overrides adicionada.';
            END IF;
        END $$;
        """,
        # 2. Criar tabela signal_logs se não existir
        """
        CREATE TABLE IF NOT EXISTS signal_logs (
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipments(id) ON DELETE CASCADE,
            rssi FLOAT,
            ccq INTEGER,
            noise_floor INTEGER,
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
        );
        """,
        # 3. Criar índice para performance
        "CREATE INDEX IF NOT EXISTS idx_signal_logs_equipment_timestamp ON signal_logs(equipment_id, timestamp);"
    ]
    
    print("📡 Iniciando atualização forçada via PSYCOPG2 (Sync)...")
    
    try:
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        for query in queries:
            cur.execute(query)
            print(f"✅ Executado: {query.strip()[:60]}...")
            
        cur.close()
        conn.close()
        print("🚀 Banco de dados atualizado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao atualizar banco: {e}")

if __name__ == "__main__":
    fix_database()
