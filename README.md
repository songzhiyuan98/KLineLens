# KLineLens

KLineLens is a minimalist market-structure terminal for **OHLCV-based** analysis (no login, no noise).  
Type a ticker → open a detail page → get **structure + behavior probabilities + evidence + timeline + conditional playbook**, updated periodically.

> ⚠️ Disclaimer: Not financial advice. This tool provides rule-based analysis and probability-style interpretations.

---

## What it does (MVP)
- **Dashboard**: one big search box → enter ticker → go to detail page
- **Detail page**:
  - Candlestick chart (OHLC) + Volume
  - Support/Resistance **zones**
  - Breakout / Fakeout markers
  - Market regime (trend/range) + confidence
  - Behavior probabilities (Accumulation / Shakeout / Markup / Distribution / Markdown)
  - Evidence pack (traceable to bar_time + computed metrics)
  - Stateful timeline (recent structural/behavior changes)
  - Conditional playbook (Plan A/B with invalidation)

- **Settings**:
  - Manual language toggle: 中文 / English (site-wide)

---

## Repo layout
kline-lens/
apps/
web/ # Next.js UI (dashboard/detail/settings)
api/ # FastAPI REST endpoints
packages/
core/ # Pure Python engine (structure/behavior/state/report)
Docs/ # Specs & documentation (source of truth)
infra/ # Local dev infra (docker-compose, etc.)
README.md
CLAUDE.md

## Documentation (Source of Truth)
All product/engineering decisions are defined in `Docs/`.

Must-read documents:
- `Docs/PRD.md` — MVP scope and requirements (what we build / not build)
- `Docs/UX_SPEC.md` — page layout & UX rules
- `Docs/API.md` — API contract (frontend-backend “contract”)
- `Docs/ENGINE_SPEC.md` — algorithm / finance logic spec (structure + behavior + state machine)
- `Docs/ARCHITECTURE.md` — system architecture & data flow
- `Docs/PLAN.md` — milestones & dev plan
- `Docs/I18N.md` — language toggle + key-based text strategy
- `Docs/DISCLAIMER.md` — risk & compliance statement
- `Docs/TEST_PLAN.md` — tests & regression plan

> Rule: **If code conflicts with Docs, Docs win** (until Docs are updated).

---

## Local development (placeholder)
MVP focus is documentation-first. Local run instructions may evolve as implementation lands.

Expected (target) stacks:
- Web: Next.js
- API: FastAPI
- Core: Python engine package
- Optional: Redis/Postgres for caching/snapshots

See:
- `Docs/ARCHITECTURE.md` for runtime diagram
- `infra/` for docker-compose once available

---

## Contributing
Before implementing any feature, ensure the corresponding doc exists or is updated:
- new algorithm → add/update doc under `Docs/` (see CLAUDE.md)
- new architecture change → update `Docs/ARCHITECTURE.md`
- new deployment method → create `Docs/DEPLOYMENT.md` (or `Docs/DEPLOYMENT_*.md`)

---

## Disclaimer
See `Docs/DISCLAIMER.md`.