"""
Script DIRETO para testar mensagens WhatsApp
Envia direto para o gateway sem passar pelo notifier
"""
import asyncio
import aiohttp

# Configuração
GATEWAY_URL = "http://127.0.0.1:3001/send"
API_KEY = "de2f2895-7329-4b46-b9f0-e45f3dc54b34"  # API Key do .env
TARGET = "120363406257973793@g.us"  # Grupo configurado

async def send_direct(message: str):
    """Envia mensagem direto para o gateway"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "number": TARGET,
                "message": message
            }
            headers = {"x-api-key": API_KEY}
            
            async with session.post(GATEWAY_URL, json=payload, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    print(f"✅ Enviada com sucesso!")
                else:
                    text = await resp.text()
                    print(f"❌ Erro {resp.status}: {text}")
    except Exception as e:
        print(f"❌ Exceção: {e}")

async def test_all_messages():
    """Envia exemplos de todas as mensagens do sistema"""
    
    print("🚀 Iniciando testes de mensagens WhatsApp (DIRETO)...")
    print("=" * 60)
    
    # 1. Alerta de Equipamento OFFLINE
    print("\n📤 Enviando: Alerta de Equipamento OFFLINE...")
    await send_direct(
        "🔴 *ALERTA - EQUIPAMENTO OFFLINE*\n\n"
        "📡 *Equipamento:* PTP-TORRE-CENTRO\n"
        "🌐 *IP:* 192.168.1.10\n"
        "📍 *Torre:* Torre Principal\n"
        "⏰ *Horário:* 05/01/2026 11:25\n"
        "⚠️ *Status:* OFFLINE há 2 minutos\n\n"
        "🔧 Verifique a conectividade do equipamento."
    )
    await asyncio.sleep(2)
    
    # 2. Alerta de Equipamento ONLINE (Recuperado)
    print("📤 Enviando: Alerta de Equipamento ONLINE...")
    await send_direct(
        "✅ *RECUPERADO - EQUIPAMENTO ONLINE*\n\n"
        "📡 *Equipamento:* PTP-TORRE-CENTRO\n"
        "🌐 *IP:* 192.168.1.10\n"
        "📍 *Torre:* Torre Principal\n"
        "⏰ *Horário:* 05/01/2026 11:30\n"
        "🟢 *Status:* ONLINE\n"
        "⏱️ *Downtime:* 5 minutos\n\n"
        "✨ Equipamento voltou ao normal!"
    )
    await asyncio.sleep(2)
    
    # 3. Relatório Diário de Sinal
    print("📤 Enviando: Relatório Diário de Sinal...")
    await send_direct(
        "📊 *RELATÓRIO DIÁRIO DE SINAL*\n\n"
        "📅 05/01/2026 08:00\n"
        "📡 Total de estações: 145\n\n"
        "🔴 *TOP 5 PIORES SINAIS:*\n"
        "1. Cliente-João Silva\n"
        "   📍 192.168.100.50 | 📶 -86 dBm | CCQ: 45%\n\n"
        "2. Cliente-Maria Santos\n"
        "   📍 192.168.100.75 | 📶 -82 dBm | CCQ: 55%\n\n"
        "3. Cliente-Pedro Costa\n"
        "   📍 192.168.100.90 | 📶 -79 dBm | CCQ: 60%\n\n"
        "4. Cliente-Ana Lima\n"
        "   📍 192.168.100.120 | 📶 -77 dBm | CCQ: 52%\n\n"
        "5. Cliente-Carlos Souza\n"
        "   📍 192.168.100.135 | 📶 -75 dBm | CCQ: 48%\n\n"
        "💡 *Recomendação:* Verifique alinhamento e obstruções"
    )
    await asyncio.sleep(2)
    
    # 4. Auditoria de Segurança
    print("📤 Enviando: Auditoria de Segurança...")
    await send_direct(
        "🔒 *AUDITORIA DE SEGURANÇA SEMANAL*\n\n"
        "📅 05/01/2026 10:00\n"
        "⚠️ *Encontrados 3 dispositivos vulneráveis*\n\n"
        "🔴 *PTP-CLIENTE-A* (192.168.2.5)\n"
        "  • ⚠️ Senha padrão detectada (SSH)\n"
        "  • ⚠️ SNMP community padrão: public\n"
        "  • ⚠️ Porta 23 aberta (Telnet)\n\n"
        "🟠 *PTP-CLIENTE-B* (192.168.2.10)\n"
        "  • ⚠️ Porta 80 aberta (HTTP)\n\n"
        "🟡 *Torre-Buriti* (192.168.1.5)\n"
        "  • ⚠️ SNMP: public, private\n\n"
        "🛡️ *Ação Requerida:* Altere senhas padrão e desabilite serviços inseguros!"
    )
    await asyncio.sleep(2)
    
    # 5. Alerta de Capacidade
    print("📤 Enviando: Alerta de Capacidade...")
    await send_direct(
        "📈 *ALERTA DE CAPACIDADE - ATENÇÃO!*\n\n"
        "📅 05/01/2026\n\n"
        "🔴 *CRÍTICO - JÁ NO LIMITE!*\n"
        "📡 *Link:* PTP-PRINCIPAL\n"
        "🌐 *IP:* 192.168.1.10\n"
        "📊 *Uso atual:* 92 Mbps / 100 Mbps (92%)\n"
        "📈 *Crescimento:* +0.8 Mbps/dia\n"
        "⚠️ *Status:* SATURAÇÃO IMINENTE\n\n"
        "🟠 *URGENTE - 12 DIAS ATÉ LIMITE*\n"
        "📡 *Link:* PTP-BACKBONE\n"
        "🌐 *IP:* 192.168.1.20\n"
        "📊 *Uso atual:* 180 Mbps / 200 Mbps (90%)\n"
        "📈 *Crescimento:* +1.2 Mbps/dia\n"
        "⏰ *Estimativa:* 12 dias até 90%\n\n"
        "💡 *Recomendação:* Planeje upgrade de capacidade urgente!"
    )
    await asyncio.sleep(2)
    
    # 6. Alerta do Agente IA (Degradação)
    print("📤 Enviando: Alerta do Agente IA...")
    await send_direct(
        "🤖 *AGENTE IA - DEGRADAÇÃO DETECTADA*\n\n"
        "📅 05/01/2026 11:15\n"
        "🎯 *Alvo:* google.com (HTTP)\n\n"
        "⚠️ *ANOMALIA CONFIRMADA*\n"
        "📊 *Latência atual:* 285ms\n"
        "📈 *Baseline (30 dias):* 45ms ± 12ms\n"
        "🔺 *Desvio:* +533% (Z-score: 20.0)\n"
        "🔄 *Ciclos anômalos:* 3/3\n\n"
        "🌐 *Possíveis causas:*\n"
        "  • Congestionamento de rede\n"
        "  • Problema no provedor upstream\n"
        "  • Rota instável\n\n"
        "🔧 *Ação:* Verifique conectividade e rotas!"
    )
    await asyncio.sleep(2)
    
    # 7. Alerta de Torre OFFLINE (Topologia)
    print("📤 Enviando: Alerta de Torre OFFLINE...")
    await send_direct(
        "🗼 *ALERTA - TORRE OFFLINE*\n\n"
        "📡 *Torre:* Torre Buriti\n"
        "🌐 *IP:* 192.168.1.5\n"
        "⏰ *Horário:* 05/01/2026 11:20\n"
        "⚠️ *Status:* OFFLINE há 3 minutos\n\n"
        "📊 *Impacto:*\n"
        "  • 15 equipamentos afetados\n"
        "  • 45 clientes sem conexão\n\n"
        "🔴 *(Silenciados por topologia: 15 alertas)*\n\n"
        "🔧 Verifique energia e conectividade da torre!"
    )
    
    print("\n" + "=" * 60)
    print("✅ Todos os exemplos de mensagens foram enviados!")
    print("📱 Verifique seu WhatsApp para ver como ficaram formatadas.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_all_messages())
