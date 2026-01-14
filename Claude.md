# CLAUDE.md — KLineLens Collaboration Guide

This file tells Claude (and any collaborator) how to work in this repo:
- where the source-of-truth docs are
- how to implement changes safely
- how to update documentation, TODOs, and bug records

## 0) Ground rules (must follow)
1) **Docs-first**: Implementation must match docs in `docs/`.  
2) Any significant change requires a doc update:
   - new algorithm / new signal / new behavior logic → `docs/ENGINE_SPEC.md` (or a new engine doc)
   - new API/fields → `docs/API.md`
   - new UX/component behavior → `docs/UX_SPEC.md`
   - new architecture/data flow/caching/storage → `docs/ARCHITECTURE.md`
   - new deployment steps → `docs/DEPLOYMENT.md` (new file)
3) **No silent breaking changes**: if a field changes shape, update docs and add migration notes.
4) **Key-based text only** (for narrative/evidence/playbook): backend should output `*_key` and numeric values; frontend maps keys to `zh/en`.

---

## 1) Where to start (read order)
Before coding, read:
1. `docs/PRD.md` (scope and MVP requirements)
2. `docs/UX_SPEC.md` (page layout & required panels)
3. `docs/API.md` (frontend-backend contract)
4. `docs/ENGINE_SPEC.md` (algorithm + finance logic)
5. `docs/ARCHITECTURE.md` (services + data flow)
6. `docs/I18N.md` (language toggle + text keys)
7. `docs/PLAN.md` (milestones)

If any ambiguity exists, **update the docs** before implementing.

---

## 2) How to implement (recommended workflow)
### Step A — pick a milestone
Use `docs/PLAN.md` milestones. Implement in small increments:
- core engine functions first
- then API endpoints
- then web UI integration

### Step B — keep the engine deterministic
- `packages/core/` should remain pure, testable, and deterministic:
  - same input bars -> same output report
- do not mix provider/network logic into core

### Step C — maintain schema discipline
- The API must return the `AnalysisReport` shape as documented
- Backend should output:
  - regime, zones, signals, behavior probs, evidence packs, timeline events, playbook
- Narrative strings should be key-based (`reason_key`, `note_key`, `risk_key`, etc.)

---

## 3) Documentation update rules
### 3.1 When adding a new algorithm/signal/heuristic
- Update `docs/ENGINE_SPEC.md`:
  - definitions and finance rationale
  - features used (formulas)
  - parameters and default values
  - evidence rules (what gets shown and why)
- If it’s large, create a dedicated doc:
  - `docs/ENGINE_SIGNAL_<NAME>.md` or `docs/ENGINE_BEHAVIOR_<NAME>.md`
- Link the new doc from `docs/ENGINE_SPEC.md`.

### 3.2 When changing architecture (storage, caching, workers, websockets)
- Update `docs/ARCHITECTURE.md`:
  - what changed and why
  - data flow diagram (textual is fine)
  - operational concerns (rate limits, retries, caching TTL)
- If deployment changes, create/update:
  - `docs/DEPLOYMENT.md` (mandatory for any deploy steps)

### 3.3 When changing APIs
- Update `docs/API.md`:
  - endpoint params
  - response fields and examples
  - errors and codes
- If breaking: add a “Breaking Changes” section.

### 3.4 When changing UX
- Update `docs/UX_SPEC.md`:
  - page layout
  - panels/cards order
  - error states

---

## 4) TODO, Bug fixes, and Change log
We keep lightweight but disciplined records in docs.

### 4.1 TODO list
- File: `docs/TODO.md`
- Format:
  - [ ] item
  - [x] done item (with date)

Rules:
- Every milestone should have a TODO section
- Keep TODO updated when work starts/finishes

### 4.2 Bug log
- File: `docs/BUGS.md`
- Each bug entry must include:
  - ID (incremental)
  - Date
  - Symptom
  - Root cause
  - Fix summary
  - Test added (yes/no) and where

### 4.3 Changelog / release notes
- File: `docs/CHANGELOG.md`
- Follow Keep-a-Changelog style:
  - Added / Changed / Fixed / Removed
- Every PR/major commit should update CHANGELOG.

---

## 5) Required additional docs (create when needed)
- `docs/DEPLOYMENT.md` — required once deployment exists
- `docs/PROVIDER.md` — when adding data providers (rate limits, auth, symbols)
- `docs/CONFIG.md` — environment variables and config strategy
- `docs/SECURITY.md` — if any auth/key handling grows complex
- `docs/PERFORMANCE.md` — if latency/caching becomes a major theme

---

## 6) Minimal doc templates (copy/paste)
### 6.1 Template: docs/TODO.md
- Milestone 0: Repo/Infra
- Milestone 1: Market Data
- Milestone 2: Structure Engine
- Milestone 3: Behavior+Timeline+Playbook
- Milestone 4: Web Terminal + Settings

### 6.2 Template: docs/BUGS.md
- #001 (YYYY-MM-DD): <title>
  - Symptom:
  - Root cause:
  - Fix:
  - Test:

### 6.3 Template: docs/DEPLOYMENT.md
- Local run
- Environment variables
- Provider keys setup
- Build steps
- Deploy steps
- Rollback steps

---

## 7) What Claude should NOT do
- Do not invent providers, keys, or claim “live data” works without implementation.
- Do not add features outside MVP scope without PRD updates.
- Do not output final user-facing trading advice; keep playbooks conditional and evidence-based.
