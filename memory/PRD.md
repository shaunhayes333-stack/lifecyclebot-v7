# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
Build a sophisticated Solana trading bot Android application that autonomously scans, learns, and trades.

## BUILD STATUS
- **Build #53**: SUCCESS - Fixed compilation errors
- **Build #54**: SUCCESS - Enabled autonomous mode
- **Build #55**: SUCCESS - Fixed DexScreener API endpoints

## SCANNER FIX (Build #55)

### Problem
The scanner was using broken DexScreener API endpoints:
```
https://api.dexscreener.com/latest/dex/pairs/solana/raydium
```
This endpoint returns `{"pairs": null}` - empty data.

### Solution
Changed to use the search API which works:
```
https://api.dexscreener.com/latest/dex/search?q=solana  (returns 30 pairs)
https://api.dexscreener.com/latest/dex/search?q=pump     (finds pump.fun tokens)
```

### Files Changed
- `SolanaMarketScanner.kt`:
  - `runTestScan()` - Fixed to use search API
  - `scanDexGainers()` - Fixed to use search API  
  - `scanPumpGraduates()` - Fixed to use search API

## Core Functionality - AUTONOMOUS OPERATION

The bot is designed to be fully autonomous:

### 1. Scanner (SolanaMarketScanner.kt)
- Scans DexScreener (search API), Birdeye, Pump.fun for new tokens
- Filters by liquidity (>$3K), volume, age
- Auto-adds promising tokens to watchlist
- Runs every 5 seconds by default

### 2. Self-Learning Engine (BotBrain.kt) - 3 Layers

**Layer 1 - Statistical Learning (every 20 trades)**
- Analyzes win rates per signal combination
- Adjusts entry/exit thresholds automatically
- Tracks phase performance (pumping, range, cooling)
- Records bad patterns to avoid

**Layer 2 - LLM Analysis (every 50 trades)**
- Uses Groq LLM for deep pattern recognition
- Identifies what's working vs failing
- Suggests parameter adjustments
- Requires Groq API key

**Layer 3 - Regime Detection (real-time)**
- Classifies market: BULL_HOT, BULL, NEUTRAL, BEAR, BEAR_COLD, DANGER
- Adjusts position sizing based on conditions

### 3. Shadow Learning Engine (ShadowLearningEngine.kt)
- Runs parallel simulated trades with different parameters
- Tests 11 strategy variants simultaneously
- Compares to live trading, generates insights

## Current Configuration (BotConfig.kt)

| Setting | Default | Description |
|---------|---------|-------------|
| **`autoTrade`** | **true** | Bot trades automatically |
| **`autoAddNewTokens`** | **true** | Auto-scan new launches |
| `paperMode` | true | Simulate without real money |
| `fullMarketScanEnabled` | true | Scanner active |
| `scanIntervalSecs` | 5 | Scan frequency |
| `minLiquidityUsd` | 3000 | Min liquidity filter |

## Architecture

### Mobile App (Android/Kotlin)
```
/lifecycle_apk/app/src/main/kotlin/com/lifecyclebot/
├── engine/
│   ├── BotService.kt          # Main loop
│   ├── SolanaMarketScanner.kt # Token discovery (FIXED)
│   ├── LifecycleStrategy.kt   # Trading signals
│   ├── Executor.kt            # Trade execution
│   ├── BotBrain.kt            # Self-learning
│   └── ShadowLearningEngine.kt # Parallel simulations
├── network/
│   ├── DexscreenerApi.kt
│   └── BirdeyeApi.kt
└── ui/
    └── MainActivity.kt
```

### Web Dashboard
- URL: https://dex-strategy-v7.preview.emergentagent.com
- Login: testuser / test123

## 3rd Party APIs Used
- **DexScreener** - Token search (FREE, `/latest/dex/search?q=...`)
- **Birdeye** - Token data (API key required)
- **Helius** - RPC (API key required)
- **Groq** - LLM learning (optional)
- **Jupiter** - DEX aggregator for swaps

## User Setup
1. Download APK from GitHub Actions (Build #55)
2. Install on Android
3. Connect Solana wallet
4. (Optional) Add API keys: Helius, Birdeye, Groq
5. Start bot - it will scan, learn, and trade automatically

## What the Scanner Should Now Find
With the fixed API:
- Tokens with >$3K liquidity on Solana
- New pump.fun launches
- Pump.fun graduates (migrated to Raydium)
- Trending tokens with high volume
