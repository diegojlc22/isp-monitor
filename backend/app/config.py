"""
Performance and Configuration Settings
"""
import os

# Ping Configuration
PING_INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL_SECONDS", "30"))  # Default 30s for production
PING_TIMEOUT_SECONDS = int(os.getenv("PING_TIMEOUT_SECONDS", "2"))
PING_CONCURRENT_LIMIT = int(os.getenv("PING_CONCURRENT_LIMIT", "100"))  # Max concurrent pings
USE_FPING = os.getenv("USE_FPING", "false").lower() == "true"  # Use fping if available

# Log Retention
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))  # Keep logs for 30 days

# Redis Cache (optional)
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))  # Cache dashboard for 60s
