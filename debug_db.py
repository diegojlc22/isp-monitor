import asyncio
import asyncpg
import sys

async def check():
    try:
        conn = await asyncpg.connect("postgresql://postgres:110812@127.0.0.1:5432/postgres")
        print("✅ Conexão com 'postgres' OK")
        
        rows = await conn.fetch("SELECT datname FROM pg_database")
        dbs = [r['datname'] for r in rows]
        print(f"Databases: {dbs}")
        
        if 'isp_monitor' in dbs:
            print("✅ Database 'isp_monitor' existe.")
            await conn.close()
            conn2 = await asyncpg.connect("postgresql://postgres:110812@127.0.0.1:5432/isp_monitor")
            print("✅ Conexão com 'isp_monitor' OK")
            await conn2.close()
        else:
            print("❌ Database 'isp_monitor' NÃO ENCONTRADA.")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(check())
