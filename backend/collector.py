import asyncio
import sys
import os
import signal
import traceback
from sqlalchemy import select
from loguru import logger

# Adicionar o diretório raiz ao PYTHONPATH para imports funcionarem
sys.path.append(os.getcwd())

from backend.app.database import engine, Base
from backend.app.services.pinger_fast import PingerService
from backend.app.services.snmp_monitor import snmp_monitor_job
from backend.app.services.synthetic_agent import synthetic_agent_job, start_auto_priority_loop
from backend.app.services.maintenance import cleanup_job
from backend.app.services.topology import run_topology_discovery
from backend.app.services.security_audit import security_audit_job
from backend.app.services.capacity_planning import capacity_planning_job
from backend.app.services.backup_service import backup_scheduler_loop
from backend.app.database import AsyncSessionLocal
from backend.app.models import Parameters

# Configure Loguru
logger.add("collector_supervisor.log", rotation="1 MB", retention="5 days", level="INFO")

async def topology_loop():
    """Roda descoberta de topologia a cada 30 minutos"""
    logger.info("[COLLECTOR] Discovery de Topologia agendado (30min)")
    while True:
        try:
            await asyncio.sleep(60) # Espera sistema inicializar
            await run_topology_discovery()
        except asyncio.CancelledError:
            logger.info("[TOPOLOGY] Loop cancelado.")
            break
        except Exception as e:
            logger.error(f"[ERROR] Falha na descoberta de topologia: {e}")
        
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Parameters).where(Parameters.key == "topology_interval"))
                param = res.scalar_one_or_none()
                interval = int(param.value) if param else 1800
        except:
            interval = 1800
            
        await asyncio.sleep(interval) # Configurable interval

async def heartbeat_loop():
    """Atualiza o timestamp de 'last seen' no banco a cada 10 segundos"""
    from backend.app.models import Parameters
    from backend.app.database import AsyncSessionLocal
    from datetime import datetime, timezone
    
    logger.info("[COLLECTOR] Heartbeat iniciado (10s)")
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
        except asyncio.CancelledError:
            logger.info("[HEARTBEAT] Loop cancelado.")
            break
        except Exception as e:
            logger.warning(f"[WARN] Falha no heartbeat do collector: {e}")
        
        await asyncio.sleep(10)

async def maintenance_loop():
    """Roda tarefas de limpeza a cada 24 horas"""
    logger.info("[COLLECTOR] Agendador de limpeza iniciado (24h)")
    while True:
        try:
            await asyncio.sleep(60) # Espera sistema estabilizar na primeira vez
            await cleanup_job()
            
            # Rollup de estatísticas horárias
            from backend.app.services.maintenance import rollup_hourly_stats_job
            await rollup_hourly_stats_job()
        except asyncio.CancelledError:
            logger.info("[MAINTENANCE] Loop cancelado.")
            break
        except Exception as e:
            logger.error(f"[ERROR] Falha na manutenção diária: {e}")
        
        # Esperar 24h (86400 segundos)
        await asyncio.sleep(86400)

async def main():
    logger.info("---------------------------------------------------------")
    logger.info("[COLLECTOR] Iniciando Processo de Coleta Independente (SUPERVISOR V2)...")
    logger.info("---------------------------------------------------------")
    
    # Garantir que o banco existe (With Retries)
    db_ok = False
    logger.info("[COLLECTOR] ⏳ Aguardando estabilização do PostgreSQL...")
    for attempt in range(10): 
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("[COLLECTOR] ✅ Conexão estabelecida e banco verificado.")
            db_ok = True
            break
        except Exception as e:
            error_str = str(e).lower()
            if "connection was closed" in error_str or "connectiondoesnotexist" in error_str:
                wait_time = 2 + attempt
                logger.warning(f"[COLLECTOR] 📡 Conexão instável. Aguardando {wait_time}s ({attempt+1}/10)...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[COLLECTOR] ⏳ Tentativa {attempt+1}/10 falhou: {e}")
                await asyncio.sleep(2)
    
    if not db_ok:
        logger.critical("[CRITICAL] Falha total na conexão com o banco após 10 tentativas.")
        return

    # Aplicar otimizações avançadas
    try:
        from backend.app.services.postgres_optimizer import apply_postgres_optimizations
        await apply_postgres_optimizations()
    except Exception as e:
        logger.warning(f"[WARN] Erro ao aplicar otimizações Postgres: {e}")

    # Definição das Tarefas supervisionadas
    pinger = PingerService()
    
    # Dicionário de tarefas ativas: {name: Task}
    active_tasks = {}
    
    def start_task(name, coro):
        task = asyncio.create_task(coro)
        task.set_name(name)
        active_tasks[name] = task
        return task

    # 1. Start Initial Tasks
    start_task("Pinger", pinger.start())
    # Note: snmp_monitor_job and others are infinite loops. 
    start_task("SNMP Monitor", snmp_monitor_job())
    start_task("AI Agent", synthetic_agent_job())
    start_task("Auto Priority Monitor", start_auto_priority_loop())  # 🎯 NEW: Auto-monitor priority targets
    start_task("Topology", topology_loop())
    start_task("Maintenance", maintenance_loop())
    start_task("Heartbeat", heartbeat_loop())
    start_task("Security Audit", security_audit_job())
    start_task("Capacity Planning", capacity_planning_job())
    start_task("Backup Service", backup_scheduler_loop())
    
    logger.info(f"[SUPERVISOR] {len(active_tasks)} tarefas iniciais disparadas.")

    # SUPERVISOR LOOP
    try:
        while True:
            # Check for done tasks
            # Use list() because we modify dict in loop
            for name, task in list(active_tasks.items()):
                if task.done():
                    try:
                        exc = task.exception()
                        if exc:
                            logger.error(f"[SUPERVISOR] ⚠️ Tarefa '{name}' MORREU com erro: {exc}")
                            # Não precisamos imprimir traceback completo aqui se já foi logado pelo loguru,
                            # mas útil para debug profundo.
                        else:
                            logger.warning(f"[SUPERVISOR] ⚠️ Tarefa '{name}' terminou inesperadamente (sem erro).")
                    except asyncio.CancelledError:
                        logger.info(f"[SUPERVISOR] Tarefa '{name}' foi cancelada.")
                        del active_tasks[name]
                        continue
                    
                    # RESTART STRATEGY
                    logger.info(f"[SUPERVISOR] 🔄 Reiniciando '{name}' em 5 segundos...")
                    del active_tasks[name]
                    
                    # Recreate coroutine based on name
                    new_coro = None
                    if name == "Pinger": new_coro = pinger.start()
                    elif name == "SNMP Monitor": new_coro = snmp_monitor_job()
                    elif name == "AI Agent": new_coro = synthetic_agent_job()
                    elif name == "Topology": new_coro = topology_loop()
                    elif name == "Maintenance": new_coro = maintenance_loop()
                    elif name == "Heartbeat": new_coro = heartbeat_loop()
                    elif name == "Security Audit": new_coro = security_audit_job()
                    elif name == "Capacity Planning": new_coro = capacity_planning_job()
                    
                    if new_coro:
                         # Launch restart delay as a separate task? 
                         # No, we can just sleep here? No, blocking loop blocks supervisor.
                         # Better to launch a "restarter" task.
                         # Simpler: Just restart immediately but the task itself handles initial delay?
                         # Or simpler: asyncio.create_task(restart_with_delay(name, new_coro))
                         
                         async def delayed_restart(n, c):
                             await asyncio.sleep(5)
                             logger.info(f"[SUPERVISOR] Relançando {n} agora.")
                             start_task(n, c)

                         asyncio.create_task(delayed_restart(name, new_coro))

                    else:
                        logger.critical(f"[SUPERVISOR] Não sei como reiniciar '{name}'!")

            await asyncio.sleep(2) # Check every 2 seconds

    except asyncio.CancelledError:
        logger.info("[SUPERVISOR] Recebido sinal de parada. Cancelando tarefas...")
        for name, task in active_tasks.items():
            task.cancel()
        
        await asyncio.gather(*active_tasks.values(), return_exceptions=True)
        logger.info("[SUPERVISOR] Todas as tarefas encerradas.")

if __name__ == "__main__":
    try:
        # Policy fix for Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        # Signal Handling for Graceful Shutdown
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        main_task = loop.create_task(main())
        
        def signal_handler(sig, frame):
            logger.info(f"[COLLECTOR] Signal {sig} received. Shutting down...")
            if not main_task.done():
                main_task.cancel()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            loop.run_until_complete(main_task)
        except asyncio.CancelledError:
            pass
        finally:
            loop.close()
            logger.info("[COLLECTOR] Processo finalizado.")
            
    except KeyboardInterrupt:
        logger.info("[COLLECTOR] Encerrando via KeyboardInterrupt...")
    except Exception as e:
        logger.critical(f"[CRITICAL] Erro fatal no coletor: {e}")
        import traceback
        traceback.print_exc()
