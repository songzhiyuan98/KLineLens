# KLineLens MVP - Development Plan

## Milestone 0: Repo & Infra
- Monorepo initialization
- web/api/core basic setup
- Environment variables and configuration

## Milestone 1: Market Data
- Provider integration (start with one)
- GET /v1/bars
- Basic caching, error handling

## Milestone 2: Core Structure
- Swing points
- Zones (support/resistance)
- Regime (trend/range)
- Breakout state machine

## Milestone 3: Behavior + Timeline + Playbook
- Behavior scores -> probabilities
- Evidence pack
- Stateful timeline (in-memory)
- Playbook templates

## Milestone 4: Web Terminal + Settings Language
- Dashboard large search box -> /t/{ticker}
- Detail chart + overlays + panel cards
- /settings language toggle (localStorage)
- 60-second auto-refresh analyze

## Milestone 5: Extended Hours + 0DTE Strategy
- Extended hours context (premarket/afterhours)
- 0DTE trade plan module
- Strategy type selection (Playbook / 0DTE)

## MVP Acceptance Criteria
- / input ticker navigates to detail page
- 1m K-line displays + zones + signals
- Behavior probabilities + evidence + timeline + playbook all visible
- Settings language toggle applies site-wide
- Docker compose up one-click startup succeeds
