# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
Build a sophisticated Solana trading bot Android application that autonomously scans, learns, and trades.

## BUILD STATUS (All Passing ✅)
- **Build #53**: Fixed compilation errors
- **Build #54**: Enabled autonomous mode
- **Build #55**: Fixed DexScreener API endpoints
- **Build #56**: Paper mode now uses wallet balance

## LATEST IMPROVEMENTS

### WebSocket Real-Time Dashboard (Web)
- Added WebSocket endpoint `/ws/{token}` for live updates
- Dashboard auto-connects and shows "Live" when connected
- Falls back to polling when WebSocket unavailable
- Real-time updates when Android app syncs data

### Paper Trading with Real Balance (Android - Build #56)
- Paper wallet syncs with real wallet balance on connect
- Paper trades deduct/add from paper balance
- Learning engine receives proper trade data
- P&L calculations reflect real position sizing

### DexScreener Scanner Fix (Android - Build #55)
- Changed from broken `/latest/dex/pairs/solana/raydium` endpoint
- Now uses `/latest/dex/search?q=solana` which works
- Scanner finds Solana tokens with >$3K liquidity
- Detects pump.fun tokens and graduates

## Architecture

### Mobile App (Android/Kotlin)
```
/lifecycle_apk/app/src/main/kotlin/com/lifecyclebot/
├── engine/
│   ├── BotService.kt          # Main bot loop
│   ├── SolanaMarketScanner.kt # Token discovery (FIXED)
│   ├── LifecycleStrategy.kt   # Trading signals
│   ├── Executor.kt            # Trade execution
│   ├── BotBrain.kt            # Self-learning (3 layers)
│   └── ShadowLearningEngine.kt # Parallel simulations
├── data/
│   ├── BotConfig.kt           # Settings (autoTrade=true)
│   └── Models.kt              # Paper wallet tracking
└── ui/
    └── MainActivity.kt
```

### Web Dashboard (React + FastAPI)
```
/backend/server.py    # WebSocket + REST API
/frontend/src/
├── pages/
│   ├── DashboardPage.jsx  # WebSocket connection
│   └── LoginPage.jsx
└── components/dashboard/
    ├── Header.jsx         # Connection status
    ├── StatsCards.jsx
    ├── PnLChart.jsx
    ├── PositionsTable.jsx
    ├── TradeHistory.jsx
    ├── ActivityFeed.jsx
    └── Watchlist.jsx
```

## Configuration (BotConfig.kt)

| Setting | Default | Description |
|---------|---------|-------------|
| `autoTrade` | **true** | Autonomous trading |
| `autoAddNewTokens` | **true** | Auto-scan launches |
| `paperMode` | true | Simulate first |
| `minLiquidityUsd` | 3000 | Min liquidity filter |

## Self-Learning System

### BotBrain - 3 Layers
1. **Statistical (every 20 trades)**: Win rate analysis, threshold adjustment
2. **LLM (every 50 trades)**: Groq deep analysis (if key set)
3. **Regime Detection**: Market classification, position sizing

### ShadowLearningEngine
- 11 parallel strategy variants
- Compares to live trading
- Auto-generates optimization insights

## API Endpoints

### REST
- `POST /api/auth/login` - JWT auth
- `POST /api/sync/bulk` - Android sync (triggers WebSocket)
- `GET /api/dashboard` - Stats
- `GET /api/positions` - Open positions
- `GET /api/trades` - History

### WebSocket
- `WS /ws/{token}` - Real-time updates
- Message types: `init`, `update`, `sync_update`, `heartbeat`

## Dashboard Access
- **URL**: https://dex-strategy-v7.preview.emergentagent.com
- **Login**: testuser / test123

## User Flow
1. Download APK from GitHub Actions Build #56
2. Install on Android, connect wallet
3. Paper wallet syncs with real balance
4. Scanner finds tokens → adds to watchlist
5. Strategy evaluates → generates signals
6. Paper trades execute → learning engine fed
7. Dashboard updates in real-time via WebSocket
