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
│   ├── engine/          # Core trading logic
│   │   ├── BotService.kt       # Main service lifecycle
│   │   ├── Executor.kt         # Trade execution
│   │   ├── SecurityGuard.kt    # Safety checks (FIXED)
│   │   ├── TreasuryManager.kt  # Profit locking (FIXED)
│   │   ├── WalletManager.kt    # Wallet connection
│   │   ├── AutoModeEngine.kt   # Trading mode switching
│   │   ├── SolanaMarketScanner.kt # Token discovery
│   │   └── BotBrain.kt         # Self-learning engine
│   ├── network/         # API clients
│   │   ├── SolanaWallet.kt     # Solana RPC
│   │   ├── JupiterApi.kt       # DEX aggregator
│   │   └── DexscreenerApi.kt   # Market data
│   ├── data/            # Data models
│   └── ui/              # Android UI
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
- [x] Treasury lock blocking fix (Build #15-16)
- [x] UTC pause logic improvement
- [x] Watchlist token refresh optimization

### 🔴 Critical Issues (P0)
- [ ] App runtime crash - needs logcat verification
- [ ] Wallet connection not working - needs testing

### 🟡 Medium Priority (P1)
- [ ] Watchlist generating same tokens - verify after crash fix
- [ ] Android-Dashboard sync integration

### 🔵 Future Tasks (P2)
- [ ] Backtesting UI in dashboard
- [ ] Mobile-responsive dashboard
- [ ] Strategy parameter tuning

## Key Technical Decisions

### Treasury Lock Fix (Build #15-16)
- Only apply lock if milestones ($500+) actually hit
- Auto-reset corrupted state on restore
- Emergency unlock if wallet low but treasury claims funds

### Security Model
- SecurityGuard validates all trades pre-flight
- Circuit breaker on consecutive losses
- Price impact and slippage protection

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

## Testing Status
- Web dashboard: All 30 tests passed
- Android app: Requires device testing with logcat
