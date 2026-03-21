# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
Build a sophisticated Solana trading bot Android application with a web dashboard for monitoring. The project includes:
1. Android Kotlin app for automated trading on Solana
2. Web dashboard (React/FastAPI) for visualizing trading activity
3. GitHub Actions CI/CD for APK builds

## Product Overview
**Lifecycle Bot** is a sophisticated Solana trading bot with:
- Anti-rug engine and MEV protection
- LLM sentiment analysis
- Multi-layered trading strategies
- Self-learning BotBrain for adaptive trading
- Treasury management with scaling modes
- Real-time market scanning (DexScreener, Birdeye, CoinGecko, Pump.fun)
- **Web Dashboard** for remote monitoring and analytics

## Technology Stack
- **Mobile App:** Android (Kotlin)
- **Build System:** Gradle, GitHub Actions CI/CD
- **Backend:** FastAPI (Python)
- **Frontend:** React + TailwindCSS + Shadcn/UI
- **Database:** MongoDB

## What's Been Implemented

### Phase 1: Android App Build Fix (March 21, 2026) ✅
- Fixed all 56+ Kotlin compilation errors across 16 source files
- GitHub Actions build now passing (Run #23370831059, commit `e8cc10e`)
- APK artifact successfully generated and available for download

### Phase 2: Web Dashboard (March 21, 2026) ✅

**Backend API Endpoints:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User authentication
- `GET /api/auth/me` - Get current user
- `GET /api/dashboard` - Aggregated dashboard stats
- `GET /api/bot/status` - Bot running status
- `POST /api/bot/status` - Update bot status
- `GET /api/treasury/history` - Treasury performance history
- `POST /api/treasury/snapshot` - Record treasury snapshot
- `GET /api/positions` - Open positions
- `POST /api/positions/sync` - Sync positions from app
- `GET /api/trades` - Trade history
- `POST /api/trades` - Record new trade
- `GET /api/trades/stats` - Trading statistics
- `GET /api/activity` - Activity feed
- `POST /api/activity` - Log activity
- `GET /api/watchlist` - Token watchlist
- `POST /api/watchlist/sync` - Sync watchlist
- `POST /api/sync/bulk` - Bulk data push from Android app

**Frontend Dashboard Features:**
- 🔐 Password-protected authentication (login/register)
- 📊 Stats Cards: Treasury, P&L, Win Rate, Total Trades, Avg Win/Loss
- 📈 Treasury Performance Chart (30-day SVG graph)
- 💼 Open Positions Table with real-time P&L
- 📜 Trade History with WIN/LOSS badges
- 🔔 Activity Feed with categorized logs
- 👀 Token Watchlist with signals
- 🤖 Bot Status indicator (Running/Stopped, Mode badge)
- 🔄 Auto-refresh every 30 seconds

**Testing Status:** ✅ All 30 backend tests passed, frontend fully functional

## Architecture
```
/app
├── .github/workflows/build.yml    # Android APK CI/CD
├── backend/
│   ├── server.py                  # FastAPI with all endpoints
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js                 # Main app with auth routing
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx      # Auth UI
│   │   │   └── DashboardPage.jsx  # Main dashboard
│   │   └── components/dashboard/
│   │       ├── Header.jsx
│   │       ├── StatsCards.jsx
│   │       ├── PnLChart.jsx
│   │       ├── PositionsTable.jsx
│   │       ├── TradeHistory.jsx
│   │       ├── ActivityFeed.jsx
│   │       └── Watchlist.jsx
├── lifecycle_bot/
│   └── lifecycle_apk/             # Android Kotlin App
└── scripts/                       # Backtesting scripts
```

## Required API Keys (for Android app)
- Birdeye API key
- Groq API key (for LLM)
- Helius API key
- Telegram Bot Token + Chat ID

## Live URLs
- **Dashboard:** https://lifecycle-bot-build.preview.emergentagent.com
- **API:** https://lifecycle-bot-build.preview.emergentagent.com/api
- **GitHub Repo:** https://github.com/shaunhayes333-stack/lifecycle-bot

## Test Credentials
- Username: `demo_user`
- Password: `demo123`

## Prioritized Backlog

### P0 (Completed) ✅
- [x] Fix all Kotlin compilation errors
- [x] Get GitHub Actions build passing
- [x] APK artifact generated
- [x] Build web dashboard with authentication
- [x] Implement all dashboard components
- [x] Create API for Android app data sync

### P1 (Next)
- [ ] Connect Android app to dashboard API (add NetworkModule for data push)
- [ ] Add real-time WebSocket updates
- [ ] Implement push notifications for trades

### P2 (Future)
- [ ] Add portfolio analytics page
- [ ] Implement strategy backtesting UI
- [ ] Add export/import functionality
- [ ] Mobile-responsive optimizations

## Changelog

### March 21, 2026
- **BUILD FIX:** Successfully fixed 56+ Kotlin compilation errors
- **DASHBOARD:** Implemented full-stack web dashboard
  - Authentication system (register/login)
  - 6 stat cards with real-time metrics
  - Treasury performance chart
  - Trade history table
  - Activity feed
  - Watchlist and positions tables
  - Bot status monitoring
- **TESTING:** All 30 backend tests passing, frontend verified
