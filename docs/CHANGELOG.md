# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- N/A (preparing for 0.2.0 release)

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A

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
