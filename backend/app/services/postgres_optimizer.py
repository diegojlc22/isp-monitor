import logging
from sqlalchemy import text
from backend.app.database import engine

logger = logging.getLogger(__name__)

async def apply_postgres_optimizations():
    """
    Aplica otimizações avançadas específicas para PostgreSQL.
    Foco: Big Data (BRIN Index) para tabelas de logs.
    """
    conn_url = str(engine.url)
    if "postgresql" not in conn_url:
        print("[INFO] Ignorando otimizações Postgres (Banco atual não é Postgres)")
        return

    print("[INFO] Verificando otimizações avançadas Postgres...")
    
    async with engine.begin() as conn:
        # 1. Verificar/Criar BRIN Index em ping_logs
        # BRIN (Block Range INdex) é excelente para timestamps sequenciais em tabelas gigantes
        try:
            # Verifica se o índice já existe
            check_index = await conn.execute(text(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_ping_logs_brin_timestamp'"
            ))
            
            if not check_index.scalar():
                print("[OPTIMIZER] Criando índice BRIN em ping_logs (pode demorar um pouco)...")
                await conn.execute(text(
                    "CREATE INDEX idx_ping_logs_brin_timestamp ON ping_logs USING BRIN (timestamp) WITH (pages_per_range = 128);"
                ))
                print("[OPTIMIZER] Índice BRIN criado com sucesso! 🚀")
            else:
                print("[OPTIMIZER] Índice BRIN já existe. Pular.")
                
        except Exception as e:
            print(f"[WARN] Falha ao criar índice BRIN: {e}")

        # 2. Tuning de Autovacuum para tabelas de alta escrita
        try:
            # Ajustar autovacuum para ser mais agressivo na tabela de logs para evitar inchaço
            await conn.execute(text(
                "ALTER TABLE ping_logs SET (autovacuum_vacuum_scale_factor = 0.01, autovacuum_analyze_scale_factor = 0.005);"
            ))
            print("[OPTIMIZER] Autovacuum ajustado para ping_logs.")
        except Exception as e:
            print(f"[WARN] Falha ao ajustar autovacuum: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(apply_postgres_optimizations())
