# 📡 ISP Monitor - Sistema de Monitoramento para Provedores de Internet
*Versão 4.6 - Enterprise Ready (Big Data Enabled)*

Sistema completo de monitoramento de torres e equipamentos para provedores de internet, com rastreamento de técnicos em tempo real, notificações multicanal (WhatsApp/Telegram) e banco de dados preparado para escala massiva.

**Desenvolvido com tecnologia de ponta para alta disponibilidade, performance extrema e auto-recuperação.**

---

## ⚡ Instalação Automática (Zero Config)

**Novo usuário? Execute o Launcher Inteligente:**

1. **Duplo clique** em `ABRIR_SISTEMA.bat`
2. O sistema verificará automaticamente:
   - ✅ Python & Dependências
   - ✅ Node.js & Módulos
   - ✅ Banco de Dados (PostgreSQL) com Otimizações Big Data
3. Se algo faltar, o instalador corrigirá automaticamente.

---

## 🚀 Novidades da Versão 4.6 (04/01/2026) - Enterprise Edition

### 💾 1. Banco de Dados Enterprise (Big Data Ready)
O sistema agora está preparado para lidar com **milhões de registros histórica** sem perder performance:
- **Particionamento Automático**: Tabelas de logs (`ping_logs`, `traffic_logs`) são automaticamente divididas em arquivos mensais, permitindo gerenciamento eficiente de espaço e backup.
- **Índices BRIN & Autovacuum**: Otimização profunda para leitura rápida de períodos longos e manutenção automática agressiva para evitar inchaço do banco.

### 📡 2. Monitoramento Wireless Avançado
Visualização detalhada para equipamentos de rádio:
- **Stations (Clientes)**: Exibe Sinal (dBm) e Qualidade (CCQ) com gráficos em tempo real.
- **Transmissores (AP)**: Monitoramento de número de clientes conectados.
- **Interface Intuitiva**: Ícones dedicados na listagem para acesso rápido aos detalhes de RF.

### � 3. Ping Cirúrgico (Precision Mode V3)
Reformulação completa da lógica de monitoramento para precisão absoluta:
- **Latência Zero-Jitter**: Algoritmos de calibração eliminam overhead do SO, garantindo medições de 0-1ms em rede local.
- **Prioridade Real-Time**: O processo de coleta roda com prioridade máxima no Windows.

---

## 🚀 Início Rápido

### **1. Iniciar o Sistema (Tudo em Um)**

```bash
# Modo Interface Gráfica (Recomendado para uso diário)
./ABRIR_SISTEMA.bat

# Modo Servidor / Headless (Para rodar em VPS ou Task Scheduler)
./INICIAR_MODO_SERVIDOR.bat
```

### **2. Acessar o Painel Administrativo**

- **URL Local**: `http://localhost:5173`
- **Login Padrão**:
  - **Email**: `admin@admin.com` (ou configurado na instalação)
  - **Senha**: `admin`

---

## 📁 Estrutura do Projeto (Reorganizada)

```
isp_monitor/
├── 📱 mobile/              # App React Native + Expo (Uso dos Técnicos)
├── 🖥️  backend/             # API FastAPI + PostgreSQL (Core do Sistema)
│   ├── app/               # Lógica de Negócio (Routers, Models, Services)
│   ├── collector.py       # Supervisor de Coleta Independente (V2)
│   └── scripts/           # Scripts de Banco e Migrações
├── 💻 frontend/            # Painel Administrativo (React + Vite + Tailwind)
├── 🛠️  scripts/             # Ferramentas de Manutenção e Diagnóstico
│   ├── maintenance/       # Scripts de reparo e limpeza
│   ├── setup/             # Scripts de instalação inicial
│   └── self_heal.py       # Watchdog (Sistema Doctor)
├── 📊 logs/                # Logs centralizados do sistema
├── � backups/             # Backups automáticos do Banco de Dados
├── �🚀 ABRIR_SISTEMA.bat    # Launcher Principal (GUI)
└── ⚙️ TESTAR_BACKUP.bat    # Validador de Backup Manual
```

---

## ✨ Funcionalidades Principais

### **Monitoramento & Alertas**
- 📡 **Pinger Ultra-Rápido**: Monitoramento ICMP assíncrono capaz de pingar milhares de hosts por segundo.
- 🔔 **Notificações Inteligentes**: Envia alertas apenas quando necessário (evita spam) via WhatsApp e Telegram.
- � **Histórico Completo**: Armazenamento particionado de latência, perda de pacotes e tráfego.

### **Gestão de Rede**
- 🗺️ **Mapa em Tempo Real**: Localização geo-referenciada de torres e clientes.
- 🔗 **Topologia Automática**: Visualização e descoberta de links entre torres via CDP/LLDP/Mac Telnet.
- 🏥 **Health Check**: Monitoramento de voltagem, temperatura, CPU e frequências de rádio.

---

## 🤝 Suporte & Manutenção

**Backup & Recuperação:**
O sistema inclui scripts robustos de backup (`TESTAR_BACKUP.bat`) validados para a nova estrutura particionada. Recomenda-se a execução diária.

**Auto-Reparo:**
O watchdog `self_heal.py` monitora a saúde dos processos Python e Node.js, reiniciando-os automaticamente em caso de falha.

---

**Desenvolvido para provedores que exigem estabilidade e precisão.**
