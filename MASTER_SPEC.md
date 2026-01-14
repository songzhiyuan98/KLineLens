# KLineLens — MASTER SPEC (Project Constitution)

> This document is the **project constitution** — high-level vision, principles, and scope.
> For implementation details, see the linked documents in Section 5.
> Any implementation must follow this spec. Any new feature must update docs first.

---

## 1. Project Vision

KLineLens is a **minimalist professional trading terminal** that:
- Continuously analyzes OHLCV bars and detects market structure
- Infers behavior probabilities with traceable evidence
- Maintains a stateful narrative timeline (never "forgets")
- Outputs structured reports for UI rendering

**Core Philosophy:**
- Deterministic + Explainable (same input → same output)
- Evidence-based (every inference has traceable data points)
- Conditional playbooks only (no direct buy/sell advice)

---

## 2. Scope Boundaries

### 2.1 MVP (Must Ship First)
| Category | Items |
|----------|-------|
| Pages | `/` Dashboard, `/t/{ticker}` Detail, `/settings` Settings |
| Structure | Swing points, Support/Resistance zones, Regime (trend/range), Breakout FSM |
| Behavior | 5-class probabilities + evidence pack |
| State | Timeline tracking changes across refresh cycles |
| Playbook | Plan A/B (If/Target/Invalidation/Risk) |
| Refresh | Auto-refresh every 60s |
| i18n | Key-based text, 中文/English toggle |

### 2.2 Explicitly NOT in MVP
- Login / user accounts
- News / social sentiment (Reddit/X)
- L2 orderbook / tick-by-tick order flow
- Backtesting UI
- Embeddings / LLM narration

### 2.3 Future Roadmap (V1/V2)
- V1: Multi-timeframe alignment, Redis cache, WebSocket streaming, snapshots/replay
- V2: LLM narration layer on top of deterministic JSON, case library embeddings

---

## 3. Engineering Principles (Non-negotiable)

| Principle | Description |
|-----------|-------------|
| **Determinism** | Same bars → same report. No randomness in core engine. |
| **Explainability** | Every behavior output must contain evidence (bar_time + metrics). |
| **No Trading Advice** | Only conditional playbooks with explicit invalidation. |
| **Docs-First** | Update docs BEFORE implementing significant changes. |
| **Key-Based Text** | Backend outputs `*_key` fields; frontend maps to zh/en. |

---

## 4. Acceptance Criteria (MVP Done When)

- [ ] User can search ticker and open detail page
- [ ] 1m chart shows zones + markers
- [ ] Behavior probabilities are stable and reasonable over time
- [ ] Timeline records meaningful evolution (not noise)
- [ ] Playbook always provides Plan A/B with invalidation
- [ ] Language toggle works globally
- [ ] No crashes on invalid ticker / no data / rate limits

---

## 5. Documentation Index (Source of Truth)

| Document | Purpose |
|----------|---------|
| `Docs/PRD.md` | Product requirements, user scenarios, feature list |
| `Docs/UX_SPEC.md` | Page layout, card order, interaction rules |
| `Docs/API.md` | REST endpoints, request/response schema, errors |
| `Docs/ENGINE_SPEC.md` | Algorithm logic: features, structure, behavior, FSM |
| `Docs/ARCHITECTURE.md` | System architecture, data flow, caching strategy |
| `Docs/PROVIDER.md` | Data provider integration spec |
| `Docs/CONFIG.md` | Environment variables and configuration |
| `Docs/I18N.md` | Language toggle and key-based text strategy |
| `Docs/PLAN.md` | Development milestones |
| `Docs/TODO.md` | Task tracking |
| `Docs/TEST_PLAN.md` | Testing strategy |
| `Docs/DISCLAIMER.md` | Risk statement |

**Rule:** If code conflicts with Docs, Docs win (until Docs are updated).

---

## 6. Output Contract (Report Schema Summary)

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

Full schema definition: see `Docs/API.md`.
