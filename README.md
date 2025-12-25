# 🌐 ISP Monitor - Sistema de Monitoramento para Provedores

**Versão:** 2.1 (PostgreSQL Otimizado)  
**Status:** Produção  
**Performance:** 3x mais rápido que v1.0  
**Capacidade:** 1000+ dispositivos

---

## 🎯 VISÃO GERAL

Sistema profissional de monitoramento em tempo real para provedores de internet (ISPs), focado em **alta performance**, **estabilidade** e **escalabilidade**.

### ✨ Destaques da v2.1

🚀 **Performance 3x superior** - Cache inteligente + PostgreSQL otimizado  
⚡ **1000+ dispositivos** - Suporta grandes redes com facilidade  
📊 **Dashboard 10x mais rápido** - Respostas em <50ms  
🧠 **IA integrada** - Detecção automática de anomalias  
📱 **Pronto para mobile** - Arquitetura preparada para app técnico

---

## 📋 O QUE O SISTEMA FAZ

✅ Monitora torres e equipamentos via **ICMP (ping)** ultra-rápido  
✅ Coleta tráfego e estatísticas wireless via **SNMP**  
✅ Detecta quedas e degradação de rede automaticamente  
✅ Envia alertas inteligentes via **Telegram**  
✅ Dashboard web responsivo em tempo real  
✅ Hierarquia de dependências (torre → equipamento)  
✅ Modo manutenção programável  
✅ Monitoramento sintético (Google DNS, Cloudflare)  
✅ Análise de padrões com Z-Score  
✅ Cache inteligente (5-10x menos queries)

### ❌ O QUE NÃO FAZ

- Não monitora largura de banda de clientes finais
- Não gerencia autenticação PPPoE/Radius
- Não faz billing ou cobrança
- Não substitui NOC completos (Zabbix, PRTG)
- Não monitora servidores (apenas rede)

---

## 🏗️ ARQUITETURA

### Stack Tecnológico

**Backend:**
- Python 3.11+ (asyncio nativo)
- FastAPI (API REST)
- SQLAlchemy 2.0 (ORM async)
- PostgreSQL 15+ (otimizado)
- icmplib (ping ICMP raw)
- PySNMP (coleta SNMP)
- APScheduler (jobs periódicos)
- Cache em memória (TTL 30-60s)

**Frontend:**
- React 18 + TypeScript
- Vite (build ultra-rápido)
- TailwindCSS
- Recharts (gráficos)
- Leaflet (mapas)

**Otimizações:**
- Índices compostos PostgreSQL
- Pool de conexões (20+10)
- Compressão Gzip (70-80% redução)
- Batch processing (multiping)

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND (React + Cache)                 │
│  Dashboard │ Mapa │ Equipamentos │ Torres │ Alertas     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/JSON (Gzip)
                         ↓
┌─────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI + Cache 30s)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Routers  │  │ Services │  │  Cache   │              │
│  │  +Gzip   │  │ +Indexes │  │  Memory  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Pinger     │  │ SNMP Monitor │  │ Synthetic    │
│  (icmplib)   │  │  (PySNMP)    │  │   Agent      │
│ 30s/100 conc │  │ 60s/100 conc │  │  300s loop   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                  ┌──────────────┐
                  │  PostgreSQL  │
                  │  (Otimizado) │
                  │  - Índices   │
                  │  - Pool 20   │
                  │  - 2GB RAM   │
                  └──────────────┘
```

### Fluxo de Dados Otimizado

1. **Pinger** → Batch ping (100 simultâneos) a cada 30s
2. **SNMP Monitor** → Coleta paralela (100 concurrent) a cada 60s
3. **Synthetic Agent** → Testa conectividade externa a cada 5min
4. **Cache** → Armazena resultados por 30-60s
5. **PostgreSQL** → Salva com índices compostos
6. **Dashboard** → Busca do cache (50ms) ou DB (200ms)
7. **Alertas** → Telegram quando detecta anomalias

---

## 🚀 INSTALAÇÃO

### Pré-requisitos

- **Windows 10/11** ou **Server 2019+**
- **Python 3.11+**
- **Node.js 18+** (apenas para build)
- **PostgreSQL 15+**

### Instalação Rápida (5 minutos)

```bash
# 1. Clone o repositório
git clone <repo-url>
cd isp_monitor

# 2. Instale PostgreSQL
# Download: https://www.postgresql.org/download/windows/

# 3. Crie o banco de dados
psql -U postgres
CREATE DATABASE monitor_prod;
\q

# 4. Execute o script de inicialização
python scripts/init_postgres.py

# 5. Aplique otimizações PostgreSQL (IMPORTANTE!)
copy postgresql.conf.optimized "C:\Program Files\PostgreSQL\15\data\postgresql.conf"
Restart-Service postgresql-x64-15

# 6. Inicie o sistema
iniciar_postgres.bat
```

**Acesse:** http://localhost:8080  
**Login:** admin@admin.com  
**Senha:** admin

---

## ⚙️ CONFIGURAÇÃO

### Variáveis de Ambiente

```bash
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://postgres:senha@localhost:5432/monitor_prod

# Telegram (Alertas)
TELEGRAM_TOKEN=seu_bot_token
TELEGRAM_CHAT_ID=seu_chat_id

# Performance
PING_INTERVAL_SECONDS=30        # Intervalo de ping
PING_CONCURRENT_LIMIT=100       # Pings simultâneos
LOG_RETENTION_DAYS=30           # Retenção de logs
```

### PostgreSQL - Configuração Otimizada

**Arquivo incluído:** `postgresql.conf.optimized`

**Aplicação rápida:**
```bash
# 1. Backup
copy "C:\Program Files\PostgreSQL\15\data\postgresql.conf" postgresql.conf.backup

# 2. Aplicar
copy postgresql.conf.optimized "C:\Program Files\PostgreSQL\15\data\postgresql.conf"

# 3. Reiniciar
Restart-Service postgresql-x64-15
```

**Principais otimizações:**
```ini
# MEMÓRIA (16GB RAM)
shared_buffers = 2GB              # 25% da RAM
effective_cache_size = 6GB        # 50% da RAM
work_mem = 16MB
maintenance_work_mem = 512MB

# WAL
wal_buffers = 16MB
max_wal_size = 4GB
min_wal_size = 1GB
checkpoint_completion_target = 0.9

# SSD
random_page_cost = 1.1
effective_io_concurrency = 200

# QUERY PLANNER
default_statistics_target = 100
```

**Ganho:** +20-30% performance geral

**Documentação:** `docs/APLICAR_POSTGRESQL_OTIMIZADO.md`

---

## 📊 PERFORMANCE

### Benchmarks (v2.1 vs v1.0)

| Métrica | v1.0 (SQLite) | v2.1 (PostgreSQL) | Ganho |
|---------|---------------|-------------------|-------|
| **Dashboard** | ~500ms | ~50ms | **10x** ⚡ |
| **Queries/min** | ~100 | ~10 | **90% menos** |
| **Dispositivos** | 500 max | 1000+ | **2x** |
| **Usuários simultâneos** | 5 | 20+ | **4x** |
| **Tráfego HTTP** | 500KB | 100KB | **80% menor** |

### Otimizações Aplicadas

✅ **Índices compostos** - Queries 10-20x mais rápidas  
✅ **Cache em memória** - 90% redução de queries  
✅ **Pool de conexões** - 30 conexões simultâneas  
✅ **Compressão Gzip** - 70-80% menos tráfego  
✅ **Batch processing** - 100 pings simultâneos  
✅ **PostgreSQL tuning** - 30% ganho geral

---

## 📈 CAPACIDADE

### Limites Atuais (v2.1)

| Métrica | Confortável | Máximo | Observação |
|---------|-------------|--------|------------|
| **Dispositivos** | 800 | 1500 | CPU bound |
| **Usuários simultâneos** | 15 | 30 | Cache ajuda |
| **Intervalo mínimo ping** | 30s | 15s | Recomendado 30s |
| **Retenção de logs** | 30 dias | 90 dias | Com particionamento |
| **Targets synthetic** | 10 | 50 | Baseline training |

### O Que Acontece no Limite?

**1000+ dispositivos:**
- Pings começam a atrasar (30-60s)
- CPU ~80-90%
- Timeouts ocasionais

**30+ usuários:**
- Dashboard fica lento (2-5s)
- Cache ajuda muito
- Considerar workers múltiplos

**Solução:** Ver `docs/FASE3_ANALISE_AJUSTES.md`

---

## 🛠️ MANUTENÇÃO

### Logs do Sistema

```bash
# Ver logs em tempo real
tail -f logs/app.log

# Windows (PowerShell)
Get-Content logs/app.log -Wait
```

### Backup do Banco

```bash
# PostgreSQL
pg_dump -U postgres monitor_prod > backup_$(date +%Y%m%d).sql

# Restaurar
psql -U postgres monitor_prod < backup_20241225.sql
```

### Limpeza Manual de Logs

```sql
-- Deletar logs > 60 dias
DELETE FROM ping_logs WHERE timestamp < NOW() - INTERVAL '60 days';
DELETE FROM traffic_logs WHERE timestamp < NOW() - INTERVAL '60 days';
VACUUM ANALYZE;
```

### Verificar Performance

```sql
-- Tamanho do banco
SELECT pg_size_pretty(pg_database_size('monitor_prod'));

-- Queries lentas
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;

-- Índices não utilizados
SELECT * FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
```

### Limpar Cache

```python
# Adicione um endpoint admin
# backend/app/routers/settings.py
from backend.app.services.cache import cache

@router.post("/cache/clear")
async def clear_cache():
    await cache.clear()
    return {"message": "Cache limpo"}
```

---

## 🐛 TROUBLESHOOTING

### Problema: Dashboard lento

**Causa:** Cache não está funcionando ou índices faltando

**Solução:**
```sql
-- Verificar índices
SELECT indexname FROM pg_indexes WHERE tablename = 'ping_logs';

-- Criar se não existir
python scripts/criar_indices.py

-- Limpar cache
curl -X POST http://localhost:8080/api/cache/clear
```

### Problema: Pings não funcionam

**Causa:** icmplib precisa de privilégios admin

**Solução:**
```bash
# Windows: Execute como Administrador
# Linux: Configure capabilities
sudo setcap cap_net_raw+ep /path/to/python
```

### Problema: PostgreSQL lento

**Causa:** Configurações não aplicadas

**Solução:**
```sql
-- Verificar configurações
SHOW shared_buffers;  -- Deve ser 2GB
SHOW work_mem;        -- Deve ser 16MB

-- Se não estiver, aplicar postgresql.conf.optimized
```

### Problema: Muitas queries no banco

**Causa:** Cache desabilitado ou TTL muito baixo

**Solução:**
```python
# Aumentar TTL do cache
# backend/app/routers/equipments.py
await cache.set(cache_key, data, ttl_seconds=60)  # Era 30s
```

---

## 📚 DOCUMENTAÇÃO

### Guias Técnicos

- **Instalação:** Este README
- **Migração PostgreSQL:** `docs/GUIA_MIGRACAO_POSTGRES.md`
- **Otimizações:** `docs/APLICAR_POSTGRESQL_OTIMIZADO.md`
- **Cache:** `docs/CACHE_IMPLEMENTADO.md`
- **Performance:** `docs/FASE2_SIMULACAO_CARGA.md`
- **Ajustes:** `docs/FASE3_ANALISE_AJUSTES.md`

### Relatórios

- **Limpeza de código:** `docs/FASE1_LIMPEZA.md`
- **Simulação de carga:** `docs/FASE2_SIMULACAO_CARGA.md`
- **Análise completa:** `docs/RELATORIO_COMPLETO.md`

### Operacional

- **Como reiniciar:** `docs/COMO_REINICIAR.md`
- **Configuração PostgreSQL:** `docs/POSTGRESQL_CONFIG_MUDANCAS.md`

---

## 🗂️ ESTRUTURA DO PROJETO

```
isp_monitor/
├── backend/
│   ├── app/
│   │   ├── routers/          # Endpoints da API
│   │   ├── services/         # Lógica de negócio
│   │   │   ├── cache.py      # Cache em memória (NOVO)
│   │   │   ├── pinger_fast.py
│   │   │   ├── snmp_monitor.py
│   │   │   └── synthetic_agent.py
│   │   ├── models.py         # Schema do banco
│   │   ├── database.py       # Pool otimizado (MODIFICADO)
│   │   └── main.py           # Entry point + Gzip (MODIFICADO)
│   └── tools/                # Scripts de debug (NOVO)
├── frontend/
│   └── src/
│       ├── pages/            # Telas React
│       └── components/       # Componentes
├── docs/
│   ├── archive/              # Docs obsoletos (NOVO)
│   ├── FASE1_LIMPEZA.md      # Análise de código (NOVO)
│   ├── FASE2_SIMULACAO_CARGA.md  # Testes (NOVO)
│   ├── FASE3_ANALISE_AJUSTES.md  # Otimizações (NOVO)
│   ├── CACHE_IMPLEMENTADO.md     # Cache (NOVO)
│   └── APLICAR_POSTGRESQL_OTIMIZADO.md  # Guia (NOVO)
├── scripts/
│   ├── init_postgres.py      # Inicialização
│   ├── criar_indices.py      # Índices (NOVO)
│   └── migrar_sqlite_para_postgres.py
├── postgresql.conf.optimized  # Config otimizado (NOVO)
├── iniciar_postgres.bat      # Startup script
└── README.md                 # Este arquivo
```

---

## 🎯 DECISÕES TÉCNICAS

### Por Que PostgreSQL?

✅ Escala melhor que SQLite (1000+ devices)  
✅ Índices avançados (B-tree, GIN, BRIN)  
✅ ACID completo  
✅ Replicação nativa (futuro)  
✅ Queries complexas mais rápidas  

### Por Que Cache em Memória?

✅ 90% redução de queries  
✅ Simples de implementar  
✅ Sem dependências extras  
✅ TTL automático  
❌ Não compartilhado entre workers (futuro: Redis)

### Por Que icmplib?

✅ Cross-platform (Windows, Linux, Mac)  
✅ Async nativo  
✅ Multiping (100 IPs simultâneos)  
✅ Raw ICMP (preciso como The Dude)  

### Por Que 1 Worker Uvicorn?

✅ Simplicidade  
✅ Suficiente para 20 usuários  
✅ Sem race conditions  
❌ Não escala horizontalmente (futuro: workers + Redis)

---

## 🛣️ ROADMAP

### ✅ v2.1 (Atual)

- [x] Migração PostgreSQL
- [x] Cache em memória
- [x] Índices compostos
- [x] Pool de conexões
- [x] Compressão Gzip
- [x] Limpeza de código
- [x] Documentação completa

### 🔄 v2.2 (Próximos 30 dias)

- [ ] Paginação em endpoints
- [ ] Cleanup em batches
- [ ] Monitoramento de cache
- [ ] Testes automatizados

### 📅 v3.0 (Futuro)

- [ ] Redis (cache distribuído)
- [ ] Workers múltiplos
- [ ] Particionamento de tabelas
- [ ] Read Replicas
- [ ] App móvel (APK técnico)
- [ ] Grafana integration
- [ ] Webhooks personalizados

---

## 🤝 CONTRIBUINDO

### Padrões de Código

- **Python:** PEP 8, type hints, async/await
- **TypeScript:** ESLint, functional components
- **SQL:** Lowercase, snake_case
- **Commits:** Conventional Commits

### Como Contribuir

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'feat: Nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📄 LICENÇA

MIT License - Veja `LICENSE` para detalhes.

---

## 🙏 AGRADECIMENTOS

- **icmplib** - Ping cross-platform incrível
- **FastAPI** - Framework web moderno
- **PostgreSQL** - Banco de dados robusto
- **The Dude (MikroTik)** - Inspiração para arquitetura

---

## 📞 SUPORTE

**Issues:** GitHub Issues  
**Docs:** `docs/` folder  
**Email:** [seu-email]

---

## 🎉 CHANGELOG

### v2.1 (25/12/2024)

**Performance:**
- ✨ Cache em memória (5-10x redução de queries)
- ✨ Índices compostos PostgreSQL (10-20x queries)
- ✨ Pool de conexões otimizado (20+10)
- ✨ Compressão Gzip (70-80% redução HTTP)

**Limpeza:**
- 🧹 Scripts de debug movidos para `backend/tools`
- 🧹 Docs obsoletos arquivados
- 🧹 Seção de DB removida do frontend

**Documentação:**
- 📚 7 novos guias técnicos
- 📚 README completamente reescrito
- 📚 Relatório completo de otimizações

**Ganho Total:** Sistema 3x mais rápido! 🚀

### v2.0 (20/12/2024)

- Migração para PostgreSQL
- Ping ultra-rápido (icmplib)
- SNMP paralelo
- Synthetic Agent
- Dashboard responsivo

---

**Desenvolvido com ❤️ para ISPs que valorizam performance e estabilidade.**

**Versão 2.1 - Otimizado para 1000+ dispositivos** 🚀
