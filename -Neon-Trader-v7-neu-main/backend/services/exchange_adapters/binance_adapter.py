"""
Binance Exchange Adapter
Real integration with Binance API using CCXT
"""

import ccxt.async_support as ccxt
from typing import Dict, List, Optional, Any
import logging
from .base_adapter import BaseExchangeAdapter, ExchangeError

class BinanceAdapter(BaseExchangeAdapter):
    """Binance exchange adapter with full trading capabilities"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None, testnet: bool = True):
        super().__init__(api_key, api_secret, passphrase, testnet)
        self.exchange_name = "Binance"
        self.logger = logging.getLogger("BinanceAdapter")
    
    async def connect(self) -> bool:
        """Connect to Binance"""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # spot, future, margin
                }
            }
            
            # Set testnet if enabled
            if self.testnet:
                config['sandbox'] = True
                # Binance testnet URL
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
            
            self.exchange = ccxt.binance(config)
            await self.exchange.load_markets()
            
            self.logger.info(f"Connected to {self.exchange_name} {'TESTNET' if self.testnet else 'LIVE'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance: {e}")
            raise ExchangeError(f"Binance connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance"""
        try:
            if self.exchange:
                await self.exchange.close()
            self.logger.info("Disconnected from Binance")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from Binance: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Binance"""
        try:
            if not self.exchange:
                await self.connect()
            
            # Test by fetching server time
            server_time = await self.exchange.fetch_time()
            balance = await self.exchange.fetch_balance()
            
            return {
                'success': True,
                'exchange': self.exchange_name,
                'testnet': self.testnet,
                'server_time': server_time,
                'account_active': True,
                'balance_accessible': True
            }
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'exchange': self.exchange_name,
                'error': str(e)
            }
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance from Binance"""
        try:
            if not self.exchange:
                await self.connect()
            
            balance = await self.exchange.fetch_balance()
            return self._standardize_balance(balance)
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            raise ExchangeError(f"Get balance failed: {str(e)}")
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for symbol"""
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
                'change_24h': ticker['percentage'],
                'timestamp': ticker['timestamp']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise ExchangeError(f"Get ticker failed: {str(e)}")
    
    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create new order on Binance"""
        try:
            if not self.exchange:
                await self.connect()
            
            # Validate order type
            if order_type not in ['market', 'limit']:
                raise ExchangeError(f"Invalid order type: {order_type}")
            
            # Validate side
            if side not in ['buy', 'sell']:
                raise ExchangeError(f"Invalid side: {side}")
            
            # Create order
            order = await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params or {}
            )
            
            self.logger.info(f"Order created: {order['id']} - {side} {amount} {symbol} @ {price or 'market'}")
            return self._standardize_order(order)
            
        except Exception as e:
            self.logger.error(f"Failed to create order: {e}")
            raise ExchangeError(f"Create order failed: {str(e)}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel existing order"""
        try:
            if not self.exchange:
                await self.connect()
            
            result = await self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Order cancelled: {order_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            raise ExchangeError(f"Cancel order failed: {str(e)}")
    
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status"""
        try:
            if not self.exchange:
                await self.connect()
            
            order = await self.exchange.fetch_order(order_id, symbol)
            return self._standardize_order(order)
            
        except Exception as e:
            self.logger.error(f"Failed to get order status for {order_id}: {e}")
            raise ExchangeError(f"Get order status failed: {str(e)}")
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders"""
        try:
            if not self.exchange:
                await self.connect()
            
            orders = await self.exchange.fetch_open_orders(symbol)
            return [self._standardize_order(order) for order in orders]
            
        except Exception as e:
            self.logger.error(f"Failed to get open orders: {e}")
            raise ExchangeError(f"Get open orders failed: {str(e)}")
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trade history"""
        try:
            if not self.exchange:
                await self.connect()
            
            if symbol:
                trades = await self.exchange.fetch_my_trades(symbol, limit=limit)
            else:
                # Get trades for all symbols (Binance limitation: need to specify symbol)
                trades = []
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Failed to get trade history: {e}")
            raise ExchangeError(f"Get trade history failed: {str(e)}")
    
    async def get_deposit_address(self, currency: str) -> Dict[str, Any]:
        """Get deposit address for currency"""
        try:
            if not self.exchange:
                await self.connect()
            
            address = await self.exchange.fetch_deposit_address(currency)
            return address
            
        except Exception as e:
            self.logger.error(f"Failed to get deposit address for {currency}: {e}")
            raise ExchangeError(f"Get deposit address failed: {str(e)}")
    
    async def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get trading fees"""
        try:
            if not self.exchange:
                await self.connect()
            
            fees = await self.exchange.fetch_trading_fees()
            
            if symbol:
                return fees.get(symbol, {})
            return fees
            
        except Exception as e:
            self.logger.error(f"Failed to get trading fees: {e}")
            raise ExchangeError(f"Get trading fees failed: {str(e)}")
