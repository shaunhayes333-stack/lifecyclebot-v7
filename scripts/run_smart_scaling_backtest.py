#!/usr/bin/env python3
"""
Lifecycle Bot v3.0 - WITH SMART TREASURY SCALING
Implements dynamic position sizing based on growing treasury
"""

import json
from datetime import datetime
from typing import Dict
from dataclasses import dataclass

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
    treasury_size: float  # NEW: Track treasury at time of trade

@dataclass
class SmartScalingConfig:
    """Configuration with smart treasury scaling"""
    initial_capital_sol: float = 10.0
    base_position_size_pct: float = 0.15  # Base 15% of current treasury
    
    # SMART SCALING: As treasury grows, increase position sizes
    treasury_scaling_enabled: bool = True
    max_position_size_pct: float = 0.20  # Cap at 20% per position
    
    # Treasury milestones for scaling
    scaling_tiers: dict = None
    
    # Risk management
    max_positions: int = 5
    entry_score_threshold: float = 68.0
    stop_loss_pct: float = -12.0  # Balanced stop loss
    take_profit_pct: float = 35.0  # Balanced take profit
    max_holding_days: int = 6
    
    # Partial profits (enhanced)
    partial_tp_1_pct: float = 18.0  # Take 25% at +18%
    partial_tp_1_size: float = 0.25
    partial_tp_2_pct: float = 28.0  # Take 35% at +28%
    partial_tp_2_size: float = 0.35
    
    def __post_init__(self):
        if self.scaling_tiers is None:
            # Define scaling tiers: treasury_size -> position_size_multiplier
            self.scaling_tiers = {
                10.0: 1.0,   # Initial: 1x (15%)
                15.0: 1.1,   # +50% profit: 1.1x (16.5%)
                20.0: 1.15,  # +100% profit: 1.15x (17.25%)
                30.0: 1.2,   # +200% profit: 1.2x (18%)
                50.0: 1.25,  # +400% profit: 1.25x (18.75%)
                100.0: 1.3,  # +900% profit: 1.3x (19.5%)
            }

class SmartScalingBacktester:
    def __init__(self, config: SmartScalingConfig):
        self.config = config
        self.treasury = config.initial_capital_sol  # Total capital (grows with profits)
        self.available_capital = config.initial_capital_sol  # Capital not in positions
        self.positions = {}
        self.closed_trades = []
        self.daily_portfolio_values = []
        self.logs = []
        self.partial_exits = {}
        
    def log(self, msg: str):
        self.logs.append(msg)
        print(msg)
    
    def get_position_size_multiplier(self) -> float:
        """
        SMART SCALING: Get position size multiplier based on current treasury
        """
        if not self.config.treasury_scaling_enabled:
            return 1.0
        
        # Find applicable tier
        multiplier = 1.0
        for threshold, mult in sorted(self.config.scaling_tiers.items()):
            if self.treasury >= threshold:
                multiplier = mult
        
        return multiplier
    
    def calculate_dynamic_position_size(self, token_data: Dict, day_idx: int) -> float:
        """
        Calculate position size with SMART SCALING based on treasury growth
        """
        # Base position size from current treasury
        base_size_sol = self.treasury * self.config.base_position_size_pct
        
        # Apply smart scaling multiplier
        multiplier = self.get_position_size_multiplier()
        scaled_size_sol = base_size_sol * multiplier
        
        # Calculate volatility adjustment
        ohlcv = token_data['historical_ohlcv']
        volatilities = []
        for i in range(max(0, day_idx-5), day_idx):
            if ohlcv[i]['low'] > 0:
                vol = ((ohlcv[i]['high'] - ohlcv[i]['low']) / ohlcv[i]['low']) * 100
                volatilities.append(vol)
        
        avg_vol = sum(volatilities) / len(volatilities) if volatilities else 10
        
        # Reduce for high volatility
        if avg_vol > 20:
            scaled_size_sol *= 0.8
        elif avg_vol > 15:
            scaled_size_sol *= 0.9
        
        # Cap at max position size
        max_size = self.treasury * self.config.max_position_size_pct
        final_size = min(scaled_size_sol, max_size)
        
        # Cap at available capital
        final_size = min(final_size, self.available_capital)
        
        return final_size
    
    def calculate_entry_score(self, token_data: Dict, day_idx: int) -> float:
        """Enhanced entry scoring"""
        if day_idx < 5:
            return 0.0
        
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        # 5-day momentum
        prev_5_close = ohlcv[day_idx - 5]['close']
        momentum = ((current['close'] - prev_5_close) / prev_5_close) * 100
        
        # Volume trend
        current_vol = current['volume']
        avg_vol = sum(ohlcv[i]['volume'] for i in range(max(0, day_idx-5), day_idx)) / 5
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
        
        # Price action
        price_action = ((current['close'] - current['open']) / current['open']) * 100 if current['open'] > 0 else 0
        
        # Trend consistency
        up_days = sum(1 for i in range(max(0, day_idx-5), day_idx) 
                      if ohlcv[i]['close'] > ohlcv[i]['open'])
        trend_strength = (up_days / 5) * 20
        
        # Score
        score = 50.0
        score += momentum * 1.5
        score += (vol_ratio - 1) * 15
        score += price_action * 2
        score += trend_strength
        
        return max(0, min(100, score))
    
    def calculate_exit_score(self, token_data: Dict, day_idx: int, entry_info: Dict):
        """Calculate exit signals with partial profits"""
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        current_price = current['close']
        entry_price = entry_info['entry_price']
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        token = entry_info.get('token', '')
        if token not in self.partial_exits:
            self.partial_exits[token] = {'tp1': False, 'tp2': False}
        
        # Partial TP checks
        if profit_pct >= self.config.partial_tp_1_pct and not self.partial_exits[token]['tp1']:
            return 100, f"Partial TP1 ({self.config.partial_tp_1_pct:.0f}%)"
        
        if profit_pct >= self.config.partial_tp_2_pct and not self.partial_exits[token]['tp2']:
            return 100, f"Partial TP2 ({self.config.partial_tp_2_pct:.0f}%)"
        
        # Full exit conditions
        if profit_pct >= self.config.take_profit_pct:
            return 100, "Full Take Profit"
        
        if profit_pct <= self.config.stop_loss_pct:
            return 100, "Stop Loss"
        
        # Max holding
        holding_days = day_idx - entry_info['entry_day_idx']
        if holding_days >= self.config.max_holding_days:
            return 85, "Max Holding Period"
        
        return 0, ""
    
    def open_position(self, token: str, token_data: Dict, day_idx: int):
        """Open position with smart treasury scaling"""
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        # Calculate dynamic size with treasury scaling
        position_size_sol = self.calculate_dynamic_position_size(token_data, day_idx)
        
        if position_size_sol < 0.01 or position_size_sol > self.available_capital:
            return
        
        entry_price = current['close']
        multiplier = self.get_position_size_multiplier()
        
        self.positions[token] = {
            'entry_date': current['date'],
            'entry_day_idx': day_idx,
            'entry_price': entry_price,
            'initial_position_size_sol': position_size_sol,
            'position_size_sol': position_size_sol,
            'token_data': token_data,
            'token': token,
            'treasury_at_entry': self.treasury,
            'multiplier_at_entry': multiplier
        }
        
        self.available_capital -= position_size_sol
        self.partial_exits[token] = {'tp1': False, 'tp2': False}
        
        self.log(f"🟢 ENTRY: {token} @ ${entry_price:.6f} | Size: {position_size_sol:.2f} SOL | "
                f"Treasury: {self.treasury:.1f} SOL (×{multiplier:.2f}) | Date: {current['date']}")
    
    def close_position(self, token: str, day_idx: int, reason: str, partial_pct: float = 1.0):
        """Close position and update treasury"""
        if token not in self.positions:
            return
        
        entry_info = self.positions[token]
        token_data = entry_info['token_data']
        ohlcv = token_data['historical_ohlcv']
        current = ohlcv[day_idx]
        
        exit_price = current['close']
        entry_price = entry_info['entry_price']
        position_size_sol = entry_info['position_size_sol']
        
        close_amount = position_size_sol * partial_pct
        
        # Calculate P&L
        profit_pct = ((exit_price - entry_price) / entry_price) * 100
        profit_loss_sol = close_amount * (profit_pct / 100)
        
        # Update available capital
        self.available_capital += close_amount + profit_loss_sol
        
        if partial_pct < 1.0:
            # Partial exit
            entry_info['position_size_sol'] -= close_amount
            emoji = "🟡"
            self.log(f"{emoji} PARTIAL EXIT: {token} ({partial_pct*100:.0f}%) @ ${exit_price:.6f} | "
                    f"P&L: {profit_loss_sol:+.2f} SOL ({profit_pct:+.1f}%) | Reason: {reason}")
            
            if 'TP1' in reason:
                self.partial_exits[token]['tp1'] = True
            elif 'TP2' in reason:
                self.partial_exits[token]['tp2'] = True
        else:
            # Full exit - update treasury
            old_treasury = self.treasury
            self.treasury = self.available_capital  # Update total treasury
            
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
                exit_reason=reason,
                treasury_size=entry_info['treasury_at_entry']
            )
            
            self.closed_trades.append(trade)
            del self.positions[token]
            if token in self.partial_exits:
                del self.partial_exits[token]
            
            emoji = "🟢" if profit_loss_sol > 0 else "🔴"
            treasury_change = self.treasury - old_treasury
            self.log(f"{emoji} FULL EXIT: {token} @ ${exit_price:.6f} | "
                    f"P&L: {profit_loss_sol:+.2f} SOL ({profit_pct:+.1f}%) | "
                    f"Treasury: {old_treasury:.1f} → {self.treasury:.1f} SOL ({treasury_change:+.1f}) | "
                    f"Reason: {reason}")
    
    def run_backtest(self, dataset: Dict) -> Dict:
        """Run backtest with smart scaling"""
        tokens = dataset['tokens']
        num_days = dataset['metadata']['period_days']
        
        self.log(f"\n{'='*80}")
        self.log(f"LIFECYCLE BOT v3.0 - SMART TREASURY SCALING")
        self.log(f"{'='*80}")
        self.log(f"Feature: Position sizes scale up as treasury grows")
        self.log(f"Initial: {self.config.base_position_size_pct*100:.0f}% | Max: {self.config.max_position_size_pct*100:.0f}%")
        self.log(f"{'='*80}\n")
        
        # Iterate through each day
        for day_idx in range(num_days):
            # Check exits
            for token_symbol in list(self.positions.keys()):
                exit_score, reason = self.calculate_exit_score(
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
            
            # Check entries
            if len(self.positions) < self.config.max_positions:
                opportunities = []
                for token in tokens:
                    if token['symbol'] in self.positions:
                        continue
                    
                    entry_score = self.calculate_entry_score(token, day_idx)
                    if entry_score >= self.config.entry_score_threshold:
                        opportunities.append((token['symbol'], entry_score, token))
                
                opportunities.sort(key=lambda x: x[1], reverse=True)
                
                for symbol, score, token_data in opportunities[:self.config.max_positions - len(self.positions)]:
                    self.open_position(symbol, token_data, day_idx)
            
            # Track portfolio value
            portfolio_value = self.available_capital
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
                'value': portfolio_value,
                'treasury': self.treasury
            })
        
        # Close remaining
        for token_symbol in list(self.positions.keys()):
            self.close_position(token_symbol, num_days - 1, "End of Period", 1.0)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate comprehensive report"""
        total_trades = len(self.closed_trades)
        if total_trades == 0:
            return {"error": "No trades"}
        
        winning_trades = [t for t in self.closed_trades if t.profit_loss_sol > 0]
        losing_trades = [t for t in self.closed_trades if t.profit_loss_sol <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        total_profit = sum(t.profit_loss_sol for t in winning_trades)
        total_loss = sum(t.profit_loss_sol for t in losing_trades)
        net_profit = total_profit + total_loss
        
        avg_win = total_profit / len(winning_trades) if winning_trades else 0
        avg_loss = total_loss / len(losing_trades) if losing_trades else 0
        
        final_capital = self.treasury
        roi = ((final_capital - self.config.initial_capital_sol) / self.config.initial_capital_sol) * 100
        
        best_trade = max(self.closed_trades, key=lambda t: t.profit_loss_pct)
        worst_trade = min(self.closed_trades, key=lambda t: t.profit_loss_pct)
        
        avg_holding = sum(t.holding_period_days for t in self.closed_trades) / total_trades
        
        # Calculate treasury growth rate
        treasury_growth = []
        for i, trade in enumerate(self.closed_trades):
            if i > 0:
                prev_treasury = self.closed_trades[i-1].treasury_size
                growth = ((trade.treasury_size - prev_treasury) / prev_treasury) * 100
                treasury_growth.append(growth)
        
        avg_treasury_growth = sum(treasury_growth) / len(treasury_growth) if treasury_growth else 0
        
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
                'treasury_compounding': True,
                'avg_treasury_growth_per_trade_pct': avg_treasury_growth,
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
            'scaling_impact': {
                'enabled': self.config.treasury_scaling_enabled,
                'scaling_tiers': self.config.scaling_tiers,
                'final_position_size_multiplier': self.get_position_size_multiplier(),
            }
        }


def main():
    with open('/app/backtest_data_30d_comprehensive.json', 'r') as f:
        dataset = json.load(f)
    
    # Load previous reports for comparison
    try:
        with open('/app/backtest_report.json', 'r') as f:
            v1_report = json.load(f)
    except:
        v1_report = None
    
    # Run smart scaling backtest
    config = SmartScalingConfig()
    backtester = SmartScalingBacktester(config)
    v3_report = backtester.run_backtest(dataset)
    
    # Print comparison
    if v1_report:
        print(f"\n{'='*80}")
        print("TREASURY SCALING IMPACT")
        print(f"{'='*80}\n")
        print(f"{'Version':<20} | {'ROI':>12} | {'Final Capital':>15} | {'Trades':>8}")
        print(f"{'-'*80}")
        print(f"{'v1.0 (No Scaling)':<20} | {v1_report['summary']['roi_pct']:>11.2f}% | {v1_report['summary']['final_capital_sol']:>13.2f} SOL | {v1_report['summary']['total_trades']:>8}")
        print(f"{'v3.0 (Smart Scaling)':<20} | {v3_report['summary']['roi_pct']:>11.2f}% | {v3_report['summary']['final_capital_sol']:>13.2f} SOL | {v3_report['summary']['total_trades']:>8}")
        improvement = ((v3_report['summary']['roi_pct'] - v1_report['summary']['roi_pct']) / v1_report['summary']['roi_pct']) * 100
        print(f"\n🚀 Improvement with Smart Scaling: +{improvement:.1f}%")
        print(f"{'='*80}\n")
    
    # Save report
    with open('/app/backtest_report_v3_smart_scaling.json', 'w') as f:
        json.dump(v3_report, f, indent=2)
    
    print(f"💾 Smart Scaling report saved to: /app/backtest_report_v3_smart_scaling.json\n")


if __name__ == "__main__":
    main()
