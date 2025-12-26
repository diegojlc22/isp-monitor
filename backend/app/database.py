from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

# Load .env explicitamente
load_dotenv()

# Check for DATABASE_URL env var, otherwise fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./monitor.db")

# Ensure asyncpg driver is used for Postgres
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Debug: Mostrar URL mascarada
try:
    if DATABASE_URL and "://" in DATABASE_URL:
        masked_url = DATABASE_URL
        if "@" in masked_url:
            part1 = masked_url.split("@")[0] # protocol://user:pass
            if ":" in part1.split("://")[1]:
                user_part = part1.split("://")[1].split(":")[0]
                masked_url = f"{part1.split('://')[0]}://{user_part}:****@{masked_url.split('@')[1]}"
        print(f"[DATABASE] Conectando a: {masked_url}")
except:
    print("[DATABASE] Iniciando conexao...")

# Connection Args adjustments
connect_args = {}
# Note: aiosqlite doesn't need check_same_thread like sync sqlite

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args=connect_args,
    pool_size=20,              # Conexões permanentes no pool
    max_overflow=10,           # Conexões extras sob demanda
    pool_pre_ping=False,       # DESATIVADO TEMPORARIAMENTE para evitar erro de startup no Windows
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
