#!/usr/bin/env python3
"""
Comprehensive Test Script for Neon Trader V7
Tests all major features and integrations
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Test Results
test_results = {
    'passed': [],
    'failed': [],
    'skipped': []
}

def log_test(name: str, status: str, message: str = ""):
    """Log test result"""
    emoji = {
        'passed': '✅',
        'failed': '❌',
        'skipped': '⏭️'
    }.get(status, '❓')
    
    logger.info(f"{emoji} {name}: {message}")
    test_results[status].append(name)

async def test_database_connection():
    """Test PostgreSQL connection"""
    try:
        from database import check_db_health
        
        is_healthy = await check_db_health()
        if is_healthy:
            log_test("Database Connection", "passed", "PostgreSQL connected")
        else:
            log_test("Database Connection", "failed", "Cannot connect to PostgreSQL")
    except Exception as e:
        log_test("Database Connection", "failed", str(e))

async def test_database_models():
    """Test SQLAlchemy models"""
    try:
        from models.database_models import User, Portfolio, Trade, Platform
        
        # Check if models are properly defined
        assert hasattr(User, '__tablename__')
        assert hasattr(Portfolio, '__tablename__')
        assert hasattr(Trade, '__tablename__')
        assert hasattr(Platform, '__tablename__')
        
        log_test("Database Models", "passed", "All models defined correctly")
    except Exception as e:
        log_test("Database Models", "failed", str(e))

async def test_exchange_adapters():
    """Test Exchange Adapters"""
    try:
        from services.exchange_adapters import BinanceAdapter, BybitAdapter, OKXAdapter
        
        # Check if adapters can be instantiated
        binance = BinanceAdapter("test_key", "test_secret", testnet=True)
        bybit = BybitAdapter("test_key", "test_secret", testnet=True)
        okx = OKXAdapter("test_key", "test_secret", "test_pass", testnet=True)
        
        assert binance is not None
        assert bybit is not None
        assert okx is not None
        
        log_test("Exchange Adapters", "passed", "Binance, Bybit, OKX adapters ready")
    except Exception as e:
        log_test("Exchange Adapters", "failed", str(e))

async def test_deepseek_ai():
    """Test DeepSeek AI Integration"""
    try:
        import os
        from services.ai.deepseek_integration import DeepSeekAI
        
        deepseek = DeepSeekAI()
        
        if not deepseek.api_key:
            log_test("DeepSeek AI", "skipped", "No API key configured")
        else:
            # Test simple generation
            result = await deepseek.generate_text(
                prompt="What is 2+2?",
                max_tokens=50
            )
            
            if result.get('success'):
                log_test("DeepSeek AI", "passed", "AI generation working")
            else:
                log_test("DeepSeek AI", "failed", result.get('error', 'Unknown error'))
    except Exception as e:
        log_test("DeepSeek AI", "failed", str(e))

async def test_circuit_breaker():
    """Test Circuit Breaker"""
    try:
        from services.circuit_breaker import CircuitBreaker, trading_circuit_breaker
        
        # Test basic circuit breaker
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Simulate failures
        def failing_func():
            raise Exception("Test failure")
        
        failures = 0
        for _ in range(3):
            try:
                breaker.call(failing_func)
            except:
                failures += 1
        
        # Check if circuit opened
        status = breaker.get_status()
        if status['state'] == 'open':
            log_test("Circuit Breaker", "passed", "Circuit opens after threshold")
        else:
            log_test("Circuit Breaker", "failed", "Circuit didn't open")
            
    except Exception as e:
        log_test("Circuit Breaker", "failed", str(e))

async def test_prometheus_metrics():
    """Test Prometheus Metrics"""
    try:
        from services.prometheus_metrics import (
            http_requests_total, 
            trades_total,
            market_data_fetches,
            ai_predictions_total
        )
        
        # Test metric increments
        http_requests_total.labels(method="GET", endpoint="/test", status=200).inc()
        trades_total.labels(trade_type="buy", status="executed", platform="test").inc()
        
        log_test("Prometheus Metrics", "passed", "Metrics system working")
    except Exception as e:
        log_test("Prometheus Metrics", "failed", str(e))

async def test_security_vault():
    """Test Security Vault (Encryption)"""
    try:
        import os
        from models.vault import SecurityVault
        
        # Check if Fernet key is configured
        if not os.environ.get('FERNET_KEY'):
            log_test("Security Vault", "skipped", "No Fernet key configured")
        else:
            vault = SecurityVault()
            
            # Test encryption/decryption
            test_data = "sensitive_api_key_12345"
            encrypted = vault.encrypt_data(test_data)
            decrypted = vault.decrypt_data(encrypted)
            
            if decrypted == test_data:
                log_test("Security Vault", "passed", "Encryption/Decryption working")
            else:
                log_test("Security Vault", "failed", "Decryption mismatch")
                
    except Exception as e:
        log_test("Security Vault", "failed", str(e))

async def test_market_data_service():
    """Test Market Data Service"""
    try:
        from services.exchange_service import market_data_service
        
        # Test market data fetch
        result = await market_data_service.get_market_price_with_fallback("BTCUSDT")
        
        if result and result.get('price', 0) > 0:
            log_test("Market Data Service", "passed", f"BTC Price: ${result['price']:.2f}")
        else:
            log_test("Market Data Service", "failed", "No price data")
            
    except Exception as e:
        log_test("Market Data Service", "failed", str(e))

async def test_two_factor_auth():
    """Test Two-Factor Authentication"""
    try:
        from services.two_factor_auth import TwoFactorAuthService
        
        # Generate secret and test token
        secret = TwoFactorAuthService.generate_secret_key()
        
        # Generate token
        import pyotp
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        # Verify token
        is_valid = TwoFactorAuthService.verify_token(secret, token)
        
        if is_valid:
            log_test("Two-Factor Auth", "passed", "TOTP generation and verification working")
        else:
            log_test("Two-Factor Auth", "failed", "Token verification failed")
            
    except Exception as e:
        log_test("Two-Factor Auth", "failed", str(e))

async def test_jwt_authentication():
    """Test JWT Authentication"""
    try:
        from jose import jwt
        import os
        
        JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'test_secret')
        
        # Create token
        payload = {"sub": "test_user", "exp": datetime.utcnow().timestamp() + 3600}
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        # Decode token
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if decoded['sub'] == 'test_user':
            log_test("JWT Authentication", "passed", "Token creation and verification working")
        else:
            log_test("JWT Authentication", "failed", "Token mismatch")
            
    except Exception as e:
        log_test("JWT Authentication", "failed", str(e))

async def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("🧪 Neon Trader V7 - Comprehensive Test Suite")
    logger.info("=" * 60)
    logger.info("")
    
    # Run tests
    await test_database_connection()
    await test_database_models()
    await test_exchange_adapters()
    await test_deepseek_ai()
    await test_circuit_breaker()
    await test_prometheus_metrics()
    await test_security_vault()
    await test_market_data_service()
    await test_two_factor_auth()
    await test_jwt_authentication()
    
    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 60)
    logger.info(f"✅ Passed:  {len(test_results['passed'])}")
    logger.info(f"❌ Failed:  {len(test_results['failed'])}")
    logger.info(f"⏭️  Skipped: {len(test_results['skipped'])}")
    logger.info("")
    
    if test_results['failed']:
        logger.info("❌ Failed Tests:")
        for test in test_results['failed']:
            logger.info(f"   - {test}")
        logger.info("")
    
    if test_results['skipped']:
        logger.info("⏭️  Skipped Tests:")
        for test in test_results['skipped']:
            logger.info(f"   - {test}")
        logger.info("")
    
    total_tests = len(test_results['passed']) + len(test_results['failed'])
    if total_tests > 0:
        success_rate = (len(test_results['passed']) / total_tests) * 100
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
    
    logger.info("=" * 60)
    
    # Exit code
    return 0 if not test_results['failed'] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
