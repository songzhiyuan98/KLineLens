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

## Milestone 9: Responsive Design + UI Polish ✅

### Tasks
- [x] 响应式设计 (2026-01-15)
  - [x] 详情页流体排版 (clamp())
  - [x] 图表高度动态调整 (280-550px, 45% vh)
  - [x] 右侧面板字体缩放
- [x] 首页简化 (2026-01-15)
  - [x] 纯黑白设计
  - [x] 大搜索框居中
  - [x] 最近访问记录 (localStorage)
  - [x] 移除推荐分类
- [x] 设置页面优化 (2026-01-15)
  - [x] 简洁现代风格
  - [x] 响应式字体
  - [x] 免责声明简化
- [x] 移除页脚 (2026-01-15)
- [x] 智能图表可视范围 (2026-01-15)
  - [x] 1m: 120 bars (2小时)
  - [x] 5m: 78 bars (1交易日)
  - [x] 1d: 20 bars (1个月)
- [x] 修复价格线重复问题 (2026-01-15)

### Acceptance ✅
- 全屏时字体自动放大
- 图表高度随视口调整
- 首页简洁现代
- 设置页面响应式

---

## Milestone 10: Enhanced Features (Current)

### Tasks
- [ ] Signal Evaluation（信号评估）功能
  - [ ] 新增数据库表存储预测记录
  - [ ] POST /v1/signal-evaluation API（记录预测）
  - [ ] GET /v1/signal-evaluations API（获取历史记录）
  - [ ] PUT /v1/signal-evaluation/{id} API（更新结果）
  - [ ] 前端信号评估 Tab（与 Playbook 切换）
  - [ ] 表格显示：时间 | 预测 | 实际 | 结果 | 原因
  - [ ] 正确率统计展示
- [ ] 事件驱动的自动短评
  - [ ] regime shift 触发
  - [ ] breakout state change 触发
  - [ ] behavior delta >= 12% 触发

### Acceptance
- Signal Evaluation 可记录预测并跟踪结果
- 正确率统计准确显示
- 自动短评触发正常

---

## Milestone 11: Extended Hours (EH) System

> Premarket/Afterhours Structure Completion Engine
> Spec: `Docs/EH_SPEC.md`

### Tasks
- [x] **Phase 0: Free EH Data Source** (2026-01-15)
  - [x] Add `get_bars_extended()` to YFinanceProvider with `prepost=True`
  - [x] Update PROVIDER.md with Yahoo EH support
  - [x] Update EH_SPEC.md with Yahoo as MVP option
  - MVP 方案: TwelveData 正盘 + Yahoo prepost 盘前盘后（免费）
- [x] **Phase 1: Data Layer** (2026-01-15)
  - [x] YFinance provider with `prepost=True` parameter (免费)
  - [x] Add `split_bars_by_session()` helper (Regular/PM/AH 分割)
  - [x] Add `SessionBars` dataclass
  - [x] Add `build_eh_context_from_bars()` high-level builder
  - [x] Test extended hours data availability ✅ (648 PM + 780 Regular + 481 AH bars)
  - [ ] Update TwelveData provider with `prepost=true` parameter (Pro tier, optional)
- [x] **Phase 2: Core EH Module** (`packages/core/src/extended_hours.py`) (已有基础实现)
  - [x] `EHLevels` dataclass (YC/YH/YL/PMH/PML/AHH/AHL/GAP)
  - [x] `EHContext` dataclass (full output structure)
  - [x] `extract_eh_levels_*()` - Extract key levels from bars
  - [x] `generate_key_zones()` - Generate zones with roles
  - [x] `assess_afterhours_risk()` - AH risk assessment
  - [x] `build_eh_context()` - Main orchestrator
  - [ ] `calculate_eh_metrics()` - EH_RVOL, EH_range_score (TODO)
  - [ ] `classify_premarket_regime()` - 4-class classification (TODO)
  - [ ] `detect_pm_absorption()` - Absorption pattern detection (TODO)
- [x] **Phase 3: API Integration** (2026-01-15)
  - [x] `GET /v1/eh-context?ticker=TSLA` endpoint
  - [x] Support `use_eh` parameter for Yahoo EH data
  - [x] Graceful fallback to minimal mode
  - [ ] Update `/v1/analyze` with `include_eh` parameter (TODO)
  - [ ] Integration tests (TODO)
- [x] **Phase 4: Frontend** (2026-01-15)
  - [x] Add `fetchEHContext` API function and types
  - [x] Add `useEHContext` hook
  - [x] Display EH levels on chart (YC/PMH/PML/AHH/AHL)
    - YC: 橙色实线 (磁吸位)
    - PMH/PML: 紫色虚线 (盘前)
    - AHH/AHL: 靛蓝点线 (盘后)
  - [x] Integrate EH data in detail page
  - [x] EH Context panel (regime, bias, key zones)
    - 显示盘前形态 (Trend Continuation / Gap & Go / Gap Fill / Range)
    - 显示方向偏向 (Bullish / Bearish / Neutral)
    - 显示置信度和关键位
  - [x] Opening protection indicator (first 10 min)
    - 仅在 1m 周期 + 开盘后前10分钟显示
    - 黄色警告条，提示高波动风险
  - [x] i18n for all EH strings (2026-01-15)
- [x] **Phase 4b: EH Integration into Analysis System** (2026-01-15)
  - [x] `inject_eh_levels_as_zones()` in structure.py
  - [x] Add `eh_context` parameter to `analyze_market()` in analyze.py
  - [x] Add EH-influenced playbook logic in playbook.py
  - [x] Add gap fill plans (Plan EH) for gap_fill_bias regime
  - [x] Elevate breakout plans for gap_and_go regime
  - [x] Update ENGINE_SPEC.md with EH integration
  - [x] Update API.md with `/v1/eh-context` endpoint
- [ ] **Phase 5: Testing**
  - [ ] Unit tests for `extended_hours.py`
  - [ ] Integration test with real TwelveData EH data
  - [ ] Test fallback when EH data unavailable

### Data Source Notes
- **Yahoo Finance (MVP 推荐)**: `prepost=True` 免费获取盘前盘后，延迟 15-20 分钟
- TwelveData `prepost=true` parameter for extended hours
- Historical EH data: Free tier (T-1 delay)
- Real-time EH data: Pro plan required ($79/month)
- Fallback: YC/YH/YL only if PM data unavailable

### Acceptance
- EH levels displayed on chart (PMH/PML/YC as key levels)
- Premarket regime classified correctly
- EH context available via API
- Graceful fallback when EH data unavailable

---

## Backlog (Post-MVP)

- [ ] K线 Tooltip 增强 (Volume/RVOL/Effort/Result)
- [ ] Multi-timeframe analysis (1D + 1m alignment)
- [ ] Redis cache for state persistence
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
- [x] Milestone 9: Responsive Design + UI Polish (2026-01-15)
  - [x] 流体排版 (clamp())
  - [x] 动态图表高度
  - [x] 首页简化重设计
  - [x] 设置页面优化
  - [x] 移除页脚
  - [x] 智能图表可视范围
  - [x] 修复价格线重复
- [x] Milestone 11: Extended Hours (EH) Phase 1-4 (2026-01-15)
  - [x] Yahoo EH data source with prepost=True
  - [x] EH levels API endpoint
  - [x] Frontend EH context display
  - [x] EH levels on chart
  - [x] EH integration into analysis system
  - [x] EH-influenced playbook generation
  - [x] i18n for EH strings
  - [x] Documentation updates (API.md, ENGINE_SPEC.md)
