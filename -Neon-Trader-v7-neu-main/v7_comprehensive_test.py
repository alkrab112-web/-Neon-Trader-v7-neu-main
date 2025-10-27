import requests
import sys
import json
import uuid
import time
from datetime import datetime

class NeonTraderV7ComprehensiveTester:
    def __init__(self, base_url="https://neon-trader-2.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.test_user_email = f"v7comprehensive_{uuid.uuid4().hex[:8]}@neontrader.com"
        self.test_user_username = f"v7user_{uuid.uuid4().hex[:8]}"
        self.test_password = "V7TestPass2024!"
        self.created_snapshot_id = None
        self.created_trade_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=30):
        """Run a single API test with performance monitoring"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=timeout)

            response_time = (time.time() - start_time) * 1000
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code} - Response Time: {response_time:.2f}ms")
                
                # Check for performance headers
                if 'X-Process-Time' in response.headers:
                    print(f"   📊 Performance Header: X-Process-Time = {response.headers['X-Process-Time']}")
                
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)[:400]}...")
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

    # ========== Setup Authentication ==========
    
    def setup_authentication(self):
        """Setup user and get authentication tokens"""
        print("\n🔐 Setting up authentication for V7 comprehensive testing...")
        
        registration_data = {
            "email": self.test_user_email,
            "username": self.test_user_username,
            "password": self.test_password,
            "confirm_password": self.test_password
        }
        
        success, response = self.run_test("User Registration", "POST", "/auth/register", 200, registration_data)
        
        if success and response:
            self.access_token = response.get('access_token')
            self.refresh_token = response.get('refresh_token')
            self.user_id = response.get('user_id')
            print(f"   ✅ Authentication setup complete - User ID: {self.user_id}")
            return True
        else:
            print("   ❌ Failed to setup authentication")
            return False

    # ========== 1. Performance Monitoring & Logging Tests ==========
    
    def test_health_endpoint(self):
        """Test GET /api/health - فحص صحة الخدمة"""
        success, response = self.run_test("Health Check Endpoint", "GET", "/health", 200)
        
        if success and response:
            required_fields = ['status', 'timestamp', 'service']
            for field in required_fields:
                if field not in response:
                    print(f"   ❌ Missing health field: {field}")
                    return False, response
            
            if response.get('status') != 'ok':
                print(f"   ❌ Health status not ok: {response.get('status')}")
                return False, response
                
            print(f"   ✅ Health check passed - Service: {response.get('service')}")
            
        return success, response

    def test_readiness_endpoint(self):
        """Test GET /api/ready - فحص الجاهزية مع تفاصيل الاتصالات"""
        success, response = self.run_test("Readiness Check with Connection Details", "GET", "/ready", 200)
        
        if success and response:
            required_fields = ['status', 'timestamp', 'checks']
            for field in required_fields:
                if field not in response:
                    print(f"   ❌ Missing readiness field: {field}")
                    return False, response
            
            checks = response.get('checks', {})
            expected_checks = ['database', 'ai_service', 'market_data', 'exchanges']
            
            for check in expected_checks:
                if check not in checks:
                    print(f"   ❌ Missing service check: {check}")
                else:
                    print(f"   ✅ Service check {check}: {checks[check]}")
            
            print(f"   ✅ Readiness check passed - Overall status: {response.get('status')}")
            
        return success, response

    # ========== 2. JWT Refresh Token System Tests ==========
    
    def test_login_returns_refresh_token(self):
        """Test that login يُرجع refresh_token في الاستجابة"""
        login_data = {
            "email": self.test_user_email,
            "password": self.test_password
        }
        
        success, response = self.run_test("Login Returns Refresh Token", "POST", "/auth/login", 200, login_data)
        
        if success and response:
            if 'refresh_token' not in response:
                print("   ❌ Login response missing refresh_token")
                return False, response
            
            required_fields = ['access_token', 'token_type', 'expires_in', 'refresh_token']
            for field in required_fields:
                if field not in response:
                    print(f"   ❌ Missing login field: {field}")
                    return False, response
            
            self.access_token = response.get('access_token')
            self.refresh_token = response.get('refresh_token')
            
            print(f"   ✅ Login successful with refresh token")
            print(f"   Access Token: {self.access_token[:20]}...")
            print(f"   Refresh Token: {self.refresh_token[:20]}...")
            
        return success, response

    def test_refresh_token_endpoint(self):
        """Test POST /api/auth/refresh - تجديد الرموز"""
        if not self.refresh_token:
            print("   ❌ No refresh token available")
            return False, {}
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        url = f"{self.base_url}/auth/refresh"
        
        self.tests_run += 1
        print(f"\n🔍 Testing JWT Refresh Token...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, data={'refresh_token': self.refresh_token}, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                response_data = response.json()
                required_fields = ['access_token', 'token_type', 'refresh_token']
                for field in required_fields:
                    if field not in response_data:
                        print(f"   ❌ Missing refresh field: {field}")
                        return False, response_data
                
                old_access_token = self.access_token
                self.access_token = response_data.get('access_token')
                self.refresh_token = response_data.get('refresh_token')
                
                if self.access_token == old_access_token:
                    print("   ❌ New access token same as old token")
                    return False, response_data
                
                print(f"   ✅ Token refresh successful - New tokens issued")
                return True, response_data
                    
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    # ========== 3. Rate Limiting Tests ==========
    
    def test_rate_limiting_login(self):
        """Test محاولة تسجيل دخول متكرر للتأكد من Rate limiting"""
        print("\n🚦 Testing Rate Limiting on Login...")
        
        login_data = {
            "email": "nonexistent@test.com",
            "password": "wrong_password"
        }
        
        rate_limited = False
        attempts = 0
        max_attempts = 15
        
        for i in range(max_attempts):
            attempts += 1
            url = f"{self.base_url}/auth/login"
            try:
                resp = requests.post(url, json=login_data, headers={'Content-Type': 'application/json'}, timeout=10)
                if resp.status_code == 429:
                    rate_limited = True
                    print(f"   ✅ Rate limiting triggered after {attempts} attempts")
                    try:
                        error_data = resp.json()
                        if 'rate limit' in str(error_data).lower() or 'too many' in str(error_data).lower():
                            print(f"   ✅ Rate limit message: {error_data}")
                        else:
                            print(f"   ⚠️  Rate limited but unclear message: {error_data}")
                    except:
                        print(f"   ⚠️  Rate limited but no JSON response")
                    break
                elif resp.status_code == 401:
                    print(f"   Login attempt {i+1}: 401 (expected)")
                else:
                    print(f"   Login attempt {i+1}: {resp.status_code}")
                    
            except Exception as e:
                print(f"   Login attempt {i+1} error: {e}")
            
            time.sleep(0.1)
        
        if rate_limited:
            self.tests_passed += 1
            return True, {"rate_limited": True, "attempts": attempts}
        else:
            print(f"   ❌ Rate limiting not triggered after {max_attempts} attempts")
            return False, {"rate_limited": False, "attempts": attempts}

    def test_rate_limiting_trades(self):
        """Test محاولة إنشاء trades متكررة"""
        if not self.access_token:
            print("   ❌ No access token for trade rate limiting test")
            return False, {}
        
        print("\n🚦 Testing Rate Limiting on Trade Creation...")
        
        trade_data = {
            "symbol": "BTCUSDT",
            "trade_type": "buy",
            "order_type": "market",
            "quantity": 0.001
        }
        
        auth_headers = self.get_auth_headers()
        rate_limited = False
        attempts = 0
        max_attempts = 20
        
        for i in range(max_attempts):
            attempts += 1
            url = f"{self.base_url}/trades"
            try:
                resp = requests.post(url, json=trade_data, headers={**auth_headers, 'Content-Type': 'application/json'}, timeout=10)
                
                if resp.status_code == 429:
                    rate_limited = True
                    print(f"   ✅ Trade rate limiting triggered after {attempts} attempts")
                    try:
                        error_data = resp.json()
                        if 'rate limit' in str(error_data).lower() or 'too many' in str(error_data).lower():
                            print(f"   ✅ Rate limit message: {error_data}")
                        else:
                            print(f"   ⚠️  Rate limited but unclear message: {error_data}")
                    except:
                        print(f"   ⚠️  Rate limited but no JSON response")
                    break
                elif resp.status_code == 200:
                    print(f"   Trade {i+1}: Success")
                else:
                    print(f"   Trade {i+1}: Status {resp.status_code}")
                    
            except Exception as e:
                print(f"   Trade {i+1} error: {e}")
            
            time.sleep(0.05)
        
        if rate_limited:
            self.tests_passed += 1
            return True, {"rate_limited": True, "attempts": attempts}
        else:
            print(f"   ❌ Trade rate limiting not triggered after {max_attempts} attempts")
            return False, {"rate_limited": False, "attempts": attempts}

    # ========== 4. Portfolio Snapshots Tests ==========
    
    def test_create_portfolio_snapshot(self):
        """Test POST /api/snapshots - إنشاء لقطة للمحفظة"""
        if not self.access_token:
            print("   ❌ No access token for snapshot creation")
            return False, {}
        
        snapshot_data = {
            "total_balance": 25000.75,
            "available_balance": 18000.50,
            "invested_balance": 7000.25,
            "daily_pnl": 250.75,
            "total_pnl": 5000.75,
            "assets": {
                "BTCUSDT": {"quantity": 0.15, "value": 6800.0},
                "ETHUSDT": {"quantity": 2.5, "value": 6500.0}
            },
            "positions": [
                {"symbol": "BTCUSDT", "side": "long", "size": 0.15, "entry_price": 45000},
                {"symbol": "ETHUSDT", "side": "long", "size": 2.5, "entry_price": 2600}
            ],
            "metadata": {
                "platform": "binance_testnet",
                "strategy": "swing_trading",
                "created_by": "v7_test"
            }
        }
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Create Portfolio Snapshot", "POST", "/snapshots", 200, snapshot_data, auth_headers)
        
        if success and response:
            if 'snapshot_id' not in response:
                print("   ❌ Missing snapshot_id in response")
                return False, response
            
            self.created_snapshot_id = response.get('snapshot_id')
            print(f"   ✅ Snapshot created: {self.created_snapshot_id}")
            
        return success, response

    def test_get_portfolio_snapshots(self):
        """Test GET /api/snapshots - جلب التاريخ"""
        if not self.access_token:
            print("   ❌ No access token for snapshots retrieval")
            return False, {}
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Get Portfolio Snapshots History", "GET", "/snapshots?limit=10&days=30", 200, headers=auth_headers)
        
        if success and response:
            if not isinstance(response, list):
                print("   ❌ Response should be a list")
                return False, response
            
            print(f"   ✅ Retrieved {len(response)} snapshots")
            
            if len(response) > 0:
                snapshot = response[0]
                required_fields = ['id', 'user_id', 'total_balance', 'timestamp']
                for field in required_fields:
                    if field not in snapshot:
                        print(f"   ❌ Missing snapshot field: {field}")
                        return False, response
                
                print(f"   ✅ Snapshot structure validated")
            
        return success, response

    def test_get_snapshot_analysis(self):
        """Test GET /api/snapshots/analysis/30d - تحليل الأداء"""
        if not self.access_token:
            print("   ❌ No access token for snapshot analysis")
            return False, {}
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Get 30-Day Performance Analysis", "GET", "/snapshots/analysis/30d", 200, headers=auth_headers)
        
        if success and response:
            if 'message' in response and 'insufficient data' in response['message'].lower():
                print("   ✅ Appropriate message for insufficient data")
                return True, response
            
            expected_fields = ['period', 'balance_change', 'balance_change_percent', 'total_trades', 'win_rate']
            for field in expected_fields:
                if field not in response:
                    print(f"   ❌ Missing analysis field: {field}")
                    return False, response
            
            print(f"   ✅ Analysis validated - Period: {response.get('period')}")
            
        return success, response

    # ========== 5. Human-in-the-loop Trading Tests ==========
    
    def test_simulate_trade(self):
        """Test POST /api/trades/simulate - محاكاة التداول"""
        if not self.access_token:
            print("   ❌ No access token for trade simulation")
            return False, {}
        
        trade_simulation_data = {
            "symbol": "BTCUSDT",
            "trade_type": "buy",
            "order_type": "limit",
            "quantity": 0.08,
            "entry_price": 45000,
            "stop_loss": 42000,
            "take_profit": 48000,
            "platform_id": "test_platform_v7"
        }
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Simulate Trade for Approval", "POST", "/trades/simulate", 200, trade_simulation_data, auth_headers)
        
        if success and response:
            required_fields = ['trade_id', 'status', 'estimated_cost', 'risk_assessment']
            for field in required_fields:
                if field not in response:
                    print(f"   ❌ Missing simulation field: {field}")
                    return False, response
            
            if response.get('status') != 'pending_approval':
                print(f"   ❌ Expected 'pending_approval', got {response.get('status')}")
                return False, response
            
            self.created_trade_id = response.get('trade_id')
            print(f"   ✅ Trade simulation successful: {self.created_trade_id}")
            print(f"   Estimated Cost: ${response.get('estimated_cost')}")
            print(f"   Risk Level: {response.get('risk_assessment', {}).get('risk_level')}")
            
        return success, response

    def test_get_pending_approvals(self):
        """Test GET /api/trades/pending-approval - جلب الموافقات المعلقة"""
        if not self.access_token:
            print("   ❌ No access token for pending approvals")
            return False, {}
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Get Pending Trade Approvals", "GET", "/trades/pending-approval", 200, headers=auth_headers)
        
        if success and response:
            if not isinstance(response, list):
                print("   ❌ Response should be a list")
                return False, response
            
            print(f"   ✅ Retrieved {len(response)} pending approvals")
            
            if len(response) > 0:
                trade = response[0]
                required_fields = ['id', 'user_id', 'symbol', 'status', 'estimated_cost']
                for field in required_fields:
                    if field not in trade:
                        print(f"   ❌ Missing pending trade field: {field}")
                        return False, response
                
                print(f"   ✅ Pending trade structure validated")
            
        return success, response

    def test_approve_trade(self):
        """Test POST /api/trades/{id}/approve - الموافقة/الرفض"""
        if not self.access_token or not self.created_trade_id:
            print("   ❌ No access token or trade ID for approval")
            return False, {}
        
        approval_data = {
            "action": "approve",
            "notes": "Approved for V7 comprehensive testing"
        }
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test(f"Approve Trade {self.created_trade_id}", "POST", f"/trades/{self.created_trade_id}/approve", 200, approval_data, auth_headers)
        
        if success and response:
            if 'status' not in response:
                print("   ❌ Missing status in approval response")
                return False, response
            
            print(f"   ✅ Trade approval successful - Status: {response.get('status')}")
            
        return success, response

    def test_get_approval_summary(self):
        """Test GET /api/trades/approval-summary - ملخص الموافقات"""
        if not self.access_token:
            print("   ❌ No access token for approval summary")
            return False, {}
        
        auth_headers = self.get_auth_headers()
        success, response = self.run_test("Get Approval Summary", "GET", "/trades/approval-summary", 200, headers=auth_headers)
        
        if success and response:
            expected_fields = ['total_proposed', 'total_approved', 'total_rejected', 'approval_rate']
            for field in expected_fields:
                if field not in response:
                    print(f"   ❌ Missing approval summary field: {field}")
                    return False, response
            
            print(f"   ✅ Approval summary validated")
            print(f"   Total Proposed: {response.get('total_proposed')}")
            print(f"   Approval Rate: {response.get('approval_rate')}%")
            
        return success, response

    # ========== 6. Enhanced Market Data Tests ==========
    
    def test_enhanced_market_data_performance(self):
        """Test استخدام الخدمة الجديدة مع retry وcache"""
        print("\n📊 Testing Enhanced Market Data with Retry & Cache...")
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        total_time = 0
        successful_requests = 0
        
        for symbol in symbols:
            start_time = time.time()
            success, response = self.run_test(f"Enhanced Market Data - {symbol}", "GET", f"/market/{symbol}", 200)
            request_time = (time.time() - start_time) * 1000
            
            if success and response:
                successful_requests += 1
                total_time += request_time
                
                # Check for enhanced data fields
                enhanced_fields = ['data_source', 'fetch_time_ms', 'asset_type', 'last_updated']
                for field in enhanced_fields:
                    if field in response:
                        print(f"   ✅ Enhanced field {field}: {response[field]}")
                    else:
                        print(f"   ⚠️  Missing enhanced field: {field}")
                
                # Check for realistic pricing
                price = response.get('price', 0)
                if symbol == 'BTCUSDT' and price > 30000:
                    print(f"   ✅ Realistic BTC price: ${price}")
                elif symbol == 'ETHUSDT' and price > 1000:
                    print(f"   ✅ Realistic ETH price: ${price}")
                elif price == 100:
                    print(f"   ⚠️  Mock price detected: ${price}")
                else:
                    print(f"   ℹ️  Price: ${price}")
        
        if successful_requests > 0:
            avg_time = total_time / successful_requests
            print(f"\n   📈 Performance Summary:")
            print(f"   Average Response Time: {avg_time:.2f}ms")
            print(f"   Successful Requests: {successful_requests}/{len(symbols)}")
            
            if avg_time < 2000:
                print(f"   ✅ Performance benchmark met (< 2000ms)")
                self.tests_passed += 1
                return True, {"avg_time": avg_time, "successful": successful_requests}
            else:
                print(f"   ⚠️  Performance benchmark not met (>= 2000ms)")
                return False, {"avg_time": avg_time, "successful": successful_requests}
        else:
            print(f"   ❌ No successful market data requests")
            return False, {"successful": 0}

def main():
    print("🚀 Neon Trader V7 Comprehensive Improvements Testing")
    print("=" * 80)
    print("اختبار شامل للتحسينات الجديدة في Neon Trader V7:")
    print("1. Performance Monitoring & Logging - مراقبة الأداء والتسجيل")
    print("2. JWT Refresh Token System - نظام تجديد رموز JWT")
    print("3. Rate Limiting - تحديد معدل الطلبات")
    print("4. Portfolio Snapshots - لقطات المحفظة")
    print("5. Human-in-the-loop Trading - التداول مع التدخل البشري")
    print("6. Enhanced Market Data - بيانات السوق المحسنة")
    print("=" * 80)
    
    tester = NeonTraderV7ComprehensiveTester()
    
    # Setup authentication
    if not tester.setup_authentication():
        print("❌ Failed to setup authentication. Aborting tests.")
        return 1
    
    # Test sequence for V7 improvements
    tests = [
        # 1. Performance Monitoring & Logging
        ("Health Check Endpoint", tester.test_health_endpoint),
        ("Readiness Check with Connection Details", tester.test_readiness_endpoint),
        
        # 2. JWT Refresh Token System
        ("Login Returns Refresh Token", tester.test_login_returns_refresh_token),
        ("JWT Refresh Token Endpoint", tester.test_refresh_token_endpoint),
        
        # 3. Rate Limiting
        ("Rate Limiting - Login Attempts", tester.test_rate_limiting_login),
        ("Rate Limiting - Trade Creation", tester.test_rate_limiting_trades),
        
        # 4. Portfolio Snapshots
        ("Create Portfolio Snapshot", tester.test_create_portfolio_snapshot),
        ("Get Portfolio Snapshots History", tester.test_get_portfolio_snapshots),
        ("Get 30-Day Performance Analysis", tester.test_get_snapshot_analysis),
        
        # 5. Human-in-the-loop Trading
        ("Simulate Trade for Approval", tester.test_simulate_trade),
        ("Get Pending Trade Approvals", tester.test_get_pending_approvals),
        ("Approve Trade", tester.test_approve_trade),
        ("Get Approval Summary", tester.test_get_approval_summary),
        
        # 6. Enhanced Market Data
        ("Enhanced Market Data Performance", tester.test_enhanced_market_data_performance),
    ]
    
    print(f"\n📋 Running {len(tests)} comprehensive V7 improvement tests...")
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    # Print final results
    print("\n" + "=" * 80)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    print(f"📈 Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All V7 improvement tests passed!")
        print("✅ جميع التحسينات تعمل بشكل صحيح ولا تؤثر على الوظائف الموجودة")
        return 0
    else:
        failed = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed} tests failed")
        print("❌ بعض التحسينات تحتاج إلى مراجعة")
        return 1

if __name__ == "__main__":
    sys.exit(main())