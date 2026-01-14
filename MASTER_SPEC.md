# KLineLens — MASTER SPEC (Single Source of Truth)

> This document is the **project constitution**.
> Any implementation must follow this spec. Any new feature must update this spec first.

---

## 1) Project Vision
KLineLens is a minimalist, professional trading terminal that:
- continuously analyzes OHLCV bars (1m/5m/1d)
- detects market structure (trend/range + key zones + breakout/fakeout)
- infers trader-behavior probabilities (accumulation/shakeout/markup/distribution/markdown)
- maintains a **stateful narrative timeline** so analysis never “forgets”
- outputs structured reports (JSON) for UI rendering and future extensions

Core philosophy:
- deterministic + explainable
- evidence-based
- conditional playbooks (no direct buy/sell calls)

---

## 2) Scope & Roadmap
### 2.1 MVP Scope (must ship first)
Pages:
- `/` dashboard: big search box
- `/t/{ticker}` detail: chart + analysis panel
- `/settings`: language toggle (中文/English)

Features:
- Pull OHLCV bars for ticker (provider)
- Structure engine:
  - swing points
  - support/resistance zones
  - regime classification (trend/range)
  - breakout/fakeout state machine
- Behavior inference:
  - 5-class behavior probabilities
  - evidence pack (max 3 items)
- Stateful timeline:
  - tracks changes across refresh cycles
- Playbook:
  - Plan A/B (If/Target/Invalidation/Risk)
- Auto refresh every 60s

Explicitly NOT in MVP:
- login / user accounts
- news / reddit sentiment
- L2 orderbook / tick-by-tick true orderflow
- backtesting UI
- embeddings / LLM

### 2.2 V1 (post-MVP)
- multi-timeframe alignment (1D + 1m execution)
- snapshots + replay
- redis cache / websocket streaming
- more robust zones + range box detection

### 2.3 V2 (optional AI layer)
- LLM narration built on top of deterministic report JSON
- embeddings for “case library” retrieval (pattern memory)
- personalized user preferences

---

## 3) UX / User Flow
### 3.1 Dashboard (/)
- input ticker
- click search -> navigate to `/t/{ticker}`
- top-right settings entry

### 3.2 Detail Page (/t/{ticker})
Layout: minimalist professional terminal
- Left: chart (candles + volume + overlays)
- Right: analysis cards

Chart must include:
- candles + volume
- support/resistance zones overlay
- breakout/fakeout markers

Analysis panel cards (fixed order):
1) Market State
2) Key Zones
3) Behavior Probabilities
4) Evidence
5) Timeline
6) Playbook (Plan A / Plan B)

Refresh:
- every 60 seconds rerun analysis
- show last updated time

### 3.3 Settings (/settings)
- language selection
- persistent storage: localStorage
- applies site-wide immediately

---

## 4) Core Output Standard (Report Schema)
### 4.1 Key rule: backend returns STRUCTURED JSON
No large natural language paragraph output.

Backend may output keys:
- `reason_key`, `note_key`, `risk_key`, `if_key`
Frontend renders localized text.

### 4.2 AnalysisReport (required fields)
- ticker, timeframe, generated_at
- market_state: regime + confidence
- zones: support/resistance list
- signals: breakout/fakeout etc
- behavior: probabilities + dominant + evidence[]
- timeline: events[] (ts + event_type + delta + reason_key)
- playbook: PlanA/PlanB (conditional)

---

## 5) Financial Logic: Engine Modules
### 5.1 Feature Layer
Compute from OHLCV:
- ATR(14)
- SMA volume + volume_ratio
- wick/body ratios
- move efficiency: body / volume

### 5.2 Structure Detection
- Swing points (fractal window)
- Zones clustering:
  - outputs zones as price BANDS (low-high)
  - score zones by touches + reaction strength
- Regime classification:
  - HH/HL -> uptrend
  - LL/LH -> downtrend
  - else range
- Breakout state machine:
  - attempt / confirmed / fakeout
  - volume confirmation required

### 5.3 Behavior Inference (5-class)
Output probabilities over:
- accumulation
- shakeout
- markup
- distribution
- markdown

Inference must be:
- evidence-based
- probability-style (no absolute claims)

### 5.4 Timeline State Machine
Maintain per ticker+tf state memory:
- last regime
- last dominant behavior + probs
- last breakout state
Write event only if meaningful change:
- dominant changes
- delta >= threshold
- breakout state changes
- regime changes

### 5.5 Playbook Generation
Always output:
- Plan A (usually breakout continuation)
- Plan B (usually breakdown / invalidation scenario)

Each plan must include:
- If (conditional trigger)
- Target
- Invalidation
- Risk key

---

## 6) System Architecture
### 6.1 Monorepo layout
kline-lens/
  apps/web
  apps/api
  packages/core
  docs
  infra

### 6.2 Services
- web: Next.js
- api: FastAPI
- core: pure python library

### 6.3 Data flow
1) web calls API: /bars -> /analyze
2) api pulls bars from provider (cached)
3) core generates report JSON
4) web renders chart overlays + cards

Caching:
- MVP: in-memory TTL cache
- later: Redis shared cache

State storage:
- MVP: in-memory dict per instance
- later: Redis state store

---

## 7) Engineering Rules (Non-negotiable)
- deterministic report: same bars -> same report
- explainability: behavior outputs must contain evidence
- no direct trading advice: only conditional playbooks
- docs-first: update docs before large changes
- every new algorithm or architecture change must add doc

---

## 8) Acceptance Criteria (MVP)
MVP done when:
- user can search ticker and open detail page
- 1m chart shows zones + markers
- behavior probabilities show stable and reasonable changes over time
- timeline records meaningful evolution
- playbook always provides Plan A/B with invalidation
- language toggle works globally
- no crashes on invalid ticker / no data / rate limits
