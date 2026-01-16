# SIM_TRADER_SPEC.md (Plan A: 0DTE Trade Plan Module)

> 0DTE Trading Playbook Module Design Document - Does not depend on options quotes, only outputs trading plans at the underlying price level

---

## 1. Module Goals (Scope)

This module converts structured signals from the analysis system into:

* **Trade Setup (WATCH/ARMED)**
* **Clear Entry Signals (ENTER CALL / ENTER PUT)**
* **Exit Targets and Invalidation Conditions**
* **Position Management Advice (HOLD / TRIM / EXIT)**
* **Post-trade Review Records (signal correctness, rule execution)**

> ⚠️ This module does not require real-time options quotes and does not calculate actual premium.
> It outputs trading playbooks and execution advice at the "underlying (QQQ) price level".

---

## 2. Complete Separation from Analysis System (Hard Separation)

### Analysis System Responsibilities:

* Calculate signals, behavior structure, trends
* Calculate levels/zones (R1/R2/S1/S2/YC/HOD/LOD, etc.)
* Output unified structured snapshot `AnalysisSnapshot`

### Trade Plan Module Responsibilities:

* Does NOT perform any technical indicator calculations
* Does NOT recalculate trends
* Only consumes `AnalysisSnapshot`
* Outputs trade plan `TradePlanRow` + position advice `ManageAdvice`

---

## 3. Input/Output Contracts (Types)

### 3.1 Input: AnalysisSnapshot

Minimum fields:

```ts
type AnalysisSnapshot = {
  ts: string; // ISO time (ET or UTC)
  ticker: string; // "QQQ"
  interval: "1m" | "5m";

  price: {
    open: number; high: number; low: number; close: number;
  };

  levels: {
    R1?: number; R2?: number;
    S1?: number; S2?: number;
    YC?: number;
    HOD?: number; LOD?: number;
    YH?: number; YL?: number;
    PMH?: number; PML?: number;
  };

  signals: {
    trend_1m: "up" | "down" | "neutral";
    trend_5m?: "up" | "down" | "neutral";
    behavior?: "accumulation" | "distribution" | "wash" | "rally" | "chop";
    breakoutQuality?: "pass" | "fail" | "unknown";
    rvolState?: "low" | "ok" | "high";
    openingProtection?: boolean; // 09:30-09:40 ET true
  };

  confidence?: number; // 0-100
};
```

---

### 3.2 Output: TradePlanRow (For UI Table)

```ts
type TradeStatus = "WAIT" | "WATCH" | "ARMED" | "ENTER" | "HOLD" | "TRIM" | "EXIT";

type TradeDirection = "CALL" | "PUT" | "NONE";

type TradePlanRow = {
  ts: string;
  status: TradeStatus;
  direction: TradeDirection;

  entryZone?: string;           // "R1 breakout" / "YC reclaim" etc.
  entryUnderlying?: string;     // ">= 624.30 (2 closes above R1)"
  targetUnderlying?: string;    // "R2 626.10"
  invalidation?: string;        // "close back below R1"

  risk: "LOW" | "MED" | "HIGH";
  watchlistHint?: string;       // "Watch 0DTE ATM +1 strike CALL"

  reasons: string[];            // 2-4 bullets
};
```

---

## 4. Core Philosophy: Trade Plan (Playbook) Not Premium

### 4.1 Why Premium Is Not Needed

0DTE option premium heavily depends on:

* Theta decay
* IV changes
* Spread/liquidity

If a simulation system lacks professional options data sources, hard-calculating premium would be misleading.

✅ Therefore Plan A only outputs:

* **Underlying trigger level (entry)**
* **Underlying target level (target)**
* **Underlying invalidation level (stop)**
* **Risk and confirmation conditions**

When executing, you check the current 0DTE contract premium on Robinhood.

---

## 5. State Machine

Each ticker has at most 1 "high probability trade" per day (configurable).

State transitions:

```
WAIT → WATCH → ARMED → ENTER → HOLD → TRIM/EXIT
                 ↓
               (conditions not met, fallback)
                 ↓
               WAIT
```

State definitions:

| State | Meaning | Trigger Condition |
|-------|---------|-------------------|
| `WAIT` | No trade opportunity | Default state, no setup |
| `WATCH` | Setup appeared, but not near trigger | Price > 0.3% from key level |
| `ARMED` | Near trigger, send alert | Price <= 0.3% from key level |
| `ENTER` | Trigger conditions met, recommend order | All confirmation conditions passed |
| `HOLD` | In position management | Next bar after ENTER |
| `TRIM` | Recommend partial exit | Soft stop conditions triggered |
| `EXIT` | Recommend full exit | Hard stop conditions triggered |

> Note: Next bar after ENTER automatically enters HOLD (to avoid constantly showing ENTER).

---

## 6. 0DTE Strategy Rules (QQQ Specific)

### 6.1 Time Windows

| Session | Eastern Time | Pacific Time | Notes |
|---------|--------------|--------------|-------|
| Opening Protection | 09:30-09:40 | 06:30-06:40 | openingProtection=true, stricter confirmation |
| Golden Hour | 09:40-11:00 | 06:40-08:00 | Best trading window |
| Midday | 11:00-14:00 | 08:00-11:00 | Lower liquidity, cautious |
| Close | 14:00-16:00 | 11:00-13:00 | Theta accelerates, high risk |

Recommended trading time: **06:00–11:00 PT** (configurable)

---

### 6.2 Entry Setups (Trade Opportunity Types)

Supports 4 core setups:

#### Setup A: R1 Breakout (CALL)

**Scenario**: Price approaching R1, breakout may rally

**Trigger Conditions**:
- `1m close > R1` for **2 consecutive confirmations**
- `breakoutQuality == pass`
- `trend_1m == up`
- `rvolState != low` (mandatory during opening protection)

**Output**:
```
status: ENTER
direction: CALL
entryUnderlying: >= R1 + buffer (2 closes)
targetUnderlying: R2 or HOD
invalidation: close < R1 (2 bars)
```

---

#### Setup B: S1 Breakdown (PUT)

**Scenario**: Price approaching S1, breakdown may drop

**Trigger Conditions** (symmetric logic):
- `1m close < S1` for 2 consecutive bars
- `breakoutQuality == pass`
- `trend_1m == down`
- `rvolState != low`

**Output**:
```
status: ENTER
direction: PUT
entryUnderlying: <= S1 - buffer (2 closes)
targetUnderlying: S2 or LOD
invalidation: close > S1 (2 bars)
```

---

#### Setup C: YC Reclaim (CALL)

**Scenario**: Price tests YC without breaking, reclaims

**Trigger Conditions**:
- Price previously broke below YC then reclaimed
- `1m close > YC` for 2 consecutive bars
- `trend_1m != down`

**Output**:
```
status: ENTER
direction: CALL
entryUnderlying: >= YC + buffer (reclaim)
targetUnderlying: R1 or PMH
invalidation: close < YC (2 bars)
```

Suitable for high-probability "gap fill/bounce" on range days.

---

#### Setup D: R1 Reject (PUT)

**Scenario**: Touched R1 but rejected, structure turns bearish

**Trigger Conditions**:
- Price touched R1 but failed to break (wicks)
- `1m close < R1` for 2 consecutive bars (rejection confirmation)
- `trend_1m == down` or `behavior == distribution`

**Output**:
```
status: ENTER
direction: PUT
entryUnderlying: <= R1 - buffer (rejection)
targetUnderlying: YC or S1
invalidation: close > R1 (2 bars)
```

---

### 6.3 Buffer (Avoiding Fakeouts)

```
buffer = 0.05% * price
```

| Underlying Price | Buffer |
|------------------|--------|
| QQQ 500 | ~0.25 |
| QQQ 600 | ~0.30 |
| QQQ 624 | ~0.31 |

Configurable parameter: `BUFFER_PCT = 0.0005`

---

## 7. HOLD/TRIM/EXIT (Position Management Advice)

### 7.1 EXIT (Hard Conditions)

Any hit triggers immediate `EXIT`:

| Condition | Description |
|-----------|-------------|
| Trend reversal + key level lost | CALL position falls back below R1 with 2-bar confirmation |
| Behavior turns distribution/wash | Conflicts with CALL direction |
| Invalidation triggered | Preset stop level hit |

---

### 7.2 TRIM (Soft Conditions, 0DTE Specific)

Any hit suggests `TRIM`:

| Condition | Description |
|-----------|-------------|
| Time stop | 8-12 minutes after entry with no progress toward target |
| Multiple failed attempts | Target tested >= 3 times without breaking |
| Momentum decay | RVOL turns low + chop increases |

---

### 7.3 HOLD (Continue Holding)

Continue `HOLD` when all conditions satisfied:

- Structure not broken (key levels intact)
- Still pushing toward target
- breakoutQuality still valid

---

## 8. Watchlist Hint (Pre-alert to Watch Contract on RH)

When status = ARMED or ENTER, output:

| Direction | Hint |
|-----------|------|
| CALL | `Watch 0DTE ATM +1 strike CALL` |
| PUT | `Watch 0DTE ATM +1 strike PUT` |

Additional note:
> "Prefer liquidity: highest OI/volume strike"

> Future: If options data source connected, upgrade to specific contract symbol and premium.

---

## 9. UI Display: Table is Optimal

### 9.1 Recommended Table Columns

**Sim Trade Plan (Table)**

| Column | Field | Description |
|--------|-------|-------------|
| Time | ts | Timestamp |
| Status | status | WAIT/WATCH/ARMED/ENTER/HOLD/TRIM/EXIT |
| Dir | direction | CALL/PUT/NONE |
| Entry | entryUnderlying | Entry condition |
| Target | targetUnderlying | Target level |
| Invalidation | invalidation | Stop condition |
| Risk | risk | LOW/MED/HIGH |
| Watch | watchlistHint | Contract hint |

Click row to expand `reasons[]` (evidence chain).

### 9.2 Color Coding

| Status | Background Color |
|--------|------------------|
| WAIT | Gray |
| WATCH | Light Yellow |
| ARMED | Orange |
| ENTER | Green (CALL) / Red (PUT) |
| HOLD | Blue |
| TRIM | Purple |
| EXIT | Dark Gray |

### 9.3 Placement

- ✅ Place **below K-line chart** (as new Tab)
- Right panel keeps Summary/Trigger/Action fixed visible

---

## 10. Update Frequency (Performance & UX)

| Operation | Frequency | Notes |
|-----------|-----------|-------|
| Internal state update | Every 1m bar close | Fast enough, doesn't waste resources |
| UI refresh | Every 1m or throttled 3s | Avoid flickering |
| EH data | Cache only | Never request EH during session |

---

## 11. Post-Trade Review (Post-Mortem)

After each trade completion, generate:

```ts
type TradeReview = {
  date: string;
  ticker: string;
  direction: "CALL" | "PUT";
  setup: "R1_BREAKOUT" | "S1_BREAKDOWN" | "YC_RECLAIM" | "R1_REJECT";

  entryTs: string;
  entryPrice: number;
  exitTs: string;
  exitPrice: number;

  outcome: "WIN" | "LOSS" | "BREAKEVEN";
  pnlPct?: number;  // Underlying price change (not option return)

  notes: string[];

  signalCorrect: boolean;
  executionCorrect: boolean;
  failureReason?: "FAKEOUT" | "LOW_RVOL" | "OPENING_NOISE" | "BAD_CONFIRMATION" | "TIME_DECAY" | "CHOP";
};
```

### 11.1 Review Statistics

| Metric | Calculation |
|--------|-------------|
| Win Rate | WIN / (WIN + LOSS) |
| Signal Accuracy | signalCorrect / total |
| Execution Accuracy | executionCorrect / total |
| Common Failure Reasons | Group by failureReason |

> Plan A doesn't calculate real dollar returns, but outcome + failure reasons can optimize strategy thresholds.

---

## 12. Parameter Configuration (Defaults)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BUFFER_PCT` | 0.0005 | Fakeout avoidance buffer |
| `CONFIRM_BARS` | 2 | Bars needed for confirmation |
| `INVALIDATE_BARS` | 2 | Bars needed for invalidation |
| `ARMED_DISTANCE_PCT` | 0.003 | Trigger ARMED within 0.3% of key level |
| `TIME_STOP_MINUTES` | 10 | Time stop (no progress) |
| `MAX_TARGET_ATTEMPTS` | 3 | Max target test attempts |
| `MAX_TRADES_PER_DAY` | 1 | Max daily trades |
| `OPENING_PROTECTION_MINUTES` | 10 | Opening protection duration |

---

## 13. File Structure Recommendation

```
packages/core/src/
├── sim_trader/
│   ├── __init__.py
│   ├── types.py          # AnalysisSnapshot, TradePlanRow, TradeReview
│   ├── state_machine.py  # TradeStateMachine class
│   ├── setups.py         # 4 setup detection logic
│   ├── manager.py        # HOLD/TRIM/EXIT position management
│   └── config.py         # Parameter configuration
│
apps/api/src/
├── services/
│   └── sim_trader_service.py  # API layer wrapper
│
apps/web/src/
├── components/
│   └── SimTradeTable.tsx      # Table UI component
```

---

## 14. API Endpoint Design

### GET /v1/sim-trade-plan

**Request**:
```
GET /v1/sim-trade-plan?ticker=QQQ&tf=1m
```

**Response**:
```json
{
  "ticker": "QQQ",
  "ts": "2026-01-16T09:45:00-05:00",
  "plan": {
    "status": "ARMED",
    "direction": "CALL",
    "entryZone": "R1 breakout",
    "entryUnderlying": ">= 624.30 (2 closes above R1)",
    "targetUnderlying": "R2 626.10",
    "invalidation": "close < R1 (2 bars)",
    "risk": "MED",
    "watchlistHint": "Watch 0DTE ATM +1 strike CALL",
    "reasons": [
      "Price approaching R1 (624.30)",
      "Trend 1m: up",
      "RVOL: ok (1.2x)",
      "Breakout quality: pass"
    ]
  },
  "history": [
    {
      "ts": "09:35",
      "status": "WATCH",
      "direction": "CALL"
    },
    {
      "ts": "09:42",
      "status": "ARMED",
      "direction": "CALL"
    }
  ]
}
```

---

## 15. Example Outputs

### 15.1 ARMED State

| Time | Status | Dir | Entry | Target | Invalidation | Risk | Watch |
|------|--------|-----|-------|--------|--------------|------|-------|
| 09:42 | **ARMED** | CALL | >= 624.30 (R1) | R2 626.10 | < R1 (2 bars) | MED | 0DTE ATM+1 CALL |

**Reasons**:
- Price 0.2% from R1 (624.30)
- Trend 1m: up
- RVOL: 1.2x (ok)
- Breakout quality: pass

---

### 15.2 ENTER State

| Time | Status | Dir | Entry | Target | Invalidation | Risk | Watch |
|------|--------|-----|-------|--------|--------------|------|-------|
| 09:45 | **ENTER** | CALL | ✓ 624.35 (confirmed) | R2 626.10 | < 624.00 | MED | Execute now |

**Reasons**:
- 2 consecutive closes above R1
- Breakout confirmed with volume
- Target: R2 at 626.10 (+0.28%)

---

### 15.3 WAIT State (No Opportunity)

| Time | Status | Dir | Entry | Target | Invalidation | Risk | Watch |
|------|--------|-----|-------|--------|--------------|------|-------|
| 10:15 | WAIT | NONE | - | - | - | - | No setup |

**Reasons**:
- Price in chop zone between S1 and R1
- No clear directional bias
- RVOL low (0.7x)

---

## Appendix: Mapping with Existing System

| Existing Field | Maps To AnalysisSnapshot |
|----------------|--------------------------|
| `report.trend.regime` | signals.trend_1m/5m |
| `report.behavior.dominant` | signals.behavior |
| `report.breakout.state` | signals.breakoutQuality |
| `report.zones[].level` | levels.R1/R2/S1/S2 |
| `eh_context.yc` | levels.YC |
| `eh_context.pmh/pml` | levels.PMH/PML |
| `features.rvol` | signals.rvolState |
