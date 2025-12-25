from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Check for DATABASE_URL env var, otherwise fallback to SQLite
# Example Postgres: postgresql+asyncpg://user:pass@localhost/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./monitor.db")

# Connection Args adjustments
connect_args = {}
# Note: aiosqlite doesn't need check_same_thread like sync sqlite

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args=connect_args,
    pool_size=20,              # Conexões permanentes no pool
    max_overflow=10,           # Conexões extras sob demanda
    pool_pre_ping=True,        # Testa conexão antes de usar (evita erros)
    pool_recycle=3600          # Recicla conexões a cada 1h (evita timeouts)
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Alias for compatibility if used elsewhere as AsyncSessionLocal
AsyncSessionLocal = async_session_factory

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session_factory() as session:
        yield session
