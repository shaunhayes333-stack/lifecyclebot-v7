#!/usr/bin/env python3
"""
Lifecycle Bot Backtesting Engine
Tests the bot's trading strategy against historical data
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
class BacktestConfig:
    """Simplified bot configuration for backtesting"""
    initial_capital_sol: float = 10.0  # Starting capital in SOL
    max_positions: int = 5  # Max concurrent positions
    position_size_pct: float = 0.15  # 15% of capital per trade
    entry_score_threshold: float = 65.0  # Minimum score to enter
    exit_score_threshold: float = 40.0  # Score to exit position
    take_profit_pct: float = 30.0  # Take profit at +30%
    stop_loss_pct: float = -15.0  # Stop loss at -15%
    max_holding_days: int = 7  # Max holding period

class LifecycleBacktester:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.capital_sol = config.initial_capital_sol
        self.positions = {}  # token -> entry_info
        self.closed_trades = []
        self.daily_portfolio_values = []
        self.logs = []
        
    def log(self, msg: str):
        """Log message"""
        self.logs.append(msg)
        print(msg)
    
    def calculate_entry_score(self, token_data: Dict, day_idx: int) -> float:
        """
        Simplified entry scoring based on momentum and volume
        Real bot uses complex multi-factor model
        """
        if day_idx < 3:  # Need history
            return 0.0
        
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        # Calculate momentum (3-day price change)
        prev_3_close = ohlcv[day_idx - 3]['close']
        momentum = ((current['close'] - prev_3_close) / prev_3_close) * 100
        
        # Calculate volume trend
        current_vol = current['volume']
        avg_vol = sum(ohlcv[i]['volume'] for i in range(max(0, day_idx-3), day_idx)) / 3
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
        
        # Calculate price action (bullish candle)
        price_action = ((current['close'] - current['open']) / current['open']) * 100 if current['open'] > 0 else 0
        
        # Simple scoring formula
        score = 50.0  # Base score
        score += momentum * 2  # Momentum weight
        score += (vol_ratio - 1) * 20  # Volume surge bonus
        score += price_action * 3  # Price action weight
        
        # Clamp between 0-100
        return max(0, min(100, score))
    
    def calculate_exit_score(self, token_data: Dict, day_idx: int, entry_info: Dict) -> float:
        """
        Simplified exit scoring based on profit and momentum reversal
        """
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        # Calculate current profit
        current_price = current['close']
        entry_price = entry_info['entry_price']
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Calculate momentum reversal
        if day_idx >= 2:
            prev_2_close = ohlcv[day_idx - 2]['close']
            momentum = ((current_price - prev_2_close) / prev_2_close) * 100
        else:
            momentum = 0
        
        # Exit score (higher = should exit)
        score = 50.0
        
        # Exit if profit target hit
        if profit_pct >= self.config.take_profit_pct:
            score += 50
        
        # Exit if stop loss hit
        if profit_pct <= self.config.stop_loss_pct:
            score += 50
        
        # Exit if momentum reverses (negative momentum when profitable)
        if profit_pct > 10 and momentum < -5:
            score += 30
        
        # Exit if holding too long
        holding_days = day_idx - entry_info['entry_day_idx']
        if holding_days >= self.config.max_holding_days:
            score += 40
        
        return score
    
    def can_open_position(self) -> bool:
        """Check if we can open a new position"""
        return len(self.positions) < self.config.max_positions
    
    def open_position(self, token: str, token_data: Dict, day_idx: int):
        """Open a new position"""
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        # Calculate position size
        position_size_sol = self.capital_sol * self.config.position_size_pct
        
        if position_size_sol > self.capital_sol:
            return  # Not enough capital
        
        entry_price = current['close']
        
        self.positions[token] = {
            'entry_date': current['date'],
            'entry_day_idx': day_idx,
            'entry_price': entry_price,
            'position_size_sol': position_size_sol,
            'token_data': token_data
        }
        
        self.capital_sol -= position_size_sol
        
        self.log(f"🟢 ENTRY: {token} @ ${entry_price:.6f} | Size: {position_size_sol:.2f} SOL | Date: {current['date']}")
    
    def close_position(self, token: str, day_idx: int, reason: str):
        """Close an existing position"""
        if token not in self.positions:
            return
        
        entry_info = self.positions[token]
        token_data = entry_info['token_data']
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        exit_price = current['close']
        entry_price = entry_info['entry_price']
        position_size_sol = entry_info['position_size_sol']
        
        # Calculate P&L
        profit_pct = ((exit_price - entry_price) / entry_price) * 100
        profit_loss_sol = position_size_sol * (profit_pct / 100)
        
        # Return capital + profit
        self.capital_sol += position_size_sol + profit_loss_sol
        
        # Create trade record
        holding_days = day_idx - entry_info['entry_day_idx']
        trade = Trade(
            token=token,
            entry_date=entry_info['entry_date'],
            entry_price=entry_price,
            exit_date=current['date'],
            exit_price=exit_price,
            position_size_sol=position_size_sol,
            profit_loss_sol=profit_loss_sol,
            profit_loss_pct=profit_pct,
            holding_period_days=holding_days,
            exit_reason=reason
        )
        
        self.closed_trades.append(trade)
        del self.positions[token]
        
        emoji = "🟢" if profit_loss_sol > 0 else "🔴"
        self.log(f"{emoji} EXIT: {token} @ ${exit_price:.6f} | P&L: {profit_loss_sol:+.2f} SOL ({profit_pct:+.1f}%) | Reason: {reason} | Date: {current['date']}")
    
    def run_backtest(self, dataset: Dict) -> Dict:
        """Run backtest on the dataset"""
        tokens = dataset['tokens']
        num_days = dataset['metadata']['period_days']
        
        self.log(f"\n{'='*80}")
        self.log(f"LIFECYCLE BOT BACKTEST")
        self.log(f"{'='*80}")
        self.log(f"Period: {num_days} days")
        self.log(f"Tokens: {len(tokens)}")
        self.log(f"Initial Capital: {self.config.initial_capital_sol} SOL")
        self.log(f"{'='*80}\n")
        
        # Iterate through each day
        for day_idx in range(num_days):
            day_date = tokens[0]['historical_ohlcv'][day_idx]['date'].split()[0]
            
            # Check exit signals for open positions
            for token_symbol in list(self.positions.keys()):
                token_data = self.positions[token_symbol]['token_data']
                exit_score = self.calculate_exit_score(token_data, day_idx, self.positions[token_symbol])
                
                # Exit conditions
                ohlcv = token_data['historical_ohlcv']
                current_price = ohlcv[day_idx]['close']
                entry_price = self.positions[token_symbol]['entry_price']
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                holding_days = day_idx - self.positions[token_symbol]['entry_day_idx']
                
                should_exit = False
                reason = ""
                
                if profit_pct >= self.config.take_profit_pct:
                    should_exit = True
                    reason = "Take Profit"
                elif profit_pct <= self.config.stop_loss_pct:
                    should_exit = True
                    reason = "Stop Loss"
                elif holding_days >= self.config.max_holding_days:
                    should_exit = True
                    reason = "Max Holding Period"
                elif exit_score >= 70:
                    should_exit = True
                    reason = "Exit Signal"
                
                if should_exit:
                    self.close_position(token_symbol, day_idx, reason)
            
            # Check entry signals for new positions
            if self.can_open_position():
                # Evaluate all tokens
                opportunities = []
                for token in tokens:
                    if token['symbol'] in self.positions:
                        continue  # Already in position
                    
                    entry_score = self.calculate_entry_score(token, day_idx)
                    if entry_score >= self.config.entry_score_threshold:
                        opportunities.append((token['symbol'], entry_score, token))
                
                # Sort by score and take best opportunities
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
        
        # Close any remaining positions at end
        for token_symbol in list(self.positions.keys()):
            self.close_position(token_symbol, num_days - 1, "End of Period")
        
        # Calculate statistics
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate comprehensive backtest report"""
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
        
        # Best and worst trades
        best_trade = max(self.closed_trades, key=lambda t: t.profit_loss_pct)
        worst_trade = min(self.closed_trades, key=lambda t: t.profit_loss_pct)
        
        # Average holding period
        avg_holding = sum(t.holding_period_days for t in self.closed_trades) / total_trades
        
        report = {
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
                'entry_date': best_trade.entry_date,
                'exit_date': best_trade.exit_date,
            },
            'worst_trade': {
                'token': worst_trade.token,
                'profit_pct': worst_trade.profit_loss_pct,
                'profit_sol': worst_trade.profit_loss_sol,
                'entry_date': worst_trade.entry_date,
                'exit_date': worst_trade.exit_date,
            },
            'trades': [
                {
                    'token': t.token,
                    'entry_date': t.entry_date,
                    'exit_date': t.exit_date,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'profit_loss_sol': t.profit_loss_sol,
                    'profit_loss_pct': t.profit_loss_pct,
                    'holding_days': t.holding_period_days,
                    'exit_reason': t.exit_reason,
                }
                for t in self.closed_trades
            ],
            'daily_portfolio': self.daily_portfolio_values,
        }
        
        return report


def print_report(report: Dict):
    """Print formatted backtest report"""
    print(f"\n{'='*80}")
    print("BACKTEST RESULTS")
    print(f"{'='*80}\n")
    
    summary = report['summary']
    perf = report['performance']
    
    print("📊 SUMMARY")
    print(f"{'─'*80}")
    print(f"Initial Capital:  {summary['initial_capital_sol']:.2f} SOL")
    print(f"Final Capital:    {summary['final_capital_sol']:.2f} SOL")
    print(f"Net Profit:       {summary['net_profit_sol']:+.2f} SOL")
    print(f"ROI:              {summary['roi_pct']:+.2f}%")
    print(f"\n📈 PERFORMANCE")
    print(f"{'─'*80}")
    print(f"Total Trades:     {summary['total_trades']}")
    print(f"Winning Trades:   {summary['winning_trades']} ({summary['win_rate_pct']:.1f}%)")
    print(f"Losing Trades:    {summary['losing_trades']} ({100-summary['win_rate_pct']:.1f}%)")
    print(f"Win Rate:         {summary['win_rate_pct']:.1f}%")
    print(f"\n💰 PROFIT/LOSS")
    print(f"{'─'*80}")
    print(f"Total Profit:     {perf['total_profit_sol']:+.2f} SOL")
    print(f"Total Loss:       {perf['total_loss_sol']:+.2f} SOL")
    print(f"Average Win:      {perf['avg_win_sol']:+.2f} SOL")
    print(f"Average Loss:     {perf['avg_loss_sol']:+.2f} SOL")
    print(f"Profit Factor:    {perf['profit_factor']:.2f}")
    print(f"Avg Hold Period:  {perf['avg_holding_period_days']:.1f} days")
    
    print(f"\n🏆 BEST TRADE")
    print(f"{'─'*80}")
    best = report['best_trade']
    print(f"{best['token']}: {best['profit_pct']:+.2f}% ({best['profit_sol']:+.2f} SOL)")
    print(f"Entry: {best['entry_date']} → Exit: {best['exit_date']}")
    
    print(f"\n💔 WORST TRADE")
    print(f"{'─'*80}")
    worst = report['worst_trade']
    print(f"{worst['token']}: {worst['profit_pct']:+.2f}% ({worst['profit_sol']:+.2f} SOL)")
    print(f"Entry: {worst['entry_date']} → Exit: {worst['exit_date']}")
    
    print(f"\n📋 TRADE HISTORY (Last 10)")
    print(f"{'─'*80}")
    for trade in report['trades'][-10:]:
        emoji = "🟢" if trade['profit_loss_sol'] > 0 else "🔴"
        print(f"{emoji} {trade['token']:8s} | {trade['profit_loss_pct']:+6.1f}% | {trade['profit_loss_sol']:+6.2f} SOL | {trade['holding_days']}d | {trade['exit_reason']}")
    
    print(f"\n{'='*80}\n")


def main():
    # Load dataset
    print("📂 Loading backtest data...")
    with open('/app/backtest_data_30d_comprehensive.json', 'r') as f:
        dataset = json.load(f)
    
    # Configure backtest
    config = BacktestConfig(
        initial_capital_sol=10.0,
        max_positions=5,
        position_size_pct=0.15,
        entry_score_threshold=65.0,
        exit_score_threshold=40.0,
        take_profit_pct=30.0,
        stop_loss_pct=-15.0,
        max_holding_days=7
    )
    
    # Run backtest
    backtester = LifecycleBacktester(config)
    report = backtester.run_backtest(dataset)
    
    # Print report
    print_report(report)
    
    # Save report
    output_file = '/app/backtest_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"💾 Full report saved to: {output_file}\n")


if __name__ == "__main__":
    main()
