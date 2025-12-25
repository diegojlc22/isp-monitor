# 🌐 ISP Monitor - Sistema de Monitoramento para Provedores de Internet

**Versão:** 2.0 (PostgreSQL)  
**Status:** Produção  
**Licença:** MIT  
**Plataforma:** Windows Server (Linux compatível)

---

## 📋 VISÃO GERAL

Sistema de monitoramento em tempo real para provedores de internet (ISPs), focado em **estabilidade**, **performance** e **simplicidade operacional**.

### O Que Este Sistema FAZ

✅ Monitora torres e equipamentos via **ICMP (ping)**  
✅ Coleta tráfego e estatísticas wireless via **SNMP**  
✅ Detecta quedas e degradação de rede  
✅ Envia alertas via **Telegram**  
✅ Exibe dashboard web em tempo real  
✅ Suporta hierarquia de dependências (torre → equipamento)  
✅ Modo manutenção (silencia alertas temporariamente)  
✅ Monitoramento sintético (Google DNS, Cloudflare, etc)  
✅ Detecção inteligente de anomalias (Z-Score)

### O Que Este Sistema NÃO FAZ

❌ Não monitora largura de banda de clientes finais  
❌ Não gerencia autenticação PPPoE/Radius  
❌ Não faz billing ou cobrança  
❌ Não substitui sistemas de NOC completos (Zabbix, PRTG)  
❌ Não monitora servidores (apenas equipamentos de rede)

---

## 🏗️ ARQUITETURA TÉCNICA

### Stack Tecnológico

**Backend:**
- Python 3.11+ (asyncio nativo)
- FastAPI (API REST)
- SQLAlchemy 2.0 (ORM async)
- PostgreSQL 15+ (banco de dados)
- icmplib (ping ICMP raw)
- PySNMP (coleta SNMP)
- APScheduler (jobs periódicos)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- Recharts (gráficos)
- Leaflet (mapas)

**Infraestrutura:**
- Uvicorn (ASGI server)
- 1 worker (single process)
- PostgreSQL local (sem replicação)

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  Dashboard │ Mapa │ Equipamentos │ Torres │ Alertas     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/JSON
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 BACKEND (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Routers  │  │ Services │  │  Models  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Pinger     │  │ SNMP Monitor │  │ Synthetic    │
│  (icmplib)   │  │  (PySNMP)    │  │   Agent      │
│   30s loop   │  │   60s loop   │  │  300s loop   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                  ┌──────────────┐
                  │  PostgreSQL  │
                  │   (Local)    │
                  └──────────────┘
```

### Fluxo de Dados

1. **Pinger** pinga todos os devices a cada 30s (batch)
2. **SNMP Monitor** coleta tráfego/wireless a cada 60s (paralelo)
3. **Synthetic Agent** testa conectividade externa a cada 5min
4. Dados são salvos no **PostgreSQL**
5. **Dashboard** consulta via API REST
6. **Alertas** são enviados via Telegram quando detectadas anomalias

---

## 🚀 INSTALAÇÃO E EXECUÇÃO

### Pré-requisitos

- **Windows 10/11** ou **Server 2019+** (ou Linux)
- **Python 3.11+** (instalado ou será baixado automaticamente)
- **Node.js 18+** (apenas para build do frontend)
- **PostgreSQL 15+** (para modo produção)

### Instalação Rápida (SQLite)

```bash
# 1. Clone o repositório
git clone <repo-url>
cd isp_monitor

# 2. Execute o instalador
iniciar_sistema.bat

# 3. Acesse o sistema
http://localhost:8080
Login: admin@admin.com
Senha: admin
```

O script `iniciar_sistema.bat` automaticamente:
- Detecta ou baixa Python 3.11
- Cria ambiente virtual (`.venv`)
- Instala dependências
- Compila o frontend
- Inicia o servidor

### Instalação Produção (PostgreSQL)

```bash
# 1. Instale PostgreSQL
# Download: https://www.postgresql.org/download/windows/

# 2. Crie o banco de dados
psql -U postgres
CREATE DATABASE monitor_prod;
\q

# 3. Execute o script de migração
python scripts/init_postgres.py
python scripts/migrar_sqlite_para_postgres.py

# 4. Inicie com PostgreSQL
iniciar_postgres.bat
```

**Veja:** `docs/GUIA_MIGRACAO_POSTGRES.md` para detalhes.

---

## ⚙️ CONFIGURAÇÃO

### Variáveis de Ambiente

```bash
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/monitor_prod

# Telegram (Alertas)
TELEGRAM_TOKEN=seu_bot_token
TELEGRAM_CHAT_ID=seu_chat_id

# Performance
PING_INTERVAL_SECONDS=30        # Intervalo de ping (padrão: 30s)
PING_CONCURRENT_LIMIT=100       # Pings simultâneos (padrão: 100)
LOG_RETENTION_DAYS=30           # Retenção de logs (padrão: 30 dias)
```

### Ajustes de Performance

**PostgreSQL - Otimização Automática:**

O projeto inclui um arquivo de configuração otimizado para PostgreSQL:

```bash
# 1. Faça backup do arquivo original
copy "C:\Program Files\PostgreSQL\15\data\postgresql.conf" "C:\Program Files\PostgreSQL\15\data\postgresql.conf.backup"

# 2. Copie o arquivo otimizado
copy postgresql.conf.optimized "C:\Program Files\PostgreSQL\15\data\postgresql.conf"

# 3. Reinicie o PostgreSQL
Restart-Service postgresql-x64-15
```

**Ou edite manualmente** (veja `docs/POSTGRESQL_CONFIG_MUDANCAS.md`):

```ini
# MEMÓRIA (para 16GB RAM)
shared_buffers = 2GB              # 25% da RAM
effective_cache_size = 6GB        # 50% da RAM
work_mem = 16MB
maintenance_work_mem = 512MB

# WAL (Write-Ahead Logging)
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
checkpoint_completion_target = 0.9

# SSD Optimization
random_page_cost = 1.1            # SSD
effective_io_concurrency = 200    # SSD

# Query Planner
default_statistics_target = 100
```

**Ganho esperado:** +20-30% performance geral

---

## 📊 DECISÕES TÉCNICAS

### Por Que Python + Asyncio?

✅ **Concorrência nativa** (asyncio) permite pingar 1000 devices simultaneamente  
✅ **Ecossistema rico** (icmplib, PySNMP, FastAPI)  
✅ **Manutenibilidade** (código limpo e legível)  
❌ **GIL limita CPU** (mas I/O-bound, não CPU-bound)

### Por Que PostgreSQL?

✅ **Escala melhor** que SQLite (1000+ devices)  
✅ **Índices avançados** (B-tree, GIN, BRIN)  
✅ **ACID completo** (transações seguras)  
✅ **Replicação nativa** (futuro)  
❌ **Mais complexo** de instalar

### Por Que icmplib?

✅ **Cross-platform** (Windows, Linux, Mac)  
✅ **Async nativo** (integra com asyncio)  
✅ **Multiping** (pinga N IPs simultaneamente)  
✅ **Raw ICMP** (preciso como The Dude)  
❌ **Requer privilégios** (admin/root)

### Por Que 1 Worker Uvicorn?

✅ **Simplicidade** (sem shared state)  
✅ **Suficiente** para 20 usuários simultâneos  
✅ **Menos bugs** (sem race conditions)  
❌ **Não escala horizontalmente** (futuro: workers + Redis)

---

## 📈 ESTRATÉGIAS DE PERFORMANCE

### 1. Batch Pinging (icmplib multiping)

Ao invés de pingar 1 device por vez:
```python
# ❌ Lento (sequencial)
for ip in ips:
    ping(ip)

# ✅ Rápido (paralelo)
results = await async_multiping(ips, concurrent_tasks=100)
```

**Ganho:** 100x mais rápido

### 2. Semaphores para Controle de Concorrência

```python
sem = asyncio.Semaphore(100)

async def fetch_snmp(ip):
    async with sem:  # Limita a 100 simultâneos
        return await get_snmp_data(ip)
```

**Benefício:** Evita sobrecarga de rede

### 3. Smart Logging (Reduz Writes)

Só salva log quando status muda:
```python
if device.is_online != new_status:
    # Mudou de online → offline (ou vice-versa)
    save_log()
```

**Ganho:** 90% menos writes no banco

### 4. Índices Compostos

```sql
CREATE INDEX idx_ping_logs_device_time 
ON ping_logs(device_id, timestamp DESC);
```

**Ganho:** Queries 20x mais rápidas

### 5. Limpeza Automática de Logs

Job diário remove logs > 30 dias:
```python
cutoff = datetime.utcnow() - timedelta(days=30)
delete(PingLog).where(PingLog.timestamp < cutoff)
```

**Benefício:** Banco não cresce infinitamente

---

## ⚠️ LIMITES CONHECIDOS

### Capacidade Atual

| Métrica | Limite Confortável | Limite Máximo |
|---------|-------------------|---------------|
| **Dispositivos** | 500 | 1000 |
| **Usuários Simultâneos** | 10 | 20 |
| **Intervalo Mínimo de Ping** | 30s | 15s |
| **Retenção de Logs** | 30 dias | 90 dias |

### Gargalos Identificados

1. **CPU** - Limita em ~1000 devices (Python GIL)
2. **PostgreSQL Queries** - Lentas sem índices adequados
3. **Serialização JSON** - Lenta com muitos usuários
4. **Ausência de Cache** - Queries repetidas desperdiçam CPU

### O Que Acontece no Limite?

- **1000+ devices:** Pings começam a atrasar (timeouts)
- **20+ usuários:** Dashboard fica lento (2-5s)
- **90+ dias de logs:** Queries demoram (5-10s)

**Solução:** Ver `docs/FASE3_ANALISE_AJUSTES.md`

---

## 🛣️ ROADMAP

### ✅ Implementado (v2.0)

- [x] Migração para PostgreSQL
- [x] Ping ultra-rápido (icmplib)
- [x] SNMP paralelo (Semaphore 100)
- [x] Synthetic Agent (IA leve)
- [x] Detecção de anomalias (Z-Score)
- [x] Alertas Telegram
- [x] Dashboard responsivo
- [x] Modo manutenção

### 🔄 Em Progresso

- [ ] Índices compostos (performance)
- [ ] Cache em memória (reduz queries)
- [ ] Paginação em endpoints
- [ ] Compressão Gzip

### 📅 Futuro (v3.0)

- [ ] Redis (cache distribuído)
- [ ] Workers múltiplos (escala horizontal)
- [ ] Particionamento de tabelas
- [ ] Read Replicas (PostgreSQL)
- [ ] App móvel (APK técnico)
- [ ] Grafana integration
- [ ] Webhooks personalizados

---

## 🔧 MANUTENÇÃO

### Logs do Sistema

```bash
# Ver logs em tempo real
tail -f logs/app.log

# Ou no Windows (PowerShell)
Get-Content logs/app.log -Wait
```

### Backup do Banco

```bash
# PostgreSQL
pg_dump -U postgres monitor_prod > backup.sql

# Restaurar
psql -U postgres monitor_prod < backup.sql
```

### Limpeza Manual de Logs

```sql
-- Deletar logs > 60 dias
DELETE FROM ping_logs WHERE timestamp < NOW() - INTERVAL '60 days';
DELETE FROM traffic_logs WHERE timestamp < NOW() - INTERVAL '60 days';
VACUUM ANALYZE;
```

### Reiniciar Serviços

```bash
# Windows
taskkill /F /IM python.exe
iniciar_postgres.bat

# Linux (systemd)
sudo systemctl restart isp-monitor
```

---

## 🐛 TROUBLESHOOTING

### Problema: Pings não funcionam

**Causa:** icmplib precisa de privilégios de administrador

**Solução:**
```bash
# Windows: Execute como Administrador
# Linux: Use sudo ou configure capabilities
sudo setcap cap_net_raw+ep /path/to/python
```

### Problema: SNMP não retorna dados

**Causa:** Community string incorreta ou firewall

**Solução:**
1. Teste com `snmpwalk`:
```bash
snmpwalk -v2c -c public <IP> 1.3.6.1.2.1.2.2.1.10
```
2. Verifique firewall (porta 161 UDP)
3. Confirme community string no equipamento

### Problema: Dashboard lento

**Causa:** Muitos logs acumulados sem índices

**Solução:**
```sql
-- Criar índices (se não existirem)
CREATE INDEX idx_ping_logs_device_time ON ping_logs(device_id, timestamp DESC);

-- Limpar logs antigos
DELETE FROM ping_logs WHERE timestamp < NOW() - INTERVAL '30 days';
VACUUM ANALYZE;
```

### Problema: PostgreSQL connection refused

**Causa:** Serviço não está rodando

**Solução:**
```bash
# Windows
services.msc → PostgreSQL → Iniciar

# Linux
sudo systemctl start postgresql
```

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- **Migração PostgreSQL:** `docs/GUIA_MIGRACAO_POSTGRES.md`
- **Performance:** `docs/FASE2_SIMULACAO_CARGA.md`
- **Otimizações:** `docs/FASE3_ANALISE_AJUSTES.md`
- **Limpeza de Código:** `docs/FASE1_LIMPEZA.md`
- **Como Reiniciar:** `docs/COMO_REINICIAR.md`

---

## 🤝 CONTRIBUINDO

### Estrutura do Projeto

```
isp_monitor/
├── backend/
│   ├── app/
│   │   ├── routers/      # Endpoints da API
│   │   ├── services/     # Lógica de negócio
│   │   ├── models.py     # Schema do banco
│   │   └── main.py       # Entry point
│   └── tools/            # Scripts de debug
├── frontend/
│   └── src/
│       ├── pages/        # Telas React
│       ├── components/   # Componentes reutilizáveis
│       └── services/     # API client
├── docs/                 # Documentação técnica
├── scripts/              # Scripts de produção
└── README.md
```

### Padrões de Código

- **Python:** PEP 8, type hints, async/await
- **TypeScript:** ESLint, functional components
- **SQL:** Lowercase, snake_case
- **Commits:** Conventional Commits

### Testes

```bash
# Backend (futuro)
pytest backend/tests/

# Frontend
cd frontend
npm test
```

---

## 📄 LICENÇA

MIT License - Veja `LICENSE` para detalhes.

---

## 🙏 AGRADECIMENTOS

- **icmplib** - Ping cross-platform incrível
- **FastAPI** - Framework web moderno
- **PostgreSQL** - Banco de dados robusto
- **The Dude (MikroTik)** - Inspiração para arquitetura de ping

---

## 📞 SUPORTE

**Issues:** GitHub Issues  
**Docs:** `docs/` folder  
**Email:** [seu-email]

---

**Desenvolvido com ❤️ para ISPs que valorizam estabilidade e performance.**
