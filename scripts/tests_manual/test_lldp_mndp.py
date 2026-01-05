import asyncio
import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.getcwd())

from backend.app.services.wireless_snmp import get_neighbors_data
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def test_topology_discovery():
    print("="*60)
    print("🚀 INICIANDO TESTE DE DESCOBERTA DE VIZINHOS (LLDP/MNDP)")
    print("="*60)
    
    async with AsyncSessionLocal() as session:
        # Pega equipamentos online que tenham marca detectada
        res = await session.execute(
            select(Equipment).where(Equipment.is_online == True)
        )
        eqs = res.scalars().all()
        
        if not eqs:
            print("❌ Nenhum equipamento online encontrado para testar.")
            return

        print(f"📡 Testando {len(eqs)} equipamentos...\n")

        for eq in eqs:
            print(f"👉 Analisando: {eq.name} ({eq.ip})")
            print(f"   Marca: {eq.brand} | Comunidade: {eq.snmp_community}")
            
            try:
                # Chama a função de descoberta de vizinhos
                neighbors = await get_neighbors_data(
                    eq.ip, 
                    eq.brand, 
                    eq.snmp_community, 
                    eq.snmp_port or 161
                )
                
                if neighbors:
                    print(f"   ✅ VIZINHOS ENCONTRADOS ({len(neighbors)}):")
                    for n in neighbors:
                        print(f"      - {n.get('name', 'Sem Nome')} IP: {n.get('ip', 'Desconhecido')}")
                else:
                    print("   ℹ️ Nenhum vizinho detectado via SNMP (MNDP/LLDP).")
            except Exception as e:
                print(f"   ❌ Erro ao consultar {eq.ip}: {e}")
            
            print("-" * 30)

    print("\n✅ Teste finalizado.")

if __name__ == "__main__":
    asyncio.run(test_topology_discovery())
