"""
Verifica índices do PostgreSQL - Versão corrigida
Executa com DATABASE_URL configurado
"""
import sys
import os

# Configurar DATABASE_URL para PostgreSQL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:110812@localhost:5432/monitor_prod"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from backend.app.database import AsyncSessionLocal

async def verificar_indices():
    """Verifica quais índices existem no PostgreSQL"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Listar todos os índices
            query = text("""
                SELECT 
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            
            result = await session.execute(query)
            indices = result.fetchall()
            
            print("\n" + "="*80)
            print("ÍNDICES EXISTENTES NO POSTGRESQL")
            print("="*80)
            
            if not indices:
                print("⚠️  NENHUM ÍNDICE CUSTOMIZADO ENCONTRADO!")
                print("\n🔴 AÇÃO NECESSÁRIA: Executar scripts/criar_indices.py")
            else:
                tabelas = {}
                for table, index, definition in indices:
                    if table not in tabelas:
                        tabelas[table] = []
                    tabelas[table].append((index, definition))
                
                for table, idx_list in sorted(tabelas.items()):
                    print(f"\n📊 Tabela: {table}")
                    for idx_name, idx_def in idx_list:
                        print(f"   ✅ {idx_name}")
            
            print("\n" + "="*80)
            
            # Verificar índices críticos
            indices_criticos = {
                "idx_ping_device_time": "ping_logs(device_id, timestamp DESC)",
                "idx_traffic_device_time": "traffic_logs(device_id, timestamp DESC)",
                "idx_alerts_created": "alerts(created_at DESC)",
                "idx_ping_type_id_time": "ping_logs(device_type, device_id, timestamp DESC)"
            }
            
            indices_existentes = [idx[1] for idx in indices]
            
            print("\n🎯 ÍNDICES CRÍTICOS:")
            faltando = []
            for idx, descricao in indices_criticos.items():
                if idx in indices_existentes:
                    print(f"   ✅ {idx} - {descricao}")
                else:
                    print(f"   ❌ {idx} - {descricao} - FALTANDO!")
                    faltando.append(idx)
            
            if faltando:
                print(f"\n🔴 FALTAM {len(faltando)} ÍNDICES CRÍTICOS!")
                print("   Execute: python scripts/criar_indices.py")
            else:
                print("\n✅ TODOS OS ÍNDICES CRÍTICOS ESTÃO CRIADOS!")
            
            print("\n")
            
    except Exception as e:
        print(f"\n❌ ERRO ao conectar no PostgreSQL:")
        print(f"   {e}")
        print("\n💡 Verifique se:")
        print("   1. PostgreSQL está rodando")
        print("   2. Banco 'monitor_prod' existe")
        print("   3. Credenciais estão corretas")
        print("\n")

if __name__ == "__main__":
    asyncio.run(verificar_indices())
