# TODO

## Milestone 0 — Repo & Docs
- [ ] Add initial Docs set (PRD/UX/API/ENGINE/ARCH/PLAN/I18N/DISCLAIMER/TEST)
- [ ] Setup repo structure (apps/web, apps/api, packages/core, infra)

## Milestone 1 — Market Data
- [ ] Implement MarketDataProvider abstraction
- [ ] Implement GET /v1/bars
- [ ] Add caching (in-memory TTL)
- [ ] Add error handling (rate limit, no data, invalid ticker)

## Milestone 2 — Structure Engine
- [ ] Swing points (fractal)
- [ ] Zones (support/resistance clustering)
- [ ] Regime classification (trend/range)
- [ ] Breakout/fakeout state machine
- [ ] Unit tests for structure

## Milestone 3 — Behavior + Timeline + Playbook
- [ ] Behavior scores -> softmax probabilities
- [ ] Evidence pack generation
- [ ] Stateful timeline (in-memory)
- [ ] Playbook template generation
- [ ] Unit tests for behavior + timeline

## Milestone 4 — Web Terminal + Settings
- [ ] Dashboard search -> detail route
- [ ] Detail chart + overlays
- [ ] Analysis panel cards
- [ ] Settings language toggle (localStorage)
- [ ] Auto refresh loop (60s)
