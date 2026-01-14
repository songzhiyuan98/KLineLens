# KLineLens — TODO

> Task tracking for MVP development. Update as you work.

---

## Milestone 0: Repo & Infrastructure ✅

### Tasks
- [x] Initialize monorepo structure (2026-01-13)
  - [x] Create `apps/web/` with Next.js
  - [x] Create `apps/api/` with FastAPI
  - [x] Create `packages/core/` Python package
  - [x] Setup root `package.json` for monorepo scripts
- [x] Setup Python virtual environment
- [x] Setup TypeScript config for web
- [x] Add `.gitignore` for all layers
- [x] Create `.env.example` files

### Acceptance ✅
- `npm install` works at root
- `uvicorn` can start API (returns 404 on /)
- `npm run dev` starts web (shows Next.js default page)

---

## Milestone 1: Market Data ✅

### Tasks
- [x] Implement `MarketDataProvider` interface (2026-01-13)
  - [x] Define `Bar` dataclass
  - [x] Define error types (`TickerNotFoundError`, `RateLimitError`)
- [x] Implement `YFinanceProvider`
  - [x] `get_bars(ticker, tf, window)`
  - [x] `validate_ticker(ticker)`
  - [x] Handle timeframe mapping (1m, 5m, 1d)
- [x] Implement `GET /v1/bars` endpoint
  - [x] Parse query params (ticker, tf, window)
  - [x] Call provider
  - [x] Return JSON response
- [x] Add in-memory cache
  - [x] Cache key: `{ticker}:{tf}:{window}`
  - [x] TTL: 60s default
- [x] Add error handling
  - [x] Invalid ticker → 400
  - [x] No data → 404
  - [x] Rate limit → 429
  - [x] Provider error → 502

### Acceptance ✅
- `GET /v1/bars?ticker=TSLA&tf=1m` returns bars JSON
- `GET /v1/bars?ticker=INVALID123&tf=1m` returns 400/404
- Second request within 60s hits cache (faster response)
- Rate limit error returns proper 429 response

---

## Milestone 2: Core Structure Engine ✅

### Tasks
- [x] `features.py` - Feature calculations (2026-01-13)
  - [x] `calculate_atr(bars, period=14)`
  - [x] `calculate_volume_ratio(bars, period=30)`
  - [x] `calculate_wick_ratios(bar)`
  - [x] `calculate_efficiency(bar)`
- [x] `structure.py` - Structure detection
  - [x] `find_swing_points(bars, n=4)` - Fractal method
  - [x] `cluster_zones(points, atr)` - Price binning
  - [x] `classify_regime(swings)` - HH/HL/LL/LH analysis
  - [x] `BreakoutFSM` class - State machine
- [x] `analyze.py` - Main entry point
  - [x] `analyze_structure(bars, params)` → partial report
- [x] Unit tests (42 tests passing)
  - [x] Test swing points with known data
  - [x] Test regime classification (uptrend/downtrend/range)
  - [x] Test zone clustering
  - [x] Test breakout state machine transitions

### Acceptance ✅
- `find_swing_points()` returns correct peaks/troughs for test data
- `classify_regime()` returns "uptrend" for HH/HL sequence
- `cluster_zones()` groups nearby prices into zones
- `BreakoutFSM` transitions: idle → attempt → confirmed/fakeout

---

## Milestone 3: Behavior + Timeline + Playbook ✅

### Tasks
- [x] `behavior.py` - Behavior inference (2026-01-13)
  - [x] `score_accumulation(bars, zones, features)`
  - [x] `score_shakeout(bars, zones, features)`
  - [x] `score_markup(bars, zones, features, breakout_state)`
  - [x] `score_distribution(bars, zones, features)`
  - [x] `score_markdown(bars, zones, features, breakout_state)`
  - [x] `scores_to_probabilities(scores)` - Softmax
  - [x] `generate_evidence(bars, dominant, features)`
- [x] `timeline.py` - State machine
  - [x] `TimelineState` dataclass
  - [x] `TimelineManager.update(new_report)` → events
  - [x] Event emission rules (delta threshold, state change)
- [x] `playbook.py` - Playbook generation
  - [x] `generate_playbook(report)` → Plan A, Plan B
  - [x] Target calculation (next zone or ATR-based)
  - [x] Invalidation level calculation
- [x] Complete `analyze.py`
  - [x] `analyze_market(bars, state, params)` → full `AnalysisReport`
- [x] `POST /v1/analyze` endpoint
  - [x] Fetch bars (cached)
  - [x] Call `analyze_market()`
  - [x] Return report JSON
- [x] Unit tests (37 API tests + 42 core tests = 79 total)
  - [x] Test behavior scores with constructed bars
  - [x] Test probability softmax
  - [x] Test timeline event emission
  - [x] Test playbook generation

### Acceptance ✅
- Shakeout scenario (sweep + reclaim) → high shakeout probability
- Timeline emits event when dominant behavior changes
- Playbook contains Plan A and Plan B with valid levels
- `/v1/analyze` returns complete `AnalysisReport` JSON

---

## Milestone 4: Web Terminal ✅

### Tasks
- [x] Dashboard page (`/`) (2026-01-14)
  - [x] Search input (ticker)
  - [x] Validation (non-empty, format check)
  - [x] Navigate to `/t/{ticker}` on submit
  - [x] Popular tickers quick access
- [x] Detail page (`/t/[ticker]`)
  - [x] Fetch bars on mount
  - [x] Fetch analysis on mount
  - [x] Chart component (candlestick + volume) using lightweight-charts
  - [x] Zone overlays on chart (support/resistance lines)
  - [x] Analysis panel (cards)
    - [x] Market State card
    - [x] Behavior Probabilities card
    - [x] Evidence card
    - [x] Timeline card
    - [x] Playbook card
  - [x] Timeframe switcher (1m, 5m, 1d)
  - [x] Last updated timestamp
  - [x] Auto-refresh every 60s
  - [x] Error states (loading, error, retry)
- [x] Settings page (`/settings`)
  - [x] Placeholder for future settings
  - [x] About section with version
  - [x] Disclaimer notice
- [x] Layout
  - [x] Header with logo + navigation
  - [x] Footer
  - [x] Global styles

### Acceptance ✅
- Enter "TSLA" on dashboard → navigate to detail page
- Chart shows candlesticks with zone lines
- All 5 analysis cards render with data
- Timeframe switch reloads data
- Page auto-refreshes every 60s
- Error message shown for invalid ticker

---

## Milestone 5: Polish & Ship ✅

### Tasks
- [x] Error boundary for React (2026-01-14)
- [x] Loading states (skeleton) (2026-01-14)
- [x] Final UI polish (2026-01-14)
  - [x] 移除卡片边框和背景
  - [x] 简化颜色使用（灰色系）
  - [x] 移除滚动条
- [x] i18n 国际化（中英文）(2026-01-14)
- [x] Volume 面板 + Volume MA (2026-01-14)
- [x] Evidence 可视化（点击定位图表）(2026-01-14)
- [x] Breakout Status 卡片 (2026-01-14)
- [x] Signals 面板（含时间）(2026-01-14)
- [x] Test with multiple tickers (2026-01-14)
- [x] Update README with run instructions (2026-01-14)

### Acceptance ✅
- No crashes on edge cases
- Smooth user experience
- Documentation complete
- i18n working (中文/English)

---

## Backlog (Post-MVP)

- [ ] Multi-timeframe analysis (1D + 1m alignment)
- [ ] Redis cache for state persistence
- [ ] WebSocket for real-time updates
- [ ] Snapshot/replay feature
- [ ] Polygon provider
- [ ] LLM narration layer
- [ ] Dark mode

---

## Completed

- [x] Initial documentation set (2026-01-13)
- [x] Document optimization and restructure (2026-01-13)
- [x] Milestone 0: Repo & Infrastructure (2026-01-13)
- [x] Milestone 1: Market Data (2026-01-13)
- [x] Milestone 2: Core Structure Engine (2026-01-13)
- [x] Milestone 3: Behavior + Timeline + Playbook + API Integration (2026-01-13)
- [x] Milestone 4: Web Terminal (2026-01-14)
- [x] Milestone 5: Polish & Ship (2026-01-14)
- [x] i18n 国际化 (2026-01-14)
- [x] Alpaca/Alpha Vantage Providers (2026-01-14)
