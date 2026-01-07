import asyncio
import sys
import os

# Adicionar root ao path
sys.path.append(os.getcwd())

from backend.app.services.snmp import detect_brand, get_snmp_interfaces

async def main():
    ip = "192.168.80.8"
    communities = ["public", "publicRadionet", "ozoniotelecom", "private"] 
    
    print(f"--- DIAGNÓSTICO MANUAL PARA {ip} ---")
    
    found = False
    for comm in communities:
        print(f"\n🔍 Tentando comunidade: '{comm}'...")
        try:
            brand = await detect_brand(ip, comm)
            print(f"   Resultado detect_brand: {brand}")
            
            if brand and brand != 'generic':
                print(f"   ✅ SUCESSO! Marca identificada: {brand}")
                
                print("   📡 Buscando interfaces...")
                ifaces = await get_snmp_interfaces(ip, comm)
                print(f"   ✅ Encontradas {len(ifaces)} interfaces.")
                if ifaces:
                    print(f"      Exemplos: {[i['name'] for i in ifaces[:5]]}")
                found = True
                break
            else:
                # Se retornou generic, tenta listar interfaces para ver se a comunidade funciona mesmo assim
                print("   ⚠️ Marca genérica. Testando acesso às interfaces...")
                ifaces = await get_snmp_interfaces(ip, comm)
                if len(ifaces) > 0:
                     print(f"   ✅ SUCESSO (Genérico)! Acesso SNMP OK. Interfaces: {len(ifaces)}")
                     found = True
                     break
                else:
                     print("   ❌ Acesso SNMP falhou (sem interfaces).")

        except Exception as e:
            print(f"   💥 Erro: {e}")

    if not found:
        print("\n❌ FALHA TOTAL: Nenhuma comunidade funcionou ou dispositivo não suporta SNMP.")

if __name__ == "__main__":
    asyncio.run(main())
