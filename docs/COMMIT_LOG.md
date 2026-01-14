# Commit Log

Detailed record of each GitHub commit with context and changes.

---

## [158f198] - 2026-01-13

**Message:** `refactor: migrate to open-source local Docker tool`

**Milestone:** N/A - Major Architecture Change

**Changes:**
| Type | File | Description |
|------|------|-------------|
| Rename | `Docs/` → `docs/` | Lowercase convention for GitHub |
| Modify | `MASTER_SPEC.md` | Local tool positioning, user responsibilities |
| Modify | `docs/PRD.md` | Docker deployment, user responsibilities |
| Modify | `README.md` | Docker quickstart guide |
| Modify | `docs/ARCHITECTURE.md` | Docker topology diagram |
| Modify | `docs/PROVIDER.md` | Rate limits, provider switching guide |
| Add | `docker-compose.yml` | Docker orchestration |
| Add | `apps/api/Dockerfile` | API container |
| Add | `apps/web/Dockerfile` | Web container |
| Add | `docs/DEPLOYMENT.md` | Docker setup and troubleshooting |
| Add | `.env.example` | Environment configuration template |
| Add | `LICENSE` | MIT License |
| Add | `Makefile` | Common commands |
| Add | `apps/api/tests/` | API test suite (29 tests) |

**Result:** Project repositioned as open-source local Docker tool. Users run on their own machine and manage their own data sources.

---

## [02ba430] - 2026-01-13

**Message:** `feat(api): implement market data provider with yfinance (Milestone 1)`

**Milestone:** 1 - Market Data

**Changes:**
| Type | File | Description |
|------|------|-------------|
| Add | `apps/api/src/providers/__init__.py` | Provider package with exports |
| Add | `apps/api/src/providers/base.py` | Abstract provider interface and Bar dataclass |
| Add | `apps/api/src/providers/yfinance_provider.py` | Yahoo Finance implementation |
| Add | `apps/api/src/cache.py` | Memory cache with TTL |
| Add | `apps/api/src/config.py` | Settings from environment |
| Modify | `apps/api/src/main.py` | Implement /v1/bars endpoint |
| Modify | `apps/api/src/__init__.py` | Add Chinese comments |
| Modify | `packages/core/src/__init__.py` | Add Chinese comments |
| Modify | `packages/core/src/types.py` | Add Chinese comments |
| Modify | `packages/core/tests/__init__.py` | Add Chinese comments |
| Modify | `apps/web/src/pages/_app.tsx` | Add Chinese comments |
| Modify | `apps/web/src/pages/index.tsx` | Add Chinese comments |
| Modify | `apps/web/src/pages/t/[ticker].tsx` | Add Chinese comments |
| Modify | `Claude.md` | Add Chinese comment requirement |

**API Added:**
- `GET /v1/bars?ticker=TSLA&tf=1m&window=1d` - Fetch OHLCV K-line data

**Result:** Market data API functional. Can fetch 1m/5m/1d bars from Yahoo Finance with caching.

---

## [bfe86b9] - 2026-01-13

**Message:** `docs: add commit log for tracking GitHub updates`

**Milestone:** N/A - Documentation

**Changes:**
| Type | File | Description |
|------|------|-------------|
| Add | `docs/COMMIT_LOG.md` | Detailed history of all commits |
| Modify | `Claude.md` | Added commit log workflow rules and documentation index entry |

**Result:** Commit log system established for tracking all GitHub updates.

---

## [246bcca] - 2026-01-13

**Message:** `feat: initialize monorepo structure (Milestone 0)`

**Milestone:** 0 - Repo & Infrastructure

**Changes:**
| Type | File | Description |
|------|------|-------------|
| Add | `package.json` | Root monorepo config with workspace scripts |
| Add | `.gitignore` | Ignore patterns for Node, Python, IDE, OS |
| Add | `apps/web/package.json` | Next.js dependencies |
| Add | `apps/web/tsconfig.json` | TypeScript config |
| Add | `apps/web/next.config.js` | Next.js config |
| Add | `apps/web/src/pages/index.tsx` | Dashboard with search box |
| Add | `apps/web/src/pages/_app.tsx` | App wrapper |
| Add | `apps/web/src/pages/t/[ticker].tsx` | Detail page scaffold |
| Add | `apps/web/.env.example` | Environment template |
| Add | `apps/api/pyproject.toml` | Python project config |
| Add | `apps/api/requirements.txt` | Python dependencies |
| Add | `apps/api/src/__init__.py` | Package init |
| Add | `apps/api/src/main.py` | FastAPI app with placeholder endpoints |
| Add | `apps/api/.env.example` | Environment template |
| Add | `packages/core/pyproject.toml` | Core engine project config |
| Add | `packages/core/src/__init__.py` | Package init |
| Add | `packages/core/src/types.py` | Type definitions (Bar, Zone, Signal, etc.) |
| Add | `packages/core/tests/__init__.py` | Test package init |

**Result:** Monorepo structure ready for development.

---

## [ec426df] - 2026-01-13

**Message:** `docs(claude): add explain-before-coding workflow rule`

**Milestone:** N/A - Documentation

**Changes:**
| Type | File | Description |
|------|------|-------------|
| Modify | `Claude.md` | Added rules 1-2: explain before coding, ask for requirements first |
| Modify | `Claude.md` | Added Step A workflow with example |

**Result:** Claude now explains each step and asks for prerequisites before coding.

---

## [dd6d8c7] - 2026-01-13

**Message:** `docs: restructure and enhance documentation system`

**Milestone:** N/A - Documentation

**Changes:**
| Type | File | Description |
|------|------|-------------|
| Modify | `MASTER_SPEC.md` | Restructured as concise project constitution |
| Modify | `docs/ENGINE_SPEC.md` | Fixed format, added tables and code blocks |
| Modify | `docs/API.md` | Added complete schema definitions, error codes |
| Modify | `docs/ARCHITECTURE.md` | Added ASCII diagrams, data flow details |
| Modify | `docs/I18N.md` | Updated for English-only MVP |
| Modify | `docs/TODO.md` | Added sub-tasks and acceptance criteria |
| Modify | `docs/CHANGELOG.md` | Recorded documentation changes |
| Modify | `Claude.md` | Updated document index |
| Add | `docs/PROVIDER.md` | Data provider integration spec |
| Add | `docs/CONFIG.md` | Environment variables spec |

**Result:** Documentation system restructured with clear separation of concerns.

---

## [7f4a750] - 2026-01-13

**Message:** `DOCS UPDATE`

**Milestone:** N/A - Initial Documentation

**Changes:**
- Initial documentation set created by ChatGPT

---

## [3b27a05] - 2026-01-13

**Message:** `Initial commit`

**Milestone:** N/A

**Changes:**
- Repository initialized
