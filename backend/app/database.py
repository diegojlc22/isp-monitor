from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
from backend.app.config import settings, logger

# Engine Creation - Pure PostgreSQL Logic
db_url = settings.async_database_url
if "localhost" in db_url:
    db_url = db_url.replace("localhost", "127.0.0.1")

connect_args = {
    "server_settings": {"application_name": "isp_monitor_backend"},
    "command_timeout": 60
}

# Configuração Otimizada para PostgreSQL Async
try:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_size=10, # Reduzi de 20 para 10 para ser mais leve
        max_overflow=5,
        pool_timeout=60,
        pool_recycle=1800, # Recicla conexões a cada 30 min
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

async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database Session Error: {e}")
            raise
        finally:
            await session.close()
