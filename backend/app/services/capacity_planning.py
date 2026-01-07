"""
Capacity Planning Service
Analyzes traffic trends and predicts when links will reach capacity
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, TrafficLog, Parameters, Insight
from backend.app.services.notifier import send_notification
from loguru import logger

async def analyze_capacity_trends():
    """Analyze traffic growth and predict capacity issues"""
    logger.info("[CAPACITY PLANNING] Analyzing traffic trends...")
    
    warnings = []
    
    async with AsyncSessionLocal() as session:
        # Get equipment with significant traffic (> 10 Mbps average) AND marked as priority
        result = await session.execute(
            select(Equipment.id, Equipment.name, Equipment.ip, Equipment.last_traffic_in, Equipment.last_traffic_out)
            .where(
                and_(
                    Equipment.is_online == True,
                    Equipment.is_priority == True,  # Only analyze priority equipment
                    Equipment.last_traffic_in > 10  # Only analyze links with real usage
                )
            )
        )
        
        active_links = result.all()
        
        for eq_id, name, ip, current_in, current_out in active_links:
            # Get traffic history for last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # Define trunc expression to ensure consistency in GROUP BY
            trunc_date = func.date_trunc('day', TrafficLog.timestamp)
            
            history_result = await session.execute(
                select(
                    trunc_date.label('day'),
                    func.max(TrafficLog.in_mbps).label('max_in'),
                    func.max(TrafficLog.out_mbps).label('max_out')
                )
                .where(
                    and_(
                        TrafficLog.equipment_id == eq_id,
                        TrafficLog.timestamp >= thirty_days_ago
                    )
                )
                .group_by(trunc_date)
                .order_by(trunc_date)
            )
            
            daily_peaks = history_result.all()
            
            if len(daily_peaks) < 7:  # Need at least 1 week of data
                continue
            
            # Calculate growth rate (simple linear regression)
            days = [(i, max(row.max_in or 0, row.max_out or 0)) for i, row in enumerate(daily_peaks)]
            
            if len(days) < 2:
                continue
            
            # Simple linear trend: y = mx + b
            n = len(days)
            sum_x = sum(d[0] for d in days)
            sum_y = sum(d[1] for d in days)
            sum_xy = sum(d[0] * d[1] for d in days)
            sum_x2 = sum(d[0] ** 2 for d in days)
            
            # Slope (growth per day in Mbps)
            if (n * sum_x2 - sum_x ** 2) == 0:
                continue
                
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            
            # Only warn if growing (positive slope)
            if slope <= 0:
                continue
            
            # Assume link capacity (common values)
            # Try to detect from current peak
            current_peak = max(current_in, current_out)
            
            # Estimate capacity based on current usage with more common link steps
            if current_peak < 85:
                estimated_capacity = 100  # 100 Mbps link
            elif current_peak < 180:
                estimated_capacity = 200  # 200 Mbps link
            elif current_peak < 270:
                estimated_capacity = 300  # 300 Mbps link
            elif current_peak < 420:
                estimated_capacity = 500  # 500 Mbps link
            elif current_peak < 750:
                estimated_capacity = 800  # 800 Mbps link
            else:
                estimated_capacity = 1000  # 1 Gbps link
            
            # Calculate days until 90% capacity
            usage_threshold = estimated_capacity * 0.9
            remaining_capacity = usage_threshold - current_peak
            
            if remaining_capacity <= 0:
                # Already at capacity!
                warnings.append({
                    "name": name,
                    "ip": ip,
                    "current": round(current_peak, 1),
                    "capacity": estimated_capacity,
                    "days_until_full": 0,
                    "growth_rate": round(slope, 2)
                })
            elif slope > 0:
                days_until_full = remaining_capacity / slope
                
                # Warn if will reach capacity in next 60 days
                if days_until_full < 60:
                    warnings.append({
                        "id": eq_id,
                        "name": name,
                        "ip": ip,
                        "current": round(current_peak, 1),
                        "capacity": estimated_capacity,
                        "days_until_full": int(days_until_full),
                        "growth_rate": round(slope, 2)
                    })
                    
                    # Salvar no banco como Insight
                    severity = 'critical' if days_until_full < 10 else 'warning'
                    session.add(Insight(
                        insight_type='capacity',
                        severity=severity,
                        equipment_id=eq_id,
                        title=f"Saturação de link em {name}",
                        message=f"Uso atual: {round(current_peak, 1)} Mbps. Capacidade estimada: {estimated_capacity} Mbps. Crescimento: +{round(slope, 2)} Mbps/dia.",
                        recommendation=f"Estimado {int(days_until_full)} dias para atingir 90% da capacidade. Planeje upgrade."
                    ))
        
        await session.commit()
    
    # Send report if warnings found
    if warnings:
        message = "📈 *ALERTA DE CAPACIDADE*\n\n"
        message += f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        message += f"⚠️ {len(warnings)} links precisam de atenção:\n\n"
        
        # Sort by urgency (days until full)
        warnings.sort(key=lambda x: x['days_until_full'])
        
        for w in warnings[:10]:  # Top 10 most urgent
            if w['days_until_full'] == 0:
                urgency = "🔴 *CRÍTICO - JÁ NO LIMITE!*"
            elif w['days_until_full'] < 15:
                urgency = "🟠 *URGENTE*"
            else:
                urgency = "🟡 *ATENÇÃO*"
            
            message += f"{urgency}\n"
            message += f"*{w['name']}* ({w['ip']})\n"
            message += f"📊 Uso atual: {w['current']} Mbps / {w['capacity']} Mbps ({int(w['current']/w['capacity']*100)}%)\n"
            message += f"📈 Crescimento: +{w['growth_rate']} Mbps/dia\n"
            
            if w['days_until_full'] > 0:
                message += f"⏰ Estimativa: {w['days_until_full']} dias até 90% de capacidade\n"
            
            message += "\n"
        
        if len(warnings) > 10:
            message += f"... e mais {len(warnings) - 10} links.\n\n"
        
        message += "💡 Recomendação: Planeje upgrade de capacidade"
        
        # Get notification config
        async with AsyncSessionLocal() as session:
            params_res = await session.execute(
                select(Parameters).where(Parameters.key.in_([
                    'telegram_token', 'telegram_chat_id', 'telegram_enabled',
                    'whatsapp_enabled', 'whatsapp_target', 'whatsapp_target_group'
                ]))
            )
            config = {p.key: p.value for p in params_res.scalars().all()}
        
        await send_notification(
            message=message,
            telegram_token=config.get('telegram_token'),
            telegram_chat_id=config.get('telegram_chat_id'),
            telegram_enabled=config.get('telegram_enabled', 'true').lower() == 'true',
            whatsapp_enabled=config.get('whatsapp_enabled', 'false').lower() == 'true',
            whatsapp_target=config.get('whatsapp_target'),
            whatsapp_target_group=config.get('whatsapp_target_group')
        )
        
        logger.info(f"[CAPACITY PLANNING] Sent alert for {len(warnings)} links")
    else:
        logger.info("[CAPACITY PLANNING] All links have healthy capacity")

async def capacity_planning_job():
    """Background job that runs capacity analysis at configured interval"""
    while True:
        try:
            # Check last run
            now = datetime.now()
            should_run = False
            
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(Parameters).where(Parameters.key == "capacity_planning_last_run")
                )
                last_run_param = res.scalar_one_or_none()
                
                res_days = await session.execute(
                    select(Parameters).where(Parameters.key == "capacity_planning_days")
                )
                days_param = res_days.scalar_one_or_none()
                days = int(days_param.value) if days_param else 7

                if not last_run_param:
                    should_run = True
                else:
                    last_run = datetime.fromisoformat(last_run_param.value)
                    if (now - last_run).total_seconds() >= days * 86400:
                        should_run = True

            if should_run:
                await analyze_capacity_trends()
                async with AsyncSessionLocal() as session:
                    # Update last run
                    res = await session.execute(
                        select(Parameters).where(Parameters.key == "capacity_planning_last_run")
                    )
                    param = res.scalar_one_or_none()
                    if not param:
                        session.add(Parameters(key="capacity_planning_last_run", value=now.isoformat()))
                    else:
                        param.value = now.isoformat()
                    await session.commit()
            else:
                logger.info("[CAPACITY] Analysis skipped (already ran recently).")

        except Exception as e:
            logger.error(f"[CAPACITY PLANNING] Error: {e}")
        
        await asyncio.sleep(3600)  # Check every hour

if __name__ == "__main__":
    asyncio.run(analyze_capacity_trends())
