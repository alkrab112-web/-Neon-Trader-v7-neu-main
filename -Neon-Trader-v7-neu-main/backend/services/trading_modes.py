"""
Trading Modes Service
Implements three operational modes: Learning-Only, Assisted, Autopilot
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TradingMode(str, Enum):
    LEARNING_ONLY = "learning_only"  # Watch and learn, no execution
    ASSISTED = "assisted"  # AI suggests, user approves
    AUTOPILOT = "autopilot"  # Fully automatic trading

class TradingModeService:
    """
    Trading Mode Manager
    
    Modes:
    1. LEARNING_ONLY: 
       - AI analyzes and generates signals
       - NO execution
       - Logs for learning and backtesting
    
    2. ASSISTED:
       - AI generates trade recommendations
       - User must approve each trade
       - Approval flow with expiry
    
    3. AUTOPILOT:
       - Full automatic execution
       - AI decides and executes
       - User can monitor and intervene
    """
    
    def __init__(self):
        self.logger = logging.getLogger("TradingModes")
        self.pending_approvals = {}
    
    async def get_user_mode(self, db, user_id: str) -> TradingMode:
        """Get user's current trading mode"""
        try:
            # Try PostgreSQL first
            from database import get_db_session
            from models.database_models import UserSettings
            
            async with get_db_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(UserSettings).where(UserSettings.user_id == user_id)
                )
                settings = result.scalar_one_or_none()
                
                if settings:
                    mode_value = getattr(settings, 'trading_mode', TradingMode.LEARNING_ONLY.value)
                    return TradingMode(mode_value)
        except:
            # Fallback to MongoDB
            try:
                settings = await db.user_settings.find_one({"user_id": user_id})
                if settings:
                    return TradingMode(settings.get('trading_mode', TradingMode.LEARNING_ONLY.value))
            except:
                pass
        
        # Default
        return TradingMode.LEARNING_ONLY
    
    async def set_user_mode(self, db, user_id: str, mode: TradingMode) -> Dict[str, Any]:
        """Set user's trading mode"""
        try:
            # Update in database
            await db.user_settings.update_one(
                {"user_id": user_id},
                {"$set": {
                    "trading_mode": mode.value,
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
            
            self.logger.info(f"User {user_id} trading mode changed to {mode.value}")
            
            return {
                "success": True,
                "mode": mode.value,
                "message": f"Trading mode set to {mode.value}"
            }
        except Exception as e:
            self.logger.error(f"Failed to set trading mode: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def should_execute_trade(
        self,
        user_id: str,
        trade_signal: Dict[str, Any],
        mode: TradingMode
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if trade should be executed based on mode
        
        Returns:
            (should_execute, reason/approval_id)
        """
        
        if mode == TradingMode.LEARNING_ONLY:
            # No execution - just log
            self.logger.info(
                f"LEARNING MODE: Trade signal logged but not executed: {trade_signal.get('symbol')}"
            )
            return (False, "learning_mode_no_execution")
        
        elif mode == TradingMode.ASSISTED:
            # Create approval request
            approval_id = f"approval_{user_id}_{int(datetime.now().timestamp())}"
            
            self.pending_approvals[approval_id] = {
                "user_id": user_id,
                "trade_signal": trade_signal,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc).timestamp() + 300,  # 5 min expiry
                "status": "pending"
            }
            
            self.logger.info(
                f"ASSISTED MODE: Trade requires approval - {approval_id}"
            )
            return (False, approval_id)
        
        elif mode == TradingMode.AUTOPILOT:
            # Execute automatically
            self.logger.info(
                f"AUTOPILOT MODE: Trade executing automatically: {trade_signal.get('symbol')}"
            )
            return (True, "autopilot_execution")
        
        return (False, "unknown_mode")
    
    async def approve_trade(self, approval_id: str, user_id: str) -> Dict[str, Any]:
        """Approve pending trade in Assisted mode"""
        
        if approval_id not in self.pending_approvals:
            return {
                "success": False,
                "error": "Approval request not found"
            }
        
        approval = self.pending_approvals[approval_id]
        
        # Check ownership
        if approval["user_id"] != user_id:
            return {
                "success": False,
                "error": "Unauthorized"
            }
        
        # Check expiry
        if datetime.now(timezone.utc).timestamp() > approval["expires_at"]:
            return {
                "success": False,
                "error": "Approval request expired"
            }
        
        # Mark as approved
        approval["status"] = "approved"
        approval["approved_at"] = datetime.now(timezone.utc)
        
        self.logger.info(f"Trade approved: {approval_id}")
        
        return {
            "success": True,
            "trade_signal": approval["trade_signal"],
            "message": "Trade approved for execution"
        }
    
    async def reject_trade(self, approval_id: str, user_id: str, reason: str = "") -> Dict[str, Any]:
        """Reject pending trade in Assisted mode"""
        
        if approval_id not in self.pending_approvals:
            return {
                "success": False,
                "error": "Approval request not found"
            }
        
        approval = self.pending_approvals[approval_id]
        
        # Check ownership
        if approval["user_id"] != user_id:
            return {
                "success": False,
                "error": "Unauthorized"
            }
        
        # Mark as rejected
        approval["status"] = "rejected"
        approval["rejected_at"] = datetime.now(timezone.utc)
        approval["rejection_reason"] = reason
        
        self.logger.info(f"Trade rejected: {approval_id} - {reason}")
        
        return {
            "success": True,
            "message": "Trade rejected"
        }
    
    async def get_pending_approvals(self, user_id: str) -> list:
        """Get all pending approval requests for user"""
        
        pending = []
        current_time = datetime.now(timezone.utc).timestamp()
        
        for approval_id, approval in self.pending_approvals.items():
            if approval["user_id"] == user_id and approval["status"] == "pending":
                # Check if expired
                if current_time > approval["expires_at"]:
                    approval["status"] = "expired"
                    continue
                
                pending.append({
                    "approval_id": approval_id,
                    "trade_signal": approval["trade_signal"],
                    "created_at": approval["created_at"].isoformat(),
                    "expires_in_seconds": int(approval["expires_at"] - current_time)
                })
        
        return pending
    
    def get_mode_description(self, mode: TradingMode) -> Dict[str, Any]:
        """Get detailed description of trading mode"""
        
        descriptions = {
            TradingMode.LEARNING_ONLY: {
                "name": "التعلم فقط",
                "name_en": "Learning Only",
                "description": "يراقب السوق ويحلل الفرص دون تنفيذ أي صفقات",
                "description_en": "Watches market and analyzes opportunities without executing trades",
                "features": [
                    "تحليل السوق المستمر",
                    "توليد إشارات التداول",
                    "تسجيل البيانات للتعلم",
                    "لا يوجد تنفيذ للصفقات"
                ],
                "risk_level": "zero",
                "requires_approval": False,
                "auto_execute": False
            },
            TradingMode.ASSISTED: {
                "name": "المساعدة",
                "name_en": "Assisted",
                "description": "يقترح الذكاء الاصطناعي الصفقات وتحتاج موافقتك للتنفيذ",
                "description_en": "AI suggests trades, requires your approval to execute",
                "features": [
                    "توصيات ذكية من AI",
                    "مراجعة يدوية لكل صفقة",
                    "موافقة قبل التنفيذ",
                    "تحكم كامل"
                ],
                "risk_level": "controlled",
                "requires_approval": True,
                "auto_execute": False
            },
            TradingMode.AUTOPILOT: {
                "name": "الطيار الآلي",
                "name_en": "Autopilot",
                "description": "تنفيذ تلقائي كامل للصفقات بناءً على استراتيجية الذكاء الاصطناعي",
                "description_en": "Full automatic trade execution based on AI strategy",
                "features": [
                    "تنفيذ تلقائي كامل",
                    "لا حاجة للموافقة",
                    "استجابة فورية للسوق",
                    "إدارة مخاطر صارمة"
                ],
                "risk_level": "managed",
                "requires_approval": False,
                "auto_execute": True,
                "warning": "⚠️ يتطلب إدارة مخاطر نشطة ومراقبة مستمرة"
            }
        }
        
        return descriptions.get(mode, {})

# Global instance
trading_mode_service = TradingModeService()
