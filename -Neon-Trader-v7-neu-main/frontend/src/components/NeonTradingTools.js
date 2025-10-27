import React, { useState, useContext, useEffect, Suspense, lazy } from 'react';
import { AppContext } from '../App';
import { 
  BarChart3, TrendingUp, Calculator, Target, Layers, 
  PieChart, Activity, Zap, Eye, Settings, ChevronRight,
  LineChart, CandlestickChart, Search, RefreshCw, Play,
  Loader, AlertCircle, TrendingDown
} from 'lucide-react';
import axios from 'axios';

// Error Boundary Component
class ChartErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Chart Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-96 bg-gray-900/50 rounded-xl border border-red-500/30">
          <div className="text-center">
            <AlertCircle className="mx-auto mb-4 text-red-400" size={32} />
            <p className="text-red-400 font-medium mb-2">خطأ في تحميل الرسم البياني</p>
            <p className="text-gray-400 text-sm">يرجى تحديث الصفحة للمحاولة مرة أخرى</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Lazy load heavy components for better performance
const RealTradingChart = lazy(() => import('./RealTradingChart'));

const NeonTradingTools = () => {
  const { showToast, currentUser } = useContext(AppContext);
  const [activeCategory, setActiveCategory] = useState('charts');
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [marketData, setMarketData] = useState(null);
  const [indicators, setIndicators] = useState({});
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connected');

  // Risk Calculator States
  const [accountBalance, setAccountBalance] = useState('10000');
  const [riskPercentage, setRiskPercentage] = useState('2');
  const [entryPrice, setEntryPrice] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [calculation, setCalculation] = useState(null);

  // Available trading symbols with enhanced data
  const tradingAssets = {
    crypto: [
      { symbol: 'BTCUSDT', name: 'Bitcoin/USDT', type: 'crypto', icon: '₿' },
      { symbol: 'ETHUSDT', name: 'Ethereum/USDT', type: 'crypto', icon: 'Ξ' },
      { symbol: 'ADAUSDT', name: 'Cardano/USDT', type: 'crypto', icon: 'ADA' },
      { symbol: 'BNBUSDT', name: 'BNB/USDT', type: 'crypto', icon: 'BNB' },
      { symbol: 'SOLUSDT', name: 'Solana/USDT', type: 'crypto', icon: 'SOL' },
      { symbol: 'XRPUSDT', name: 'XRP/USDT', type: 'crypto', icon: 'XRP' },
      { symbol: 'DOGEUSDT', name: 'Dogecoin/USDT', type: 'crypto', icon: 'DOGE' },
      { symbol: 'AVAXUSDT', name: 'Avalanche/USDT', type: 'crypto', icon: 'AVAX' }
    ],
    stocks: [
      { symbol: 'AAPL', name: 'Apple Inc.', type: 'stock', icon: '🍎' },
      { symbol: 'GOOGL', name: 'Google/Alphabet', type: 'stock', icon: '🔍' },
      { symbol: 'MSFT', name: 'Microsoft Corp.', type: 'stock', icon: '🪟' },
      { symbol: 'AMZN', name: 'Amazon.com Inc.', type: 'stock', icon: '📦' },
      { symbol: 'TSLA', name: 'Tesla Inc.', type: 'stock', icon: '🚗' },
      { symbol: 'META', name: 'Meta Platforms', type: 'stock', icon: '📘' },
      { symbol: 'NVDA', name: 'NVIDIA Corp.', type: 'stock', icon: '🎮' },
      { symbol: 'NFLX', name: 'Netflix Inc.', type: 'stock', icon: '🎬' }
    ],
    forex: [
      { symbol: 'EURUSD', name: 'Euro/US Dollar', type: 'forex', icon: '€/$' },
      { symbol: 'GBPUSD', name: 'Pound/US Dollar', type: 'forex', icon: '£/$' },
      { symbol: 'USDJPY', name: 'US Dollar/Japanese Yen', type: 'forex', icon: '$/¥' },
      { symbol: 'AUDUSD', name: 'Australian Dollar/USD', type: 'forex', icon: 'A$/$' }
    ]
  };

  // Fetch market data with enhanced error handling
  const fetchMarketData = async (symbol) => {
    try {
      setLoading(true);
      setConnectionStatus('connecting');
      
      const response = await axios.get(`/market/${symbol}`);
      const data = response.data;
      
      setMarketData({
        ...data,
        lastUpdate: new Date().toLocaleTimeString('ar-SA')
      });
      
      setConnectionStatus('connected');
      
      // Fetch technical indicators
      await fetchTechnicalIndicators(symbol);
      
    } catch (error) {
      console.error('Market data fetch error:', error);
      setConnectionStatus('error');
      showToast(`خطأ في جلب بيانات ${symbol}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Enhanced technical indicators
  const fetchTechnicalIndicators = async (symbol) => {
    try {
      // Simulate technical analysis - replace with real API
      const mockIndicators = {
        rsi: Math.round(30 + Math.random() * 40), // RSI between 30-70
        macd: {
          value: (Math.random() - 0.5) * 2,
          signal: 'bullish',
          histogram: Math.random() * 0.5
        },
        ema: {
          ema20: marketData?.price * (0.98 + Math.random() * 0.04),
          ema50: marketData?.price * (0.95 + Math.random() * 0.08),
          trend: Math.random() > 0.5 ? 'صاعد' : 'هابط'
        },
        volume: {
          current: Math.floor(1000000 + Math.random() * 5000000),
          average: Math.floor(800000 + Math.random() * 2000000),
          trend: Math.random() > 0.4 ? 'مرتفع' : 'منخفض'
        }
      };
      
      setIndicators(mockIndicators);
    } catch (error) {
      console.error('Indicators fetch error:', error);
    }
  };

  // Calculate risk management
  const calculateRisk = () => {
    const balance = parseFloat(accountBalance) || 0;
    const riskPercent = parseFloat(riskPercentage) || 0;
    const entry = parseFloat(entryPrice) || 0;
    const stop = parseFloat(stopLoss) || 0;

    if (balance <= 0 || riskPercent <= 0 || entry <= 0 || stop <= 0) {
      showToast('يرجى إدخال قيم صحيحة', 'error');
      return;
    }

    const riskAmount = (balance * riskPercent) / 100;
    const priceDistance = Math.abs(entry - stop);
    const positionSize = priceDistance > 0 ? riskAmount / priceDistance : 0;
    const maxLoss = positionSize * priceDistance;

    setCalculation({
      riskAmount: riskAmount.toFixed(2),
      positionSize: positionSize.toFixed(2),
      priceDistance: priceDistance.toFixed(2),
      maxLoss: maxLoss.toFixed(2),
      riskReward: stop > entry ? (entry * 1.02 - entry) / priceDistance : (entry - entry * 0.98) / priceDistance
    });

    showToast('تم حساب المخاطر بنجاح', 'success');
  };

  // Load data on component mount
  useEffect(() => {
    fetchMarketData(selectedSymbol);
  }, [selectedSymbol]);

  // Enhanced categories with Neon styling
  const categories = [
    { 
      id: 'charts', 
      name: 'الرسوم البيانية', 
      icon: CandlestickChart,
      color: 'from-cyan-500 to-blue-500',
      description: 'تحليل فني متقدم'
    },
    { 
      id: 'calculators', 
      name: 'الحاسبات', 
      icon: Calculator,
      color: 'from-purple-500 to-pink-500',
      description: 'حاسبات المخاطر والربح'
    },
    { 
      id: 'screener', 
      name: 'فاحص الأسواق', 
      icon: Eye,
      color: 'from-emerald-500 to-teal-500',
      description: 'فحص الفرص الاستثمارية'
    }
  ];

  // Neon connection status indicator
  const ConnectionStatus = () => (
    <div className="flex items-center gap-2 text-sm">
      <div className={`w-2 h-2 rounded-full ${
        connectionStatus === 'connected' ? 'bg-green-400 animate-pulse shadow-green-400/50 shadow-lg' :
        connectionStatus === 'connecting' ? 'bg-yellow-400 animate-ping shadow-yellow-400/50 shadow-lg' :
        'bg-red-400 animate-pulse shadow-red-400/50 shadow-lg'
      }`} />
      <span className="text-gray-300">
        {connectionStatus === 'connected' && 'متصل'}
        {connectionStatus === 'connecting' && 'جاري الاتصال...'}
        {connectionStatus === 'error' && 'خطأ في الاتصال'}
      </span>
    </div>
  );

  // Enhanced Chart Section
  const renderCharts = () => (
    <div className="space-y-6">
      {/* Symbol Selection */}
      <div className="neon-card bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-6 shadow-2xl shadow-cyan-500/10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
              <CandlestickChart className="text-cyan-400" size={24} />
              <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                الرسوم البيانية التفاعلية
              </span>
            </h3>
            <p className="text-gray-400">رسوم بيانية حية مع مؤشرات فنية متقدمة</p>
          </div>
          <ConnectionStatus />
        </div>

        {/* Asset Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {Object.entries(tradingAssets).map(([category, assets]) => (
            <div key={category} className="space-y-2">
              <label className="block text-sm font-medium text-cyan-400 mb-2 capitalize">
                {category === 'crypto' && 'العملات الرقمية'}
                {category === 'stocks' && 'الأسهم'}
                {category === 'forex' && 'الفوركس'}
              </label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30 transition-all"
              >
                {assets.map((asset) => (
                  <option key={asset.symbol} value={asset.symbol} className="bg-gray-800">
                    {asset.icon} {asset.name}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>

        {/* Market Data Display */}
        {marketData && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <div className="text-gray-400 text-sm">السعر الحالي</div>
              <div className="text-xl font-bold text-white">
                ${marketData.price?.toLocaleString()}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <div className="text-gray-400 text-sm">التغيير 24س</div>
              <div className={`text-xl font-bold ${marketData.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {marketData.change_24h >= 0 ? '+' : ''}{marketData.change_24h?.toFixed(2)}%
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <div className="text-gray-400 text-sm">الحجم</div>
              <div className="text-xl font-bold text-cyan-400">
                ${marketData.volume_24h?.toLocaleString()}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <div className="text-gray-400 text-sm">آخر تحديث</div>
              <div className="text-sm text-gray-300">
                {marketData.lastUpdate}
              </div>
            </div>
          </div>
        )}

        {/* Chart Component */}
        <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700/30 min-h-[400px]">
          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <Loader className="animate-spin mx-auto mb-4 text-cyan-400" size={32} />
                <p className="text-gray-400">جاري تحميل الرسم البياني...</p>
              </div>
            </div>
          ) : (
            <Suspense fallback={
              <div className="flex items-center justify-center h-96">
                <Loader className="animate-spin text-cyan-400" size={32} />
              </div>
            }>
              <ChartErrorBoundary>
                <RealTradingChart symbol={selectedSymbol} timeframe={selectedTimeframe} height={400} />
              </ChartErrorBoundary>
            </Suspense>
          )}
        </div>

        {/* Technical Indicators */}
        {indicators && Object.keys(indicators).length > 0 && (
          <div className="mt-6">
            <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="text-cyan-400" size={20} />
              المؤشرات الفنية
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm mb-2">مؤشر القوة النسبية (RSI)</div>
                <div className={`text-lg font-bold ${
                  indicators.rsi > 70 ? 'text-red-400' : 
                  indicators.rsi < 30 ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {indicators.rsi}
                </div>
                <div className="text-xs text-gray-500">
                  {indicators.rsi > 70 ? 'مُشبع شراءً' : 
                   indicators.rsi < 30 ? 'مُشبع بيعاً' : 'متوازن'}
                </div>
              </div>
              
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm mb-2">MACD</div>
                <div className={`text-lg font-bold ${
                  indicators.macd?.signal === 'bullish' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {indicators.macd?.value?.toFixed(3)}
                </div>
                <div className="text-xs text-gray-500">{indicators.macd?.signal}</div>
              </div>

              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm mb-2">المتوسط المتحرك</div>
                <div className={`text-lg font-bold ${
                  indicators.ema?.trend === 'صاعد' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {indicators.ema?.trend}
                </div>
                <div className="text-xs text-gray-500">
                  EMA20: ${indicators.ema?.ema20?.toFixed(2)}
                </div>
              </div>

              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm mb-2">حجم التداول</div>
                <div className={`text-lg font-bold ${
                  indicators.volume?.trend === 'مرتفع' ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {indicators.volume?.trend}
                </div>
                <div className="text-xs text-gray-500">
                  {indicators.volume?.current?.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // Enhanced Calculator Section
  const renderCalculators = () => (
    <div className="space-y-6">
      <div className="neon-card bg-gradient-to-br from-purple-900/90 to-pink-900/90 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-6 shadow-2xl shadow-purple-500/10">
        <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
          <Calculator className="text-purple-400" size={24} />
          <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            حاسبة إدارة المخاطر
          </span>
        </h3>
        <p className="text-gray-400 mb-6">احسب حجم المركز المناسب وإدارة المخاطر</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-purple-300 mb-2">
                رصيد الحساب ($)
              </label>
              <input
                type="number"
                value={accountBalance}
                onChange={(e) => setAccountBalance(e.target.value)}
                className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white focus:border-purple-400 focus:ring-2 focus:ring-purple-400/30 transition-all"
                placeholder="10000"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-purple-300 mb-2">
                نسبة المخاطرة (%)
              </label>
              <input
                type="number"
                value={riskPercentage}
                onChange={(e) => setRiskPercentage(e.target.value)}
                className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white focus:border-purple-400 focus:ring-2 focus:ring-purple-400/30 transition-all"
                placeholder="2"
                step="0.1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-purple-300 mb-2">
                سعر الدخول ($)
              </label>
              <input
                type="number"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white focus:border-purple-400 focus:ring-2 focus:ring-purple-400/30 transition-all"
                placeholder={marketData?.price || "100"}
                step="0.01"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-purple-300 mb-2">
                وقف الخسارة ($)
              </label>
              <input
                type="number"
                value={stopLoss}
                onChange={(e) => setStopLoss(e.target.value)}
                className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white focus:border-purple-400 focus:ring-2 focus:ring-purple-400/30 transition-all"
                placeholder={marketData?.price ? (marketData.price * 0.95).toFixed(2) : "95"}
                step="0.01"
              />
            </div>
            
            <button
              onClick={calculateRisk}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium py-3 px-6 rounded-lg transition-all transform hover:scale-105 shadow-lg shadow-purple-500/30"
            >
              احسب المخاطر
            </button>
          </div>
          
          {calculation && (
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-white mb-4">نتائج الحساب:</h4>
              
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm">مبلغ المخاطرة</div>
                <div className="text-xl font-bold text-purple-400">
                  ${calculation.riskAmount}
                </div>
              </div>
              
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm">حجم المركز</div>
                <div className="text-xl font-bold text-cyan-400">
                  {calculation.positionSize}
                </div>
              </div>
              
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm">مسافة السعر</div>
                <div className="text-xl font-bold text-yellow-400">
                  ${calculation.priceDistance}
                </div>
              </div>
              
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="text-gray-400 text-sm">أقصى خسارة</div>
                <div className="text-xl font-bold text-red-400">
                  ${calculation.maxLoss}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Enhanced Market Screener
  const renderScreener = () => (
    <div className="space-y-6">
      <div className="neon-card bg-gradient-to-br from-emerald-900/90 to-teal-900/90 backdrop-blur-xl border border-emerald-500/30 rounded-2xl p-6 shadow-2xl shadow-emerald-500/10">
        <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
          <Search className="text-emerald-400" size={24} />
          <span className="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
            فاحص الأسواق المتقدم
          </span>
        </h3>
        <p className="text-gray-400 mb-6">ابحث عن الفرص الاستثمارية بناء على معايير تقنية</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <select className="bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30">
            <option>نوع الأصل</option>
            <option>العملات الرقمية</option>
            <option>الأسهم</option>
            <option>الفوركس</option>
          </select>
          
          <select className="bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-2 text-white focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30">
            <option>الإطار الزمني</option>
            <option>15 دقيقة</option>
            <option>1 ساعة</option>
            <option>4 ساعات</option>
            <option>يومي</option>
          </select>
          
          <button className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-medium py-2 px-4 rounded-lg transition-all">
            <Search size={16} className="inline mr-2" />
            بحث
          </button>
        </div>
        
        <div className="text-center py-12">
          <Eye size={48} className="mx-auto text-emerald-400/50 mb-4" />
          <p className="text-gray-400">ستتم إضافة نتائج الفحص هنا</p>
          <p className="text-gray-500 text-sm mt-2">قريباً - فحص الأسواق بالذكاء الصناعي</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4">
      {/* Enhanced Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
              أدوات التداول المتقدمة
            </h1>
            <p className="text-gray-400 mt-2">رسوم بيانية حقيقية ومؤشرات فنية وحاسبات تداول</p>
          </div>
          <div className="flex items-center gap-4">
            <ConnectionStatus />
            <button
              onClick={() => fetchMarketData(selectedSymbol)}
              className="flex items-center gap-2 bg-gray-800/50 hover:bg-gray-700/50 text-gray-300 px-3 py-2 rounded-lg transition-all border border-gray-600/50"
            >
              <RefreshCw size={16} />
              تحديث
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced Categories */}
      <div className="flex overflow-x-auto gap-4 mb-8 pb-2">
        {categories.map((category) => {
          const Icon = category.icon;
          const isActive = activeCategory === category.id;
          
          return (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`flex flex-col items-center gap-2 px-6 py-4 rounded-xl text-sm font-medium whitespace-nowrap transition-all transform hover:scale-105 min-w-[160px] ${
                isActive
                  ? `bg-gradient-to-r ${category.color} text-white shadow-lg shadow-cyan-500/30`
                  : 'bg-gray-800/50 text-gray-400 hover:text-white hover:bg-gray-700/50 border border-gray-600/30'
              }`}
            >
              <Icon size={24} />
              <span className="font-semibold">{category.name}</span>
              <span className="text-xs opacity-75">{category.description}</span>
            </button>
          );
        })}
      </div>

      {/* Enhanced Content */}
      <div className="space-y-6">
        {activeCategory === 'charts' && renderCharts()}
        {activeCategory === 'calculators' && renderCalculators()}
        {activeCategory === 'screener' && renderScreener()}
      </div>

      {/* Enhanced Styles */}
      <style jsx>{`
        .neon-card {
          position: relative;
        }
        
        .neon-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border-radius: 1rem;
          padding: 1px;
          background: linear-gradient(45deg, transparent, rgba(0, 255, 242, 0.3), transparent);
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          -webkit-mask-composite: subtract;
          mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          mask-composite: subtract;
        }
      `}</style>
    </div>
  );
};

export default NeonTradingTools;