import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from backend.app.database import engine

logger = logging.getLogger(__name__)

async def setup_table_partitioning(conn):
    """
    Converte tabelas normais para particionadas e gerencia partições mensais.
    TARGETS: ping_logs, traffic_logs
    """
    logger.info("[OPTIMIZER] 🔄 Verificando Particionamento de Tabelas...")

    async def migrate_to_partition(table_name, create_sql, cols_sql):
        # 1. Check if table is already partitioned
        check = await conn.execute(text(
            f"SELECT relkind FROM pg_class WHERE relname = '{table_name}'"
        ))
        kind = check.scalar()
        
        if kind == 'p': # Already partitioned
            return False
            
        logger.warning(f"[OPTIMIZER] ⚠️ Migrando '{table_name}' para particionamento (Big Data Mode)...")
        
        # 2. Rename old table
        await conn.execute(text(f"ALTER TABLE {table_name} RENAME TO {table_name}_old"))
        
        # 3. Create new Partitioned Table
        await conn.execute(text(create_sql))
        
        # 4. Create Initial Partition
        next_month = (datetime.now() + timedelta(days=32)).replace(day=1)
        next_month_str = next_month.strftime("%Y-%m-%d")
        
        part_name = f"{table_name}_history"
        await conn.execute(text(
            f"CREATE TABLE {part_name} PARTITION OF {table_name} FOR VALUES FROM (MINVALUE) TO ('{next_month_str}')"
        ))
        
        # 5. Restore Data
        logger.info(f"[OPTIMIZER] 📥 Migrando dados legados de {table_name}...")
        await conn.execute(text(
            f"INSERT INTO {table_name} ({cols_sql}) SELECT {cols_sql} FROM {table_name}_old"
        ))
        
        logger.info(f"[OPTIMIZER] ✅ Migração de {table_name} concluída! Tabela antiga mantida como '{table_name}_old'.")
        return True

    # --- PING_LOGS Definition ---
    cols_ping = "device_type, device_id, status, latency_ms, timestamp"
    sql_ping = """
    CREATE TABLE ping_logs (
        id SERIAL,
        device_type VARCHAR,
        device_id INTEGER,
        status BOOLEAN,
        latency_ms INTEGER,
        timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
        PRIMARY KEY (id, timestamp)
    ) PARTITION BY RANGE (timestamp);
    """
    await migrate_to_partition("ping_logs", sql_ping, cols_ping)

    # --- TRAFFIC_LOGS Definition ---
    cols_traffic = "equipment_id, interface_index, in_mbps, out_mbps, signal_dbm, cpu_usage, memory_usage, disk_usage, temperature, voltage, timestamp"
    sql_traffic = """
    CREATE TABLE traffic_logs (
        id SERIAL,
        equipment_id INTEGER,
        interface_index INTEGER DEFAULT 1,
        in_mbps FLOAT,
        out_mbps FLOAT,
        signal_dbm FLOAT,
        cpu_usage INTEGER,
        memory_usage INTEGER,
        disk_usage INTEGER,
        temperature FLOAT,
        voltage FLOAT,
        timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
        PRIMARY KEY (id, timestamp)
    ) PARTITION BY RANGE (timestamp);
    """
    await migrate_to_partition("traffic_logs", sql_traffic, cols_traffic)
    
    # --- MAINTENANCE: Create Future Partitions ---
    today = datetime.now()
    for i in range(1, 3):
        future_date = (today + timedelta(days=32*i)).replace(day=1)
        next_mo_date = (future_date + timedelta(days=32)).replace(day=1)
        
        part_month_str = future_date.strftime("%Y_%m")
        start_str = future_date.strftime("%Y-%m-%d")
        end_str = next_mo_date.strftime("%Y-%m-%d")
        
        for tbl in ["ping_logs", "traffic_logs"]:
            p_name = f"{tbl}_{part_month_str}"
            exists = await conn.execute(text(f"SELECT 1 FROM pg_class WHERE relname = '{p_name}'"))
            if not exists.scalar():
                logger.info(f"[OPTIMIZER] Criando partição futura: {p_name}")
                await conn.execute(text(
                    f"CREATE TABLE {p_name} PARTITION OF {tbl} FOR VALUES FROM ('{start_str}') TO ('{end_str}')"
                ))

async def apply_postgres_optimizations():
    """Aplica otimizações avançadas específicas para PostgreSQL."""
    conn_url = str(engine.url)
    if "postgresql" not in conn_url:
        logger.info("[INFO] Ignorando otimizações Postgres (Banco atual não é Postgres)")
        return

    logger.info("[INFO] Verificando otimizações avançadas Postgres...")
    
    async with engine.begin() as conn:
        # 1. Verificar/Criar BRIN Index em ping_logs
        try:
            check_index = await conn.execute(text(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_ping_logs_brin_timestamp'"
            ))
            
            if not check_index.scalar():
                logger.info("[OPTIMIZER] Criando índice BRIN em ping_logs (pode demorar um pouco)...")
                await conn.execute(text(
                    "CREATE INDEX idx_ping_logs_brin_timestamp ON ping_logs USING BRIN (timestamp) WITH (pages_per_range = 128);"
                ))
                logger.info("[OPTIMIZER] Índice BRIN criado com sucesso para PING_LOGS! 🚀")
            else:
                logger.debug("[OPTIMIZER] Índice BRIN já existe em ping_logs.")

            # 1.1 Verificar/Criar BRIN Index em traffic_logs
            check_index_traffic = await conn.execute(text(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_traffic_logs_brin_timestamp'"
            ))
            
            if not check_index_traffic.scalar():
                 logger.info("[OPTIMIZER] Criando índice BRIN em traffic_logs...")
                 await conn.execute(text(
                     "CREATE INDEX idx_traffic_logs_brin_timestamp ON traffic_logs USING BRIN (timestamp) WITH (pages_per_range = 128);"
                 ))
                 logger.info("[OPTIMIZER] Índice BRIN criado com sucesso para TRAFFIC_LOGS! 🚀")
            else:
                 logger.debug("[OPTIMIZER] Índice BRIN já existe em traffic_logs.")
                
        except Exception as e:
            logger.warning(f"[WARN] Falha ao criar índice BRIN: {e}")

        # 2. Particionamento de Tabelas
        try:
            await setup_table_partitioning(conn)
        except Exception as e:
            logger.error(f"[ERROR] Falha crítica no particionamento: {e}")
            pass

        # 3. Tuning de Autovacuum
        try:
            async def optimize_table_and_partitions(target_table):
                query_partitions = text(f"""
                    SELECT child.relname 
                    FROM pg_inherits 
                    JOIN pg_class parent ON pg_inherits.inhparent = parent.oid 
                    JOIN pg_class child ON pg_inherits.inhrelid = child.oid 
                    WHERE parent.relname = '{target_table}'
                """)
                
                result = await conn.execute(query_partitions)
                partitions = result.scalars().all()
                
                targets = partitions if partitions else [target_table]
                    
                for tbl in targets:
                    try:
                        await conn.execute(text(
                            f"ALTER TABLE {tbl} SET (autovacuum_vacuum_scale_factor = 0.01, autovacuum_analyze_scale_factor = 0.005);"
                        ))
                    except Exception as inner_e:
                        logger.warning(f"[WARN] Falha ao tunar {tbl}: {inner_e}")
                
                return len(targets)

            count_ping = await optimize_table_and_partitions("ping_logs")
            count_traffic = await optimize_table_and_partitions("traffic_logs")
            
            logger.info(f"[OPTIMIZER] Autovacuum ajustado em {count_ping + count_traffic} tabelas/partições.")
            
        except Exception as e:
            logger.warning(f"[WARN] Falha ao ajustar autovacuum: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(apply_postgres_optimizations())
