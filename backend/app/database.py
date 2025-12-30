from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
from backend.app.config import settings, logger

# Engine Creation - Pure PostgreSQL Logic
connect_args = {"server_settings": {"application_name": "isp_monitor_backend"}}

# Standard Production Pool Settings
# Configuração Otimizada para PostgreSQL Async
try:
    engine = create_async_engine(
        settings.async_database_url,
        echo=False,
        future=True, # SQLAlchemy 2.0 style
        pool_size=20, # Tamanho do pool
        max_overflow=10, # Conexões extras permitidas
        pool_timeout=30, # Timeout para pegar conexão
        pool_pre_ping=True, # Evita conexões mortas
        connect_args=connect_args
        # Para Async Engine, NÃO passamos poolclass=QueuePool explicitamente,
        # o create_async_engine já usa um pool compatível (AsyncAdaptedQueuePool) por padrão.
    )
    logger.info("✅ PostgreSQL Async Engine Created")
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

async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database Session Error: {e}")
            raise
        finally:
            await session.close()
