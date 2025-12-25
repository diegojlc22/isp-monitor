# ⚡ FASE 2 – SIMULAÇÃO DE TESTES (CARGA / ESTRESSE / LIMITE)

**Data:** 25/12/2024  
**Contexto:** Sistema em PostgreSQL, Windows Server, Hardware típico (i5/16GB)  
**Metodologia:** Análise teórica baseada em arquitetura, sem execução real

---

## 📊 PREMISSAS TÉCNICAS

### Hardware Base (Cenário Realista)
- **CPU:** Intel i5-10400 (6 cores, 12 threads) @ 2.9GHz
- **RAM:** 16GB DDR4
- **Disco:** SSD SATA 500GB (550 MB/s read, 520 MB/s write)
- **Rede:** 1 Gbps Ethernet
- **OS:** Windows Server 2019/2022

### Software Stack
- **Python:** 3.11 (asyncio nativo)
- **PostgreSQL:** 15.x (local, default config)
- **Uvicorn:** 1 worker (conforme `iniciar_postgres.bat`)
- **Concorrência Ping:** 100 (config atual)
- **Concorrência SNMP:** 100 (config atual)

### Configurações Atuais
```python
PING_INTERVAL_SECONDS = 30
PING_TIMEOUT_SECONDS = 2
PING_CONCURRENT_LIMIT = 100
SNMP_INTERVAL = 60
SNMP_SEMAPHORE = 100
```

---

## 🧪 CENÁRIOS DE TESTE

### CENÁRIO 1: Crescimento de Dispositivos Monitorados

| Dispositivos | Comportamento Esperado | Limite Aproximado | Sintoma da Falha |
|--------------|------------------------|-------------------|------------------|
| **100** | ✅ Perfeito. Ping completa em ~2s, SNMP em ~5s | N/A | N/A |
| **300** | ✅ Estável. Ping em ~4s, SNMP em ~10s | N/A | Nenhum |
| **500** | ✅ Bom. Ping em ~6s, SNMP em ~15s | CPU ~40% | Leve aumento de latência |
| **800** | ⚠️ Aceitável. Ping em ~10s, SNMP em ~25s | CPU ~65% | Pings começam a atrasar |
| **1000** | ⚠️ Limite. Ping em ~12s, SNMP em ~30s | CPU ~80% | Timeouts ocasionais |
| **1500** | ❌ Degradação. Ping em ~20s, SNMP em ~50s | CPU ~95% | Timeouts frequentes, UI lenta |
| **2000+** | ❌ Colapso. Ping não completa no intervalo | CPU 100% | Sistema trava, DB locks |

**Gargalo Principal:** CPU (processamento de ICMP + SNMP)  
**Componente que Falha Primeiro:** Pinger (timeouts acumulam)

**Cálculo Técnico:**
```
Ping por dispositivo: ~20ms (ICMP) + ~10ms (DB write) = 30ms
Com concorrência 100: 1000 devices / 100 = 10 batches
Tempo total: 10 batches × 30ms × 2 (overhead) = ~600ms (ideal)
Real com network jitter: ~10-12s para 1000 devices
```

---

### CENÁRIO 2: Aumento de Frequência de Ping

**Baseline:** 30s (atual)

| Intervalo | Dispositivos | Comportamento | Limite | Sintoma |
|-----------|--------------|---------------|--------|---------|
| **30s** | 800 | ✅ Estável | CPU ~65% | Nenhum |
| **15s** | 800 | ⚠️ Tenso | CPU ~85% | DB writes aumentam 2x |
| **10s** | 800 | ❌ Crítico | CPU ~95% | Pings atrasam, logs acumulam |
| **5s** | 800 | ❌ Impossível | CPU 100% | Sistema não acompanha |

**Gargalo:** CPU + Disco (writes no PostgreSQL)

**Cálculo de Writes:**
```
800 devices × 2 pings/min (30s) = 1600 writes/min = ~27 writes/s
800 devices × 12 pings/min (5s) = 9600 writes/min = 160 writes/s

PostgreSQL em SSD SATA: ~5000 IOPS
Mas com índices + WAL: efetivo ~2000 writes/s
Conclusão: 160 writes/s é viável, mas CPU não aguenta processar
```

---

### CENÁRIO 3: Escritas Intensivas no Banco

**Teste:** Simular 1 mês de logs para 500 dispositivos

| Período | Registros Totais | Tamanho Estimado | Comportamento |
|---------|------------------|------------------|---------------|
| **1 dia** | 1.4M pings | ~70 MB | ✅ Normal |
| **1 semana** | 10M pings | ~500 MB | ✅ Estável |
| **1 mês** | 43M pings | ~2.1 GB | ⚠️ Queries lentas sem índices |
| **3 meses** | 130M pings | ~6.5 GB | ⚠️ Vacuum necessário |
| **6 meses** | 260M pings | ~13 GB | ❌ Precisa particionamento |

**Gargalo:** Tamanho da tabela `ping_logs`

**Impacto em Queries:**
```sql
-- Query típica do dashboard (últimos 24h)
SELECT * FROM ping_logs 
WHERE device_id = 123 AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC LIMIT 100;

Sem índice em (device_id, timestamp):
- 1M rows: ~200ms
- 10M rows: ~2s
- 43M rows: ~8s (INACEITÁVEL)

Com índice composto:
- 43M rows: ~50ms ✅
```

**Solução Atual:** 
- ✅ Índice em `timestamp DESC` existe
- ✅ Limpeza automática de 30 dias (reduz para ~43M max)
- ⚠️ Falta índice composto `(device_id, timestamp)`

---

### CENÁRIO 4: Leitura Simultânea de Gráficos

**Teste:** 10 usuários acessando dashboard simultaneamente

| Usuários | Queries/s | Comportamento | Limite | Sintoma |
|----------|-----------|---------------|--------|---------|
| **1** | ~5 | ✅ Instantâneo (<100ms) | CPU ~5% | Nenhum |
| **5** | ~25 | ✅ Rápido (~200ms) | CPU ~15% | Nenhum |
| **10** | ~50 | ✅ Bom (~500ms) | CPU ~30% | Leve delay |
| **20** | ~100 | ⚠️ Lento (~1.5s) | CPU ~60% | Gráficos demoram |
| **50** | ~250 | ❌ Travado (~5s+) | CPU ~90% | Timeout no frontend |

**Gargalo:** PostgreSQL query processing + JSON serialization

**Queries Mais Pesadas:**
1. **Dashboard principal:** 8 queries (torres, equipamentos, logs recentes, stats)
2. **Gráfico de latência:** 1 query agregada (AVG por hora, últimos 7 dias)
3. **Mapa de rede:** 2 queries (posições + status)

**Otimização Atual:**
- ✅ Queries usam índices
- ❌ Sem cache (Redis desabilitado)
- ❌ Sem paginação em alguns endpoints

**Potencial com Cache:**
```
Dashboard sem cache: 500ms
Dashboard com Redis (60s TTL): 50ms (10x mais rápido)
```

---

### CENÁRIO 5: Processamento da "IA Leve" (Synthetic Agent)

**Baseline:** 3 targets (Google DNS, Cloudflare, etc), check a cada 5 min

| Targets | Intervalo | Comportamento | Limite | Sintoma |
|---------|-----------|---------------|--------|---------|
| **3** | 5 min | ✅ Imperceptível | CPU <1% | Nenhum |
| **10** | 5 min | ✅ Leve | CPU ~2% | Nenhum |
| **50** | 5 min | ⚠️ Moderado | CPU ~10% | Baseline training lento |
| **100** | 5 min | ❌ Pesado | CPU ~25% | Queries de agregação demoram |

**Gargalo:** Query de agregação com `EXTRACT(hour, ...)` em milhões de rows

**Query Crítica:**
```sql
SELECT target, EXTRACT(hour FROM timestamp) AS hour,
       AVG(latency_ms), COUNT(*)
FROM synthetic_logs
WHERE timestamp >= NOW() - INTERVAL '14 days'
GROUP BY target, EXTRACT(hour FROM timestamp);
```

**Performance:**
- 10k logs: ~50ms ✅
- 100k logs: ~500ms ✅
- 1M logs: ~5s ⚠️
- 10M logs: ~50s ❌

**Solução:** Limitar retenção de `synthetic_logs` para 7 dias (não 30)

---

## 🔥 CENÁRIO EXTREMO: "Black Friday"

**Situação:** Todos os fatores de estresse simultaneamente

```
- 1000 dispositivos
- Ping a cada 15s
- 50 usuários no dashboard
- 20 targets do Synthetic Agent
- 30 dias de logs acumulados
```

### Resultado Esperado

| Componente | Uso | Status |
|------------|-----|--------|
| **CPU** | 95-100% | ❌ Saturado |
| **RAM** | 8-10 GB | ⚠️ Alto mas OK |
| **Disco I/O** | 80% | ⚠️ Gargalo |
| **PostgreSQL** | 200 conexões | ❌ Pool esgotado |
| **Network** | 50 Mbps | ✅ OK |

**Sintomas:**
1. Dashboard demora 10-15s para carregar
2. Pings atrasam 30-60s
3. SNMP para de funcionar (timeout)
4. Alertas do Telegram atrasam
5. Usuários reportam "sistema travado"

**Ponto de Falha:** PostgreSQL connection pool (default 20 conexões)

---

## 📈 ANÁLISE DE GARGALOS POR COMPONENTE

### 1. CPU

**Uso por Processo:**
- Pinger: 40-50% (em 1000 devices)
- SNMP Monitor: 20-30%
- Uvicorn/FastAPI: 10-15%
- PostgreSQL: 15-20%
- Synthetic Agent: 5-10%

**Limite:** ~800-1000 devices com config atual

**Escala:** Linear até 500, depois degrada exponencialmente

---

### 2. Memória (RAM)

**Uso Estimado:**
- Python process: 500 MB (base)
- Asyncio tasks (1000 devices): +1.5 GB
- PostgreSQL shared_buffers (default 128MB): +128 MB
- OS + outros: 2 GB

**Total:** ~4-5 GB para 1000 devices

**Limite:** Não é gargalo até 2000+ devices

---

### 3. Disco (I/O)

**Writes por Segundo (1000 devices, 30s interval):**
```
Ping logs: 33 writes/s
Traffic logs (SNMP 60s): 16 writes/s
Synthetic logs: 0.1 writes/s
Total: ~50 writes/s
```

**SSD SATA:** Aguenta 5000 IOPS, então I/O não é gargalo

**Mas:** PostgreSQL WAL + fsync pode criar micro-stalls

---

### 4. PostgreSQL

**Conexões Simultâneas:**
- Pinger: 1 conexão (pool interno)
- SNMP: 1 conexão
- Uvicorn: até 20 (default pool)
- Synthetic Agent: 1

**Total:** ~25 conexões pico

**Limite Default:** 100 conexões (OK)

**Gargalo Real:** Query performance sem índices adequados

---

### 5. Rede

**Tráfego Estimado (1000 devices):**
- ICMP pings: ~1 KB/device = 1 MB/30s = ~33 KB/s
- SNMP queries: ~500 bytes/device = 500 KB/60s = ~8 KB/s
- HTTP (dashboard): ~100 KB/request × 10 users = 1 MB/s

**Total:** ~1.5 MB/s = 12 Mbps

**Limite:** Não é gargalo (1 Gbps disponível)

---

## 🎯 RESUMO DOS LIMITES

| Métrica | Limite Confortável | Limite Máximo | Sintoma de Falha |
|---------|-------------------|---------------|------------------|
| **Dispositivos** | 500 | 1000 | Timeouts de ping |
| **Intervalo Ping** | 30s | 15s | CPU saturado |
| **Usuários Simultâneos** | 10 | 20 | Dashboard lento |
| **Retenção de Logs** | 30 dias | 90 dias | Queries lentas |
| **Targets Synthetic** | 10 | 50 | Training demorado |

---

## 🔬 COMPONENTE QUE "CAI PRIMEIRO"

### Em Ordem de Falha

1. **Pinger** (CPU bound) - Falha em ~1000 devices
2. **SNMP Monitor** (Network + CPU) - Falha em ~800 devices
3. **PostgreSQL Queries** (Disk I/O) - Degrada em ~60 dias de logs
4. **Dashboard** (Serialization) - Lento com 20+ usuários
5. **Synthetic Agent** (Agregação) - Lento com 100+ targets

---

## ⚠️ AVISOS IMPORTANTES

### O Que Estes Números NÃO São

❌ Benchmarks reais  
❌ Garantias de performance  
❌ Resultados de testes de carga  

### O Que Estes Números SÃO

✅ Estimativas técnicas plausíveis  
✅ Baseadas em análise de código  
✅ Considerando hardware típico  
✅ Úteis para planejamento de capacidade  

---

## 🎓 CONCLUSÕES TÉCNICAS

### Pontos Fortes

✅ **Arquitetura assíncrona** permite alta concorrência  
✅ **PostgreSQL** escala melhor que SQLite  
✅ **Batch pinging** (icmplib multiping) é muito eficiente  
✅ **Semaphores** evitam sobrecarga de rede  

### Pontos Fracos

⚠️ **CPU single-threaded** limita escala (Python GIL)  
⚠️ **Sem cache** (Redis) desperdiça CPU em queries repetidas  
⚠️ **Índices incompletos** causam queries lentas  
⚠️ **1 worker Uvicorn** limita throughput HTTP  

### Limite Realista Atual

**Configuração Atual:** 500-800 devices confortavelmente  
**Com Otimizações (Fase 3):** 1000-1500 devices  
**Com Arquitetura Distribuída:** 5000+ devices (futuro)

---

## 📊 PRÓXIMOS PASSOS

Fase 3 irá analisar estes resultados e propor:
1. Otimizações de índices
2. Implementação de cache
3. Ajustes de configuração
4. Melhorias incrementais

**Foco:** Maximizar performance sem mudanças arquiteturais drásticas.
