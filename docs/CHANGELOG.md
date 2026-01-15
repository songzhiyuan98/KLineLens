# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

N/A

---

## [0.7.0] - 2026-01-15

### Added
- **Responsive Design** - Fluid typography and dynamic layouts:
  - CSS `clamp()` for all font sizes (scales with viewport width)
  - Dynamic chart height (280-550px, ~45% of viewport height)
  - Right panel fonts scale proportionally on larger screens
  - Settings page responsive typography

- **Smart Chart Visible Range** - Timeframe-specific context windows:
  - 1m: 120 bars (~2 hours) - execution level
  - 5m: 78 bars (~1 trading day) - structure level
  - 1d: 20 bars (~1 month) - trend level

- **Homepage Redesign** - Minimal search-focused design:
  - Pure black/white color scheme
  - Large centered search box with rounded corners (12px)
  - Recent tickers from localStorage (max 6)
  - Removed category-based recommendations

### Changed
- **Settings Page** - Simplified modern design:
  - Removed Card components, using native sections
  - Modern button-style language toggle (selected = black bg)
  - Shorter disclaimer text (CN/EN)
- **Layout** - Removed footer from all pages
- **Disclaimer** - Simplified text:
  - CN: "本工具仅用于技术分析学习，不构成任何投资建议。市场有风险，投资需谨慎。"
  - EN: "For educational purposes only. Not financial advice. Trade at your own risk."

### Fixed
- **Price Lines Duplication** - Fixed R1/R2/S1/S2 lines duplicating when switching timeframes
  - Added `priceLinesRef` to track and clean up old lines before creating new ones

### Technical
- `[ticker].tsx`: Added fluid typography scale `F` object with 6 size levels
- `[ticker].tsx`: Added `chartHeight` state with viewport-based calculation
- `CandlestickChart.tsx`: Added `priceLinesRef` for price line cleanup
- `CandlestickChart.tsx`: Smart visible range using `setVisibleLogicalRange()`
- `index.tsx`: Complete rewrite for minimal homepage with localStorage recent tickers
- `settings.tsx`: Rewritten with responsive design
- `Layout.tsx`: Removed footer section

---

## [0.6.0] - 2026-01-14

### Added
- **v4 Terminal UI** - Professional Bloomberg-style design:
  - **Status Strip**: Smaller font, Volume indicator as colored dot
  - **Decision Line**: Bloomberg-style Action/Trigger/Risk display in Summary
    - Action: WAIT / WATCH / CONFIRM / AVOID
    - Trigger: Specific condition description
    - Risk: Low confidence warning (optional)
  - **Zone Hierarchy**: Top1 solid line + label, Top2 dashed, Top3+ dotted lighter
  - **ATR Distance**: Key Zones table shows ATR distance (hover for %)
  - **Short TF Warnings**: 1m/5m timeframes show noise warning badges
    - Behavior: "短周期噪音较高" / "Short TF high noise"
    - Playbook: "ENTRY" badge indicating entry-only use
  - **low conf Tooltip**: Hover explanation for low confidence

### Changed
- **Section Titles**: Smaller (0.5rem), lighter gray (#b0b0b0), tighter spacing
- **Section Dividers**: More subtle (1px rgba(0,0,0,0.04))
- **Status Strip**: Smaller font (0.5625rem), lighter colors (#b0b0b0/#888888)
- **i18n**: Full Chinese support for all new UI elements
  - Decision Line labels (Action/Trigger/Risk)
  - 3-Factor breakout labels (收盘确认 ×2, etc.)
  - Zone types (阻/支)
  - Noise warnings

### Technical
- `CandlestickChart.tsx`: Zone rendering now hierarchical (Top1/Top2/Top3+ different styles)
- `[ticker].tsx`: Added `estimatedATR` calculation, `getDecisionLine()` function
- `i18n.tsx`: Added 20+ new translation keys for v4 UI

---

## [0.5.0] - 2026-01-14

### Added
- **TwelveData Provider** (Recommended):
  - Real-time market data with ~170ms latency
  - Reliable 1-minute volume data
  - Free tier: 800 credits/day, 8 requests/minute
  - Global market coverage (US, crypto, forex)
  - `apps/api/src/providers/twelvedata_provider.py`

- **Core Engine Enhancements** (`packages/core/src/`):
  - `features.py`:
    - `calculate_rvol()` - Relative Volume (volume / MA30)
    - `calculate_effort_result()` - VSA Effort vs Result
    - `get_volume_quality()` - Volume data quality assessment (reliable/partial/unavailable)
  - `structure.py`:
    - Zone Strength 多维评分: `(0.3×tests) + (0.3×rejections) + (0.25×reaction) + (0.15×recency)`
    - 3-Factor Breakout FSM: Structure (2 closes) + Volume (RVOL ≥ 1.8) + Result (≥ 0.6 ATR)
  - `behavior.py`:
    - VSA Absorption detection (High Effort + Low Result)
    - Evidence types: VOLUME_SPIKE, REJECTION, SWEEP, ABSORPTION, BREAKOUT
    - Evidence severity levels: low, med, high
  - `timeline.py`:
    - Soft Events: zone_approached, zone_tested, zone_rejected, zone_accepted
    - Wyckoff Events: spring, upthrust
    - VSA Events: absorption_clue, volume_spike, volume_dryup
  - `models.py`:
    - Zone: added `rejections`, `last_reaction`, `last_test_time`
    - Signal: added `bar_index`, `volume_quality`
    - Evidence: added `type`, `severity`, `bar_index`, VSA metrics
    - TimelineEvent: added `bar_index`, `severity`
    - AnalysisReport: added `volume_quality`
  - `analyze.py`:
    - Integrated RVOL, Effort, Result into analysis pipeline
    - Added `result_threshold` parameter (default 0.6)
    - Volume quality assessment in final report

### Changed
- **ENGINE_SPEC.md** - Major algorithm specification update:
  - Added RVOL (Relative Volume) with N/A fallback handling
  - Added Effort vs Result (VSA core indicator) - 4 quadrant interpretation
  - Enhanced Zone Strength scoring (tests, rejections, reaction magnitude, recency)
  - Updated Breakout FSM with 3-factor confirmation (Structure + Volume + Result)
  - Enhanced Evidence System with click-to-locate anchors (bar_index, type, severity)
  - Added Soft Events to Timeline (zone_approached, zone_tested, spring, upthrust, absorption_clue, volume_spike/dryup)
  - Added Multi-Timeframe Logic section (future enhancement)
  - Added Algorithm Summary with product description (EN/CN)
  - Added Key Terms appendix (RVOL, VSA, Wyckoff, FSM, Evidence, Effort, Result)
- **API.md** - Schema enhancements:
  - Added `volume_quality` field to AnalysisReport and Signal
  - Enhanced Zone schema (rejections, last_reaction, last_test_time)
  - Enhanced Signal schema (bar_index, volume_quality)
  - Enhanced Evidence schema (type, severity, bar_index, effort/result metrics)
  - Enhanced TimelineEvent schema (bar_index, severity)
  - Added soft event types (zone_*, spring, upthrust, absorption_clue, volume_*)
  - Added Volume Quality Handling section
- **PROVIDER.md** - Updated for TwelveData:
  - TwelveData as recommended provider
  - Provider comparison table
  - Volume quality impact on analysis
  - Updated troubleshooting section
- **docker-compose.yml** - Added TWELVEDATA_API_KEY environment variable
- **config.py** - Default provider changed to TwelveData

---

## [0.4.0] - 2026-01-14

### Added
- **国际化 (i18n)**:
  - 中英文双语支持
  - Settings 页面语言切换
  - 所有 UI 文本通过 key 翻译
  - localStorage 持久化语言偏好
- **Volume 面板**:
  - K 线图下方显示成交量柱
  - 30 周期 Volume MA 均线（橙色）
  - 量比 (Volume Ratio) 计算和显示
- **Evidence 可视化**:
  - 点击 Evidence 定位到对应 K 线
  - 图表高亮标记（橙色箭头）
  - 自动滚动到目标位置
- **Breakout Status 卡片**:
  - 突破状态显示（观望/尝试/确认/假突破）
  - 量比与阈值对比
  - Confirm Closes 显示 (2/2, 1/2, -)
- **Signals 面板**:
  - 显示最近 5 个信号
  - 信号时间戳
- **数据源扩展**:
  - Alpaca Provider（免费，有成交量）
  - Alpha Vantage Provider（高质量分钟数据）
  - 动态 Provider 切换

### Changed
- **UI 简化**:
  - 移除卡片边框和背景
  - 减少颜色使用（统一灰色系）
  - 移除滚动条，限制显示数量
  - 信号显示时间而非彩色标签
  - 时间线使用统一灰色圆点
- 详情页全中文化 UI
- Timeline 不再显示原始 key（如 event.xxx）

### Fixed
- 信号类型翻译（breakout_attempt → 尝试突破）
- Timeline reason 过滤原始 key

---

## [0.3.0] - 2026-01-14

### Added
- **Web Terminal** (`apps/web/`):
  - Dashboard page with ticker search and popular tickers
  - Detail page (`/t/[ticker]`) with full analysis display
  - CandlestickChart component using TradingView's lightweight-charts
  - Zone overlays (support/resistance price lines)
  - 5 analysis cards: MarketState, Behavior, Evidence, Timeline, Playbook
  - Timeframe switcher (1m, 5m, 1d)
  - Auto-refresh every 60s with SWR
  - Loading and error states
  - Settings page placeholder
  - Layout component with header/footer
  - Global styles

### Changed
- `apps/web/package.json` - Added lightweight-charts, swr dependencies

---

## [0.2.0] - 2026-01-13

### Added
- **Core Analysis Engine** (`packages/core/src/`):
  - `features.py` - ATR, volume ratio, wick ratios, efficiency calculations
  - `structure.py` - Swing point detection, zone clustering, regime classification, BreakoutFSM
  - `behavior.py` - 5 Wyckoff behavior scoring (accumulation, shakeout, markup, distribution, markdown), softmax probabilities, evidence generation
  - `timeline.py` - TimelineManager state machine for event emission
  - `playbook.py` - Conditional trading plan generation (Plan A/B)
  - `analyze.py` - Main orchestrator function `analyze_market()`
  - `models.py` - Core dataclasses (Bar, Zone, Signal, Evidence, TimelineEvent, PlaybookPlan, MarketState, Behavior, AnalysisReport)
- **API Integration**:
  - `POST /v1/analyze` endpoint with full AnalysisReport response
  - Core-API module integration with namespace isolation
- **Unit Tests** (79 tests total):
  - `packages/core/tests/` - 42 core engine tests
  - `apps/api/tests/test_analyze.py` - 8 API integration tests
  - Synthetic data generators for uptrend, downtrend, range, breakout, shakeout scenarios

### Changed
- `apps/api/requirements.txt` - Added `python-dateutil`, `numpy` dependencies
- `docs/TODO.md` - Updated with completed milestones 0-3

---

## [0.1.0] - 2026-01-13

### Added
- `docs/PROVIDER.md` - Data provider integration spec (yfinance, future providers)
- `docs/CONFIG.md` - Environment variables and configuration strategy
- Detailed sub-tasks and acceptance criteria in `docs/TODO.md`
- **Market Data API** (`apps/api/`):
  - `GET /v1/bars` endpoint for OHLCV data
  - YFinanceProvider with timeframe support (1m, 5m, 1d)
  - In-memory cache with TTL
  - Error handling (400, 404, 429, 502)
- **Docker Support**:
  - `Dockerfile` for API container
  - `docker-compose.yml` for development

### Changed
- `MASTER_SPEC.md` - Restructured as concise project constitution (removed duplication with sub-docs)
- `docs/ENGINE_SPEC.md` - Fixed format issues, improved structure with tables and code blocks
- `docs/API.md` - Added complete schema definitions, error codes, example requests
- `docs/ARCHITECTURE.md` - Added ASCII diagrams, detailed data flow, caching strategy
- `docs/I18N.md` - Updated for MVP English-only decision
- `CLAUDE.md` - Updated with new document index and workflow

### Fixed
- Removed malformed markdown in `ENGINE_SPEC.md` (extra code block markers)
- Completed JSON code blocks in `API.md`

---

## [0.0.1] - 2026-01-13

### Added
- Initial documentation set:
  - `MASTER_SPEC.md` - Project constitution
  - `docs/PRD.md` - Product requirements
  - `docs/UX_SPEC.md` - UI specification
  - `docs/API.md` - API contract
  - `docs/ENGINE_SPEC.md` - Algorithm specification
  - `docs/ARCHITECTURE.md` - System architecture
  - `docs/I18N.md` - Language strategy
  - `docs/PLAN.md` - Development milestones
  - `docs/TODO.md` - Task tracking
  - `docs/BUGS.md` - Bug tracking template
  - `docs/TEST_PLAN.md` - Testing strategy
  - `docs/DISCLAIMER.md` - Risk statement
  - `CLAUDE.md` - Collaboration guide
  - `README.md` - Project overview
