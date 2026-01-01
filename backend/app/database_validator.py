"""
Database Schema Validator & Auto-Repair
Garante que o schema do banco está sempre consistente com os models.
Executa automaticamente no startup do backend.
"""
import asyncio
from sqlalchemy import select, text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from backend.app.database import AsyncSessionLocal, engine
from backend.app.models import Base, Parameters, Equipment, Tower, TrafficLog

# Schema esperado para cada tabela crítica
EXPECTED_SCHEMA = {
    "equipments": {
        "columns": {
            "id": "INTEGER",
            "name": "VARCHAR",
            "ip": "VARCHAR",
            "brand": "VARCHAR",
            "is_online": "BOOLEAN",
            "last_checked": "TIMESTAMP",
            "last_latency": "FLOAT",
            "last_traffic_in": "BIGINT",
            "last_traffic_out": "BIGINT",
            "signal_dbm": "FLOAT",  # CRÍTICO: deve ser FLOAT
            "ccq": "INTEGER",
            "connected_clients": "INTEGER",
            "snmp_community": "VARCHAR",
            "snmp_port": "INTEGER",
            "snmp_interface_index": "INTEGER",
            "snmp_traffic_interface_index": "INTEGER",
            "ssh_user": "VARCHAR",
            "ssh_password": "VARCHAR",
            "ssh_port": "INTEGER",
            "equipment_type": "VARCHAR",
            "tower_id": "INTEGER",
        }
    },
    "traffic_logs": {
        "columns": {
            "id": "INTEGER",
            "equipment_id": "INTEGER",
            "timestamp": "TIMESTAMP",
            "in_mbps": "FLOAT",
            "out_mbps": "FLOAT",
            "signal_dbm": "FLOAT",  # CRÍTICO: deve ser FLOAT
        }
    },
    "parameters": {
        "columns": {
            "key": "VARCHAR",
            "value": "TEXT",
        }
    }
}

# Parâmetros obrigatórios que devem existir
REQUIRED_PARAMETERS = {
    "system_name": "ISP Monitor",
    "latency_good": "50",
    "latency_critical": "200",
    "default_ssh_user": "admin",
    "default_ssh_password": "",
    "default_snmp_community": "publicRadionet",
    "dashboard_layout": "[]",
    "telegram_enabled": "true",
    "whatsapp_enabled": "false",
    "notify_equipment_status": "true",
    "notify_backups": "true",
    "notify_agent": "true",
}


async def validate_column_type(db: AsyncSession, table: str, column: str, expected_type: str) -> bool:
    """Valida se uma coluna tem o tipo correto"""
    try:
        result = await db.execute(text(f"""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            AND column_name = '{column}'
        """))
        row = result.fetchone()
        
        if not row:
            logger.warning(f"❌ Coluna {table}.{column} não existe!")
            return False
            
        actual_type = row[0].upper()
        
        # Normalização de tipos
        type_mapping = {
            "DOUBLE PRECISION": "FLOAT",
            "REAL": "FLOAT",
            "CHARACTER VARYING": "VARCHAR",
            "TIMESTAMP WITHOUT TIME ZONE": "TIMESTAMP",
        }
        
        actual_type = type_mapping.get(actual_type, actual_type)
        
        if actual_type != expected_type.upper():
            logger.error(f"❌ ERRO DE TIPO: {table}.{column} é {actual_type}, esperado {expected_type}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Erro validando {table}.{column}: {e}")
        return False


async def repair_column_type(db: AsyncSession, table: str, column: str, expected_type: str):
    """Corrige o tipo de uma coluna"""
    try:
        logger.warning(f"🔧 Corrigindo tipo de {table}.{column} para {expected_type}...")
        
        # Mapeamento para tipos SQL corretos
        sql_type_map = {
            "FLOAT": "DOUBLE PRECISION",
            "INTEGER": "INTEGER",
            "BIGINT": "BIGINT",
            "VARCHAR": "VARCHAR(255)",
            "TEXT": "TEXT",
            "BOOLEAN": "BOOLEAN",
            "TIMESTAMP": "TIMESTAMP",
        }
        
        sql_type = sql_type_map.get(expected_type.upper(), expected_type)
        
        await db.execute(text(f"""
            ALTER TABLE {table} 
            ALTER COLUMN {column} TYPE {sql_type} 
            USING {column}::{sql_type}
        """))
        await db.commit()
        
        logger.success(f"✅ {table}.{column} corrigido para {expected_type}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Falha ao corrigir {table}.{column}: {e}")
        await db.rollback()
        return False


async def ensure_parameter_exists(db: AsyncSession, key: str, default_value: str):
    """Garante que um parâmetro existe no banco"""
    try:
        result = await db.execute(select(Parameters).where(Parameters.key == key))
        param = result.scalar_one_or_none()
        
        if not param:
            logger.warning(f"⚠️ Parâmetro '{key}' ausente. Criando com valor padrão...")
            new_param = Parameters(key=key, value=default_value)
            db.add(new_param)
            await db.commit()
            logger.success(f"✅ Parâmetro '{key}' criado")
            return True
        else:
            logger.debug(f"✓ Parâmetro '{key}' OK")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar parâmetro '{key}': {e}")
        await db.rollback()
        return False


async def validate_and_repair_database():
    """
    Validação completa e auto-reparo do banco de dados.
    Retorna True se tudo estiver OK, False se houver erros críticos.
    """
    logger.info("🔍 Iniciando validação do banco de dados...")
    
    all_ok = True
    
    async with AsyncSessionLocal() as db:
        # 1. Validar tipos de colunas críticas
        logger.info("📋 Validando schema das tabelas...")
        
        for table_name, schema in EXPECTED_SCHEMA.items():
            for column_name, expected_type in schema["columns"].items():
                is_valid = await validate_column_type(db, table_name, column_name, expected_type)
                
                if not is_valid:
                    # Tentar reparar
                    repaired = await repair_column_type(db, table_name, column_name, expected_type)
                    if not repaired:
                        all_ok = False
        
        # 2. Validar parâmetros obrigatórios
        logger.info("⚙️ Validando parâmetros do sistema...")
        
        for key, default_value in REQUIRED_PARAMETERS.items():
            param_ok = await ensure_parameter_exists(db, key, default_value)
            if not param_ok:
                all_ok = False
        
        # 3. Verificar integridade referencial básica
        logger.info("🔗 Verificando integridade referencial...")
        
        try:
            # Contar equipamentos órfãos (tower_id inválido)
            result = await db.execute(text("""
                SELECT COUNT(*) 
                FROM equipments e 
                WHERE e.tower_id IS NOT NULL 
                AND NOT EXISTS (SELECT 1 FROM towers t WHERE t.id = e.tower_id)
            """))
            orphan_count = result.scalar()
            
            if orphan_count > 0:
                logger.warning(f"⚠️ {orphan_count} equipamentos com tower_id inválido")
                # Limpar referências inválidas
                await db.execute(text("""
                    UPDATE equipments 
                    SET tower_id = NULL 
                    WHERE tower_id IS NOT NULL 
                    AND NOT EXISTS (SELECT 1 FROM towers t WHERE t.id = equipments.tower_id)
                """))
                await db.commit()
                logger.success(f"✅ Referências inválidas limpas")
                
        except Exception as e:
            logger.error(f"❌ Erro na validação de integridade: {e}")
            all_ok = False
    
    if all_ok:
        logger.success("✅ Banco de dados validado e íntegro!")
    else:
        logger.error("❌ Banco de dados possui erros que não puderam ser corrigidos automaticamente")
    
    return all_ok


async def create_tables_if_not_exist():
    """Cria todas as tabelas se não existirem"""
    try:
        logger.info("📦 Verificando existência das tabelas...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("✅ Tabelas verificadas/criadas")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        return False


async def full_database_check():
    """
    Verificação completa do banco de dados.
    Deve ser chamada no startup do backend.
    """
    logger.info("=" * 60)
    logger.info("🚀 VALIDAÇÃO AUTOMÁTICA DO BANCO DE DADOS")
    logger.info("=" * 60)
    
    # 1. Criar tabelas se necessário
    tables_ok = await create_tables_if_not_exist()
    if not tables_ok:
        logger.critical("❌ FALHA CRÍTICA: Não foi possível criar/verificar tabelas")
        return False
    
    # 2. Validar e reparar schema
    schema_ok = await validate_and_repair_database()
    
    logger.info("=" * 60)
    if schema_ok:
        logger.success("✅ BANCO DE DADOS PRONTO PARA USO")
    else:
        logger.error("⚠️ BANCO DE DADOS COM PROBLEMAS - Verifique os logs acima")
    logger.info("=" * 60)
    
    return schema_ok


if __name__ == "__main__":
    # Permite executar standalone para diagnóstico
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    result = asyncio.run(full_database_check())
    sys.exit(0 if result else 1)
