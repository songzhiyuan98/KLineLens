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

## Milestone 6: v4 Terminal UI ✅

### Tasks
- [x] Zones 层次化显示 (2026-01-14)
  - [x] Top1: 实线 + label
  - [x] Top2: 虚线，无 label
  - [x] Top3+: 点线，更淡
- [x] 右侧 Panel 终端化 (2026-01-14)
  - [x] Section title 更小更灰
  - [x] 分割线更精致
- [x] 顶部 Header 产品级 (2026-01-14)
  - [x] 字号更小
  - [x] Volume 改为圆点+颜色
- [x] Decision Line (Bloomberg 风格) (2026-01-14)
  - [x] Action: WAIT / WATCH / CONFIRM / AVOID
  - [x] Trigger: 具体触发条件
  - [x] Risk: 低置信度警告（可选）
- [x] low conf 解释 tooltip (2026-01-14)
- [x] DIST 改为 ATR 距离 (2026-01-14)
- [x] 1m/5m 周期降级提示 (2026-01-14)
- [x] i18n 适配所有新 UI (2026-01-14)

### Acceptance ✅
- Zones 视觉层次清晰
- Decision Line 提供清晰的操作指引
- 短周期有噪音警告

---

## Milestone 7: Homepage Enhancement ✅

### Tasks
- [x] 首页适配终端 UI 风格 (2026-01-14)
- [x] 更多推荐标的 (2026-01-14)
  - [x] 美股热门 (TSLA, AAPL, NVDA, META, GOOGL, AMZN, MSFT)
  - [x] ETF (SPY, QQQ, IWM, DIA, VTI)
  - [x] 加密货币 (BTC/USD, ETH/USD, SOL/USD)
- [x] 模糊搜索功能 (2026-01-14)
  - [x] 输入时显示建议
  - [x] 支持代码和公司名称搜索

### Acceptance ✅
- 首页风格与详情页一致
- 推荐标的分类清晰
- 搜索体验流畅

---

## Milestone 8: LLM Narrative ✅

### Tasks
- [x] LLM 服务模块 (OpenAI/Gemini 支持) (2026-01-14)
- [x] POST /v1/narrative API 端点 (2026-01-14)
- [x] 前端 Narrative 区块和生成按钮 (2026-01-14)
- [x] 双模型配置 (短评: gpt-4o-mini, 报告: gpt-4o) (2026-01-14)

### Acceptance ✅
- 点击"生成报告"按钮生成 AI 解读
- 短评使用 gpt-4o-mini，报告使用 gpt-4o
- 支持中英文输出
- 错误处理和加载状态

---

## Milestone 9: Enhanced UI + Signal Evaluation (Current)

### Tasks
- [ ] Playbook 表格化显示
  - [ ] 一行表格格式（方向 | 入场 | 目标 | 止损 | R:R | 条件 | 风险）
  - [ ] Plan A / Plan B 并排显示
  - [ ] 颜色区分 LONG/SHORT
- [ ] Evidence 增强
  - [ ] 添加时间戳显示（何时发生）
  - [ ] 每日缓存（localStorage）
  - [ ] 进入页面自动加载缓存
  - [ ] 每日清理一次（按日期判断）
- [ ] Timeline 每日缓存
  - [ ] localStorage 缓存策略
  - [ ] 进入页面自动加载
  - [ ] 每日清理机制
- [ ] Signal Evaluation（信号评估）功能
  - [ ] 新增数据库表存储预测记录
  - [ ] POST /v1/signal-evaluation API（记录预测）
  - [ ] GET /v1/signal-evaluations API（获取历史记录）
  - [ ] PUT /v1/signal-evaluation/{id} API（更新结果）
  - [ ] 前端信号评估 Tab（与 Playbook 切换）
  - [ ] 表格显示：时间 | 预测 | 实际 | 结果 | 原因
  - [ ] 正确率统计展示
- [ ] 事件驱动的自动短评（迁移自 M8）
  - [ ] regime shift 触发
  - [ ] breakout state change 触发
  - [ ] behavior delta >= 12% 触发

### Acceptance
- Playbook 以表格形式显示，信息一目了然
- Evidence 和 Timeline 进入页面自动加载缓存数据
- 缓存数据每天自动清理
- Signal Evaluation 可记录预测并跟踪结果
- 正确率统计准确显示

---

## Backlog (Post-MVP)

- [ ] K线 Tooltip 增强 (Volume/RVOL/Effort/Result)
- [ ] Multi-timeframe analysis (1D + 1m alignment)
- [ ] Redis cache for state persistence
- [ ] WebSocket for real-time updates
- [ ] Snapshot/replay feature
- [ ] Polygon provider
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
- [x] TwelveData Provider (2026-01-14)
- [x] v4 Terminal UI (2026-01-14)
- [x] Milestone 7: Homepage Enhancement (2026-01-14)
- [x] Milestone 8: LLM Narrative (2026-01-14)
- [x] Playbook UI Enhancement (方向/R:R/条件/风险) (2026-01-14)
- [x] Playbook/Timeline 位置互换 (2026-01-14)
- [x] K线图本地时间显示 (2026-01-14)
