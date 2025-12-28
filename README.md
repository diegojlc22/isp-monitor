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


## 🚀 Novidades da Versão 3.7 (28/12/2025)

### 👻 1. Invisible Startup & Silent Mode
A inicialização do sistema foi completamente reescrita para ser **100% invisível**:
- **Zero Janelas Pretas**: Removemos completamente a dependência de arquivos `.bat` no boot.
- **Boot Direto via Python**: O Launcher inicia o Banco de Dados e a API diretamente, sem invocar o Shell do Windows.
- **Silent Firewall Check**: A verificação de firewall (`network_diagnostics.py`) agora roda silenciosamente em background.
- **Resultado**: Uma experiência de usuário "fantasba", profissional e sem interrupções visuais.

### 🧟 2. Doctor V3.7 "Zombie Hunter"
O sistema de auto-cura agora possui um protocolo de **Extermínio de Zumbis**:
- **Monitoramento de Árvore**: O Doctor memoriza cada processo filho criado (Node, Python, Postgres).
- **Shutdown Hook**: Se o Launcher fechar (crash ou stop manual), o Doctor intercepta o evento.
- **Kill Recursivo**: Mata não apenas o processo pai, mas toda a árvore de dependentes (ex: `npm` -> `vite` -> `esbuild`).
- **Garantia de Limpeza**: Impede erros de "Porta em Uso" ao reiniciar o sistema.

## 🚀 Novidades da Versão 3.4 (28/12/2025)

### 📡 1. Monitoramento Wireless Multi-Fabricante
Sistema completo de monitoramento SNMP para equipamentos wireless:
- **Ubiquiti**: Suporte total (M5, AC, AirFiber) com detecção automática de tabelas dinâmicas.
- **Mikrotik**: Station e AP mode com CCQ e contagem de clientes.
- **Mimosa**: C5c e similares com SNR como métrica de qualidade.
- **Intelbras**: WOM series (compatível com OIDs Ubiquiti).
- **Métricas**: Signal Strength (dBm), CCQ/SNR, Clientes Conectados.

### 🔍 2. Auto-Detecção Inteligente
Cadastro de equipamentos agora é automático:
- **Botão "Auto-Detectar"**: Identifica marca e tipo via SNMP.
- **Detecção de Marca**: Analisa sysDescr, sysObjectID e testa OIDs específicos.
- **Detecção de Tipo**: Diferencia automaticamente Station (Cliente) vs Transmitter (AP).
- **Priorização Intelbras**: Identifica corretamente Intelbras WOM (não confunde com Ubiquiti).
- **Endpoint API**: `POST /api/equipments/detect-brand`

### 🎨 3. Interface Aprimorada
- **Modal Wireless**: Gráficos em tempo real de Sinal e Clientes Conectados.
- **Formulário Inteligente**: Campos de marca e tipo preenchidos automaticamente.
- **Opções Expandidas**: Suporte a 5 fabricantes (Generic, Ubiquiti, Mikrotik, Mimosa, Intelbras).
- **Loading States**: Feedback visual durante detecção SNMP.

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


**Última atualização:** 28/12/2025
**Build:** v3.4.0 (Wireless Multi-Vendor Edition)


---

**Desenvolvido com ❤️ para otimizar o trabalho dos provedores ISP.**
