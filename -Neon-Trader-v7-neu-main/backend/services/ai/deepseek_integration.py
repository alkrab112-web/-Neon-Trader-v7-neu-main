"""
DeepSeek AI Integration for Trading Analysis
Provides advanced AI capabilities using DeepSeek models
"""

import os
import logging
import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DeepSeekAI:
    """DeepSeek AI client for trading analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('DEEPSEEK_API_KEY')
        self.base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        self.model = "deepseek-chat"  # or deepseek-coder for technical analysis
        
        if not self.api_key:
            logger.warning("DeepSeek API key not found")
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text using DeepSeek"""
        try:
            if not self.api_key:
                raise Exception("DeepSeek API key not configured")
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model or self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    
                    return {
                        'content': content,
                        'model': data['model'],
                        'usage': data.get('usage', {}),
                        'success': True
                    }
                else:
                    logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                    return {
                        'success': False,
                        'error': f"API returned {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"DeepSeek generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_market_trend(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        historical_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Analyze market trend using DeepSeek"""
        try:
            prompt = f"""
            تحليل اتجاه السوق المتقدم للرمز {symbol}:
            
            البيانات الحالية:
            - السعر: ${market_data.get('price', 0):,.2f}
            - التغيير 24س: {market_data.get('change_24h_percent', 0):+.2f}%
            - الحجم: ${market_data.get('volume_24h', 0):,.0f}
            - أعلى سعر: ${market_data.get('high_24h', 0):,.2f}
            - أدنى سعر: ${market_data.get('low_24h', 0):,.2f}
            
            قم بتحليل شامل يتضمن:
            1. تحديد الاتجاه الحالي (صاعد/هابط/جانبي) مع التفسير
            2. قوة الاتجاه والزخم (momentum)
            3. مستويات فيبوناتشي المهمة
            4. مستويات الدعم والمقاومة الرئيسية
            5. إشارات المؤشرات الفنية (RSI, MACD, Moving Averages)
            6. توقعات قصيرة ومتوسطة المدى
            7. توصية تداول مفصلة مع نقاط الدخول والخروج
            
            الرجاء الرد بصيغة JSON:
            {{
                "trend": "bullish|bearish|sideways",
                "trend_strength": "strong|moderate|weak",
                "momentum": {{"value": 0-100, "direction": "increasing|decreasing"}},
                "key_levels": {{
                    "support": [level1, level2, level3],
                    "resistance": [level1, level2, level3],
                    "fibonacci_levels": {{"0.382": value, "0.5": value, "0.618": value}}
                }},
                "technical_indicators": {{
                    "rsi": {{"value": 50, "signal": "neutral|oversold|overbought"}},
                    "macd": {{"signal": "bullish|bearish|neutral"}},
                    "moving_averages": {{"ma50": value, "ma200": value, "signal": "golden_cross|death_cross|neutral"}}
                }},
                "price_targets": {{
                    "short_term": {{"high": value, "low": value, "timeframe": "1-3 days"}},
                    "medium_term": {{"high": value, "low": value, "timeframe": "1-2 weeks"}}
                }},
                "trading_recommendation": {{
                    "action": "strong_buy|buy|hold|sell|strong_sell",
                    "confidence": 0-100,
                    "entry_zone": {{"min": value, "max": value}},
                    "targets": [target1, target2, target3],
                    "stop_loss": value,
                    "risk_reward_ratio": value
                }},
                "analysis_summary": "تحليل مفصل بالعربية",
                "key_factors": ["عامل 1", "عامل 2", "عامل 3"],
                "risks": ["خطر 1", "خطر 2"]
            }}
            """
            
            system_prompt = "أنت محلل مالي خبير متخصص في التحليل الفني والتنبؤ بحركة الأسواق المالية."
            
            result = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2500
            )
            
            if result['success']:
                # Parse JSON from response
                analysis = self._extract_json(result['content'])
                analysis['analyzed_at'] = datetime.utcnow().isoformat()
                analysis['symbol'] = symbol
                analysis['model'] = 'deepseek'
                return analysis
            else:
                return self._fallback_analysis(symbol, market_data)
                
        except Exception as e:
            logger.error(f"DeepSeek market analysis failed: {e}")
            return self._fallback_analysis(symbol, market_data)
    
    async def generate_trading_strategy(
        self,
        portfolio: Dict[str, Any],
        market_conditions: List[Dict[str, Any]],
        risk_profile: str = "moderate"
    ) -> Dict[str, Any]:
        """Generate comprehensive trading strategy"""
        try:
            market_summary = self._format_market_data(market_conditions)
            
            prompt = f"""
            إنشاء استراتيجية تداول متقدمة:
            
            معلومات المحفظة:
            - الرصيد الإجمالي: ${portfolio.get('total_balance', 0):,.2f}
            - المتاح: ${portfolio.get('available_balance', 0):,.2f}
            - المستثمر: ${portfolio.get('invested_balance', 0):,.2f}
            - الربح/الخسارة: ${portfolio.get('total_pnl', 0):+,.2f}
            
            ملف المخاطر: {risk_profile}
            
            ظروف السوق:
            {market_summary}
            
            أنشئ استراتيجية تداول شاملة تتضمن:
            1. تحليل الوضع العام للسوق
            2. توزيع رأس المال الأمثل
            3. فرص التداول (5-7 فرص محددة)
            4. إدارة المخاطر والتحوط
            5. خطة الدخول والخروج
            6. أهداف قصيرة ومتوسطة المدى
            7. سيناريوهات بديلة
            
            JSON Format:
            {{
                "market_analysis": {{
                    "overall_sentiment": "bullish|bearish|neutral",
                    "volatility": "high|medium|low",
                    "trend": "uptrend|downtrend|sideways",
                    "key_drivers": ["driver1", "driver2"]
                }},
                "capital_allocation": {{
                    "crypto": percentage,
                    "stocks": percentage,
                    "forex": percentage,
                    "cash": percentage
                }},
                "trading_opportunities": [
                    {{
                        "symbol": "BTCUSDT",
                        "type": "breakout|reversal|momentum|arbitrage",
                        "confidence": 0-100,
                        "timeframe": "short|medium|long",
                        "entry": {{"min": value, "max": value}},
                        "targets": [t1, t2, t3],
                        "stop_loss": value,
                        "position_size": "percentage of capital",
                        "reasoning": "سبب الفرصة",
                        "expected_return": percentage,
                        "risk_level": "low|medium|high"
                    }}
                ],
                "risk_management": {{
                    "max_position_size": percentage,
                    "max_daily_loss": percentage,
                    "diversification_strategy": "description",
                    "hedge_recommendations": ["hedge1", "hedge2"]
                }},
                "execution_plan": {{
                    "priority_trades": ["symbol1", "symbol2"],
                    "timing": "best time to enter",
                    "order_types": "recommended order types"
                }},
                "goals": {{
                    "daily_target": percentage,
                    "weekly_target": percentage,
                    "monthly_target": percentage
                }},
                "alternative_scenarios": [
                    {{"condition": "if market drops", "action": "what to do"}}
                ],
                "strategy_summary": "ملخص الاستراتيجية بالعربية"
            }}
            """
            
            system_prompt = "أنت استراتيجي تداول محترف مع خبرة 15+ سنة في الأسواق المالية."
            
            result = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=3000
            )
            
            if result['success']:
                strategy = self._extract_json(result['content'])
                strategy['generated_at'] = datetime.utcnow().isoformat()
                strategy['risk_profile'] = risk_profile
                return strategy
            else:
                return self._fallback_strategy()
                
        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            return self._fallback_strategy()
    
    async def assess_trade_risk(
        self,
        trade_details: Dict[str, Any],
        portfolio: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive trade risk assessment"""
        try:
            prompt = f"""
            تقييم مخاطر التداول المتقدم:
            
            تفاصيل التداول:
            - الرمز: {trade_details.get('symbol')}
            - النوع: {trade_details.get('side')}
            - الكمية: {trade_details.get('amount')}
            - السعر: ${trade_details.get('price', 0):,.2f}
            - قيمة الصفقة: ${trade_details.get('total_value', 0):,.2f}
            
            المحفظة:
            - الرصيد: ${portfolio.get('total_balance', 0):,.2f}
            - نسبة الصفقة: {trade_details.get('percentage_of_portfolio', 0):.2f}%
            
            قيّم المخاطر بشكل شامل:
            1. مستوى المخاطرة الإجمالي
            2. تحليل نسبة المخاطرة للعائد
            3. تأثير على المحفظة
            4. احتمالية النجاح
            5. أسوأ سيناريو ممكن
            6. توصيات للتحسين
            
            JSON Response:
            {{
                "risk_assessment": {{
                    "overall_risk": "low|medium|high|very_high",
                    "risk_score": 0-100,
                    "risk_factors": [
                        {{"factor": "name", "severity": "low|medium|high", "description": "desc"}}
                    ]
                }},
                "risk_reward": {{
                    "ratio": value,
                    "expected_return": percentage,
                    "max_loss": value,
                    "probability_of_profit": percentage
                }},
                "portfolio_impact": {{
                    "position_size_rating": "appropriate|too_large|too_small",
                    "diversification_impact": "positive|negative|neutral",
                    "correlation_risk": "description"
                }},
                "worst_case_scenario": {{
                    "max_potential_loss": value,
                    "portfolio_percentage_loss": percentage,
                    "recovery_timeframe": "estimation"
                }},
                "recommendation": {{
                    "action": "approve|modify|reject",
                    "confidence": 0-100,
                    "reasoning": "detailed reasoning",
                    "modifications": [
                        {{"aspect": "what to change", "suggestion": "how to change"}}
                    ]
                }},
                "warnings": ["warning1", "warning2"],
                "summary": "ملخص التقييم بالعربية"
            }}
            """
            
            system_prompt = "أنت خبير في إدارة المخاطر المالية متخصص في تقييم صفقات التداول."
            
            result = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,  # Lower temperature for risk assessment
                max_tokens=2000
            )
            
            if result['success']:
                assessment = self._extract_json(result['content'])
                assessment['assessed_at'] = datetime.utcnow().isoformat()
                return assessment
            else:
                return self._fallback_risk_assessment(trade_details)
                
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return self._fallback_risk_assessment(trade_details)
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response"""
        try:
            # Find JSON block
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
            return {}
        except Exception as e:
            logger.error(f"JSON extraction failed: {e}")
            return {}
    
    def _format_market_data(self, data: List[Dict]) -> str:
        """Format market data for prompt"""
        formatted = []
        for item in data[:10]:  # Limit to 10 items
            formatted.append(
                f"- {item.get('symbol')}: ${item.get('price', 0):.2f} "
                f"({item.get('change_24h_percent', 0):+.2f}%)"
            )
        return "\n".join(formatted)
    
    def _fallback_analysis(self, symbol: str, market_data: Dict) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        change = market_data.get('change_24h_percent', 0)
        return {
            "trend": "bullish" if change > 0 else "bearish" if change < 0 else "sideways",
            "trend_strength": "moderate",
            "confidence": 30,
            "analysis_summary": "تحليل احتياطي - البيانات محدودة",
            "fallback": True
        }
    
    def _fallback_strategy(self) -> Dict[str, Any]:
        return {
            "market_analysis": {"overall_sentiment": "neutral"},
            "trading_opportunities": [],
            "strategy_summary": "استراتيجية محافظة - انتظار ظروف أفضل",
            "fallback": True
        }
    
    def _fallback_risk_assessment(self, trade: Dict) -> Dict[str, Any]:
        return {
            "risk_assessment": {"overall_risk": "medium", "risk_score": 50},
            "recommendation": {"action": "review", "confidence": 40},
            "summary": "تقييم احتياطي - يُنصح بمراجعة يدوية",
            "fallback": True
        }

# Global instance
deepseek_ai = DeepSeekAI()
