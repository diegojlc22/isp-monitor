
import asyncio
import os
import sys

# Adicionar raiz ao path
sys.path.append(os.getcwd())

from backend.app.services.synthetic_agent import run_single_test_cycle

async def test():
    print("Iniciando ciclo de teste manual...")
    result = await run_single_test_cycle()
    print("Resultado:", result)

if __name__ == "__main__":
    asyncio.run(test())
