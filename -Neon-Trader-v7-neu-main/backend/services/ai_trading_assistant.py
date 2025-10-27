"""
Neon Trader V7 - AI Trading Assistant
Enhanced AI-powered trading analysis and recommendations
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import httpx
from emergentintegrations import LLMManager

class AITradingAssistant:
    """Advanced AI assistant for trading analysis and recommendations"""
    
    def __init__(self, emergent_key: str):
        self.llm_manager = LLMManager(api_key=emergent_key)
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
    async def analyze_market_sentiment(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market sentiment using AI"""
        try:
            cache_key = f"sentiment_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]
            
            prompt = f"""
            تحليل معنويات السوق للرمز {symbol}:
            
            البيانات الحالية:
            - السعر: ${market_data.get('price', 0):,.2f}
            - التغيير 24س: {market_data.get('change_24h_percent', 0):+.2f}%
            - الحجم: ${market_data.get('volume_24h', 0):,}
            - أعلى سعر: ${market_data.get('high_24h', 0):,.2f}
            - أقل سعر: ${market_data.get('low_24h', 0):,.2f}
            
            قم بتحليل:
            1. المعنويات العامة (إيجابي/سلبي/محايد)
            2. قوة الاتجاه (1-10)
            3. مستويات الدعم والمقاومة
            4. التوصية (شراء/بيع/انتظار)
            5. سبب التوصية
            
            أجب بصيغة JSON فقط:
            {{
                "sentiment": "positive|negative|neutral",
                "trend_strength": 7,
                "support_level": 95000,
                "resistance_level": 105000,
                "recommendation": "buy|sell|hold",
                "confidence": 85,
                "reasoning": "سبب التحليل هنا",
                "target_price": 110000,
                "stop_loss": 92000,
                "timeframe": "short|medium|long"
            }}
            """
            
            response = await self._call_llm(prompt)
            analysis = self._parse_json_response(response)
            
            # Add timestamp and cache
            analysis['timestamp'] = datetime.now(timezone.utc).isoformat()
            analysis['symbol'] = symbol
            self.analysis_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logging.error(f"Market sentiment analysis failed: {e}")
            return self._fallback_analysis(symbol, market_data)
    
    async def generate_daily_strategy(self, user_portfolio: Dict[str, Any], market_conditions: List[Dict]) -> Dict[str, Any]:
        """Generate daily trading strategy based on portfolio and market conditions"""
        try:
            portfolio_summary = {
                "total_balance": user_portfolio.get('total_balance', 0),
                "invested": user_portfolio.get('invested_balance', 0),
                "daily_pnl": user_portfolio.get('daily_pnl', 0),
                "positions": len(user_portfolio.get('positions', []))
            }
            
            prompt = f"""
            إنشاء استراتيجية تداول يومية:
            
            ملخص المحفظة:
            - الرصيد الإجمالي: ${portfolio_summary['total_balance']:,.2f}
            - المبلغ المستثمر: ${portfolio_summary['invested']:,.2f}
            - الربح/الخسارة اليومية: ${portfolio_summary['daily_pnl']:+,.2f}
            - عدد المراكز: {portfolio_summary['positions']}
            
            ظروف السوق:
            {self._format_market_conditions(market_conditions)}
            
            أنشئ استراتيجية تتضمن:
            1. تقييم المخاطر العام
            2. الفرص المتاحة (3-5 فرص)
            3. مستوى المخاطرة الموصى به
            4. أهداف اليوم
            5. تحذيرات مهمة
            
            الرد بصيغة JSON:
            {{
                "risk_level": "low|medium|high",
                "market_outlook": "bullish|bearish|neutral",
                "recommended_allocation": {{"crypto": 60, "stocks": 30, "cash": 10}},
                "opportunities": [
                    {{
                        "symbol": "BTCUSDT",
                        "type": "breakout",
                        "confidence": 80,
                        "entry_range": [94000, 96000],
                        "target": 102000,
                        "stop_loss": 91000,
                        "reasoning": "سبب الفرصة"
                    }}
                ],
                "daily_goals": ["هدف 1", "هدف 2"],
                "warnings": ["تحذير 1", "تحذير 2"],
                "strategy_summary": "ملخص الاستراتيجية"
            }}
            """
            
            response = await self._call_llm(prompt)
            strategy = self._parse_json_response(response)
            
            strategy['generated_at'] = datetime.now(timezone.utc).isoformat()
            strategy['valid_until'] = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            
            return strategy
            
        except Exception as e:
            logging.error(f"Daily strategy generation failed: {e}")
            return self._fallback_strategy()
    
    async def analyze_trade_opportunity(self, symbol: str, trade_type: str, market_data: Dict) -> Dict[str, Any]:
        """Analyze specific trade opportunity"""
        try:
            prompt = f"""
            تحليل فرصة تداول:
            
            الرمز: {symbol}
            نوع التداول: {trade_type}
            السعر الحالي: ${market_data.get('price', 0):,.2f}
            التغيير: {market_data.get('change_24h_percent', 0):+.2f}%
            
            حلل:
            1. جودة الفرصة (1-100)
            2. نسبة المخاطرة للعائد
            3. نقطة الدخول المثلى
            4. أهداف الربح
            5. وقف الخسارة
            6. الإطار الزمني المتوقع
            
            JSON Response:
            {{
                "opportunity_score": 85,
                "risk_reward_ratio": 2.5,
                "optimal_entry": 95500,
                "targets": [98000, 101000, 104000],
                "stop_loss": 92000,
                "timeframe_hours": 24,
                "analysis": "تحليل مفصل للفرصة",
                "pros": ["إيجابية 1", "إيجابية 2"],
                "cons": ["سلبية 1", "سلبية 2"],
                "market_conditions": "مناسب|غير مناسب|محايد"
            }}
            """
            
            response = await self._call_llm(prompt)
            analysis = self._parse_json_response(response)
            
            analysis['symbol'] = symbol
            analysis['trade_type'] = trade_type
            analysis['analyzed_at'] = datetime.now(timezone.utc).isoformat()
            
            return analysis
            
        except Exception as e:
            logging.error(f"Trade opportunity analysis failed: {e}")
            return self._fallback_trade_analysis(symbol, trade_type)
    
    async def risk_assessment(self, portfolio: Dict, proposed_trade: Dict) -> Dict[str, Any]:
        """Assess risk of proposed trade against portfolio"""
        try:
            total_balance = portfolio.get('total_balance', 0)
            trade_amount = proposed_trade.get('quantity', 0) * proposed_trade.get('entry_price', 0)
            
            risk_percentage = (trade_amount / total_balance) * 100 if total_balance > 0 else 0
            
            prompt = f"""
            تقييم مخاطر التداول:
            
            المحفظة:
            - الرصيد: ${total_balance:,.2f}
            - المواضع الحالية: {len(portfolio.get('positions', []))}
            
            التداول المقترح:
            - الرمز: {proposed_trade.get('symbol')}
            - النوع: {proposed_trade.get('trade_type')}
            - المبلغ: ${trade_amount:,.2f}
            - النسبة من المحفظة: {risk_percentage:.1f}%
            
            قيم:
            1. مستوى المخاطرة (منخفض/متوسط/عالي)
            2. التوصية (موافق/مشروط/مرفوض)
            3. التعديلات المقترحة
            4. تحذيرات المخاطر
            
            JSON:
            {{
                "risk_level": "low|medium|high",
                "recommendation": "approve|conditional|reject",
                "risk_score": 65,
                "suggested_adjustments": {{
                    "position_size": 0.8,
                    "stop_loss": 91000,
                    "take_profit": 98000
                }},
                "warnings": ["تحذير 1", "تحذير 2"],
                "max_loss_estimate": 2500,
                "portfolio_impact": 5.2,
                "reasoning": "سبب التقييم"
            }}
            """
            
            response = await self._call_llm(prompt)
            assessment = self._parse_json_response(response)
            
            assessment['assessed_at'] = datetime.now(timezone.utc).isoformat()
            assessment['trade_amount'] = trade_amount
            assessment['portfolio_percentage'] = risk_percentage
            
            return assessment
            
        except Exception as e:
            logging.error(f"Risk assessment failed: {e}")
            return self._fallback_risk_assessment(risk_percentage)
    
    async def market_news_analysis(self, news_data: List[Dict]) -> Dict[str, Any]:
        """Analyze market news for trading insights"""
        try:
            if not news_data:
                return {"impact": "neutral", "confidence": 0}
            
            news_summary = "\n".join([
                f"- {item.get('title', '')}: {item.get('summary', '')}"
                for item in news_data[:5]  # Analyze top 5 news
            ])
            
            prompt = f"""
            تحليل تأثير الأخبار على السوق:
            
            الأخبار الحديثة:
            {news_summary}
            
            حدد:
            1. التأثير العام (إيجابي/سلبي/محايد)
            2. القطاعات المتأثرة
            3. الرموز المتأثرة
            4. درجة الثقة في التحليل
            5. التوصيات قصيرة المدى
            
            JSON:
            {{
                "overall_impact": "positive|negative|neutral",
                "confidence": 80,
                "affected_sectors": ["crypto", "tech"],
                "affected_symbols": ["BTCUSDT", "ETHUSDT"],
                "short_term_outlook": "bullish|bearish|sideways",
                "key_factors": ["عامل 1", "عامل 2"],
                "trading_recommendations": ["توصية 1", "توصية 2"]
            }}
            """
            
            response = await self._call_llm(prompt)
            return self._parse_json_response(response)
            
        except Exception as e:
            logging.error(f"News analysis failed: {e}")
            return {"impact": "neutral", "confidence": 0}
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with error handling"""
        try:
            response = await self.llm_manager.generate_text(
                prompt=prompt,
                model="gpt-4",
                temperature=0.3,
                max_tokens=1500
            )
            return response
        except Exception as e:
            logging.error(f"LLM call failed: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response with fallback"""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logging.error(f"JSON parsing failed: {e}")
            return {"error": "Failed to parse AI response"}
    
    def _format_market_conditions(self, conditions: List[Dict]) -> str:
        """Format market conditions for AI prompt"""
        if not conditions:
            return "لا توجد بيانات سوق متاحة"
        
        formatted = []
        for condition in conditions:
            formatted.append(
                f"- {condition.get('symbol')}: ${condition.get('price'):.2f} "
                f"({condition.get('change_24h_percent', 0):+.1f}%)"
            )
        return "\n".join(formatted)
    
    def _fallback_analysis(self, symbol: str, market_data: Dict) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        change = market_data.get('change_24h_percent', 0)
        
        return {
            "sentiment": "positive" if change > 0 else "negative" if change < 0 else "neutral",
            "trend_strength": min(10, max(1, abs(change) * 2)),
            "recommendation": "hold",
            "confidence": 30,
            "reasoning": "تحليل أساسي بناءً على التغيير السعري",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fallback": True
        }
    
    def _fallback_strategy(self) -> Dict[str, Any]:
        """Fallback strategy when AI fails"""
        return {
            "risk_level": "medium",
            "market_outlook": "neutral",
            "opportunities": [],
            "daily_goals": ["مراقبة السوق", "إدارة المخاطر"],
            "warnings": ["استخدم تحليل احتياطي"],
            "strategy_summary": "استراتيجية محافظة - مراقبة السوق",
            "fallback": True
        }
    
    def _fallback_trade_analysis(self, symbol: str, trade_type: str) -> Dict[str, Any]:
        """Fallback trade analysis"""
        return {
            "opportunity_score": 50,
            "risk_reward_ratio": 1.5,
            "analysis": "تحليل احتياطي - يُنصح بالحذر",
            "market_conditions": "محايد",
            "symbol": symbol,
            "trade_type": trade_type,
            "fallback": True
        }
    
    def _fallback_risk_assessment(self, risk_percentage: float) -> Dict[str, Any]:
        """Fallback risk assessment"""
        risk_level = "high" if risk_percentage > 20 else "medium" if risk_percentage > 10 else "low"
        
        return {
            "risk_level": risk_level,
            "recommendation": "conditional" if risk_level != "high" else "reject",
            "risk_score": min(100, risk_percentage * 3),
            "reasoning": f"تقييم تلقائي بناءً على نسبة {risk_percentage:.1f}%",
            "fallback": True
        }

# Global AI assistant instance
ai_assistant = None

def get_ai_assistant(emergent_key: str) -> AITradingAssistant:
    """Get or create AI assistant instance"""
    global ai_assistant
    if not ai_assistant:
        ai_assistant = AITradingAssistant(emergent_key)
    return ai_assistant