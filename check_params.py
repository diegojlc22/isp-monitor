
import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Parameters, Equipment

async def check_params():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Parameters))
        params = res.scalars().all()
        print("--- Parâmetros no Banco ---")
        for p in params:
            print(f"{p.key}: {p.value}")
        
        print("\n--- Equipamento Especifico (62) ---")
        res = await session.execute(select(Equipment).where(Equipment.ip == '192.168.106.62'))
        eq = res.scalar_one_or_none()
        if eq:
            print(f"Nome: {eq.name}")
            print(f"Voltagem Atual: {eq.voltage}V")
            print(f"Threshold: {eq.min_voltage_threshold}V")
            print(f"Último Alerta: {eq.last_voltage_alert_sent}")
            print(f"Intervalo Alerta: {eq.voltage_alert_interval}")
        else:
            print("Equipamento 192.168.106.62 não encontrado.")

if __name__ == "__main__":
    asyncio.run(check_params())
