# 🔌 دليل الربط والتكامل - Neon Trader V7

## 📋 المحتويات

1. [ربط Binance](#binance)
2. [ربط Bybit](#bybit)
3. [ربط OKX](#okx)
4. [تكامل DeepSeek AI](#deepseek)
5. [استخدام Circuit Breaker](#circuit-breaker)
6. [مراقبة الأداء](#monitoring)

---

## 🟡 ربط Binance {#binance}

### الخطوة 1: إنشاء API Key

1. سجل الدخول إلى [Binance](https://www.binance.com/)
2. اذهب إلى **Account** → **API Management**
3. اضغط **Create API**
4. أكمل التحقق الأمني (2FA, Email, SMS)
5. احفظ:
   - **API Key**
   - **Secret Key**

### الخطوة 2: تفعيل الصلاحيات

✅ **Enable Reading** (قراءة البيانات)  
✅ **Enable Spot & Margin Trading** (التداول)  
❌ **Enable Withdrawals** (غير مطلوب - للأمان)

### الخطوة 3: IP Whitelist (اختياري للأمان)

إذا أردت تفعيل IP whitelist:
```bash
# احصل على IP الخاص بك
curl ifconfig.me

# أضفه في Binance API settings
```

### الخطوة 4: اختبار على Testnet

```python
# backend/test_binance.py
import asyncio
from services.exchange_adapters.binance_adapter import BinanceAdapter

async def test_binance():
    # استخدم مفاتيح testnet من: https://testnet.binance.vision/
    adapter = BinanceAdapter(
        api_key="YOUR_TESTNET_API_KEY",
        api_secret="YOUR_TESTNET_SECRET",
        testnet=True
    )
    
    # اختبار الاتصال
    result = await adapter.test_connection()
    print("✅ Connection test:", result)
    
    # جلب السعر
    ticker = await adapter.get_ticker("BTCUSDT")
    print("💰 BTC Price:", ticker['price'])
    
    # جلب الرصيد (testnet)
    balance = await adapter.get_balance()
    print("💼 Balance:", balance['total'])
    
    await adapter.disconnect()

# تشغيل الاختبار
asyncio.run(test_binance())
```

### الخطوة 5: الربط من واجهة التطبيق

```
1. سجل الدخول للتطبيق
2. اذهب إلى صفحة "المنصات"
3. اضغط "إضافة منصة جديدة"
4. املأ التفاصيل:
   - الاسم: Binance Main
   - النوع: Binance
   - API Key: [مفتاحك]
   - Secret Key: [مفتاحك السري]
   - Testnet: نعم (للتجربة) / لا (للتداول الحقيقي)
5. اضغط "اختبار الاتصال"
6. إذا نجح، اضغط "حفظ"
```

### التداول على Binance

```python
# إنشاء أمر شراء
order = await adapter.create_order(
    symbol="BTCUSDT",
    order_type="market",  # أو "limit"
    side="buy",
    amount=0.001,  # 0.001 BTC
    price=None  # None للسوق، أو سعر محدد للحد
)

print("Order created:", order['id'])

# متابعة حالة الأمر
status = await adapter.get_order_status(order['id'], "BTCUSDT")
print("Order status:", status['status'])
```

---

## 🔵 ربط Bybit {#bybit}

### الخطوة 1: إنشاء API Key

1. سجل الدخول إلى [Bybit](https://www.bybit.com/)
2. اذهب إلى **Account** → **API**
3. اضغط **Create New Key**
4. احفظ API Key و Secret Key

### الخطوة 2: تفعيل Testnet

```bash
# Bybit Testnet
https://testnet.bybit.com/

# احصل على testnet API keys من هناك
```

### الخطوة 3: الربط

```python
from services.exchange_adapters.bybit_adapter import BybitAdapter

adapter = BybitAdapter(
    api_key="YOUR_BYBIT_KEY",
    api_secret="YOUR_BYBIT_SECRET",
    testnet=True
)

# اختبار
result = await adapter.test_connection()
print(result)
```

---

## 🟢 ربط OKX {#okx}

### الخطوة 1: إنشاء API Key

1. سجل الدخول إلى [OKX](https://www.okx.com/)
2. اذهب إلى **Account** → **API**
3. اضغط **Create API Key**
4. **مهم:** OKX يتطلب **Passphrase**
5. احفظ:
   - API Key
   - Secret Key
   - **Passphrase** (مهم جداً!)

### الخطوة 2: الربط

```python
from services.exchange_adapters.okx_adapter import OKXAdapter

adapter = OKXAdapter(
    api_key="YOUR_OKX_KEY",
    api_secret="YOUR_OKX_SECRET",
    passphrase="YOUR_PASSPHRASE",  # مطلوب لـ OKX
    testnet=True
)

result = await adapter.test_connection()
```

---

## 🤖 تكامل DeepSeek AI {#deepseek}

### الخطوة 1: الحصول على API Key

1. سجل في [DeepSeek Platform](https://platform.deepseek.com/)
2. اذهب إلى **API Keys**
3. أنشئ API Key جديد
4. احفظه

### الخطوة 2: إضافة المفتاح

```bash
# في backend/.env
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

### الخطوة 3: استخدام DeepSeek

#### تحليل السوق

```python
from services.ai.deepseek_integration import deepseek_ai

# تحليل اتجاه السوق
analysis = await deepseek_ai.analyze_market_trend(
    symbol="BTCUSDT",
    market_data={
        "price": 95000,
        "change_24h_percent": 2.5,
        "volume_24h": 50000000000,
        "high_24h": 96000,
        "low_24h": 93000
    }
)

print("Trend:", analysis['trend'])
print("Confidence:", analysis['trading_recommendation']['confidence'])
print("Entry Zone:", analysis['trading_recommendation']['entry_zone'])
```

#### توليد استراتيجية تداول

```python
strategy = await deepseek_ai.generate_trading_strategy(
    portfolio={
        "total_balance": 10000,
        "available_balance": 8000,
        "invested_balance": 2000,
        "total_pnl": 150
    },
    market_conditions=[
        {"symbol": "BTCUSDT", "price": 95000, "change_24h_percent": 2.5},
        {"symbol": "ETHUSDT", "price": 3500, "change_24h_percent": 1.8}
    ],
    risk_profile="moderate"
)

print("Strategy:", strategy['strategy_summary'])
print("Opportunities:", strategy['trading_opportunities'])
```

#### تقييم مخاطر صفقة

```python
risk = await deepseek_ai.assess_trade_risk(
    trade_details={
        "symbol": "BTCUSDT",
        "side": "buy",
        "amount": 0.1,
        "price": 95000,
        "total_value": 9500,
        "percentage_of_portfolio": 95
    },
    portfolio={"total_balance": 10000},
    market_context={}
)

print("Risk Level:", risk['risk_assessment']['overall_risk'])
print("Recommendation:", risk['recommendation']['action'])
```

---

## 🛡️ استخدام Circuit Breaker {#circuit-breaker}

### ما هو Circuit Breaker؟

Circuit Breaker يوقف التداول تلقائياً عند حدوث مشاكل متكررة لحماية رأس المال.

### الأنواع المتوفرة

1. **API Circuit Breaker** - يوقف عند فشل 5 محاولات API
2. **Trade Execution Breaker** - يوقف عند فشل 3 عمليات تداول
3. **Risk Threshold Breaker** - يوقف عند تجاوز حدود المخاطر مرتين

### الاستخدام

```python
from services.circuit_breaker import trading_circuit_breaker

# تنفيذ صفقة مع حماية
try:
    result = await trading_circuit_breaker.execute_trade(
        create_trade_function,
        symbol="BTCUSDT",
        amount=0.1
    )
except CircuitBreakerOpenError as e:
    print("❌ Circuit Breaker OPEN:", e)
    # التداول متوقف مؤقتاً!

# التحقق من الحالة
status = trading_circuit_breaker.get_all_status()
print("Circuit Breaker Status:", status)

# إعادة تعيين يدوية (للمشرف فقط)
trading_circuit_breaker.reset_all()
```

### من API

```bash
# التحقق من الحالة
curl http://localhost:8001/api/circuit-breaker/status

# إعادة تعيين (يتطلب صلاحيات مشرف)
curl -X POST http://localhost:8001/api/circuit-breaker/reset \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 📊 مراقبة الأداء {#monitoring}

### Prometheus Metrics

```bash
# جميع المقاييس
curl http://localhost:8001/api/metrics

# مقاييس التداول
http_requests_total
trades_total
trade_execution_duration_seconds
trade_pnl

# مقاييس المنصات
exchange_api_calls_total
exchange_connection_status
exchange_api_latency_seconds

# مقاييس AI
ai_predictions_total
ai_prediction_confidence
ai_prediction_latency_seconds

# مقاييس Circuit Breaker
circuit_breaker_trips_total
risk_threshold_breaches_total
```

### Grafana Dashboards

```
URL: http://localhost:3001
Username: admin
Password: admin

Dashboards المتوفرة:
1. Trading Overview - نظرة عامة على التداول
2. Exchange Performance - أداء المنصات
3. AI Analytics - تحليلات الذكاء الاصطناعي
4. System Health - صحة النظام
```

### Health Checks

```bash
# صحة Backend
curl http://localhost:8001/api/health

# Response:
{
  "status": "ok",
  "timestamp": "2025-01-15T10:30:00Z",
  "service": "neon-trader-v7"
}

# جاهزية شاملة
curl http://localhost:8001/api/ready

# Response:
{
  "status": "ok",
  "checks": {
    "database": "connected",
    "ai_service": "ready",
    "market_data": "coingecko:ok",
    "exchanges": ["binance:testnet", "bybit:testnet"]
  }
}
```

---

## 🔄 سير العمل الكامل

### 1. إعداد أولي

```bash
# تثبيت المتطلبات
cd backend && pip install -r requirements.txt
cd frontend && yarn install

# إنشاء قاعدة البيانات
python backend/init_db.py

# ضبط المفاتيح في .env
```

### 2. ربط المنصات

```
واجهة التطبيق → المنصات → إضافة منصة → Binance/Bybit/OKX
```

### 3. اختبار على Testnet

```bash
# تفعيل testnet
is_testnet: true

# تنفيذ صفقة تجريبية
symbol: BTCUSDT
amount: 0.001
```

### 4. المراقبة

```bash
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001
# Logs: tail -f backend/logs/app.log
```

### 5. التداول الحقيقي

```bash
# تغيير إلى live
is_testnet: false

# ✅ تأكد من:
- Circuit Breaker يعمل
- Risk limits محددة
- Stop losses مفعلة
```

---

## ⚠️ تحذيرات مهمة

### الأمان

1. **لا تشارك API Keys أبداً**
2. **استخدم IP Whitelist**
3. **فعّل 2FA دائماً**
4. **ابدأ بـ testnet**
5. **راقب Circuit Breaker**

### إدارة المخاطر

1. **لا تستثمر أكثر من 5% في صفقة واحدة**
2. **استخدم Stop Loss دائماً**
3. **راقب التقلبات**
4. **تابع Circuit Breaker trips**

### الصيانة

1. **نسخ احتياطي يومي لقاعدة البيانات**
2. **مراقبة اللوجات**
3. **تحديث المكتبات**
4. **مراجعة Prometheus alerts**

---

## 🆘 استكشاف الأخطاء الشائعة

### خطأ: "Exchange connection failed"

```bash
# تحقق من:
1. صحة API Keys
2. صلاحيات API (Trading enabled?)
3. IP Whitelist (إذا كان مفعلاً)
4. استخدم testnet أولاً

# اختبار يدوي
python backend/test_exchange.py
```

### خطأ: "DeepSeek API error"

```bash
# تحقق من:
1. DEEPSEEK_API_KEY في .env
2. الرصيد في حساب DeepSeek
3. Rate limits

# اختبار
curl https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY"
```

### خطأ: "Circuit Breaker OPEN"

```bash
# السبب: كثرة الفشل في العمليات

# الحل:
1. تحقق من اللوجات
2. أصلح المشكلة الأساسية
3. أعد تعيين Circuit Breaker

curl -X POST http://localhost:8001/api/circuit-breaker/reset
```

---

## 📞 الدعم الفني

### اللوجات

```bash
# Backend logs
tail -f /var/log/supervisor/backend.*.log

# Application logs
tail -f backend/logs/app.log

# Trading logs
grep "trade_execution" backend/logs/app.log
```

### التشخيص

```bash
# صحة النظام
curl http://localhost:8001/api/health

# حالة المنصات
curl http://localhost:8001/api/platforms \
  -H "Authorization: Bearer YOUR_TOKEN"

# مقاييس
curl http://localhost:8001/api/metrics | grep trade
```

---

## ✅ Checklist قبل الإنتاج

- [ ] قاعدة البيانات PostgreSQL جاهزة
- [ ] جميع API Keys مُضافة ومُشفرة
- [ ] Testnet اختُبر بنجاح
- [ ] Circuit Breaker يعمل
- [ ] Prometheus + Grafana مُفعّلين
- [ ] النسخ الاحتياطية التلقائية مُفعّلة
- [ ] SSL/HTTPS مُفعّل
- [ ] Firewall مُضبوط
- [ ] Monitoring Alerts مُفعّلة
- [ ] توثيق كامل للفريق

---

**Happy Trading! 🚀📈**

*تذكر: التداول ينطوي على مخاطر. استخدم المنصة بحكمة.*
