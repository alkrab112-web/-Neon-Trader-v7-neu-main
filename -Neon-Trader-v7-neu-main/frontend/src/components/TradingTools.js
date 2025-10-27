import React, { useState, useContext, useEffect } from 'react';
import { AppContext } from '../App';
import { 
  BarChart3, TrendingUp, Calculator, Target, Layers, 
  PieChart, Activity, Zap, Eye, Settings, ChevronRight,
  LineChart, CandlestickChart, Search, RefreshCw, Play
} from 'lucide-react';
import axios from 'axios';
import RealTradingChart from './RealTradingChart';

const TradingTools = () => {
  const { showToast } = useContext(AppContext);
  const [activeCategory, setActiveCategory] = useState('charts');
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [marketData, setMarketData] = useState(null);
  const [indicators, setIndicators] = useState({});
  const [loading, setLoading] = useState(false);

  // Risk Calculator States (moved to top level to fix React Hooks error)
  const [accountBalance, setAccountBalance] = useState('10000');
  const [riskPercentage, setRiskPercentage] = useState('2');
  const [entryPrice, setEntryPrice] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [calculation, setCalculation] = useState(null);

  // Available trading symbols
  const cryptoSymbols = [
    { symbol: 'BTCUSDT', name: 'Bitcoin/USDT', type: 'crypto' },
    { symbol: 'ETHUSDT', name: 'Ethereum/USDT', type: 'crypto' },
    { symbol: 'ADAUSDT', name: 'Cardano/USDT', type: 'crypto' },
    { symbol: 'BNBUSDT', name: 'BNB/USDT', type: 'crypto' },
    { symbol: 'SOLUSDT', name: 'Solana/USDT', type: 'crypto' },
    { symbol: 'XRPUSDT', name: 'XRP/USDT', type: 'crypto' },
    { symbol: 'DOGEUSDT', name: 'Dogecoin/USDT', type: 'crypto' },
    { symbol: 'AVAXUSDT', name: 'Avalanche/USDT', type: 'crypto' }
  ];

  const stockSymbols = [
    { symbol: 'AAPL', name: 'Apple Inc.', type: 'stock' },
    { symbol: 'GOOGL', name: 'Google/Alphabet', type: 'stock' },
    { symbol: 'MSFT', name: 'Microsoft Corp.', type: 'stock' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', type: 'stock' },
    { symbol: 'TSLA', name: 'Tesla Inc.', type: 'stock' },
    { symbol: 'META', name: 'Meta Platforms', type: 'stock' },
    { symbol: 'NVDA', name: 'NVIDIA Corp.', type: 'stock' },
    { symbol: 'NFLX', name: 'Netflix Inc.', type: 'stock' }
  ];

  const forexSymbols = [
    { symbol: 'EURUSD', name: 'EUR/USD', type: 'forex' },
    { symbol: 'GBPUSD', name: 'GBP/USD', type: 'forex' },
    { symbol: 'USDJPY', name: 'USD/JPY', type: 'forex' },
    { symbol: 'AUDUSD', name: 'AUD/USD', type: 'forex' },
    { symbol: 'USDCHF', name: 'USD/CHF', type: 'forex' },
    { symbol: 'USDCAD', name: 'USD/CAD', type: 'forex' },
    { symbol: 'NZDUSD', name: 'NZD/USD', type: 'forex' },
    { symbol: 'EURJPY', name: 'EUR/JPY', type: 'forex' }
  ];

  const allSymbols = [...cryptoSymbols, ...stockSymbols, ...forexSymbols];

  const timeframes = [
    { value: '1m', label: '1 دقيقة' },
    { value: '5m', label: '5 دقائق' },
    { value: '15m', label: '15 دقيقة' },
    { value: '1h', label: 'ساعة' },
    { value: '4h', label: '4 ساعات' },
    { value: '1d', label: 'يوم' },
    { value: '1w', label: 'أسبوع' }
  ];

  useEffect(() => {
    loadMarketData();
  }, [selectedSymbol]);

  const loadMarketData = async () => {
    try {
      setLoading(true);
      
      // Get current market data
      const marketResponse = await axios.get(`/market/${selectedSymbol}`);
      setMarketData(marketResponse.data);
      
      // Calculate technical indicators would go here
      // For now, we'll use the real chart component's built-in indicators
      
    } catch (error) {
      console.error('Error loading market data:', error);
      showToast('خطأ في تحميل بيانات السوق', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Real Interactive Chart Component
  const renderRealTradingChart = () => (
    <div className="space-y-6">
      <div className="card p-0 overflow-hidden">
        <div className="p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-b border-slate-700/50">
          <h3 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
            <CandlestickChart size={20} />
            الرسوم البيانية التفاعلية - الشموع اليابانية
          </h3>
          <p className="text-gray-400 text-sm">
            رسوم بيانية حقيقية تفاعلية مع إمكانية التكبير والتحرك والمؤشرات الفنية
          </p>
        </div>
        
        <RealTradingChart 
          symbol={selectedSymbol}
          timeframe={selectedTimeframe}
          height={500}
        />
      </div>

      {/* Market Analysis Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h4 className="font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={18} />
            تحليل السوق المباشر
          </h4>
          
          {marketData ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">السعر الحالي</p>
                <p className="text-lg font-bold text-white font-mono">
                  ${marketData.price?.toFixed(4)}
                </p>
              </div>
              
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">التغير 24 ساعة</p>
                <p className={`text-lg font-bold font-mono ${
                  marketData.change_24h_percent >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {marketData.change_24h_percent >= 0 ? '+' : ''}{marketData.change_24h_percent}%
                </p>
              </div>
              
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">الحجم</p>
                <p className="text-lg font-bold text-white font-mono">
                  {marketData.volume_24h?.toLocaleString()}
                </p>
              </div>
              
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">أعلى 24س</p>
                <p className="text-sm font-mono text-green-400">
                  ${marketData.high_24h?.toFixed(4)}
                </p>
              </div>
              
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">أقل 24س</p>
                <p className="text-sm font-mono text-red-400">
                  ${marketData.low_24h?.toFixed(4)}
                </p>
              </div>
              
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">مصدر البيانات</p>
                <p className="text-sm text-blue-400">
                  {marketData.data_source?.replace('_', ' ') || 'Real API'}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="text-gray-400 mt-2">جاري تحميل بيانات السوق...</p>
            </div>
          )}
        </div>

        <div className="card">
          <h4 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Activity size={18} />
            إشارات تداول سريعة
          </h4>
          
          <div className="space-y-3">
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 font-medium text-sm">إشارة شراء</span>
              </div>
              <p className="text-xs text-gray-300">
                اختراق مستوى مقاومة مهم عند ${(marketData?.price * 1.02)?.toFixed(2)}
              </p>
            </div>
            
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span className="text-yellow-400 font-medium text-sm">تحذير</span>
              </div>
              <p className="text-xs text-gray-300">
                حجم التداول أقل من المتوسط المتحرك
              </p>
            </div>
            
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="text-blue-400 font-medium text-sm">معلومة</span>
              </div>
              <p className="text-xs text-gray-300">
                RSI في منطقة متوسطة (45-55)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
  // Risk Management Calculator
  const calculateRisk = () => {
    const balance = parseFloat(accountBalance);
    const risk = parseFloat(riskPercentage);
    const entry = parseFloat(entryPrice);
    const stop = parseFloat(stopLoss);

    if (balance && risk && entry && stop) {
      const riskAmount = (balance * risk) / 100;
      const priceDistance = Math.abs(entry - stop);
      const positionSize = riskAmount / priceDistance;

      setCalculation({
        riskAmount,
        positionSize,
        priceDistance,
        potentialLoss: riskAmount
      });
    }
  };

  const renderRiskCalculator = () => {
    return (
      <div className="card">
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Calculator size={20} />
          حاسبة إدارة المخاطر
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">رصيد الحساب ($)</label>
              <input
                type="number"
                value={accountBalance}
                onChange={(e) => setAccountBalance(e.target.value)}
                className="input-field"
                placeholder="10000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">نسبة المخاطرة (%)</label>
              <input
                type="number"
                value={riskPercentage}
                onChange={(e) => setRiskPercentage(e.target.value)}
                className="input-field"
                placeholder="2"
                max="10"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">سعر الدخول ($)</label>
              <input
                type="number"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                className="input-field"
                placeholder={marketData?.price?.toFixed(4) || "100.00"}
                step="0.01"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">وقف الخسارة ($)</label>
              <input
                type="number"
                value={stopLoss}
                onChange={(e) => setStopLoss(e.target.value)}
                className="input-field"
                placeholder={(marketData?.price * 0.95)?.toFixed(4) || "95.00"}
                step="0.01"
              />
            </div>

            <button
              onClick={calculateRisk}
              className="btn-primary w-full"
            >
              احسب المخاطر
            </button>
          </div>

          {calculation && (
            <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg p-6 border border-blue-500/30">
              <h4 className="font-semibold text-blue-400 mb-4">نتائج الحساب</h4>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-300">مبلغ المخاطرة:</span>
                  <span className="font-mono font-semibold text-white">
                    ${calculation.riskAmount.toFixed(2)}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-300">حجم الصفقة:</span>
                  <span className="font-mono font-semibold text-white">
                    {calculation.positionSize.toFixed(4)}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-300">المسافة السعرية:</span>
                  <span className="font-mono font-semibold text-white">
                    ${calculation.priceDistance.toFixed(4)}
                  </span>
                </div>
                
                <div className="flex justify-between border-t border-gray-600 pt-3">
                  <span className="text-gray-300">أقصى خسارة محتملة:</span>
                  <span className="font-mono font-semibold text-red-400">
                    -${calculation.potentialLoss.toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded">
                <p className="text-sm text-amber-300">
                  💡 نصيحة: لا تخاطر بأكثر من 2% من رأس المال في صفقة واحدة
                </p>
              </div>
              
              <div className="mt-3 p-3 bg-green-500/10 border border-green-500/30 rounded">
                <p className="text-sm text-green-300">
                  📊 نسبة المخاطرة الحالية: {((calculation.riskAmount / parseFloat(accountBalance)) * 100).toFixed(2)}%
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const categories = [
    { id: 'charts', name: 'الرسوم البيانية', icon: CandlestickChart },
    { id: 'calculators', name: 'الحاسبات', icon: Calculator },
    { id: 'screener', name: 'فاحص الأسواق', icon: Eye }
  ];

  const renderScreener = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Search size={20} />
          فاحص الأسواق
        </h3>
        <p className="text-gray-400 mb-6">ابحث عن الفرص الاستثمارية بناء على معايير تقنية</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <select className="input-field">
            <option>نوع الأصل</option>
            <option>العملات الرقمية</option>
            <option>الأسهم</option>
            <option>الفوركس</option>
            <option>السلع</option>
          </select>
          
          <select className="input-field">
            <option>المؤشر</option>
            <option>RSI أكبر من 70 (ذروة شراء)</option>
            <option>RSI أقل من 30 (ذروة بيع)</option>
            <option>MACD إشارة إيجابية</option>
            <option>كسر مستوى المقاومة</option>
          </select>
          
          <button className="btn-primary flex items-center gap-2">
            <Eye size={16} />
            فحص الأسواق
          </button>
        </div>
        
        <div className="bg-white/5 rounded-lg p-4">
          <div className="text-center text-gray-400 py-8">
            <Eye size={48} className="mx-auto mb-4 opacity-50" />
            <p>اختر المعايير أعلاه وانقر "فحص الأسواق" لعرض النتائج</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">أدوات التداول المتقدمة</h1>
        <p className="text-gray-400 mt-1">رسوم بيانية حقيقية ومؤشرات فنية وحاسبات تداول</p>
      </div>

      {/* Categories */}
      <div className="flex overflow-x-auto gap-2 pb-2">
        {categories.map((category) => {
          const Icon = category.icon;
          return (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                activeCategory === category.id
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : 'bg-white/10 text-gray-400 hover:text-white hover:bg-white/20'
              }`}
            >
              <Icon size={16} />
              {category.name}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div>
        {activeCategory === 'charts' && renderRealTradingChart()}
        {activeCategory === 'calculators' && renderRiskCalculator()}
        {activeCategory === 'screener' && renderScreener()}
      </div>

      {/* Trading Insights */}
      <div className="card bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/30">
        <h3 className="font-semibold text-blue-400 mb-3 flex items-center gap-2">
          <Target size={20} />
          رؤى تداول ذكية
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-200">
          <div>
            <h4 className="font-medium mb-2">تحليل فني متقدم:</h4>
            <ul className="space-y-1">
              <li>• الشموع اليابانية تكشف نفسية السوق</li>
              <li>• RSI فوق 70 يشير لذروة شراء محتملة</li>
              <li>• MACD يساعد في تحديد نقاط التحول</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">إدارة المخاطر الذكية:</h4>
            <ul className="space-y-1">
              <li>• احسب حجم المركز بناء على المخاطرة</li>
              <li>• ضع وقف الخسارة قبل الدخول</li>
              <li>• استخدم نسبة مخاطرة 1:2 أو أفضل</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingTools;