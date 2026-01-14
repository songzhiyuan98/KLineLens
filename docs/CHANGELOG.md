# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

N/A

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
