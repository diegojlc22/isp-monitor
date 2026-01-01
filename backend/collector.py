import asyncio
import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH para imports funcionarem
sys.path.append(os.getcwd())

from backend.app.database import engine, Base
from backend.app.services.pinger_fast import PingerService
from backend.app.services.snmp_monitor import snmp_monitor_job
from backend.app.services.synthetic_agent import synthetic_agent_job
from backend.app.services.maintenance import cleanup_job

from backend.app.services.topology import run_topology_discovery

async def topology_loop():
    """Roda descoberta de topologia a cada 30 minutos"""
    print("[COLLECTOR] Discovery de Topologia agendado (30min)")
    while True:
        try:
            await asyncio.sleep(60) # Espera sistema inicializar
            await run_topology_discovery()
        except Exception as e:
            print(f"[ERROR] Falha na descoberta de topologia: {e}")
            
        await asyncio.sleep(1800) # 30 min

async def heartbeat_loop():
    """Atualiza o timestamp de 'last seen' no banco a cada 10 segundos"""
    from backend.app.models import Parameters
    from backend.app.database import AsyncSessionLocal
    from datetime import datetime, timezone
    
    print("[COLLECTOR] Heartbeat iniciado (10s)")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                param = await db.get(Parameters, "collector_last_seen")
                if not param:
                    param = Parameters(key="collector_last_seen", value=datetime.now(timezone.utc).isoformat())
                    db.add(param)
                else:
                    param.value = datetime.now(timezone.utc).isoformat()
                await db.commit()
        except Exception as e:
            print(f"[WARN] Falha no heartbeat do collector: {e}")
        
        await asyncio.sleep(10)

async def maintenance_loop():
    """Roda tarefas de limpeza a cada 24 horas"""
    print("[COLLECTOR] Agendador de limpeza iniciado (24h)")
    while True:
        try:
            await asyncio.sleep(60) # Espera sistema estabilizar na primeira vez
            await cleanup_job()
        except Exception as e:
            print(f"[ERROR] Falha na manutenção diária: {e}")
        
        # Esperar 24h (86400 segundos)
        await asyncio.sleep(86400)

async def main():
    print("---------------------------------------------------------")
    print("[COLLECTOR] Iniciando Processo de Coleta Independente...")
    print("---------------------------------------------------------")
    
    # Garantir que o banco existe (With Retries)
    db_ok = False
    print("[COLLECTOR] ⏳ Aguardando estabilização do PostgreSQL...")
    for attempt in range(10): # Mais tentativas para o coletor
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("[COLLECTOR] ✅ Conexão estabelecida e banco verificado.")
            db_ok = True
            break
        except Exception as e:
            error_str = str(e).lower()
            if "connection was closed" in error_str or "connectiondoesnotexist" in error_str:
                wait_time = 2 + attempt
                print(f"[COLLECTOR] 📡 Conexão instável. Aguardando {wait_time}s ({attempt+1}/10)...")
                await asyncio.sleep(wait_time)
            else:
                print(f"[COLLECTOR] ⏳ Tentativa {attempt+1}/10 falhou: {e}")
                await asyncio.sleep(2)
    
    if not db_ok:
        print("[CRITICAL] Falha total na conexão com o banco após 10 tentativas.")
        return

    # Aplicar otimizações avançadas
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
    pinger = PingerService()
    tasks.append(asyncio.create_task(pinger.start()))
    
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

    # Manutenção Diária (Limpeza de Logs)
    tasks.append(asyncio.create_task(maintenance_loop()))

    # Topologia Automática
    tasks.append(asyncio.create_task(topology_loop()))

    # Heartbeat (Status de Saúde)
    tasks.append(asyncio.create_task(heartbeat_loop()))

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
