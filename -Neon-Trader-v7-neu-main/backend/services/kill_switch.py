"""
Kill-Switch Service
Manual and automatic emergency trading halt
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class KillSwitchReason(str, Enum):
    MANUAL = "manual"
    DAILY_DRAWDOWN = "daily_drawdown_exceeded"
    TOTAL_DRAWDOWN = "total_drawdown_exceeded"
    DATA_DELAY = "data_delay_exceeded"
    CIRCUIT_BREAKER = "circuit_breaker_triggered"
    SECURITY = "security_incident"
    SYSTEM_ERROR = "system_error"

class KillSwitchStatus(str, Enum):
    ACTIVE = "active"  # Trading allowed
    TRIGGERED = "triggered"  # Kill-switch activated
    RECOVERING = "recovering"  # In recovery mode

class KillSwitchService:
    """
    Kill-Switch Service - Emergency trading halt
    
    Features:
    - Manual activation by user
    - Automatic activation on risk violations
    - Close all open positions
    - Prevent new trades
    - Audit logging
    """
    
    def __init__(self):
        self.logger = logging.getLogger("KillSwitch")
        self.status = {}
        self.activation_history = []
    
    def is_active(self, user_id: str) -> bool:
        """Check if kill-switch is active for user"""
        return self.status.get(user_id, {}).get('status') == KillSwitchStatus.TRIGGERED
    
    async def activate(
        self,
        user_id: str,
        reason: KillSwitchReason,
        triggered_by: str = "system",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Activate kill-switch for user
        
        Steps:
        1. Set status to TRIGGERED
        2. Log activation
        3. Return instructions to close positions
        """
        
        activation_time = datetime.now(timezone.utc)
        
        activation_data = {
            "user_id": user_id,
            "status": KillSwitchStatus.TRIGGERED,
            "reason": reason.value,
            "triggered_by": triggered_by,
            "triggered_at": activation_time.isoformat(),
            "details": details or {}
        }
        
        # Store status
        self.status[user_id] = activation_data
        
        # Add to history
        self.activation_history.append(activation_data)
        
        # Log
        self.logger.critical(
            f"⚠️ KILL-SWITCH ACTIVATED for user {user_id}: {reason.value} by {triggered_by}"
        )
        
        return {
            "success": True,
            "message": "Kill-switch activated",
            "status": KillSwitchStatus.TRIGGERED.value,
            "reason": reason.value,
            "triggered_at": activation_time.isoformat(),
            "actions_required": [
                "close_all_positions",
                "freeze_new_trades",
                "notify_user"
            ]
        }
    
    async def deactivate(
        self,
        user_id: str,
        deactivated_by: str = "user",
        reason: str = "manual_reset"
    ) -> Dict[str, Any]:
        """
        Deactivate kill-switch and resume trading
        """
        
        if user_id not in self.status:
            return {
                "success": False,
                "message": "Kill-switch was not active"
            }
        
        deactivation_time = datetime.now(timezone.utc)
        
        # Update status
        self.status[user_id] = {
            "status": KillSwitchStatus.ACTIVE,
            "deactivated_at": deactivation_time.isoformat(),
            "deactivated_by": deactivated_by,
            "reason": reason
        }
        
        self.logger.info(
            f"✅ Kill-switch deactivated for user {user_id} by {deactivated_by}"
        )
        
        return {
            "success": True,
            "message": "Kill-switch deactivated, trading resumed",
            "status": KillSwitchStatus.ACTIVE.value,
            "deactivated_at": deactivation_time.isoformat()
        }
    
    def get_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get kill-switch status for user
        """
        if user_id not in self.status:
            return {
                "status": KillSwitchStatus.ACTIVE.value,
                "message": "Trading active"
            }
        
        return self.status[user_id]
    
    def get_activation_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """
        Get activation history
        """
        history = self.activation_history
        
        if user_id:
            history = [h for h in history if h['user_id'] == user_id]
        
        return history[-limit:]
    
    async def check_and_trigger_automatic(
        self,
        user_id: str,
        risk_assessment: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check risk assessment and trigger kill-switch if needed
        """
        
        # Don't retrigger if already active
        if self.is_active(user_id):
            return None
        
        # Check total drawdown (5% limit)
        if risk_assessment.get('close_all_positions', False):
            return await self.activate(
                user_id=user_id,
                reason=KillSwitchReason.TOTAL_DRAWDOWN,
                triggered_by="risk_engine",
                details={
                    "total_drawdown_percent": risk_assessment.get('total_drawdown_percent'),
                    "limit": risk_assessment.get('total_drawdown_limit')
                }
            )
        
        # Check daily drawdown (3% limit)
        if risk_assessment.get('freeze_new_trades', False):
            return await self.activate(
                user_id=user_id,
                reason=KillSwitchReason.DAILY_DRAWDOWN,
                triggered_by="risk_engine",
                details={
                    "daily_drawdown_percent": risk_assessment.get('daily_drawdown_percent'),
                    "limit": risk_assessment.get('daily_drawdown_limit')
                }
            )
        
        return None

# Global instance
kill_switch = KillSwitchService()
