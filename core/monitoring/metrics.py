from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import logging

logger = logging.getLogger(__name__)

# Define metrics
ANALYSIS_REQUESTS = Counter('trading_analysis_requests_total', 'Total number of analysis requests', ['status'])
ANALYSIS_DURATION = Histogram('trading_analysis_duration_seconds', 'Time spent processing analysis requests')
ACTIVE_ANALYSES = Gauge('trading_active_analyses', 'Number of currently active analyses')
TOOL_CALLS = Counter('trading_tool_calls_total', 'Total number of tool calls', ['tool_name'])
MEMORY_OPERATIONS = Counter('trading_memory_operations_total', 'Total memory operations', ['operation'])

class MetricsCollector:
    def __init__(self, port: int = 8001):
        self.port = port
        
    def start_server(self):
        """Start Prometheus metrics server."""
        try:
            start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    def record_analysis_request(self, status: str):
        """Record an analysis request."""
        ANALYSIS_REQUESTS.labels(status=status).inc()
    
    def record_analysis_duration(self, duration: float):
        """Record analysis duration."""
        ANALYSIS_DURATION.observe(duration)
    
    def set_active_analyses(self, count: int):
        """Set the number of active analyses."""
        ACTIVE_ANALYSES.set(count)
    
    def record_tool_call(self, tool_name: str):
        """Record a tool call."""
        TOOL_CALLS.labels(tool_name=tool_name).inc()
    
    def record_memory_operation(self, operation: str):
        """Record a memory operation."""
        MEMORY_OPERATIONS.labels(operation=operation).inc()

# Global metrics collector
metrics = MetricsCollector()

def track_analysis_time(func):
    """Decorator to track analysis execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.record_analysis_duration(duration)
            metrics.record_analysis_request("success")
            return result
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_analysis_duration(duration)
            metrics.record_analysis_request("error")
            raise e
    return wrapper