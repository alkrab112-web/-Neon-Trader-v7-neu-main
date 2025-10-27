"""
Human-in-the-loop Trading Approval System
Manages proposed trades that require human approval
"""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
import uuid

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ProposedTrade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    symbol: str
    trade_type: str  # buy, sell
    order_type: str  # market, limit
    quantity: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    platform_id: str
    
    # Simulation results
    estimated_cost: float
    estimated_fees: float
    risk_assessment: Dict[str, Any]
    market_analysis: str
    
    # Approval workflow
    status: ApprovalStatus = ApprovalStatus.PENDING
    proposed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(minute=datetime.now(timezone.utc).minute + 15))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
class TradeApprovalRequest(BaseModel):
    action: str  # "approve" or "reject"
    reason: Optional[str] = None

class ApprovalSummary(BaseModel):
    total_pending: int
    total_approved_today: int
    total_rejected_today: int
    pending_value: float
    avg_approval_time_minutes: float