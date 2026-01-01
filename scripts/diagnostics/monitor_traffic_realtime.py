"""
Script de Monitoramento em Tempo Real de Tráfego SNMP
Monitora continuamente os equipamentos e mostra se o tráfego está sendo coletado
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from sqlalchemy import select
from backend.app.models import Equipment

async def monitor_traffic():
    print("=" * 80)
    print("🔍 MONITOR DE TRÁFEGO EM TEMPO REAL")
    print("=" * 80)
    print("Aguardando você adicionar equipamentos...")
    print("Pressione Ctrl+C para parar\n")
    
    last_count = 0
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Buscar equipamentos online
                result = await db.execute(
                    select(Equipment)
                    .where(Equipment.is_online == True)
                    .order_by(Equipment.id.desc())
                )
                equipments = result.scalars().all()
                
                # Detectar novos equipamentos
                if len(equipments) > last_count:
                    print(f"\n🆕 NOVO EQUIPAMENTO DETECTADO! Total: {len(equipments)}")
                    last_count = len(equipments)
                
                # Limpar tela e mostrar status
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("=" * 80)
                print(f"🔍 MONITOR DE TRÁFEGO - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 80)
                print(f"📊 Total de Equipamentos Online: {len(equipments)}\n")
                
                if not equipments:
                    print("⏳ Aguardando equipamentos serem adicionados...")
                else:
                    print(f"{'ID':<5} {'Nome':<30} {'IP':<16} {'Marca':<12} {'IN (Mbps)':<12} {'OUT (Mbps)':<12} {'Sinal':<10} {'Status'}")
                    print("-" * 120)
                    
                    for eq in equipments:
                        # Status do tráfego
                        traffic_in = eq.last_traffic_in if eq.last_traffic_in is not None else 0.0
                        traffic_out = eq.last_traffic_out if eq.last_traffic_out is not None else 0.0
                        signal = eq.signal_dbm if eq.signal_dbm is not None else "N/A"
                        
                        # Determinar status
                        if traffic_in > 0 or traffic_out > 0:
                            status = "✅ TRÁFEGO OK"
                        elif signal != "N/A":
                            status = "⚠️ SEM TRÁFEGO (Sinal OK)"
                        else:
                            status = "❌ SEM DADOS"
                        
                        # Formatação
                        name = eq.name[:28] + ".." if len(eq.name) > 30 else eq.name
                        brand = (eq.brand or "generic")[:10]
                        
                        print(f"{eq.id:<5} {name:<30} {eq.ip:<16} {brand:<12} "
                              f"{traffic_in:<12.2f} {traffic_out:<12.2f} {str(signal):<10} {status}")
                
                print("\n" + "=" * 80)
                print("💡 Dica: Adicione equipamentos pela interface web e veja aqui em tempo real!")
                print("🔄 Atualizando a cada 3 segundos... (Ctrl+C para sair)")
                
            await asyncio.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitor encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_traffic())
    except KeyboardInterrupt:
        print("\n\n✅ Monitor finalizado.")
