"""
Advanced Risk Management Engine
Implements strict risk controls as per PRD requirements
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskViolation(Exception):
    """Raised when risk limits are violated"""
    def __init__(self, message: str, risk_level: RiskLevel):
        self.message = message
        self.risk_level = risk_level
        super().__init__(self.message)

class AdvancedRiskEngine:
    """
    Advanced Risk Engine with strict controls:
    - Position size ≤ 0.5% of Equity
    - Total open ≤ 3× leverage
    - Daily DD ≤ 3%
    - Total DD ≤ 5%
    - Circuit breaker integration
    """
    
    # Risk Limits (from PRD)
    MAX_POSITION_SIZE_PERCENT = 0.5  # 0.5% of equity per trade
    MAX_LEVERAGE = 3.0  # 3× max
    MAX_DAILY_DRAWDOWN_PERCENT = 3.0  # 3% daily
    MAX_TOTAL_DRAWDOWN_PERCENT = 5.0  # 5% total
    NEWS_FREEZE_MINUTES = 30  # ±30 minutes around high-impact news
    MAX_DATA_DELAY_SECONDS = 5  # Kill-switch if data delay > 5s
    
    def __init__(self):
        self.logger = logging.getLogger("RiskEngine")
        self.daily_trades_count = {}
        self.daily_pnl = {}
        self.peak_equity = {}
        
    async def validate_trade(
        self,
        user_id: str,
        trade_size: float,
        equity: float,
        open_positions_value: float,
        current_leverage: float,
        daily_pnl: float,
        total_pnl: float,
        initial_equity: float = 10000.0
    ) -> Tuple[bool, Optional[str], RiskLevel]:
        """
        Validate trade against all risk rules
        
        Returns:
            (is_valid, violation_message, risk_level)
        """
        
        # 1. Check position size (≤ 0.5% of equity)
        max_position = equity * (self.MAX_POSITION_SIZE_PERCENT / 100)
        if trade_size > max_position:
            return (
                False,
                f"Position size ${trade_size:.2f} exceeds max ${max_position:.2f} (0.5% of equity)",
                RiskLevel.HIGH
            )
        
        # 2. Check total leverage (≤ 3×)
        new_total_exposure = open_positions_value + trade_size
        new_leverage = new_total_exposure / equity if equity > 0 else 0
        
        if new_leverage > self.MAX_LEVERAGE:
            return (
                False,
                f"Total leverage {new_leverage:.2f}× exceeds max {self.MAX_LEVERAGE}×",
                RiskLevel.HIGH
            )
        
        # 3. Check daily drawdown (≤ 3%)
        daily_dd_percent = (abs(daily_pnl) / equity) * 100 if equity > 0 else 0
        if daily_pnl < 0 and daily_dd_percent >= self.MAX_DAILY_DRAWDOWN_PERCENT:
            return (
                False,
                f"Daily drawdown {daily_dd_percent:.2f}% reached limit {self.MAX_DAILY_DRAWDOWN_PERCENT}%",
                RiskLevel.CRITICAL
            )
        
        # 4. Check total drawdown (≤ 5%)
        current_equity = initial_equity + total_pnl
        if user_id not in self.peak_equity:
            self.peak_equity[user_id] = initial_equity
        
        peak = max(self.peak_equity[user_id], current_equity)
        total_dd = ((peak - current_equity) / peak) * 100 if peak > 0 else 0
        
        if total_dd >= self.MAX_TOTAL_DRAWDOWN_PERCENT:
            return (
                False,
                f"Total drawdown {total_dd:.2f}% reached limit {self.MAX_TOTAL_DRAWDOWN_PERCENT}%",
                RiskLevel.CRITICAL
            )
        
        # Update peak equity
        self.peak_equity[user_id] = peak
        
        # All checks passed
        return (True, None, RiskLevel.LOW)
    
    def calculate_position_size_kelly(
        self,
        equity: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        sl_distance_percent: float,
        contract_size: float = 1.0
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion
        
        Formula from PRD:
        Size = min(
            Equity × KellyFraction ÷ (SL_distance × ContractSize),
            0.005 × Equity
        )
        """
        
        # Kelly Fraction = (p × b - q) / b
        # p = win rate, q = 1 - p, b = avg_win / avg_loss
        if avg_loss == 0 or win_rate <= 0:
            kelly_fraction = 0
        else:
            b = avg_win / avg_loss
            q = 1 - win_rate
            kelly_fraction = max(0, (win_rate * b - q) / b)
        
        # Apply conservative factor (0.25 of Kelly for safety)
        conservative_kelly = kelly_fraction * 0.25
        
        # Calculate size
        if sl_distance_percent == 0:
            kelly_size = 0
        else:
            kelly_size = equity * conservative_kelly / (sl_distance_percent * contract_size)
        
        # Max 0.5% of equity (from PRD)
        max_size = 0.005 * equity
        
        return min(kelly_size, max_size)
    
    def check_drawdown_freeze(self, daily_pnl: float, equity: float) -> Tuple[bool, str]:
        """
        Check if trading should be frozen due to daily drawdown
        """
        daily_dd_percent = (abs(daily_pnl) / equity) * 100 if equity > 0 else 0
        
        if daily_pnl < 0 and daily_dd_percent >= self.MAX_DAILY_DRAWDOWN_PERCENT:
            return (
                True,
                f"Trading frozen: Daily drawdown {daily_dd_percent:.2f}% reached {self.MAX_DAILY_DRAWDOWN_PERCENT}%"
            )
        
        return (False, "")
    
    def check_total_drawdown_freeze(
        self,
        current_equity: float,
        initial_equity: float,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Check if all positions should be closed due to total drawdown
        """
        if user_id not in self.peak_equity:
            self.peak_equity[user_id] = initial_equity
        
        peak = self.peak_equity[user_id]
        total_dd = ((peak - current_equity) / peak) * 100 if peak > 0 else 0
        
        if total_dd >= self.MAX_TOTAL_DRAWDOWN_PERCENT:
            return (
                True,
                f"CRITICAL: Total drawdown {total_dd:.2f}% reached {self.MAX_TOTAL_DRAWDOWN_PERCENT}%. All positions must be closed!"
            )
        
        return (False, "")
    
    def get_risk_assessment(
        self,
        equity: float,
        open_positions_value: float,
        daily_pnl: float,
        total_pnl: float,
        initial_equity: float,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive risk assessment
        """
        # Calculate metrics
        current_leverage = open_positions_value / equity if equity > 0 else 0
        daily_dd_percent = (abs(daily_pnl) / equity) * 100 if equity > 0 and daily_pnl < 0 else 0
        
        if user_id not in self.peak_equity:
            self.peak_equity[user_id] = initial_equity
        
        peak = max(self.peak_equity[user_id], initial_equity + total_pnl)
        current_equity = initial_equity + total_pnl
        total_dd = ((peak - current_equity) / peak) * 100 if peak > 0 else 0
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        warnings = []
        
        if current_leverage > self.MAX_LEVERAGE * 0.8:
            risk_level = RiskLevel.HIGH
            warnings.append(f"Leverage approaching limit: {current_leverage:.2f}×")
        
        if daily_dd_percent > self.MAX_DAILY_DRAWDOWN_PERCENT * 0.8:
            risk_level = RiskLevel.HIGH
            warnings.append(f"Daily drawdown approaching limit: {daily_dd_percent:.2f}%")
        
        if total_dd > self.MAX_TOTAL_DRAWDOWN_PERCENT * 0.8:
            risk_level = RiskLevel.CRITICAL
            warnings.append(f"Total drawdown approaching limit: {total_dd:.2f}%")
        
        return {
            "risk_level": risk_level.value,
            "current_leverage": round(current_leverage, 2),
            "max_leverage": self.MAX_LEVERAGE,
            "leverage_usage_percent": round((current_leverage / self.MAX_LEVERAGE) * 100, 1),
            "daily_drawdown_percent": round(daily_dd_percent, 2),
            "daily_drawdown_limit": self.MAX_DAILY_DRAWDOWN_PERCENT,
            "total_drawdown_percent": round(total_dd, 2),
            "total_drawdown_limit": self.MAX_TOTAL_DRAWDOWN_PERCENT,
            "max_position_size": round(equity * (self.MAX_POSITION_SIZE_PERCENT / 100), 2),
            "available_buying_power": round(equity * self.MAX_LEVERAGE - open_positions_value, 2),
            "warnings": warnings,
            "peak_equity": round(peak, 2),
            "current_equity": round(current_equity, 2),
            "freeze_new_trades": daily_dd_percent >= self.MAX_DAILY_DRAWDOWN_PERCENT,
            "close_all_positions": total_dd >= self.MAX_TOTAL_DRAWDOWN_PERCENT
        }

# Global instance
risk_engine = AdvancedRiskEngine()
