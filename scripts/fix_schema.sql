-- Adiciona colunas faltantes na tabela equipments
-- Execute com: psql -U postgres -d isp_monitor -f fix_schema.sql

-- Adicionar colunas se não existirem
ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_ping FLOAT;
ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_latency FLOAT;
ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_in BIGINT;
ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_out BIGINT;
ALTER TABLE equipments ADD COLUMN IF NOT EXISTS signal_dbm INTEGER;
ALTER TABLE equipments ADD COLUMN IF NOT EXISTS ccq INTEGER;
ALTER TABLE equipments ADD COLUMN IF NOT EXISTS connected_clients INTEGER;

-- Confirmar
SELECT 'Schema atualizado com sucesso!' AS status;
