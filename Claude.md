# CLAUDE.md — KLineLens Collaboration Guide

This file tells Claude (and any collaborator) how to work in this repo.

---

## 0. Ground Rules (Must Follow)

1. **Docs-first**: Implementation must match docs in `Docs/`. Read docs before coding.
2. **Update docs before significant changes**: New algorithm/signal/behavior → update docs first.
3. **No silent breaking changes**: If schema changes, update `Docs/API.md` and add migration notes.
4. **MVP is English-only**: No i18n complexity for MVP. Multi-language is post-MVP.
5. **Deterministic engine**: `packages/core/` must be pure and testable. Same input → same output.

---

## 1. Documentation Index (Read Order)

Before coding, read these in order:

| Order | Document | Purpose |
|-------|----------|---------|
| 1 | `MASTER_SPEC.md` | Project constitution, scope, principles |
| 2 | `Docs/PRD.md` | Product requirements, user scenarios |
| 3 | `Docs/UX_SPEC.md` | Page layout, UI rules |
| 4 | `Docs/API.md` | REST endpoints, request/response schema |
| 5 | `Docs/ENGINE_SPEC.md` | Algorithm logic, formulas, parameters |
| 6 | `Docs/ARCHITECTURE.md` | System architecture, data flow |
| 7 | `Docs/PROVIDER.md` | Data provider integration |
| 8 | `Docs/CONFIG.md` | Environment variables |
| 9 | `Docs/PLAN.md` | Development milestones |
| 10 | `Docs/TODO.md` | Current task tracking |

If any ambiguity exists, **update the Docs** before implementing.

---

## 2. Development Workflow

### Step A: Pick a Milestone
Use `Docs/PLAN.md` milestones. Implement in order:
1. Core engine functions first
2. Then API endpoints
3. Then web UI

### Step B: Keep Engine Deterministic
- `packages/core/` should be pure Python, no I/O
- Same input bars → same output report
- Do not mix provider/network logic into core

### Step C: Follow Schema
- API must return `AnalysisReport` as documented in `Docs/API.md`
- All fields required unless marked optional

### Step D: Update TODO
- Mark tasks in `Docs/TODO.md` as you work
- Add new tasks if scope changes

---

## 3. Documentation Update Rules

### 3.1 When Adding Algorithm/Signal
- Update `Docs/ENGINE_SPEC.md`:
  - Feature definitions and formulas
  - Parameters and defaults
  - Evidence rules

### 3.2 When Changing Architecture
- Update `Docs/ARCHITECTURE.md`:
  - Data flow changes
  - New services/components
  - Caching/storage changes

### 3.3 When Changing API
- Update `Docs/API.md`:
  - Endpoint params
  - Response fields
  - Error codes
- If breaking: add "Breaking Changes" section

### 3.4 When Changing UX
- Update `Docs/UX_SPEC.md`:
  - Page layout
  - Card order
  - Error states

---

## 4. Task Tracking

### 4.1 TODO List
- File: `Docs/TODO.md`
- Update status as you work
- Add new tasks when discovered

### 4.2 Bug Log
- File: `Docs/BUGS.md`
- Format: ID, Date, Symptom, Root cause, Fix, Test added

### 4.3 Changelog
- File: `Docs/CHANGELOG.md`
- Update for every significant change
- Follow Keep-a-Changelog format

---

## 5. Code Quality Rules

### 5.1 Python (Core + API)
- Type hints required
- Docstrings for public functions
- Unit tests for core logic

### 5.2 TypeScript (Web)
- TypeScript strict mode
- Types for API responses
- Component props typed

### 5.3 Testing
- Core: pytest unit tests
- API: Integration tests for endpoints
- Web: Smoke tests for pages

---

## 6. What NOT to Do

- Do not invent providers or claim "live data" works without implementation
- Do not add features outside MVP scope without updating PRD
- Do not output final trading advice; keep playbooks conditional
- Do not commit secrets or API keys
- Do not skip docs updates for significant changes

---

## 7. Quick Start

```bash
# Read docs first
cat MASTER_SPEC.md
cat Docs/TODO.md

# Check current milestone
# Implement tasks in order
# Update TODO as you go
# Update docs if schema changes
```
