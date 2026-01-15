# 📡 ISP Monitor - Sistema de Monitoramento para Provedores de Internet
*Versão 5.0 - AI-Powered Network Intelligence*

Sistema completo de monitoramento de torres e equipamentos para provedores de internet, com **Inteligência Artificial integrada**, rastreamento de técnicos em tempo real, notificações multicanal (WhatsApp/Telegram) e banco de dados preparado para escala massiva.

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

## 🚀 Novidades da Versão 6.0 (15/01/2026) - AIOps & Big Data

### � 1. Cortex AI v2.0 (AIOps Engine)
O cérebro do sistema foi totalmente redesenhado para análise preditiva avançada:
- **� Detecção de Flapping**: Identifica equipamentos com instabilidade intermitente ("pisca-pisca") e gera alertas preventivos.
- **� Inteligência de Energia**: Monitoramento inteligente de voltagem e baterias com previsão de autonomia.
- **�️ Anomalias de Segurança**: Detecção proativa de ataques de força bruta e mudanças suspeitas de tráfego.
- **🕒 Análise de Ciclo**: Identifica padrões de falha baseados em horário (ex: equipamentos que falham apenas à noite).

### � 2. Notificações Multicanal Inteligentes
Novo sistema de roteamento de alertas para WhatsApp e Telegram:
- **� Roteamento Dinâmico**: Encaminha alertas técnicos (Energia/Bateria/IA) para grupos específicos e alertas de queda para grupos operacionais.
- **� Atendimento Automático**: O Bot de WhatsApp agora suporta comandos básicos e listagem de grupos diretamente pelo sistema.
- **🛠️ Self-Healing Feedback**: O sistema notifica quando o "Doctor" realiza um auto-reparo bem-sucedido.

### � 3. Big Data Engine (PostgreSQL Partitioning)
Otimização para ISPs com milhares de equipamentos e milhões de logs:
- **� Particionamento Nativo**: Tabelas de `ping_logs` e `traffic_logs` agora são particionadas mensalmente de forma automática.
- **⚡ Performance Flash**: Consultas em históricos de anos agora levam milissegundos devido à técnica de *Constraint Exclusion*.
- **🧹 Manutenção Zero**: O sistema gerencia a criação de partições futuras e a limpeza de logs antigos sem intervenção humana.

### � 4. Doctor V4.0 - Guardião Supremo
Novo watchdog residente no Launcher:
- **👁️ Monitoramento 360°**: Monitora simultaneamente API, Collector, Frontend, WhatsApp Gateway e PostgreSQL.
- **� Força Bruta**: Capaz de encerrar processos zumbis e limpar travas de socket (Porta 8080/3001) para garantir reinícios perfeitos.
- **📝 Logs Espelhados**: Logs de startup e erro condensados em uma visão única para facilitaro diagnóstico.

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
  - **Email**: `admin@admin.com`
  - **Senha**: `admin`

---

## 📁 Estrutura do Projeto

```
isp_monitor/
├── 📱 mobile/              # App React Native + Expo (Uso dos Técnicos)
├── 🖥️  backend/             # API FastAPI + PostgreSQL (Core do Sistema)
│   ├── app/
│   │   ├── routers/       # Endpoints da API
│   │   ├── models.py      # Modelos do Banco de Dados
│   │   ├── schemas.py     # Validação Pydantic
│   │   └── services/      # Lógica de Negócio
│   │       ├── snmp_monitor.py      # Coleta SNMP
│   │       ├── topology.py          # Descoberta de Topologia
│   │       ├── security_audit.py    # Auditoria de Segurança (AI)
│   │       └── capacity_planning.py # Planejamento de Capacidade (AI)
│   ├── collector.py       # Supervisor de Coleta Independente
│   └── database.py        # Configuração PostgreSQL
├── 💻 frontend/            # Painel Administrativo (React + Vite + Tailwind)
│   └── src/
│       └── pages/
│           ├── Dashboard.tsx     # Visão Geral
│           ├── Equipments.tsx    # Gestão de Equipamentos
│           ├── Priority.tsx      # Equipamentos Prioritários
│           ├── Intelligence.tsx  # Central de IA
│           ├── NetMap.tsx        # Mapa de Topologia
│           └── Reports.tsx       # Relatórios Gerenciais
├── 🛠️  scripts/             # Ferramentas de Manutenção
│   ├── maintenance/       # Scripts de reparo e limpeza
│   ├── setup/             # Scripts de instalação inicial
│   └── self_heal.py       # Watchdog (Sistema Doctor)
├── 📊 logs/                # Logs centralizados do sistema
├── 💾 backups/             # Backups automáticos do Banco de Dados
├── 🚀 ABRIR_SISTEMA.bat    # Launcher Principal (GUI)
└── ⚙️ TESTAR_BACKUP.bat    # Validador de Backup Manual
```

---

## ✨ Funcionalidades Principais

### **🤖 Inteligência Artificial**
- 🔍 **Análise Automática**: Varredura periódica de equipamentos prioritários
- 🛡️ **Auditoria de Segurança**: Detecta vulnerabilidades e configurações inseguras
- 📈 **Previsão de Capacidade**: Identifica links próximos da saturação
- 💡 **Recomendações Práticas**: Sugestões acionáveis para melhorias

### **Monitoramento & Alertas**
- 📡 **Pinger Ultra-Rápido**: Monitoramento ICMP assíncrono de milhares de hosts
- 🔔 **Notificações Inteligentes**: Alertas via WhatsApp e Telegram com cooldown configurável
- 📊 **Histórico Completo**: Armazenamento particionado de latência, perda e tráfego
- 🚨 **Alertas de Tráfego**: Notificações quando limites são ultrapassados

### **Gestão de Rede**
- 🗺️ **Mapa em Tempo Real**: Localização geo-referenciada de torres e clientes
- 🔗 **Topologia Automática**: Descoberta e visualização de links via LLDP/MNDP
- 🏥 **Health Check**: Monitoramento de voltagem, temperatura, CPU e RF
- ⚙️ **Configuração Rápida**: Edição de limites de tráfego sem formulários complexos

### **Relatórios & Analytics**
- 📄 **Relatórios PDF**: SLA e Incidentes com design profissional
- 📊 **Dashboards Interativos**: Visualização de métricas em tempo real
- 📋 **Logs Detalhados**: Histórico completo de eventos e alterações
- 🎯 **Filtros Avançados**: Busca e filtragem por múltiplos critérios

---

## 🔧 Configuração Avançada

### **Equipamentos Prioritários**
1. Marque equipamentos como "Prioritário" na página de Equipamentos
2. Acesse a aba "Prioritários" para configurar limites de tráfego
3. Clique no ícone ⚙️ para editar Download/Upload máximos
4. Configure o intervalo de alertas (padrão: 360 minutos)

### **Inteligência Artificial**
- As análises rodam automaticamente em equipamentos prioritários
- Acesse "Inteligência" no menu para ver recomendações
- Filtre por categoria: Segurança ou Capacidade
- Arquive insights resolvidos para manter a lista organizada

### **Notificações**
- Configure WhatsApp e Telegram em "Configurações > Alertas"
- Personalize templates de mensagens com variáveis dinâmicas
- Ajuste cooldowns para evitar spam de notificações

---

## 🤝 Suporte & Manutenção

### **Backup & Recuperação**
O sistema inclui scripts robustos de backup (`TESTAR_BACKUP.bat`) validados para a estrutura particionada. Recomenda-se execução diária.

### **Auto-Reparo**
O watchdog `self_heal.py` monitora a saúde dos processos Python e Node.js, reiniciando-os automaticamente em caso de falha.

### **Banco de Dados**
- **PostgreSQL 14+** com particionamento automático
- **Índices otimizados** para consultas rápidas em grandes volumes
- **Autovacuum agressivo** para manutenção preventiva

---

## 📈 Roadmap Futuro

- [ ] Machine Learning para previsão de falhas
- [ ] Integração com sistemas de ticketing
- [ ] API pública para integrações externas
- [ ] App mobile nativo (iOS/Android)
- [ ] Suporte multi-tenant para MSPs

---

**Desenvolvido para provedores que exigem estabilidade, precisão e inteligência.**

*Powered by AI | Built with ❤️ for ISPs*
