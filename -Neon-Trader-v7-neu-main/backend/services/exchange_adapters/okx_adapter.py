"""
OKX Exchange Adapter
Real integration with OKX API using CCXT
"""

import ccxt.async_support as ccxt
from typing import Dict, List, Optional, Any
import logging
from .base_adapter import BaseExchangeAdapter, ExchangeError

class OKXAdapter(BaseExchangeAdapter):
    """OKX exchange adapter with full trading capabilities"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, passphrase, testnet)
        self.exchange_name = "OKX"
        self.logger = logging.getLogger("OKXAdapter")
    
    async def connect(self) -> bool:
        """Connect to OKX"""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'password': self.passphrase,  # OKX requires passphrase
                'enableRateLimit': True,
            }
            
            if self.testnet:
                config['sandbox'] = True
            
            self.exchange = ccxt.okx(config)
            await self.exchange.load_markets()
            
            self.logger.info(f"Connected to {self.exchange_name} {'TESTNET' if self.testnet else 'LIVE'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to OKX: {e}")
            raise ExchangeError(f"OKX connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        try:
            if self.exchange:
                await self.exchange.close()
            self.logger.info("Disconnected from OKX")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        try:
            if not self.exchange:
                await self.connect()
            
            server_time = await self.exchange.fetch_time()
            balance = await self.exchange.fetch_balance()
            
            return {
                'success': True,
                'exchange': self.exchange_name,
                'testnet': self.testnet,
                'server_time': server_time,
                'account_active': True
            }
        except Exception as e:
            return {'success': False, 'exchange': self.exchange_name, 'error': str(e)}
    
    async def get_balance(self) -> Dict[str, Any]:
        try:
            if not self.exchange:
                await self.connect()
            balance = await self.exchange.fetch_balance()
            return self._standardize_balance(balance)
        except Exception as e:
            raise ExchangeError(f"Get balance failed: {str(e)}")
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        try:
            if not self.exchange:
                await self.connect()
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'change_24h': ticker.get('percentage', 0),
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            raise ExchangeError(f"Get ticker failed: {str(e)}")
    
    async def create_order(
        self, symbol: str, order_type: str, side: str,
        amount: float, price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        try:
            if not self.exchange:
                await self.connect()
            
            order = await self.exchange.create_order(
                symbol, order_type, side, amount, price, params or {}
            )
            self.logger.info(f"Order created on OKX: {order['id']}")
            return self._standardize_order(order)
        except Exception as e:
            raise ExchangeError(f"Create order failed: {str(e)}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        try:
            if not self.exchange:
                await self.connect()
            result = await self.exchange.cancel_order(order_id, symbol)
            return result
        except Exception as e:
            raise ExchangeError(f"Cancel order failed: {str(e)}")
    
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        try:
            if not self.exchange:
                await self.connect()
            order = await self.exchange.fetch_order(order_id, symbol)
            return self._standardize_order(order)
        except Exception as e:
            raise ExchangeError(f"Get order status failed: {str(e)}")
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            if not self.exchange:
                await self.connect()
            orders = await self.exchange.fetch_open_orders(symbol)
            return [self._standardize_order(order) for order in orders]
        except Exception as e:
            raise ExchangeError(f"Get open orders failed: {str(e)}")
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if not self.exchange:
                await self.connect()
            if symbol:
                trades = await self.exchange.fetch_my_trades(symbol, limit=limit)
            else:
                trades = []
            return trades
        except Exception as e:
            raise ExchangeError(f"Get trade history failed: {str(e)}")
