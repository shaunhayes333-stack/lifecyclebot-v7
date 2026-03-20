#!/usr/bin/env python3
"""
ENHANCED Lifecycle Bot Backtesting Engine v2.0
Improvements based on v1.0 backtest results
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Trade:
    token: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    position_size_sol: float
    profit_loss_sol: float
    profit_loss_pct: float
    holding_period_days: int
    exit_reason: str

@dataclass
class EnhancedConfig:
    """Enhanced configuration with improvements"""
    initial_capital_sol: float = 10.0
    max_positions: int = 5
    base_position_size_pct: float = 0.12  # Reduced from 0.15 (more conservative)
    entry_score_threshold: float = 70.0  # Raised from 65 (more selective)
    exit_score_threshold: float = 35.0  # Lowered from 40 (exit faster on bad signals)
    
    # IMPROVED: Tighter stop loss
    stop_loss_pct: float = -10.0  # Was -15% (reduce losses faster)
    
    # IMPROVED: Partial profit taking
    partial_tp_1_pct: float = 15.0  # Take 30% profit at +15%
    partial_tp_1_size: float = 0.3
    partial_tp_2_pct: float = 25.0  # Take 40% profit at +25%
    partial_tp_2_size: float = 0.4
    take_profit_pct: float = 40.0  # Full exit at +40% (was +30%)
    
    max_holding_days: int = 5  # Reduced from 7 (exit faster)
    
    # NEW: Token quality filters
    min_liquidity_usd: float = 50000  # Minimum $50k liquidity
    max_volatility_pct: float = 50.0  # Skip tokens with >50% daily swings
    min_volume_usd: float = 10000  # Minimum $10k daily volume

class EnhancedBacktester:
    def __init__(self, config: EnhancedConfig):
        self.config = config
        self.capital_sol = config.initial_capital_sol
        self.positions = {}
        self.closed_trades = []
        self.daily_portfolio_values = []
        self.logs = []
        self.partial_exits = {}  # Track partial exits
        
    def log(self, msg: str):
        self.logs.append(msg)
        print(msg)
    
    def is_token_quality(self, token_data: Dict) -> Tuple[bool, str]:
        """
        NEW: Filter tokens based on quality criteria
        """
        current = token_data['current_data']
        
        # Check liquidity
        liquidity = current.get('liquidity_usd', 0)
        if liquidity < self.config.min_liquidity_usd:
            return False, f"Low liquidity (${liquidity:,.0f})"
        
        # Check volume
        volume = current.get('volume_24h', 0)
        if volume < self.config.min_volume_usd:
            return False, f"Low volume (${volume:,.0f})"
        
        # Check volatility (skip extreme movers)
        price_change = abs(current.get('price_change_24h', 0))
        if price_change > self.config.max_volatility_pct:
            return False, f"High volatility ({price_change:.1f}%)"
        
        return True, "Pass"
    
    def calculate_enhanced_entry_score(self, token_data: Dict, day_idx: int) -> float:
        """
        IMPROVED: Enhanced entry scoring with more factors
        """
        if day_idx < 5:  # Need more history
            return 0.0
        
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        # 1. Momentum (5-day instead of 3-day)
        prev_5_close = ohlcv[day_idx - 5]['close']
        momentum = ((current['close'] - prev_5_close) / prev_5_close) * 100
        
        # 2. Volume trend (stronger filter)
        current_vol = current['volume']
        avg_vol = sum(ohlcv[i]['volume'] for i in range(max(0, day_idx-5), day_idx)) / 5
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
        
        # 3. Price action
        price_action = ((current['close'] - current['open']) / current['open']) * 100 if current['open'] > 0 else 0
        
        # 4. NEW: Trend consistency (how many up days in last 5)
        up_days = sum(1 for i in range(max(0, day_idx-5), day_idx) 
                      if ohlcv[i]['close'] > ohlcv[i]['open'])
        trend_strength = (up_days / 5) * 20  # 0-20 points
        
        # 5. NEW: Volatility check (prefer moderate volatility)
        high_low_range = ((current['high'] - current['low']) / current['low']) * 100 if current['low'] > 0 else 0
        volatility_score = 10 if 2 < high_low_range < 15 else 0
        
        # Enhanced scoring formula
        score = 50.0
        score += momentum * 1.5  # Reduced weight
        score += (vol_ratio - 1) * 15  # Reduced weight
        score += price_action * 2
        score += trend_strength  # NEW
        score += volatility_score  # NEW
        
        return max(0, min(100, score))
    
    def calculate_dynamic_position_size(self, token_data: Dict, day_idx: int) -> float:
        """
        NEW: Dynamic position sizing based on volatility
        """
        ohlcv = token_data['historical_ohlcv']
        
        # Calculate recent volatility
        volatilities = []
        for i in range(max(0, day_idx-5), day_idx):
            if ohlcv[i]['low'] > 0:
                vol = ((ohlcv[i]['high'] - ohlcv[i]['low']) / ohlcv[i]['low']) * 100
                volatilities.append(vol)
        
        avg_vol = sum(volatilities) / len(volatilities) if volatilities else 10
        
        # Reduce position size for high volatility
        base_size = self.config.base_position_size_pct
        if avg_vol > 20:
            position_size = base_size * 0.7  # 30% smaller
        elif avg_vol > 10:
            position_size = base_size * 0.85  # 15% smaller
        else:
            position_size = base_size
        
        return position_size
    
    def calculate_enhanced_exit_score(self, token_data: Dict, day_idx: int, entry_info: Dict) -> Tuple[float, str]:
        """
        IMPROVED: Enhanced exit logic with partial profits
        """
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        current_price = current['close']
        entry_price = entry_info['entry_price']
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Check for partial profit taking
        token = entry_info.get('token', '')
        if token not in self.partial_exits:
            self.partial_exits[token] = {'tp1': False, 'tp2': False}
        
        # Partial TP 1 (15% profit - take 30%)
        if profit_pct >= self.config.partial_tp_1_pct and not self.partial_exits[token]['tp1']:
            return 100, f"Partial TP1 ({self.config.partial_tp_1_pct:.0f}%)"
        
        # Partial TP 2 (25% profit - take 40%)
        if profit_pct >= self.config.partial_tp_2_pct and not self.partial_exits[token]['tp2']:
            return 100, f"Partial TP2 ({self.config.partial_tp_2_pct:.0f}%)"
        
        # Full exit conditions
        if profit_pct >= self.config.take_profit_pct:
            return 100, "Full Take Profit"
        
        if profit_pct <= self.config.stop_loss_pct:
            return 100, "Stop Loss"
        
        # Momentum reversal
        if day_idx >= 3:
            prev_3_close = ohlcv[day_idx - 3]['close']
            momentum = ((current_price - prev_3_close) / prev_3_close) * 100
            if profit_pct > 5 and momentum < -8:  # Stronger reversal signal
                return 90, "Momentum Reversal"
        
        # Max holding period
        holding_days = day_idx - entry_info['entry_day_idx']
        if holding_days >= self.config.max_holding_days:
            return 85, "Max Holding Period"
        
        return 0, ""
    
    def can_open_position(self) -> bool:
        return len(self.positions) < self.config.max_positions
    
    def open_position(self, token: str, token_data: Dict, day_idx: int):
        """Open position with dynamic sizing"""
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        # Dynamic position sizing
        position_size_pct = self.calculate_dynamic_position_size(token_data, day_idx)
        position_size_sol = self.capital_sol * position_size_pct
        
        if position_size_sol > self.capital_sol:
            return
        
        entry_price = current['close']
        
        self.positions[token] = {
            'entry_date': current['date'],
            'entry_day_idx': day_idx,
            'entry_price': entry_price,
            'initial_position_size_sol': position_size_sol,
            'position_size_sol': position_size_sol,  # Current size (after partial exits)
            'token_data': token_data,
            'token': token
        }
        
        self.capital_sol -= position_size_sol
        self.partial_exits[token] = {'tp1': False, 'tp2': False}
        
        self.log(f"🟢 ENTRY: {token} @ ${entry_price:.6f} | Size: {position_size_sol:.2f} SOL | Date: {current['date']}")
    
    def close_position(self, token: str, day_idx: int, reason: str, partial_pct: float = 1.0):
        """
        Close position (full or partial)
        """
        if token not in self.positions:
            return
        
        entry_info = self.positions[token]
        token_data = entry_info['token_data']
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        exit_price = current['close']
        entry_price = entry_info['entry_price']
        position_size_sol = entry_info['position_size_sol']
        
        # Calculate amount to close
        close_amount = position_size_sol * partial_pct
        
        # Calculate P&L
        profit_pct = ((exit_price - entry_price) / entry_price) * 100
        profit_loss_sol = close_amount * (profit_pct / 100)
        
        # Return capital + profit
        self.capital_sol += close_amount + profit_loss_sol
        
        # Update position size or close fully
        if partial_pct < 1.0:
            # Partial exit
            entry_info['position_size_sol'] -= close_amount
            emoji = "🟡"
            self.log(f"{emoji} PARTIAL EXIT: {token} ({partial_pct*100:.0f}%) @ ${exit_price:.6f} | P&L: {profit_loss_sol:+.2f} SOL ({profit_pct:+.1f}%) | Reason: {reason}")
            
            # Mark partial exit
            if 'TP1' in reason:
                self.partial_exits[token]['tp1'] = True
            elif 'TP2' in reason:
                self.partial_exits[token]['tp2'] = True
        else:
            # Full exit
            holding_days = day_idx - entry_info['entry_day_idx']
            trade = Trade(
                token=token,
                entry_date=entry_info['entry_date'],
                entry_price=entry_price,
                exit_date=current['date'],
                exit_price=exit_price,
                position_size_sol=entry_info['initial_position_size_sol'],
                profit_loss_sol=profit_loss_sol,
                profit_loss_pct=profit_pct,
                holding_period_days=holding_days,
                exit_reason=reason
            )
            
            self.closed_trades.append(trade)
            del self.positions[token]
            if token in self.partial_exits:
                del self.partial_exits[token]
            
            emoji = "🟢" if profit_loss_sol > 0 else "🔴"
            self.log(f"{emoji} FULL EXIT: {token} @ ${exit_price:.6f} | P&L: {profit_loss_sol:+.2f} SOL ({profit_pct:+.1f}%) | Reason: {reason}")
    
    def run_backtest(self, dataset: Dict) -> Dict:
        """Run enhanced backtest"""
        tokens = dataset['tokens']
        num_days = dataset['metadata']['period_days']
        
        self.log(f"\n{'='*80}")
        self.log(f"ENHANCED LIFECYCLE BOT BACKTEST v2.0")
        self.log(f"{'='*80}")
        self.log(f"Improvements: Tighter stops, partial profits, quality filters")
        self.log(f"{'='*80}\n")
        
        # Filter tokens by quality
        quality_tokens = []
        for token in tokens:
            is_quality, reason = self.is_token_quality(token)
            if is_quality:
                quality_tokens.append(token)
            else:
                self.log(f"⚠️  FILTERED OUT: {token['symbol']} - {reason}")
        
        self.log(f"\n✅ {len(quality_tokens)}/{len(tokens)} tokens passed quality filters\n")
        
        # Iterate through each day
        for day_idx in range(num_days):
            day_date = quality_tokens[0]['historical_ohlcv'][day_idx]['date'].split()[0] if quality_tokens else ""
            
            # Check exit signals
            for token_symbol in list(self.positions.keys()):
                exit_score, reason = self.calculate_enhanced_exit_score(
                    self.positions[token_symbol]['token_data'], 
                    day_idx, 
                    self.positions[token_symbol]
                )
                
                if exit_score >= 80:
                    if 'Partial TP1' in reason:
                        self.close_position(token_symbol, day_idx, reason, self.config.partial_tp_1_size)
                    elif 'Partial TP2' in reason:
                        self.close_position(token_symbol, day_idx, reason, self.config.partial_tp_2_size)
                    else:
                        self.close_position(token_symbol, day_idx, reason, 1.0)
            
            # Check entry signals
            if self.can_open_position():
                opportunities = []
                for token in quality_tokens:
                    if token['symbol'] in self.positions:
                        continue
                    
                    entry_score = self.calculate_enhanced_entry_score(token, day_idx)
                    if entry_score >= self.config.entry_score_threshold:
                        opportunities.append((token['symbol'], entry_score, token))
                
                opportunities.sort(key=lambda x: x[1], reverse=True)
                
                for symbol, score, token_data in opportunities[:self.config.max_positions - len(self.positions)]:
                    self.open_position(symbol, token_data, day_idx)
            
            # Track portfolio value
            portfolio_value = self.capital_sol
            for token_symbol, entry_info in self.positions.items():
                token_data = entry_info['token_data']
                current_price = token_data['historical_ohlcv'][day_idx]['close']
                position_size_sol = entry_info['position_size_sol']
                entry_price = entry_info['entry_price']
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                position_value = position_size_sol * (1 + profit_pct / 100)
                portfolio_value += position_value
            
            self.daily_portfolio_values.append({
                'day': day_idx,
                'date': day_date,
                'value': portfolio_value
            })
        
        # Close remaining positions
        for token_symbol in list(self.positions.keys()):
            self.close_position(token_symbol, num_days - 1, "End of Period", 1.0)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate report"""
        total_trades = len(self.closed_trades)
        if total_trades == 0:
            return {"error": "No trades executed"}
        
        winning_trades = [t for t in self.closed_trades if t.profit_loss_sol > 0]
        losing_trades = [t for t in self.closed_trades if t.profit_loss_sol <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        total_profit = sum(t.profit_loss_sol for t in winning_trades)
        total_loss = sum(t.profit_loss_sol for t in losing_trades)
        net_profit = total_profit + total_loss
        
        avg_win = total_profit / len(winning_trades) if winning_trades else 0
        avg_loss = total_loss / len(losing_trades) if losing_trades else 0
        
        final_capital = self.capital_sol
        roi = ((final_capital - self.config.initial_capital_sol) / self.config.initial_capital_sol) * 100
        
        best_trade = max(self.closed_trades, key=lambda t: t.profit_loss_pct)
        worst_trade = min(self.closed_trades, key=lambda t: t.profit_loss_pct)
        
        avg_holding = sum(t.holding_period_days for t in self.closed_trades) / total_trades
        
        return {
            'summary': {
                'initial_capital_sol': self.config.initial_capital_sol,
                'final_capital_sol': final_capital,
                'net_profit_sol': net_profit,
                'roi_pct': roi,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate_pct': win_rate,
            },
            'performance': {
                'total_profit_sol': total_profit,
                'total_loss_sol': total_loss,
                'avg_win_sol': avg_win,
                'avg_loss_sol': avg_loss,
                'profit_factor': abs(total_profit / total_loss) if total_loss != 0 else float('inf'),
                'avg_holding_period_days': avg_holding,
            },
            'best_trade': {
                'token': best_trade.token,
                'profit_pct': best_trade.profit_loss_pct,
                'profit_sol': best_trade.profit_loss_sol,
            },
            'worst_trade': {
                'token': worst_trade.token,
                'profit_pct': worst_trade.profit_loss_pct,
                'profit_sol': worst_trade.profit_loss_sol,
            },
            'trades': [
                {
                    'token': t.token,
                    'profit_loss_sol': t.profit_loss_sol,
                    'profit_loss_pct': t.profit_loss_pct,
                    'holding_days': t.holding_period_days,
                    'exit_reason': t.exit_reason,
                }
                for t in self.closed_trades
            ],
        }


def print_comparison(v1_report: Dict, v2_report: Dict):
    """Print comparison between v1 and v2"""
    print(f"\n{'='*80}")
    print("PERFORMANCE COMPARISON: v1.0 vs v2.0 (ENHANCED)")
    print(f"{'='*80}\n")
    
    print(f"{'Metric':<30} | {'v1.0':>15} | {'v2.0':>15} | {'Improvement':>15}")
    print(f"{'-'*80}")
    
    v1 = v1_report['summary']
    v2 = v2_report['summary']
    
    metrics = [
        ('ROI', v1['roi_pct'], v2['roi_pct'], '%'),
        ('Final Capital (SOL)', v1['final_capital_sol'], v2['final_capital_sol'], 'SOL'),
        ('Net Profit (SOL)', v1['net_profit_sol'], v2['net_profit_sol'], 'SOL'),
        ('Win Rate', v1['win_rate_pct'], v2['win_rate_pct'], '%'),
        ('Total Trades', v1['total_trades'], v2['total_trades'], ''),
    ]
    
    v1p = v1_report['performance']
    v2p = v2_report['performance']
    
    metrics.extend([
        ('Profit Factor', v1p['profit_factor'], v2p['profit_factor'], ''),
        ('Avg Win (SOL)', v1p['avg_win_sol'], v2p['avg_win_sol'], 'SOL'),
        ('Avg Loss (SOL)', v1p['avg_loss_sol'], v2p['avg_loss_sol'], 'SOL'),
    ])
    
    for name, val1, val2, unit in metrics:
        if 'Loss' in name:
            improvement = ((val1 - val2) / abs(val1) * 100) if val1 != 0 else 0  # Less loss is better
            imp_str = f"+{improvement:.1f}%" if improvement > 0 else f"{improvement:.1f}%"
        else:
            improvement = ((val2 - val1) / abs(val1) * 100) if val1 != 0 else 0
            imp_str = f"+{improvement:.1f}%" if improvement > 0 else f"{improvement:.1f}%"
        
        if unit in ['SOL', '%']:
            print(f"{name:<30} | {val1:>13.2f}{unit:>2} | {val2:>13.2f}{unit:>2} | {imp_str:>15}")
        else:
            print(f"{name:<30} | {val1:>15.2f} | {val2:>15.2f} | {imp_str:>15}")
    
    print(f"{'='*80}\n")


def main():
    # Load dataset
    with open('/app/backtest_data_30d_comprehensive.json', 'r') as f:
        dataset = json.load(f)
    
    # Load v1 report for comparison
    try:
        with open('/app/backtest_report.json', 'r') as f:
            v1_report = json.load(f)
    except:
        v1_report = None
    
    # Run enhanced backtest
    config = EnhancedConfig()
    backtester = EnhancedBacktester(config)
    v2_report = backtester.run_backtest(dataset)
    
    # Print comparison if v1 exists
    if v1_report:
        print_comparison(v1_report, v2_report)
    
    # Save v2 report
    with open('/app/backtest_report_v2_enhanced.json', 'w') as f:
        json.dump(v2_report, f, indent=2)
    
    print(f"💾 Enhanced report saved to: /app/backtest_report_v2_enhanced.json\n")


if __name__ == "__main__":
    main()
