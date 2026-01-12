import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Alert, Equipment, PingLog
from datetime import datetime, timedelta

async def check_alerts():
    target_ip = "192.168.96.3"
    print(f"--- Investigando IP {target_ip} ---")
    
    async with AsyncSessionLocal() as session:
        # 1. Pegar detalhes do equipamento
        res = await session.execute(select(Equipment).where(Equipment.ip == target_ip))
        eq = res.scalar_one_or_none()
        
        if not eq:
            print("❌ Equipamento não encontrado no banco de dados!")
            return
            
        print(f"✅ Equipamento Encontrado: {eq.id} - {eq.name}")
        
        # 2. Ver últimos 10 alertas
        print("\n[ALERTAS RECENTES (Última 1h)]")
        since = datetime.utcnow() - timedelta(hours=1)
        stmt = select(Alert).where(Alert.timestamp >= since).order_by(Alert.timestamp.desc())
        res = await session.execute(stmt)
        alerts = res.scalars().all()
        
        found_count = 0
        for a in alerts:
            # Filtra apenas os relevantes (pelo nome ou mensagem genérica se name for null)
            if a.device_name == eq.name or target_ip in a.message:
                print(f"⏰ {a.timestamp} | {a.message}")
                found_count += 1
                
        if found_count == 0:
            print("🚫 Nenhum alerta encontrado para este equipamento.")
            
        # 3. Ver Ping Logs (Prova real)
        print("\n[PING LOGS (Últimos 10)]")
        stmt = select(PingLog).where(PingLog.equipment_id == eq.id).order_by(PingLog.timestamp.desc()).limit(10)
        res = await session.execute(stmt)
        pings = res.scalars().all()
        
        for p in pings:
            status_icon = "🟢" if p.is_online else "🔴"
            print(f"{status_icon} {p.timestamp} | {p.latency_ms}ms | Online: {p.is_online}")

if __name__ == "__main__":
    asyncio.run(check_alerts())
