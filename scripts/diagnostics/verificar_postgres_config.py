"""
Verifica configurações do PostgreSQL - Versão corrigida
"""
import sys
import os

# Configurar DATABASE_URL para PostgreSQL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:110812@localhost:5432/monitor_prod"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from backend.app.database import AsyncSessionLocal

async def verificar_config():
    """Verifica configurações do PostgreSQL"""
    
    configs = [
        "shared_buffers",
        "effective_cache_size",
        "work_mem",
        "maintenance_work_mem",
        "wal_buffers",
        "max_wal_size",
        "random_page_cost",
        "effective_io_concurrency",
        "autovacuum_vacuum_scale_factor",
        "autovacuum_analyze_scale_factor"
    ]
    
    try:
        async with AsyncSessionLocal() as session:
            print("\n" + "="*80)
            print("CONFIGURAÇÕES POSTGRESQL")
            print("="*80)
            
            for config in configs:
                query = text(f"SHOW {config};")
                result = await session.execute(query)
                value = result.scalar()
                
                # Valores recomendados
                recomendado = {
                    "shared_buffers": "2GB",
                    "effective_cache_size": "6GB",
                    "work_mem": "16MB",
                    "maintenance_work_mem": "512MB",
                    "wal_buffers": "16MB",
                    "max_wal_size": "4GB",
                    "random_page_cost": "1.1",
                    "effective_io_concurrency": "200",
                    "autovacuum_vacuum_scale_factor": "0.05",
                    "autovacuum_analyze_scale_factor": "0.02"
                }
                
                rec = recomendado.get(config, "N/A")
                status = "✅" if str(value) == rec else "⚠️"
                
                print(f"\n{status} {config}")
                print(f"   Atual: {value}")
                print(f"   Recomendado: {rec}")
            
            print("\n" + "="*80)
            print("\n💡 Se valores diferentes, aplicar postgresql.conf.optimized")
            print("   Ver: docs/APLICAR_POSTGRESQL_OTIMIZADO.md")
            print("\n")
            
    except Exception as e:
        print(f"\n❌ ERRO ao conectar no PostgreSQL:")
        print(f"   {e}")
        print("\n💡 Verifique se PostgreSQL está rodando")
        print("\n")

if __name__ == "__main__":
    asyncio.run(verificar_config())
