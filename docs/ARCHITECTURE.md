# KLineLens — Architecture

> System architecture, data flow, and technical decisions.

---

## 1. Overview

MVP uses a **Monorepo + 3-Layer** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Web)                        │
│                         Next.js                              │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────────┐  │
│  │Dashboard│  │  Detail  │  │ Settings│  │ Chart + Panel │  │
│  └─────────┘  └──────────┘  └─────────┘  └───────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend (API)                        │
│                          FastAPI                             │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────────┐  │
│  │  /bars  │  │ /analyze │  │  Cache  │  │    Provider   │  │
│  └─────────┘  └──────────┘  └─────────┘  └───────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │ Function call
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Core Engine (Lib)                      │
│                    Python Package (Pure)                     │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────────┐  │
│  │Features │  │Structure │  │Behavior │  │Timeline+Playb │  │
│  └─────────┘  └──────────┘  └─────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
kline-lens/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── src/
│   │   │   ├── pages/          # Route pages
│   │   │   ├── components/     # UI components
│   │   │   ├── hooks/          # React hooks
│   │   │   ├── lib/            # API client, utils
│   │   │   └── styles/         # CSS/Tailwind
│   │   ├── package.json
│   │   └── next.config.js
│   │
│   └── api/                    # FastAPI backend
│       ├── src/
│       │   ├── main.py         # FastAPI app
│       │   ├── routes/         # API routes
│       │   ├── providers/      # Data provider adapters
│       │   ├── cache.py        # Caching layer
│       │   └── config.py       # Configuration
│       ├── requirements.txt
│       └── pyproject.toml
│
├── packages/
│   └── core/                   # Pure Python engine
│       ├── src/
│       │   ├── __init__.py
│       │   ├── features.py     # Feature calculations
│       │   ├── structure.py    # Swing, zones, regime
│       │   ├── behavior.py     # Behavior inference
│       │   ├── timeline.py     # State machine
│       │   ├── playbook.py     # Playbook generation
│       │   └── analyze.py      # Main analysis entry
│       ├── tests/
│       └── pyproject.toml
│
├── docs/                       # Documentation (source of truth)
├── infra/                      # Docker, deployment configs
├── MASTER_SPEC.md
├── CLAUDE.md
└── README.md
```

---

## 3. Data Flow

### 3.1 Request Flow (Detail Page Load)

```
User enters ticker
       │
       ▼
┌──────────────┐
│   Web: /t/   │
│   {ticker}   │
└──────┬───────┘
       │ 1. GET /v1/bars?ticker=X&tf=1m
       ▼
┌──────────────┐     ┌─────────────┐
│   API:       │────▶│   Cache     │ Check cache
│   /v1/bars   │     │  (TTL 60s)  │
└──────┬───────┘     └─────────────┘
       │                   │
       │ Cache miss        │ Cache hit
       ▼                   │
┌──────────────┐           │
│   Provider   │           │
│   (yfinance) │           │
└──────┬───────┘           │
       │                   │
       └───────────────────┘
       │
       ▼ Return bars
┌──────────────┐
│   Web:       │
│   render     │
│   chart      │
└──────┬───────┘
       │ 2. POST /v1/analyze
       ▼
┌──────────────┐
│   API:       │
│   /v1/analyze│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Core:      │
│   analyze()  │
└──────┬───────┘
       │
       ▼ Return AnalysisReport
┌──────────────┐
│   Web:       │
│   render     │
│   panel      │
└──────────────┘
```

### 3.2 Auto-Refresh Flow (Every 60s)

```
setInterval(60000)
       │
       ▼
┌──────────────┐
│ POST /analyze│ (bars may be cached)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Core.analyze │
│  with state  │─────▶ Timeline updated if change detected
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Web: update  │
│ panel cards  │
└──────────────┘
```

---

## 4. Layer Responsibilities

### 4.1 Web (Next.js)

| Responsibility | Description |
|----------------|-------------|
| Routing | `/`, `/t/{ticker}`, `/settings` |
| Chart rendering | OHLCV candles + volume + zone overlays |
| Panel rendering | Cards for state, behavior, timeline, playbook |
| API client | Fetch bars and analysis from backend |
| Refresh loop | Auto-fetch every 60s |

**Key Libraries:**
- Chart: `lightweight-charts` (TradingView) or `recharts`
- HTTP: `fetch` or `swr`
- State: React useState/useReducer (no Redux for MVP)

### 4.2 API (FastAPI)

| Responsibility | Description |
|----------------|-------------|
| REST endpoints | `/v1/bars`, `/v1/analyze` |
| Data provider | Adapter pattern for different sources |
| Caching | In-memory TTL cache for bars |
| State storage | In-memory dict for timeline state (MVP) |
| Error handling | Structured error responses |

**Key Design:**
- Provider abstraction: `MarketDataProvider` interface
- Single instance for MVP (no horizontal scaling yet)

### 4.3 Core (Python Package)

| Responsibility | Description |
|----------------|-------------|
| Feature calculation | ATR, volume_ratio, wick ratios, efficiency |
| Structure detection | Swing points, zones, regime, breakout FSM |
| Behavior inference | 5-class probabilities + evidence |
| Timeline state | Compare with previous state, emit events |
| Playbook generation | Template-based conditional plans |

**Key Principles:**
- **Pure functions**: No I/O, no network calls
- **Deterministic**: Same input bars → same output
- **Testable**: Unit tests for each module

---

## 5. Caching Strategy

### 5.1 MVP: In-Memory Cache

```python
# Simple TTL cache
cache = {}

def get_bars(ticker, tf, window):
    key = f"{ticker}:{tf}:{window}"
    if key in cache and not expired(cache[key]):
        return cache[key].data

    data = provider.fetch(ticker, tf, window)
    cache[key] = CacheEntry(data, ttl=60)
    return data
```

| Cache | TTL | Scope |
|-------|-----|-------|
| Bars | 60s | Per ticker+tf+window |
| Timeline state | Permanent (in-memory) | Per ticker+tf |

### 5.2 Future: Redis Cache

For multi-instance deployment:
- Bars cache: Redis with TTL
- Timeline state: Redis hash per ticker+tf
- Session affinity not required

---

## 6. State Management

### 6.1 Timeline State (Per Ticker+TF)

```python
TimelineState = {
    "ticker": "TSLA",
    "tf": "1m",
    "last_regime": "range",
    "last_behavior_probs": {...},
    "last_breakout_state": "idle",
    "last_zones_hash": "abc123",
    "last_updated": "2026-01-13T18:00:00Z"
}
```

**Storage:**
- MVP: In-memory dict (lost on restart)
- V1: Redis or PostgreSQL

### 6.2 State Comparison Logic

```python
def should_emit_event(old_state, new_report):
    # Emit if dominant behavior changed
    if old_state.dominant != new_report.behavior.dominant:
        return True

    # Emit if probability delta > threshold
    if abs(old_state.probs[dominant] - new_report.probs[dominant]) >= 0.12:
        return True

    # Emit if breakout state changed
    if old_state.breakout_state != new_report.breakout_state:
        return True

    # Emit if regime changed
    if old_state.regime != new_report.market_state.regime:
        return True

    return False
```

---

## 7. Error Handling

### 7.1 Provider Errors

| Error Type | Handling |
|------------|----------|
| Rate limited | Return 429, suggest retry after |
| No data | Return 404 with clear message |
| Provider down | Return 502, use cached data if available |
| Invalid ticker | Return 400 with validation error |

### 7.2 Core Engine Errors

| Error Type | Handling |
|------------|----------|
| Insufficient bars | Return partial report with warning |
| Calculation error | Log and return 500 |

---

## 8. Extensibility Points (V1/V2)

| Feature | Approach |
|---------|----------|
| Multiple providers | `MarketDataProvider` interface, factory pattern |
| WebSocket streaming | Add `/ws/ticker` endpoint, push on bar update |
| Snapshots | Store `AnalysisReport` to PostgreSQL with timestamp |
| LLM narration | Post-process deterministic JSON, add `narrative` field |
| Multi-timeframe | Run analyze() for 1m and 1d, merge in API layer |

---

## 9. Development Setup (MVP)

### 9.1 Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Docker

### 9.2 Local Run

```bash
# Terminal 1: API
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Terminal 2: Web
cd apps/web
npm install
npm run dev
```

### 9.3 Environment Variables

See `docs/CONFIG.md` for full list.

```bash
# API
PROVIDER=yfinance
CACHE_TTL=60

# Web
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 10. Docker Deployment

### 10.1 Docker Compose Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     Host Machine                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Docker Network (klinelens)               │  │
│  │                                                       │  │
│  │  ┌─────────────────┐      ┌─────────────────┐        │  │
│  │  │   web (Next.js) │      │   api (FastAPI) │        │  │
│  │  │   Port: 3000    │─────▶│   Port: 8000    │        │  │
│  │  │                 │ HTTP │                 │        │  │
│  │  └─────────────────┘      └────────┬────────┘        │  │
│  │                                    │                  │  │
│  │                                    │ yfinance         │  │
│  │                                    ▼                  │  │
│  │                           ┌─────────────────┐        │  │
│  │                           │ Yahoo Finance   │        │  │
│  │                           │ (External API)  │        │  │
│  │                           └─────────────────┘        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Browser ◀────────────────────────────────────────────────┘
│     │
│     └─▶ http://localhost:3000
│     └─▶ http://localhost:8000/docs (API Docs)
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Container Configuration

| Service | Image Base | Port | Purpose |
|---------|------------|------|---------|
| `api` | python:3.11-slim | 8000 | FastAPI backend |
| `web` | node:20-alpine | 3000 | Next.js frontend |

### 10.3 Environment Variables Flow

```
.env (Host)
    │
    ├──▶ docker-compose.yml
    │       │
    │       ├──▶ api container
    │       │     - PROVIDER
    │       │     - CACHE_TTL
    │       │     - LOG_LEVEL
    │       │     - CORS_ORIGINS
    │       │
    │       └──▶ web container
    │             - NEXT_PUBLIC_API_URL
    │             - NEXT_PUBLIC_REFRESH_SECONDS
```

### 10.4 Quick Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after code changes
docker compose up --build
```

See `docs/DEPLOYMENT.md` for detailed instructions.
