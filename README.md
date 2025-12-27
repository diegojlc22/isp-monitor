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

## 🚀 Novidades da Versão 3.3 (27/12/2025)

### 📱 1. Mobile & Expo Offline Mode
- **Auto-Discovery**: O App Mobile detecta automaticamente o IP do servidor (`hostUri`). Chega de configurar IPs fixos!
- **Modo Offline**: Inicialização do Expo otimizada com `--offline` para evitar falhas de login.
- **Auto-Install Healer**: O Launcher detecta dependências ausentes e instala automaticamente na primeira execução.

### 🗺️ 2. Frontend GPS Fix
- **Parser Inteligente**: Agora aceita coordenadas em qualquer formato (ex: `-19,55` ou `-19.55`), corrigindo erro de cálculo de distância.

### 🛠️ 3. Launcher 3.0 (Stability)
- **Logs em Tempo Real**: Novo sistema "Memory Mirror" evita bloqueio de arquivos de log.
- **Crash Shield**: Correção de bugs críticos de terminação de processos.
- **Startup Otimizado**: Inicialização silenciosa e invisível para serviços de background.

### 🏥 4. Auto-Reparo (Doctor AI + Healer)
Reduzimos a necessidade de suporte técnico manual com um sistema de auto-cura:
- **Diagnóstico Ativo**: O script `diagnostico.py` lê logs em busca de erros conhecidos (porta presa, queda de API).
- **Cura Automática**: Scripts de correção (`tools/reparo/`) são acionados automaticamente para:
  - Destravar processos zumbis.
  - Reinstalar dependências corrompidas.
  - Reconectar o Gateway WhatsApp.
  - Otimizar o banco PostgreSQL (`turbo_db.py`).

### 📱 2. Gateway WhatsApp 2.0 (Dual Channel)
Notificações robustas e flexíveis:
- **Envio Duplo**: Suporte simultâneo a envio para **Número Individual** (Admin) e **Grupo de Técnicos** (`@g.us`).
- **Antitrava**: Versão do WhatsApp Web fixada (`2.2407.3`) para evitar falhas de envio "No LID".
- **Visualizador de Grupos**: Nova ferramenta no Launcher para listar seus grupos e copiar o ID facilmente.

### 🔔 3. Painel de Alertas Multicanal
Agora você tem controle total sobre onde receber os avisos:
- **Telegram**: Configuração de Bot Token e Chat ID.
- **WhatsApp**: Campos separados para **Número Individual** e **ID de Grupo**.
- **Templates**: Personalize as mensagens de "Queda" e "Retorno" com variáveis dinâmicas (`[Device.Name]`, `[Device.IP]`).

### 🛠️ 4. Launcher Profissional (GUI)
Interface gráfica moderna (`launcher.pyw`) para controle total:
- **Abas de Controle**: Principal, WhatsApp, Mobile e Logs.
- **Monitoramento em Tempo Real**: Status da API, Ngrok e Expo.
- **Botões de Ação**: Reiniciar tudo, Testar ZAP, Abrir Dashboard.

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

**Última atualização:** 27/12/2025
**Build:** v3.3.0 (Stability Edition)

---

**Desenvolvido com ❤️ para otimizar o trabalho dos provedores ISP.**
