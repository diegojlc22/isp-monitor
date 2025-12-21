from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Check for DATABASE_URL env var, otherwise fallback to SQLite
# Example Postgres: postgresql+asyncpg://user:pass@localhost/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./monitor.db")

# Connection Args adjustments
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False} 

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)

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
