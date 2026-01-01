import asyncio
import sys
import os
import time
from sqlalchemy import select, update

# Add root path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic

TARGETS = [
    "10.50.1.2",       # AirFiber
    "192.168.103.2",   # Mikrotik
    "192.168.80.13",   # Ubiquiti
    "192.168.177.30",  # Intelbras
    "192.168.148.200", # Mimosa
]

COMMUNITIES = ["publicRadionet", "public"]

async def find_best_interface(ip, specific_community=None):
    print(f"\n🔍 Analisando {ip}...")
    
    # 1. Detect Community & Interfaces
    interfaces = None
    working_community = None

    comms_to_try = [specific_community] if specific_community else COMMUNITIES

    for comm in comms_to_try:
        if not comm: continue
        try:
            ints = await get_snmp_interfaces(ip, comm)
            if ints:
                interfaces = ints
                working_community = comm
                print(f"   ✅ Community encontrada: '{comm}' ({len(ints)} interfaces)")
                break
        except Exception as e:
            # print(f"   (Debug: Falha com {comm}: {e})")
            pass
    
    if not interfaces:
        print("   ❌ Não foi possível comunicar via SNMP (verifique IP/Community).")
        return None, None

    # 2. Measure Traffic
    print("   🚦 Medindo tráfego em todas as interfaces (Aguarde 3s)...")
    
    # First Pass
    counters_1 = {}
    for iface in interfaces:
        idx = iface['index']
        res = await get_snmp_interface_traffic(ip, working_community, 161, idx)
        if res:
            counters_1[idx] = {'t': time.time(), 'in': res[0], 'out': res[1]}
    
    await asyncio.sleep(3)

    # Second Pass & Max logic
    best_idx = None
    max_traffic = -1
    best_desc = ""

    for iface in interfaces:
        idx = iface['index']
        name = iface['name']
        if idx not in counters_1:
            continue
            
        try:
            res = await get_snmp_interface_traffic(ip, working_community, 161, idx)
            if res:
                c1 = counters_1[idx]
                dt = time.time() - c1['t']
                delta_in =  max(0, res[0] - c1['in'])
                delta_out = max(0, res[1] - c1['out'])
                
                # Total Mbps
                mbps = ((delta_in + delta_out) * 8) / (dt * 1_000_000)
                
                if mbps > 0.01:
                    print(f"      - [{idx}] {name}: {mbps:.2f} Mbps")
                
                if mbps > max_traffic:
                    max_traffic = mbps
                    best_idx = idx
                    best_desc = f"{name} ({mbps:.2f} Mbps)"
        except:
            pass

    if best_idx:
        print(f"   🏆 VENCEDOR: Interface {best_idx} - {best_desc}")
        return best_idx, working_community
    else:
        print("   ⚠️ Nenhuma interface com tráfego relevante encontrada. Mantendo atual.")
        return None, working_community


async def main():
    print("🚀 Iniciando Auto-Configuração de Interfaces de Tráfego\n")
    
    async with AsyncSessionLocal() as db:
        for ip in TARGETS:
            # Get current DB record to check community preference
            stmt = select(Equipment).where(Equipment.ip == ip)
            res = await db.execute(stmt)
            eq = res.scalar_one_or_none()
            
            db_comm = eq.snmp_community if eq else None
            
            # Find best interface
            best_idx, valid_comm = await find_best_interface(ip, specific_community=db_comm)

            if best_idx and eq:
                # Update DB
                eq.snmp_traffic_interface_index = best_idx
                # Also update snmp_interface_index as fallback
                eq.snmp_interface_index = best_idx 
                
                if valid_comm and valid_comm != eq.snmp_community:
                    eq.snmp_community = valid_comm
                    print(f"      📝 Atualizando Community para '{valid_comm}'")
                
                await db.commit()
                print(f"      💾 Configuração SALVA no banco para {eq.name}!")
            elif not eq:
                print(f"      ❌ Equipamento {ip} não está cadastrado no banco.")

    print("\n✅ Processo finalizado.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
