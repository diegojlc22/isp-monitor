-- =========================================================
-- OTIMIZAÇÕES DE PERFORMANCE - FASE 2
-- Data: 2025-12-26
-- Objetivo: Adicionar índices para queries mais rápidas
-- Impacto Esperado: 50-80% redução no tempo de queries
-- Risco: BAIXO (índices não quebram funcionalidades)
-- =========================================================

-- =========================================================
-- 1. ÍNDICES NA TABELA EQUIPMENTS
-- =========================================================

-- Índice para filtros por status (Online/Offline)
-- Usado em: GET /equipments/ com filtro de status
CREATE INDEX IF NOT EXISTS idx_equipments_is_online 
ON equipments(is_online);

-- Índice para filtros por torre
-- Usado em: GET /equipments/ com filtro de torre
CREATE INDEX IF NOT EXISTS idx_equipments_tower_id 
ON equipments(tower_id) 
WHERE tower_id IS NOT NULL;

-- Índice para filtros por tipo de equipamento
-- Usado em: GET /equipments/ com filtro de tipo
CREATE INDEX IF NOT EXISTS idx_equipments_type 
ON equipments(equipment_type);

-- Índice composto para queries que filtram múltiplos campos
-- Usado em: Filtros combinados (torre + status)
CREATE INDEX IF NOT EXISTS idx_equipments_tower_status 
ON equipments(tower_id, is_online) 
WHERE tower_id IS NOT NULL;

-- Índice para busca por IP (usado em validações de duplicatas)
-- Usado em: POST /equipments/ (check de IP duplicado)
CREATE INDEX IF NOT EXISTS idx_equipments_ip 
ON equipments(ip);

-- =========================================================
-- 2. ÍNDICES NA TABELA PING_LOGS
-- =========================================================

-- Índice para queries de histórico por equipamento
-- Usado em: GET /equipments/{id}/latency-history
CREATE INDEX IF NOT EXISTS idx_ping_logs_device 
ON ping_logs(device_type, device_id, timestamp DESC);

-- Índice para limpeza de logs antigos (performance de DELETE)
CREATE INDEX IF NOT EXISTS idx_ping_logs_timestamp 
ON ping_logs(timestamp);

-- =========================================================
-- 3. ÍNDICES NA TABELA TRAFFIC_LOGS
-- =========================================================

-- Índice para queries de histórico de tráfego
-- Usado em: GET /equipments/{id}/traffic-history
CREATE INDEX IF NOT EXISTS idx_traffic_logs_equipment 
ON traffic_logs(equipment_id, timestamp DESC);

-- =========================================================
-- 4. ÍNDICES NA TABELA TOWERS
-- =========================================================

-- Índice para busca por nome (usado em autocomplete/busca)
CREATE INDEX IF NOT EXISTS idx_towers_name 
ON towers(name);

-- =========================================================
-- 5. ÍNDICES NA TABELA USERS
-- =========================================================

-- Índice para login (busca por email)
-- Usado em: POST /auth/login
CREATE INDEX IF NOT EXISTS idx_users_email 
ON users(email);

-- =========================================================
-- 6. ANÁLISE E ESTATÍSTICAS
-- =========================================================

-- Atualizar estatísticas para o query planner
ANALYZE equipments;
ANALYZE ping_logs;
ANALYZE traffic_logs;
ANALYZE towers;
ANALYZE users;

-- =========================================================
-- 7. VERIFICAÇÃO DE ÍNDICES CRIADOS
-- =========================================================

-- Query para verificar índices criados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- =========================================================
-- NOTAS DE PERFORMANCE:
-- =========================================================
-- 1. Índices são criados com IF NOT EXISTS (seguro para re-executar)
-- 2. Índices parciais (WHERE) são menores e mais eficientes
-- 3. Índices compostos otimizam queries com múltiplos filtros
-- 4. ANALYZE atualiza estatísticas para melhor query planning
-- 5. Índices DESC otimizam ORDER BY timestamp DESC

-- =========================================================
-- MONITORAMENTO:
-- =========================================================
-- Para verificar uso de índices em uma query:
-- EXPLAIN ANALYZE SELECT * FROM equipments WHERE is_online = true;

-- Para ver tamanho dos índices:
-- SELECT 
--     indexrelname as index_name,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size
-- FROM pg_stat_user_indexes
-- ORDER BY pg_relation_size(indexrelid) DESC;
