import asyncio
import sys
import os
from sqlalchemy import select, text

# Add root path
sys.path.append(os.getcwd())

from backend.app.database import get_db, AsyncSessionLocal
from backend.app.models import Parameters

async def repair_dashboard_layout():
    """
    Checks if the 'dashboard_layout' key exists in the 'parameters' table.
    If not, or if it is invalid, it attempts to clean or initialize it.
    """
    async with AsyncSessionLocal() as db:
        print("🔍 Verificando integridade da chave 'dashboard_layout' no banco...")
        try:
            # 1. Check if key exists
            res = await db.execute(select(Parameters).where(Parameters.key == "dashboard_layout"))
            param = res.scalar_one_or_none()

            if not param:
                print("⚠️ Chave 'dashboard_layout' não encontrada. Criando vazia...")
                new_param = Parameters(key="dashboard_layout", value="[]")
                db.add(new_param)
                await db.commit()
                print("✅ Chave criada com sucesso.")
            else:
                print(f"ℹ️ Chave encontrada.")
                # Validate JSON
                import json
                try:
                    layout = json.loads(param.value)
                    if not isinstance(layout, list):
                        print("❌ Valor inválido (não é lista). Resetando...")
                        param.value = "[]"
                        await db.commit()
                        print("✅ Resetado para lista vazia.")
                    else:
                        print(f"✅ Layout válido com {len(layout)} widgets.")
                except json.JSONDecodeError:
                    print("❌ JSON Corrompido. Resetando...")
                    param.value = "[]"
                    await db.commit()
                    print("✅ Resetado para lista vazia.")

        except Exception as e:
            print(f"❌ Erro Crítico ao acessar banco: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(repair_dashboard_layout())
