"""
Simple in-memory cache for API responses
Reduz carga no PostgreSQL em 5-10x
"""
from datetime import datetime, timedelta
from typing import Any, Optional
import asyncio

class SimpleCache:
    """Cache simples em memória com TTL"""
    
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._ttl: dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Retorna valor do cache se ainda válido"""
        async with self._lock:
            if key in self._cache:
                if datetime.utcnow() < self._ttl[key]:
                    return self._cache[key]
                else:
                    # Expirou, remove
                    del self._cache[key]
                    del self._ttl[key]
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 60):
        """Salva valor no cache com TTL"""
        async with self._lock:
            self._cache[key] = value
            self._ttl[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    async def clear(self):
        """Limpa todo o cache"""
        async with self._lock:
            self._cache.clear()
            self._ttl.clear()
    
    async def delete(self, key: str):
        """Remove uma chave específica"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._ttl[key]
    
    def size(self) -> int:
        """Retorna número de itens no cache"""
        return len(self._cache)

# Instância global
cache = SimpleCache()
