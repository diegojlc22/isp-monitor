import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def list_voltages():
    async with AsyncSessionLocal() as session:
        stmt = select(Equipment.name, Equipment.ip, Equipment.voltage, Equipment.voltage_multiplier, Equipment.voltage_offset)
        result = await session.execute(stmt)
        data = result.all()
        print(f"{'Name':<30} | {'IP':<15} | {'Volt':<6} | {'Mult':<6} | {'Offset':<6}")
        print("-" * 75)
        for row in data:
            volt = f"{row[2]:.2f}" if row[2] is not None else "N/A"
            mult = f"{row[3]:.2f}" if row[3] is not None else "1.00"
            offset = f"{row[4]:.2f}" if row[4] is not None else "0.00"
            print(f"{row[0]:<30} | {row[1]:<15} | {volt:<6} | {mult:<6} | {offset:<6}")

if __name__ == "__main__":
    asyncio.run(list_voltages())
