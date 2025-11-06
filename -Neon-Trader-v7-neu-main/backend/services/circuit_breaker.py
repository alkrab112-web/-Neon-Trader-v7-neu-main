"""
Circuit Breaker for Risk Management
Automatically halts trading when risk thresholds are exceeded
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Trading halted
    HALF_OPEN = "half_open"  # Testing if safe to resume

class CircuitBreaker:
    """Circuit breaker for trading safety"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
        logger.info(f"Circuit Breaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("Circuit Breaker: Attempting reset to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Trading halted. "
                    f"Will retry after {self.recovery_timeout}s from last failure."
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("Circuit Breaker: Attempting reset to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Trading halted. "
                    f"Will retry after {self.recovery_timeout}s from last failure."
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit Breaker: Reset to CLOSED after successful test")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(
            f"Circuit Breaker: Failure #{self.failure_count} "
            f"(threshold: {self.failure_threshold})"
        )
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit Breaker: OPENED after {self.failure_count} failures. "
                f"Trading HALTED for {self.recovery_timeout}s"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    def reset(self):
        """Manually reset circuit breaker"""
        logger.info("Circuit Breaker: Manual reset")
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'time_until_retry': self._get_time_until_retry()
        }
    
    def _get_time_until_retry(self) -> Optional[int]:
        """Get seconds until retry attempt"""
        if self.state != CircuitState.OPEN or self.last_failure_time is None:
            return None
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        remaining = max(0, self.recovery_timeout - time_since_failure)
        return int(remaining)

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class TradingCircuitBreaker:
    """Specialized circuit breaker for trading operations"""
    
    def __init__(self):
        # Different breakers for different risk levels
        self.api_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        
        self.trade_execution_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=120
        )
        
        self.risk_threshold_breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=300  # 5 minutes
        )
        
        logger.info("Trading Circuit Breakers initialized")
    
    async def execute_trade(self, func: Callable, *args, **kwargs):
        """Execute trade with circuit breaker protection"""
        return await self.trade_execution_breaker.call_async(func, *args, **kwargs)
    
    async def api_call(self, func: Callable, *args, **kwargs):
        """Execute API call with circuit breaker protection"""
        return await self.api_breaker.call_async(func, *args, **kwargs)
    
    def check_risk_threshold(self, func: Callable, *args, **kwargs):
        """Check risk threshold with circuit breaker"""
        return self.risk_threshold_breaker.call(func, *args, **kwargs)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return {
            'api': self.api_breaker.get_status(),
            'trade_execution': self.trade_execution_breaker.get_status(),
            'risk_threshold': self.risk_threshold_breaker.get_status(),
            'any_open': any([
                self.api_breaker.state == CircuitState.OPEN,
                self.trade_execution_breaker.state == CircuitState.OPEN,
                self.risk_threshold_breaker.state == CircuitState.OPEN
            ])
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        self.api_breaker.reset()
        self.trade_execution_breaker.reset()
        self.risk_threshold_breaker.reset()
        logger.info("All circuit breakers reset")

# Global instance
trading_circuit_breaker = TradingCircuitBreaker()
