# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
Build a sophisticated Solana trading bot Android application that autonomously scans, learns, and trades.

## BUILD STATUS
- **Build #53**: SUCCESS - Fixed compilation errors
- **Build #54**: SUCCESS - Enabled autonomous mode
- **Build #55**: SUCCESS - Fixed DexScreener API endpoints
- **Build #56**: SUCCESS - Paper mode now uses wallet balance

## LATEST FIX - Paper Trading with Real Balance (Build #56)

### Problem
Paper mode wasn't feeding the learning system because:
1. Without wallet connection, `walletSol` was 0
2. Position sizing returned 0 (no balance = no trades)
3. Learning engine got no data

### Solution
- Added `paperWalletSol` to track simulated balance
- Paper wallet syncs with real wallet balance on first connection
- Paper buys deduct from paper balance
- Paper sells add proceeds back
- All trade decisions now use effective balance

### How Learning Works Now
1. **Paper buy** → Deducts SOL from paper wallet
2. **Paper sell** → Adds proceeds, calculates P&L
3. **BotBrain** receives trade data:
   - Bad observations for losing trades
   - Good observations for winning trades
4. **Every 20 trades** → Statistical learning adjusts thresholds
5. **Every 50 trades** → LLM analysis (if Groq key set)

## Core Functionality - AUTONOMOUS OPERATION

### 1. Scanner (SolanaMarketScanner.kt)
- Uses DexScreener search API (`/latest/dex/search?q=solana`)
- Filters: chainId=solana, >$3K liquidity
- Detects pump.fun tokens and graduates
- Auto-adds to watchlist

### 2. Self-Learning Engine (BotBrain.kt)
**Layer 1 - Statistical (every 20 trades)**
- Win rate analysis per signal combo
- Auto-adjusts thresholds
- Bad behaviour registry

**Layer 2 - LLM (every 50 trades)**
- Groq deep analysis
- Pattern recognition

**Layer 3 - Regime Detection**
- Market classification: BULL_HOT → DANGER
- Adjusts position sizing

### 3. Shadow Learning (ShadowLearningEngine.kt)
- 11 parallel strategy variants
- Compares to live trading
- Generates optimization insights

## Configuration (BotConfig.kt)

| Setting | Default | Description |
|---------|---------|-------------|
| `autoTrade` | **true** | Autonomous trading |
| `autoAddNewTokens` | **true** | Auto-scan launches |
| `paperMode` | true | Simulate first |
| `fullMarketScanEnabled` | true | Scanner on |
| `minLiquidityUsd` | 3000 | Min liquidity |

## Key Files Changed

### Build #56 Changes
- `Models.kt`: Added `paperWalletSol`, `paperWalletInitialized`, `getEffectiveBalance()`
- `Executor.kt`: Added `onPaperBalanceChange` callback, updates paper balance on trades
- `BotService.kt`: Syncs paper wallet, uses effective balance for all trading

## 3rd Party APIs
- **DexScreener**: `/latest/dex/search?q=solana` (works)
- **Birdeye**: Token data (API key required)
- **Helius**: RPC (API key required)
- **Groq**: LLM learning (optional)

## User Flow
1. Download APK from Build #56
2. Install, connect wallet
3. Bot syncs paper wallet with real balance
4. Scanner finds tokens → adds to watchlist
5. Strategy evaluates → generates signals
6. Paper trades execute → learning engine fed
7. BotBrain adjusts → strategy improves

## Dashboard
- URL: https://dex-strategy-v7.preview.emergentagent.com
- Login: testuser / test123
