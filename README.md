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


## 🚀 Novidades da Versão 4.3 (01/01/2026) - Autonomous Network Edition

### 🌍 1. Topologia Automática e Descoberta de Rede
O sistema agora "desenha" o mapa da rede sozinho:
- **Auto-Discovery via SNMP**: Uma varredura inteligente detecta vizinhos via **LLDP** e **MNDP**.
- **Desenho Automático de Links**: Criação automática de conexões entre Torres no mapa.
- **Identificação de Equipamentos**: Detecta automaticamente Marca (Ubiquiti/Mikrotik), Tipo (AP/Estação) e MAC Address.
- **Botão "Auto Topologia"**: Integrado ao Mapa para atualização sob demanda.

### �️ 2. Watchdog de Sistema (Doctor V3.7)
Um monitor de processos implacável (`scripts/self_heal.py`) que garante "Imortalidade" ao sistema:
- **Zombie Hunter**: Detecta e mata processos travados ou "zumbis".
- **Auto-Restart**: Se a API, o Coletor ou o WhatsApp cair, ele levanta novamente em segundos.
- **Prevenção de Conflitos**: Mecanismo de **Lock File** garante que apenas uma instância do guardião rode por vez.

### � 3. Relatórios PDF & SLA
- **Relatório de Disponibilidade**: Novo gerador de PDF na aba Relatórios.
- **Métricas Reais**: Uptime precisa baseada em logs e Latência média por equipamento.
- **Design Profissional**: Relatórios formatados prontos para enviar ao cliente ou gerência.

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
