"""
Base Exchange Adapter
Defines common interface for all exchange adapters
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

class ExchangeError(Exception):
    """Custom exception for exchange-related errors"""
    pass

class BaseExchangeAdapter(ABC):
    """Base class for exchange adapters"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.testnet = testnet
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from exchange"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to exchange"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for symbol"""
        pass
    
    @abstractmethod
    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create new order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel existing order"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders"""
        pass
    
    @abstractmethod
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trade history"""
        pass
    
    def _standardize_order(self, raw_order: Dict) -> Dict[str, Any]:
        """Standardize order format across exchanges"""
        return {
            'id': raw_order.get('id'),
            'symbol': raw_order.get('symbol'),
            'type': raw_order.get('type'),
            'side': raw_order.get('side'),
            'price': raw_order.get('price'),
            'amount': raw_order.get('amount'),
            'filled': raw_order.get('filled', 0),
            'remaining': raw_order.get('remaining', 0),
            'status': raw_order.get('status'),
            'timestamp': raw_order.get('timestamp'),
            'datetime': raw_order.get('datetime'),
        }
    
    def _standardize_balance(self, raw_balance: Dict) -> Dict[str, Any]:
        """Standardize balance format"""
        return {
            'total': raw_balance.get('total', {}),
            'free': raw_balance.get('free', {}),
            'used': raw_balance.get('used', {}),
            'timestamp': datetime.utcnow().isoformat()
        }
