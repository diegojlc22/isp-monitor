
import asyncio
import os
import sys
from sqlalchemy import select, desc

# Adicionar raiz ao path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import SyntheticLog

async def show_logs():
    async with AsyncSessionLocal() as session:
        stmt = select(SyntheticLog).order_by(desc(SyntheticLog.timestamp)).limit(10)
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        print("\n=== ÚLTIMOS 10 LOGS DO AGENTE INTELIGENTE ===")
        if not logs:
            print("Nenhum log encontrado.")
        for log in logs:
            status = "✅ OK" if log.success else "❌ FALHA"
            print(f"[{log.timestamp}] {log.test_type.upper()} -> {log.target}: {log.latency_ms:.2f}ms | {status}")
        print("============================================\n")

if __name__ == "__main__":
    asyncio.run(show_logs())
