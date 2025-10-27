import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, ColorType, CrosshairMode, LineStyle } from 'lightweight-charts';
import axios from 'axios';
import { RefreshCw, TrendingUp, BarChart3, Settings } from 'lucide-react';

const RealTradingChart = ({ symbol = 'BTCUSDT', timeframe = '1h', height = 500 }) => {
  const chartContainerRef = useRef();
  const chart = useRef();
  const candlestickSeries = useRef();
  const volumeSeries = useRef();
  const indicatorSeries = useRef({});

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  const [showIndicators, setShowIndicators] = useState({
    sma20: false,
    sma50: false,
    rsi: false,
    bollinger: false
  });

  // Chart configuration optimized for financial data
  const chartOptions = {
    layout: {
      background: { type: ColorType.Solid, color: 'transparent' },
      textColor: '#d1d5db',
      fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
    },
    grid: {
      vertLines: { color: '#374151' },
      horzLines: { color: '#374151' },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: {
        width: 1,
        color: '#6b7280',
        style: LineStyle.Dashed,
      },
      horzLine: {
        width: 1,
        color: '#6b7280',
        style: LineStyle.Dashed,
      },
    },
    rightPriceScale: {
      borderColor: '#4b5563',
      scaleMargins: { top: 0.1, bottom: 0.2 },
    },
    timeScale: {
      borderColor: '#4b5563',
      timeVisible: true,
      secondsVisible: false,
    },
    handleScroll: {
      mouseWheel: true,
      pressedMouseMove: true,
    },
    handleScale: {
      axisPressedMouseMove: true,
      mouseWheel: true,
      pinch: true,
    },
  };

  // Available symbols for different asset types
  const availableSymbols = {
    crypto: [
      { symbol: 'BTCUSDT', name: 'Bitcoin/USDT' },
      { symbol: 'ETHUSDT', name: 'Ethereum/USDT' }, 
      { symbol: 'ADAUSDT', name: 'Cardano/USDT' },
      { symbol: 'BNBUSDT', name: 'BNB/USDT' },
      { symbol: 'SOLUSDT', name: 'Solana/USDT' },
      { symbol: 'XRPUSDT', name: 'XRP/USDT' },
    ],
    stocks: [
      { symbol: 'AAPL', name: 'Apple Inc.' },
      { symbol: 'GOOGL', name: 'Google/Alphabet' },
      { symbol: 'MSFT', name: 'Microsoft' },
      { symbol: 'AMZN', name: 'Amazon' },
      { symbol: 'TSLA', name: 'Tesla' },
      { symbol: 'META', name: 'Meta/Facebook' }
    ],
    forex: [
      { symbol: 'EURUSD', name: 'EUR/USD' },
      { symbol: 'GBPUSD', name: 'GBP/USD' },
      { symbol: 'USDJPY', name: 'USD/JPY' },
      { symbol: 'AUDUSD', name: 'AUD/USD' }
    ]
  };

  const timeframes = [
    { value: '1m', label: '1 دقيقة' },
    { value: '5m', label: '5 دقائق' },
    { value: '15m', label: '15 دقيقة' },
    { value: '1h', label: 'ساعة واحدة' },
    { value: '4h', label: '4 ساعات' },
    { value: '1d', label: 'يوم واحد' }
  ];

  // Initialize chart
  useEffect(() => {
    let resizeObserver;
    
    const initializeChart = () => {
      try {
        // Ensure the container is mounted and has dimensions
        if (chartContainerRef.current && chartContainerRef.current.clientWidth > 0) {
          // Clean up existing chart if it exists
          if (chart.current) {
            chart.current.remove();
            chart.current = null;
          }

          chart.current = createChart(chartContainerRef.current, {
            ...chartOptions,
            width: chartContainerRef.current.clientWidth,
            height: height,
          });

          // Add candlestick series with a small delay to ensure chart is fully initialized
          setTimeout(() => {
            if (chart.current) {
              try {
                candlestickSeries.current = chart.current.addCandlestickSeries({
                  upColor: '#10b981',
                  downColor: '#ef4444',
                  borderVisible: false,
                  wickUpColor: '#10b981',
                  wickDownColor: '#ef4444',
                  priceLineVisible: false,
                });

                // Add volume series
                volumeSeries.current = chart.current.addHistogramSeries({
                  color: '#6b7280',
                  priceFormat: { type: 'volume' },
                  priceScaleId: '',
                  scaleMargins: { top: 0.8, bottom: 0 },
                });
              } catch (error) {
                console.error('Error adding series to chart:', error);
                setError('خطأ في إضافة السلاسل إلى الرسم البياني');
              }
            }
          }, 0);
        }
      } catch (error) {
        console.error('Error initializing chart:', error);
        setError('خطأ في تهيئة الرسم البياني');
      }
    };

    // Initialize chart
    initializeChart();

    // Set up resize observer for more responsive behavior
    if (chartContainerRef.current) {
      resizeObserver = new ResizeObserver(entries => {
        try {
          if (chart.current && chartContainerRef.current) {
            chart.current.applyOptions({
              width: chartContainerRef.current.clientWidth,
            });
          }
        } catch (error) {
          console.error('Error resizing chart:', error);
        }
      });
      resizeObserver.observe(chartContainerRef.current);
    }

    return () => {
      if (resizeObserver && chartContainerRef.current) {
        resizeObserver.unobserve(chartContainerRef.current);
      }
      if (chart.current) {
        try {
          chart.current.remove();
        } catch (error) {
          console.error('Error removing chart:', error);
        }
        chart.current = null;
      }
    };
  }, [height]);

  // Fetch real market data
  const fetchMarketData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Get current market data
      const marketResponse = await axios.get(`/market/${selectedSymbol}`);
      setMarketData(marketResponse.data);

      // Generate realistic candlestick data (in real app, this would come from API)
      const candlesticks = generateRealisticCandlesticks(marketResponse.data.price, 100);
      setChartData(candlesticks);

      // Update chart with new data
      try {
        if (chart.current && candlestickSeries.current) {
          candlestickSeries.current.setData(candlesticks);
        }

        // Generate volume data
        const volumes = candlesticks.map(candle => ({
          time: candle.time,
          value: Math.random() * 1000000,
          color: candle.close > candle.open ? '#10b98140' : '#ef444440'
        }));

        if (chart.current && volumeSeries.current) {
          volumeSeries.current.setData(volumes);
        }
      } catch (error) {
        console.error('Error setting chart data:', error);
        setError('خطأ في تحديث بيانات الرسم البياني');
      }

    } catch (error) {
      console.error('Error fetching market data:', error);
      setError('خطأ في تحميل بيانات السوق');
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol]);

  // Generate realistic candlestick data
  const generateRealisticCandlesticks = (basePrice, count) => {
    const candlesticks = [];
    let currentPrice = basePrice;
    const now = Date.now();
    const intervalMs = getIntervalMs(selectedTimeframe);

    for (let i = count - 1; i >= 0; i--) {
      const time = Math.floor((now - (i * intervalMs)) / 1000);
      
      const volatility = 0.02; // 2% volatility
      const change = (Math.random() - 0.5) * volatility * currentPrice;
      
      const open = currentPrice;
      const close = Math.max(0, currentPrice + change);
      const high = Math.max(open, close) * (1 + Math.random() * 0.01);
      const low = Math.min(open, close) * (1 - Math.random() * 0.01);

      candlesticks.push({
        time: time,
        open: parseFloat(open.toFixed(4)),
        high: parseFloat(high.toFixed(4)),
        low: parseFloat(low.toFixed(4)),
        close: parseFloat(close.toFixed(4))
      });

      currentPrice = close;
    }

    return candlesticks.sort((a, b) => a.time - b.time);
  };

  const getIntervalMs = (timeframe) => {
    const intervals = {
      '1m': 60 * 1000,
      '5m': 5 * 60 * 1000,
      '15m': 15 * 60 * 1000,
      '1h': 60 * 60 * 1000,
      '4h': 4 * 60 * 60 * 1000,
      '1d': 24 * 60 * 60 * 1000
    };
    return intervals[timeframe] || intervals['1h'];
  };

  // Add technical indicators
  const addTechnicalIndicator = useCallback((type) => {
    if (!chartData.length || !chart.current) return;

    try {
      switch (type) {
        case 'sma20':
          if (!indicatorSeries.current.sma20) {
            const sma20Data = calculateSMA(chartData, 20);
            if (chart.current) {
              indicatorSeries.current.sma20 = chart.current.addLineSeries({
                color: '#f59e0b',
                lineWidth: 2,
                title: 'SMA 20'
              });
              indicatorSeries.current.sma20.setData(sma20Data);
            }
          }
          break;

        case 'sma50':
          if (!indicatorSeries.current.sma50) {
            const sma50Data = calculateSMA(chartData, 50);
            if (chart.current) {
              indicatorSeries.current.sma50 = chart.current.addLineSeries({
                color: '#8b5cf6',
                lineWidth: 2,
                title: 'SMA 50'
              });
              indicatorSeries.current.sma50.setData(sma50Data);
            }
          }
          break;

        case 'bollinger':
          if (!indicatorSeries.current.bollinger) {
            const bollingerData = calculateBollingerBands(chartData, 20, 2);
            if (chart.current) {
              indicatorSeries.current.bollinger = {
                upper: chart.current.addLineSeries({
                  color: '#ec4899',
                  lineWidth: 1,
                  title: 'BB Upper'
                }),
                middle: chart.current.addLineSeries({
                  color: '#06b6d4',
                  lineWidth: 1,
                  title: 'BB Middle'
                }),
                lower: chart.current.addLineSeries({
                  color: '#ec4899',
                  lineWidth: 1,
                  title: 'BB Lower'
                })
              };

              indicatorSeries.current.bollinger.upper.setData(bollingerData.upper);
              indicatorSeries.current.bollinger.middle.setData(bollingerData.middle);
              indicatorSeries.current.bollinger.lower.setData(bollingerData.lower);
            }
          }
          break;
      }
    } catch (error) {
      console.error('Error adding technical indicator:', error);
      setError('خطأ في إضافة المؤشر الفني');
    }
  }, [chartData]);

  // Remove technical indicator
  const removeTechnicalIndicator = useCallback((type) => {
    try {
      if (indicatorSeries.current[type]) {
        if (type === 'bollinger') {
          if (chart.current && indicatorSeries.current[type].upper) {
            chart.current.removeSeries(indicatorSeries.current[type].upper);
          }
          if (chart.current && indicatorSeries.current[type].middle) {
            chart.current.removeSeries(indicatorSeries.current[type].middle);
          }
          if (chart.current && indicatorSeries.current[type].lower) {
            chart.current.removeSeries(indicatorSeries.current[type].lower);
          }
        } else {
          if (chart.current) {
            chart.current.removeSeries(indicatorSeries.current[type]);
          }
        }
        delete indicatorSeries.current[type];
      }
    } catch (error) {
      console.error('Error removing technical indicator:', error);
      setError('خطأ في إزالة المؤشر الفني');
    }
  }, []);

  // Technical indicator calculations
  const calculateSMA = (data, period) => {
    if (data.length < period) return [];
    
    const smaData = [];
    for (let i = period - 1; i < data.length; i++) {
      const sum = data.slice(i - period + 1, i + 1).reduce((acc, item) => acc + item.close, 0);
      const sma = sum / period;
      smaData.push({ time: data[i].time, value: sma });
    }
    return smaData;
  };

  const calculateBollingerBands = (data, period, multiplier) => {
    if (data.length < period) return { upper: [], middle: [], lower: [] };
    
    const upper = [];
    const middle = [];
    const lower = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const sma = slice.reduce((acc, item) => acc + item.close, 0) / period;
      
      const variance = slice.reduce((acc, item) => acc + Math.pow(item.close - sma, 2), 0) / period;
      const stdDev = Math.sqrt(variance);
      
      const time = data[i].time;
      middle.push({ time, value: sma });
      upper.push({ time, value: sma + (stdDev * multiplier) });
      lower.push({ time, value: sma - (stdDev * multiplier) });
    }
    
    return { upper, middle, lower };
  };

  // Handle indicator toggle
  const toggleIndicator = (type) => {
    setShowIndicators(prev => {
      const newState = { ...prev, [type]: !prev[type] };
      
      if (newState[type]) {
        addTechnicalIndicator(type);
      } else {
        removeTechnicalIndicator(type);
      }
      
      return newState;
    });
  };

  // Load data when symbol or timeframe changes
  useEffect(() => {
    fetchMarketData();
  }, [fetchMarketData]);

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
      {/* Chart Header */}
      <div className="bg-slate-800/30 p-4 border-b border-slate-700/50">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div>
              <h3 className="text-lg font-bold text-white">{selectedSymbol}</h3>
              {marketData && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-2xl font-mono font-bold text-white">
                    ${marketData.price?.toFixed(4)}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    marketData.change_24h_percent >= 0 
                      ? 'bg-green-500/20 text-green-400' 
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {marketData.change_24h_percent >= 0 ? '+' : ''}{marketData.change_24h_percent}%
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Symbol Selection */}
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:ring-2 focus:ring-blue-500"
            >
              <optgroup label="العملات الرقمية">
                {availableSymbols.crypto.map(s => (
                  <option key={s.symbol} value={s.symbol}>{s.name}</option>
                ))}
              </optgroup>
              <optgroup label="الأسهم">
                {availableSymbols.stocks.map(s => (
                  <option key={s.symbol} value={s.symbol}>{s.name}</option>
                ))}
              </optgroup>
              <optgroup label="الفوركس">
                {availableSymbols.forex.map(s => (
                  <option key={s.symbol} value={s.symbol}>{s.name}</option>
                ))}
              </optgroup>
            </select>

            {/* Timeframe Selection */}
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              className="bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:ring-2 focus:ring-blue-500"
            >
              {timeframes.map(tf => (
                <option key={tf.value} value={tf.value}>{tf.label}</option>
              ))}
            </select>

            {/* Refresh Button */}
            <button
              onClick={fetchMarketData}
              disabled={loading}
              className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Technical Indicators Toggle */}
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-33 border-t border-slate-700/50">
          <span className="text-sm text-gray-400 mr-2">المؤشرات الفنية:</span>
          {Object.entries(showIndicators).map(([key, active]) => (
            <button
              key={key}
              onClick={() => toggleIndicator(key)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                active
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              {key.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Container */}
      <div className="relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-800/50 z-10">
            <div className="flex items-center gap-2 text-white">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
              <span>جاري تحميل بيانات السوق...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-800/50 z-10">
            <div className="text-red-400 text-center">
              <p>{error}</p>
              <button 
                onClick={fetchMarketData}
                className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg"
              >
                إعادة المحاولة
              </button>
            </div>
          </div>
        )}

        <div
          ref={chartContainerRef}
          style={{ height: `${height}px`, minHeight: `${height}px` }}
          className="w-full min-h-[300px]"
        />
      </div>

      {/* Chart Info */}
      {marketData && (
        <div className="bg-slate-800/30 p-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-t border-slate-700/50">
          <div>
            <span className="text-gray-400">الحجم 24س:</span>
            <div className="font-mono text-white">{marketData.volume_24h?.toLocaleString()}</div>
          </div>
          <div>
            <span className="text-gray-400">أعلى 24س:</span>
            <div className="font-mono text-green-400">${marketData.high_24h?.toFixed(4)}</div>
          </div>
          <div>
            <span className="text-gray-400">أقل 24س:</span>
            <div className="font-mono text-red-400">${marketData.low_24h?.toFixed(4)}</div>
          </div>
          <div>
            <span className="text-gray-400">مصدر البيانات:</span>
            <div className="text-blue-400">{marketData.data_source || 'Real API'}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTradingChart;