import asyncio
import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH para imports funcionarem
sys.path.append(os.getcwd())

from backend.app.database import engine, Base
from backend.app.services.pinger_fast import monitor_job_fast
from backend.app.services.snmp_monitor import snmp_monitor_job
from backend.app.services.synthetic_agent import synthetic_agent_job

async def main():
    print("---------------------------------------------------------")
    print("[COLLECTOR] Iniciando Processo de Coleta Independente...")
    print("---------------------------------------------------------")
    
    # Garantir que o banco existe (Create Tables se não existirem)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("[COLLECTOR] Banco de dados conectado.")

    # Aplicar otimizações avançadas (BRIN Index, Autovacuum)
    try:
        from backend.app.services.postgres_optimizer import apply_postgres_optimizations
        await apply_postgres_optimizations()
    except Exception as e:
        print(f"[WARN] Erro ao aplicar otimizações Postgres: {e}")

    # Iniciar tarefas concorrentes
    # 1. Pinger (monitor_job_fast já tem loop infinito)
    # 2. SNMP (snmp_monitor_job tem loop infinito?) -> Vamos verificar.
    # 3. Agent (synthetic_agent_job tem loop infinito?) -> Vamos verificar.
    
    tasks = []
    
    # Pinger (Crítico)
    print("[COLLECTOR] Iniciando Pinger...")
    tasks.append(asyncio.create_task(monitor_job_fast()))
    
    # SNMP (Opcional, se existir)
    try:
        print("[COLLECTOR] Iniciando Monitor SNMP...")
        tasks.append(asyncio.create_task(snmp_monitor_job()))
    except Exception as e:
        print(f"[WARN] SNMP Monitor falhou na inicialização: {e}")

    # IA Agent (Opcional)
    try:
        print("[COLLECTOR] Iniciando IA Agent...")
        tasks.append(asyncio.create_task(synthetic_agent_job()))
    except Exception as e:
        print(f"[WARN] IA Agent falhou na inicialização: {e}")

    # Manter o processo vivo aguardando as tarefas
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        # Policy fix for Windows (evita erros de loop fechado)
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[COLLECTOR] Encerrando coleta...")
    except Exception as e:
        print(f"[CRITICAL] Erro no coletor: {e}")
        import traceback
        traceback.print_exc()
