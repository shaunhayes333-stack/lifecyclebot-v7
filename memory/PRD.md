# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
Build a sophisticated Solana trading bot Android application that autonomously scans, learns, and trades.

## Core Functionality - AUTONOMOUS OPERATION

The bot is designed to be fully autonomous:

### 1. Scanner (SolanaMarketScanner.kt)
- Scans DexScreener, Raydium, Birdeye, Pump.fun for new tokens
- Filters by liquidity, age, market cap, volume
- Auto-adds promising tokens to watchlist
- Runs every 5 seconds by default

### 2. Self-Learning Engine (BotBrain.kt) - 3 Layers

**Layer 1 - Statistical Learning (every 20 trades)**
- Analyzes win rates per signal combination
- Adjusts entry/exit thresholds automatically
- Tracks phase performance (pumping, range, cooling, etc.)
- Records bad patterns to avoid

**Layer 2 - LLM Analysis (every 50 trades)**
- Uses Groq LLM for deep pattern recognition
- Identifies what's working vs failing
- Suggests parameter adjustments
- Requires Groq API key

**Layer 3 - Regime Detection (real-time)**
- Classifies market: BULL_HOT, BULL, NEUTRAL, BEAR, BEAR_COLD, DANGER
- Adjusts position sizing based on conditions
- Reduces size in dangerous markets, increases in hot markets

### 3. Shadow Learning Engine (ShadowLearningEngine.kt)
- Runs parallel simulated trades with different parameters
- Tests aggressive vs conservative strategies simultaneously
- Compares variants to live trading
- Auto-generates insights: "Variant A would have made +15% more"

### 4. Strategy (LifecycleStrategy.kt)
- Token lifecycle-based trading (launch snipe vs range trade)
- EMA fan detection for trend following
- Volume, pressure, momentum scoring
- Multi-timeframe analysis (1m, 5m, 15m)
- Bonding curve tracking for pump.fun tokens
- Whale detection and smart money tracking

## Current Configuration (BotConfig.kt)

| Setting | Default | Description |
|---------|---------|-------------|
| **`autoTrade`** | **true** | Bot trades automatically |
| **`autoAddNewTokens`** | **true** | Auto-scan new launches |
| `paperMode` | true | Simulate without real money |
| `fullMarketScanEnabled` | true | Scanner active |
| `scanIntervalSecs` | 5 | Scan frequency |
| `minLiquidityUsd` | 3000 | Min liquidity filter |
| `minDiscoveryScore` | 25 | Min score to watchlist |

## Build Status
- **Build #53**: SUCCESS - Fixed compilation errors
- **Build #54**: SUCCESS - Enabled autonomous mode

## Architecture

### Mobile App (Android/Kotlin)
```
/lifecycle_apk/app/src/main/kotlin/com/lifecyclebot/
├── engine/
│   ├── BotService.kt          # Main loop
│   ├── SolanaMarketScanner.kt # Token discovery
│   ├── LifecycleStrategy.kt   # Trading signals
│   ├── Executor.kt            # Trade execution
│   ├── BotBrain.kt            # Self-learning
│   ├── ShadowLearningEngine.kt # Parallel simulations
│   ├── WalletManager.kt       # Wallet (singleton)
│   └── TreasuryManager.kt     # Profit management
├── network/
│   ├── DexscreenerApi.kt
│   ├── BirdeyeApi.kt
│   └── JupiterApi.kt
└── ui/
    ├── MainActivity.kt
    └── ErrorLogActivity.kt
```

### Web Dashboard (React + FastAPI)
- URL: https://dex-strategy-v7.preview.emergentagent.com
- Features: Treasury chart, positions, watchlist, activity, trade history
- API: `/api/sync/bulk` for Android sync

## 3rd Party Integrations
- **Helius** - RPC (user key required)
- **Birdeye** - Token data (user key required)
- **Groq** - LLM learning (optional, for Layer 2)
- **Jupiter** - DEX aggregator for swaps
- **DexScreener, Raydium, Pump.fun** - Free APIs

## How the Bot Learns

1. **On every trade**: Records entry phase, EMA fan, MTF trend, source, score, hold time, P&L
2. **Every 20 trades**: Statistical analysis identifies winning/losing patterns
3. **Every 50 trades**: LLM deep analysis (if Groq key provided)
4. **Continuously**: Shadow engine tests parameter variants
5. **Real-time**: Regime detection adjusts to market conditions

### Bad Behaviour Registry
- Patterns with <40% win rate get flagged
- Confirmed bad patterns get suppressed (-45 pts from entry score)
- Severe patterns get near-blocked (-80 pts)
- LLM cannot override hard-learned bad patterns

## User Setup
1. Download APK from GitHub Actions (Build #54+)
2. Install on Android
3. Connect Solana wallet
4. (Optional) Add API keys: Helius, Birdeye, Groq
5. Start bot - it will scan, learn, and trade automatically

## Next Steps
- [ ] Add backtesting UI to dashboard
- [ ] Implement WebSocket real-time sync
- [ ] Mobile-responsive dashboard
