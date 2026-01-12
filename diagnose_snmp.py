import asyncio
import sys
import os

# Adiciona o diretório raiz ao path para importar backend
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select
from backend.app.services.snmp import get_snmp_uptime, detect_equipment_name
from icmplib import async_multiping

async def ping_host(ip):
    try:
        results = await async_multiping([ip], count=1, timeout=2, privileged=False)
        for host in results:
            if host.is_alive:
                return host.avg_rtt
        return None
    except:
        return None

async def diagnose_ip(target_ip):
    print(f"\n--- DIAGNÓSTICO PARA {target_ip} ---")
    
    # 1. Check DB Info
    print("[1] Buscando dados no Banco...")
    db_eq = None
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Equipment).where(Equipment.ip == target_ip))
        db_eq = res.scalar()
        
    if not db_eq:
        print("❌ IP não encontrado no banco de dados!")
        community = "public"
    else:
        print(f"✅ Encontrado: {db_eq.name}")
        print(f"   Community Configurada: '{db_eq.snmp_community}'")
        print(f"   Marca: {db_eq.brand}")
        community = db_eq.snmp_community or "public"

    # 2. Test Ping
    print(f"\n[2] Testando PING para {target_ip}...")
    latency = await ping_host(target_ip)
    if latency is not None:
        print(f"✅ PING OK! Latência: {latency}ms")
    else:
        print("❌ PING FALHOU! Dispositivo parece inacessível.")
        # Se falhar ping, SNMP provavelmente falhará, mas tentaremos
        
    # 3. Test SNMP (Stored Community)
    print(f"\n[3] Testando SNMP com community '{community}'...")
    uptime = await get_snmp_uptime(target_ip, community)
    if uptime:
        print(f"✅ SNMP OK! Uptime detectado: {uptime}")
        name = await detect_equipment_name(target_ip, community)
        print(f"   Nome detectado via SNMP: {name}")
    else:
        print(f"❌ SNMP FALHOU com '{community}'.")
        
        # 4. Brute Force Fallback
        common_communities = ["public", "private", "isp", "admin", "123456"]
        if community in common_communities: common_communities.remove(community)
        
        print(f"\n[4] Tentando outras communities comuns: {common_communities}...")
        for comm in common_communities:
            print(f"   Tentando '{comm}'...", end="")
            up = await get_snmp_uptime(target_ip, comm)
            if up:
                print(f" ✅ SUCESSO! A community correta parece ser '{comm}'")
                print("   ⚠️ ATUALIZE O CADASTRO DESTE EQUIPAMENTO!")
                break
            else:
                print(" ❌ Falhou")

if __name__ == "__main__":
    # Testar o IP problemático identificado anteriormente
    target = "192.168.103.247"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    asyncio.run(diagnose_ip(target))
