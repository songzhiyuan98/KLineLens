# KLineLens MVP - Product Requirements Document (PRD)

## 1. Background & Goals

### 1.1 Background
Short-term traders frequently take screenshots of 1-minute K-lines and send them to LLMs for market structure interpretation (trend/range, support/resistance, volume surges, shakeout/accumulation/distribution, etc.). The current workflow has significant pain points:
- High input cost: Screenshotting, sending, and waiting for responses every minute
- Lack of continuity: LLMs cannot reliably "inherit previous minute's structure state"
- Lack of visualization & evidence: Interpretations lack traceable indicators/evidence
- Lack of structured output: Hard to accumulate into replayable, comparable "structure state timelines"

### 1.2 Product Positioning
**KLineLens is an open-source local tool** — users run it locally via Docker and configure their own data sources.

| Attribute | Description |
|-----------|-------------|
| Product Form | Open-source local terminal |
| Deployment | Docker Compose local startup |
| Data Source | User-configured locally, default Yahoo Finance |
| We Provide | Analysis engine + API + UI |
| User Provides | Data source selection, API keys (if needed), local runtime environment |

### 1.3 Product Goals (MVP)
User inputs a stock ticker, system automatically fetches minute/daily OHLCV data and outputs:
1) **Structure Recognition**: Trend/range state, key support/resistance zones, breakout/fakeout state
2) **Behavior Inference (Probability-based)**: Accumulation/shakeout/markup/distribution/markdown probabilities + evidence points
3) **Continuous Narrative (Stateful Timeline)**: Records the last N structure/behavior changes with reasons
4) **Trading Playbook (Conditional)**: Plan A/B (trigger conditions, targets, invalidation, risk notes)

### 1.4 Non-Goals (MVP Explicitly Excludes)
- Login/registration/user system
- Cloud-hosted service
- Database persistent storage
- News/social sentiment (Reddit/X)
- Level 2/tick-by-tick (order flow) depth inference
- Backtesting panel (can be added later)
- "Definitive calls" (must be conditional + invalidation conditions + probability explanations)
- Multi-language support (MVP English-only) → *Note: Now implemented*

---

## 2. Deployment & Operation

### 2.1 Docker Compose One-Click Startup
Users execute the following commands to run:

```bash
# 1. Clone repository
git clone https://github.com/songzhiyuan98/KLineLens.git
cd KLineLens

# 2. Copy environment config
cp .env.example .env
# (Optional) Edit .env to fill in provider keys

# 3. Start services
docker compose up --build

# 4. Access
open http://localhost:3000
```

### 2.2 Environment Configuration (.env.example)
```bash
# Provider Configuration
PROVIDER=yahoo              # yahoo | twelvedata | alpaca | alphavantage
TIMEZONE=UTC

# Refresh Frequency
REFRESH_SECONDS=60          # Frontend auto-refresh interval

# Cache Configuration
CACHE_TTL=60                # K-line data cache duration in seconds

# Port Configuration
API_PORT=8000
WEB_PORT=3000

# Optional: Provider API Keys
# TWELVEDATA_API_KEY=
# ALPACA_API_KEY=
# ALPACA_API_SECRET=
# ALPHAVANTAGE_API_KEY=
```

### 2.3 No Public Hosting Service
- No cloud availability guarantees
- No online accounts
- All API keys exist only in user's local .env
- Data request rate limiting is user's responsibility

---

## 3. Users & Scenarios

### 3.1 Target Users
- High-frequency short-term traders: Often watch 1m/5m K-lines
- Volatile/small-cap stock traders: Focus on volume-price structure and key levels
- Those who need "market narrative" for decision support: Want quick structure explanations and risk boundaries

### 3.2 Core Scenarios (MVP Coverage)
1) Start Docker container locally, open browser and enter ticker to access detail page
2) View current 1m structure interpretation, auto-updates every 60 seconds
3) Observe if structure evolves from "range → breakout attempt → confirmed/failed"
4) Switch timeframes (1m/5m/1d) to align higher timeframe key levels with lower timeframe execution
5) View "timeline" to understand: why system says "shakeout probability rising/distribution probability rising"

---

## 4. Information Architecture & Pages

### 4.1 Page List (MVP)
- `/` Dashboard: Large search box (Ticker)
- `/t/{ticker}` Detail: K-line + Analysis Panel (structure/behavior/evidence/timeline/playbook)
- `/settings` Settings: Settings page

### 4.2 Dashboard Page (/)
**Requirements**
- Input box supports ticker (case-insensitive)
- After search, redirect to detail page `/t/TSLA`
- Top right corner: Settings entry

**Acceptance Criteria**
- Entering valid ticker (letters + optional dots/hyphens) redirects successfully
- Empty input/invalid format shows prompt (no redirect)

### 4.3 Detail Page (/t/{ticker})
**Layout Principles: Minimal, professional, high information density but clean**
- Main body: Chart + Analysis Panel
- Default timeframe: 1m (window=1d)
- Auto-refresh: Refresh analyze every 60 seconds

**Display Content (Required)**

A. Chart
- K-lines (OHLC)
- Volume bars
- Support/Resistance Zone overlays (rectangles/bands)
- Breakout/Fakeout markers (annotation points/segments)

B. Analysis Panel (Card-based)
1) **Market State**
   - Regime: Uptrend / Downtrend / Range
   - Confidence (0-1)
   - Key Zones (Top 2 support + Top 2 resistance)

2) **Behavior Probabilities** (Five types)
   - Accumulation
   - Shakeout
   - Markup
   - Distribution
   - Markdown
   - Dominant Narrative (highest probability)

3) **Evidence** (Evidence points, max 3)
   - Each piece of evidence must link to bar_time + key values

4) **Timeline** (Last N events)
   - Event type, probability change, reason, timestamp

5) **Playbook** (Plan A / Plan B)
   - Conditional (If…), target, invalidation, risk notes

C. **Provider Status**
- Current provider: Yahoo / TwelveData / Alpaca
- Data update time
- If error: rate limited / provider error

**Interactions (Required)**
- Timeframe toggle (at least: 1m / 1d; can add 5m)
- Refresh status indicator (last updated time)
- Error states: Data fetch failure/rate limiting/no data

**Acceptance Criteria**
- After entering ticker, chart and report visible within 10 seconds
- Every 60-second refresh adds timeline events or shows "no significant change"
- Switching timeframe refreshes bars + report

### 4.4 Settings Page (/settings)
**Requirements**
- Display current provider status
- Display cache TTL configuration
- Language selection (English/Chinese)

---

## 5. Functional Requirements (MVP Scope)

### 5.1 Market Data Retrieval
- Support entering ticker to fetch OHLCV bars
- Support timeframes: 1m, 5m, 1d
- Window: 1d (1m) / 5d (5m) / 6mo (1d)

**Data Source Protection**
- Frontend refresh frequency fixed (default 60 seconds)
- Only request on ticker/timeframe switch
- No 1-second refreshes allowed (avoid Yahoo rate limits)

**Caching Strategy**
- Bars with same parameters: 60-second TTL
- Analyze with same parameters: can cache 10-30 seconds (optional)

### 5.2 Structure Recognition
Output:
- Swing points (for structure skeleton)
- Regime (trend/range + confidence)
- Zones (support/resistance: price band + score)
- Breakout state (attempt/confirmed/fakeout etc.)
- Signals (breakout/rejection/fakeout markers)

### 5.3 Behavior Inference
Output:
- Five behavior probabilities (softmax)
- Dominant narrative
- Evidence pack (max 3 pieces)

### 5.4 Continuous Narrative (Stateful Timeline)
Output:
- Last N change events (event_type, delta, reason_key, ts)
- Rule: Only write to timeline when "structure/probability change exceeds threshold"

### 5.5 Trading Playbook
Output two plans:
- Plan A (trend-following/breakout bias)
- Plan B (invalidation/reversal bias)
Each must include: trigger condition, target, invalidation, risk notes

---

## 6. Data Storage

### 6.1 MVP Default Requires No Database
| Data Type | Storage Method | Description |
|-----------|---------------|-------------|
| Bars | In-memory cache (TTL) | Re-fetch after restart |
| Timeline state | In-memory state | Lost on restart, acceptable |
| Config | .env file | User-managed locally |

### 6.2 V1 Adds Persistence (Optional)
- Default SQLite (local file)
- Postgres as docker profile optional
- PRD clearly states: MVP has no DB to avoid users starting extra services

---

## 7. Output Specification (Schema Requirements)
Backend must return structured JSON (not long prose), text uses key + template rendering approach.

Key fields:
- market_state.regime + confidence
- zones.support/resistance (low/high/score/touches)
- behavior.probabilities + dominant + evidence[]
- timeline[]
- playbook[]

See `docs/API.md` and `docs/ENGINE_SPEC.md` for details.

---

## 8. Success Metrics (MVP)
- Functionality: User inputs ticker and can stably see structure, probabilities, timeline
- Responsiveness: First load ≤ 10s, refresh ≤ 5s (depends on provider)
- Continuity: Timeline reflects structure evolution
- Credibility: Each behavior interpretation has at least 1 evidence point
- **Deployability**: docker compose up one-click startup succeeds

---

## 9. Risks & Boundaries (Must Declare)
- This system does not constitute investment advice, only provides volume-price structure analysis and probability explanations
- Behavior inference does not represent actual "institutional account" behavior, only pattern recognition inference
- 1m has high noise, recommend verifying with higher timeframes
- **Data source risk is user's responsibility**: Yahoo Finance has daily request limits, exceeding will return empty data
