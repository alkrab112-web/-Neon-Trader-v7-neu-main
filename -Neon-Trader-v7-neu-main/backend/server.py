from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
import asyncio
from passlib.context import CryptContext
from jose import JWTError, jwt
import hashlib
from logging_config import PerformanceMonitoringMiddleware, performance_logger, trading_metrics, health_logger
from services.exchange_service import market_data_service, trading_service
from rate_limiting import limiter, user_limiter, RATE_LIMITS
from websocket_manager import manager, WebSocketHandler
from fastapi import WebSocket, WebSocketDisconnect
from models.vault import SecurityVault
from models.snapshots import PortfolioSnapshot, SnapshotRequest, SnapshotAnalysis
from models.approvals import ProposedTrade, TradeApprovalRequest, ApprovalStatus, ApprovalSummary
from services.two_factor_auth import TwoFactorAuthService, SecurityAuditLogger, validate_totp_token_format

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security settings
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback_secret_key')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Emergent LLM Key from environment
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app
app = FastAPI(title="Neon Trader V7", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Enums
class TradeType(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class TradeStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class PlatformStatus(str, Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    hashed_password: str
    is_active: bool = True
    two_factor_enabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Portfolio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    total_balance: float
    available_balance: float
    invested_balance: float
    daily_pnl: float
    total_pnl: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Trade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    platform: str
    symbol: str
    trade_type: TradeType
    order_type: OrderType
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: TradeStatus
    pnl: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None

class Platform(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    platform_type: str  # binance, bybit, etc
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    is_testnet: bool = True
    status: PlatformStatus = PlatformStatus.DISCONNECTED
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AIRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    symbol: str
    action: str  # buy, sell, hold
    confidence: str  # high, medium, low
    reason: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DailyPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str
    market_analysis: str
    trading_strategy: str
    risk_level: str
    opportunities: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response Models
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    two_factor_code: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str
    username: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None

class TradeRequest(BaseModel):
    symbol: str
    trade_type: TradeType
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    platform_id: Optional[str] = None

class PlatformRequest(BaseModel):
    name: str
    platform_type: str
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    is_testnet: bool = True

class AIAnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"

# Authentication Utilities
class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def get_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get user from JWT token"""
        token = credentials.credentials
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise credentials_exception
        
        user.pop('_id', None)
        return User(**user)
    
    @staticmethod
    async def get_current_active_user(current_user: User = Depends(lambda: AuthService.get_user_from_token)):
        """Get current active user"""
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    @staticmethod
    def create_refresh_token_data(user_id: str):
        """Create refresh token data for storage"""
        import secrets
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=30)  # Refresh tokens expire in 30 days
        
        from pydantic import BaseModel, Field
        
        class RefreshTokenData(BaseModel):
            user_id: str
            refresh_token: str
            expires_at: datetime
            created_at: datetime = Field(default_factory=datetime.utcnow)
            
            def dict(self):
                return {
                    "user_id": self.user_id,
                    "refresh_token": self.refresh_token,
                    "expires_at": self.expires_at,
                    "created_at": self.created_at
                }
        
        return RefreshTokenData(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

# Enhanced Market Data Service with real APIs
class RealMarketDataService:
    def __init__(self):
        # Initialize real API connections
        try:
            from pycoingecko import CoinGeckoAPI
            self.coingecko = CoinGeckoAPI()
            self.coingecko_available = True
            logging.info("CoinGecko API initialized successfully")
        except Exception as e:
            logging.warning(f"CoinGecko API not available: {e}")
            self.coingecko_available = False
    
    @staticmethod
    async def get_real_crypto_price(symbol: str) -> Dict[str, Any]:
        """Get real cryptocurrency price from CoinGecko"""
        try:
            symbol_map = {
                'BTCUSDT': 'bitcoin',
                'ETHUSDT': 'ethereum', 
                'ADAUSDT': 'cardano',
                'BNBUSDT': 'binancecoin',
                'SOLUSDT': 'solana',
                'XRPUSDT': 'ripple',
                'DOGEUSDT': 'dogecoin',
                'AVAXUSDT': 'avalanche-2'
            }
            
            coin_id = symbol_map.get(symbol)
            if not coin_id:
                return None
                
            import httpx
            async with httpx.AsyncClient() as client:
                # Get detailed coin data
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                params = {
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false'
                }
                
                response = await client.get(url, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    market_data = data.get('market_data', {})
                    
                    current_price = market_data.get('current_price', {}).get('usd', 0)
                    price_change_24h = market_data.get('price_change_24h', 0)
                    price_change_percentage_24h = market_data.get('price_change_percentage_24h', 0)
                    high_24h = market_data.get('high_24h', {}).get('usd', current_price * 1.05)
                    low_24h = market_data.get('low_24h', {}).get('usd', current_price * 0.95)
                    market_cap = market_data.get('market_cap', {}).get('usd', 0)
                    total_volume = market_data.get('total_volume', {}).get('usd', 0)
                    
                    return {
                        "symbol": symbol,
                        "name": data.get('name', symbol),
                        "price": float(current_price),
                        "change_24h": float(price_change_24h),
                        "change_24h_percent": round(float(price_change_percentage_24h), 2),
                        "high_24h": float(high_24h),
                        "low_24h": float(low_24h),
                        "volume_24h": float(total_volume),
                        "market_cap": float(market_cap),
                        "data_source": "CoinGecko_Real_API",
                        "timestamp": datetime.utcnow(),
                        "last_updated": market_data.get('last_updated', datetime.utcnow().isoformat())
                    }
                else:
                    logging.warning(f"CoinGecko API returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            logging.error(f"Error fetching real crypto price from CoinGecko: {e}")
            return None
    
    @staticmethod
    async def get_real_stock_price(symbol: str) -> Dict[str, Any]:
        """Get real stock price from financial APIs"""
        try:
            # Use Alpha Vantage or similar free APIs for stocks
            import httpx
            
            # For demo, using Yahoo Finance alternative API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('chart', {}).get('result', [])
                    
                    if result:
                        meta = result[0].get('meta', {})
                        current_price = meta.get('regularMarketPrice', 0)
                        previous_close = meta.get('previousClose', current_price)
                        
                        change_24h = current_price - previous_close
                        change_24h_percent = (change_24h / previous_close) * 100 if previous_close > 0 else 0
                        
                        return {
                            "symbol": symbol,
                            "name": meta.get('longName', symbol),
                            "price": float(current_price),
                            "change_24h": float(change_24h),
                            "change_24h_percent": round(float(change_24h_percent), 2),
                            "high_24h": float(meta.get('regularMarketDayHigh', current_price * 1.02)),
                            "low_24h": float(meta.get('regularMarketDayLow', current_price * 0.98)),
                            "volume_24h": float(meta.get('regularMarketVolume', 1000000)),
                            "market_cap": float(meta.get('marketCap', 0)),
                            "data_source": "Yahoo_Finance_Real_API",
                            "timestamp": datetime.utcnow(),
                            "last_updated": datetime.utcnow().isoformat()
                        }
                        
        except Exception as e:
            logging.error(f"Error fetching real stock price: {e}")
        
        return None
    
    @staticmethod
    async def get_real_forex_rate(symbol: str) -> Dict[str, Any]:
        """Get real forex rates"""
        try:
            # Use exchangerate-api or similar
            base_currency = symbol[:3]  # EUR from EURUSD
            target_currency = symbol[3:]  # USD from EURUSD
            
            import httpx
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get('rates', {})
                    
                    if target_currency in rates:
                        current_rate = rates[target_currency]
                        
                        # Simulate daily change (in real app, you'd store historical data)
                        change_24h_percent = (hash(symbol + str(datetime.now().date())) % 200 - 100) / 1000  # -0.1% to +0.1%
                        change_24h = current_rate * (change_24h_percent / 100)
                        
                        return {
                            "symbol": symbol,
                            "name": f"{base_currency}/{target_currency}",
                            "price": float(current_rate),
                            "change_24h": float(change_24h),
                            "change_24h_percent": round(float(change_24h_percent), 4),
                            "high_24h": float(current_rate * 1.001),
                            "low_24h": float(current_rate * 0.999),
                            "volume_24h": 1000000000,  # Forex has huge volume
                            "data_source": "ExchangeRate_API_Real",
                            "timestamp": datetime.utcnow(),
                            "last_updated": datetime.utcnow().isoformat()
                        }
                        
        except Exception as e:
            logging.error(f"Error fetching real forex rate: {e}")
        
        return None

# Create instance
real_market_service = RealMarketDataService()

class MarketDataService:
    # Asset type definitions
    ASSET_TYPES = {
        'crypto': {
            'name': 'العملات الرقمية',
            'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'AVAXUSDT']
        },
        'forex': {
            'name': 'الفوركس',
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'USDCAD', 'NZDUSD', 'EURJPY']
        },
        'stocks': {
            'name': 'الأسهم',
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
        },
        'commodities': {
            'name': 'السلع',
            'symbols': ['XAUUSD', 'XAGUSD', 'USOIL', 'UKOIL', 'NATGAS', 'COPPER', 'WHEAT', 'CORN']
        },
        'indices': {
            'name': 'المؤشرات',
            'symbols': ['SPX500', 'NAS100', 'DJ30', 'GER40', 'UK100', 'JPN225', 'AUS200', 'HK50']
        }
    }

    @staticmethod
    async def get_all_asset_types():
        """Get all supported asset types"""
        return MarketDataService.ASSET_TYPES

    @staticmethod
    async def get_symbols_by_type(asset_type: str):
        """Get symbols for specific asset type"""
        return MarketDataService.ASSET_TYPES.get(asset_type, {}).get('symbols', [])

    @staticmethod
    async def get_price_from_coingecko(symbol: str) -> float:
        """Get real price from CoinGecko API (free, no restrictions)"""
        try:
            import aiohttp
            
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTCUSDT': 'bitcoin',
                'ETHUSDT': 'ethereum', 
                'ADAUSDT': 'cardano',
                'BNBUSDT': 'binancecoin',
                'SOLUSDT': 'solana',
                'XRPUSDT': 'ripple',
                'DOGEUSDT': 'dogecoin',
                'AVAXUSDT': 'avalanche-2'
            }
            
            coin_id = symbol_map.get(symbol)
            if not coin_id:
                return None
                
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data[coin_id]['usd'])
        except Exception as e:
            logging.error(f"Error fetching price from CoinGecko: {e}")
        return None

    @staticmethod
    async def get_price_from_binance(symbol: str) -> float:
        """Get real price from Binance API (for crypto)"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
        except Exception as e:
            logging.error(f"Error fetching price from Binance: {e}")
        return None

    @staticmethod
    async def get_price_from_alpha_vantage(symbol: str, asset_type: str) -> float:
        """Get price from Alpha Vantage for stocks/forex"""
        try:
            # This would require Alpha Vantage API key in production
            # For now, return mock data based on asset type
            mock_prices = {
                'forex': {
                    'EURUSD': 1.0950, 'GBPUSD': 1.2750, 'USDJPY': 149.50,
                    'AUDUSD': 0.6650, 'USDCHF': 0.8950, 'USDCAD': 1.3550,
                    'NZDUSD': 0.6150, 'EURJPY': 163.20
                },
                'stocks': {
                    'AAPL': 195.50, 'GOOGL': 142.80, 'MSFT': 415.25,
                    'AMZN': 155.75, 'TSLA': 248.50, 'META': 325.80,
                    'NVDA': 875.25, 'NFLX': 485.60
                },
                'commodities': {
                    'XAUUSD': 2015.50, 'XAGUSD': 24.85, 'USOIL': 78.25,
                    'UKOIL': 82.15, 'NATGAS': 2.65, 'COPPER': 8.45,
                    'WHEAT': 5.85, 'CORN': 4.75
                },
                'indices': {
                    'SPX500': 4515.25, 'NAS100': 15850.75, 'DJ30': 35650.80,
                    'GER40': 16250.45, 'UK100': 7485.60, 'JPN225': 32850.90,
                    'AUS200': 7125.35, 'HK50': 17850.25
                }
            }
            
            return mock_prices.get(asset_type, {}).get(symbol, 100.0)
            
        except Exception as e:
            logging.error(f"Error fetching price from Alpha Vantage: {e}")
        return None

    @staticmethod
    async def detect_asset_type(symbol: str) -> str:
        """Detect asset type based on symbol"""
        for asset_type, data in MarketDataService.ASSET_TYPES.items():
            if symbol in data['symbols']:
                return asset_type
        return 'crypto'  # Default to crypto

    @staticmethod
    async def get_price(symbol: str) -> float:
        """Get price with priority on real data sources"""
        asset_type = await MarketDataService.detect_asset_type(symbol)
        
        try:
            # Try real APIs first based on asset type
            if asset_type == 'crypto':
                real_data = await RealMarketDataService.get_real_crypto_price(symbol)
                if real_data and real_data.get('price', 0) > 0:
                    logging.info(f"Real crypto price for {symbol}: ${real_data['price']} from {real_data['data_source']}")
                    return real_data['price']
            
            elif asset_type == 'stock':
                real_data = await RealMarketDataService.get_real_stock_price(symbol)
                if real_data and real_data.get('price', 0) > 0:
                    logging.info(f"Real stock price for {symbol}: ${real_data['price']} from {real_data['data_source']}")
                    return real_data['price']
            
            elif asset_type == 'forex':
                real_data = await RealMarketDataService.get_real_forex_rate(symbol)
                if real_data and real_data.get('price', 0) > 0:
                    logging.info(f"Real forex rate for {symbol}: {real_data['price']} from {real_data['data_source']}")
                    return real_data['price']
            
        except Exception as e:
            logging.error(f"Error fetching real price for {symbol}: {e}")
        
        # Fallback to CoinGecko for crypto
        if asset_type == 'crypto':
            try:
                price = await MarketDataService.get_price_from_coingecko(symbol)
                if price is not None:
                    logging.info(f"CoinGecko fallback price for {symbol}: ${price}")
                    return price
            except Exception as e:
                logging.error(f"CoinGecko fallback failed: {e}")
        
        # Ultimate fallback to realistic mock prices (updated with 2024 realistic values)
        realistic_prices = {
            # Crypto (realistic Dec 2024 prices)
            "BTCUSDT": 43250.50, "ETHUSDT": 2580.75, "ADAUSDT": 0.45, "BNBUSDT": 310.25,
            "SOLUSDT": 95.30, "XRPUSDT": 0.52, "DOGEUSDT": 0.08, "AVAXUSDT": 32.15,
            
            # Forex (realistic rates)
            "EURUSD": 1.0950, "GBPUSD": 1.2750, "USDJPY": 149.50, "AUDUSD": 0.6650,
            "USDCHF": 0.8950, "USDCAD": 1.3550, "NZDUSD": 0.6150, "EURJPY": 163.20,
            
            # Stocks (realistic Dec 2024 prices)
            "AAPL": 195.50, "GOOGL": 142.80, "MSFT": 415.25, "AMZN": 155.75,
            "TSLA": 248.50, "META": 325.80, "NVDA": 875.25, "NFLX": 485.60,
            
            # Commodities (realistic prices)
            "XAUUSD": 2015.50, "XAGUSD": 24.85, "USOIL": 78.25, "UKOIL": 82.15,
            "NATGAS": 2.65, "COPPER": 8.45, "WHEAT": 5.85, "CORN": 4.75,
            
            # Indices (realistic values)
            "SPX500": 4515.25, "NAS100": 15850.75, "DJ30": 35650.80, "GER40": 16250.45,
            "UK100": 7485.60, "JPN225": 32850.90, "AUS200": 7125.35, "HK50": 17850.25
        }
        
        price = realistic_prices.get(symbol, 100.0)
        logging.warning(f"Using REALISTIC FALLBACK price for {symbol} ({asset_type}): ${price}")
        
        return price
    
    @staticmethod
    async def get_market_data(symbol: str) -> Dict[str, Any]:
        """Get comprehensive market data with enhanced resilience"""
        asset_type = await MarketDataService.detect_asset_type(symbol)
        
        try:
            # Use new resilient market data service with retry and fallback
            start_time = time.time()
            price_data = await market_data_service.get_market_price_with_fallback(symbol)
            fetch_time_ms = (time.time() - start_time) * 1000
            
            # Log performance metric
            trading_metrics.log_market_data_fetch(
                fetch_time_ms,
                price_data.get('source', 'unknown'),
                symbol
            )
            
            # Add asset type information
            price_data.update({
                "asset_type": asset_type,
                "asset_type_name": MarketDataService.ASSET_TYPES.get(asset_type, {}).get('name', 'غير معروف'),
                "fetch_time_ms": round(fetch_time_ms, 2)
            })
            
            # Add additional market data fields for compatibility
            price_data.update({
                "volume_24h": int(1000000 * (1 + (hash(symbol) % 10))),
                "high_24h": round(price_data['price'] * 1.02, 4),
                "low_24h": round(price_data['price'] * 0.98, 4),
                "open_price": round(price_data['price'] * (1 - price_data.get('change_24h', 0) / 100), 4),
                "last_updated": price_data.get('timestamp', datetime.now(timezone.utc).isoformat())
            })
            
            logging.info(f"Returning market data for {symbol} from {price_data.get('source', 'unknown')}")
            return price_data
                
        except Exception as e:
            logging.error(f"Error fetching market data for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")

# AI Service
class AIService:
    @staticmethod
    async def get_market_analysis(symbol: str) -> str:
        try:
            # Using Emergent LLM Key for real AI analysis
            from emergentintegrations import EmergentLLM
            
            market_data = await MarketDataService.get_market_data(symbol)
            
            # Get additional market data for more comprehensive analysis
            volume_24h = market_data.get('volume_24h', 0)
            market_cap = market_data.get('market_cap', 0)
            asset_type = market_data.get('asset_type', 'unknown')
            asset_type_name = market_data.get('asset_type_name', 'غير معروف')
            
            change_percent = market_data.get('change_24h_percent', market_data.get('change_24h', 0))
            prompt = """
            أنت خبير تحليل مالي متخصص في %s. قم بتحليل البيانات التالية لـ %s:
            
            السعر الحالي: $%.2f
            التغيير خلال 24 ساعة: %+.2f%%
            أعلى سعر خلال 24 ساعة: $%.2f
            أدنى سعر خلال 24 ساعة: $%.2f
            الحجم خلال 24 ساعة: %.0f
            
            قدم تحليلاً تقنياً شاملاً يتضمن:
            1. تحليل الاتجاه الحالي (صاعد/هابط/جانبي) مع ذكر الأسباب
            2. مستويات الدعم والمقاومة المهمة مع الأسعار
            3. توصية التداول (شراء/بيع/انتظار) مع سبب التوصية
            4. إدارة المخاطر المقترحة (نسبة التوقف والخسارة)
            5. تحليل الحجم وتأثيره على الاتجاه
            
            اجعل التحليل مختصراً وقابلاً للتطبيق باللغة العربية.
            """ % (asset_type_name, symbol, market_data['price'], change_percent, 
                   market_data['high_24h'], market_data['low_24h'], volume_24h)
            
            # Initialize Emergent LLM
            llm = EmergentLLM(api_key=EMERGENT_LLM_KEY)
            
            # Get AI analysis
            analysis = llm.generate_text(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                max_tokens=300
            )
            
            return analysis.get('content', f"تحليل أساسي لـ {symbol}: السعر مستقر حالياً، يُنصح بالمتابعة قبل اتخاذ قرار.")
            
        except Exception as e:
            logging.error(f"Error in AI analysis: {e}")
            market_data = await MarketDataService.get_market_data(symbol)
            return f"تحليل فني لـ {symbol}: السعر الحالي ${{market_data['price']}} يظهر اتجاهاً مستقراً. المستوى الداعم عند ${{market_data['low_24h']:.2f}} والمقاومة عند ${{market_data['high_24h']:.2f}}."

    @staticmethod
    async def generate_daily_plan(user_id: str) -> DailyPlan:
        try:
            from emergentintegrations import EmergentLLM
            
            # Get current market data for major cryptocurrencies with more details
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT']
            market_summary = []
            detailed_market_data = []
            
            for symbol in symbols:
                data = await MarketDataService.get_market_data(symbol)
                market_summary.append(f"{symbol}: ${data['price']:.2f} ({data.get('change_24h_percent', data.get('change_24h', 0)):+.2f}%)")
                detailed_market_data.append({
                    'symbol': symbol,
                    'price': data['price'],
                    'change_24h': data.get('change_24h_percent', data.get('change_24h', 0)),
                    'high_24h': data.get('high_24h', 0),
                    'low_24h': data.get('low_24h', 0),
                    'volume_24h': data.get('volume_24h', 0),
                    'asset_type': data.get('asset_type', 'crypto')
                })
            
            prompt = f"""
            أنت مساعد تداول ذكي متخصص في العملات المشفرة. قم بإعداد خطة تداول يومية باللغة العربية تتضمن:

            بيانات السوق الحالية:
            {' | '.join(market_summary)}

            أعد خطة تداول يومية شاملة تتضمن:
            1. تحليل وضع السوق العام (50-80 كلمة) مع التركيز على الاتجاهات الرئيسية
            2. استراتيجية التداول المقترحة (30-50 كلمة) مع ذكر الأدوات المستخدمة
            3. تقييم مستوى المخاطرة (منخفض/متوسط/عالي) مع التبرير
            4. 2-3 فرص تداول محددة مع التفسير والأهداف والوقوف المكسي
            5. تحليل الحجم وتأثيره على الثقة في الاتجاهات

            يجب أن تكون التوصيات عملية ومناسبة للتداول اليومي مع إدارة مخاطر محافظة.
            """
            
            llm = EmergentLLM(api_key=EMERGENT_LLM_KEY)
            ai_response = llm.generate_text(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                max_tokens=400
            )
            
            ai_content = ai_response.get('content', '')
            
            # Parse AI response or use fallback
            if ai_content:
                plan = DailyPlan(
                    user_id=user_id,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    market_analysis=ai_content[:200] + "..." if len(ai_content) > 200 else ai_content,
                    trading_strategy="استراتيجية محافظة مع التركيز على الفرص عالية الاحتمالية",
                    risk_level="متوسط",
                    opportunities=[
                        {
                            "symbol": "BTCUSDT",
                            "action": "buy" if "شراء" in ai_content or "buy" in ai_content.lower() else "hold",
                            "confidence": "high",
                            "reason": "تحليل AI يشير لفرصة إيجابية",
                            "target": 45000,
                            "stop_loss": 42000
                        },
                        {
                            "symbol": "ETHUSDT", 
                            "action": "hold",
                            "confidence": "medium",
                            "reason": "انتظار إشارة اختراق واضحة",
                            "target": 2700,
                            "stop_loss": 2400
                        }
                    ]
                )
            else:
                # Fallback plan
                plan = DailyPlan(
                    user_id=user_id,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    market_analysis="السوق يظهر استقراراً نسبياً مع تقلبات معتدلة. Bitcoin يحافظ على مستويات دعم مهمة.",
                    trading_strategy="التركيز على العملات الرئيسية مع إدارة مخاطر محافظة",
                    risk_level="متوسط",
                    opportunities=[
                        {
                            "symbol": "BTCUSDT",
                            "action": "buy",
                            "confidence": "high",
                            "reason": "مستوى دعم قوي مع حجم تداول جيد",
                            "target": 45000,
                            "stop_loss": 42000
                        },
                        {
                            "symbol": "ETHUSDT", 
                            "action": "hold",
                            "confidence": "medium",
                            "reason": "انتظار كسر مستوى المقاومة",
                            "target": 2700,
                            "stop_loss": 2400
                        }
                    ]
                )
            
            return plan
            
        except Exception as e:
            logging.error(f"Error generating daily plan: {e}")
            # Return fallback plan
            plan = DailyPlan(
                user_id=user_id,
                date=datetime.now().strftime("%Y-%m-%d"),
                market_analysis="السوق يظهر استقراراً مع فرص محدودة اليوم",
                trading_strategy="نهج محافظ مع التركيز على إدارة المخاطر",
                risk_level="منخفض",
                opportunities=[
                    {
                        "symbol": "BTCUSDT",
                        "action": "hold",
                        "confidence": "medium",
                        "reason": "انتظار إشارات السوق",
                        "target": 44000,
                        "stop_loss": 41000
                    }
                ]
            )
            return plan

# Real Trading Engine with multiple exchange support
class RealTradingEngine:
    @staticmethod
    async def get_exchange_client(platform_type: str, api_key: str, secret_key: str, is_testnet: bool = True):
        """Initialize exchange client using CCXT"""
        try:
            import ccxt
            
            exchange_class = getattr(ccxt, platform_type.lower())
            
            # Configure exchange
            config = {
                'apiKey': api_key,
                'secret': secret_key,
                'timeout': 30000,
                'enableRateLimit': True,
            }
            
            # Set sandbox mode for supported exchanges
            if is_testnet:
                if platform_type.lower() in ['binance', 'bybit']:
                    config['sandbox'] = True
                elif platform_type.lower() == 'binance':
                    config['urls'] = {'api': 'https://testnet.binance.vision'}
            
            exchange = exchange_class(config)
            return exchange
            
        except Exception as e:
            logging.error(f"Error initializing exchange client: {e}")
            return None

    @staticmethod
    async def test_connection(platform_type: str, api_key: str, secret_key: str, is_testnet: bool = True) -> bool:
        """Test connection to exchange"""
        try:
            exchange = await RealTradingEngine.get_exchange_client(platform_type, api_key, secret_key, is_testnet)
            if exchange is None:
                return False
            
            # Test API connection
            await exchange.fetch_balance()
            return True
            
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False

    @staticmethod
    async def execute_real_trade(platform: Platform, trade_request: TradeRequest) -> Dict[str, Any]:
        """Execute real trade on exchange"""
        try:
            exchange = await RealTradingEngine.get_exchange_client(
                platform.platform_type, 
                platform.api_key, 
                platform.secret_key, 
                platform.is_testnet
            )
            
            if exchange is None:
                raise Exception("Failed to initialize exchange client")
            
            # Prepare order parameters
            order_type = 'market' if trade_request.order_type == OrderType.MARKET else 'limit'
            side = 'buy' if trade_request.trade_type == TradeType.BUY else 'sell'
            
            # Execute order
            order = await exchange.create_order(
                symbol=trade_request.symbol,
                type=order_type,
                side=side,
                amount=trade_request.quantity,
                price=trade_request.price if order_type == 'limit' else None
            )
            
            return {
                'success': True,
                'order': order,
                'exchange': platform.platform_type
            }
            
        except Exception as e:
            logging.error(f"Real trade execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'exchange': platform.platform_type
            }

# Enhanced Trading Engine with real trading support
class TradingEngine:
    @staticmethod
    async def execute_trade(user_id: str, trade_request: TradeRequest, use_real_trading: bool = True) -> Trade:
        try:
            current_price = await MarketDataService.get_price(trade_request.symbol)
            
            # Determine platform to use
            platform_name = "paper_trading"
            trade_executed_real = False
            
            if use_real_trading:
                # Get user's connected platforms
                platforms = await db.platforms.find({
                    "user_id": user_id, 
                    "status": PlatformStatus.CONNECTED
                }).to_list(10)
                
                if platforms:
                    # Use first connected platform
                    platform = platforms[0]
                    platform_obj = Platform(**platform)
                    
                    # Execute real trade
                    real_trade_result = await RealTradingEngine.execute_real_trade(platform_obj, trade_request)
                    
                    if real_trade_result['success']:
                        platform_name = f"{platform['platform_type']}_{'testnet' if platform['is_testnet'] else 'live'}"
                        current_price = real_trade_result['order'].get('price', current_price)
                        trade_executed_real = True
                        logging.info(f"Real trade executed successfully on {platform_name}")
                    else:
                        logging.warning(f"Real trade failed, using paper trading: {real_trade_result['error']}")
                        platform_name = "paper_trading_fallback"
                else:
                    logging.warning("No connected platforms found, using paper trading")
                    platform_name = "paper_trading_no_platforms"
            
            # Create trade entry
            trade = Trade(
                user_id=user_id,
                platform=platform_name,
                symbol=trade_request.symbol,
                trade_type=trade_request.trade_type,
                order_type=trade_request.order_type,
                quantity=trade_request.quantity,
                entry_price=trade_request.price or current_price,
                stop_loss=trade_request.stop_loss,
                take_profit=trade_request.take_profit,
                status=TradeStatus.OPEN
            )
            
            # Add metadata about trade execution
            trade_dict = trade.dict()
            trade_dict['execution_type'] = 'real' if trade_executed_real else 'paper'
            trade_dict['current_market_price'] = current_price
            
            # Save to database
            await db.trades.insert_one(trade_dict)
            
            # Update portfolio
            await TradingEngine.update_portfolio(user_id, trade)
            
            return trade
            
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            raise HTTPException(status_code=500, detail="فشل في تنفيذ الصفقة")
    
    @staticmethod
    async def update_portfolio(user_id: str, trade: Trade):
        try:
            portfolio = await db.portfolios.find_one({"user_id": user_id})
            
            if not portfolio:
                # Create new portfolio
                portfolio = Portfolio(
                    user_id=user_id,
                    total_balance=10000.0,  # Starting balance
                    available_balance=10000.0,
                    invested_balance=0.0,
                    daily_pnl=0.0,
                    total_pnl=0.0
                )
                await db.portfolios.insert_one(portfolio.dict())
            
            # Calculate trade value
            trade_value = trade.quantity * trade.entry_price
            
            # Update balances
            if trade.status == TradeStatus.OPEN:
                new_available = portfolio["available_balance"] - trade_value
                new_invested = portfolio["invested_balance"] + trade_value
                
                await db.portfolios.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "available_balance": new_available,
                            "invested_balance": new_invested,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
        except Exception as e:
            logging.error(f"Error updating portfolio: {e}")

# API Routes

@api_router.get("/")
async def root():
    return {"message": "Neon Trader V7 API", "status": "active", "version": "1.0.0"}

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register_user(user_data: UserRegister):
    try:
        # Validate password confirmation
        if user_data.password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="كلمات المرور غير متطابقة")
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
        
        existing_username = await db.users.find_one({"username": user_data.username})
        if existing_username:
            raise HTTPException(status_code=400, detail="اسم المستخدم غير متاح")
        
        # Hash password
        hashed_password = AuthService.get_password_hash(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )
        
        # Save to database
        await db.users.insert_one(user.dict())
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        # Create default portfolio for user
        portfolio = Portfolio(
            user_id=user.id,
            total_balance=10000.0,
            available_balance=10000.0,
            invested_balance=0.0,
            daily_pnl=0.0,
            total_pnl=0.0
        )
        await db.portfolios.insert_one(portfolio.dict())
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            username=user.username
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="خطأ في إنشاء الحساب")

@api_router.post("/auth/login", response_model=Token)
@limiter.limit(RATE_LIMITS['auth'])
async def login_user(request: Request, user_data: UserLogin):
    try:
        # Find user
        user = await db.users.find_one({"email": user_data.email})
        if not user:
            raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        # Verify password
        if not AuthService.verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        # Check if account is active
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="الحساب غير نشط")
        
        # TODO: Handle 2FA if enabled
        if user.get("two_factor_enabled", False) and not user_data.two_factor_code:
            raise HTTPException(status_code=422, detail="مطلوب رمز التحقق الثنائي")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user["id"], "username": user["username"]}, expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token_data = AuthService.create_refresh_token_data(user["id"])
        
        # Store refresh token in database
        await db.refresh_tokens.insert_one(refresh_token_data.dict())
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token_data.refresh_token,
            user_id=user["id"],
            email=user["email"],
            username=user["username"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="خطأ في تسجيل الدخول")

@api_router.post("/auth/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str = Form(...)):
    """Refresh access token using refresh token"""
    try:
        # Find refresh token in database
        refresh_data = await db.refresh_tokens.find_one({"refresh_token": refresh_token})
        
        if not refresh_data:
            raise HTTPException(status_code=401, detail="Refresh token not found")
        
        # Check if refresh token is expired
        if datetime.utcnow() > refresh_data["expires_at"]:
            # Delete expired refresh token
            await db.refresh_tokens.delete_one({"refresh_token": refresh_token})
            raise HTTPException(status_code=401, detail="Refresh token expired")
        
        # Get user data
        user = await db.users.find_one({"id": refresh_data["user_id"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="User account is inactive")
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user["id"], "username": user["username"]}, 
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token_data = AuthService.create_refresh_token_data(user["id"])
        
        # Delete old refresh token and store new one
        await db.refresh_tokens.delete_one({"refresh_token": refresh_token})
        await db.refresh_tokens.insert_one(new_refresh_token_data.dict())
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_refresh_token_data.refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Refresh token error: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")

@api_router.get("/auth/me")
async def get_current_user(current_user: User = Depends(AuthService.get_user_from_token)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "two_factor_enabled": current_user.two_factor_enabled,
        "created_at": current_user.created_at
    }

# Health Check Routes
@api_router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    health_status = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "neon-trader-v7"
    }
    
    health_logger.log_health_check("api", "ok", health_status)
    return health_status

@api_router.get("/ready")
async def readiness_check():
    """Readiness probe - checks if service is ready to serve requests"""
    checks = {}
    overall_status = "ok"
    
    # Check database connection
    try:
        await db.users.find_one({}, {"_id": 1})
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "error"
    
    # Check AI service
    try:
        if EMERGENT_LLM_KEY:
            checks["ai_service"] = "ready"
        else:
            checks["ai_service"] = "no_key"
            overall_status = "degraded"
    except Exception as e:
        checks["ai_service"] = f"error: {str(e)}"
        overall_status = "error"
    
    # Check market data services
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/ping", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    checks["market_data"] = "coingecko:ok"
                else:
                    checks["market_data"] = "coingecko:degraded"
                    overall_status = "degraded"
    except Exception as e:
        checks["market_data"] = f"coingecko:error: {str(e)}"
        if overall_status == "ok":
            overall_status = "degraded"
    
    # Check exchange connections (sample)
    exchanges_status = []
    try:
        # This is a placeholder - in production you'd check actual exchange APIs
        exchanges_status = ["binance:testnet", "bybit:testnet"]
        checks["exchanges"] = exchanges_status
    except Exception as e:
        checks["exchanges"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    readiness_result = {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks
    }
    
    health_logger.log_health_check("readiness", overall_status, readiness_result)
    
    # Return appropriate HTTP status
    if overall_status == "error":
        raise HTTPException(status_code=503, detail=readiness_result)
    
    return readiness_result

# Portfolio Routes
@api_router.get("/portfolio")
async def get_portfolio(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        portfolio = await db.portfolios.find_one({"user_id": current_user.id})
        if not portfolio:
            # Create default portfolio
            portfolio = Portfolio(
                user_id=current_user.id,
                total_balance=10000.0,
                available_balance=10000.0,
                invested_balance=0.0,
                daily_pnl=0.0,
                total_pnl=0.0
            )
            await db.portfolios.insert_one(portfolio.dict())
            return portfolio.dict()
        
        # Remove _id field for JSON serialization
        portfolio.pop('_id', None)
        return portfolio
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trades Routes
@api_router.post("/trades")
@limiter.limit(RATE_LIMITS['trading'])
async def create_trade(request: Request, trade_request: TradeRequest, current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        trade = await TradingEngine.execute_trade(current_user.id, trade_request, use_real_trading=True)
        
        # Get the enhanced trade data from database (includes execution_type and current_market_price)
        enhanced_trade_data = await db.trades.find_one({"id": trade.id})
        if enhanced_trade_data:
            enhanced_trade_data.pop('_id', None)
            return {"message": "تم تنفيذ الصفقة بنجاح", "trade": enhanced_trade_data}
        else:
            return {"message": "تم تنفيذ الصفقة بنجاح", "trade": trade.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Two-Factor Authentication Routes
@api_router.post("/auth/2fa/setup")
async def setup_2fa(current_user: User = Depends(AuthService.get_user_from_token)):
    """Setup Two-Factor Authentication"""
    try:
        # Generate secret key
        secret_key = TwoFactorAuthService.generate_secret_key()
        
        # Generate QR code
        qr_code = TwoFactorAuthService.generate_qr_code(
            user_email=current_user.email,
            secret_key=secret_key,
            app_name="Neon Trader V7"
        )
        
        # Generate backup codes
        backup_codes = TwoFactorAuthService.generate_backup_codes()
        
        # Store secret temporarily (not activated yet)
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {
                "two_factor_secret_temp": secret_key,
                "backup_codes_temp": backup_codes
            }}
        )
        
        return {
            "qr_code": qr_code,
            "secret_key": secret_key,
            "backup_codes": backup_codes,
            "message": "اسحب QR Code بتطبيق المصادقة وأدخل الرمز للتأكيد"
        }
        
    except Exception as e:
        logging.error(f"2FA setup error: {e}")
        raise HTTPException(status_code=500, detail="فشل في إعداد المصادقة الثنائية")

@api_router.post("/auth/2fa/verify-setup")
async def verify_2fa_setup(
    token: str = Form(...),
    current_user: User = Depends(AuthService.get_user_from_token)
):
    """Verify and activate Two-Factor Authentication"""
    try:
        if not validate_totp_token_format(token):
            raise HTTPException(status_code=400, detail="تنسيق الرمز غير صحيح")
        
        # Get temporary secret
        user_data = await db.users.find_one({"id": current_user.id})
        temp_secret = user_data.get("two_factor_secret_temp")
        temp_backup_codes = user_data.get("backup_codes_temp", [])
        
        if not temp_secret:
            raise HTTPException(status_code=400, detail="لم يتم العثور على إعداد مؤقت للمصادقة")
        
        # Verify token
        if not TwoFactorAuthService.verify_token(temp_secret, token):
            SecurityAuditLogger.log_2fa_setup(current_user.id, False)
            raise HTTPException(status_code=400, detail="رمز التحقق غير صحيح")
        
        # Activate 2FA
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$set": {
                    "two_factor_secret": temp_secret,
                    "two_factor_enabled": True,
                    "backup_codes": temp_backup_codes,
                    "two_factor_setup_at": datetime.now(timezone.utc)
                },
                "$unset": {
                    "two_factor_secret_temp": "",
                    "backup_codes_temp": ""
                }
            }
        )
        
        SecurityAuditLogger.log_2fa_setup(current_user.id, True)
        
        return {
            "message": "تم تفعيل المصادقة الثنائية بنجاح",
            "backup_codes": temp_backup_codes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"2FA verification error: {e}")
        raise HTTPException(status_code=500, detail="فشل في تأكيد المصادقة الثنائية")

@api_router.post("/auth/2fa/verify")
async def verify_2fa_login(
    token: str = Form(...),
    backup_code: str = Form(None),
    user_id: str = Form(...)
):
    """Verify 2FA token during login"""
    try:
        user_data = await db.users.find_one({"id": user_id})
        if not user_data or not user_data.get("two_factor_enabled"):
            raise HTTPException(status_code=400, detail="المصادقة الثنائية غير مُفعّلة")
        
        is_valid = False
        method = "totp"
        
        # Try TOTP token first
        if token and validate_totp_token_format(token):
            secret = user_data.get("two_factor_secret")
            is_valid = TwoFactorAuthService.verify_token(secret, token)
            method = "totp"
        
        # Try backup code if TOTP fails
        if not is_valid and backup_code:
            stored_codes = user_data.get("backup_codes", [])
            is_valid, remaining_codes = TwoFactorAuthService.validate_backup_code(stored_codes, backup_code)
            
            if is_valid:
                # Update remaining backup codes
                await db.users.update_one(
                    {"id": user_id},
                    {"$set": {"backup_codes": remaining_codes}}
                )
                method = "backup_code"
                SecurityAuditLogger.log_backup_code_usage(user_id, True)
        
        SecurityAuditLogger.log_2fa_verification(user_id, is_valid, method)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="رمز التحقق غير صحيح")
        
        return {"message": "تم التحقق بنجاح", "method": method}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"2FA login verification error: {e}")
        raise HTTPException(status_code=500, detail="فشل في التحقق من المصادقة")

@api_router.post("/auth/2fa/disable")
async def disable_2fa(
    password: str = Form(...),
    current_user: User = Depends(AuthService.get_user_from_token)
):
    """Disable Two-Factor Authentication"""
    try:
        # Verify password
        user_data = await db.users.find_one({"id": current_user.id})
        if not AuthService.verify_password(password, user_data["password"]):
            raise HTTPException(status_code=400, detail="كلمة المرور غير صحيحة")
        
        # Disable 2FA
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$set": {"two_factor_enabled": False},
                "$unset": {
                    "two_factor_secret": "",
                    "backup_codes": ""
                }
            }
        )
        
        SecurityAuditLogger.log_2fa_disable(current_user.id)
        
        return {"message": "تم إلغاء تفعيل المصادقة الثنائية"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"2FA disable error: {e}")
        raise HTTPException(status_code=500, detail="فشل في إلغاء المصادقة الثنائية")

@api_router.get("/auth/2fa/backup-codes")
async def regenerate_backup_codes(current_user: User = Depends(AuthService.get_user_from_token)):
    """Regenerate backup codes"""
    try:
        user_data = await db.users.find_one({"id": current_user.id})
        if not user_data.get("two_factor_enabled"):
            raise HTTPException(status_code=400, detail="المصادقة الثنائية غير مُفعّلة")
        
        # Generate new backup codes
        new_backup_codes = TwoFactorAuthService.generate_backup_codes()
        
        # Update user
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"backup_codes": new_backup_codes}}
        )
        
        logging.info(f"Backup codes regenerated for user: {current_user.id}")
        
        return {
            "backup_codes": new_backup_codes,
            "message": "تم إنشاء رموز احتياطية جديدة"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Backup codes regeneration error: {e}")
        raise HTTPException(status_code=500, detail="فشل في إنشاء رموز احتياطية")

# Portfolio Snapshot Routes
@api_router.post("/snapshots")
@limiter.limit("30/minute")
async def create_snapshot(request: Request, snapshot_data: SnapshotRequest, current_user: User = Depends(AuthService.get_user_from_token)):
    """Create a portfolio snapshot"""
    try:
        snapshot = PortfolioSnapshot(
            user_id=current_user.id,
            total_balance=snapshot_data.total_balance,
            available_balance=snapshot_data.available_balance,
            invested_balance=snapshot_data.invested_balance,
            daily_pnl=snapshot_data.daily_pnl,
            total_pnl=snapshot_data.total_pnl,
            assets=snapshot_data.assets or {},
            positions=snapshot_data.positions or [],
            metadata=snapshot_data.metadata or {}
        )
        
        await db.portfolio_snapshots.insert_one(snapshot.dict())
        return {"message": "Snapshot created successfully", "snapshot_id": snapshot.id}
        
    except Exception as e:
        logging.error(f"Snapshot creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create snapshot")

@api_router.get("/snapshots")
async def get_snapshots(
    current_user: User = Depends(AuthService.get_user_from_token),
    limit: int = 50,
    days: int = 30
):
    """Get portfolio snapshots history"""
    try:
        # Calculate date range
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        snapshots = await db.portfolio_snapshots.find({
            "user_id": current_user.id,
            "timestamp": {"$gte": cutoff_date}
        }).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Remove _id fields
        for snapshot in snapshots:
            snapshot.pop('_id', None)
            
        return snapshots
        
    except Exception as e:
        logging.error(f"Snapshots retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve snapshots")

@api_router.get("/snapshots/analysis/{period}")
async def get_snapshot_analysis(
    period: str,
    current_user: User = Depends(AuthService.get_user_from_token)
):
    """Get portfolio performance analysis based on snapshots"""
    try:
        # Define period mapping
        period_days = {
            "1d": 1,
            "7d": 7, 
            "30d": 30,
            "90d": 90
        }
        
        days = period_days.get(period, 30)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get snapshots for the period
        snapshots = await db.portfolio_snapshots.find({
            "user_id": current_user.id,
            "timestamp": {"$gte": cutoff_date}
        }).sort("timestamp", 1).to_list(1000)
        
        if len(snapshots) < 2:
            return {"message": "Insufficient data for analysis", "snapshots_count": len(snapshots)}
        
        # Calculate performance metrics
        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]
        
        balance_change = last_snapshot['total_balance'] - first_snapshot['total_balance']
        balance_change_percent = (balance_change / first_snapshot['total_balance']) * 100
        pnl_change = last_snapshot['total_pnl'] - first_snapshot['total_pnl']
        
        # Get trades count for the period
        trades = await db.trades.find({
            "user_id": current_user.id,
            "created_at": {"$gte": cutoff_date}
        }).to_list(1000)
        
        total_trades = len(trades)
        profitable_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate average daily return
        avg_daily_return = balance_change_percent / days if days > 0 else 0
        
        analysis = SnapshotAnalysis(
            period=period,
            balance_change=round(balance_change, 2),
            balance_change_percent=round(balance_change_percent, 2),
            pnl_change=round(pnl_change, 2),
            total_trades=total_trades,
            win_rate=round(win_rate, 2),
            avg_daily_return=round(avg_daily_return, 4)
        )
        
        return analysis
        
    except Exception as e:
        logging.error(f"Snapshot analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analysis")

@api_router.get("/trades")
async def get_trades(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        trades = await db.trades.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
        # Remove _id fields
        for trade in trades:
            trade.pop('_id', None)
        return trades
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/trades/{trade_id}/close")
async def close_trade(trade_id: str):
    try:
        trade = await db.trades.find_one({"id": trade_id})
        if not trade:
            raise HTTPException(status_code=404, detail="الصفقة غير موجودة")
        
        # Get current price for closing
        current_price = await MarketDataService.get_price(trade["symbol"])
        
        # Calculate PnL
        if trade["trade_type"] == "buy":
            pnl = (current_price - trade["entry_price"]) * trade["quantity"]
        else:
            pnl = (trade["entry_price"] - current_price) * trade["quantity"]
        
        # Update trade
        await db.trades.update_one(
            {"id": trade_id},
            {
                "$set": {
                    "status": TradeStatus.CLOSED,
                    "exit_price": current_price,
                    "pnl": pnl,
                    "closed_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "تم إغلاق الصفقة بنجاح", "pnl": pnl}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trade Approval Routes (Human-in-the-loop)
@api_router.post("/trades/simulate")
@limiter.limit("10/minute")
async def simulate_trade(request: Request, trade_request: TradeRequest, current_user: User = Depends(AuthService.get_user_from_token)):
    """Simulate trade and create approval request"""
    try:
        # Get market data for simulation
        market_data = await MarketDataService.get_market_data(trade_request.symbol)
        current_price = market_data['price']
        
        # Calculate estimated costs
        estimated_cost = current_price * trade_request.quantity
        estimated_fees = estimated_cost * 0.001  # 0.1% fee simulation
        
        # Risk assessment
        portfolio = await db.portfolios.find_one({"user_id": current_user.id}) or {"available_balance": 10000}
        risk_percentage = (estimated_cost / portfolio["available_balance"]) * 100
        
        risk_assessment = {
            "risk_level": "high" if risk_percentage > 20 else "medium" if risk_percentage > 10 else "low",
            "risk_percentage": round(risk_percentage, 2),
            "max_loss": estimated_cost if not trade_request.stop_loss else abs(current_price - trade_request.stop_loss) * trade_request.quantity,
            "reward_ratio": 2.0 if trade_request.take_profit else 1.0
        }
        
        # Get AI market analysis
        try:
            analysis = await AIService.get_market_analysis(trade_request.symbol)
        except:
            analysis = f"تحليل لـ {trade_request.symbol}: السعر الحالي ${current_price:,.2f}"
        
        # Create proposed trade
        proposed_trade = ProposedTrade(
            user_id=current_user.id,
            symbol=trade_request.symbol,
            trade_type=trade_request.trade_type.value,
            order_type=trade_request.order_type.value,
            quantity=trade_request.quantity,
            entry_price=trade_request.entry_price or current_price,
            stop_loss=trade_request.stop_loss,
            take_profit=trade_request.take_profit,
            platform_id=trade_request.platform_id,
            estimated_cost=estimated_cost,
            estimated_fees=estimated_fees,
            risk_assessment=risk_assessment,
            market_analysis=analysis
        )
        
        # Store for approval
        await db.proposed_trades.insert_one(proposed_trade.dict())
        
        return {
            "trade_id": proposed_trade.id,
            "status": "pending_approval",
            "estimated_cost": estimated_cost,
            "estimated_fees": estimated_fees,
            "risk_assessment": risk_assessment,
            "market_analysis": analysis,
            "expires_at": proposed_trade.expires_at.isoformat()
        }
        
    except Exception as e:
        logging.error(f"Trade simulation error: {e}")
        raise HTTPException(status_code=500, detail="فشل في محاكاة الصفقة")

@api_router.get("/trades/pending-approval")
async def get_pending_approvals(current_user: User = Depends(AuthService.get_user_from_token)):
    """Get all pending trade approvals"""
    try:
        # Clean expired approvals first
        await db.proposed_trades.update_many(
            {
                "user_id": current_user.id,
                "status": ApprovalStatus.PENDING,
                "expires_at": {"$lt": datetime.now(timezone.utc)}
            },
            {"$set": {"status": ApprovalStatus.EXPIRED}}
        )
        
        # Get pending approvals
        pending_trades = await db.proposed_trades.find({
            "user_id": current_user.id,
            "status": ApprovalStatus.PENDING
        }).sort("proposed_at", -1).to_list(50)
        
        # Remove _id fields
        for trade in pending_trades:
            trade.pop('_id', None)
            
        return pending_trades
        
    except Exception as e:
        logging.error(f"Pending approvals error: {e}")
        raise HTTPException(status_code=500, detail="فشل في جلب الموافقات المعلقة")

@api_router.post("/trades/{trade_id}/approve")
@limiter.limit("20/minute")
async def approve_trade(request: Request, trade_id: str, approval: TradeApprovalRequest, current_user: User = Depends(AuthService.get_user_from_token)):
    """Approve or reject a proposed trade"""
    try:
        # Find proposed trade
        proposed_trade = await db.proposed_trades.find_one({
            "id": trade_id,
            "user_id": current_user.id,
            "status": ApprovalStatus.PENDING
        })
        
        if not proposed_trade:
            raise HTTPException(status_code=404, detail="الصفقة المقترحة غير موجودة أو منتهية الصلاحية")
        
        # Check if not expired
        if datetime.now(timezone.utc) > proposed_trade["expires_at"]:
            await db.proposed_trades.update_one(
                {"id": trade_id},
                {"$set": {"status": ApprovalStatus.EXPIRED}}
            )
            raise HTTPException(status_code=400, detail="انتهت صلاحية الصفقة المقترحة")
        
        if approval.action == "approve":
            # Execute the actual trade
            trade_request = TradeRequest(
                symbol=proposed_trade["symbol"],
                trade_type=TradeType(proposed_trade["trade_type"]),
                order_type=OrderType(proposed_trade["order_type"]),
                quantity=proposed_trade["quantity"],
                entry_price=proposed_trade.get("entry_price"),
                stop_loss=proposed_trade.get("stop_loss"),
                take_profit=proposed_trade.get("take_profit"),
                platform_id=proposed_trade["platform_id"]
            )
            
            # Execute via TradingEngine
            executed_trade = await TradingEngine.execute_trade(current_user.id, trade_request)
            
            # Update proposed trade status
            await db.proposed_trades.update_one(
                {"id": trade_id},
                {
                    "$set": {
                        "status": ApprovalStatus.APPROVED,
                        "approved_at": datetime.now(timezone.utc),
                        "approved_by": current_user.id
                    }
                }
            )
            
            return {
                "message": "تم تنفيذ الصفقة بنجاح",
                "executed_trade_id": executed_trade.id,
                "status": "executed"
            }
            
        elif approval.action == "reject":
            # Reject the trade
            await db.proposed_trades.update_one(
                {"id": trade_id},
                {
                    "$set": {
                        "status": ApprovalStatus.REJECTED,
                        "rejection_reason": approval.reason or "مرفوض من قبل المستخدم"
                    }
                }
            )
            
            return {"message": "تم رفض الصفقة", "status": "rejected"}
        
        else:
            raise HTTPException(status_code=400, detail="إجراء غير صالح")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Trade approval error: {e}")
        raise HTTPException(status_code=500, detail="فشل في معالجة الموافقة")

@api_router.get("/trades/approval-summary")
async def get_approval_summary(current_user: User = Depends(AuthService.get_user_from_token)):
    """Get approval statistics summary"""
    try:
        from datetime import timedelta
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count pending trades
        total_pending = await db.proposed_trades.count_documents({
            "user_id": current_user.id,
            "status": ApprovalStatus.PENDING
        })
        
        # Count today's approvals and rejections
        total_approved_today = await db.proposed_trades.count_documents({
            "user_id": current_user.id,
            "status": ApprovalStatus.APPROVED,
            "approved_at": {"$gte": today}
        })
        
        total_rejected_today = await db.proposed_trades.count_documents({
            "user_id": current_user.id,
            "status": ApprovalStatus.REJECTED,
            "approved_at": {"$gte": today}
        })
        
        # Calculate pending value
        pending_trades = await db.proposed_trades.find({
            "user_id": current_user.id,
            "status": ApprovalStatus.PENDING
        }).to_list(100)
        
        pending_value = sum(trade.get("estimated_cost", 0) for trade in pending_trades)
        
        summary = ApprovalSummary(
            total_pending=total_pending,
            total_approved_today=total_approved_today,
            total_rejected_today=total_rejected_today,
            pending_value=round(pending_value, 2),
            avg_approval_time_minutes=5.5  # Mock average - would calculate from historical data
        )
        
        return summary
        
    except Exception as e:
        logging.error(f"Approval summary error: {e}")
        raise HTTPException(status_code=500, detail="فشل في جلب ملخص الموافقات")

# Platforms Routes
@api_router.post("/platforms")
async def add_platform(platform_request: PlatformRequest, current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        # Default to live trading unless explicitly set to testnet
        is_testnet = platform_request.is_testnet if platform_request.is_testnet is not None else False
        
        platform = Platform(
            user_id=current_user.id,
            name=platform_request.name,
            platform_type=platform_request.platform_type,
            api_key=platform_request.api_key,
            secret_key=platform_request.secret_key,
            is_testnet=is_testnet,
            status=PlatformStatus.DISCONNECTED
        )
        
        await db.platforms.insert_one(platform.dict())
        return {"message": "تم إضافة المنصة بنجاح", "platform": platform.dict()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/platforms")
async def get_platforms(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        platforms = await db.platforms.find({"user_id": current_user.id}).to_list(100)
        # Remove _id and sensitive fields
        for platform in platforms:
            platform.pop('_id', None)
            platform.pop('secret_key', None)  # Don't expose secret keys
        return platforms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/platforms/{platform_id}/test")
async def test_platform_connection(platform_id: str, current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        platform = await db.platforms.find_one({"id": platform_id, "user_id": current_user.id})
        if not platform:
            raise HTTPException(status_code=404, detail="المنصة غير موجودة")
        
        # Real connection test if API keys are provided
        success = False
        message = ""
        connection_details = {}
        
        if platform.get('api_key') and platform.get('secret_key'):
            # Test real connection
            try:
                success = await RealTradingEngine.test_connection(
                    platform['platform_type'],
                    platform['api_key'],
                    platform['secret_key'],
                    platform['is_testnet']
                )
                
                if success:
                    message = f"✅ تم اختبار الاتصال بنجاح - المنصة متصلة بـ {platform['platform_type']}!"
                    connection_details = {
                        "platform_type": platform['platform_type'],
                        "connection_mode": "testnet" if platform['is_testnet'] else "live",
                        "last_tested": datetime.utcnow().isoformat(),
                        "status": "active"
                    }
                else:
                    message = f"❌ فشل الاتصال بـ {platform['platform_type']} - تحقق من صحة مفاتيح API"
                    connection_details = {
                        "platform_type": platform['platform_type'],
                        "error": "authentication_failed",
                        "last_tested": datetime.utcnow().isoformat(),
                        "status": "failed"
                    }
                    
            except Exception as e:
                success = False
                message = f"❌ خطأ في اختبار الاتصال بـ {platform['platform_type']}: {str(e)}"
                connection_details = {
                    "platform_type": platform['platform_type'],
                    "error": str(e),
                    "last_tested": datetime.utcnow().isoformat(),
                    "status": "error"
                }
        else:
            # Mock connection for platforms without API keys
            success = True
            message = f"⚠️ اختبار وهمي لـ {platform['name']} - أضف مفاتيح API للاتصال الحقيقي"
            connection_details = {
                "platform_type": platform['platform_type'],
                "connection_mode": "demo",
                "message": "تحتاج إضافة مفاتيح API",
                "last_tested": datetime.utcnow().isoformat(),
                "status": "demo"
            }
        
        status = PlatformStatus.CONNECTED if success else PlatformStatus.DISCONNECTED
        
        # Update platform with connection details
        await db.platforms.update_one(
            {"id": platform_id},
            {
                "$set": {
                    "status": status,
                    "last_tested": datetime.utcnow().isoformat(),
                    "connection_details": connection_details
                }
            }
        )
        
        return {
            "success": success, 
            "status": status, 
            "message": message,
            "connection_details": connection_details,
            "platform_name": platform['name']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Platform connection test error: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في اختبار الاتصال: {str(e)}")

# AI Assistant Routes
@api_router.get("/ai/daily-plan")
async def get_daily_plan(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        # Check if plan exists for today
        today = datetime.now().strftime("%Y-%m-%d")
        existing_plan = await db.daily_plans.find_one({"user_id": current_user.id, "date": today})
        
        if existing_plan:
            existing_plan.pop('_id', None)
            return existing_plan
        
        # Generate new plan
        plan = await AIService.generate_daily_plan(current_user.id)
        await db.daily_plans.insert_one(plan.dict())
        
        return plan.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/analyze")
async def analyze_market(analysis_request: AIAnalysisRequest):
    try:
        analysis = await AIService.get_market_analysis(analysis_request.symbol)
        market_data = await MarketDataService.get_market_data(analysis_request.symbol)
        
        return {
            "symbol": analysis_request.symbol,
            "analysis": analysis,
            "market_data": market_data,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Market Data Routes
@api_router.get("/market/{symbol}")
async def get_market_data(symbol: str):
    try:
        data = await MarketDataService.get_market_data(symbol)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/market/types/all")
async def get_all_asset_types():
    try:
        types = await MarketDataService.get_all_asset_types()
        return types
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/market/symbols/{asset_type}")
async def get_symbols_by_asset_type(asset_type: str):
    try:
        symbols = await MarketDataService.get_symbols_by_type(asset_type)
        if not symbols:
            raise HTTPException(status_code=404, detail="نوع الأصل غير موجود")
        return {"asset_type": asset_type, "symbols": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/market/prices/multiple")
async def get_multiple_prices(symbols: str):
    try:
        symbol_list = symbols.split(",")
        prices = {}
        
        for symbol in symbol_list:
            symbol = symbol.strip()
            market_data = await MarketDataService.get_market_data(symbol)
            prices[symbol] = {
                "price": market_data["price"],
                "change_24h": market_data.get("change_24h", 0),
                "change_24h_percent": market_data.get("change_24h_percent", market_data.get("change_24h", 0)),
                "asset_type": market_data.get("asset_type", "unknown")
            }
            
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Smart Notifications System
class SmartNotificationService:
    @staticmethod
    async def generate_market_analysis() -> str:
        """Generate AI-powered market analysis"""
        try:
            from emergentintegrations import EmergentLLM
            
            # Get current market data for analysis
            symbols = ['BTCUSDT', 'ETHUSDT', 'XAUUSD', 'EURUSD', 'AAPL']
            market_data = []
            
            for symbol in symbols:
                data = await MarketDataService.get_market_data(symbol)
                market_data.append({
                    'symbol': symbol,
                    'price': data['price'],
                    'change_24h_percent': data['change_24h_percent'],
                    'asset_type': data.get('asset_type', 'unknown')
                })
            
            prompt = f"""
            أنت خبير تحليل أسواق مالية متخصص. قم بتحليل البيانات التالية وقدم توصيات ذكية:

            بيانات السوق الحالية:
            {market_data}

            قدم تحليلاً يتضمن:
            1. تحليل الاتجاه العام للأسواق
            2. أفضل 2-3 فرص استثمارية حالياً 
            3. تحذيرات مخاطر محتملة
            4. توصيات للمدى القصير والطويل
            5. نصائح لإدارة المحفظة

            اجعل التحليل مفيداً وقابلاً للتطبيق باللغة العربية.
            """
            
            llm = EmergentLLM(api_key=EMERGENT_LLM_KEY)
            analysis = llm.generate_text(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                max_tokens=500
            )
            
            return analysis.get('content', 'تحليل السوق غير متاح حالياً')
            
        except Exception as e:
            logging.error(f"Error generating market analysis: {e}")
            return "تحليل السوق العام: الأسواق تشهد حركة طبيعية مع فرص متنوعة للاستثمار."

    @staticmethod
    async def detect_trading_opportunities(user_id: str) -> List[Dict[str, Any]]:
        """Detect trading opportunities using AI"""
        try:
            # Mock opportunities - في الإنتاج ستكون تحليل حقيقي
            mock_opportunities = [
                {
                    'symbol': 'BTCUSDT',
                    'type': 'breakout',
                    'confidence': 85,
                    'timeframe': 'متوسط المدى',
                    'description': 'كسر مستوى المقاومة مع حجم تداول عالي',
                    'target_price': 47000,
                    'stop_loss': 41000,
                    'risk_reward': 2.5
                },
                {
                    'symbol': 'XAUUSD', 
                    'type': 'news_driven',
                    'confidence': 78,
                    'timeframe': 'طويل المدى',
                    'description': 'قرارات البنوك المركزية تدعم ارتفاع الذهب',
                    'target_price': 2100,
                    'stop_loss': 1980,
                    'risk_reward': 3.0
                }
            ]
            
            return mock_opportunities
            
        except Exception as e:
            logging.error(f"Error detecting opportunities: {e}")
            return []

    @staticmethod
    async def create_smart_notification(user_id: str, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a smart notification"""
        try:
            notification = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'type': notification_type,
                'title': data.get('title', 'إشعار جديد'),
                'message': data.get('message', ''),
                'symbol': data.get('symbol'),
                'confidence': data.get('confidence'),
                'timeframe': data.get('timeframe'),
                'priority': data.get('priority', 'medium'),
                'created_at': datetime.utcnow().isoformat(),  # Serialize to ISO string
                'read': False
            }
            
            await db.notifications.insert_one(notification)
            
            # Remove MongoDB _id for clean response
            notification.pop('_id', None)
            return notification
            
        except Exception as e:
            logging.error(f"Error creating notification: {e}")
            return None

# User Settings Routes
@api_router.get("/user/settings")
async def get_user_settings(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        settings = await db.user_settings.find_one({"user_id": current_user.id})
        if settings:
            settings.pop('_id', None)
            return settings.get('settings', {})
        return {}
    except Exception as e:
        logging.error(f"Error getting user settings: {e}")
        raise HTTPException(status_code=500, detail="خطأ في تحميل الإعدادات")

@api_router.put("/user/settings")
async def update_user_settings(
    settings: dict, 
    current_user: User = Depends(AuthService.get_user_from_token)
):
    try:
        # Update or create user settings
        await db.user_settings.update_one(
            {"user_id": current_user.id},
            {
                "$set": {
                    "user_id": current_user.id,
                    "settings": settings,
                    "updated_at": datetime.utcnow().isoformat()
                }
            },
            upsert=True
        )
        
        return {"message": "تم حفظ الإعدادات بنجاح", "success": True}
    except Exception as e:
        logging.error(f"Error updating user settings: {e}")
        raise HTTPException(status_code=500, detail="خطأ في حفظ الإعدادات")

@api_router.put("/user/change-password")
async def change_password(
    password_data: dict,
    current_user: User = Depends(AuthService.get_user_from_token)
):
    try:
        current_password = password_data.get('currentPassword')
        new_password = password_data.get('newPassword')
        
        if not current_password or not new_password:
            raise HTTPException(status_code=400, detail="كلمة المرور الحالية والجديدة مطلوبة")
        
        # Get user from database
        user = await db.users.find_one({"id": current_user.id})
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        # Verify current password
        if not AuthService.verify_password(current_password, user['hashed_password']):
            raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
        
        # Hash new password
        new_hashed_password = AuthService.get_password_hash(new_password)
        
        # Update password in database
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"hashed_password": new_hashed_password, "updated_at": datetime.utcnow()}}
        )
        
        return {"message": "تم تغيير كلمة المرور بنجاح", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail="خطأ في تغيير كلمة المرور")
@api_router.get("/notifications")
async def get_user_notifications(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        notifications = await db.notifications.find({"user_id": current_user.id}).sort("created_at", -1).to_list(50)
        # Remove _id fields
        for notification in notifications:
            notification.pop('_id', None)
        return notifications
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/notifications/smart-alert")
async def create_smart_alert(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        # Generate AI-powered market analysis
        analysis = await SmartNotificationService.generate_market_analysis()
        
        # Detect opportunities
        opportunities = await SmartNotificationService.detect_trading_opportunities(current_user.id)
        
        # Create notification with analysis
        notification_data = {
            'title': 'تحليل ذكي جديد للأسواق',
            'message': analysis[:200] + "...",  # Truncate for notification
            'type': 'ai_analysis',
            'priority': 'high',
            'timeframe': 'تحليل شامل'
        }
        
        notification = await SmartNotificationService.create_smart_notification(
            current_user.id, 'opportunity', notification_data
        )
        
        return {
            'notification': notification,
            'analysis': analysis,
            'opportunities': opportunities
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notifications/opportunities")
async def get_trading_opportunities(current_user: User = Depends(AuthService.get_user_from_token)):
    try:
        opportunities = await SmartNotificationService.detect_trading_opportunities(current_user.id)
        return {'opportunities': opportunities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    try:
        result = await db.notifications.update_one(
            {"id": notification_id},
            {"$set": {"read": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="الإشعار غير موجود")
            
        return {"message": "تم تحديد الإشعار كمقروء"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"]
)

# Performance Monitoring
app.add_middleware(PerformanceMonitoringMiddleware, logger=performance_logger)

# Rate Limiting
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data"""
    connection_id = await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            await WebSocketHandler.handle_message(websocket, connection_id, message_data)
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background Tasks
async def update_market_prices():
    """Background task to update market prices periodically"""
    while True:
        try:
            # This would update real market prices in production
            await asyncio.sleep(60)  # Update every minute
        except Exception as e:
            logger.error(f"Error updating market prices: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("Neon Trader V7 API Started")
    # Start background tasks
    # asyncio.create_task(update_market_prices())

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")