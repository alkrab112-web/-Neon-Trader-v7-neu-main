"""
Prometheus Metrics for Monitoring
Provides comprehensive metrics for system monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
import logging

logger = logging.getLogger(__name__)

# Application Info
app_info = Info('neontrader_app', 'Neon Trader V7 Application Info')
app_info.info({
    'version': '7.0.0',
    'environment': 'production'
})

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Trading Metrics
trades_total = Counter(
    'trades_total',
    'Total trades executed',
    ['trade_type', 'status', 'platform']
)

trade_execution_duration = Histogram(
    'trade_execution_duration_seconds',
    'Trade execution duration',
    ['platform']
)

trade_pnl = Histogram(
    'trade_pnl',
    'Trade profit and loss',
    ['symbol', 'trade_type']
)

# Market Data Metrics
market_data_fetches = Counter(
    'market_data_fetches_total',
    'Total market data fetch operations',
    ['source', 'status']
)

market_data_latency = Histogram(
    'market_data_latency_seconds',
    'Market data fetch latency',
    ['source']
)

# AI/ML Metrics
ai_predictions_total = Counter(
    'ai_predictions_total',
    'Total AI predictions made',
    ['model', 'prediction_type']
)

ai_prediction_latency = Histogram(
    'ai_prediction_latency_seconds',
    'AI prediction latency',
    ['model']
)

ai_prediction_confidence = Histogram(
    'ai_prediction_confidence',
    'AI prediction confidence score',
    ['model']
)

# Database Metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation']
)

db_errors = Counter(
    'db_errors_total',
    'Database errors',
    ['operation', 'error_type']
)

# Exchange Integration Metrics
exchange_api_calls = Counter(
    'exchange_api_calls_total',
    'Exchange API calls',
    ['exchange', 'endpoint', 'status']
)

exchange_api_latency = Histogram(
    'exchange_api_latency_seconds',
    'Exchange API latency',
    ['exchange']
)

exchange_connection_status = Gauge(
    'exchange_connection_status',
    'Exchange connection status (1=connected, 0=disconnected)',
    ['exchange']
)

# User Metrics
active_users = Gauge(
    'active_users',
    'Currently active users'
)

user_registrations = Counter(
    'user_registrations_total',
    'Total user registrations'
)

user_logins = Counter(
    'user_logins_total',
    'Total user logins',
    ['status']
)

# Portfolio Metrics
portfolio_total_value = Gauge(
    'portfolio_total_value',
    'Total portfolio value across all users'
)

portfolio_pnl = Histogram(
    'portfolio_pnl',
    'Portfolio profit and loss',
    ['user_id']
)

# Risk Management Metrics
risk_threshold_breaches = Counter(
    'risk_threshold_breaches_total',
    'Risk threshold breaches',
    ['threshold_type']
)

circuit_breaker_trips = Counter(
    'circuit_breaker_trips_total',
    'Circuit breaker activations',
    ['breaker_type']
)

# System Metrics
system_errors = Counter(
    'system_errors_total',
    'System errors',
    ['error_type', 'severity']
)

background_tasks_active = Gauge(
    'background_tasks_active',
    'Active background tasks',
    ['task_type']
)

# WebSocket Metrics
websocket_connections = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

websocket_messages = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['direction', 'message_type']
)

# Helper class for timing operations
class MetricsTimer:
    """Context manager for timing operations"""
    
    def __init__(self, histogram, *labels):
        self.histogram = histogram
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if self.labels:
            self.histogram.labels(*self.labels).observe(duration)
        else:
            self.histogram.observe(duration)

# Metrics endpoint
def get_metrics():
    """Get Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Utility functions
def track_http_request(method: str, endpoint: str, status: int):
    """Track HTTP request"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()

def track_trade(trade_type: str, status: str, platform: str, pnl: float = None):
    """Track trade execution"""
    trades_total.labels(trade_type=trade_type, status=status, platform=platform).inc()
    if pnl is not None:
        trade_pnl.labels(symbol="all", trade_type=trade_type).observe(pnl)

def track_market_data_fetch(source: str, status: str, latency: float):
    """Track market data fetch"""
    market_data_fetches.labels(source=source, status=status).inc()
    market_data_latency.labels(source=source).observe(latency)

def track_ai_prediction(model: str, prediction_type: str, confidence: float, latency: float):
    """Track AI prediction"""
    ai_predictions_total.labels(model=model, prediction_type=prediction_type).inc()
    ai_prediction_confidence.labels(model=model).observe(confidence)
    ai_prediction_latency.labels(model=model).observe(latency)

def track_error(error_type: str, severity: str = "error"):
    """Track system error"""
    system_errors.labels(error_type=error_type, severity=severity).inc()

logger.info("Prometheus metrics initialized")
