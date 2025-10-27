"""
Neon Trader V7 - WebSocket Manager
Real-time data broadcasting and connection management
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime, timezone
import uuid

class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.symbol_subscribers: Dict[str, Set[str]] = {}  # symbol -> connection_ids
        self.notification_subscribers: Set[str] = set()
        self.trade_subscribers: Set[str] = set()
        
    async def connect(self, websocket: WebSocket, connection_id: str | None = None):
        """Accept new WebSocket connection"""
        if not connection_id:
            connection_id = str(uuid.uuid4())
            
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        logging.info(f"WebSocket connected: {connection_id}")
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove connection and clean up subscriptions"""
        if connection_id in self.active_connections:
            # Remove from all subscriptions
            self._cleanup_subscriptions(connection_id)
            
            # Remove connection
            del self.active_connections[connection_id]
            logging.info(f"WebSocket disconnected: {connection_id}")
    
    def _cleanup_subscriptions(self, connection_id: str):
        """Clean up all subscriptions for a connection"""
        # Remove from user connections
        for user_id, connections in self.user_connections.items():
            connections.discard(connection_id)
            
        # Remove from symbol subscriptions
        for symbol, connections in self.symbol_subscribers.items():
            connections.discard(connection_id)
            
        # Remove from notification subscribers
        self.notification_subscribers.discard(connection_id)
        
        # Remove from trade subscribers
        self.trade_subscribers.discard(connection_id)
    
    def associate_user(self, connection_id: str, user_id: str):
        """Associate connection with authenticated user"""
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logging.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_user_message(self, message: dict, user_id: str):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            connections = self.user_connections[user_id].copy()
            for connection_id in connections:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_to_subscribers(self, message: dict, subscriber_set: Set[str]):
        """Broadcast message to a set of subscribers"""
        if not subscriber_set:
            return
            
        disconnected = []
        for connection_id in subscriber_set.copy():
            try:
                if connection_id in self.active_connections:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_text(json.dumps(message))
                else:
                    disconnected.append(connection_id)
            except Exception as e:
                logging.error(f"Broadcast failed to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            subscriber_set.discard(connection_id)
    
    async def broadcast_price_update(self, symbol: str, price_data: dict):
        """Broadcast price update to symbol subscribers"""
        if symbol in self.symbol_subscribers:
            message = {
                "type": "price_update",
                "data": price_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.broadcast_to_subscribers(message, self.symbol_subscribers[symbol])
    
    async def broadcast_trade_update(self, user_id: str, trade_data: dict):
        """Broadcast trade update to user's connections"""
        message = {
            "type": "trade_update", 
            "data": trade_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.send_user_message(message, user_id)
    
    async def broadcast_notification(self, user_id: str, notification: dict):
        """Send notification to specific user"""
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.send_user_message(message, user_id)
    
    async def broadcast_system_status(self, status_data: dict):
        """Broadcast system status to all connections"""
        message = {
            "type": "system_status",
            "data": status_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Send to all active connections
        for connection_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, connection_id)
    
    def subscribe_to_symbol(self, connection_id: str, symbol: str):
        """Subscribe connection to symbol price updates"""
        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = set()
        self.symbol_subscribers[symbol].add(connection_id)
        logging.info(f"Connection {connection_id} subscribed to {symbol}")
    
    def unsubscribe_from_symbol(self, connection_id: str, symbol: str):
        """Unsubscribe connection from symbol updates"""
        if symbol in self.symbol_subscribers:
            self.symbol_subscribers[symbol].discard(connection_id)
            logging.info(f"Connection {connection_id} unsubscribed from {symbol}")
    
    def subscribe_to_notifications(self, connection_id: str):
        """Subscribe to notifications"""
        self.notification_subscribers.add(connection_id)
    
    def subscribe_to_trades(self, connection_id: str):
        """Subscribe to trade updates"""
        self.trade_subscribers.add(connection_id)
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "authenticated_users": len(self.user_connections),
            "symbol_subscriptions": len(self.symbol_subscribers),
            "notification_subscribers": len(self.notification_subscribers),
            "trade_subscribers": len(self.trade_subscribers)
        }

# Global connection manager instance
manager = ConnectionManager()

class WebSocketHandler:
    """Handles WebSocket message processing"""
    
    @staticmethod
    async def handle_message(websocket: WebSocket, connection_id: str, message_data: dict):
        """Process incoming WebSocket messages"""
        try:
            message_type = message_data.get("type")
            
            if message_type == "authenticate":
                await WebSocketHandler._handle_authentication(connection_id, message_data)
                
            elif message_type == "subscribe":
                await WebSocketHandler._handle_subscription(connection_id, message_data)
                
            elif message_type == "unsubscribe":
                await WebSocketHandler._handle_unsubscription(connection_id, message_data)
                
            elif message_type == "ping":
                await WebSocketHandler._handle_ping(connection_id)
                
            else:
                logging.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logging.error(f"Message handling error: {e}")
    
    @staticmethod
    async def _handle_authentication(connection_id: str, message_data: dict):
        """Handle user authentication with real JWT verification"""
        token = message_data.get("token")
        if token:
            try:
                # Import JWT verification from server
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from server import AuthService, User
                from motor.motor_asyncio import AsyncIOMotorClient
                import os
                from dotenv import load_dotenv
                
                # Load environment
                load_dotenv()
                
                # Verify JWT token
                from fastapi import HTTPException
                from fastapi.security import HTTPBearer
                from jose import jwt
                
                # Extract user from token
                JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback_secret_key')
                JWT_ALGORITHM = "HS256"
                
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("sub")
                
                if user_id:
                    manager.associate_user(connection_id, user_id)
                    
                    response = {
                        "type": "authenticated",
                        "data": {"status": "success", "user_id": user_id},
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.send_personal_message(response, connection_id)
                else:
                    raise HTTPException(status_code=401, detail="Invalid token")
                
            except Exception as e:
                logging.error(f"WebSocket authentication failed: {e}")
                error_response = {
                    "type": "auth_error",
                    "data": {"error": "Authentication failed", "detail": str(e)},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_personal_message(error_response, connection_id)
    
    @staticmethod
    async def _handle_subscription(connection_id: str, message_data: dict):
        """Handle subscription requests"""
        channel = message_data.get("channel")
        
        if channel == "price_updates":
            symbol = message_data.get("symbol")
            if symbol:
                manager.subscribe_to_symbol(connection_id, symbol)
                
        elif channel == "notifications":
            manager.subscribe_to_notifications(connection_id)
            
        elif channel == "trade_updates":
            manager.subscribe_to_trades(connection_id)
        
        # Send confirmation
        response = {
            "type": "subscribed",
            "data": {"channel": channel, "symbol": message_data.get("symbol")},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await manager.send_personal_message(response, connection_id)
    
    @staticmethod
    async def _handle_unsubscription(connection_id: str, message_data: dict):
        """Handle unsubscription requests"""
        channel = message_data.get("channel")
        
        if channel == "price_updates":
            symbol = message_data.get("symbol")
            if symbol:
                manager.unsubscribe_from_symbol(connection_id, symbol)
        
        # Send confirmation
        response = {
            "type": "unsubscribed",
            "data": {"channel": channel, "symbol": message_data.get("symbol")},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await manager.send_personal_message(response, connection_id)
    
    @staticmethod
    async def _handle_ping(connection_id: str):
        """Handle ping messages"""
        pong_response = {
            "type": "pong",
            "data": {"timestamp": datetime.now(timezone.utc).isoformat()},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await manager.send_personal_message(pong_response, connection_id)

# Background task for real market data broadcasting
async def market_data_broadcaster():
    """Background task to broadcast real market data"""
    from services.exchange_service import market_data_service
    
    while True:
        try:
            # Fetch real price updates for subscribed symbols
            for symbol in list(manager.symbol_subscribers.keys()):
                try:
                    # Get real market data
                    market_data = await market_data_service.get_market_price_with_fallback(symbol)
                    
                    price_data = {
                        "symbol": symbol,
                        "price": market_data.get('price', 0),
                        "change": market_data.get('change_24h', 0),
                        "change_percent": market_data.get('change_24h_percent', market_data.get('change_24h', 0)),
                        "volume": market_data.get('volume_24h', 0),
                        "high_24h": market_data.get('high_24h', 0),
                        "low_24h": market_data.get('low_24h', 0),
                        "source": market_data.get('source', 'unknown'),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await manager.broadcast_price_update(symbol, price_data)
                except Exception as e:
                    logging.error(f"Failed to fetch market data for {symbol}: {e}")
                    # Send fallback data
                    import random
                    fallback_data = {
                        "symbol": symbol,
                        "price": random.uniform(1000, 50000),
                        "change": random.uniform(-5, 5),
                        "change_percent": random.uniform(-2, 2),
                        "volume": random.randint(100000, 5000000),
                        "source": "fallback",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.broadcast_price_update(symbol, fallback_data)
            
            # Wait 30 seconds before next update (respect API rate limits)
            await asyncio.sleep(30)
            
        except Exception as e:
            logging.error(f"Market data broadcaster error: {e}")
            await asyncio.sleep(60)