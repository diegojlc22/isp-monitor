"""
Utilitários para o Pinger Fast.
Funções auxiliares reutilizáveis.
"""
import ipaddress
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager
from collections import defaultdict
import time


def is_valid_ip(ip: str) -> bool:
    """
    Valida formato de endereço IP.
    
    Args:
        ip: String do endereço IP
        
    Returns:
        True se IP válido, False caso contrário
        
    Examples:
        >>> is_valid_ip("192.168.1.1")
        True
        >>> is_valid_ip("999.999.999.999")
        False
        >>> is_valid_ip("invalid")
        False
    """
    if not ip or not isinstance(ip, str):
        return False
    
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


class JSONFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON."""
    
    def format(self, record):
        """Formata log record como JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        
        # Adicionar dados extras se existirem
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class PerformanceMetrics:
    """
    Coleta e analisa métricas de performance do pinger.
    
    Attributes:
        timings: Histórico de tempos por seção
        counters: Contadores diversos
    """
    
    def __init__(self):
        """Inicializa métricas."""
        self.timings = defaultdict(list)
        self.counters = defaultdict(int)
        self._max_history = 100  # Manter últimos 100 valores
    
    @asynccontextmanager
    async def measure(self, section: str):
        """
        Context manager para medir tempo de execução.
        
        Args:
            section: Nome da seção sendo medida
            
        Usage:
            async with metrics.measure("database_query"):
                await session.execute(query)
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.timings[section].append(elapsed)
            
            # Limitar histórico
            if len(self.timings[section]) > self._max_history:
                self.timings[section].pop(0)
    
    def get_stats(self, section: str) -> dict:
        """
        Retorna estatísticas de uma seção.
        
        Args:
            section: Nome da seção
            
        Returns:
            Dict com avg, min, max, count ou vazio se sem dados
        """
        if not self.timings[section]:
            return {}
        
        values = self.timings[section]
        return {
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "count": len(values)
        }
    
    def increment(self, counter: str, value: int = 1):
        """
        Incrementa um contador.
        
        Args:
            counter: Nome do contador
            value: Valor a incrementar (padrão: 1)
        """
        self.counters[counter] += value
    
    def log_summary(self, logger: logging.Logger):
        """
        Loga sumário de métricas.
        
        Args:
            logger: Logger para output
        """
        if not self.timings:
            return
        
        metrics_data = {}
        for section in sorted(self.timings.keys()):
            stats = self.get_stats(section)
            if stats:
                metrics_data[section] = {
                    "avg_ms": round(stats['avg'] * 1000, 1),
                    "min_ms": round(stats['min'] * 1000, 1),
                    "max_ms": round(stats['max'] * 1000, 1),
                    "samples": stats['count']
                }
        
        logger.info("Performance metrics summary", extra={
            'extra_data': {
                'timings': metrics_data,
                'counters': dict(self.counters)
            }
        })


def setup_logger(name: str, level: str = "INFO", use_json: bool = True) -> logging.Logger:
    """
    Configura logger estruturado.
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        use_json: Se True, usa formato JSON, senão formato padrão
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remover handlers existentes
    logger.handlers.clear()
    
    handler = logging.StreamHandler()
    
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    logger.addHandler(handler)
    return logger
