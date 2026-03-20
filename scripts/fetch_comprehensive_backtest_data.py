#!/usr/bin/env python3
"""
Enhanced Solana token data fetcher for backtesting
Uses multiple free APIs to get 30 top tokens
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

class EnhancedDataFetcher:
    def __init__(self):
        self.headers = {"Accept": "application/json"}
        
    def get_top_solana_tokens_coingecko(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch top Solana tokens from CoinGecko (free API)"""
        print(f"🔍 Fetching top {limit} Solana tokens from CoinGecko...")
        
        try:
            # Get Solana ecosystem tokens
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'category': 'solana-ecosystem',
                'order': 'volume_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': False
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                tokens = response.json()
                print(f"✅ Found {len(tokens)} tokens from CoinGecko")
                return tokens
            else:
                print(f"⚠️ CoinGecko returned status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ CoinGecko error: {e}")
            return []
    
    def get_dexscreener_tokens(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch from DexScreener as backup"""
        print(f"🔍 Fetching tokens from DexScreener...")
        
        try:
            url = "https://api.dexscreener.com/latest/dex/search?q=SOL"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                # Filter for Solana
                solana_pairs = [p for p in pairs if p.get('chainId') == 'solana']
                print(f"✅ Found {len(solana_pairs)} Solana pairs")
                return solana_pairs[:limit]
            else:
                return []
                
        except Exception as e:
            print(f"❌ DexScreener error: {e}")
            return []
    
    def generate_realistic_ohlcv(self, 
                                  current_price: float,
                                  volume_24h: float,
                                  price_change_24h: float,
                                  days: int = 30) -> List[Dict[str, Any]]:
        """
        Generate realistic OHLCV data based on token characteristics
        """
        if current_price <= 0:
            return []
        
        # Estimate volatility from 24h change
        daily_volatility = abs(price_change_24h) if price_change_24h else 5.0
        daily_volatility = max(min(daily_volatility, 40.0), 1.0)
        
        historical_data = []
        current_time = datetime.now()
        
        # Work backwards from current price
        price = current_price
        
        for day in range(days):
            date = current_time - timedelta(days=days-day)
            
            # Random walk with realistic characteristics
            daily_change = random.gauss(0, daily_volatility/100)
            
            # Add some momentum (trending behavior)
            if day > 0 and len(historical_data) > 0:
                prev_change = (historical_data[-1]['close'] - historical_data[-1]['open']) / historical_data[-1]['open']
                momentum = prev_change * 0.3  # 30% momentum carry-over
                daily_change += momentum
            
            open_price = price
            close_price = price * (1 + daily_change)
            
            # Realistic intraday movement
            intraday_vol = daily_volatility / 3
            high_price = max(open_price, close_price) * (1 + random.uniform(0, intraday_vol/100))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, intraday_vol/100))
            
            # Volume varies ±50%
            volume = volume_24h * random.uniform(0.5, 1.5) if volume_24h > 0 else 100000
            
            historical_data.append({
                'timestamp': int(date.timestamp()),
                'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                'open': round(open_price, 10),
                'high': round(high_price, 10),
                'low': round(low_price, 10),
                'close': round(close_price, 10),
                'volume': round(volume, 2)
            })
            
            price = close_price
        
        return historical_data
    
    def build_comprehensive_dataset(self, num_tokens: int = 30, days: int = 30) -> Dict[str, Any]:
        """Build dataset using multiple sources"""
        print(f"\n🚀 Building comprehensive backtest dataset\n")
        print(f"Target: {num_tokens} tokens over {days} days\n")
        
        # Try CoinGecko first
        tokens_data = self.get_top_solana_tokens_coingecko(num_tokens)
        
        # If CoinGecko doesn't return enough, supplement with DexScreener
        if len(tokens_data) < num_tokens:
            print(f"\n📡 Supplementing with DexScreener data...")
            dex_tokens = self.get_dexscreener_tokens(num_tokens - len(tokens_data))
            time.sleep(2)  # Rate limiting
        
        dataset = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'period_days': days,
                'num_tokens': len(tokens_data),
                'data_sources': ['CoinGecko API', 'Simulated Historical Data'],
                'note': 'Current data from CoinGecko, historical OHLCV simulated with realistic patterns'
            },
            'tokens': []
        }
        
        for idx, token in enumerate(tokens_data, 1):
            print(f"\n[{idx}/{len(tokens_data)}] Processing {token.get('symbol', 'UNKNOWN').upper()}")
            
            # Extract data (CoinGecko format)
            current_price = token.get('current_price', 0)
            volume_24h = token.get('total_volume', 0)
            price_change_24h = token.get('price_change_percentage_24h', 0)
            market_cap = token.get('market_cap', 0)
            
            token_info = {
                'symbol': token.get('symbol', 'UNKNOWN').upper(),
                'name': token.get('name', 'Unknown'),
                'coingecko_id': token.get('id', ''),
                'current_data': {
                    'price_usd': current_price,
                    'volume_24h': volume_24h,
                    'price_change_24h': price_change_24h,
                    'market_cap': market_cap,
                    'market_cap_rank': token.get('market_cap_rank', 0),
                    'circulating_supply': token.get('circulating_supply', 0),
                    'total_supply': token.get('total_supply', 0),
                    'ath': token.get('ath', current_price),
                    'ath_change_percentage': token.get('ath_change_percentage', 0),
                },
                'historical_ohlcv': []
            }
            
            # Generate historical data
            print(f"  📈 Generating {days}-day historical OHLCV...")
            historical_data = self.generate_realistic_ohlcv(
                current_price, volume_24h, price_change_24h, days
            )
            token_info['historical_ohlcv'] = historical_data
            
            print(f"  ✅ Generated {len(historical_data)} data points")
            
            dataset['tokens'].append(token_info)
            
            # Rate limiting
            time.sleep(1.5)
        
        return dataset


def main():
    fetcher = EnhancedDataFetcher()
    
    # Build dataset
    dataset = fetcher.build_comprehensive_dataset(num_tokens=30, days=30)
    
    if dataset and len(dataset['tokens']) > 0:
        # Save to JSON
        output_file = '/app/backtest_data_30d_comprehensive.json'
        with open(output_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        print(f"\n{'='*70}")
        print(f"✅ COMPREHENSIVE DATASET CREATED")
        print(f"{'='*70}")
        print(f"📁 Saved to: {output_file}")
        print(f"📊 Tokens: {len(dataset['tokens'])}")
        print(f"📅 Period: {dataset['metadata']['period_days']} days")
        print(f"💾 Size: {len(json.dumps(dataset)) / 1024:.2f} KB")
        
        # Print summary
        print(f"\n📈 TOP 10 TOKENS BY VOLUME:")
        for idx, token in enumerate(sorted(dataset['tokens'], 
                                          key=lambda x: x['current_data']['volume_24h'], 
                                          reverse=True)[:10], 1):
            print(f"  {idx:2d}. {token['symbol']:8s} - ${token['current_data']['volume_24h']:,.0f} 24h vol - ${token['current_data']['price_usd']:.6f}")
        
        print(f"\n🎯 Dataset ready for backtesting!")
        print(f"{'='*70}\n")
        
        return output_file
    else:
        print("\n❌ Failed to create dataset")
        return None


if __name__ == "__main__":
    main()
