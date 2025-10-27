import requests
import sys
import json
import uuid
from datetime import datetime

class NeonTraderComprehensiveTester:
    def __init__(self, base_url="https://neon-trader-2.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.access_token = None
        self.user_id = None
        self.test_user_email = f"comprehensive_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_username = f"comp_test_{uuid.uuid4().hex[:8]}"
        self.test_password = "testpass123"
        self.created_platform_id = None
        self.functionality_analysis = {
            "real_features": [],
            "mock_features": [],
            "broken_features": [],
            "percentage_real": 0
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def get_auth_headers(self):
        """Get authorization headers with JWT token"""
        if not self.access_token:
            return {}
        return {'Authorization': f'Bearer {self.access_token}'}

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("\n🔐 Setting up authentication...")
        
        # Register user
        registration_data = {
            "email": self.test_user_email,
            "username": self.test_user_username,
            "password": self.test_password,
            "confirm_password": self.test_password
        }
        
        success, response = self.run_test("User Registration", "POST", "/auth/register", 200, registration_data)
        
        if success and response:
            self.access_token = response.get('access_token')
            self.user_id = response.get('user_id')
            print(f"✅ Authentication setup complete - User ID: {self.user_id}")
            return True
        else:
            print("❌ Authentication setup failed")
            return False

    def test_market_data_functionality(self):
        """Test market data to determine if it's real or mock"""
        print("\n📊 Testing Market Data Functionality...")
        
        # Test Bitcoin price
        success, btc_data = self.run_test("Bitcoin Market Data", "GET", "/market/BTCUSDT", 200)
        if success and btc_data:
            btc_price = btc_data.get('price', 0)
            data_source = btc_data.get('data_source', 'unknown')
            
            if btc_price == 100.0:
                self.functionality_analysis["mock_features"].append("Market Data - Bitcoin showing mock price $100")
                print("   ⚠️ MOCK DATA DETECTED: Bitcoin price is $100 (unrealistic)")
            elif btc_price > 40000:
                self.functionality_analysis["real_features"].append(f"Market Data - Bitcoin realistic price ${btc_price}")
                print(f"   ✅ REAL DATA: Bitcoin price ${btc_price} is realistic")
            else:
                self.functionality_analysis["mock_features"].append(f"Market Data - Bitcoin suspicious price ${btc_price}")
                print(f"   ⚠️ SUSPICIOUS: Bitcoin price ${btc_price} seems unrealistic")
            
            print(f"   Data Source: {data_source}")
        
        # Test multiple asset types
        success, asset_types = self.run_test("Asset Types", "GET", "/market/types/all", 200)
        if success and asset_types:
            total_symbols = sum(len(data.get('symbols', [])) for data in asset_types.values())
            self.functionality_analysis["real_features"].append(f"Asset Types - {len(asset_types)} types with {total_symbols} symbols")
            print(f"   ✅ COMPREHENSIVE: {len(asset_types)} asset types with {total_symbols} total symbols")

    def test_trading_functionality(self):
        """Test trading system to determine if it's real or paper trading"""
        print("\n💰 Testing Trading Functionality...")
        
        if not self.access_token:
            print("❌ No authentication token available")
            return
        
        # Create a trade
        trade_data = {
            "symbol": "BTCUSDT",
            "trade_type": "buy",
            "order_type": "market",
            "quantity": 0.01,
            "stop_loss": 42000,
            "take_profit": 45000
        }
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Create Trade", "POST", "/trades", 200, trade_data, auth_headers)
        
        if success and response and 'trade' in response:
            trade = response['trade']
            platform = trade.get('platform', '')
            execution_type = trade.get('execution_type', 'unknown')
            current_market_price = trade.get('current_market_price', 0)
            
            if 'paper' in platform.lower() or execution_type == 'paper':
                self.functionality_analysis["mock_features"].append(f"Trading System - Paper trading only (platform: {platform})")
                print(f"   ⚠️ PAPER TRADING: Platform '{platform}', execution type '{execution_type}'")
            else:
                self.functionality_analysis["real_features"].append(f"Trading System - Real trading (platform: {platform})")
                print(f"   ✅ REAL TRADING: Platform '{platform}', execution type '{execution_type}'")
            
            if current_market_price > 40000:
                print(f"   ✅ REALISTIC PRICE: Current market price ${current_market_price}")
            elif current_market_price == 100:
                print(f"   ⚠️ MOCK PRICE: Current market price ${current_market_price}")

    def test_platform_integration(self):
        """Test platform integration functionality"""
        print("\n🔗 Testing Platform Integration...")
        
        if not self.access_token:
            print("❌ No authentication token available")
            return
        
        # Add a platform
        platform_data = {
            "name": "Test Binance Integration",
            "platform_type": "binance",
            "api_key": "test_api_key_123",
            "secret_key": "test_secret_key_456",
            "is_testnet": True
        }
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Add Platform", "POST", "/platforms", 200, platform_data, auth_headers)
        
        if success and response and 'platform' in response:
            self.created_platform_id = response['platform'].get('id')
            is_testnet = response['platform'].get('is_testnet', True)
            
            if is_testnet:
                self.functionality_analysis["mock_features"].append("Platform Integration - Testnet mode only")
                print("   ⚠️ TESTNET MODE: Platform configured for testnet only")
            else:
                self.functionality_analysis["real_features"].append("Platform Integration - Live trading enabled")
                print("   ✅ LIVE MODE: Platform configured for live trading")
            
            # Test platform connection
            if self.created_platform_id:
                success, test_response = self.run_test("Test Platform Connection", "PUT", f"/platforms/{self.created_platform_id}/test", 200, headers=auth_headers)
                
                if success and test_response:
                    connection_success = test_response.get('success', False)
                    message = test_response.get('message', '')
                    connection_details = test_response.get('connection_details', {})
                    
                    if connection_success and 'demo' not in connection_details.get('status', ''):
                        self.functionality_analysis["real_features"].append("Platform Connection - Real API connection working")
                        print("   ✅ REAL CONNECTION: Platform API connection successful")
                    else:
                        self.functionality_analysis["mock_features"].append("Platform Connection - Demo/mock connection only")
                        print(f"   ⚠️ MOCK CONNECTION: {message}")

    def test_ai_functionality(self):
        """Test AI features to determine if they're real or mock"""
        print("\n🤖 Testing AI Functionality...")
        
        # Test AI market analysis (public)
        analysis_data = {
            "symbol": "BTCUSDT",
            "timeframe": "1h"
        }
        success, response = self.run_test("AI Market Analysis", "POST", "/ai/analyze", 200, analysis_data, timeout=60)
        
        if success and response:
            analysis = response.get('analysis', '')
            
            if 'تحليل فني' in analysis and len(analysis) > 50:
                if 'السعر الحالي $100.0' in analysis:
                    self.functionality_analysis["mock_features"].append("AI Analysis - Using mock price data")
                    print("   ⚠️ MOCK AI: Analysis uses mock price data ($100)")
                else:
                    self.functionality_analysis["real_features"].append("AI Analysis - Real Arabic AI analysis")
                    print("   ✅ REAL AI: Generating Arabic technical analysis")
            else:
                self.functionality_analysis["mock_features"].append("AI Analysis - Generic/template responses")
                print("   ⚠️ TEMPLATE AI: Generic analysis responses")
        
        # Test daily plan (requires authentication)
        if self.access_token:
            auth_headers = self.get_auth_headers()
            success, response = self.run_test("AI Daily Plan", "GET", "/ai/daily-plan", 200, headers=auth_headers, timeout=60)
            
            if success and response:
                market_analysis = response.get('market_analysis', '')
                opportunities = response.get('opportunities', [])
                
                if len(market_analysis) > 20 and len(opportunities) > 0:
                    self.functionality_analysis["real_features"].append("AI Daily Plan - Comprehensive planning with opportunities")
                    print("   ✅ REAL AI PLANNING: Detailed daily plan with opportunities")
                else:
                    self.functionality_analysis["mock_features"].append("AI Daily Plan - Basic/template planning")
                    print("   ⚠️ BASIC PLANNING: Simple template-based planning")

    def test_smart_notifications(self):
        """Test smart notifications system"""
        print("\n🔔 Testing Smart Notifications...")
        
        if not self.access_token:
            print("❌ No authentication token available")
            return
        
        auth_headers = self.get_auth_headers()
        
        # Test creating smart alert
        success, response = self.run_test("Create Smart Alert", "POST", "/notifications/smart-alert", 200, headers=auth_headers, timeout=60)
        
        if success and response:
            notification = response.get('notification', {})
            analysis = response.get('analysis', '')
            opportunities = response.get('opportunities', [])
            
            if notification and len(analysis) > 50:
                self.functionality_analysis["real_features"].append("Smart Notifications - AI-powered alerts working")
                print("   ✅ REAL NOTIFICATIONS: AI-powered smart alerts functional")
            else:
                self.functionality_analysis["mock_features"].append("Smart Notifications - Basic notification system")
                print("   ⚠️ BASIC NOTIFICATIONS: Simple notification system")
        
        # Test getting notifications
        success, response = self.run_test("Get Notifications", "GET", "/notifications", 200, headers=auth_headers)
        
        if success:
            notifications_count = len(response) if isinstance(response, list) else 0
            print(f"   📊 Found {notifications_count} notifications")
        
        # Test trading opportunities
        success, response = self.run_test("Get Trading Opportunities", "GET", "/notifications/opportunities", 200, headers=auth_headers)
        
        if success and response:
            opportunities = response.get('opportunities', [])
            if len(opportunities) > 0:
                first_opp = opportunities[0]
                confidence = first_opp.get('confidence', 0)
                description = first_opp.get('description', '')
                
                if confidence > 70 and len(description) > 20:
                    self.functionality_analysis["real_features"].append("Trading Opportunities - Detailed opportunity analysis")
                    print(f"   ✅ DETAILED OPPORTUNITIES: {len(opportunities)} opportunities with analysis")
                else:
                    self.functionality_analysis["mock_features"].append("Trading Opportunities - Basic opportunity templates")
                    print(f"   ⚠️ BASIC OPPORTUNITIES: {len(opportunities)} template opportunities")

    def calculate_functionality_percentage(self):
        """Calculate percentage of real vs mock functionality"""
        total_features = len(self.functionality_analysis["real_features"]) + len(self.functionality_analysis["mock_features"]) + len(self.functionality_analysis["broken_features"])
        
        if total_features > 0:
            real_percentage = (len(self.functionality_analysis["real_features"]) / total_features) * 100
            mock_percentage = (len(self.functionality_analysis["mock_features"]) / total_features) * 100
            broken_percentage = (len(self.functionality_analysis["broken_features"]) / total_features) * 100
            
            self.functionality_analysis["percentage_real"] = round(real_percentage, 1)
            self.functionality_analysis["percentage_mock"] = round(mock_percentage, 1)
            self.functionality_analysis["percentage_broken"] = round(broken_percentage, 1)

    def print_comprehensive_analysis(self):
        """Print comprehensive analysis in Arabic"""
        print("\n" + "=" * 80)
        print("📋 تحليل شامل لوظائف تطبيق Neon Trader V7")
        print("=" * 80)
        
        self.calculate_functionality_percentage()
        
        print(f"\n📊 إحصائيات عامة:")
        print(f"   • إجمالي الاختبارات: {self.tests_run}")
        print(f"   • الاختبارات الناجحة: {self.tests_passed}")
        print(f"   • معدل النجاح: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🎯 تحليل الوظائف:")
        print(f"   • الوظائف الحقيقية: {len(self.functionality_analysis['real_features'])} ({self.functionality_analysis['percentage_real']}%)")
        print(f"   • الوظائف الوهمية: {len(self.functionality_analysis['mock_features'])} ({self.functionality_analysis['percentage_mock']}%)")
        print(f"   • الوظائف المعطلة: {len(self.functionality_analysis['broken_features'])} ({self.functionality_analysis['percentage_broken']}%)")
        
        print(f"\n✅ الوظائف الحقيقية العاملة:")
        for feature in self.functionality_analysis["real_features"]:
            print(f"   • {feature}")
        
        print(f"\n⚠️ الوظائف الوهمية/المحاكاة:")
        for feature in self.functionality_analysis["mock_features"]:
            print(f"   • {feature}")
        
        if self.functionality_analysis["broken_features"]:
            print(f"\n❌ الوظائف المعطلة:")
            for feature in self.functionality_analysis["broken_features"]:
                print(f"   • {feature}")
        
        print(f"\n🏆 التقييم النهائي:")
        if self.functionality_analysis["percentage_real"] >= 80:
            print("   🟢 التطبيق يحتوي على وظائف حقيقية بنسبة عالية")
        elif self.functionality_analysis["percentage_real"] >= 60:
            print("   🟡 التطبيق يحتوي على مزيج من الوظائف الحقيقية والوهمية")
        elif self.functionality_analysis["percentage_real"] >= 40:
            print("   🟠 التطبيق يحتوي على وظائف وهمية أكثر من الحقيقية")
        else:
            print("   🔴 التطبيق يعتمد بشكل أساسي على الوظائف الوهمية")

def main():
    print("🚀 بدء الفحص الشامل لتطبيق Neon Trader V7")
    print("=" * 60)
    
    tester = NeonTraderComprehensiveTester()
    
    # Setup authentication first
    if not tester.setup_authentication():
        print("❌ فشل في إعداد المصادقة - إنهاء الاختبار")
        return 1
    
    # Run comprehensive functionality tests
    print("\n🔍 بدء اختبار الوظائف الشاملة...")
    
    try:
        tester.test_market_data_functionality()
        tester.test_trading_functionality()
        tester.test_platform_integration()
        tester.test_ai_functionality()
        tester.test_smart_notifications()
    except Exception as e:
        print(f"❌ خطأ أثناء الاختبار: {e}")
    
    # Print comprehensive analysis
    tester.print_comprehensive_analysis()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())