# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
Build a sophisticated Solana trading bot Android application that autonomously scans, learns, and trades.

## BUILD STATUS (All Passing ✅)
- **Build #53-#63**: Stable builds with continuous improvements
- **Latest fixes (Dec 2025)**: Sound system upgrade, autonomous mode enabled by default

## LATEST IMPROVEMENTS

### Sound System v2 (Dec 2025)
- Added support for custom sound files via MediaPlayer (woohoo.mp3, awesome.mp3)
- Automatic fallback to ToneGenerator if custom sounds unavailable
- `playBuySound()` triggers on BUY events (Homer "Woohoo!")
- `playBlockSound()` triggers on BLOCK/SAFETY events (Peter Griffin "Awesome")
- All existing sounds (cash register, milestone, warning siren) preserved

### Autonomous Mode Enabled by Default (Dec 2025)
- `autoTrade` now defaults to `true` for autonomous operation
- `autoAddNewTokens` now defaults to `true` for auto-scanning
- Users can still disable in settings if desired

### WebSocket Real-Time Dashboard (Web)
- Added WebSocket endpoint `/ws/{token}` for live updates
- Dashboard auto-connects and shows "Live" when connected
- Falls back to polling when WebSocket unavailable
- Real-time updates when Android app syncs data

### Paper Trading with Real Balance (Android)
- Paper wallet syncs with real wallet balance on connect
- Paper trades deduct/add from paper balance
- Learning engine receives proper trade data
- P&L calculations reflect real position sizing

### DexScreener Scanner Fix (Android)
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
│   ├── SolanaMarketScanner.kt # Token discovery
│   ├── LifecycleStrategy.kt   # Trading signals
│   ├── Executor.kt            # Trade execution (with sound triggers)
│   ├── SoundManager.kt        # Custom sounds + fallbacks
│   ├── BotBrain.kt            # Self-learning (3 layers)
│   └── ShadowLearningEngine.kt # Parallel simulations
├── data/
│   ├── BotConfig.kt           # Settings (autoTrade=true, autoAddNewTokens=true)
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
| `autoTrade` | **true** | Autonomous trading enabled by default |
| `autoAddNewTokens` | **true** | Auto-scan pump.fun launches |
| `paperMode` | true | Simulate first (disable for live) |
| `minLiquidityUsd` | **5000** | Min liquidity filter (lowered from 8000) |
| `minDiscoveryScore` | **30** | Min score for watchlist (lowered from 35) |
| `scanIntervalSecs` | **30** | Scan interval (lowered from 45) |
| `maxWatchlistSize` | **75** | Max tracked tokens (raised from 50) |
| `soundEnabled` | true | Play audio feedback on trades |

## WebSocket Real-Time Updates (Backend + Frontend)
- ✅ Backend `/ws/{token}` endpoint working
- ✅ Frontend WebSocket connection logic implemented
- ✅ Graceful fallback to polling every 30s when WS unavailable
- ✅ Connection status indicator in header ("Live" / "Polling")
- Session validation fixed to not require `expires_at` field
- `get_dashboard_data()` falls back to global data if user-specific not found

## Custom Sound Files (res/raw/)
| File | Event | Status |
|------|-------|--------|
| `woohoo.mp3` | BUY executed | ✅ Placeholder created (replace with real audio) |
| `awesome.mp3` | Token BLOCKED | ✅ Placeholder created (replace with real audio) |
| `README.md` | Instructions | ✅ Created |

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
- **URL**: https://bot-backtest.preview.emergentagent.com
- **Login**: testuser / test123

## User Flow
1. Download APK from GitHub Actions (latest build)
2. Install on Android, connect wallet
3. Paper wallet syncs with real balance
4. Scanner finds tokens → adds to watchlist
5. Strategy evaluates → generates signals
6. Paper trades execute → learning engine fed
7. On BUY: "Woohoo!" sound plays
8. On BLOCK: "Awesome" sound plays
9. Dashboard updates in real-time via WebSocket

## Known Issues / In Progress
1. **Bot stops when minimized** - ✅ FIXED: Added battery optimization check + enhanced service lifecycle logging
2. **Scanner token yield** - ✅ FIXED: Added detailed filter rejection logging to diagnose issues

## Files Modified (Dec 2025)
- `SoundManager.kt` - Added MediaPlayer support for custom sounds
- `Executor.kt` - Added `playBuySound()` calls on BUY events
- `BotConfig.kt` - Changed `autoTrade` and `autoAddNewTokens` defaults to `true`
- `BotService.kt` - Added battery optimization check, enhanced lifecycle logging
- `SolanaMarketScanner.kt` - Added detailed filter rejection logging with reasons
- `MainActivity.kt` - Battery optimization dialog (already existed)

## Background Execution Improvements
- **Battery Optimization Check**: Bot logs warning if battery optimization is enabled
- **START_STICKY**: Service restarts automatically if killed by system
- **onTaskRemoved**: Schedules restart via AlarmManager when app swiped from recents
- **Lifecycle Logging**: Full visibility into onStartCommand, onDestroy, onTaskRemoved events

## Scanner Improvements (Dec 2025)

### New Data Sources
- **Source 9: Pump.fun Direct API** - Scans `frontend-api.pump.fun` for new launches
  - Gets bonding curve progress (tokens near graduation get higher scores)
  - Filters by mcap > $1000 to avoid dead tokens
  - Up to 15 tokens per scan cycle

### Lowered Filter Thresholds
| Setting | Old Value | New Value | Reason |
|---------|-----------|-----------|--------|
| `minLiquidityUsd` | $8,000 | $5,000 | Catch earlier opportunities |
| `minVolLiqRatio` | 0.30 | 0.20 | Allow more tokens through |
| `minDiscoveryScore` | 35 | 30 | Lower barrier for watchlist |
| `scanMinMcapUsd` | $5,000 | $3,000 | Earlier entry on pump.fun tokens |
| `scanIntervalSecs` | 45 | 30 | Faster scanning |
| `maxWatchlistSize` | 50 | 75 | Track more tokens |

### Scanner Sources (9 total)
1. DexScreener Trending
2. DexScreener Gainers
3. DexScreener Boosted
4. Pump.fun Graduates (Raydium migrations)
5. **Pump.fun New Launches** (NEW)
6. Birdeye Trending (needs API key)
7. CoinGecko Trending
8. Raydium New Pools
9. Narrative Scanning (keyword-based)

## Scanner Debugging
Filter rejection logs now show exact reason:
- `❌ FILTER REJECT: TOKEN — liq $X < min $Y`
- `❌ FILTER REJECT: TOKEN — score X < min Y`
- `❌ FILTER REJECT: TOKEN — mcap $X < min $Y`
- `❌ FILTER REJECT: TOKEN — scam pattern detected`
- `✅ FILTER PASS: TOKEN (SOURCE) liq=$XK score=Y`
