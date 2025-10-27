/**
 * Neon Trader V7 - Type Definitions (JavaScript)
 * Common object structures and constants for the application
 */

// ================================
// User & Authentication Types
// ================================
export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  avatar?: string;
  role: 'user' | 'admin' | 'premium';
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user_id: string;
  email: string;
  username: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  two_factor_code?: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

// ================================
// Trading & Market Types
// ================================
export interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  change_24h_percent: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
  open_price: number;
  asset_type: AssetType;
  asset_type_name: string;
  source: string;
  timestamp: string;
  last_updated: string;
  fetch_time_ms?: number;
}

export type AssetType = 'crypto' | 'stock' | 'forex' | 'commodity' | 'index';

export interface TradingAsset {
  symbol: string;
  name: string;
  type: AssetType;
  icon: string;
  category?: string;
}

export interface Trade {
  id: string;
  user_id: string;
  symbol: string;
  trade_type: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop_loss' | 'take_profit';
  quantity: number;
  entry_price: number;
  exit_price?: number;
  stop_loss?: number;
  take_profit?: number;
  status: 'open' | 'closed' | 'cancelled';
  pnl: number;
  platform_id: string;
  created_at: string;
  closed_at?: string;
  execution_type?: 'paper' | 'live';
  current_market_price?: number;
}

export interface Portfolio {
  user_id: string;
  total_balance: number;
  available_balance: number;
  invested_balance: number;
  daily_pnl: number;
  total_pnl: number;
  assets: Record<string, number>;
  positions: Position[];
  last_updated: string;
}

export interface Position {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  pnl: number;
  pnl_percentage: number;
  side: 'long' | 'short';
}

// ================================
// Platform Integration Types
// ================================
export interface Platform {
  id: string;
  user_id: string;
  name: string;
  platform_type: 'binance' | 'bybit' | 'okx' | 'paper';
  api_key?: string;
  secret_key?: string;
  passphrase?: string;
  is_testnet: boolean;
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  created_at: string;
  last_connected?: string;
  connection_details?: {
    balance?: number;
    ping?: number;
    error_message?: string;
  };
}

// ================================
// AI & Analysis Types
// ================================
export interface AIAnalysis {
  symbol: string;
  analysis: string;
  confidence: 'high' | 'medium' | 'low';
  recommendation: 'buy' | 'sell' | 'hold';
  target_price?: number;
  stop_loss?: number;
  timeframe: string;
  market_data: MarketData;
  timestamp: string;
  reasoning: string[];
}

export interface DailyPlan {
  id: string;
  user_id: string;
  date: string;
  market_analysis: string;
  trading_strategy: string;
  risk_level: 'low' | 'medium' | 'high';
  opportunities: TradingOpportunity[];
  created_at: string;
}

export interface TradingOpportunity {
  symbol: string;
  type: 'breakout' | 'reversal' | 'trend' | 'arbitrage';
  confidence: number;
  timeframe: string;
  description: string;
  target_price: number;
  stop_loss: number;
  potential_return: number;
  risk_reward_ratio: number;
}

// ================================
// Technical Analysis Types
// ================================
export interface TechnicalIndicators {
  rsi: number;
  macd: {
    value: number;
    signal: string;
    histogram: number;
  };
  ema: {
    ema20: number;
    ema50: number;
    trend: string;
  };
  volume: {
    current: number;
    average: number;
    trend: string;
  };
  bollinger_bands?: {
    upper: number;
    middle: number;
    lower: number;
  };
  support_resistance?: {
    support: number[];
    resistance: number[];
  };
}

// ================================
// WebSocket Types
// ================================
export interface WSMessage {
  type: 'price_update' | 'trade_update' | 'notification' | 'system_status';
  data: any;
  timestamp: string;
  channel?: string;
}

export interface PriceUpdate {
  symbol: string;
  price: number;
  change: number;
  volume: number;
  timestamp: string;
}

// ================================
// Notification Types
// ================================
export interface Notification {
  id: string;
  user_id: string;
  type: 'price_alert' | 'trade_executed' | 'system' | 'ai_recommendation';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  read: boolean;
  action_url?: string;
  metadata?: Record<string, any>;
  created_at: string;
  expires_at?: string;
}

export interface SmartAlert {
  id: string;
  user_id: string;
  symbol: string;
  condition: 'price_above' | 'price_below' | 'volume_spike' | 'rsi_overbought' | 'rsi_oversold';
  value: number;
  active: boolean;
  triggered: boolean;
  created_at: string;
  triggered_at?: string;
}

// ================================
// Settings & Preferences Types
// ================================
export interface UserSettings {
  theme: 'dark' | 'light' | 'neon';
  language: 'ar' | 'en';
  rtl: boolean;
  notifications: {
    email: boolean;
    push: boolean;
    trading_updates: boolean;
    price_alerts: boolean;
    ai_recommendations: boolean;
  };
  trading: {
    default_risk_percentage: number;
    auto_stop_loss: boolean;
    paper_trading_mode: boolean;
    max_daily_trades: number;
  };
  security: {
    two_factor_enabled: boolean;
    session_timeout: number;
    login_notifications: boolean;
  };
}

// ================================
// Risk Management Types
// ================================
export interface RiskCalculation {
  account_balance: number;
  risk_percentage: number;
  entry_price: number;
  stop_loss: number;
  risk_amount: number;
  position_size: number;
  price_distance: number;
  max_loss: number;
  risk_reward_ratio: number;
}

// ================================
// System Status Types
// ================================
export interface SystemStatus {
  status: 'ok' | 'degraded' | 'error';
  database: 'connected' | 'disconnected' | 'error';
  ai_service: 'ready' | 'loading' | 'error';
  market_data: string;
  exchanges: string[];
  last_updated: string;
}

// ================================
// API Response Types
// ================================
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

// ================================
// Component Props Types
// ================================
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingState {
  loading: boolean;
  error?: string;
}

// ================================
// App Context Types
// ================================
export interface AppContextType {
  // User & Auth
  currentUser: User | null;
  isAuthenticated: boolean;
  isLocked: boolean;
  login: (credentials: LoginCredentials) => Promise<APIResponse>;
  logout: () => void;
  register: (data: RegisterData) => Promise<APIResponse>;
  
  // Navigation
  currentPage: string;
  setCurrentPage: (page: string) => void;
  
  // Data
  portfolio: Portfolio | null;
  trades: Trade[];
  platforms: Platform[];
  notifications: Notification[];
  
  // Functions
  showToast: (message: string, type: 'success' | 'error' | 'info' | 'warning') => void;
  fetchPortfolio: () => Promise<void>;
  fetchTrades: () => Promise<void>;
  fetchPlatforms: () => Promise<void>;
  
  // Settings
  settings: UserSettings;
  updateSettings: (settings: Partial<UserSettings>) => Promise<void>;
  
  // Loading States
  loading: Record<string, boolean>;
  setLoading: (key: string, loading: boolean) => void;
}