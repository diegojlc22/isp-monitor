from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event
from backend.app.config import settings, logger

# Engine Creation
is_sqlite = "sqlite" in settings.async_database_url

connect_args = {}
pool_class = QueuePool

if is_sqlite:
    connect_args = {"check_same_thread": False}
    pool_class = NullPool # Let aiosqlite handle connection, or use very consistent pool
else:
    connect_args = {"server_settings": {"application_name": "isp_monitor_backend"}}

engine_kwargs = {
    "echo": False,
    "connect_args": connect_args,
    "poolclass": pool_class,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": 30
    })

try:
    engine = create_async_engine(
        settings.async_database_url,
        **engine_kwargs
    )
except Exception as e:
    logger.critical(f"Failed to create DB engine: {e}")
    raise

# SQLite Performance Tuning (WAL Mode)
if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        except Exception as e:
            logger.warning(f"Could not set SQLite PRAGMA: {e}")

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False # Performance boost for complex ops
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
