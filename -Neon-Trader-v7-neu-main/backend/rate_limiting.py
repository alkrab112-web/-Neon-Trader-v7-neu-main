"""
Rate Limiting Configuration for Neon Trader V7
Protects trading endpoints from abuse
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import redis
import os

# Try to use Redis, fall back to in-memory storage
try:
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    # For now, use in-memory storage
    limiter = Limiter(key_func=get_remote_address)
except:
    # Fallback to in-memory storage
    limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    'trading': "5/minute",      # 5 trades per minute
    'auth': "10/minute",        # 10 auth attempts per minute  
    'market_data': "60/minute", # 60 market data requests per minute
    'ai_analysis': "20/minute", # 20 AI requests per minute
    'general': "100/minute"     # 100 general requests per minute
}

def get_user_id_from_request(request: Request):
    """Extract user ID from JWT token for user-specific rate limiting"""
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # This would extract user ID from JWT - simplified for now
            return get_remote_address(request)
    except:
        pass
    return get_remote_address(request)

# Create user-specific limiter
user_limiter = Limiter(key_func=get_user_id_from_request)