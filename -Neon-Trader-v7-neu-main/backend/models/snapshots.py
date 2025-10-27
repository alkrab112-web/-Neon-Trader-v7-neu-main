"""
Portfolio Snapshots Model
Tracks portfolio history for analysis and reporting
"""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid

class PortfolioSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_balance: float
    available_balance: float
    invested_balance: float
    daily_pnl: float
    total_pnl: float
    assets: Dict[str, Any] = Field(default_factory=dict)
    positions: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SnapshotRequest(BaseModel):
    total_balance: float
    available_balance: float
    invested_balance: float
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    assets: Optional[Dict[str, Any]] = None
    positions: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class SnapshotAnalysis(BaseModel):
    period: str  # "1d", "7d", "30d", "90d"
    balance_change: float
    balance_change_percent: float
    pnl_change: float
    best_performing_asset: Optional[str] = None
    worst_performing_asset: Optional[str] = None
    total_trades: int
    win_rate: float
    avg_daily_return: float