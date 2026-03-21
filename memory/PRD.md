# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
Build a sophisticated Solana trading bot Android application with:
1. Clone and fix the GitHub repository `https://github.com/shaunhayes333-stack/lifecycle-bot`
2. Debug and fix all compilation errors in the Android (Kotlin) application
3. Ensure GitHub Actions build passes successfully
4. Implement continuous background operation on phone
5. Generate test dataset for backtesting
6. Build web dashboard to visualize bot activity
7. Integrate Android app with web dashboard

## CRITICAL FINDINGS - Why Bot Hasn't Traded

### Root Cause Analysis
After analyzing the codebase, the primary reasons the bot has not executed a single trade:

1. **`autoTrade` defaults to `false`** (BotConfig.kt line 14)
   - Even when the bot is "running", it won't execute trades unless this is enabled
   - User MUST enable "Auto Trade" in the app's settings

2. **Strategy requires 3+ candles** (LifecycleStrategy.kt line 72-74)
   - New tokens without historical data return "bootstrap" phase with "WAIT" signal
   - Need at least 3 data points before any BUY signal can be generated

3. **Entry threshold is high** 
   - Launch snipe mode: 42-65 entry score required depending on phase
   - Range trade mode: 38-50 entry score required
   - Many tokens may never reach these thresholds

### Recommendations for User
1. **Enable Auto Trade** in app settings
2. **Enable Paper Mode** first to test without real money
3. **Check Logs** - the in-app error logger shows exactly why trades aren't happening
4. **Lower thresholds** if needed (exitScoreThreshold, minDiscoveryScore)

## Current Architecture

### Mobile App (Android/Kotlin)
```
/lifecycle_bot/lifecycle_apk/
├── app/src/main/kotlin/com/lifecyclebot/
│   ├── engine/
│   │   ├── BotService.kt          # Main service lifecycle
│   │   ├── SolanaMarketScanner.kt # Token discovery (DexScreener, Raydium, Birdeye)
│   │   ├── LifecycleStrategy.kt   # Trading strategy (1700+ lines of logic)
│   │   ├── Executor.kt            # Trade execution (1000+ lines)
│   │   ├── WalletManager.kt       # Wallet connection (singleton)
│   │   ├── TreasuryManager.kt     # Profit locking
│   │   └── ErrorLogger.kt         # SQLite error logging
│   ├── network/
│   │   ├── DexscreenerApi.kt      # Market data
│   │   └── BirdeyeApi.kt          # Token data
│   └── ui/
│       ├── MainActivity.kt        # Main screen
│       └── ErrorLogActivity.kt    # Error log viewer
```

### Web Dashboard (React + FastAPI)
```
/backend/server.py       # FastAPI with JWT auth, MongoDB
/frontend/src/
├── App.js               # AuthProvider context, routing
├── pages/
│   ├── LoginPage.jsx    # Authentication (login/register)
│   └── DashboardPage.jsx # Main dashboard
└── components/dashboard/ # Dashboard components
```

## What's Been Implemented

### Completed (March 2025)
- [x] **BUILD FIXED** - GitHub Actions Build #53 passing
  - Removed buggy trade simulation feature
  - Fixed syntax error in SolanaMarketScanner.kt
- [x] Web dashboard fully functional
  - Auth system with JWT tokens  
  - Stats cards, Treasury chart, Positions, Watchlist, Activity feed, Trade history
- [x] Fixed auth context - AuthProvider now wraps app correctly
- [x] Login/register flow working
- [x] In-app error logger (SQLite with UI)
- [x] Comprehensive diagnostic logging in scanner and strategy

### Critical Issues (P0) - FOR USER TO TEST
- [ ] **Enable Auto Trade** and verify trading signals
- [ ] Check why scanner may not be finding tokens (filters may be too strict)
- [ ] Wallet persistence - verify wallet stays connected between screens

### Medium Priority (P1)
- [ ] Android-Dashboard real-time sync (API ready at `/api/sync/bulk`)
- [ ] Watchlist token variety

### Future Tasks (P2)
- [ ] Backtesting UI in dashboard
- [ ] Mobile-responsive dashboard
- [ ] Strategy parameter tuning
- [ ] 30-day test dataset generation

## Key Configuration Values (BotConfig.kt)

| Setting | Default | Description |
|---------|---------|-------------|
| `autoTrade` | **false** | Must enable to execute trades |
| `paperMode` | true | Simulate trades without real money |
| `minLiquidityUsd` | 3000 | Min liquidity for scanner |
| `minDiscoveryScore` | 25 | Min score to add token to watchlist |
| `exitScoreThreshold` | 58 | Score to trigger exit |
| `fullMarketScanEnabled` | true | Enable scanner |
| `scanIntervalSecs` | 5 | Scanner poll interval |

## API Endpoints
- POST `/api/auth/register` - User registration
- POST `/api/auth/login` - JWT authentication
- GET `/api/dashboard` - Dashboard stats
- POST `/api/sync/bulk` - Bulk data push from Android app
- GET `/api/positions` - Open positions
- GET `/api/trades` - Trade history
- GET `/api/watchlist` - Watchlist
- GET `/api/treasury/history` - Treasury history

## 3rd Party Integrations
- Helius (RPC) - User API key required
- Birdeye (Token data) - User API key required
- Groq (LLM sentiment) - Optional
- DexScreener, Raydium, Pump.fun - Free APIs for token scanning

## Build History
- Build #51-52: Failed - Trade simulation bugs
- **Build #53: SUCCESS** - Fixed build

## Next Steps for User
1. Download APK from GitHub Actions artifacts
2. Install on Android device
3. Go to Settings → Enable "Auto Trade" and "Paper Mode"
4. Connect wallet
5. Start bot
6. Check Logs to see scanner activity and why signals may be blocked
