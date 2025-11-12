"""
SQLAlchemy ORM Models for PostgreSQL
Defines all database tables and relationships
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, ForeignKey, Enum, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid
import enum
from database import Base

# Enums
class TradeType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class TradeStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    PENDING = "pending"

class PlatformStatus(str, enum.Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Two-Factor Authentication
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    backup_codes = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    platforms = relationship("Platform", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # UI Preferences
    theme = Column(String(50), default="dark")
    language = Column(String(10), default="ar")
    timezone = Column(String(50), default="UTC")
    
    # Notification Settings
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    trade_alerts = Column(Boolean, default=True)
    
    # Trading Settings
    default_risk_level = Column(String(20), default="medium")
    auto_trading_enabled = Column(Boolean, default=False)
    
    # Privacy Settings
    show_balance = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="settings")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Balances
    total_balance = Column(Float, default=10000.0)
    available_balance = Column(Float, default=10000.0)
    invested_balance = Column(Float, default=0.0)
    
    # Performance Metrics
    daily_pnl = Column(Float, default=0.0)
    weekly_pnl = Column(Float, default=0.0)
    monthly_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    
    # Risk Metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id = Column(String(36), ForeignKey("platforms.id", ondelete="SET NULL"), nullable=True)
    
    # Trade Details
    platform = Column(String(100), nullable=False)  # Name of platform used
    symbol = Column(String(50), nullable=False, index=True)
    trade_type = Column(Enum(TradeType), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    
    # Quantities and Prices
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    
    # Risk Management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Status and PnL
    status = Column(Enum(TradeStatus), nullable=False, default=TradeStatus.OPEN, index=True)
    pnl = Column(Float, default=0.0)
    
    # Execution Details
    execution_type = Column(String(20), default="paper")  # paper, real, simulated
    exchange_order_id = Column(String(255), nullable=True)  # External order ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trades")
    platform_rel = relationship("Platform", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_symbol_status', 'symbol', 'status'),
    )

class Platform(Base):
    __tablename__ = "platforms"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Platform Details
    name = Column(String(100), nullable=False)
    platform_type = Column(String(50), nullable=False)  # binance, bybit, okx, etc.
    
    # API Keys (Encrypted)
    api_key_encrypted = Column(Text, nullable=True)
    secret_key_encrypted = Column(Text, nullable=True)
    passphrase_encrypted = Column(Text, nullable=True)
    
    # Configuration
    is_testnet = Column(Boolean, default=True)
    status = Column(Enum(PlatformStatus), default=PlatformStatus.DISCONNECTED)
    
    # Connection Details
    last_connected = Column(DateTime(timezone=True), nullable=True)
    connection_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="platforms")
    trades = relationship("Trade", back_populates="platform_rel")

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String(36), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Snapshot Data
    total_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    invested_balance = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    
    # Asset Distribution
    assets = Column(JSON, nullable=True)  # {"crypto": 5000, "stocks": 3000}
    positions = Column(JSON, nullable=True)  # List of open positions
    metadata = Column(JSON, nullable=True)  # Additional data
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    symbol = Column(String(50), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # buy, sell, hold
    confidence = Column(String(20), nullable=False)  # high, medium, low
    confidence_score = Column(Float, nullable=True)  # 0-100
    
    reason = Column(Text, nullable=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    # AI Model Info
    model_used = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    
    # Outcome Tracking
    was_followed = Column(Boolean, default=False)
    actual_outcome = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

class DailyPlan(Base):
    __tablename__ = "daily_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    market_analysis = Column(Text, nullable=False)
    trading_strategy = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)
    
    opportunities = Column(JSON, nullable=True)  # List of trading opportunities
    warnings = Column(JSON, nullable=True)  # List of warnings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'date'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(36), nullable=True)
    
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_action_timestamp', 'action', 'timestamp'),
    )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False)

# New tables from PRD
class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    model_uri = Column(String(500), nullable=True)  # MLflow model URI
    config_json = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_backtested = Column(Boolean, default=False)
    
    # Performance
    win_rate = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    signals = relationship("Signal", back_populates="strategy", cascade="all, delete-orphan")
    metrics = relationship("ModelMetric", back_populates="strategy", cascade="all, delete-orphan")

class ModelMetric(Base):
    __tablename__ = "model_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Performance Metrics
    sharpe_ratio = Column(Float, nullable=False)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    
    # Additional Metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    avg_win = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    
    # Timeframe
    evaluation_period_days = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="metrics")

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Signal Details
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    size = Column(Float, nullable=False)
    
    # Price Targets
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Confidence
    score = Column(Float, nullable=False)  # 0-100
    confidence = Column(String(20), nullable=True)  # low, medium, high
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, executed, expired
    
    # Execution
    executed_trade_id = Column(String(36), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="signals")
    
    __table_args__ = (
        Index('idx_signal_status', 'status', 'timestamp'),
    )
