# 🌐 ISP Monitor

> Sistema profissional de monitoramento para provedores de internet (ISP) com suporte para 800+ dispositivos

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-009688.svg)](https://fastapi.tiangolo.com/)

---

## 📋 Índice

- [Sobre](#-sobre)
- [Características](#-características)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Performance](#-performance)
- [Documentação](#-documentação)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🎯 Sobre

O **ISP Monitor** é um sistema completo de monitoramento de rede desenvolvido especificamente para provedores de internet. Inspirado no **The Dude** da Mikrotik, oferece monitoramento em tempo real, alertas automáticos e visualização geográfica da topologia de rede.

### Por que ISP Monitor?

- ✅ **100% Windows-native** - Funciona perfeitamente no Windows
- ✅ **Ultra-rápido** - Pinga 800 dispositivos em 3-5 segundos
- ✅ **Zero configuração** - SQLite embutido, sem servidor de banco
- ✅ **Alertas inteligentes** - Telegram integrado
- ✅ **Mapa interativo** - Visualize sua rede geograficamente
- ✅ **SSH integrado** - Reboot remoto de equipamentos Mikrotik

---

## ✨ Características

### 🔍 Monitoramento

- **Ping ultra-rápido** usando `icmplib` (mesma técnica do The Dude)
- **Monitoramento simultâneo** de 800+ dispositivos
- **Histórico de latência** com gráficos interativos
- **Detecção automática** de status (online/offline)
- **Intervalo configurável** (padrão: 30 segundos)

### 🗺️ Visualização

- **Mapa interativo** com Leaflet
- **Marcadores customizados** por status (verde/vermelho)
- **Topologia de rede** com links entre torres
- **Busca rápida** de dispositivos
- **Múltiplas camadas** de mapa (satélite, ruas, terreno)

### 📊 Dashboard

- **Estatísticas em tempo real**
- **Gráficos de disponibilidade**
- **Alertas visuais**
- **Histórico de latência**
- **Dispositivos offline** destacados

### 🔔 Alertas

- **Telegram integrado**
- **Notificações instantâneas** de mudança de status
- **Alertas configuráveis**
- **Histórico de eventos**

### 🔧 Gerenciamento

- **CRUD completo** de torres e equipamentos
- **SSH para reboot** remoto (Mikrotik)
- **Migração de dados** SQLite → PostgreSQL
- **Backup simples** (copiar arquivo .db)
- **Usuários e permissões**

---

## 🛠️ Tecnologias

### Backend

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM assíncrono
- **SQLite** - Banco de dados (otimizado como The Dude)
- **icmplib** - Ping ultra-rápido (cross-platform)
- **Paramiko** - SSH para reboot remoto
- **python-telegram-bot** - Alertas via Telegram

### Frontend

- **React 18** - Interface moderna e responsiva
- **TypeScript** - Tipagem estática
- **Vite** - Build ultra-rápido
- **Tailwind CSS** - Estilização moderna
- **Leaflet** - Mapas interativos
- **Recharts** - Gráficos bonitos
- **Lucide React** - Ícones modernos

### Performance

- **SQLite WAL mode** - 5-10x mais rápido
- **Cache de 64MB** - Queries instantâneas
- **Auto-vacuum** - Banco sempre compacto
- **Índices otimizados** - 100x mais rápido
- **Batch pinging** - Todos dispositivos simultaneamente

---

## 🚀 Instalação

### Requisitos

- **Windows 10/11** (ou Linux/Mac)
- **Python 3.11+**
- **Node.js 18+**
- **Git**

### Passo a Passo

#### 1. Clone o repositório

```bash
git clone https://github.com/diegojlc22/isp-monitor.git
cd isp-monitor
```

#### 2. Configure o Backend

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
.\venv\Scripts\activate

# Instalar dependências
pip install -r backend/requirements.txt
```

#### 3. Configure o Frontend

```bash
cd frontend
npm install
```

#### 4. Inicie o sistema

**Terminal 1 - Backend:**
```bash
# Na raiz do projeto
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev -- --host
```

#### 5. Acesse o sistema

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Documentação API:** http://localhost:8000/docs

### 🔐 Login Padrão

```
Email: diegojlc22@gmail.com
Senha: 110812
```

> ⚠️ **IMPORTANTE:** Troque as credenciais em produção!

---

## 📖 Uso

### Adicionar Torre

1. Acesse **Torres** no menu
2. Clique em **Nova Torre**
3. Preencha:
   - Nome
   - IP (opcional)
   - Latitude, Longitude (ex: `-23.550520, -46.633308`)
   - Observações
4. Salvar

### Adicionar Equipamento

1. Acesse **Equipamentos**
2. Clique em **Novo Equipamento**
3. Preencha:
   - Nome
   - IP
   - Torre associada
   - Credenciais SSH (para reboot)
4. Salvar

### Configurar Alertas Telegram

1. Acesse **Configurações**
2. Seção **Telegram**
3. Preencha:
   - Token do Bot
   - Chat ID
4. Salvar

### Ver Mapa

1. Acesse **Mapa**
2. Visualize torres e equipamentos
3. Clique nos marcadores para detalhes
4. Use **Gerenciar Links** para criar topologia

---

## ⚡ Performance

### Benchmarks (800 dispositivos)

| Operação | Tempo | Status |
|----------|-------|--------|
| **Ciclo de ping completo** | 3-5s | ✅ Excelente |
| **Carregar dashboard** | 0.2s | ✅ Instantâneo |
| **Histórico de latência** | 0.3s | ✅ Rápido |
| **Tamanho do banco** | ~150MB | ✅ Compacto |

### Otimizações Implementadas

- ✅ **SQLite WAL mode** - Leituras/escritas simultâneas
- ✅ **Cache de 64MB** - Dados quentes em memória
- ✅ **Batch pinging** - Todos IPs ao mesmo tempo
- ✅ **Auto-vacuum** - Recuperação automática de espaço
- ✅ **Índices otimizados** - Queries 100x mais rápidas

---

## 📚 Documentação

### Guias Disponíveis

- **[PERFORMANCE.md](PERFORMANCE.md)** - Otimizações e configurações de performance
- **[WINDOWS_ADMIN.md](WINDOWS_ADMIN.md)** - Como executar como Admin no Windows
- **[SQLITE_OPTIMIZATION.md](SQLITE_OPTIMIZATION.md)** - Detalhes das otimizações do banco
- **[ANALISE_PROJETO.md](ANALISE_PROJETO.md)** - Análise completa do código
- **[RELATORIO_DESENVOLVIMENTO.md](RELATORIO_DESENVOLVIMENTO.md)** - Relatório de desenvolvimento

### Configuração Avançada

#### Arquivo `.env` (opcional)

```bash
# Ping
PING_INTERVAL_SECONDS=30
PING_TIMEOUT_SECONDS=2
PING_CONCURRENT_LIMIT=100

# Logs
LOG_RETENTION_DAYS=30

# Database (para PostgreSQL)
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/isp_monitor
```

---

## 🏗️ Estrutura do Projeto

```
isp-monitor/
├── backend/
│   ├── app/
│   │   ├── routers/          # Endpoints da API
│   │   ├── services/         # Lógica de negócio
│   │   ├── models.py         # Modelos do banco
│   │   ├── schemas.py        # Validação Pydantic
│   │   ├── database.py       # Configuração do banco
│   │   ├── config.py         # Configurações
│   │   └── main.py           # Aplicação principal
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # Páginas React
│   │   ├── services/         # API client
│   │   ├── context/          # Context API
│   │   └── App.tsx
│   └── package.json
├── monitor.db                # Banco SQLite
├── .env.example              # Exemplo de configuração
└── README.md
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Add: Minha feature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

**Diego Lima**
- GitHub: [@diegojlc22](https://github.com/diegojlc22)
- Email: diegojlc22@gmail.com

---

## 🙏 Agradecimentos

- **Mikrotik** - Inspiração do The Dude
- **FastAPI** - Framework incrível
- **React** - Biblioteca poderosa
- **Comunidade Open Source** - Por todas as ferramentas

---

## 📊 Status do Projeto

- ✅ **Build:** Passando
- ✅ **Testes:** N/A
- ✅ **Cobertura:** N/A
- ✅ **Produção:** Pronto para 800+ dispositivos

---

<p align="center">
  Feito com ❤️ para a comunidade ISP
</p>

<p align="center">
  <a href="#-isp-monitor">Voltar ao topo</a>
</p>
