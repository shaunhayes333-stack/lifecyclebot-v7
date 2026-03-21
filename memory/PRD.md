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

## Current Architecture

### Mobile App (Android/Kotlin)
```
/lifecycle_bot/lifecycle_apk/
├── app/src/main/kotlin/com/lifecyclebot/
│   ├── engine/
│   │   ├── BotService.kt          # Main service lifecycle
│   │   ├── SolanaMarketScanner.kt # Token discovery
│   │   ├── LifecycleStrategy.kt   # Trading strategy
│   │   ├── Executor.kt            # Trade execution
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
    ├── StatsCards.jsx
    ├── PnLChart.jsx
    ├── PositionsTable.jsx
    ├── TradeHistory.jsx
    ├── ActivityFeed.jsx
    ├── Watchlist.jsx
    └── Header.jsx
```

## What's Been Implemented

### Completed (March 2025)
- [x] **BUILD FIXED** - GitHub Actions Build #53 passing
  - Removed buggy trade simulation feature
  - Fixed syntax error (duplicate brace) in SolanaMarketScanner.kt
  - Removed simulation UI from MainActivity.kt
- [x] Fixed 80+ Kotlin compilation errors
- [x] Web dashboard fully functional
  - Auth system with JWT tokens
  - Stats cards (Treasury, P&L, Win Rate, Total Trades)
  - Treasury Performance chart
  - Open Positions table
  - Watchlist display
  - Activity feed
  - Trade history
- [x] Fixed auth context issue - AuthProvider now wraps app correctly
- [x] In-app error logger (SQLite database with UI)
- [x] Major token whitelist (SOL, USDC, BONK, JUP, etc.)
- [x] Comprehensive diagnostic logging

### Critical Issues (P0) - STILL PENDING
- [ ] Core AI trading logic appears "stuck" - needs user verification with new logging
- [ ] Market scanner may be filtering out tokens too aggressively
- [ ] Wallet persistence issues (wallet shows connected but balance is $0)

### Medium Priority (P1)
- [ ] Android-Dashboard sync integration (data currently mocked)
- [ ] Watchlist token variety - verify scanner sources working

### Future Tasks (P2)
- [ ] Backtesting UI in dashboard
- [ ] Mobile-responsive dashboard
- [ ] Strategy parameter tuning
- [ ] Generate 30-day test dataset

## Database Schema (MongoDB)
- `users`: Authentication
- `sessions`: JWT tokens
- `trades`: Trade history
- `bot_status`: Current bot state
- `positions`: Open positions
- `treasury_history`: Balance tracking
- `treasury_current`: Current treasury
- `activity_logs`: Event logging
- `watchlist`: Watched tokens

## API Endpoints
- POST `/api/auth/register` - User registration
- POST `/api/auth/login` - JWT authentication
- GET `/api/auth/me` - Current user
- GET `/api/bot/status` - Bot status
- POST `/api/bot/status` - Update bot status
- GET `/api/treasury/history` - Treasury history
- POST `/api/treasury/snapshot` - Add treasury snapshot
- GET `/api/positions` - Open positions
- POST `/api/positions/sync` - Sync positions
- GET `/api/trades` - Trade history
- POST `/api/trades` - Record trade
- GET `/api/trades/stats` - Trade statistics
- GET `/api/activity` - Activity log
- POST `/api/activity` - Log activity
- GET `/api/watchlist` - Watchlist
- POST `/api/watchlist/sync` - Sync watchlist
- GET `/api/dashboard` - Dashboard stats
- POST `/api/sync/bulk` - Bulk data push (for Android app)

## 3rd Party Integrations
- Helius (RPC) - User API key required
- Birdeye (Token data) - User API key required
- Groq (LLM sentiment) - User API key required
- CoinGecko (Market data) - Free tier
- Telegram (Notifications) - User token required
- DexScreener, Raydium, Pump.fun - Token scanning

## Build History
- Build #51: Failed - Trade simulation bugs
- Build #52: Failed - Trade simulation bugs
- **Build #53: SUCCESS** - Fixed build (simulation removed, syntax fixed)

## Next Steps
1. Verify wallet persistence on Android app
2. Test market scanner with real API data
3. Verify trading logic generates signals
4. Implement Android-Dashboard real-time sync
