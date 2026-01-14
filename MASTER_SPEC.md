# KLineLens — MASTER SPEC (Project Constitution)

> This document is the **project constitution** — high-level vision, principles, and scope.
> For implementation details, see the linked documents in Section 6.
> Any implementation must follow this spec. Any new feature must update docs first.

---

## 1. Project Vision

KLineLens is an **open-source local market structure analysis terminal** that:
- Continuously analyzes OHLCV bars and detects market structure
- Infers behavior probabilities with traceable evidence
- Maintains a stateful narrative timeline (never "forgets")
- Outputs structured reports for UI rendering
- **Runs entirely on user's local machine via Docker**

**Core Philosophy:**
- Deterministic + Explainable (same input → same output)
- Evidence-based (every inference has traceable data points)
- Conditional playbooks only (no direct buy/sell advice)
- **Self-hosted**: User controls data source and API keys

---

## 2. Project Type: Open-Source Local Tool

### 2.1 What We Provide
| Component | Description |
|-----------|-------------|
| Analysis Engine | Market structure detection, behavior inference |
| REST API | FastAPI backend serving analysis results |
| Web UI | Next.js frontend for visualization |
| Docker Setup | One-command local deployment |

### 2.2 What User Provides
| Component | Description |
|-----------|-------------|
| Docker Runtime | Docker Desktop on local machine |
| Data Source Config | Choose provider (yahoo default, optional: polygon/twelvedata) |
| API Keys (optional) | If using paid providers, user supplies keys |

### 2.3 Responsibility Boundary
- **We are responsible for**: Engine accuracy, API stability, UI functionality
- **User is responsible for**: Provider rate limits, API key costs, data availability
- **We do NOT provide**: Hosted service, uptime guarantees, data storage

---

## 3. Scope Boundaries

### 3.1 MVP (Must Ship First)
| Category | Items |
|----------|-------|
| Deployment | Docker Compose one-command startup |
| Pages | `/` Dashboard, `/t/{ticker}` Detail, `/settings` Settings |
| Structure | Swing points, Support/Resistance zones, Regime (trend/range), Breakout FSM |
| Behavior | 5-class probabilities + evidence pack |
| State | Timeline tracking changes across refresh cycles |
| Playbook | Plan A/B (If/Target/Invalidation/Risk) |
| Refresh | Auto-refresh every 60s (configurable) |
| Provider | Yahoo Finance (yfinance) - free, no API key |

### 3.2 Explicitly NOT in MVP
- Login / user accounts
- Cloud-hosted service
- Database persistence (in-memory only)
- News / social sentiment (Reddit/X)
- L2 orderbook / tick-by-tick order flow
- Backtesting UI
- Embeddings / LLM narration
- Multi-language (English only for MVP)

### 3.3 Future Roadmap (V1/V2)
- V1: SQLite persistence, Redis cache, WebSocket streaming, Polygon/TwelveData providers
- V2: LLM narration layer, case library embeddings, multi-timeframe alignment

---

## 4. Engineering Principles (Non-negotiable)

| Principle | Description |
|-----------|-------------|
| **Determinism** | Same bars → same report. No randomness in core engine. |
| **Explainability** | Every behavior output must contain evidence (bar_time + metrics). |
| **No Trading Advice** | Only conditional playbooks with explicit invalidation. |
| **Docs-First** | Update docs BEFORE implementing significant changes. |
| **Key-Based Text** | Backend outputs `*_key` fields; frontend maps to display text. |
| **Local-First** | No cloud dependencies for MVP. Everything runs locally. |

---

## 5. Acceptance Criteria (MVP Done When)

- [ ] `docker compose up` starts both API and Web successfully
- [ ] User can search ticker and open detail page
- [ ] 1m chart shows zones + markers
- [ ] Behavior probabilities are stable and reasonable over time
- [ ] Timeline records meaningful evolution (not noise)
- [ ] Playbook always provides Plan A/B with invalidation
- [ ] No crashes on invalid ticker / no data / rate limits
- [ ] Provider status visible (current provider, last update, errors)

---

## 6. Documentation Index (Source of Truth)

| Document | Purpose |
|----------|---------|
| `docs/PRD.md` | Product requirements, user scenarios, feature list |
| `docs/UX_SPEC.md` | Page layout, card order, interaction rules |
| `docs/API.md` | REST endpoints, request/response schema, errors |
| `docs/ENGINE_SPEC.md` | Algorithm logic: features, structure, behavior, FSM |
| `docs/ARCHITECTURE.md` | System architecture, data flow, Docker topology |
| `docs/DEPLOYMENT.md` | Docker setup, quickstart, troubleshooting |
| `docs/PROVIDER.md` | Data provider integration, rate limits, switching |
| `docs/CONFIG.md` | Environment variables and configuration |
| `docs/PLAN.md` | Development milestones |
| `docs/TODO.md` | Task tracking |
| `docs/TEST_PLAN.md` | Testing strategy |
| `docs/DISCLAIMER.md` | Risk statement |

**Rule:** If code conflicts with docs, docs win (until docs are updated).

---

## 7. Output Contract (Report Schema Summary)

Backend returns **structured JSON only** — no large natural language paragraphs.

Required top-level fields:
```
AnalysisReport {
  ticker, timeframe, generated_at,
  market_state: { regime, confidence },
  zones: { support[], resistance[] },
  signals[],
  behavior: { probabilities, dominant, evidence[] },
  timeline[],
  playbook[]
}
```

Full schema definition: see `docs/API.md`.

---

## 8. Quick Start (Docker)

```bash
# 1. Clone repository
git clone https://github.com/user/klinelens.git
cd klinelens

# 2. Copy environment template
cp .env.example .env

# 3. Start services
docker compose up --build

# 4. Open browser
open http://localhost:3000
```

See `docs/DEPLOYMENT.md` for detailed instructions.
