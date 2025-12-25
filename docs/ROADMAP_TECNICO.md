# 🚀 Roadmap Técnico - Próximas Versões

Este documento detalha o plano de implementação para escalar o ISP Monitor para nível Enterprise (2.000+ dispositivos).

## 1. Arquitetura: Separação de Responsabilidades
**Objetivo:** Impedir que lentidão na API afete o monitoramento e vice-versa.

- [ ] **Criar `services/collector.py`**:
  - Mover lógica de loop infinito e `pinger` para este arquivo.
  - Deve conectar no banco independentemente da API.
  - Implementar sistema de "Heartbeat" para a API saber que o coletor está vivo.
- [ ] **Atualizar Launcher**:
  - Iniciar `collector.py` como um processo subprocesso independente.
- [ ] **Benefício**: API fica 100% livre para servir o frontend instantaneamente.

## 2. Banco de Dados: Otimização Big Data (PostgreSQL)

### BRIN Index (Para >1 Milhão de registros)
Ideal para colunas que crescem sequencialmente (datas/IDs).
```sql
-- Exemplo de implementação
CREATE INDEX CONCURRENTLY idx_ping_logs_brin_created_at 
ON ping_logs 
USING BRIN (created_at) 
WITH (pages_per_range = 128);
```

### Particionamento (Para >5 Milhões de registros)
Divide a tabela gigante em arquivos físicos menores.
```sql
-- 1. Renomear tabela atual
ALTER TABLE ping_logs RENAME TO ping_logs_old;

-- 2. Criar nova particionada
CREATE TABLE ping_logs (
    id BIGSERIAL,
    target_id INTEGER,
    latency INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 3. Criar partições mensais
CREATE TABLE ping_logs_2025_01 PARTITION OF ping_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

## 3. Frontend: Performance (React)

### Memoização
Evitar re-renderização de componentes pesados (Mapas, Gráficos).
- [ ] Usar `React.memo` em componentes de apresentação puros.
- [ ] Usar `useMemo` para filtros de listas grandes (>100 itens).
- [ ] Usar `useCallback` para funções passadas como props.
- [ ] **Virtualização**: Usar `react-window` para listas de dispositivos se passar de 500 itens na tela.

## 4. Escala: 2000+ Dispositivos

### Otimização do Pinger
- [ ] **AsyncICMP Batching**: Enviar pings em blocos de 256 IPs simultâneos.
- [ ] **Aumentar File Descriptors**: No Linux/Windows, aumentar limite de sockets abertos.
- [ ] **Worker Pools**:
  ```python
  # Exemplo conceitual
  from multiprocessing import Pool
  def check_chunk(ips): ...
  
  with Pool(4) as p: # Usar 4 núcleos
      p.map(check_chunk, chunks_de_ips)
  ```

### Tuning Postgres
- Aumentar `shared_buffers` para 2GB+.
- Aumentar `max_wal_size` para reduzir checkpoints.
- Usar **PgBouncer** para gerenciar conexões se tiver muitos processos python.
