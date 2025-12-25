-- ---------------------------------------------------------
-- SCRIPTS DE OTIMIZAÇÃO AVANÇADA PARA POSTGRESQL (ISP MONITOR)
-- Rodar estes comandos apenas quando atingir a escala mencionada
-- ---------------------------------------------------------

-- =========================================================
-- 1. BRIN INDEX (Para quando tiver > 1 Milhão de pings)
-- =========================================================
-- O índice BRIN é minúsculo e perfeito para logs ordenados por data.
-- Ele resume "blocos" de dados em vez de indexar linha por linha.

-- Primeiro, verificamos se o índice btree já existe para removê-lo (opcional, para economizar espaço)
-- DROP INDEX IF EXISTS idx_ping_logs_timestamp;

-- Criar o índice BRIN na coluna timestamp (que deve ser a de data/hora)
CREATE INDEX CONCURRENTLY idx_ping_logs_brin_timestamp 
ON ping_logs 
USING BRIN (timestamp) 
WITH (pages_per_range = 128);

-- NOTA: Se sua coluna chama 'created_at', mude 'timestamp' para 'created_at'.


-- =========================================================
-- 2. PARTICIONAMENTO (Para quando tiver > 10 Milhões de logs)
-- =========================================================
-- Isso requer recriar a tabela. O PostgreSQL gerencia as "partes" automaticamente.

/* 
-- Passo A: Renomear a tabela atual para backup
ALTER TABLE ping_logs RENAME TO ping_logs_old;

-- Passo B: Criar a tabela mestre particionada
CREATE TABLE ping_logs (
    id BIGSERIAL,
    target_id INTEGER NOT NULL,
    latency_ms INTEGER,
    status BOOLEAN,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
) PARTITION BY RANGE (timestamp);

-- Passo C: Criar índices na tabela mestre
CREATE INDEX idx_ping_logs_target_id ON ping_logs(target_id);
CREATE INDEX idx_ping_logs_timestamp ON ping_logs USING BRIN(timestamp);

-- Passo D: Criar partições (Exemplo para 2025)
-- Você pode criar um script Python para gerar isso todo mês

CREATE TABLE ping_logs_2025_01 PARTITION OF ping_logs
    FOR VALUES FROM ('2025-01-01 00:00:00') TO ('2025-02-01 00:00:00');

CREATE TABLE ping_logs_2025_02 PARTITION OF ping_logs
    FOR VALUES FROM ('2025-02-01 00:00:00') TO ('2025-03-01 00:00:00');

-- Passo E: Migrar dados antigos (Pode demorar!)
INSERT INTO ping_logs SELECT * FROM ping_logs_old;
*/

-- =========================================================
-- 3. MANUTENÇÃO AUTOMÁTICA (VACUUM E ANALYZE)
-- =========================================================
-- O PostgreSQL precisa "limpar" linhas mortas. 
-- Estes comandos forçam uma otimização total da tabela.

VACUUM (VERBOSE, ANALYZE) ping_logs;
