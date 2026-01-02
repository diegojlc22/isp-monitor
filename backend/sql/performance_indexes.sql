-- Otimizações de Performance para ISP Monitor
-- Foco: Reduzir uso de CPU no DB e acelerar buscas em 405+ equipamentos

-- 1. Equipamentos: Filtros comuns (Status, Torre, IP)
CREATE INDEX IF NOT EXISTS idx_equipments_online ON equipments(is_online);
CREATE INDEX IF NOT EXISTS idx_equipments_tower_id ON equipments(tower_id);
CREATE INDEX IF NOT EXISTS idx_equipments_ip ON equipments(ip);
CREATE INDEX IF NOT EXISTS idx_equipments_brand ON equipments(brand);
CREATE INDEX IF NOT EXISTS idx_equipments_type ON equipments(equipment_type);

-- 2. Histórico de Latência: Busca por equipamento e tempo
-- Esta tabela cresce muito, este índice é vital
CREATE INDEX IF NOT EXISTS idx_latency_eq_ts ON latency_history(equipment_id, timestamp DESC);

-- 3. Alertas: Ordenação por data (usado no Dashboard e Saúde)
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp_desc ON alerts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_device_ip ON alerts(device_ip);

-- 4. Torres: Filtros de status
CREATE INDEX IF NOT EXISTS idx_towers_online ON towers(is_online);

-- 5. Atualizar estatísticas do Postgres para o Planejador de Queries
ANALYZE equipments;
ANALYZE latency_history;
ANALYZE alerts;
ANALYZE towers;
