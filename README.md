# 📡 ISP Monitor - Sistema de Monitoramento para Provedores de Internet

Sistema completo de monitoramento de torres e equipamentos para provedores de internet, com rastreamento de técnicos em tempo real e notificações multicanal (WhatsApp/Telegram).

**Desenvolvido com tecnologia de ponta para alta disponibilidade e auto-recuperação.**

---

## ⚡ Instalação Automática (Zero Config)

**Novo usuário? Execute o Launcher Inteligente:**

1. **Duplo clique** em `ABRIR_SISTEMA.bat`
2. O sistema verificará automaticamente:
   - ✅ Python & Dependências
   - ✅ Node.js & Módulos
   - ✅ Banco de Dados (PostgreSQL)
3. Se algo faltar, o instalador corrigirá automaticamente.

---


## 🚀 Novidades da Versão 4.5 (03/01/2026) - Precision Edition

### 🎯 1. Ping Cirúrgico (Precision Mode V3)
Reformulação completa da lógica de ping para eliminar interferência do sistema operacional, equiparando a precisão ao CMD/Zabbix:
- **Latência Mínima (Min RTT)**: Sistema agora descarta picos artificiais causados por processamento, focando apenas na resposta física mais rápida do cabo.
- **High Priority Process**: O coletor agora roda com prioridade de tempo real no Windows, "furando" a fila do processador.
- **Calibração de Driver**: Implementação de compensação matemática (Overhead Calibration) para isolar o tempo de pilha de software do tempo de rede real.
- **Resultado**: Gráficos perfeitos de 0-1ms em rede local, eliminando o "jitter" fantasma.

### 🔌 2. Launcher & UX Refinado
- **Silent Mode**: Fim das janelas pop-up intrusivas ao parar o sistema. Agora o feedback é integrado de forma elegante na barra de status.
- **Smart Kill**: O encerramento de processos agora é cirúrgico, listando exatamente o que foi fechado sem travar a interface.

### 🏥 3. Monitoramento de Hardware Avançado (V4.4 Legacy)
Suporte completo para sensores de saúde de equipamentos (foco em MikroTik):
- **Métricas Completas**: CPU, Memória RAM, Uso de Disco (Flash/HDD), Temperatura e Voltagem.
- **Detecção Inteligente**: O sistema descobre automaticamente os sensores corretos via varredura SNMP dinâmica.

---

## 🚀 Início Rápido

### **1. Iniciar o Sistema (Tudo em Um)**

```bash
# Modo Interface Gráfica (Recomendado)
./ABRIR_SISTEMA.bat

# Modo Servidor / Headless (Para VPS ou Task Scheduler)
./INICIAR_MODO_SERVIDOR.bat
```

### **2. Acessar o Admin Panel**

```
http://localhost:5173 (ou porta definida)
Email: diegojlc22@gmail.com
Senha: 110812
```

---

## 📁 Estrutura do Projeto (Reorganizada)

```
isp_monitor/
├── 📱 mobile/              # App React Native + Expo (Técnicos)
├── 🖥️  backend/             # API FastAPI + PostgreSQL (Core)
│   └── app/               # Lógica da Aplicação (Routers, Models, Services)
├── 💻 frontend/            # Admin Panel React + Vite
├── 🛠️  scripts/             # Scripts Utilitários
│   ├── self_heal.py       # Watchdog Principal (Doctor)
│   ├── diagnostics/       # Ferramentas de diagnóstico manual
│   ├── legacy_migrations/ # Histórico de migrações e scripts antigos
│   └── tests_manual/      # Scripts de teste simples
├── 📊 logs/                # Logs centralizados
├── 🚀 ABRIR_SISTEMA.bat    # Launcher GUI
└── 🤖 INICIAR_MODO_SERVIDOR.bat # Launcher Headless
```

---

## ✨ Funcionalidades Principais

### **Monitoramento & Alertas**
- 📡 **Pinger Ultra-Rápido**: Monitoramento ICMP assíncrono (estilo The Dude).
- 🔔 **Notificações Inteligentes**: Envia alertas apenas quando necessário (evita spam).
- 💚 **WhatsApp & Telegram**: Suporte nativo e simultâneo.
- 🕒 **Histórico de Latência**: Gráficos de performance.

### **Gestão de Rede**
- 🗺️ **Mapa em Tempo Real**: Localização de torres e clientes.
- 🔗 **Topologia Automática**: Visualização de links entre torres.
- 💾 **PostgreSQL Otimizado**: Configurado para alta performance.

### **App do Técnico**
- 📍 **Rastreamento GPS Otimizado**: Economia de bateria (só envia ao mover).
- 📱 **Interface Clean**: Focado na produtividade em campo.

---

## 🌐 Acesso Externo (Ngrok)

O sistema integra o **Ngrok** nativamente para permitir acesso fora da rede local (ex: 4G).
A URL pública é gerada automaticamente e exibida no Launcher.

---

## 🤝 Suporte & Manutenção

**Auto-Reparo:**
O sistema possui um **Watchdog** (`self_heal.py`) que roda em paralelo. Se o sistema parar, ele reinicia automaticamente.

**Contato do Desenvolvedor:**
- 📧 Email: diegojlc22@gmail.com
- 🤖 AI Assistant: Antigravity (Google Deepmind)

---

## 🎉 Status do Projeto

**✅ VERSÃO ESTÁVEL (Production Ready)**

- ✅ API & Banco de Dados: **Online**
- ✅ Frontend Dashboard: **Online**
- ✅ Gateway WhatsApp: **Online**
- ✅ App Mobile: **Online**
- ✅ Watchdog: **Ativo**

**Última atualização:** 03/01/2026
**Build:** v4.5.0 (Precision Edition)


---

**Desenvolvido com ❤️ para otimizar o trabalho dos provedores ISP.**
