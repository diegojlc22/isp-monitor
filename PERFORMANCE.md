# ⚡ Otimizações de Performance - ISP Monitor

Este documento explica as otimizações implementadas para suportar **800+ equipamentos** em produção.

## 📊 Melhorias Implementadas

### 1. **Pinging Ultra-Rápido com `icmplib`**

#### ✅ Solução Recomendada: icmplib (Funciona no Windows!)
- ✅ **Funciona em Windows, Linux e Mac** (cross-platform)
- ✅ **10x mais rápido** que ping3 tradicional
- ✅ Pinga **TODOS os IPs simultaneamente** (como The Dude da Mikrotik)
- ✅ 800 devices = **~3-5 segundos** por ciclo completo
- ✅ Usa ICMP Raw Sockets (mesma técnica do The Dude)
- ⚠️ Requer executar como **Administrador no Windows** (igual The Dude)

**Como funciona:**
```python
# Pinga 800 IPs ao mesmo tempo!
results = await async_multiping(all_ips, count=1, timeout=2)
```

**Instalação:**
```bash
# Já incluído no requirements.txt
pip install icmplib

# Windows: Execute o backend como Administrador
# Linux: Execute com sudo ou configure capabilities
```

#### Opção B: ping3 (Fallback automático)
- ✅ Funciona sem privilégios de admin
- ⚠️ Mais lento (pings sequenciais)
- ⚠️ 800 devices = ~40-60s por ciclo

**O sistema usa icmplib automaticamente se disponível, senão usa ping3.**

### 2. **Intervalo de Ping Configurável**

Para 800 equipamentos, recomendamos:
- **Desenvolvimento**: 5-10 segundos
- **Produção**: 30-60 segundos

**Configuração:**
```bash
# No arquivo .env
PING_INTERVAL_SECONDS=30
```

**Por quê 30s?**
- Reduz carga no servidor
- Reduz tráfego de rede
- Ainda detecta problemas rapidamente
- 800 devices × 30s = 24,000 pings/hora (gerenciável)

### 3. **Limpeza Automática de Logs**

Os logs de ping são limpos automaticamente para evitar crescimento infinito do banco de dados.

**Configuração:**
```bash
# No arquivo .env
LOG_RETENTION_DAYS=30  # Manter logs por 30 dias
```

**Estimativa de espaço:**
- 800 devices × 2,880 pings/dia (30s) × 30 dias = ~69 milhões de registros
- Com PostgreSQL e índices adequados: ~5-10 GB
- Logs mais antigos são deletados automaticamente a cada 24h

### 4. **Cache com Redis (Opcional)**

Para sistemas com 500+ dispositivos, o cache Redis melhora significativamente a performance do dashboard.

**Instalação:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# No arquivo .env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=60
```

**Benefícios:**
- Dashboard carrega instantaneamente (dados em cache)
- Reduz carga no banco de dados
- Melhora experiência do usuário

## 🚀 Configuração para Produção (800 Equipamentos)

### Arquivo `.env` Recomendado:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://isp_user:senha_forte@localhost:5432/isp_monitor

# Ping Otimizado
PING_INTERVAL_SECONDS=30
PING_TIMEOUT_SECONDS=2
PING_CONCURRENT_LIMIT=100
USE_FPING=true

# Log Retention
LOG_RETENTION_DAYS=30

# Redis Cache
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=60
```

### Requisitos de Hardware:

**Mínimo:**
- CPU: 2 cores
- RAM: 4 GB
- Disco: 50 GB SSD
- Rede: 10 Mbps

**Recomendado:**
- CPU: 4 cores
- RAM: 8 GB
- Disco: 100 GB SSD
- Rede: 100 Mbps

## 📈 Performance Esperada

| Configuração | Tempo por Ciclo | Carga CPU | Carga RAM |
|--------------|----------------|-----------|-----------|
| ping3 + 5s   | ~40s           | 60-80%    | 2-3 GB    |
| ping3 + 30s  | ~40s           | 20-30%    | 2-3 GB    |
| fping + 30s  | ~5s            | 10-15%    | 1-2 GB    |
| fping + Redis| ~5s            | 5-10%     | 2-3 GB    |

## 🔧 Monitoramento

Para verificar a performance do sistema:

```bash
# Ver logs do backend
tail -f /var/log/isp-monitor/backend.log

# Verificar uso de recursos
htop

# Verificar tamanho do banco
du -sh monitor.db  # SQLite
# ou
psql -c "SELECT pg_size_pretty(pg_database_size('isp_monitor'));"  # PostgreSQL
```

## 📝 Notas Importantes

1. **fping no Windows**: Não funciona. Use ping3 ou considere WSL.
2. **PostgreSQL**: Obrigatório para 500+ dispositivos.
3. **Redis**: Opcional mas altamente recomendado para 500+.
4. **Backup**: Configure backups automáticos do PostgreSQL.

## 🆘 Troubleshooting

**Problema**: Pings muito lentos
- ✅ Ative `USE_FPING=true` (Linux)
- ✅ Aumente `PING_CONCURRENT_LIMIT` para 200
- ✅ Reduza `PING_TIMEOUT_SECONDS` para 1

**Problema**: Banco de dados crescendo muito
- ✅ Reduza `LOG_RETENTION_DAYS` para 15 ou 7
- ✅ Migre para PostgreSQL
- ✅ Configure vacuum automático (PostgreSQL)

**Problema**: Dashboard lento
- ✅ Ative Redis cache
- ✅ Aumente `CACHE_TTL_SECONDS` para 120
- ✅ Verifique índices no banco de dados
