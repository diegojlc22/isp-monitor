import asyncio
from sqlalchemy import text
from backend.app.database import async_session_factory
from backend.app.models import Equipment

async def check():
    async with async_session_factory() as session:
        # 1. Achar o ID do 192.168.0.1
        res = await session.execute(text("SELECT id, name, is_online FROM equipments WHERE ip = '192.168.0.1'"))
        eq = res.fetchone()
        
        if not eq:
            print("❌ Equipamento 192.168.0.1 não encontrado no banco!")
            return

        print(f"✅ Equipamento Encontrado: ID={eq[0]}, Nome='{eq[1]}', Online={eq[2]}")
        
        # 2. Contar logs na tabela latency_history
        res_count = await session.execute(text(f"SELECT COUNT(*) FROM latency_history WHERE equipment_id = {eq[0]}"))
        count = res_count.scalar()
        print(f"📊 Total de registros em 'latency_history': {count}")

        if count > 0:
            # 3. Mostrar os ultimos 5
            res_last = await session.execute(text(f"SELECT * FROM latency_history WHERE equipment_id = {eq[0]} ORDER BY timestamp DESC LIMIT 5"))
            rows = res_last.fetchall()
            print("📝 Últimos 5 registros:")
            for r in rows:
                print(r)
        else:
            print("⚠️ A tabela latency_history está vazia para este ID. Motivos possíveis:")
            print("   1. O Pinger não está rodando.")
            print("   2. O Pinger acha que está Offline.")
            print("   3. Erro de inserção silencioso.")

if __name__ == "__main__":
    asyncio.run(check())
