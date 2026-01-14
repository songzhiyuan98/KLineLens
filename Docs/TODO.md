# KLineLens — TODO

> Task tracking for MVP development. Update as you work.

---

## Milestone 0: Repo & Infrastructure

### Tasks
- [ ] Initialize monorepo structure
  - [ ] Create `apps/web/` with Next.js
  - [ ] Create `apps/api/` with FastAPI
  - [ ] Create `packages/core/` Python package
  - [ ] Setup root `package.json` for monorepo scripts
- [ ] Setup Python virtual environment
- [ ] Setup TypeScript config for web
- [ ] Add `.gitignore` for all layers
- [ ] Create `.env.example` files

### Acceptance
- `npm install` works at root
- `uvicorn` can start API (returns 404 on /)
- `npm run dev` starts web (shows Next.js default page)

---

## Milestone 1: Market Data

### Tasks
- [ ] Implement `MarketDataProvider` interface
  - [ ] Define `Bar` dataclass
  - [ ] Define error types (`TickerNotFoundError`, `RateLimitError`)
- [ ] Implement `YFinanceProvider`
  - [ ] `get_bars(ticker, tf, window)`
  - [ ] `validate_ticker(ticker)`
  - [ ] Handle timeframe mapping (1m, 5m, 1d)
- [ ] Implement `GET /v1/bars` endpoint
  - [ ] Parse query params (ticker, tf, window)
  - [ ] Call provider
  - [ ] Return JSON response
- [ ] Add in-memory cache
  - [ ] Cache key: `{ticker}:{tf}:{window}`
  - [ ] TTL: 60s default
- [ ] Add error handling
  - [ ] Invalid ticker → 400
  - [ ] No data → 404
  - [ ] Rate limit → 429
  - [ ] Provider error → 502

### Acceptance
- `GET /v1/bars?ticker=TSLA&tf=1m` returns bars JSON
- `GET /v1/bars?ticker=INVALID123&tf=1m` returns 400/404
- Second request within 60s hits cache (faster response)
- Rate limit error returns proper 429 response

---

## Milestone 2: Core Structure Engine

### Tasks
- [ ] `features.py` - Feature calculations
  - [ ] `calculate_atr(bars, period=14)`
  - [ ] `calculate_volume_ratio(bars, period=30)`
  - [ ] `calculate_wick_ratios(bar)`
  - [ ] `calculate_efficiency(bar)`
- [ ] `structure.py` - Structure detection
  - [ ] `find_swing_points(bars, n=4)` - Fractal method
  - [ ] `cluster_zones(points, atr)` - Price binning
  - [ ] `classify_regime(swings)` - HH/HL/LL/LH analysis
  - [ ] `BreakoutFSM` class - State machine
- [ ] `analyze.py` - Main entry point
  - [ ] `analyze_structure(bars, params)` → partial report
- [ ] Unit tests
  - [ ] Test swing points with known data
  - [ ] Test regime classification (uptrend/downtrend/range)
  - [ ] Test zone clustering
  - [ ] Test breakout state machine transitions

### Acceptance
- `find_swing_points()` returns correct peaks/troughs for test data
- `classify_regime()` returns "uptrend" for HH/HL sequence
- `cluster_zones()` groups nearby prices into zones
- `BreakoutFSM` transitions: idle → attempt → confirmed/fakeout

---

## Milestone 3: Behavior + Timeline + Playbook

### Tasks
- [ ] `behavior.py` - Behavior inference
  - [ ] `score_accumulation(bars, zones, features)`
  - [ ] `score_shakeout(bars, zones, features)`
  - [ ] `score_markup(bars, zones, features, breakout_state)`
  - [ ] `score_distribution(bars, zones, features)`
  - [ ] `score_markdown(bars, zones, features, breakout_state)`
  - [ ] `scores_to_probabilities(scores)` - Softmax
  - [ ] `generate_evidence(bars, dominant, features)`
- [ ] `timeline.py` - State machine
  - [ ] `TimelineState` dataclass
  - [ ] `TimelineManager.update(new_report)` → events
  - [ ] Event emission rules (delta threshold, state change)
- [ ] `playbook.py` - Playbook generation
  - [ ] `generate_playbook(report)` → Plan A, Plan B
  - [ ] Target calculation (next zone or ATR-based)
  - [ ] Invalidation level calculation
- [ ] Complete `analyze.py`
  - [ ] `analyze_market(bars, state, params)` → full `AnalysisReport`
- [ ] `POST /v1/analyze` endpoint
  - [ ] Fetch bars (cached)
  - [ ] Call `analyze_market()`
  - [ ] Maintain state per ticker+tf
  - [ ] Return report JSON
- [ ] Unit tests
  - [ ] Test behavior scores with constructed bars
  - [ ] Test probability softmax
  - [ ] Test timeline event emission
  - [ ] Test playbook generation

### Acceptance
- Shakeout scenario (sweep + reclaim) → high shakeout probability
- Timeline emits event when dominant behavior changes
- Playbook contains Plan A and Plan B with valid levels
- `/v1/analyze` returns complete `AnalysisReport` JSON

---

## Milestone 4: Web Terminal

### Tasks
- [ ] Dashboard page (`/`)
  - [ ] Search input (ticker)
  - [ ] Validation (non-empty, format check)
  - [ ] Navigate to `/t/{ticker}` on submit
- [ ] Detail page (`/t/[ticker]`)
  - [ ] Fetch bars on mount
  - [ ] Fetch analysis on mount
  - [ ] Chart component (candlestick + volume)
  - [ ] Zone overlays on chart
  - [ ] Breakout/fakeout markers
  - [ ] Analysis panel (cards)
    - [ ] Market State card
    - [ ] Behavior Probabilities card
    - [ ] Evidence card
    - [ ] Timeline card
    - [ ] Playbook card
  - [ ] Timeframe switcher (1m, 1d)
  - [ ] Last updated timestamp
  - [ ] Auto-refresh every 60s
  - [ ] Error states (no data, rate limit)
- [ ] Settings page (`/settings`)
  - [ ] Reserved for future settings (MVP: minimal)
- [ ] Layout
  - [ ] Header with logo + navigation
  - [ ] Responsive design (desktop-first)

### Acceptance
- Enter "TSLA" on dashboard → navigate to detail page
- Chart shows candlesticks with zone rectangles
- All 5 analysis cards render with data
- Timeframe switch reloads data
- Page auto-refreshes every 60s
- Error message shown for invalid ticker

---

## Milestone 5: Polish & Ship

### Tasks
- [ ] Error boundary for React
- [ ] Loading states (skeleton)
- [ ] Final UI polish
- [ ] Test with multiple tickers
- [ ] Test edge cases (no volume, gaps)
- [ ] Update README with run instructions
- [ ] Record demo video/GIF

### Acceptance
- No crashes on edge cases
- Smooth user experience
- Documentation complete
- Demo shows full flow

---

## Backlog (Post-MVP)

- [ ] Multi-timeframe analysis (1D + 1m alignment)
- [ ] Redis cache for state persistence
- [ ] WebSocket for real-time updates
- [ ] Snapshot/replay feature
- [ ] More providers (Alpha Vantage, Polygon)
- [ ] i18n (Chinese language)
- [ ] LLM narration layer

---

## Completed

- [x] Initial documentation set (2026-01-13)
- [x] Document optimization and restructure (2026-01-13)
