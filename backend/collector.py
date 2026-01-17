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
logger.remove() # Remove default stderr handler (level=DEBUG)
logger.add(sys.stderr, level="INFO") # Re-add stderr with level=INFO
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

async def postgres_watchdog():
    """🧠 Monitora a saúde do PostgreSQL e registra quedas/recuperações"""
    import socket
    from datetime import datetime
    
    def check_postgres_alive():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 5432))
            sock.close()
            return result == 0
        except:
            return False
    
    logger.info("[WATCHDOG] 🐕 PostgreSQL Watchdog iniciado (verifica a cada 30s)")
    was_alive = True
    downtime_start = None
    
    while True:
        try:
            is_alive = check_postgres_alive()
            
            if not is_alive and was_alive:
                # PostgreSQL acabou de cair
                downtime_start = datetime.now()
                logger.error(f"[WATCHDOG] ❌ PostgreSQL OFFLINE detectado às {downtime_start.strftime('%H:%M:%S')}")
                logger.warning("[WATCHDOG] ⏳ Os serviços tentarão reconectar automaticamente...")
                
            elif is_alive and not was_alive:
                # PostgreSQL voltou!
                uptime = datetime.now()
                downtime_duration = (uptime - downtime_start).total_seconds() if downtime_start else 0
                logger.info(f"[WATCHDOG] ✅ PostgreSQL ONLINE novamente às {uptime.strftime('%H:%M:%S')}")
                logger.info(f"[WATCHDOG] 📊 Tempo de inatividade: {int(downtime_duration)}s")
                logger.info("[WATCHDOG] 🔄 Os serviços devem reconectar automaticamente nos próximos segundos.")
                downtime_start = None
            
            was_alive = is_alive
            
        except asyncio.CancelledError:
            logger.info("[WATCHDOG] Loop cancelado.")
            break
        except Exception as e:
            logger.warning(f"[WATCHDOG] Erro no watchdog: {e}")
        
        await asyncio.sleep(30)  # Verifica a cada 30 segundos

async def cortex_alert_loop():
    """
    Job que roda a análise do Cortex AI e envia notificações para alertas novos/críticos.
    Roda a cada 5 minutos.
    """
    from backend.app.services.cortex_ai import CortexAI
    from backend.app.services.notifier import send_notification
    import hashlib

    logger.info("[COLLECTOR] 🧠 Cortex AI Proactive Alerts iniciado (5min)")
    cortex = CortexAI()
    sent_alerts = set() # Hash das mensagens enviadas para evitar spam

    while True:
        try:
            # 1. Aguarda um pouco para não rodar junto com outros jobs pesados
            await asyncio.sleep(30)
            
            # 2. Executa Análise
            insights = await cortex.analyze()
            
            # 3. Processa Insights críticos ou avisos
            async with AsyncSessionLocal() as session:
                # Pegar config de notificação
                from backend.app.models import Parameters
                params_res = await session.execute(
                    select(Parameters).where(Parameters.key.in_([
                        'telegram_token', 'telegram_chat_id', 'telegram_enabled',
                        'whatsapp_enabled', 'whatsapp_target', 'whatsapp_target_group'
                    ]))
                )
                notif_config = {p.key: p.value for p in params_res.scalars().all()}

                for insight in insights:
                    if insight.get("severity") in ["critical", "warning"]:
                        # Gerar um ID único para este alerta baseado no título e equipamento
                        # Validade de 6 horas para o mesmo alerta
                        alert_key = f"{insight.get('title')}_{insight.get('equipment_id')}"
                        msg_hash = hashlib.md5(alert_key.encode()).hexdigest()
                        
                        if msg_hash not in sent_alerts:
                            # Montar Mensagem Estilizada
                            emoji = "🚨" if insight['severity'] == "critical" else "⚠️"
                            msg = f"{emoji} *CORTEX AI: {insight['title']}*\n\n"
                            msg += f"📟 Dispositivo: {insight.get('equipment_name', 'Geral')}\n"
                            msg += f"📝 {insight['description']}\n\n"
                            msg += f"💡 *Recomendação:* {insight.get('recommendation', 'Verificar painel.')}"
                            
                            # Enviar
                            await send_notification(
                                message=msg,
                                telegram_token=notif_config.get('telegram_token'),
                                telegram_chat_id=notif_config.get('telegram_chat_id'),
                                telegram_enabled=notif_config.get('telegram_enabled', 'true').lower() == 'true',
                                whatsapp_enabled=notif_config.get('whatsapp_enabled', 'false').lower() == 'true',
                                whatsapp_target=notif_config.get('whatsapp_target'),
                                whatsapp_target_group=notif_config.get('whatsapp_target_group')
                            )
                            
                            sent_alerts.add(msg_hash)
                            logger.info(f"[CORTEX ALERT] Notificação enviada: {insight.get('title')}")

            # Limpeza de cache de alertas a cada 6 horas (aproximadamente 72 ciclos de 5min)
            if len(sent_alerts) > 100: sent_alerts.clear()

        except asyncio.CancelledError:
            logger.info("[CORTEX] Loop de alertas cancelado.")
            break
        except Exception as e:
            logger.error(f"[ERROR] Falha no loop de alertas Cortex: {e}")
        
        await asyncio.sleep(300) # 5 minutos

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
    
    # 🧠 INTELIGÊNCIA: Garantir que o PostgreSQL está online e acessível
    import socket
    
    def check_postgres_port():
        """Verifica se o PostgreSQL está aceitando conexões na porta 5432"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 5432))
            sock.close()
            return result == 0
        except:
            return False
    
    db_ok = False
    attempt = 0
    logger.info("[COLLECTOR] 🧠 Verificando disponibilidade do PostgreSQL...")
    
    # 🎯 FASE 1: Aguardar PostgreSQL aceitar conexões (Indefinidamente com Backoff)
    while not check_postgres_port():
        wait_time = min(5 + (attempt * 2), 60)  # Backoff exponencial até 60s
        logger.warning(f"[COLLECTOR] ⏳ PostgreSQL offline. Aguardando {wait_time}s (tentativa {attempt+1})...")
        await asyncio.sleep(wait_time)
        attempt += 1
    
    logger.info("[COLLECTOR] ✅ PostgreSQL está aceitando conexões na porta 5432!")
    
    # 🎯 FASE 2: Conectar ao banco e criar tabelas (Com Retry Inteligente)
    logger.info("[COLLECTOR] 📡 Estabelecendo conexão com o banco de dados...")
    for attempt in range(20):  # Aumentado de 10 para 20 tentativas
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("[COLLECTOR] ✅ Conexão estabelecida e esquema do banco verificado.")
            db_ok = True
            break
        except Exception as e:
            error_str = str(e).lower()
            if "connection refused" in error_str or "connect call failed" in error_str:
                wait_time = min(3 + attempt, 30)
                logger.warning(f"[COLLECTOR] 🔄 Conexão recusada. Aguardando {wait_time}s ({attempt+1}/20)...")
                await asyncio.sleep(wait_time)
            elif "connection was closed" in error_str or "connectiondoesnotexist" in error_str:
                wait_time = 2 + attempt
                logger.warning(f"[COLLECTOR] 📡 Conexão instável. Aguardando {wait_time}s ({attempt+1}/20)...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[COLLECTOR] ⚠️ Tentativa {attempt+1}/20 falhou: {e}")
                await asyncio.sleep(3)
    
    if not db_ok:
        logger.critical("[CRITICAL] ❌ Falha total na conexão com o banco após 20 tentativas.")
        logger.critical("[CRITICAL] 🔧 Verifique se o PostgreSQL está rodando e acessível.")
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
    start_task("Cortex Alerts", cortex_alert_loop())
    start_task("Topology", topology_loop())
    start_task("Maintenance", maintenance_loop())
    start_task("Heartbeat", heartbeat_loop())
    start_task("PostgreSQL Watchdog", postgres_watchdog())  # 🐕 Monitor de saúde do PostgreSQL
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
                    elif name == "Cortex Alerts": new_coro = cortex_alert_loop()
                    elif name == "PostgreSQL Watchdog": new_coro = postgres_watchdog()
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
