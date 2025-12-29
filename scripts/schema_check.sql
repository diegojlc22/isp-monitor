-- Verifica e cria colunas faltantes na tabela equipments
-- Este script é chamado automaticamente pelo ABRIR_SISTEMA.bat

DO $$
BEGIN
    -- last_ping
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='last_ping') THEN
        ALTER TABLE equipments ADD COLUMN last_ping FLOAT;
    END IF;

    -- last_latency
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='last_latency') THEN
        ALTER TABLE equipments ADD COLUMN last_latency FLOAT;
    END IF;

    -- last_traffic_in
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='last_traffic_in') THEN
        ALTER TABLE equipments ADD COLUMN last_traffic_in BIGINT;
    END IF;

    -- last_traffic_out
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='last_traffic_out') THEN
        ALTER TABLE equipments ADD COLUMN last_traffic_out BIGINT;
    END IF;

    -- signal_dbm
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='signal_dbm') THEN
        ALTER TABLE equipments ADD COLUMN signal_dbm INTEGER;
    END IF;

    -- ccq
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='ccq') THEN
        ALTER TABLE equipments ADD COLUMN ccq INTEGER;
    END IF;

    -- connected_clients
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='connected_clients') THEN
        ALTER TABLE equipments ADD COLUMN connected_clients INTEGER;
    END IF;

    -- whatsapp_groups
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='whatsapp_groups') THEN
        ALTER TABLE equipments ADD COLUMN whatsapp_groups TEXT;
    END IF;

    -- equipment_type
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='equipment_type') THEN
        ALTER TABLE equipments ADD COLUMN equipment_type VARCHAR(50) DEFAULT 'station';
    END IF;

    -- maintenance_until
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='maintenance_until') THEN
        ALTER TABLE equipments ADD COLUMN maintenance_until TIMESTAMP;
    END IF;

END $$;
