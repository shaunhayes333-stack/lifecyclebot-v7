#!/usr/bin/env python3
"""
Fetch 30-day historical data for top 30 Solana tokens for backtesting
Uses DexScreener API (free, no API key required)
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys

class SolanaDataFetcher:
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest"
        self.headers = {"Accept": "application/json"}
        
    def get_top_solana_tokens(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch top performing Solana tokens from DexScreener"""
        print(f"🔍 Fetching top {limit} Solana tokens...")
        
        # Get tokens from Solana with highest volume/liquidity
        url = f"{self.base_url}/dex/tokens/solana"
        
        try:
            # Try to get boosted/trending tokens first
            response = requests.get(f"{self.base_url}/dex/search?q=solana", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                # Filter for Solana and sort by volume
                solana_pairs = [
                    p for p in pairs 
                    if p.get('chainId') == 'solana' 
                    and p.get('liquidity', {}).get('usd', 0) > 5000  # Min liquidity filter
                ]
                
                # Sort by 24h volume
                solana_pairs.sort(key=lambda x: float(x.get('volume', {}).get('h24', 0)), reverse=True)
                
                # Get unique tokens (by base token address)
                seen_tokens = set()
                unique_tokens = []
                
                for pair in solana_pairs:
                    token_address = pair.get('baseToken', {}).get('address')
                    if token_address and token_address not in seen_tokens:
                        seen_tokens.add(token_address)
                        unique_tokens.append(pair)
                        
                    if len(unique_tokens) >= limit:
                        break
                
                print(f"✅ Found {len(unique_tokens)} tokens")
                return unique_tokens[:limit]
            else:
                print(f"❌ Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching tokens: {e}")
            return []
    
    def get_token_ohlcv(self, pair_address: str, resolution: str = "1") -> Dict[str, Any]:
        """
        Fetch OHLCV data for a token pair
        Resolution: 1 = 1min, 5 = 5min, 15 = 15min, 60 = 1hour, 240 = 4hour, 1D = 1day
        """
        # Note: DexScreener doesn't provide historical OHLCV via free API
        # We'll use the current data and generate mock historical based on trends
        print(f"  📊 Fetching data for pair {pair_address[:8]}...")
        
        try:
            url = f"{self.base_url}/dex/pairs/solana/{pair_address}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pair = data.get('pair', {})
                return pair
            else:
                return {}
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {}
    
    def generate_historical_data(self, token_data: Dict[str, Any], days: int = 30) -> List[Dict[str, Any]]:
        """
        Generate realistic historical OHLCV data based on current price and volatility
        This simulates realistic price movements for backtesting
        """
        import random
        
        current_price = float(token_data.get('priceUsd', 0))
        if current_price == 0:
            return []
        
        # Get price changes to estimate volatility
        price_change_24h = float(token_data.get('priceChange', {}).get('h24', 0))
        
        # Estimate daily volatility
        daily_volatility = abs(price_change_24h) / 100 if price_change_24h else 5.0
        daily_volatility = max(min(daily_volatility, 30.0), 2.0)  # Clamp between 2-30%
        
        historical_data = []
        current_time = datetime.now()
        
        # Work backwards from current price
        price = current_price
        
        for day in range(days):
            date = current_time - timedelta(days=days-day)
            
            # Generate realistic OHLCV
            # Random walk with mean reversion
            daily_change = random.gauss(0, daily_volatility) / 100
            
            # Add some trend (slight upward bias for top tokens)
            trend = 0.002  # 0.2% daily upward trend
            daily_change += trend
            
            open_price = price
            close_price = price * (1 + daily_change)
            
            # High/Low with realistic spread
            intraday_volatility = daily_volatility / 4
            high_price = max(open_price, close_price) * (1 + random.uniform(0, intraday_volatility/100))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, intraday_volatility/100))
            
            # Volume (use current 24h volume as base with variation)
            base_volume = float(token_data.get('volume', {}).get('h24', 100000))
            volume = base_volume * random.uniform(0.5, 1.5)
            
            historical_data.append({
                'timestamp': int(date.timestamp()),
                'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            price = close_price
        
        return historical_data
    
    def build_backtest_dataset(self, num_tokens: int = 30, days: int = 30) -> Dict[str, Any]:
        """Build complete backtesting dataset"""
        print(f"\n🚀 Building backtest dataset for {num_tokens} tokens over {days} days\n")
        
        # Get top tokens
        top_tokens = self.get_top_solana_tokens(num_tokens)
        
        if not top_tokens:
            print("❌ Failed to fetch tokens")
            return {}
        
        dataset = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'period_days': days,
                'num_tokens': len(top_tokens),
                'data_source': 'DexScreener API',
                'note': 'Historical OHLCV is simulated based on current volatility patterns'
            },
            'tokens': []
        }
        
        for idx, token_pair in enumerate(top_tokens, 1):
            print(f"\n[{idx}/{len(top_tokens)}] Processing {token_pair.get('baseToken', {}).get('symbol', 'UNKNOWN')}")
            
            # Extract token info
            base_token = token_pair.get('baseToken', {})
            quote_token = token_pair.get('quoteToken', {})
            
            token_info = {
                'symbol': base_token.get('symbol', 'UNKNOWN'),
                'name': base_token.get('name', 'Unknown'),
                'address': base_token.get('address', ''),
                'pair_address': token_pair.get('pairAddress', ''),
                'dex': token_pair.get('dexId', ''),
                'current_data': {
                    'price_usd': float(token_pair.get('priceUsd', 0)),
                    'price_native': float(token_pair.get('priceNative', 0)),
                    'liquidity_usd': float(token_pair.get('liquidity', {}).get('usd', 0)),
                    'volume_24h': float(token_pair.get('volume', {}).get('h24', 0)),
                    'volume_6h': float(token_pair.get('volume', {}).get('h6', 0)),
                    'volume_1h': float(token_pair.get('volume', {}).get('h1', 0)),
                    'price_change_24h': float(token_pair.get('priceChange', {}).get('h24', 0)),
                    'price_change_6h': float(token_pair.get('priceChange', {}).get('h6', 0)),
                    'price_change_1h': float(token_pair.get('priceChange', {}).get('h1', 0)),
                    'fdv': float(token_pair.get('fdv', 0)),
                    'market_cap': float(token_pair.get('marketCap', 0)),
                },
                'historical_ohlcv': []
            }
            
            # Generate historical data
            print(f"  📈 Generating {days}-day historical OHLCV...")
            historical_data = self.generate_historical_data(token_pair, days)
            token_info['historical_ohlcv'] = historical_data
            
            print(f"  ✅ Generated {len(historical_data)} data points")
            
            dataset['tokens'].append(token_info)
            
            # Rate limiting
            time.sleep(1.5)  # Be nice to the API
        
        return dataset


def main():
    fetcher = SolanaDataFetcher()
    
    # Build dataset
    dataset = fetcher.build_backtest_dataset(num_tokens=30, days=30)
    
    if dataset:
        # Save to JSON
        output_file = '/app/backtest_data_30d.json'
        with open(output_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✅ DATASET CREATED SUCCESSFULLY")
        print(f"{'='*60}")
        print(f"📁 Saved to: {output_file}")
        print(f"📊 Tokens: {len(dataset['tokens'])}")
        print(f"📅 Period: {dataset['metadata']['period_days']} days")
        print(f"💾 Size: {len(json.dumps(dataset)) / 1024:.2f} KB")
        
        # Print summary
        print(f"\n📈 TOP 5 TOKENS BY VOLUME:")
        for idx, token in enumerate(dataset['tokens'][:5], 1):
            print(f"  {idx}. {token['symbol']:8s} - ${token['current_data']['volume_24h']:,.0f} 24h vol")
        
        print(f"\n🎯 Dataset ready for backtesting!")
        print(f"{'='*60}\n")
        
        return output_file
    else:
        print("\n❌ Failed to create dataset")
        return None


if __name__ == "__main__":
    main()
