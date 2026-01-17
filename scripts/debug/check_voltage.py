import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment

async def check_voltage():
    print("Conectando ao banco...")
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Equipment).where(Equipment.ip == '192.168.106.62')
            result = await session.execute(stmt)
            equipment = result.scalar_one_or_none()
            
            if equipment:
                print(f"--- Dados do Equipamento ---")
                print(f"Nome: {equipment.name}")
                print(f"IP: {equipment.ip}")
                print(f"Status: {'ONLINE' if equipment.is_online else 'OFFLINE'}")
                print(f"Voltagem Atual: {equipment.voltage}V")
                print(f"Última Atualização: {equipment.last_ping}")
                print(f"Marca: {equipment.brand}")
            else:
                print("Equipamento 192.168.106.62 não encontrado no banco de dados.")
    except Exception as e:
        print(f"Erro ao consultar: {e}")

if __name__ == "__main__":
    asyncio.run(check_voltage())
