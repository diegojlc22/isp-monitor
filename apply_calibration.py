import asyncio
from sqlalchemy import text
from backend.app.database import engine

async def calibrate_equipment():
    # IP do equipamento do print
    target_ip = '192.168.106.62'
    
    # Exemplo: Se o rádio lê 26.2V e no multímetro dá 27.5V 
    # O multiplicador seria 27.5 / 26.2 = 1.0496
    multiplier = 1.05 # Ajuste de 5% para cima como exemplo
    offset = 0.0
    
    async with engine.begin() as conn:
        print(f"Aplicando calibração para {target_ip}...")
        await conn.execute(
            text("UPDATE equipments SET voltage_multiplier = :m, voltage_offset = :o WHERE ip = :ip"),
            {"m": multiplier, "o": offset, "ip": target_ip}
        )
        print("✅ Calibração aplicada no banco de dados!")

if __name__ == "__main__":
    asyncio.run(calibrate_equipment())
