from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
from backend.app.config import settings, logger

# Engine Creation - Pure PostgreSQL Logic
db_url = settings.async_database_url
if "localhost" in db_url:
    db_url = db_url.replace("localhost", "127.0.0.1")

# Configuração Ultra-Light para PostgreSQL Async (Anti-Overload)
connect_args = {
    "server_settings": {"application_name": "isp_monitor_backend"},
    "command_timeout": 30
}

try:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_size=20,      # Aumentado para lidar com 400+ dispositivos
        max_overflow=10,   # Aumentado para picos de scanner/polling
        pool_timeout=30,
        pool_recycle=300,  # Recicla a cada 5 min
        pool_pre_ping=True,
        connect_args=connect_args
    )
    logger.info("✅ PostgreSQL Async Engine Created (127.0.0.1)")
except Exception as e:
    logger.critical(f"❌ Failed to create DB engine: {e}")
    raise

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

AsyncSessionLocal = async_session_factory

class Base(DeclarativeBase):
    pass

# Compatibility with Launcher
async def init_db():
    logger.info("🚀 [INIT_DB] Iniciando verificação de tabelas...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ [INIT_DB] Tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        logger.error(f"❌ [INIT_DB] Erro ao inicializar banco: {e}")
        # Launcher expects this to succeed or at least not crash the system silently

async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database Session Error: {e}")
            raise
        finally:
            await session.close()
