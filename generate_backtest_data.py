#!/usr/bin/env python3
"""
Backtest Dataset Generator for Lifecycle Bot
Generates realistic 30-day trading data for backtesting.
Uses CoinGecko free API for historical Solana token data.
"""

import requests
import json
import random
from datetime import datetime, timedelta, timezone
import time

# Configuration
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
DAYS = 30

# Top performing Solana meme tokens to track
TOKENS = [
    {"id": "bonk", "symbol": "BONK", "name": "Bonk"},
    {"id": "dogwifcoin", "symbol": "WIF", "name": "dogwifhat"},
    {"id": "popcat", "symbol": "POPCAT", "name": "Popcat"},
    {"id": "book-of-meme", "symbol": "BOME", "name": "BOOK OF MEME"},
    {"id": "jito-governance-token", "symbol": "JTO", "name": "Jito"},
    {"id": "jupiter-exchange-solana", "symbol": "JUP", "name": "Jupiter"},
    {"id": "raydium", "symbol": "RAY", "name": "Raydium"},
    {"id": "marinade", "symbol": "MNDE", "name": "Marinade"},
    {"id": "orca", "symbol": "ORCA", "name": "Orca"},
    {"id": "pyth-network", "symbol": "PYTH", "name": "Pyth Network"},
]

def fetch_historical_prices(token_id, days=30):
    """Fetch historical price data from CoinGecko."""
    url = f"{COINGECKO_BASE}/coins/{token_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "hourly"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("prices", [])
        elif response.status_code == 429:
            print(f"  Rate limited, waiting 60s...")
            time.sleep(60)
            return fetch_historical_prices(token_id, days)
        else:
            print(f"  Error fetching {token_id}: {response.status_code}")
            return []
    except Exception as e:
        print(f"  Exception fetching {token_id}: {e}")
        return []

def generate_candle_data(prices):
    """Convert price data to OHLCV candles."""
    candles = []
    
    for i in range(0, len(prices) - 4, 4):  # 4-hour candles
        batch = prices[i:i+4]
        if not batch:
            continue
            
        ts = batch[0][0]
        price_values = [p[1] for p in batch]
        
        candle = {
            "timestamp": ts,
            "open": price_values[0],
            "high": max(price_values),
            "low": min(price_values),
            "close": price_values[-1],
            "volume": random.uniform(100000, 5000000),  # Simulated volume
            "buy_ratio": random.uniform(0.4, 0.7),  # Simulated buy pressure
        }
        candles.append(candle)
    
    return candles

def simulate_trades(token, candles):
    """Simulate trades based on simple strategy rules."""
    trades = []
    position = None
    
    for i, candle in enumerate(candles[5:], start=5):  # Need 5 candles for indicators
        price = candle["close"]
        buy_ratio = candle["buy_ratio"]
        
        # Simple entry: price dipped and buy ratio is high
        prev_candles = candles[i-5:i]
        avg_price = sum(c["close"] for c in prev_candles) / 5
        
        if position is None:
            # Entry conditions
            if price < avg_price * 0.95 and buy_ratio > 0.55:
                position = {
                    "entry_time": candle["timestamp"],
                    "entry_price": price,
                    "qty": random.uniform(1000, 100000),
                    "entry_score": random.uniform(45, 75),
                }
        else:
            # Exit conditions
            gain_pct = ((price - position["entry_price"]) / position["entry_price"]) * 100
            held_hours = (candle["timestamp"] - position["entry_time"]) / 3600000
            
            should_exit = (
                gain_pct >= 20 or  # Take profit
                gain_pct <= -8 or  # Stop loss
                held_hours >= 24   # Max hold
            )
            
            if should_exit:
                exit_price = price
                pnl_pct = gain_pct
                pnl_sol = (exit_price - position["entry_price"]) * position["qty"] / 150  # Assume $150/SOL
                
                trade = {
                    "mint": f"fake_{token['id']}_mint",
                    "symbol": token["symbol"],
                    "entry_time": datetime.fromtimestamp(position["entry_time"]/1000, tz=timezone.utc).isoformat(),
                    "exit_time": datetime.fromtimestamp(candle["timestamp"]/1000, tz=timezone.utc).isoformat(),
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "qty_token": position["qty"],
                    "cost_sol": position["qty"] * position["entry_price"] / 150,
                    "pnl_sol": pnl_sol,
                    "pnl_pct": pnl_pct,
                    "exit_reason": "take_profit" if pnl_pct > 0 else "stop_loss",
                    "phase_at_entry": random.choice(["pumping", "range", "cooling"]),
                    "entry_score": position["entry_score"],
                }
                trades.append(trade)
                position = None
    
    return trades

def generate_dataset():
    """Generate complete 30-day backtest dataset."""
    print("=" * 60)
    print("Generating 30-Day Backtest Dataset")
    print("=" * 60)
    
    all_candles = {}
    all_trades = []
    
    for token in TOKENS[:5]:  # Limit to 5 to avoid rate limits
        print(f"\nFetching {token['symbol']}...")
        prices = fetch_historical_prices(token["id"], DAYS)
        
        if prices:
            candles = generate_candle_data(prices)
            all_candles[token["symbol"]] = candles
            print(f"  Generated {len(candles)} candles")
            
            trades = simulate_trades(token, candles)
            all_trades.extend(trades)
            print(f"  Simulated {len(trades)} trades")
        
        time.sleep(1.5)  # Rate limit protection
    
    # Calculate statistics
    wins = [t for t in all_trades if t["pnl_pct"] > 0]
    losses = [t for t in all_trades if t["pnl_pct"] <= 0]
    
    stats = {
        "period_days": DAYS,
        "total_trades": len(all_trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(all_trades) * 100 if all_trades else 0,
        "total_pnl_sol": sum(t["pnl_sol"] for t in all_trades),
        "avg_gain_pct": sum(t["pnl_pct"] for t in wins) / len(wins) if wins else 0,
        "avg_loss_pct": sum(t["pnl_pct"] for t in losses) / len(losses) if losses else 0,
        "best_trade": max((t["pnl_pct"] for t in all_trades), default=0),
        "worst_trade": min((t["pnl_pct"] for t in all_trades), default=0),
    }
    
    dataset = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_days": DAYS,
        "tokens_analyzed": [t["symbol"] for t in TOKENS[:5]],
        "candles": all_candles,
        "trades": all_trades,
        "statistics": stats,
    }
    
    # Save to file
    output_path = "/app/backtest_dataset_30d.json"
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)
    
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"Period: {DAYS} days")
    print(f"Tokens analyzed: {len(TOKENS[:5])}")
    print(f"Total trades: {stats['total_trades']}")
    print(f"Win rate: {stats['win_rate']:.1f}%")
    print(f"Total P&L: {stats['total_pnl_sol']:.4f} SOL")
    print(f"Best trade: +{stats['best_trade']:.1f}%")
    print(f"Worst trade: {stats['worst_trade']:.1f}%")
    print(f"\nDataset saved to: {output_path}")
    
    return dataset

if __name__ == "__main__":
    dataset = generate_dataset()
