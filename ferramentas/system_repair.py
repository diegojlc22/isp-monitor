import asyncio
import sys
import os

# Adiciona o diretório raiz para importar módulos do backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import engine
from sqlalchemy import text

async def check_and_fix_column(conn, table, column, data_type):
    """Verifica se uma coluna existe e a cria se necessário."""
    print(f"🔍 Verificando {table}.{column}...")
    
    # Check if column exists
    result = await conn.execute(text(
        f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'"
    ))
    exists = result.scalar() is not None

    if not exists:
        print(f"⚠️ Coluna {table}.{column} ausente. Criando...")
        try:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {data_type};"))
            print(f"✅ Coluna {table}.{column} criada com sucesso.")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar {table}.{column}: {e}")
            return False
    else:
        print(f"✅ {table}.{column} já existe.")
        return False

async def run_repair():
    print("=========================================")
    print("🛠️  ISP MONITOR SYSTEM REPAIR TOOL v1.0")
    print("=========================================")
    
    async with engine.begin() as conn:
        # 1. Correções na Tabela EQUIPMENTS
        await check_and_fix_column(conn, 'equipments', 'snmp_traffic_interface_index', 'INTEGER')
        await check_and_fix_column(conn, 'equipments', 'equipment_type', "VARCHAR DEFAULT 'station'")
        await check_and_fix_column(conn, 'equipments', 'snmp_interface_index', 'INTEGER')
        
        # 2. Correções na Tabela TRAFFIC_LOGS
        # Esta é crítica para o gráfico funcionar
        await check_and_fix_column(conn, 'traffic_logs', 'interface_index', 'INTEGER')
        await check_and_fix_column(conn, 'traffic_logs', 'signal_dbm', 'FLOAT')

        # 3. Fix Column Types (Migrate Integer to Float for Signal)
        try:
            await conn.execute(text("ALTER TABLE equipments ALTER COLUMN signal_dbm TYPE FLOAT USING signal_dbm::double precision"))
            print("✅ equipments.signal_dbm convertido para FLOAT.")
        except Exception as e:
            # Ignore if already float or error
            pass

    print("\n✅ Reparo concluído com sucesso!")
    print("Reinicie o sistema se necessário.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(run_repair())
    except Exception as e:
        print(f"Erro fatal: {e}")
