from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
from typing import Optional, List
import os
import sys
from loguru import logger

# Criar diretorio de logs se nao existir
os.makedirs("logs", exist_ok=True)

# ConfigGlobal Loguru
logger.remove() # Remove default handler
logger.add(
    sys.stderr, 
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/backend.log", 
    rotation="10 MB", 
    retention="7 days", 
    level="DEBUG",
    compression="zip"
)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        case_sensitive=False
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./isp_monitor_v2.db"
    
    # Pool Settings (Tuned for SQLite/Postgres hybrid)
    db_pool_size: int = Field(20, ge=1)
    db_max_overflow: int = Field(10, ge=0)
    
    @computed_field
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        if url.startswith("sqlite://") and not "aiosqlite" in url:
             return url.replace("sqlite://", "sqlite+aiosqlite://")
        return url

    # --- Security ---
    secret_key: str = Field("your-secret-key-change-it", min_length=8)
    msg_secret: str = Field("msg-secret-key", min_length=4)
    access_token_expire_minutes: int = Field(1440, ge=1) # 24h
    admin_password: str = Field("110812")
    cors_origins: str = "*"

    @computed_field
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*": return ["*"]
        return self.cors_origins.split(",")

    # --- Pinger Core ---
    ping_interval_seconds: int = Field(30, ge=5)
    ping_timeout_seconds: float = Field(1.0, ge=0.1)
    ping_concurrent_limit: int = Field(300, ge=10, le=2000)
    log_retention_days: int = Field(30, ge=1)
    
    # --- Integration ---
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    whatsapp_api_url: str = "http://localhost:3001/send"
    whatsapp_target_number: Optional[str] = None

# Singleton Instance
settings = Settings()

# Compatibilidade para código legado que importa constantes diretamente
DATABASE_URL = settings.async_database_url
PING_INTERVAL_SECONDS = settings.ping_interval_seconds
PING_TIMEOUT_SECONDS = settings.ping_timeout_seconds
PING_CONCURRENT_LIMIT = settings.ping_concurrent_limit

logger.info(f"Config loaded: DB={settings.async_database_url.split('@')[-1] if '@' in settings.async_database_url else 'sqlite'}, PingInterval={settings.ping_interval_seconds}s")
