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

END $$;
