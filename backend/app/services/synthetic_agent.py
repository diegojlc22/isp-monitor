
import asyncio
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, delete
from backend.app.database import AsyncSessionLocal
from backend.app.models import SyntheticLog, Baseline, PingLog, MonitorTarget, Parameters
from backend.app.services.telegram import send_telegram_alert

# --- CONFIG ---
# Default fallback configs if not in DB
DEFAULT_INTERVAL = 300
DEFAULT_HTTP = ["https://www.google.com", "https://www.cloudflare.com"]
DEFAULT_DNS = "8.8.8.8"

# --- MANUAL LOOP CONTROL ---
manual_loop_running = False
manual_loop_task = None

# --- AUTO LOOP FOR PRIORITY TARGETS ---
auto_priority_loop_running = False
auto_priority_loop_task = None

async def start_auto_priority_loop():
    """Monitora automaticamente APENAS alvos prioritários em background."""
    global auto_priority_loop_running
    if auto_priority_loop_running:
        return
    
    auto_priority_loop_running = True
    print("[IA-AGENT] Loop automático de PRIORITÁRIOS INICIADO.")
    
    try:
        while auto_priority_loop_running:
            await run_priority_test_cycle()
            # Espera intervalo configurável (padrão: 5 minutos)
            async with AsyncSessionLocal() as session:
                params_res = await session.execute(
                    select(Parameters).where(Parameters.key == "agent_check_interval")
                )
                param = params_res.scalar_one_or_none()
                interval = int(param.value) if param else 300
            
            for _ in range(interval):
                if not auto_priority_loop_running: break
                await asyncio.sleep(1)
    finally:
        auto_priority_loop_running = False
        print("[IA-AGENT] Loop automático de PRIORITÁRIOS PARADO.")

async def stop_auto_priority_loop():
    global auto_priority_loop_running
    auto_priority_loop_running = False

async def start_manual_test_loop():
    """Roda testes continuamente em background até ser parado."""
    global manual_loop_running
    if manual_loop_running:
        return
    
    manual_loop_running = True
    print("[IA-AGENT] Loop de teste manual INICIADO.")
    
    try:
        while manual_loop_running:
            await run_single_test_cycle()
            # Espera 10 segundos entre ciclos manuais (mais rápido que o normal)
            for _ in range(10):
                if not manual_loop_running: break
                await asyncio.sleep(1)
    finally:
        manual_loop_running = False
        print("[IA-AGENT] Loop de teste manual PARADO.")

async def stop_manual_test_loop():
    global manual_loop_running
    manual_loop_running = False

# --- NETWORK TEST FUNCTIONS ---
from icmplib import async_ping

async def check_ping(target: str) -> dict:
    """Measures ICMP latency (Real Ping)"""
    try:
        # Strip protocol if present for ping
        host = target.replace("https://", "").replace("http://", "").split("/")[0]
        # Prefer privileged=True for better accuracy as seen in pinger_fast.py
        try:
            result = await async_ping(host, count=2, timeout=2, privileged=True)
        except Exception:
            # Fallback for environments where raw sockets are not allowed
            result = await async_ping(host, count=2, timeout=2, privileged=False)
        
        if result.is_alive:
            return {"success": True, "latency": round(result.avg_rtt)}
        else:
             return {"success": False, "latency": None}
    except Exception as e:
        print(f"Ping Error: {e}")
        return {"success": False, "latency": None}

async def check_dns(target_ip: str) -> dict:
    """Measures DNS resolution time using the target as the resolver (if possible) or just checks reachability"""
    # For now, let's keep it simple: DNS is often just UDP 53 reachability for this context
    # But usually users want to know if 8.8.8.8 responds to ping too.
    # Let's fallback to ping for DNS type as well for latency measurement
    return await check_ping(target_ip)

async def check_http(url: str) -> dict:
    # Use Ping for latency accuracy if it's just meant to be "is it slow?"
    # However, HTTP check implies checking web server payload. 
    # But user complained about latency. TCP handshake is close to Ping RTT but not same.
    # Let's verify if the user input looks like an IP.
    
    # If user provided raw IP, use Ping. If URL, use TCP Connect.
    import re
    is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", url)
    
    if is_ip:
        return await check_ping(url)
        
    start = time.time()
    try:
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        reader, writer = await asyncio.open_connection(domain, 443)
        writer.close()
        await writer.wait_closed()
        latency = round((time.time() - start) * 1000)
        return {"success": True, "latency": latency, "code": 200}
    except Exception:
         # Fallback to ping if HTTP fails (maybe firewall blocks port 443)
         return await check_ping(domain)

# --- INTELLIGENCE MODULES ---

async def train_baselines_job():
    """
    🧠 THE BRAIN: Learn patterns from history.
    Runs periodically (e.g., every 6 hours) to update 'Normal' stats for every hour of the week.
    """
    print("[IA-BRAIN] Training Baselines (Learning patterns)...")
    try:
        async with AsyncSessionLocal() as session:
            # Look back 14 days
            cutoff = datetime.utcnow() - timedelta(days=14)
            
            # Aggregate stats by Hour of Day and Target
            # We want to know: For 'google.com' at '14:00', what is Avg Latency and StdDev?
            
            # Group by hour (0-23)
            # Portable Message: Use EXTRACT(HOUR FROM ...)
            
            stmt = select(
                SyntheticLog.target,
                func.extract('hour', SyntheticLog.timestamp).label('hour'),
                func.avg(SyntheticLog.latency_ms).label('avg'),
                # Simple Variance: AVG(x*x) - AVG(x)^2
                (func.avg(SyntheticLog.latency_ms * SyntheticLog.latency_ms) - func.avg(SyntheticLog.latency_ms) * func.avg(SyntheticLog.latency_ms)).label('variance'),
                func.count().label('samples')
            ).where(
                SyntheticLog.timestamp >= cutoff,
                SyntheticLog.latency_ms.isnot(None)
            ).group_by(
                SyntheticLog.target,
                func.extract('hour', SyntheticLog.timestamp)
            )
            
            rows = await session.execute(stmt)
            
            # upsert baselines
            for row in rows:
                target_key = row.target
                hour = int(row.hour)
                # Postgres (asyncpg) returns Decimal, convert to float for python math
                avg = float(row.avg) if row.avg is not None else 0.0
                variance = float(row.variance) if (row.variance and row.variance > 0) else 0.0
                std_dev = variance ** 0.5
                samples = row.samples
                
                # Check if exists
                chk = await session.execute(select(Baseline).where(
                    Baseline.metric_type == f"synthetic_{target_key}",
                    Baseline.hour_of_day == hour
                ))
                baseline = chk.scalar_one_or_none()
                
                if baseline:
                    baseline.avg_value = avg
                    baseline.std_dev = std_dev
                    baseline.sample_count = samples
                    baseline.last_updated = datetime.utcnow()
                else:
                    new_b = Baseline(
                        metric_type=f"synthetic_{target_key}",
                        hour_of_day=hour,
                        day_of_week=-1, # -1 = All days (simplify for now)
                        avg_value=avg,
                        std_dev=std_dev,
                        sample_count=samples
                    )
                    session.add(new_b)
            
            await session.commit()
            print("[IA-BRAIN] Training Complete. Baselines updated.")
            
    except Exception as e:
        print(f"[IA-BRAIN] Error training: {e}")

async def run_priority_test_cycle():
    """
    🎯 Executa testes APENAS em alvos marcados como prioritários.
    Usado pelo loop automático em background.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Get ONLY priority targets
            targets_res = await session.execute(
                select(MonitorTarget).where(
                    MonitorTarget.enabled == True,
                    MonitorTarget.is_priority == True
                )
            )
            priority_targets = targets_res.scalars().all()
            
            if not priority_targets:
                return {"message": "No priority targets configured"}
            
            print(f"[IA-AGENT AUTO] Testando {len(priority_targets)} alvos prioritários...")
            
            # Execute Tests
            for t in priority_targets:
                res = {}
                if t.type == 'dns':
                    res = await check_dns(t.target)
                elif t.type == 'http':
                    url = t.target if t.target.startswith("http") else f"https://{t.target}"
                    res = await check_http(url)
                elif t.type == 'icmp':
                    res = await check_ping(t.target)
                
                # Save Log
                log = SyntheticLog(
                    test_type=t.type,
                    target=t.target,
                    latency_ms=res.get("latency"),
                    success=res.get("success", False),
                    timestamp=datetime.utcnow()
                )
                session.add(log)
            
            await session.commit()
            return {"message": f"Tested {len(priority_targets)} priority targets"}
    
    except Exception as e:
        print(f"[PRIORITY TEST ERROR] {e}")
        return {"error": str(e)}

async def run_single_test_cycle():
    """
    🧪 Single test cycle for manual trigger (non-blocking).
    Returns results immediately without entering infinite loop.
    """
    print("[IA-AGENT] Running manual test cycle...")
    
    try:
        results = []
        current_hour = datetime.now().hour
        
        async with AsyncSessionLocal() as session:
            # Load Configs
            params_res = await session.execute(select(Parameters).where(Parameters.key.in_(["agent_latency_threshold", "agent_anomaly_cycles"])))
            params = {p.key: p.value for p in params_res.scalars().all()}
            
            Z_SCORE_LIMIT = 3.0
            fixed_limit = int(params.get("agent_latency_threshold", 300))
            
            # Get Targets
            targets_res = await session.execute(select(MonitorTarget).where(MonitorTarget.enabled == True))
            db_targets = targets_res.scalars().all()
            
            if not db_targets:
                return {"message": "No targets configured", "tests": []}
            
            # Execute Tests
            batch_results = []
            for t in db_targets:
                res = {}
                if t.type == 'dns':
                    res = await check_dns(t.target)
                elif t.type == 'http':
                    url = t.target if t.target.startswith("http") else f"https://{t.target}"
                    res = await check_http(url)
                elif t.type == 'icmp':
                    res = await check_ping(t.target)
                
                test_result = {
                    "type": t.type,
                    "target": t.target,
                    "latency": res.get("latency"),
                    "success": res.get("success"),
                    "is_anomaly": False
                }
                
                # Save Log
                log = SyntheticLog(
                    test_type=t.type,
                    target=t.target,
                    latency_ms=round(res.get("latency")) if res.get("latency") else 0,
                    success=res.get("success"),
                    timestamp=datetime.utcnow()
                )
                session.add(log)
                
                # Check for anomaly
                if res.get("latency"):
                    metric_key = f"synthetic_{t.target}"
                    base_res = await session.execute(select(Baseline).where(
                        Baseline.metric_type == metric_key,
                        Baseline.hour_of_day == current_hour
                    ))
                    baseline = base_res.scalar_one_or_none()
                    
                    if baseline and baseline.sample_count > 10:
                        std = baseline.std_dev if baseline.std_dev > 5 else 5
                        z_score = (res["latency"] - baseline.avg_value) / std
                        
                        if z_score > Z_SCORE_LIMIT:
                            test_result["is_anomaly"] = True
                            test_result["z_score"] = round(z_score, 1)
                            test_result["expected"] = int(baseline.avg_value)
                    else:
                        # Use fixed threshold
                        if res["latency"] > fixed_limit:
                            test_result["is_anomaly"] = True
                            test_result["expected"] = f"<{fixed_limit}"
                
                batch_results.append(test_result)
            
            await session.commit()
            
            anomalies = [r for r in batch_results if r["is_anomaly"]]
            
            return {
                "message": f"Test completed. {len(anomalies)} anomalies detected.",
                "tests": batch_results,
                "anomalies": anomalies
            }
            
    except Exception as e:
        print(f"[IA-AGENT] Manual test error: {e}")
        return {"error": str(e)}

async def synthetic_agent_job():
    """
    🕵️ THE EYE: Monitors and Judges using Z-Score (Statistical Anomaly Detection).
    """
    print("[IA-AGENT] Starting AI Analyst...")
    
    # Run training once on startup
    asyncio.create_task(train_baselines_job())
    
    anomaly_streak = 0
    state_status = "NORMAL"

    while True:
        try:
            results = []
            current_hour = datetime.now().hour
            
            async with AsyncSessionLocal() as session:
                # 0. Load Configs
                params_res = await session.execute(select(Parameters).where(Parameters.key.in_(["agent_latency_threshold", "agent_anomaly_cycles", "agent_check_interval"])))
                params = {p.key: p.value for p in params_res.scalars().all()}
                
                # Configs (with Z-Score Sensitivity Factor)
                Z_SCORE_LIMIT = 3.0 # Standard statistical anomaly limit (3 sigma)
                ANOMALY_LIMIT = int(params.get("agent_anomaly_cycles", 2))
                
                # 1. Targets
                targets_res = await session.execute(select(MonitorTarget).where(MonitorTarget.enabled == True))
                db_targets = targets_res.scalars().all()
                targets = []
                
                if not db_targets:
                     # Remove defaults to respect user preference
                     # if user wants to monitor google, they add it manually.
                     pass 
                else:
                    for t in db_targets:
                        targets.append((t.type, t.target))

                # If no targets, skip
                if not targets:
                    print("[IA-AGENT] No targets configured. Sleeping.")
                    await asyncio.sleep(60)
                    continue

                # 2. Execute Tests
                batch_results = []
                for t_type, t_target in targets:
                    res = {}
                    if t_type == 'dns':
                        res = await check_dns(t_target)
                    elif t_type == 'http':
                        url = t_target if t_target.startswith("http") else f"https://{t_target}"
                        res = await check_http(url)
                    elif t_type == 'icmp':
                        res = await check_ping(t_target)
                    
                    batch_results.append({
                        "type": t_type,
                        "target": t_target,
                        "latency": res.get("latency"),
                        "success": res.get("success")
                    })
                
                # 3. Save Logs & Analyze
                anomalies_found = []
                
                for r in batch_results:
                    # Save Log
                    log = SyntheticLog(
                        test_type=r["type"],
                        target=r["target"],
                        latency_ms=round(r["latency"]) if r["latency"] else 0,
                        success=r["success"],
                        timestamp=datetime.utcnow() # Naive for Postgres
                    )
                    session.add(log)
                    
                    # 🧠 INTELLIGENCE: Compare with Baseline
                    if r["latency"]:
                        # Fetch baseline for this specific target & hour
                        metric_key = f"synthetic_{r['target']}"
                        base_res = await session.execute(select(Baseline).where(
                            Baseline.metric_type == metric_key,
                            Baseline.hour_of_day == current_hour
                        ))
                        baseline = base_res.scalar_one_or_none()
                        
                        z_score = 0
                        is_spike = False
                        
                        if baseline and baseline.sample_count > 10:
                            # We have learned data! Use Z-Score.
                            std = baseline.std_dev if baseline.std_dev > 5 else 5 # Min 5ms stddev to avoid noise
                            z_score = (r["latency"] - baseline.avg_value) / std
                            
                            if z_score > Z_SCORE_LIMIT:
                                is_spike = True
                                r["z_score"] = round(z_score, 1)
                                r["expected"] = int(baseline.avg_value)
                        else:
                            # Cold Start: Fallback to fixed threshold from settings
                            fixed_limit = int(params.get("agent_latency_threshold", 300))
                            if r["latency"] > fixed_limit:
                                is_spike = True
                                r["expected"] = f"<{fixed_limit}"
                        
                        if is_spike:
                            anomalies_found.append(r)

                await session.commit()
                
                # 4. Global State Judgement
                # CHANGED: Alert on ANY anomaly (HTTP, DNS, ICMP)
                
                is_degradation = False
                if len(anomalies_found) > 0:
                    is_degradation = True
                    print(f"[IA-AGENT] Degradation detected on: {[a['target'] for a in anomalies_found]}")
                
                if is_degradation:
                    anomaly_streak += 1
                    print(f"[IA-AGENT] Anomaly Streak: {anomaly_streak}/{ANOMALY_LIMIT}")
                else:
                    if anomaly_streak > 0:
                         print("[IA-AGENT] Streak reset to 0 (Normal)")
                    anomaly_streak = 0
                    state_status = "NORMAL"

                # 5. Alert Trigger
                print(f"[IA-AGENT-DEBUG] Checking alert: streak={anomaly_streak}, limit={ANOMALY_LIMIT}, status={state_status}")
                if anomaly_streak >= ANOMALY_LIMIT and state_status != "ALERTED":
                    state_status = "ALERTED"
                    
                    # Build Smart Message
                    avg_lat = sum([r["latency"] for r in anomalies_found]) / len(anomalies_found)
                    
                    msg = (
                        "🚨 *IA DETECTOU DEGRADAÇÃO* 🚨\n\n"
                        "📉 *Status:* Instabilidade Confirmada\n"
                        f"⏱️ *Latência Média:* {round(avg_lat)}ms\n"
                        f"🕒 *Horário:* {current_hour}:00h\n\n"
                        "🔍 *Análise Estatística:*\n"
                    )
                    
                    for a in anomalies_found:
                        z_info = f"(Z-Score: {a.get('z_score', '?')})" if a.get('z_score') else ""
                        msg += f"• {a['target']}: 🐢 {int(a['latency'])}ms {z_info}\n"
                        msg += f"  (Normal p/ horário: {a.get('expected')}ms)\n"
                        
                    msg += "\n⚠️ O sistema aprendeu que isso é incomum para agora."

                    # Send Multichannel Notification
                    # Fetch notification config from DB
                    notif_params = await session.execute(select(Parameters).where(Parameters.key.in_([
                        'telegram_token', 'telegram_chat_id', 'telegram_enabled',
                        'whatsapp_enabled', 'whatsapp_target', 'whatsapp_target_group',
                        'notify_agent'
                    ])))
                    notif_config = {p.key: p.value for p in notif_params.scalars().all()}
                    
                    # Only send if agent notifications are enabled
                    if notif_config.get('notify_agent', 'true').lower() == 'true':
                        from backend.app.services.notifier import send_notification
                        
                        await send_notification(
                            message=msg,
                            telegram_token=notif_config.get('telegram_token'),
                            telegram_chat_id=notif_config.get('telegram_chat_id'),
                            telegram_enabled=notif_config.get('telegram_enabled', 'true').lower() == 'true',
                            whatsapp_enabled=notif_config.get('whatsapp_enabled', 'false').lower() == 'true',
                            whatsapp_target=notif_config.get('whatsapp_target'),
                            whatsapp_target_group=notif_config.get('whatsapp_target_group')
                        )

        except Exception as e:
            print(f"[IA-AGENT] Job Error: {e}")

        # Sleep logic
        try:
             async with AsyncSessionLocal() as session:
                interval_res = await session.execute(select(Parameters).where(Parameters.key == "agent_interval"))
                row = interval_res.scalar_one_or_none()
                sleep_sec = int(row.value) if row else DEFAULT_INTERVAL
        except:
            sleep_sec = DEFAULT_INTERVAL
            
        await asyncio.sleep(sleep_sec)

if __name__ == "__main__":
    asyncio.run(synthetic_agent_job())
