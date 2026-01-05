"""
Daily Signal Report Service
Sends a daily report of the worst performing radios (signal/CCQ)
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, Parameters
from backend.app.services.notifier import send_notification
from loguru import logger

async def generate_daily_signal_report():
    """Generate and send daily report of worst performing radios"""
    logger.info("[DAILY REPORT] Generating signal quality report...")
    
    async with AsyncSessionLocal() as session:
        # Get all online stations with signal data
        result = await session.execute(
            select(Equipment.name, Equipment.ip, Equipment.signal_dbm, Equipment.ccq, Equipment.last_checked)
            .where(
                and_(
                    Equipment.is_online == True,
                    Equipment.equipment_type == 'station',
                    Equipment.signal_dbm.isnot(None)
                )
            )
            .order_by(Equipment.signal_dbm.asc())  # Worst signal first (most negative)
        )
        
        all_stations = result.all()
        
        if not all_stations:
            logger.info("[DAILY REPORT] No stations with signal data found")
            return
        
        # Filter worst performers (signal < -70 dBm or CCQ < 70%)
        worst_signal = [s for s in all_stations if s.signal_dbm and s.signal_dbm < -70][:10]
        worst_ccq = [s for s in all_stations if s.ccq and s.ccq < 70][:10]
        
        # Build message
        message = "📊 *RELATÓRIO DIÁRIO DE SINAL*\n\n"
        message += f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        message += f"📡 Total de estações monitoradas: {len(all_stations)}\n\n"
        
        if worst_signal:
            message += "🔴 *TOP 10 PIORES SINAIS:*\n"
            for i, station in enumerate(worst_signal, 1):
                # Check if data is recent (last 24h)
                is_stale = False
                if station.last_checked:
                    age = datetime.utcnow() - station.last_checked
                    is_stale = age > timedelta(hours=24)
                
                stale_marker = " ⏰" if is_stale else ""
                ccq_info = f" | CCQ: {station.ccq}%" if station.ccq else ""
                message += f"{i}. *{station.name}*{stale_marker}\n"
                message += f"   📍 {station.ip} | 📶 {station.signal_dbm} dBm{ccq_info}\n"
            message += "\n"
        
        if worst_ccq:
            message += "🟡 *TOP 10 PIORES CCQ:*\n"
            for i, station in enumerate(worst_ccq, 1):
                is_stale = False
                if station.last_checked:
                    age = datetime.utcnow() - station.last_checked
                    is_stale = age > timedelta(hours=24)
                
                stale_marker = " ⏰" if is_stale else ""
                signal_info = f" | 📶 {station.signal_dbm} dBm" if station.signal_dbm else ""
                message += f"{i}. *{station.name}*{stale_marker}\n"
                message += f"   📍 {station.ip} | CCQ: {station.ccq}%{signal_info}\n"
            message += "\n"
        
        if not worst_signal and not worst_ccq:
            message += "✅ *Todos os rádios estão com bom sinal!*\n"
            message += "Nenhum dispositivo com sinal < -70 dBm ou CCQ < 70%\n\n"
        
        message += "⏰ = Dados desatualizados (>24h)\n"
        message += "💡 Recomendação: Verifique alinhamento e obstruções"
        
        # Get notification config
        params_res = await session.execute(
            select(Parameters).where(Parameters.key.in_([
                'telegram_token', 'telegram_chat_id', 'telegram_enabled',
                'whatsapp_enabled', 'whatsapp_target', 'whatsapp_target_group'
            ]))
        )
        config = {p.key: p.value for p in params_res.scalars().all()}
        
        # Send notification
        await send_notification(
            message=message,
            telegram_token=config.get('telegram_token'),
            telegram_chat_id=config.get('telegram_chat_id'),
            telegram_enabled=config.get('telegram_enabled', 'true').lower() == 'true',
            whatsapp_enabled=config.get('whatsapp_enabled', 'false').lower() == 'true',
            whatsapp_target=config.get('whatsapp_target'),
            whatsapp_target_group=config.get('whatsapp_target_group')
        )
        
        logger.info(f"[DAILY REPORT] Sent report with {len(worst_signal)} bad signals and {len(worst_ccq)} bad CCQs")

async def daily_report_job():
    """Background job that sends daily signal report at 8 AM"""
    while True:
        try:
            # Calculate time until next 8 AM
            now = datetime.now()
            next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
            
            # If already past 8 AM today, schedule for tomorrow
            if now.hour >= 8:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            
            logger.info(f"[DAILY REPORT] Next report scheduled for {next_run.strftime('%d/%m/%Y %H:%M')}")
            await asyncio.sleep(wait_seconds)
            
            # Send report
            await generate_daily_signal_report()
            
        except Exception as e:
            logger.error(f"[DAILY REPORT] Error: {e}")
            # Wait 1 hour before retry on error
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(generate_daily_signal_report())
