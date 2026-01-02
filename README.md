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


## 🚀 Novidades da Versão 4.4 (02/01/2026) - Zabbix Engine Edition

### ⚡ 1. Novo Motor de Ping (Zabbix Architecture)
O núcleo de monitoramento foi reescrito para precisão cirúrgica:
- **ICMP RAW Real**: Abandono de simulações UDP. Agora usa sockets nativos do kernel (igual ao comando `ping`).
- **Controle de Concorrência**: Sistema de semáforos limita threads "in-flight" para evitar overhead no Windows.
- **Resultado**: Latência precisa (<1ms em rede local) e eliminação de "falsos positivos" em horários de pico.

### 🏥 2. Monitoramento de Hardware Avançado
Suporte completo para sensores de saúde de equipamentos (foco em MikroTik):
- **Métricas Completas**: CPU, Memória RAM, Uso de Disco (Flash/HDD), Temperatura e Voltagem.
- **Detecção Inteligente**: O sistema descobre automaticamente os sensores corretos via varredura SNMP dinâmica.
- **Visualização Premium**: Novos gauges circulares para leitura rápida no painel ao vivo.

### 🏎️ 3. Live Monitor "Turbo Mode"
- **Atualização em Tempo Real**: Telemetria de tráfego e latência agora atualiza a cada 5 segundos (antes 30s).
- **Correção de "Degraus"**: Gráficos suaves e precisos que refletem a realidade instantânea da rede.
- **Auto-Repair de Banco**: Script de migração (`apply_migration_v2.py`) garante integridade das novas colunas.

### 🔒 4. Segurança Reforçada
- **Rotas Protegidas**: Todas as operações críticas (Reboot, Configuração, Delete) agora exigem token JWT.
- **Validação de Banco**: Script de correção de timezone para evitar erros em queries históricas.

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

**Última atualização:** 01/01/2026
**Build:** v4.3.0 (Autonomous Network Edition)


---

**Desenvolvido com ❤️ para otimizar o trabalho dos provedores ISP.**
