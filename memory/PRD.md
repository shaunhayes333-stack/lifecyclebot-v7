# Lifecycle Bot - Product Requirements Document

## Original Problem Statement
The user wanted to upload a Kotlin-based Android Solana trading bot from GitHub (`https://github.com/shaunhayes333-stack/lifecycle-bot`) and fix persistent build failures. The project had 56+ compilation errors causing all GitHub Actions builds to fail after 25+ attempts.

## Product Overview
A sophisticated Solana trading bot Android application with:
- Anti-rug engine and MEV protection
- LLM sentiment analysis
- Multi-layered trading strategies
- Self-learning BotBrain for adaptive trading
- Treasury management with scaling modes
- Real-time market scanning (DexScreener, Birdeye, CoinGecko, Pump.fun)

## Technology Stack
- **Mobile App:** Android (Kotlin)
- **Build System:** Gradle, GitHub Actions CI/CD
- **Backend:** FastAPI (skeleton)
- **Frontend:** React (skeleton)
- **Database:** MongoDB (backend), EncryptedSharedPreferences/SQLite (in-app)

## What's Been Implemented

### Build Fix (March 21, 2026) ✅
Successfully fixed all 56+ Kotlin compilation errors across multiple files:

**Files Fixed:**
1. `BotBrain.kt` - String format syntax, duplicate variable declarations, coroutine scope
2. `BotService.kt` - Property getter/setter, lambda flow control, variable ordering, executor visibility
3. `TradeDatabase.kt` - Duplicate companion objects, database reference
4. `TreasuryManager.kt` - Multiline string syntax
5. `Executor.kt` - BotService.status reference, parameter types
6. `LifecycleStrategy.kt` - Added detectSpikeTop function, SpikeResult data class, parameter fixes
7. `SolanaMarketScanner.kt` - Coroutine scope, BirdeyeApi constructor
8. `PerformanceAnalytics.kt` - Import path fix
9. `StartupReconciler.kt` - OkHttp imports, Position constructor
10. `TokenSafetyChecker.kt` - OkHttp request body syntax
11. `TelegramScraper.kt` - Extension function cleanup
12. `AntiRugEngine.kt` - Empty setOf type parameter
13. `DataOrchestrator.kt` - onLog parameter count
14. `SmartSizer.kt` - fmt extension function
15. `BacktestActivity.kt` - LifecycleStrategy named parameter
16. `BotViewModel.kt` - executor accessibility

**GitHub Actions Build Status:** ✅ SUCCESS (Run #23370831059, commit e8cc10e)

## Architecture
```
/app
├── .github/workflows/build.yml    # CI/CD workflow
├── backend/                       # FastAPI (skeleton)
├── frontend/                      # React (skeleton)
├── lifecycle_bot/
│   └── lifecycle_apk/             # Android Kotlin App
│       ├── app/src/main/kotlin/com/lifecyclebot/
│       │   ├── data/              # Data models
│       │   ├── engine/            # Core trading logic
│       │   ├── network/           # API/Network calls
│       │   └── ui/                # Android UI
│       └── build.gradle.kts
└── scripts/                       # Backtesting scripts
```

## Required API Keys (for app functionality)
- Birdeye API key
- Groq API key (for LLM)
- Helius API key
- Telegram Bot Token + Chat ID

## Prioritized Backlog

### P0 (Completed)
- [x] Fix all Kotlin compilation errors
- [x] Get GitHub Actions build passing
- [x] APK artifact generated successfully

### P1 (Next)
- [ ] Develop React/FastAPI web dashboard for bot visualization
- [ ] Add P&L tracking and reporting
- [ ] Implement bot status monitoring

### P2 (Future)
- [ ] Further refine trading strategy based on live performance
- [ ] Implement "smart AI layer" for treasury-based scaling
- [ ] Add more sophisticated backtesting capabilities

## Test Reports Created
- `/app/backtest_data_30d_comprehensive.json` - 30-day dataset
- `/app/backtest_report.json` - Initial backtest
- `/app/backtest_report_v2_enhanced.json` - Enhanced backtest
- `/app/backtest_report_v3_smart_scaling.json` - Smart scaling backtest
