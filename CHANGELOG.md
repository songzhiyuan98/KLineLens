# Changelog

All notable changes to KLineLens will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.8.0] - 2025-01-16

### Added
- **0DTE Trading Strategy Module**
  - State machine: WAIT → WATCH → ARMED → ENTER → HOLD → TRIM → EXIT
  - 4 entry setups: R1 Breakout, S1 Breakdown, YC Reclaim, R1 Reject
  - Underlying-level trade plans (no options quotes required)
  - Position management with soft/hard stop conditions

- **Extended Hours (EH) System**
  - Pre-market and after-hours data integration
  - Key level extraction: PMH/PML, AHH/AHL, Yesterday Close
  - Gap analysis for opening context
  - Time-aware LLM narratives

- **Real-time Features**
  - WebSocket-based watchlist with live updates
  - Auto-refresh with configurable intervals
  - Multi-ticker monitoring

- **Documentation**
  - All documentation translated to English
  - Added DEV_QUICKSTART.md for contributors
  - Added GitHub Issue/PR templates

### Changed
- Strategy type selector in settings (Playbook/0DTE)
- Improved responsive design for mobile devices
- Enhanced fullscreen chart support

### Fixed
- Docker build issues on Apple Silicon
- Provider rate limiting edge cases

---

## [0.7.0] - 2025-01-10

### Added
- Responsive design for all screen sizes
- Homepage redesign with cleaner layout
- Settings optimization with persistent storage

### Changed
- Major UI improvements
- Fullscreen support for charts
- Better typography and spacing

---

## [0.6.0] - 2025-01-05

### Added
- Terminal-style dark mode UI
- AI interpretation via GPT-4/Gemini
- Multi-language support (EN/ZH)
- Volume panel with RVOL visualization

### Changed
- Evidence cards with visual indicators
- Cleaner UI layout

---

## [0.5.0] - 2025-01-01

### Added
- Backtest evaluation system
- 98.9% breakout identification accuracy
- Detailed evaluation documentation

---

## [0.4.0] - 2024-12-28

### Added
- Docker environment support
- Complete web terminal UI
- Core analysis engine

### Fixed
- Core module import issues in Docker

---

## [0.3.0] - 2024-12-25

### Added
- FastAPI backend with REST endpoints
- Market structure detection
- Auto S/R zone calculation

---

## [0.2.0] - 2024-12-20

### Added
- Next.js frontend foundation
- Basic chart component
- Provider integration (Yahoo Finance)

---

## [0.1.0] - 2024-12-15

### Added
- Initial project structure
- Monorepo setup with apps/api, apps/web, packages/core
- MIT License

---

[0.8.0]: https://github.com/songzhiyuan98/KLineLens/releases/tag/v0.8.0
[0.7.0]: https://github.com/songzhiyuan98/KLineLens/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/songzhiyuan98/KLineLens/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/songzhiyuan98/KLineLens/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/songzhiyuan98/KLineLens/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/songzhiyuan98/KLineLens/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/songzhiyuan98/KLineLens/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/songzhiyuan98/KLineLens/releases/tag/v0.1.0
