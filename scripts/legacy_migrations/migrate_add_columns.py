"""
Migration: Adiciona colunas faltantes na tabela equipments
"""
import asyncio
import asyncpg

async def migrate():
    # Conectar ao banco
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='110812',
        database='isp_monitor'
    )
    
    try:
        print("[Migration] Verificando colunas faltantes...")
        
        # Verificar se coluna last_ping existe
        result = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='equipments' AND column_name='last_ping'
        """)
        
        if not result:
            print("[Migration] Adicionando coluna 'last_ping'...")
            await conn.execute("""
                ALTER TABLE equipments 
                ADD COLUMN IF NOT EXISTS last_ping FLOAT
            """)
            print("[Migration] ✅ Coluna 'last_ping' adicionada!")
        else:
            print("[Migration] ✅ Coluna 'last_ping' já existe!")
        
        # Verificar outras colunas que podem estar faltando
        columns_to_add = [
            ("last_latency", "FLOAT"),
            ("last_traffic_in", "BIGINT"),
            ("last_traffic_out", "BIGINT"),
            ("signal_dbm", "INTEGER"),
            ("ccq", "INTEGER"),
            ("connected_clients", "INTEGER"),
        ]
        
        for col_name, col_type in columns_to_add:
            result = await conn.fetchval(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='equipments' AND column_name='{col_name}'
            """)
            
            if not result:
                print(f"[Migration] Adicionando coluna '{col_name}'...")
                await conn.execute(f"""
                    ALTER TABLE equipments 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                """)
                print(f"[Migration] ✅ Coluna '{col_name}' adicionada!")
        
        print("[Migration] ✅ Migration concluída com sucesso!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
