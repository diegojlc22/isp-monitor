"""
Health Check HTTP Server para monitoramento do Pinger.
Expõe endpoints /health e /metrics para observabilidade.
"""
import asyncio
import time
from aiohttp import web
import logging


class PingerHealthCheck:
    """
    Servidor HTTP para health checks e métricas.
    
    Endpoints:
        GET /health - Status de saúde do pinger
        GET /metrics - Métricas em formato Prometheus
    
    Attributes:
        last_cycle_time: Timestamp do último ciclo completo
        cycle_count: Número total de ciclos executados
        metrics: Métricas atuais do sistema
    """
    
    def __init__(self, max_cycle_age: int = 120):
        """
        Inicializa health check server.
        
        Args:
            max_cycle_age: Idade máxima do último ciclo em segundos
                          para considerar sistema saudável
        """
        self.last_cycle_time = time.time()
        self.cycle_count = 0
        self.metrics = {}
        self.max_cycle_age = max_cycle_age
        self.logger = logging.getLogger("pinger_health")
    
    async def handle_health(self, request):
        """
        Endpoint /health.
        
        Retorna:
            200 OK se sistema saudável
            503 Service Unavailable se não saudável
        """
        age = time.time() - self.last_cycle_time
        is_healthy = age < self.max_cycle_age
        
        status_code = 200 if is_healthy else 503
        
        response_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "last_cycle_age_seconds": round(age, 1),
            "cycle_count": self.cycle_count,
            "uptime_seconds": round(time.time() - self.metrics.get('start_time', time.time()), 1),
            "metrics": {
                "devices_total": self.metrics.get('devices_total', 0),
                "devices_online": self.metrics.get('devices_online', 0),
                "devices_offline": self.metrics.get('devices_offline', 0),
                "concurrency_limit": self.metrics.get('concurrency', 0),
                "ping_interval": self.metrics.get('interval', 0),
                "last_cycle_duration": self.metrics.get('last_cycle_duration', 0)
            }
        }
        
        return web.json_response(response_data, status=status_code)
    
    async def handle_metrics(self, request):
        """
        Endpoint /metrics (formato Prometheus).
        
        Retorna métricas em formato text/plain compatível com Prometheus.
        """
        lines = [
            "# HELP pinger_cycle_count Total number of monitoring cycles",
            "# TYPE pinger_cycle_count counter",
            f"pinger_cycle_count {self.cycle_count}",
            "",
            "# HELP pinger_last_cycle_age_seconds Time since last cycle completion",
            "# TYPE pinger_last_cycle_age_seconds gauge",
            f"pinger_last_cycle_age_seconds {time.time() - self.last_cycle_time:.1f}",
            "",
            "# HELP pinger_concurrency_limit Current concurrency limit",
            "# TYPE pinger_concurrency_limit gauge",
            f"pinger_concurrency_limit {self.metrics.get('concurrency', 0)}",
            "",
            "# HELP pinger_interval_seconds Current ping interval",
            "# TYPE pinger_interval_seconds gauge",
            f"pinger_interval_seconds {self.metrics.get('interval', 0)}",
            "",
            "# HELP pinger_devices_total Total number of devices",
            "# TYPE pinger_devices_total gauge",
            f"pinger_devices_total {self.metrics.get('devices_total', 0)}",
            "",
            "# HELP pinger_devices_online Number of online devices",
            "# TYPE pinger_devices_online gauge",
            f"pinger_devices_online {self.metrics.get('devices_online', 0)}",
            "",
            "# HELP pinger_devices_offline Number of offline devices",
            "# TYPE pinger_devices_offline gauge",
            f"pinger_devices_offline {self.metrics.get('devices_offline', 0)}",
            "",
            "# HELP pinger_last_cycle_duration_seconds Duration of last cycle",
            "# TYPE pinger_last_cycle_duration_seconds gauge",
            f"pinger_last_cycle_duration_seconds {self.metrics.get('last_cycle_duration', 0):.2f}",
        ]
        
        return web.Response(text="\n".join(lines) + "\n", content_type="text/plain")
    
    async def handle_root(self, request):
        """Endpoint / - Informações básicas."""
        return web.json_response({
            "service": "ISP Monitor - Pinger Fast",
            "version": "3.2",
            "endpoints": {
                "/health": "Health check endpoint",
                "/metrics": "Prometheus metrics"
            }
        })
    
    async def start_server(self, port: int = 9090):
        """
        Inicia servidor HTTP.
        
        Args:
            port: Porta para escutar (padrão: 9090)
        """
        app = web.Application()
        app.router.add_get('/', self.handle_root)
        app.router.add_get('/health', self.handle_health)
        app.router.add_get('/metrics', self.handle_metrics)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        try:
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            self.logger.info(f"Health check server started on port {port}")
        except OSError as e:
            self.logger.warning(f"Failed to start health check server on port {port}: {e}")
    
    def update_cycle(self, duration: float):
        """
        Atualiza informações do ciclo.
        
        Args:
            duration: Duração do ciclo em segundos
        """
        self.last_cycle_time = time.time()
        self.cycle_count += 1
        self.metrics['last_cycle_duration'] = duration
    
    def update_metrics(self, **kwargs):
        """
        Atualiza métricas do sistema.
        
        Args:
            **kwargs: Métricas a atualizar (devices_total, devices_offline, etc.)
        """
        self.metrics.update(kwargs)
