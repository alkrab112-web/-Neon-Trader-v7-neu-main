from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
import asyncio
from passlib.context import CryptContext
from jose import JWTError, jwt

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

# Create the main app
app = FastAPI(title="Neon Trader V7 - Development", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            user_id: str = payload.get("sub", "")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        # Return a mock user for development
        return User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password=pwd_context.hash("testpassword123"),
            is_active=True,
            two_factor_enabled=False
        )

# Development user data
DEVELOPMENT_USER = {
    "email": "test@example.com",
    "password": "testpassword123",  # This will be hashed
    "username": "testuser",
    "id": "dev-user-123"
}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Neon Trader V7 API - Development Mode", "status": "active", "version": "1.0.0"}

@api_router.post("/auth/register", response_model=Token)
async def register_user(user_data: UserRegister):
    # In development mode, always return success
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": DEVELOPMENT_USER["id"], "username": DEVELOPMENT_USER["username"]}, 
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=DEVELOPMENT_USER["id"],
        email=DEVELOPMENT_USER["email"],
        username=DEVELOPMENT_USER["username"]
    )

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_data: UserLogin):
    # In development mode, accept any login attempt
    # But for security, we'll still check if it matches our dev credentials
    if user_data.email == DEVELOPMENT_USER["email"] and user_data.password == DEVELOPMENT_USER["password"]:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": DEVELOPMENT_USER["id"], "username": DEVELOPMENT_USER["username"]}, 
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=DEVELOPMENT_USER["id"],
            email=DEVELOPMENT_USER["email"],
            username=DEVELOPMENT_USER["username"]
        )
    else:
        raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")

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

@api_router.get("/portfolio")
async def get_portfolio(current_user: User = Depends(AuthService.get_user_from_token)):
    # Return a mock portfolio for development
    return Portfolio(
        user_id=current_user.id,
        total_balance=10000.0,
        available_balance=8000.0,
        invested_balance=2000.0,
        daily_pnl=150.0,
        total_pnl=500.0
    )

@api_router.get("/trades")
async def get_trades(current_user: User = Depends(AuthService.get_user_from_token)):
    # Return mock trades for development
    return [
        Trade(
            user_id=current_user.id,
            platform="binance",
            symbol="BTCUSDT",
            trade_type=TradeType.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1,
            entry_price=45000.0,
            status=TradeStatus.OPEN,
            pnl=250.0
        )
    ]

@api_router.post("/trades")
async def create_trade(trade_request: TradeRequest, current_user: User = Depends(AuthService.get_user_from_token)):
    # Mock trade creation
    return {"message": "تم إنشاء الصفقة بنجاح", "trade_id": str(uuid.uuid4())}

@api_router.get("/platforms")
async def get_platforms(current_user: User = Depends(AuthService.get_user_from_token)):
    # Return mock platforms for development
    return [
        Platform(
            user_id=current_user.id,
            name="Binance",
            platform_type="binance",
            is_testnet=True,
            status=PlatformStatus.CONNECTED
        )
    ]

@api_router.post("/platforms")
async def add_platform(platform_request: PlatformRequest, current_user: User = Depends(AuthService.get_user_from_token)):
    # Mock platform addition
    return {"message": "تمت إضافة المنصة بنجاح", "platform_id": str(uuid.uuid4())}

# Health Check Routes
@api_router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "neon-trader-v7-dev"
    }

@api_router.get("/ready")
async def readiness_check():
    """Readiness probe - checks if service is ready to serve requests"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "neon-trader-v7-dev",
        "mode": "development"
    }

# Market Data Routes
@api_router.get("/market/types/all")
async def get_all_market_types(current_user: User = Depends(AuthService.get_user_from_token)):
    """Get all available market asset types"""
    return {
        "crypto": {"name": "العملات الرقمية", "icon": "₿"},
        "stocks": {"name": "الأسهم", "icon": "$"},
        "forex": {"name": "الفوركس", "icon": "€"}
    }

@api_router.get("/market/symbols/{asset_type}")
async def get_symbols_by_type(asset_type: str, current_user: User = Depends(AuthService.get_user_from_token)):
    """Get available symbols for a specific asset type"""
    symbols_map = {
        "crypto": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"],
        "stocks": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META"],
        "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    }
    
    return {
        "asset_type": asset_type,
        "symbols": symbols_map.get(asset_type, [])
    }

# Include the API router
app.include_router(api_router)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")