import asyncio
from sqlalchemy import text
from backend.app.database import engine

async def fix_and_calibrate():
    async with engine.begin() as conn:
        print("1. Garantindo estrutura das colunas...")
        await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS voltage_multiplier FLOAT DEFAULT 1.0"))
        await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS voltage_offset FLOAT DEFAULT 0.0"))
        
        print("2. Aplicando fator de correção (Ex: +5%)...")
        target_ip = '192.168.106.62'
        multiplier = 1.05  # Ajuste de 5%
        await conn.execute(
            text("UPDATE equipments SET voltage_multiplier = :m, voltage_offset = 0 WHERE ip = :ip"),
            {"m": multiplier, "ip": target_ip}
        )
        print(f"✅ SUCESSO! Equipamento {target_ip} calibrado.")

if __name__ == "__main__":
    asyncio.run(fix_and_calibrate())
