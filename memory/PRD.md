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
│   │   ├── BotService.kt          # Main service lifecycle (ENHANCED LOGGING)
│   │   ├── Executor.kt            # Trade execution
│   │   ├── SecurityGuard.kt       # Safety checks
│   │   ├── TreasuryManager.kt     # Profit locking
│   │   ├── WalletManager.kt       # Wallet connection
│   │   ├── ErrorLogger.kt         # SQLite error logging
│   │   ├── TokenSafetyChecker.kt  # Token validation
│   │   ├── AutoModeEngine.kt      # Trading mode switching
│   │   ├── SolanaMarketScanner.kt # Token discovery (ENHANCED LOGGING)
│   │   ├── LifecycleStrategy.kt   # Trading strategy
│   │   └── BotBrain.kt            # Self-learning engine
│   ├── network/
│   │   ├── SolanaWallet.kt        # Solana RPC
│   │   ├── JupiterApi.kt          # DEX aggregator
│   │   └── DexscreenerApi.kt      # Market data
│   ├── ui/
│   │   ├── MainActivity.kt        # Main screen
│   │   ├── ErrorLogActivity.kt    # Error log viewer
│   │   └── ...
│   └── data/
```

### Web Dashboard (React + FastAPI)
```
/backend/server.py       # FastAPI with JWT auth
/frontend/src/
├── pages/
│   ├── LoginPage.jsx    # Authentication
│   └── DashboardPage.jsx # Main dashboard
└── components/dashboard/ # Dashboard components
```

## What's Been Implemented

### ✅ Completed (Dec 2024)
- [x] Fixed 80+ Kotlin compilation errors
- [x] GitHub Actions CI/CD pipeline working
- [x] Web dashboard with auth, charts, tables
- [x] Treasury lock blocking fix
- [x] UTC pause logic improvement
- [x] Watchlist token refresh optimization
- [x] Major token whitelist (SOL, USDC, BONK, JUP, etc.)
- [x] In-app error logger (SQLite database with UI)
- [x] Wallet balance display fix (labels corrected)
- [x] RPC URL input field added to wallet screen
- [x] RPC fallback endpoints for connection stability
- [x] **Build #33: Comprehensive diagnostic logging** for scanner and trading loop

### 🔴 Critical Issues Being Investigated (P0)
- [ ] Core AI trading logic appears "stuck" - needs user verification with new logging
- [ ] Market scanner may be filtering out tokens too aggressively

### 🟡 Medium Priority (P1)
- [ ] Android-Dashboard sync integration
- [ ] Watchlist token variety - verify scanner sources working

### 🔵 Future Tasks (P2)
- [ ] Backtesting UI in dashboard
- [ ] Mobile-responsive dashboard
- [ ] Strategy parameter tuning

## Key Technical Decisions

### Build #33: Diagnostic Logging Enhancement
Added comprehensive logging to diagnose why trading logic appears inactive:
- **SolanaMarketScanner.passesFilter()**: Logs WHY tokens are rejected (liquidity, score, etc.)
- **Bot loop**: Logs every 5 loops with watchlist size and scanner status
- **onTokenFound callback**: Logs each token discovery and addition attempt
- **Strategy evaluation**: Logs BUY signals and high entry scores

All logs visible in the in-app "Logs" screen for user debugging.

### Error Logger (Build #18)
- SQLite database stores logs persistently
- 5 severity levels: DEBUG, INFO, WARN, ERROR, CRASH
- Component tagging for filtering
- Stack trace capture on crashes
- UI accessible via "Logs" button

### Major Token Whitelist (Build #17)
Verified mints that bypass ALL safety checks:
- So11111111111111111111111111111111111111112 (SOL wrapped)
- EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v (USDC)
- DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263 (BONK)
- JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN (JUP)
- Plus: RAY, ORCA, mSOL, PYTH, JITO, RENDER, USDT, WIF

## Database Schema (MongoDB)
- `users`: Authentication
- `trades`: Trade history
- `bot_status`: Current bot state
- `treasury_snapshots`: Balance tracking
- `activity_logs`: Event logging

## API Endpoints
- POST `/api/auth/register` - User registration
- POST `/api/auth/login` - JWT authentication
- GET `/api/data/pnl` - P&L data
- GET `/api/trades` - Trade history
- POST `/api/sync/bulk` - Android data sync

## 3rd Party Integrations
- Helius (RPC) - User API key required
- Birdeye (Token data) - User API key required
- Groq (LLM sentiment) - User API key required
- CoinGecko (Market data) - Free tier
- Telegram (Notifications) - User token required
- DexScreener, Raydium, Pump.fun - Token scanning

## Build History
- Build #15: Treasury lock fix
- Build #16: Indentation fix
- Build #17: Major token whitelist + crash logging
- Build #18: In-app Error Logger with SQLite
- Build #30: Restore scanner functionality
- Build #31: RPC error logging + new endpoints
- Build #32: Wallet balance display fix
- **Build #33: Comprehensive diagnostic logging for scanner + trading loop**
