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


## 🚀 Novidades da Versão 4.0 (28/12/2025) - Centralized Alerts & WhatsApp 2.0

### 🔔 1. Central de Alertas Unificada
Toda a configuração de notificações foi centralizada em uma única aba **"Alertas"**:
- **Consolidação Total**: Telegram, WhatsApp, Backups e Agente IA agora são configurados em um só lugar.
- **Toggle Control**: Ative ou desative canais de comunicação globalmente com um clique.
- **Granularidade**: Escolha exatamente o que receber em cada canal (Queda de Equipamentos, Sucesso de Backups, Alertas de Latência do Agente IA).

### 📱 2. WhatsApp Gateway 2.0
Integração profunda e simplificada:
- **Busca de Grupos**: Novo sistema de busca que lista todos os seus grupos do WhatsApp com nome e ID.
- **Autenticação Segura**: Suporte nativo a API Keys via `.env` (MSG_SECRET).
- **QR Code Integrado**: Conexão simplificada diretamente pelo Launcher.
- **Multi-Target**: Suporte simultâneo a números individuais e IDs de grupos.

### 💾 3. Backups Multi-Canal
O sistema de backup de banco de dados agora é proativo:
- **Notificações em Tempo Real**: Receba o status do backup no Telegram E no WhatsApp.
- **Auto-Fix pg_dump**: O script agora localiza automaticamente o executável do PostgreSQL no Windows, eliminando erros de "pg_dump not found".
- **Relatórios Formatados**: Mensagens ricas com tamanho do arquivo, data e status do processo.

### 🚀 4. Automated Boot & Admin Elevation
O `ABRIR_SISTEMA.bat` foi transformado em um assistente inteligente:
- **Auto-Start PostgreSQL**: O sistema detecta se o banco está parado e o inicia automaticamente.
- **Elevation Request**: Solicita privilégios de Administrador apenas quando necessário para criar regras de firewall ou iniciar serviços.
- **Depedency Check**: Verifica e instala bibliotecas Python faltando no ambiente de Administrador.

### 👻 5. Invisible Startup & Silent Mode
A inicialização do sistema foi completamente reescrita para ser **100% invisível**:
- **Zero Janelas Pretas**: Removemos completamente a dependência de arquivos `.bat` no boot.
- **Boot Direto via Python**: O Launcher inicia o Banco de Dados e a API diretamente, sem invocar o Shell do Windows.
- **Silent Firewall Check**: A verificação de firewall agora roda silenciosamente em background.

### 🧹 6. Project Cleanup & Final Polish
O projeto foi limpo de arquivos legados e temporários:
- **Remoção de Testes**: Todos os scripts de teste (`test_*.py`) e históricos de debug foram removidos.
- **Limpeza de Logs**: Logs antigos e arquivos `dummy` foram excluídos para garantir uma instalação limpa.
- **Estrutura Enxuta**: Diretórios de backup de scripts (`archive`, `deprecated`) foram consolidados.


---

## 🚀 Início Rápido

### **1. Iniciar o Sistema (Tudo em Um)**

```bash
# Basta rodar o Launcher (Ele instala tudo sozinho)
./ABRIR_SISTEMA.bat
```

### **2. Acessar o Admin Panel**

```
http://localhost:8080
Email: diegojlc22@gmail.com
Senha: 110812
```

### **3. Mobile & Acesso Técnico**

- No Launcher, vá na aba **Mobile**.
- Clique em **Iniciar Expo** e escaneie o QR Code com o app **Expo Go** (Android/iOS).

---

## 📁 Estrutura do Projeto

```
isp_monitor/
├── 📱 mobile/              # App React Native + Expo (Técnicos)
├── 🖥️  backend/             # API FastAPI + PostgreSQL (Core)
├── 💻 frontend/            # Admin Panel React + Vite (Gestão)
├── �️  tools/
│   ├── whatsapp/          # Gateway WhatsApp (Node.js)
│   ├── reparo/            # Doctor AI & Scripts de Correção
│   └── ngrok/             # Acesso Externo
├── 📊 logs/                # Logs centralizados (startup, api, collector)
├── 🚀 ABRIR_SISTEMA.bat    # Ponto de Entrada Único (Auto-Healing)
└── 📖 README.md            # Documentação Oficial
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
- 🔗 **Topologia**: Visualização de links entre torres.
- 💾 **PostgreSQL Otimizado**: Configurado para alta performance.

### **App do Técnico**
- � **Rastreamento GPS Otimizado**: Economia de bateria (só envia ao mover).
- � **Interface Clean**: Focado na produtividade em campo.

---

## 🔧 Tecnologias (Stack Moderna)

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (Async), Uvicorn.
- **Frontend**: React 18, Vite, TailwindCSS, Lucide Icons.
- **Mobile**: React Native, Expo SDK 50+.
- **Database**: PostgreSQL 16/17 (com Tuning Automático).
- **Automação**: Batch/PowerShell Scripts + Python Watchdogs.

---

## 🌐 Acesso Externo (Ngrok)

O sistema integra o **Ngrok** nativamente para permitir acesso fora da rede local (ex: 4G).
A URL pública é gerada automaticamente e exibida no Launcher.

---

## � Suporte & Manutenção

**Auto-Reparo:**
O sistema tenta se corrigir sozinho. Se falhar 3x, verifique a aba **LOGS** no Launcher.

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


**Última atualização:** 28/12/2025
**Build:** v4.0.0 (Centralized Alerts & WhatsApp 2.0 Edition)


---

**Desenvolvido com ❤️ para otimizar o trabalho dos provedores ISP.**
