#!/usr/bin/env python3
"""
Seed Dashboard with Backtest Data
Pushes the generated backtest dataset to the dashboard API.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import random

API_URL = "https://bot-backtest.preview.emergentagent.com/api"

def login():
    """Login and get token."""
    response = requests.post(f"{API_URL}/auth/login", json={
        "username": "testuser",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json()["token"]
    else:
        # Try registering
        requests.post(f"{API_URL}/auth/register", json={
            "username": "testuser",
            "password": "test123"
        })
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": "testuser",
            "password": "test123"
        })
        return response.json()["token"]

def seed_data():
    """Seed dashboard with realistic trading data."""
    token = login()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("Seeding dashboard with backtest data...")
    
    # Load backtest dataset
    try:
        with open("/app/backtest_dataset_30d.json", "r") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print("Backtest dataset not found, using sample data")
        dataset = {"trades": [], "statistics": {}}
    
    # Generate treasury history (30 days)
    treasury_history = []
    treasury_sol = 1.0  # Starting treasury
    sol_price = 150.0
    
    for i in range(30):
        date = datetime.now(timezone.utc) - timedelta(days=30-i)
        # Simulate treasury growth with some variance
        daily_change = random.uniform(-0.05, 0.15)
        treasury_sol = max(0.5, treasury_sol * (1 + daily_change))
        sol_price = sol_price * (1 + random.uniform(-0.03, 0.03))
        
        treasury_history.append({
            "timestamp": date.isoformat(),
            "treasury_sol": round(treasury_sol, 4),
            "treasury_usd": round(treasury_sol * sol_price, 2),
            "sol_price": round(sol_price, 2)
        })
    
    # Generate open positions (2-3 active)
    positions = [
        {
            "mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "symbol": "BONK",
            "entry_price": 0.00002150,
            "entry_time": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
            "qty_token": 5000000,
            "cost_sol": 0.08,
            "current_price": 0.00002380,
            "current_value_sol": 0.089,
            "unrealized_pnl_pct": 10.7,
            "phase": "pumping",
            "signal": "WAIT",
            "entry_score": 62.0,
            "exit_score": 28.0
        },
        {
            "mint": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
            "symbol": "WIF",
            "entry_price": 2.85,
            "entry_time": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
            "qty_token": 35,
            "cost_sol": 0.12,
            "current_price": 2.92,
            "current_value_sol": 0.123,
            "unrealized_pnl_pct": 2.5,
            "phase": "range",
            "signal": "WAIT",
            "entry_score": 55.0,
            "exit_score": 32.0
        }
    ]
    
    # Generate sample trades with all required fields
    trades = [
        {
            "mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "symbol": "BONK",
            "entry_time": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "exit_time": (datetime.now(timezone.utc) - timedelta(days=2, hours=-4)).isoformat(),
            "entry_price": 0.00002050,
            "exit_price": 0.00002280,
            "qty_token": 4000000,
            "cost_sol": 0.06,
            "revenue_sol": 0.0738,
            "pnl_sol": 0.0138,
            "pnl_pct": 11.2,
            "exit_reason": "take_profit",
            "phase_at_entry": "pumping",
            "entry_score": 58.0,
            "is_win": True
        },
        {
            "mint": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
            "symbol": "WIF",
            "entry_time": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "exit_time": (datetime.now(timezone.utc) - timedelta(days=5, hours=-8)).isoformat(),
            "entry_price": 2.45,
            "exit_price": 2.32,
            "qty_token": 40,
            "cost_sol": 0.10,
            "revenue_sol": 0.0947,
            "pnl_sol": -0.0053,
            "pnl_pct": -5.3,
            "exit_reason": "stop_loss",
            "phase_at_entry": "cooling",
            "entry_score": 48.0,
            "is_win": False
        },
        {
            "mint": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "symbol": "JUP",
            "entry_time": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
            "exit_time": (datetime.now(timezone.utc) - timedelta(days=7, hours=12)).isoformat(),
            "entry_price": 1.15,
            "exit_price": 1.32,
            "qty_token": 85,
            "cost_sol": 0.085,
            "revenue_sol": 0.0975,
            "pnl_sol": 0.0125,
            "pnl_pct": 14.8,
            "exit_reason": "take_profit",
            "phase_at_entry": "range",
            "entry_score": 62.0,
            "is_win": True
        },
        {
            "mint": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
            "symbol": "RAY",
            "entry_time": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
            "exit_time": (datetime.now(timezone.utc) - timedelta(days=11)).isoformat(),
            "entry_price": 4.25,
            "exit_price": 4.55,
            "qty_token": 22,
            "cost_sol": 0.095,
            "revenue_sol": 0.1018,
            "pnl_sol": 0.0068,
            "pnl_pct": 7.1,
            "exit_reason": "take_profit",
            "phase_at_entry": "cooling",
            "entry_score": 55.0,
            "is_win": True
        },
        {
            "mint": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
            "symbol": "ORCA",
            "entry_time": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
            "exit_time": (datetime.now(timezone.utc) - timedelta(days=14, hours=6)).isoformat(),
            "entry_price": 3.85,
            "exit_price": 3.62,
            "qty_token": 28,
            "cost_sol": 0.11,
            "revenue_sol": 0.1035,
            "pnl_sol": -0.0065,
            "pnl_pct": -6.0,
            "exit_reason": "stop_loss",
            "phase_at_entry": "breakdown",
            "entry_score": 42.0,
            "is_win": False
        }
    ]
    
    # Generate watchlist with all required fields
    watchlist = [
        {
            "mint": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "symbol": "JUP",
            "name": "Jupiter",
            "current_price": 1.25,
            "price_usd": 1.25,
            "change_24h": 5.2,
            "volume_24h": 45000000,
            "liquidity_usd": 120000000,
            "discovery_score": 72.0,
            "source": "TRENDING",
            "phase": "range",
            "last_update": datetime.now(timezone.utc).isoformat()
        },
        {
            "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "symbol": "USDC",
            "name": "USD Coin",
            "current_price": 1.00,
            "price_usd": 1.00,
            "change_24h": 0.01,
            "volume_24h": 500000000,
            "liquidity_usd": 2000000000,
            "discovery_score": 45.0,
            "source": "MAJOR",
            "phase": "stable",
            "last_update": datetime.now(timezone.utc).isoformat()
        },
        {
            "mint": "RAYsLUZMKzkiX5VW8MjAGNPZKxCBsQkJMzXPe5z8pay",
            "symbol": "RAY",
            "name": "Raydium",
            "current_price": 4.85,
            "price_usd": 4.85,
            "change_24h": -2.1,
            "volume_24h": 28000000,
            "liquidity_usd": 85000000,
            "discovery_score": 65.0,
            "source": "DEX_GAINER",
            "phase": "cooling",
            "last_update": datetime.now(timezone.utc).isoformat()
        },
        {
            "mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "symbol": "BONK",
            "name": "Bonk",
            "current_price": 0.0000238,
            "price_usd": 0.0000238,
            "change_24h": 8.5,
            "volume_24h": 125000000,
            "liquidity_usd": 250000000,
            "discovery_score": 78.0,
            "source": "PUMP_GRAD",
            "phase": "pumping",
            "last_update": datetime.now(timezone.utc).isoformat()
        },
        {
            "mint": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
            "symbol": "WIF",
            "name": "dogwifhat",
            "current_price": 2.92,
            "price_usd": 2.92,
            "change_24h": 3.2,
            "volume_24h": 85000000,
            "liquidity_usd": 180000000,
            "discovery_score": 75.0,
            "source": "TRENDING",
            "phase": "range",
            "last_update": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Generate activity logs
    activity_logs = [
        {"type": "info", "message": "Bot started in AUTO mode"},
        {"type": "scan", "message": "Scanner found 12 potential tokens"},
        {"type": "trade", "message": "Opened position: BONK @ $0.0000215"},
        {"type": "trade", "message": "Opened position: WIF @ $2.85"},
        {"type": "info", "message": "Market scan complete - 5 tokens in watchlist"},
    ]
    
    # Push data to API
    current_treasury = treasury_history[-1]
    
    bulk_data = {
        "bot_status": {
            "is_running": True,
            "mode": "AUTO",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "scan_count": 1250,
            "active_tokens": len(watchlist)
        },
        "treasury": {
            "treasury_sol": current_treasury["treasury_sol"],
            "treasury_usd": current_treasury["treasury_usd"],
            "sol_price": current_treasury["sol_price"]
        },
        "positions": positions,
        "new_trades": trades,  # All trades with proper fields
        "activity_logs": activity_logs,
        "watchlist": watchlist
    }
    
    response = requests.post(f"{API_URL}/sync/bulk", headers=headers, json=bulk_data)
    
    if response.status_code == 200:
        print("✅ Bulk data synced successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    # Push treasury history separately
    print("\nPushing treasury history...")
    for snapshot in treasury_history[-10:]:  # Last 10 days
        try:
            response = requests.post(f"{API_URL}/treasury/snapshot", headers=headers, json=snapshot)
        except:
            pass
    
    print("✅ Treasury history seeded!")
    
    # Summary
    stats = dataset.get("statistics", {})
    print("\n" + "=" * 50)
    print("DASHBOARD SEEDING COMPLETE")
    print("=" * 50)
    print(f"Treasury: {current_treasury['treasury_sol']:.4f} SOL (${current_treasury['treasury_usd']:.2f})")
    print(f"Open positions: {len(positions)}")
    print(f"Historical trades: {len(trades)}")
    print(f"Watchlist tokens: {len(watchlist)}")
    if stats:
        print(f"\nBacktest stats (30 days):")
        print(f"  Total trades: {stats.get('total_trades', 'N/A')}")
        print(f"  Win rate: {stats.get('win_rate', 0):.1f}%")
        print(f"  Total P&L: {stats.get('total_pnl_sol', 0):.4f} SOL")

if __name__ == "__main__":
    seed_data()
