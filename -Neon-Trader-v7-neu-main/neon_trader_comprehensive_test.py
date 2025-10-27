#!/usr/bin/env python3
"""
Neon Trader V7 Comprehensive Backend Testing
اختبار شامل لتطبيق Neon Trader V7

Tests requested by user in Arabic:
1. Health Check: /api/health و /api/ready
2. Authentication: تسجيل مستخدم جديد، تسجيل الدخول، JWT tokens
3. Market Data: /api/market/BTCUSDT
4. Portfolio: /api/portfolio
5. Platforms: /api/platforms
6. WebSocket: /ws endpoint إن أمكن

Focus: Verify all basic functions work after recent fixes
"""

import requests
import json
import uuid
import time
import websocket
import threading
from datetime import datetime
from typing import Dict, Any, Tuple

class NeonTraderComprehensiveTester:
    def __init__(self):
        # Use the production URL from frontend/.env
        self.base_url = "https://neon-trader-2.preview.emergentagent.com/api"
        self.ws_url = "wss://neon-trader-2.preview.emergentagent.com/ws"
        
        # Test counters
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        
        # Authentication data
        self.access_token = None
        self.user_id = None
        self.test_user_email = f"neonuser_{uuid.uuid4().hex[:8]}@trader.com"
        self.test_user_username = f"neontrader_{uuid.uuid4().hex[:6]}"
        self.test_password = "NeonTrader2024!"
        
        # Test results storage
        self.test_results = {}
        
        print(f"🚀 Neon Trader V7 Comprehensive Testing")
        print(f"📧 Test User: {self.test_user_email}")
        print(f"👤 Username: {self.test_user_username}")
        print(f"🌐 Backend URL: {self.base_url}")
        print("=" * 70)

    def log_test(self, name: str, success: bool, response_time: float, details: str = ""):
        """Log test result with timing"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            self.critical_failures.append(f"{name}: {details}")
        
        self.test_results[name] = {
            'success': success,
            'response_time': response_time,
            'details': details
        }
        
        print(f"{status} {name} ({response_time:.2f}s)")
        if details and not success:
            print(f"    💬 {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, timeout: int = 10) -> Tuple[bool, Dict, float]:
        """Make HTTP request with timing and error handling"""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            # Check if response time is reasonable (< 3 seconds as requested)
            if response_time > 3.0:
                print(f"    ⚠️ Slow response: {response_time:.2f}s (> 3s limit)")
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return response.status_code in [200, 201], response_data, response_time
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return False, {"error": f"Request timeout after {timeout}s"}, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return False, {"error": str(e)}, response_time

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with JWT token"""
        if not self.access_token:
            return {}
        return {'Authorization': f'Bearer {self.access_token}'}

    # ========== 1. Health Check Tests ==========
    
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        success, response, response_time = self.make_request('GET', '/health')
        
        details = ""
        if success:
            if 'status' in response and response['status'] == 'ok':
                details = f"Status: {response['status']}, Service: {response.get('service', 'unknown')}"
            else:
                success = False
                details = "Health check returned but status not 'ok'"
        else:
            details = f"Health check failed: {response.get('error', 'Unknown error')}"
        
        self.log_test("Health Check (/api/health)", success, response_time, details)
        return success

    def test_ready_endpoint(self):
        """Test /api/ready endpoint"""
        success, response, response_time = self.make_request('GET', '/ready')
        
        details = ""
        if success:
            status = response.get('status', 'unknown')
            checks = response.get('checks', {})
            details = f"Status: {status}, Checks: {len(checks)} services"
            
            # Check individual service status
            if checks:
                db_status = checks.get('database', 'unknown')
                ai_status = checks.get('ai_service', 'unknown')
                market_status = checks.get('market_data', 'unknown')
                details += f" (DB: {db_status}, AI: {ai_status}, Market: {market_status})"
        else:
            details = f"Readiness check failed: {response.get('error', 'Unknown error')}"
        
        self.log_test("Readiness Check (/api/ready)", success, response_time, details)
        return success

    # ========== 2. Authentication Tests ==========
    
    def test_user_registration(self):
        """Test user registration with JWT token generation"""
        registration_data = {
            "email": self.test_user_email,
            "username": self.test_user_username,
            "password": self.test_password,
            "confirm_password": self.test_password
        }
        
        success, response, response_time = self.make_request('POST', '/auth/register', registration_data)
        
        details = ""
        if success:
            # Store authentication data
            self.access_token = response.get('access_token')
            self.user_id = response.get('user_id')
            
            # Verify JWT token structure
            if self.access_token and '.' in self.access_token:
                details = f"User registered, JWT token received (ID: {self.user_id})"
            else:
                success = False
                details = "Registration succeeded but JWT token invalid"
        else:
            details = f"Registration failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("User Registration (/api/auth/register)", success, response_time, details)
        return success

    def test_user_login(self):
        """Test user login with JWT token validation"""
        login_data = {
            "email": self.test_user_email,
            "password": self.test_password
        }
        
        success, response, response_time = self.make_request('POST', '/auth/login', login_data)
        
        details = ""
        if success:
            # Update token
            self.access_token = response.get('access_token')
            username = response.get('username')
            
            # Verify required fields
            required_fields = ['access_token', 'token_type', 'user_id', 'email', 'username']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                details = f"Login successful for {username}, JWT token updated"
            else:
                success = False
                details = f"Login succeeded but missing fields: {missing_fields}"
        else:
            details = f"Login failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("User Login (/api/auth/login)", success, response_time, details)
        return success

    def test_jwt_token_validation(self):
        """Test JWT token validation via /api/auth/me"""
        if not self.access_token:
            self.log_test("JWT Token Validation", False, 0, "No access token available")
            return False
        
        auth_headers = self.get_auth_headers()
        success, response, response_time = self.make_request('GET', '/auth/me', headers=auth_headers)
        
        details = ""
        if success:
            email = response.get('email')
            username = response.get('username')
            
            # Verify user data matches
            if email == self.test_user_email and username == self.test_user_username:
                details = f"JWT validation successful for {username}"
            else:
                success = False
                details = f"JWT validation failed: user data mismatch"
        else:
            details = f"JWT validation failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("JWT Token Validation (/api/auth/me)", success, response_time, details)
        return success

    # ========== 3. Market Data Tests ==========
    
    def test_market_data_btcusdt(self):
        """Test market data for BTCUSDT"""
        success, response, response_time = self.make_request('GET', '/market/BTCUSDT')
        
        details = ""
        if success:
            price = response.get('price', 0)
            symbol = response.get('symbol', 'unknown')
            data_source = response.get('data_source', 'unknown')
            
            # Check if price is realistic (Bitcoin should be > $10,000)
            if price > 10000:
                details = f"BTC Price: ${price:,.2f} from {data_source}"
            else:
                success = False
                details = f"Unrealistic BTC price: ${price} (expected > $10,000)"
        else:
            details = f"Market data failed: {response.get('error', 'Unknown error')}"
        
        self.log_test("Market Data BTCUSDT (/api/market/BTCUSDT)", success, response_time, details)
        return success

    def test_market_data_multiple_symbols(self):
        """Test market data for multiple symbols"""
        symbols = "BTCUSDT,ETHUSDT,ADAUSDT"
        success, response, response_time = self.make_request('GET', f'/market/prices/multiple?symbols={symbols}')
        
        details = ""
        if success:
            if isinstance(response, dict) and len(response) >= 2:
                prices = [f"{symbol}: ${data.get('price', 0):,.2f}" 
                         for symbol, data in list(response.items())[:2]]
                details = f"Multiple prices: {', '.join(prices)}"
            else:
                success = False
                details = f"Multiple prices returned invalid format: {type(response)}"
        else:
            details = f"Multiple prices failed: {response.get('error', 'Unknown error')}"
        
        self.log_test("Multiple Market Prices", success, response_time, details)
        return success

    # ========== 4. Portfolio Tests ==========
    
    def test_portfolio_access(self):
        """Test portfolio access with authentication"""
        if not self.access_token:
            self.log_test("Portfolio Access", False, 0, "No access token available")
            return False
        
        auth_headers = self.get_auth_headers()
        success, response, response_time = self.make_request('GET', '/portfolio', headers=auth_headers)
        
        details = ""
        if success:
            total_balance = response.get('total_balance', 0)
            available_balance = response.get('available_balance', 0)
            user_id = response.get('user_id')
            
            # Verify portfolio belongs to authenticated user
            if user_id == self.user_id:
                details = f"Portfolio: ${total_balance:,.2f} total, ${available_balance:,.2f} available"
            else:
                success = False
                details = f"Portfolio user mismatch: expected {self.user_id}, got {user_id}"
        else:
            details = f"Portfolio access failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Portfolio Access (/api/portfolio)", success, response_time, details)
        return success

    # ========== 5. Platform Tests ==========
    
    def test_platforms_list(self):
        """Test platforms listing"""
        if not self.access_token:
            self.log_test("Platforms List", False, 0, "No access token available")
            return False
        
        auth_headers = self.get_auth_headers()
        success, response, response_time = self.make_request('GET', '/platforms', headers=auth_headers)
        
        details = ""
        if success:
            if isinstance(response, list):
                details = f"Platforms list retrieved: {len(response)} platforms"
            else:
                success = False
                details = "Platforms returned invalid format"
        else:
            details = f"Platforms list failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Platforms List (/api/platforms)", success, response_time, details)
        return success

    def test_platform_creation(self):
        """Test platform creation"""
        if not self.access_token:
            self.log_test("Platform Creation", False, 0, "No access token available")
            return False
        
        platform_data = {
            "name": "Test Binance Platform",
            "platform_type": "binance",
            "api_key": "test_api_key_neon_trader",
            "secret_key": "test_secret_key_neon_trader",
            "is_testnet": True
        }
        
        auth_headers = self.get_auth_headers()
        success, response, response_time = self.make_request('POST', '/platforms', platform_data, auth_headers)
        
        details = ""
        if success:
            platform_id = response.get('platform', {}).get('id')
            platform_name = response.get('platform', {}).get('name')
            
            if platform_id:
                details = f"Platform created: {platform_name} (ID: {platform_id})"
            else:
                success = False
                details = "Platform creation succeeded but no ID returned"
        else:
            details = f"Platform creation failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Platform Creation (/api/platforms)", success, response_time, details)
        return success

    # ========== 6. WebSocket Test ==========
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        ws_connected = False
        ws_error = None
        
        def on_open(ws):
            nonlocal ws_connected
            ws_connected = True
            # Send a test message
            ws.send(json.dumps({"type": "ping", "data": "test"}))
        
        def on_error(ws, error):
            nonlocal ws_error
            ws_error = str(error)
        
        def on_close(ws, close_status_code, close_msg):
            pass
        
        try:
            start_time = time.time()
            ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run WebSocket in a separate thread with timeout
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection or timeout
            timeout = 5
            elapsed = 0
            while elapsed < timeout and not ws_connected and ws_error is None:
                time.sleep(0.1)
                elapsed += 0.1
            
            response_time = time.time() - start_time
            ws.close()
            
            if ws_connected:
                details = "WebSocket connection successful"
                success = True
            elif ws_error:
                details = f"WebSocket error: {ws_error}"
                success = False
            else:
                details = "WebSocket connection timeout"
                success = False
                
        except Exception as e:
            response_time = 5.0
            success = False
            details = f"WebSocket test failed: {str(e)}"
        
        self.log_test("WebSocket Connection (/ws)", success, response_time, details)
        return success

    # ========== Additional Tests ==========
    
    def test_ai_daily_plan(self):
        """Test AI daily plan generation"""
        if not self.access_token:
            self.log_test("AI Daily Plan", False, 0, "No access token available")
            return False
        
        auth_headers = self.get_auth_headers()
        success, response, response_time = self.make_request('GET', '/ai/daily-plan', headers=auth_headers, timeout=30)
        
        details = ""
        if success:
            market_analysis = response.get('market_analysis', '')
            risk_level = response.get('risk_level', 'unknown')
            opportunities = response.get('opportunities', [])
            
            if market_analysis and len(market_analysis) > 10:
                details = f"AI plan generated: {risk_level} risk, {len(opportunities)} opportunities"
            else:
                success = False
                details = "AI plan generated but content insufficient"
        else:
            details = f"AI daily plan failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("AI Daily Plan (/api/ai/daily-plan)", success, response_time, details)
        return success

    def test_asset_types(self):
        """Test asset types endpoint"""
        success, response, response_time = self.make_request('GET', '/market/types/all')
        
        details = ""
        if success:
            if isinstance(response, dict) and len(response) > 0:
                asset_count = sum(len(data.get('symbols', [])) for data in response.values())
                details = f"Asset types: {len(response)} categories, {asset_count} total symbols"
            else:
                success = False
                details = "Asset types returned invalid format"
        else:
            details = f"Asset types failed: {response.get('error', 'Unknown error')}"
        
        self.log_test("Asset Types (/api/market/types/all)", success, response_time, details)
        return success

    # ========== Main Test Runner ==========
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("\n🔍 Starting Comprehensive Backend Testing...")
        print("=" * 70)
        
        # Test sequence following user requirements
        test_sequence = [
            # 1. Health Checks
            ("Health Check", self.test_health_endpoint),
            ("Readiness Check", self.test_ready_endpoint),
            
            # 2. Authentication Flow
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("JWT Token Validation", self.test_jwt_token_validation),
            
            # 3. Market Data
            ("Market Data BTCUSDT", self.test_market_data_btcusdt),
            ("Multiple Market Prices", self.test_market_data_multiple_symbols),
            ("Asset Types", self.test_asset_types),
            
            # 4. Portfolio
            ("Portfolio Access", self.test_portfolio_access),
            
            # 5. Platforms
            ("Platforms List", self.test_platforms_list),
            ("Platform Creation", self.test_platform_creation),
            
            # 6. Additional Features
            ("AI Daily Plan", self.test_ai_daily_plan),
            
            # 7. WebSocket (if possible)
            ("WebSocket Connection", self.test_websocket_connection),
        ]
        
        print(f"📋 Running {len(test_sequence)} comprehensive tests...\n")
        
        for test_name, test_func in test_sequence:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, 0, f"Exception: {str(e)}")
        
        # Generate final report
        self.generate_final_report()

    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("📊 NEON TRADER V7 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        # Overall statistics
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        
        # Response time analysis
        response_times = [result['response_time'] for result in self.test_results.values()]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            print(f"⏱️  Average Response Time: {avg_response_time:.2f}s")
            print(f"⏱️  Maximum Response Time: {max_response_time:.2f}s")
            
            # Check if all responses are under 3 seconds (user requirement)
            slow_responses = [name for name, result in self.test_results.items() 
                            if result['response_time'] > 3.0]
            if slow_responses:
                print(f"⚠️  Slow Responses (>3s): {len(slow_responses)} tests")
            else:
                print("🚀 All responses under 3 seconds ✓")
        
        # Critical failures
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"   • {failure}")
        
        # Success summary by category
        categories = {
            'Health': ['Health Check (/api/health)', 'Readiness Check (/api/ready)'],
            'Authentication': ['User Registration (/api/auth/register)', 'User Login (/api/auth/login)', 'JWT Token Validation (/api/auth/me)'],
            'Market Data': ['Market Data BTCUSDT (/api/market/BTCUSDT)', 'Multiple Market Prices', 'Asset Types (/api/market/types/all)'],
            'Portfolio': ['Portfolio Access (/api/portfolio)'],
            'Platforms': ['Platforms List (/api/platforms)', 'Platform Creation (/api/platforms)'],
            'AI Features': ['AI Daily Plan (/api/ai/daily-plan)'],
            'WebSocket': ['WebSocket Connection (/ws)']
        }
        
        print(f"\n📈 SUCCESS BY CATEGORY:")
        for category, tests in categories.items():
            category_passed = sum(1 for test in tests if self.test_results.get(test, {}).get('success', False))
            category_total = len([test for test in tests if test in self.test_results])
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            status = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
            print(f"   {status} {category}: {category_passed}/{category_total} ({category_rate:.0f}%)")
        
        # Final verdict
        print(f"\n🏆 FINAL VERDICT:")
        if success_rate >= 90:
            print("🎉 EXCELLENT: Neon Trader V7 is working excellently!")
        elif success_rate >= 75:
            print("✅ GOOD: Neon Trader V7 is working well with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Neon Trader V7 has some significant issues")
        else:
            print("❌ CRITICAL: Neon Trader V7 has major functionality problems")
        
        # User flow verification
        auth_flow_tests = ['User Registration (/api/auth/register)', 'User Login (/api/auth/login)', 'Portfolio Access (/api/portfolio)']
        auth_flow_success = all(self.test_results.get(test, {}).get('success', False) for test in auth_flow_tests)
        
        print(f"\n🔐 USER FLOW (Register → Login → Portfolio): {'✅ WORKING' if auth_flow_success else '❌ BROKEN'}")
        
        if auth_flow_success:
            print("   ✅ Users can successfully register, login, and access their portfolio")
        else:
            failed_steps = [test for test in auth_flow_tests if not self.test_results.get(test, {}).get('success', False)]
            print(f"   ❌ Failed steps: {', '.join(failed_steps)}")
        
        return success_rate >= 75  # Return True if system is working well

def main():
    """Main test execution"""
    tester = NeonTraderComprehensiveTester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())