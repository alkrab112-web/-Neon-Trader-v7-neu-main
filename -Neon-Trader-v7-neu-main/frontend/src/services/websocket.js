/**
 * Neon Trader V7 - WebSocket Service
 * Real-time market data and trading updates
 */

// WebSocket types will be handled as plain objects

export class WebSocketService {
  static instance;
  ws = null;
  reconnectAttempts = 0;
  maxReconnectAttempts = 5;
  reconnectInterval = 5000;
  listeners = new Map();
  heartbeatInterval = null;
  
  constructor() {}

  static getInstance() {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  connect(token) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      // Use secure WebSocket for production
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      
      // Send authentication token if provided
      if (token) {
        this.ws.onopen = () => {
          this.send({ type: 'authenticate', token });
          this.handleOpen();
        };
      }
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.scheduleReconnect();
    }
  }

  private handleOpen(): void {
    console.log('✅ WebSocket connected successfully');
    this.reconnectAttempts = 0;
    this.startHeartbeat();
    this.emit('connected', { status: 'connected' });
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WSMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'price_update':
          this.emit('price_update', message.data as PriceUpdate);
          break;
          
        case 'trade_update':
          this.emit('trade_update', message.data);
          break;
          
        case 'notification':
          this.emit('notification', message.data as Notification);
          break;
          
        case 'system_status':
          this.emit('system_status', message.data);
          break;
          
        default:
          this.emit('message', message);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.stopHeartbeat();
    this.emit('disconnected', { code: event.code, reason: event.reason });
    
    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.emit('error', event);
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('max_reconnect_attempts', null);
      return;
    }

    this.reconnectAttempts++;
    console.log(`Reconnecting in ${this.reconnectInterval}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, this.reconnectInterval * this.reconnectAttempts);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() });
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  public send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }

  public subscribe(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  public unsubscribe(event: string, callback: Function): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  private emit(event: string, data: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  public subscribeToSymbol(symbol: string): void {
    this.send({
      type: 'subscribe',
      channel: 'price_updates',
      symbol: symbol
    });
  }

  public unsubscribeFromSymbol(symbol: string): void {
    this.send({
      type: 'unsubscribe', 
      channel: 'price_updates',
      symbol: symbol
    });
  }

  public subscribeToNotifications(): void {
    this.send({
      type: 'subscribe',
      channel: 'notifications'
    });
  }

  public subscribeToTradeUpdates(): void {
    this.send({
      type: 'subscribe',
      channel: 'trade_updates'
    });
  }

  public getConnectionStatus(): 'connecting' | 'connected' | 'disconnected' {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
      default:
        return 'disconnected';
    }
  }

  public disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    this.listeners.clear();
  }
}

// React Hook for WebSocket
export const useWebSocket = () => {
  const ws = WebSocketService.getInstance();
  
  return {
    connect: ws.connect.bind(ws),
    disconnect: ws.disconnect.bind(ws),
    send: ws.send.bind(ws),
    subscribe: ws.subscribe.bind(ws),
    unsubscribe: ws.unsubscribe.bind(ws),
    subscribeToSymbol: ws.subscribeToSymbol.bind(ws),
    unsubscribeFromSymbol: ws.unsubscribeFromSymbol.bind(ws),
    subscribeToNotifications: ws.subscribeToNotifications.bind(ws),
    subscribeToTradeUpdates: ws.subscribeToTradeUpdates.bind(ws),
    getConnectionStatus: ws.getConnectionStatus.bind(ws)
  };
};