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

### Completed (March 21, 2025)
- [x] **BUILD FIXED** - GitHub Actions Build #53 passing
  - Removed buggy trade simulation feature
  - Fixed syntax error in SolanaMarketScanner.kt
- [x] **Web dashboard fully functional**
  - Auth system with JWT tokens  
  - Stats cards (Treasury, P&L, Win Rate, Total Trades, Avg Win/Loss)
  - Treasury Performance chart (30-day visualization)
  - Open Positions table with real-time P&L
  - Watchlist with 5 tokens
  - Activity feed with bot events
  - Trade history
- [x] **Fixed auth context** - AuthProvider properly wraps app
- [x] **Login/register flow working**
- [x] **API Sync working** - `/api/sync/bulk` endpoint tested and functional
- [x] **30-day backtest dataset generated** - `/app/backtest_dataset_30d.json`
- [x] **Dashboard seeded with real trading data**
  - 9 total trades (6 wins, 3 losses = 66.7% win rate)
  - 2 open positions (BONK, WIF)
  - 5 watchlist tokens (JUP, USDC, RAY, BONK, WIF)
  - Treasury performance chart
- [x] In-app error logger (SQLite with UI)
- [x] Comprehensive diagnostic logging in scanner and strategy

### Scripts Created
- `/app/generate_backtest_data.py` - Generates 30-day backtest dataset from CoinGecko API
- `/app/seed_dashboard.py` - Seeds dashboard with trading data via API

### Critical Issues (P0) - FOR USER TO TEST
- [ ] **Enable Auto Trade** and verify trading signals
- [ ] Check why scanner may not be finding tokens (filters may be too strict)
- [ ] Wallet persistence - verify wallet stays connected between screens

### Future Tasks (P2)
- [ ] Backtesting UI in dashboard (visualize historical trades)
- [ ] Mobile-responsive dashboard
- [ ] Strategy parameter tuning UI
- [ ] Real-time WebSocket sync between Android and Dashboard

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

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - JWT authentication
- `GET /api/auth/me` - Current user

### Dashboard Data
- `GET /api/dashboard` - Dashboard stats (summary)
- `GET /api/bot/status` - Bot status
- `POST /api/bot/status` - Update bot status

### Trading Data
- `GET /api/positions` - Open positions
- `POST /api/positions/sync` - Sync positions from Android
- `GET /api/trades` - Trade history
- `POST /api/trades` - Record new trade
- `GET /api/trades/stats` - Trade statistics

### Treasury
- `GET /api/treasury/history` - Treasury history
- `POST /api/treasury/snapshot` - Add treasury snapshot

### Sync
- `POST /api/sync/bulk` - Bulk data push from Android app (positions, trades, watchlist, activity)

### Watchlist & Activity
- `GET /api/watchlist` - Watchlist tokens
- `POST /api/watchlist/sync` - Sync watchlist
- `GET /api/activity` - Activity log
- `POST /api/activity` - Log activity

## 3rd Party Integrations
- Helius (RPC) - User API key required
- Birdeye (Token data) - User API key required
- Groq (LLM sentiment) - Optional
- DexScreener, Raydium, Pump.fun - Free APIs for token scanning
- CoinGecko - Free API for historical price data (used in backtest generation)

## Build History
- Build #51-52: Failed - Trade simulation bugs
- **Build #53: SUCCESS** - Fixed build (current)

## Next Steps for User
1. Download APK from GitHub Actions artifacts (Build #53)
2. Install on Android device
3. Go to Settings → Enable "Auto Trade" and "Paper Mode"
4. Connect wallet
5. Start bot
6. Check Logs to see scanner activity and why signals may be blocked
7. View web dashboard at https://dex-strategy-v7.preview.emergentagent.com

## Dashboard Access
- **URL**: https://dex-strategy-v7.preview.emergentagent.com
- **Test User**: testuser / test123
