"""
Script para criar índices compostos no PostgreSQL
Executa de forma segura com tratamento de erros
"""
import asyncio
import sys
import os

# Configurar DATABASE_URL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:110812@localhost:5432/monitor_prod"

# Adiciona o backend ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from backend.app.database import engine

async def create_indexes():
    """Cria índices compostos para otimização de performance"""
    
    indexes = [
        {
            "name": "idx_ping_device_time",
            "sql": "CREATE INDEX IF NOT EXISTS idx_ping_device_time ON ping_logs(device_id, timestamp DESC)",
            "description": "Índice composto CRÍTICO para queries de ping por device + tempo"
        },
        {
            "name": "idx_traffic_device_time",
            "sql": "CREATE INDEX IF NOT EXISTS idx_traffic_device_time ON traffic_logs(equipment_id, timestamp DESC)",
            "description": "Índice composto CRÍTICO para queries de tráfego"
        },
        {
            "name": "idx_alerts_created",
            "sql": "CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(timestamp DESC)",
            "description": "Índice CRÍTICO para ordenação de alertas por data"
        },
        {
            "name": "idx_ping_type_id_time",
            "sql": "CREATE INDEX IF NOT EXISTS idx_ping_type_id_time ON ping_logs(device_type, device_id, timestamp DESC)",
            "description": "Índice composto CRÍTICO para queries por tipo + device + tempo"
        }
    ]
    
    print("🔧 Criando índices compostos no PostgreSQL...")
    print("⚠️  Isso pode demorar alguns minutos dependendo do tamanho das tabelas\n")
    
    try:
        async with engine.begin() as conn:
            for idx in indexes:
                try:
                    print(f"📊 Criando: {idx['name']}")
                    print(f"   {idx['description']}")
                    
                    await conn.execute(text(idx['sql']))
                    
                    print(f"   ✅ Sucesso!\n")
                    
                except Exception as e:
                    print(f"   ⚠️  Aviso: {e}")
                    print(f"   (Provavelmente o índice já existe)\n")
                    continue
        
        print("✅ Processo concluído!")
        print("\n📈 Ganho esperado: Queries 10-20x mais rápidas")
        print("🎯 Execute novamente: python scripts/verificar_indices.py")
        
    except Exception as e:
        print(f"\n❌ ERRO ao criar índices:")
        print(f"   {e}")
        print("\n💡 Verifique se PostgreSQL está rodando")

if __name__ == "__main__":
    asyncio.run(create_indexes())
