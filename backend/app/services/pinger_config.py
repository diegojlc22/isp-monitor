"""
Configurações centralizadas do Pinger Fast.
Todas as constantes e magic numbers em um só lugar.
"""
from typing import TypedDict, Literal


class PingerConfig:
    """Configurações do Pinger (Enterprise-tunable)."""
    
    # Cache
    CONFIG_CACHE_TTL = 5  # segundos - refresh de configurações
    
    # Smart Logging
    SMART_LOG_INTERVAL = 600  # 10min - log forçado mesmo sem mudanças
    LATENCY_CHANGE_THRESHOLD = 20  # ms - mudança significativa de latência
    LOG_BUFFER_SIZE = 100  # tamanho do buffer para bulk insert
    LOG_BUFFER_MAX_AGE = 60  # segundos - flush forçado por idade
    
    # Adaptive Concurrency
    CONCURRENCY_HISTORY_SIZE = 5  # ciclos para calcular média
    CONCURRENCY_SLOW_THRESHOLD = 40  # segundos - ciclo muito lento
    CONCURRENCY_FAST_THRESHOLD = 15  # segundos - ciclo muito rápido
    CONCURRENCY_MIN = 30  # limite mínimo de concorrência
    CONCURRENCY_MAX = 200  # limite máximo de concorrência
    CONCURRENCY_STEP = 20  # incremento/decremento
    
    # Dynamic Interval
    INTERVAL_CRITICAL = 15  # segundos - muitos dispositivos offline
    INTERVAL_UNSTABLE = 30  # segundos - mudanças recentes
    INTERVAL_STABLE = 60  # segundos - rede estável
    OFFLINE_CRITICAL_THRESHOLD = 5  # número de dispositivos offline
    STABLE_CYCLES_REQUIRED = 3  # ciclos estáveis para relaxar intervalo
    
    # Health Check
    HEALTH_CHECK_PORT = 9090  # porta do servidor HTTP
    HEALTH_CHECK_MAX_AGE = 120  # segundos - máximo sem ciclo (2x intervalo padrão)
    
    # Performance
    METRICS_LOG_INTERVAL = 10  # ciclos - log de métricas de performance


# Type Definitions
DeviceType = Literal["tower", "equipment"]


class ConfigCache(TypedDict):
    """Cache de configurações do sistema."""
    last_update: float
    token: str
    chat_id: str
    tmpl_down: str
    tmpl_up: str
    tg_enabled: bool
    wa_enabled: bool
    wa_target: str
    wa_target_group: str


class DeviceState(TypedDict):
    """Estado rastreado de um dispositivo."""
    last_log_time: float
    last_status: bool | None
    last_latency: int | None


class StabilityTracker(TypedDict):
    """Rastreamento de estabilidade da rede."""
    stable_cycles: int
    unstable_cycles: int
    offline_count: int
    current_interval: int


class ConcurrencyTracker(TypedDict):
    """Rastreamento de concorrência adaptativa."""
    current_limit: int
    cycle_times: list[float]
    avg_cycle_time: float
