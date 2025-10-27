"""
Structured Logging Configuration for Neon Trader V7
Provides performance monitoring, request tracking, and error reporting
"""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PerformanceLogger:
    """Handles performance and request logging"""
    
    def __init__(self):
        self.logger = logging.getLogger("neon_trader.performance")
    
    def log_request(self, request_data: Dict[str, Any]):
        """Log request with structured JSON format"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "api_request",
            "path": request_data.get("path"),
            "method": request_data.get("method"),
            "user_id": request_data.get("user_id"),
            "status_code": request_data.get("status_code"),
            "latency_ms": request_data.get("latency_ms"),
            "user_agent": request_data.get("user_agent"),
            "ip_address": request_data.get("ip_address")
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_performance_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Log performance metrics"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "performance_metric",
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {}
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_error(self, error_data: Dict[str, Any]):
        """Log errors with context"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "error",
            "error_type": error_data.get("error_type"),
            "error_message": error_data.get("error_message"),
            "path": error_data.get("path"),
            "user_id": error_data.get("user_id"),
            "stack_trace": error_data.get("stack_trace")
        }
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for request monitoring"""
    
    def __init__(self, app, logger: PerformanceLogger):
        super().__init__(app)
        self.logger = logger
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Start timing
        start_time = time.time()
        
        # Extract user info from request (if authenticated)
        user_id = None
        try:
            # Try to get user from JWT token if present
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would need to be implemented with proper JWT decoding
                # For now, we'll leave it as None
                pass
        except:
            pass
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate latency
            process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log request
            request_data = {
                "path": str(request.url.path),
                "method": request.method,
                "user_id": user_id,
                "status_code": response.status_code,
                "latency_ms": round(process_time, 2),
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host if request.client else None
            }
            
            self.logger.log_request(request_data)
            
            # Add performance header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = (time.time() - start_time) * 1000
            error_data = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "path": str(request.url.path),
                "user_id": user_id,
                "latency_ms": round(process_time, 2)
            }
            
            self.logger.log_error(error_data)
            raise

class TradingMetrics:
    """Specific metrics for trading operations"""
    
    def __init__(self, logger: PerformanceLogger):
        self.logger = logger
    
    def log_trade_execution(self, execution_time_ms: float, platform: str, success: bool):
        """Log trade execution performance"""
        self.logger.log_performance_metric(
            "trade_execution_time",
            execution_time_ms,
            {"platform": platform, "success": str(success)}
        )
    
    def log_market_data_fetch(self, fetch_time_ms: float, source: str, symbol: str):
        """Log market data fetch performance"""
        self.logger.log_performance_metric(
            "market_data_fetch_time",
            fetch_time_ms,
            {"source": source, "symbol": symbol}
        )
    
    def log_ai_analysis(self, analysis_time_ms: float, analysis_type: str):
        """Log AI analysis performance"""
        self.logger.log_performance_metric(
            "ai_analysis_time",
            analysis_time_ms,
            {"type": analysis_type}
        )

# Global instances
performance_logger = PerformanceLogger()
trading_metrics = TradingMetrics(performance_logger)

# Health check logger
class HealthLogger:
    """Logs system health status"""
    
    def __init__(self):
        self.logger = logging.getLogger("neon_trader.health")
    
    def log_health_check(self, component: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Log health check results"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": component,
            "status": status,
            "details": details or {}
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))

health_logger = HealthLogger()

# Sentry Integration (optional)
def setup_sentry(dsn: Optional[str] = None):
    """Setup Sentry error tracking if DSN provided"""
    if dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            
            sentry_sdk.init(
                dsn=dsn,
                integrations=[FastApiIntegration()],
                traces_sample_rate=0.1,
            )
            logging.info("Sentry error tracking initialized")
        except ImportError:
            logging.warning("Sentry SDK not installed, skipping error tracking setup")
    else:
        logging.info("No Sentry DSN provided, skipping error tracking setup")