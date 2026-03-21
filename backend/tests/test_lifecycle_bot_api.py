"""
Lifecycle Bot Dashboard API Tests
Tests for authentication, dashboard, trades, treasury, activity, watchlist, bot status, positions, and bulk sync
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - use unique usernames to avoid conflicts
TEST_USERNAME = f"TEST_user_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = "testpass123"
# Auth user for protected endpoints - will be created if doesn't exist
AUTH_USERNAME = f"auth_user_{uuid.uuid4().hex[:6]}"
AUTH_PASSWORD = "authpass123"


class TestHealthCheck:
    """Health check and basic API tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        print(f"✓ API root: {data}")
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print(f"✓ Health check: {data}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_register_new_user(self):
        """Test user registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == TEST_USERNAME
        assert len(data["token"]) > 0
        print(f"✓ Registration successful for {TEST_USERNAME}")
    
    def test_register_duplicate_user(self):
        """Test duplicate registration fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✓ Duplicate registration rejected: {data['detail']}")
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == TEST_USERNAME
        print(f"✓ Login successful for {TEST_USERNAME}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "nonexistent_user",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ Invalid login rejected: {data['detail']}")
    
    def test_login_after_register(self):
        """Test login after registration works"""
        # Register a new user
        new_user = f"login_test_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": new_user,
            "password": "testpass123"
        })
        assert response.status_code == 200
        
        # Now login with same credentials
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": new_user,
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == new_user
        print(f"✓ Login after register successful for {new_user}")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for protected endpoints - creates user if needed"""
    # First try to register a new auth user
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": AUTH_USERNAME,
        "password": AUTH_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json()["token"]
    
    # If user exists, try to login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": AUTH_USERNAME,
        "password": AUTH_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json()["token"]
    
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication"""
    
    def test_dashboard_requires_auth(self):
        """Test dashboard endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard")
        assert response.status_code == 401
        print("✓ Dashboard requires authentication")
    
    def test_trades_requires_auth(self):
        """Test trades endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/trades")
        assert response.status_code == 401
        print("✓ Trades requires authentication")
    
    def test_positions_requires_auth(self):
        """Test positions endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/positions")
        assert response.status_code == 401
        print("✓ Positions requires authentication")
    
    def test_activity_requires_auth(self):
        """Test activity endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/activity")
        assert response.status_code == 401
        print("✓ Activity requires authentication")
    
    def test_watchlist_requires_auth(self):
        """Test watchlist endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/watchlist")
        assert response.status_code == 401
        print("✓ Watchlist requires authentication")
    
    def test_bot_status_requires_auth(self):
        """Test bot status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/bot/status")
        assert response.status_code == 401
        print("✓ Bot status requires authentication")
    
    def test_treasury_history_requires_auth(self):
        """Test treasury history endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/treasury/history")
        assert response.status_code == 401
        print("✓ Treasury history requires authentication")


class TestDashboard:
    """Dashboard stats endpoint tests"""
    
    def test_get_dashboard_stats(self, auth_headers):
        """Test getting dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        expected_fields = [
            "treasury_sol", "treasury_usd", "total_pnl_sol", "total_pnl_pct",
            "total_trades", "win_count", "loss_count", "win_rate",
            "avg_win_pct", "avg_loss_pct", "open_positions", "bot_running", "bot_mode"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert isinstance(data["treasury_sol"], (int, float))
        assert isinstance(data["total_trades"], int)
        assert isinstance(data["bot_running"], bool)
        assert isinstance(data["bot_mode"], str)
        
        print(f"✓ Dashboard stats: treasury={data['treasury_sol']} SOL, trades={data['total_trades']}, win_rate={data['win_rate']}%")


class TestTrades:
    """Trade history endpoint tests"""
    
    def test_get_trades(self, auth_headers):
        """Test getting trade history"""
        response = requests.get(f"{BASE_URL}/api/trades?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} trades")
        
        if len(data) > 0:
            trade = data[0]
            expected_fields = ["id", "mint", "symbol", "entry_price", "exit_price", 
                            "pnl_sol", "pnl_pct", "is_win"]
            for field in expected_fields:
                assert field in trade, f"Missing field: {field}"
            print(f"  First trade: {trade['symbol']} - {'WIN' if trade['is_win'] else 'LOSS'} ({trade['pnl_pct']:.2f}%)")
    
    def test_get_trade_stats(self, auth_headers):
        """Test getting trade statistics"""
        response = requests.get(f"{BASE_URL}/api/trades/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = ["total_trades", "win_count", "loss_count", "win_rate", "total_pnl_sol"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Trade stats: {data['total_trades']} trades, {data['win_rate']:.1f}% win rate")
    
    def test_create_trade(self, auth_headers):
        """Test creating a new trade"""
        now = datetime.now(timezone.utc)
        trade_data = {
            "mint": f"TEST_{uuid.uuid4().hex[:16]}",
            "symbol": "TEST_TOKEN",
            "entry_price": 0.00001234,
            "exit_price": 0.00001500,
            "entry_time": (now - timedelta(hours=1)).isoformat(),
            "exit_time": now.isoformat(),
            "qty_token": 1000000,
            "cost_sol": 0.1,
            "revenue_sol": 0.12,
            "pnl_sol": 0.02,
            "pnl_pct": 20.0,
            "is_win": True,
            "phase_at_entry": "LAUNCH",
            "phase_at_exit": "PUMP",
            "hold_duration_mins": 60.0
        }
        
        response = requests.post(f"{BASE_URL}/api/trades", json=trade_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "TEST_TOKEN"
        assert data["is_win"] == True
        assert "id" in data
        print(f"✓ Created trade: {data['symbol']} with id {data['id']}")


class TestTreasuryHistory:
    """Treasury history endpoint tests"""
    
    def test_get_treasury_history(self, auth_headers):
        """Test getting treasury history"""
        response = requests.get(f"{BASE_URL}/api/treasury/history?days=30", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} treasury snapshots")
        
        if len(data) > 0:
            snapshot = data[0]
            expected_fields = ["id", "timestamp", "treasury_sol", "treasury_usd", "sol_price"]
            for field in expected_fields:
                assert field in snapshot, f"Missing field: {field}"
            print(f"  First snapshot: {snapshot['treasury_sol']} SOL (${snapshot['treasury_usd']})")
    
    def test_add_treasury_snapshot(self, auth_headers):
        """Test adding a treasury snapshot"""
        snapshot_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "treasury_sol": 10.5,
            "treasury_usd": 2100.0,
            "sol_price": 200.0
        }
        
        response = requests.post(f"{BASE_URL}/api/treasury/snapshot", json=snapshot_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        print(f"✓ Added treasury snapshot: {snapshot_data['treasury_sol']} SOL")


class TestActivity:
    """Activity log endpoint tests"""
    
    def test_get_activity(self, auth_headers):
        """Test getting activity logs"""
        response = requests.get(f"{BASE_URL}/api/activity?limit=30", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} activity logs")
        
        if len(data) > 0:
            log = data[0]
            expected_fields = ["id", "timestamp", "type", "message"]
            for field in expected_fields:
                assert field in log, f"Missing field: {field}"
            print(f"  Latest activity: [{log['type']}] {log['message'][:50]}...")
    
    def test_log_activity(self, auth_headers):
        """Test logging an activity"""
        activity_data = {
            "type": "INFO",
            "message": "TEST: Activity log test entry",
            "mint": None,
            "symbol": None
        }
        
        response = requests.post(f"{BASE_URL}/api/activity", json=activity_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "logged"
        print(f"✓ Logged activity: {activity_data['message']}")


class TestWatchlist:
    """Watchlist endpoint tests"""
    
    def test_get_watchlist(self, auth_headers):
        """Test getting watchlist"""
        response = requests.get(f"{BASE_URL}/api/watchlist", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} watchlist tokens")
        
        if len(data) > 0:
            token = data[0]
            expected_fields = ["mint", "symbol", "current_price", "signal"]
            for field in expected_fields:
                assert field in token, f"Missing field: {field}"
            print(f"  First token: {token['symbol']} - ${token['current_price']}")
    
    def test_sync_watchlist(self, auth_headers):
        """Test syncing watchlist"""
        watchlist_data = [
            {
                "mint": f"TEST_{uuid.uuid4().hex[:16]}",
                "symbol": "TEST_WL",
                "current_price": 0.00001,
                "price_change_1h": 5.5,
                "volume_24h": 100000,
                "liquidity_usd": 50000,
                "holder_count": 1000,
                "phase": "LAUNCH",
                "signal": "BUY",
                "entry_score": 75.0,
                "exit_score": 25.0,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        response = requests.post(f"{BASE_URL}/api/watchlist/sync", json=watchlist_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "synced"
        assert data["count"] == 1
        print(f"✓ Synced watchlist with {data['count']} tokens")


class TestBotStatus:
    """Bot status endpoint tests"""
    
    def test_get_bot_status(self, auth_headers):
        """Test getting bot status"""
        response = requests.get(f"{BASE_URL}/api/bot/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = ["bot_id", "is_running", "mode"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Bot status: running={data['is_running']}, mode={data['mode']}")
    
    def test_update_bot_status(self, auth_headers):
        """Test updating bot status"""
        status_data = {
            "is_running": True,
            "mode": "AUTO",
            "wallet_address": "TEST_WALLET_ADDRESS",
            "scan_count": 100,
            "active_tokens": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/bot/status", json=status_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        print(f"✓ Updated bot status to mode={status_data['mode']}")
        
        # Verify update persisted
        response = requests.get(f"{BASE_URL}/api/bot/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "AUTO"
        print(f"✓ Verified bot status update persisted")


class TestPositions:
    """Positions endpoint tests"""
    
    def test_get_positions(self, auth_headers):
        """Test getting positions"""
        response = requests.get(f"{BASE_URL}/api/positions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} positions")
        
        if len(data) > 0:
            pos = data[0]
            expected_fields = ["id", "mint", "symbol", "entry_price", "cost_sol"]
            for field in expected_fields:
                assert field in pos, f"Missing field: {field}"
            print(f"  First position: {pos['symbol']} - {pos['cost_sol']} SOL")
    
    def test_sync_positions(self, auth_headers):
        """Test syncing positions"""
        positions_data = [
            {
                "mint": f"TEST_{uuid.uuid4().hex[:16]}",
                "symbol": "TEST_POS",
                "entry_price": 0.00001,
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "qty_token": 1000000,
                "cost_sol": 0.1,
                "current_price": 0.000012,
                "current_value_sol": 0.12,
                "unrealized_pnl_pct": 20.0,
                "phase": "PUMP",
                "signal": "HOLD",
                "entry_score": 80.0,
                "exit_score": 30.0
            }
        ]
        
        response = requests.post(f"{BASE_URL}/api/positions/sync", json=positions_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "synced"
        assert data["count"] == 1
        print(f"✓ Synced {data['count']} positions")


class TestBulkSync:
    """Bulk data push endpoint tests (for Android app)"""
    
    def test_bulk_data_push(self, auth_headers):
        """Test bulk data push endpoint"""
        now = datetime.now(timezone.utc)
        bulk_data = {
            "bot_status": {
                "is_running": True,
                "mode": "RANGE_TRADE",
                "wallet_address": "BULK_TEST_WALLET",
                "scan_count": 50,
                "active_tokens": 3
            },
            "treasury": {
                "id": str(uuid.uuid4()),
                "timestamp": now.isoformat(),
                "treasury_sol": 15.0,
                "treasury_usd": 3000.0,
                "sol_price": 200.0
            },
            "activity_logs": [
                {
                    "type": "INFO",
                    "message": "TEST: Bulk sync test"
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sync/bulk", json=bulk_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "results" in data
        assert data["results"]["bot_status"] == "updated"
        assert data["results"]["treasury"] == "recorded"
        print(f"✓ Bulk sync successful: {data['results']}")


class TestAuthMe:
    """Test /auth/me endpoint"""
    
    def test_get_current_user(self, auth_headers):
        """Test getting current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        # Username should match the auth user we created
        assert data["username"] == AUTH_USERNAME
        print(f"✓ Current user: {data['username']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
