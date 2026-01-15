# KLineLens — Engine Spec

> Market Structure + Volume-Confirmed Inference Engine
>
> Algorithm + Financial Logic: Structure Recognition + Behavior Inference + Stateful Narrative

---

## 0. Design Principles

| Principle | Description |
|-----------|-------------|
| **Deterministic** | Same input bars → same output report (no randomness) |
| **Evidence-first** | Every conclusion must be traceable to specific candles |
| **Regime First** | Determine trend/range before interpreting behavior signals |
| **Zones over Lines** | Key levels are price BANDS, not single prices |
| **Volume Awareness** | Volume rules must support N/A fallback gracefully |
| **Probability Output** | Never claim certainty; output probabilities + evidence |
| **Invalidation Required** | Every playbook must have explicit invalidation conditions |

### 0.1 What KLineLens IS

- Market Intelligence Terminal (structure inference + volume confirmation + explainable decision support)
- Deterministic, backtestable, interpretable analysis engine
- Educational tool for understanding market structure

### 0.2 What KLineLens is NOT

- NOT a price prediction black-box AI
- NOT a high-frequency trading system
- NOT optimized for PnL (no slippage, fees, money management)

---

## 1. Input Data & Reality Constraints

### 1.1 Bar Structure

```python
Bar = {
    "t": "2026-01-13T18:00:00Z",  # UTC timestamp
    "o": float,  # open
    "h": float,  # high
    "l": float,  # low
    "c": float,  # close
    "v": float   # volume (can be 0 or unreliable)
}
```

### 1.2 Preprocessing Steps

1. Sort by timestamp ascending
2. Remove duplicates
3. Handle gaps: MVP allows gaps, report includes `data_gaps` flag if detected
4. Timezone: All timestamps in UTC (frontend localizes for display)

### 1.3 Volume Data Quality Reality

**Problem:** Volume is not always reliable:
- Some free providers have missing/delayed 1m volume
- Volume must be interpreted contextually (strength vs normal), not as absolute value

**Design Principle:**
- Volume available → strict volume-price confirmation enabled
- Volume unavailable → mark N/A, reduce signal confidence, never silent output

### 1.4 Provider Data Quality Tiers

| Provider | 1D Volume | 1m Volume | Latency | Best For |
|----------|-----------|-----------|---------|----------|
| TwelveData | Strong | Strong | ~170ms | Real-time intraday (recommended) |
| Yahoo | Strong | Unstable | 15-20min | Daily structure only |
| Alpaca (IEX) | Good | Good | Low | Free minute confirmation |
| Polygon | Strong | Strong | Plan-dependent | High quality Pro |

---

## 2. Feature Layer (Interpretable Metrics)

### 2.1 ATR (Volatility Baseline)

Used for ALL normalization and threshold control:
- Zone bin width
- Breakout result quality
- Distance-to-zone
- Stop/target estimation

```python
ATR(n) = SMA(TrueRange, n)  # default n=14
TrueRange = max(high-low, abs(high-prev_close), abs(low-prev_close))
```

### 2.2 RVOL (Relative Volume) — Core Volume Metric

**Critical: NEVER use absolute volume for judgment.**

```python
RVOL = volume / MA(volume, N)  # N=30 for 1m, N=20 for 1d
```

| RVOL Value | Interpretation |
|------------|----------------|
| < 0.7 | Low volume (dry-up) |
| 0.7 - 1.3 | Normal |
| 1.3 - 1.8 | Elevated |
| >= 1.8 | High volume spike |

**N/A Handling:**
- If volume = 0 or missing → RVOL = N/A
- Display "Volume N/A - confirmation unavailable" in UI
- Reduce signal confidence by 30%

#### 2.2.1 Optional Enhancement: Time-of-Day RVOL

Intraday volume has U-shape seasonality (higher at open/close).

```python
RVOL_TOD = vol[t] / mean(vol at same minute-of-day over last K days)
```

> MVP: Use simple RVOL. TOD adjustment is future enhancement.

### 2.3 Effort vs Result (VSA Core)

> Volume Spread Analysis: Use Effort (volume) and Result (price movement) to infer institutional behavior.

```python
effort = RVOL
result = true_range / ATR  # or abs(close - open) / ATR
```

**Four Quadrant Interpretation:**

| Effort | Result | Interpretation |
|--------|--------|----------------|
| High | High | Genuine breakout / Trend push |
| High | Low | Absorption (accumulation/distribution) ⭐ |
| Low | High | Controlled move / Impulse |
| Low | Low | Exhaustion / Consolidation |

**Key Insight:** High effort + low result = major player activity (absorption at key levels).

### 2.4 Candlestick Structure

| Feature | Formula | Interpretation |
|---------|---------|----------------|
| `body` | `abs(close - open)` | Price movement magnitude |
| `body_ratio` | `body / range` | 0 = doji, 1 = marubozu |
| `upper_wick` | `high - max(open, close)` | Supply pressure above |
| `lower_wick` | `min(open, close) - low` | Demand absorption below |
| `wick_ratio_up` | `upper_wick / range` | High = rejection from above |
| `wick_ratio_low` | `lower_wick / range` | High = demand recovery |

### 2.5 Move Efficiency (Tape-reading Proxy)

| Feature | Formula | Interpretation |
|---------|---------|----------------|
| `up_eff` | `max(close - open, 0) / volume` | Low with high vol = supply absorption |
| `down_eff` | `max(open - close, 0) / volume` | Low with high vol = demand absorption |

---

## 3. Structure Layer (Market Structure Detection)

### 3.1 Swing Points (Fractal Method)

**Algorithm:**
```python
swing_high[i] = high[i] == max(high[i-n : i+n+1])
swing_low[i]  = low[i]  == min(low[i-n : i+n+1])
```

**Default Parameters:**

| Timeframe | n (fractal order) |
|-----------|-------------------|
| 1m | 4 |
| 5m | 3 |
| 1d | 2-3 |

**Output:**
```python
SwingPoint = {
    "index": int,       # bar index for click-to-locate
    "price": float,
    "bar_time": timestamp,
    "is_high": bool
}
```

**Optional Noise Filter:** ZigZag with ATR threshold (ignore moves < 0.8-1.5 × ATR)

---

### 3.2 Regime Classification (Trend/Range)

**Definitions:**

| Regime | Pattern |
|--------|---------|
| `uptrend` | Higher Highs + Higher Lows (HH+HL) dominant |
| `downtrend` | Lower Lows + Lower Highs (LL+LH) dominant |
| `range` | Mixed pattern, no clear direction |

**Algorithm:**
1. Take last `m` swing points (m = 6-10)
2. Count HH/HL vs LL/LH patterns
3. If trend consistency >= 70% → up/down
4. Else → range
5. Confidence = max_ratio or margin between top two

**Output:**
```python
MarketState = {
    "regime": "uptrend" | "downtrend" | "range",
    "confidence": 0.0 - 1.0
}
```

---

### 3.3 Support/Resistance Zones

**Principle:** Key levels are price BANDS, not exact prices.

**Algorithm:**
1. **Input:** swing_lows → support candidates, swing_highs → resistance candidates
2. **Clustering:** Group by price bins (bin_width = 0.5 × ATR)
3. **Zone generation:**
   - `zone.low = min(cluster_prices) - padding`
   - `zone.high = max(cluster_prices) + padding`
   - padding: 0.35 × ATR (1m) / 0.5 × ATR (1d)
4. **Scoring:** See Zone Strength below

### 3.4 Zone Strength Scoring (Enhanced)

Each zone has interpretable strength score:

| Factor | Weight | Description |
|--------|--------|-------------|
| `tests` | 0.3 | Number of times price touched zone |
| `rejections` | 0.3 | Number of times price reversed from zone |
| `reaction_magnitude` | 0.2 | Average reversal size (in ATR) |
| `recency` | 0.2 | Decay factor for older touches |

```python
strength = w1 * normalize(tests) +
           w2 * normalize(rejections) +
           w3 * normalize(avg_reaction / ATR) +
           w4 * recency_factor
```

**Output:**
```python
Zone = {
    "low": float,
    "high": float,
    "score": float,      # 0-1, normalized strength
    "touches": int,
    "rejections": int,   # NEW
    "last_reaction": float,  # NEW: magnitude in ATR
    "last_test_time": timestamp  # NEW: for recency
}
```

**UI Display:** Show only Key Zones (Top N by score, default N=5)

---

### 3.5 Range Box (Consolidation Detection)

**Conditions:**
- Regime = `range`
- Strong support zone + strong resistance zone exist
- Both zones touched >= 2 times

**Output:**
```python
range_box = {
    "support_zone": Zone,
    "resistance_zone": Zone,
    "duration_bars": int
}
```

---

### 3.6 Breakout State Machine (FSM)

**States:**

| State | Definition |
|-------|------------|
| `idle` | No breakout activity |
| `attempt` | Price crosses zone boundary |
| `confirmed` | 3-factor confirmation passed |
| `fakeout` | Attempt followed by quick return to zone |

#### 3.6.1 Attempt Breakout

Trigger conditions:
- close touches/briefly crosses zone boundary
- OR wick sweep (high/low beyond zone)

#### 3.6.2 Confirmed Breakout (3-Factor Confirmation)

**All three factors required:**

| Factor | Condition | Description |
|--------|-----------|-------------|
| Structure | `confirm_closes >= 2` | Consecutive closes outside zone |
| Volume | `RVOL >= 1.8` | Volume spike confirmation |
| Result | `result >= 0.6 ATR` | Meaningful price push |

**If RVOL = N/A:**
- Cannot confirm → stays as `attempt`
- Display: "Volume unavailable - confirmation pending"

#### 3.6.3 Fakeout Detection

Conditions (any):
- Within `fakeout_bars` (default: 3) after attempt, close returns inside zone
- OR: High effort + low result pattern (absorption failure)
- OR: Long wick + high volume but no follow-through

**Output:**
```python
Signal = {
    "type": "breakout_attempt" | "breakout_confirmed" | "fakeout",
    "direction": "up" | "down",
    "level": float,
    "confidence": float,
    "bar_time": timestamp,
    "bar_index": int,  # NEW: for click-to-locate
    "volume_quality": "confirmed" | "pending" | "unavailable"  # NEW
}
```

---

## 4. Behavior Inference (5-Class Probabilities)

> "Institutional behavior" is trading slang. Output = pattern-based probability inference.

### 4.1 Behavior Classes (Wyckoff-inspired)

| Class | Definition | Key Signals |
|-------|------------|-------------|
| **Accumulation** | Absorption at support | High vol + low down_eff + demand wicks |
| **Shakeout** | Stop hunt + reclaim | Break support → quick reclaim + long lower wick |
| **Markup** | Breakout + continuation | Confirmed breakout + HL structure + low vol pullback |
| **Distribution** | Supply at resistance | High vol + low up_eff + rejection wicks |
| **Markdown** | Breakdown + continuation | Confirmed breakdown + LH structure + weak bounces |

### 4.2 Score Components

#### (A) Accumulation Score
```
+ near_support (0/1)
+ RVOL (normalized)
+ (1 - down_eff_norm)
+ wick_ratio_low
+ effort_high_result_low (0/1)  # NEW: VSA absorption
```

#### (B) Shakeout Score
```
+ sweep_support (0/1): low < support.low
+ reclaim (0/1): close >= support.low
+ wick_ratio_low
+ RVOL
```

#### (C) Markup Score
```
+ breakout_confirmed (0/1)
+ hl_count_norm
+ (advance_vol - pullback_vol)
+ up_eff_norm
```

#### (D) Distribution Score
```
+ near_resistance (0/1)
+ RVOL
+ (1 - up_eff_norm)
+ wick_ratio_up
+ effort_high_result_low (0/1)  # NEW: VSA absorption
```

#### (E) Markdown Score
```
+ breakdown_confirmed (0/1)
+ ll_lh_count_norm
+ low pullback_vol
+ down_eff_norm
```

### 4.3 Score → Probability

```python
# Normalize scores (z-score or min-max)
normalized_scores = normalize([acc, shake, markup, dist, markdown])

# Softmax to get probability distribution
probabilities = softmax(normalized_scores)

# Output
dominant = argmax(probabilities)
evidence = top_3_evidence_for(dominant)
```

**Output:**
```python
behavior = {
    "probabilities": {
        "accumulation": 0.21,
        "shakeout": 0.62,
        "markup": 0.06,
        "distribution": 0.09,
        "markdown": 0.02
    },
    "dominant": "shakeout",
    "evidence": [...]  # See Evidence System
}
```

---

## 5. Evidence System (Traceable Explanation)

**Principle:** Probabilities alone explain nothing. Every conclusion must have traceable evidence.

### 5.1 Evidence Structure

```python
Evidence = {
    "type": str,          # VOLUME_SPIKE, REJECTION, SWEEP, ABSORPTION, BREAKOUT
    "behavior": str,      # Which behavior this supports
    "severity": str,      # low, med, high
    "bar_time": timestamp,
    "bar_index": int,     # For click-to-locate in chart
    "metrics": {
        "rvol": float,
        "wick_ratio": float,
        "effort": float,
        "result": float
    },
    "note_key": str       # i18n key for explanation
}
```

### 5.2 Evidence Templates

| Behavior | Note Key | Trigger |
|----------|----------|---------|
| Accumulation | `evidence.accumulation.absorption` | High effort + low result near support |
| Shakeout | `evidence.shakeout.sweep_reclaim` | Sweep below support + reclaim with elevated RVOL |
| Markup | `evidence.markup.low_vol_pullback` | Low effort pullback in uptrend |
| Distribution | `evidence.distribution.absorption` | High effort + low result near resistance |
| Markdown | `evidence.markdown.weak_bounce` | Weak bounce on low volume in downtrend |

### 5.3 Click-to-Locate Anchors

Every evidence must include:
- `bar_index`: integer index for chart highlighting
- `bar_time`: timestamp for tooltip
- `zone_id` or `level`: related structure element

---

## 6. Stateful Narrative (Timeline)

### 6.1 Purpose

Solve the "LLM forgets context" problem: system remembers previous state and tracks evolution.

### 6.2 State Store (per ticker + timeframe)

```python
State = {
    "last_regime": str,
    "last_zones_hash": str,
    "last_behavior_probs": Dict[str, float],
    "last_breakout_state": str,
    "last_updated_ts": timestamp
}
```

### 6.3 Critical Events (Hard Events)

Write to timeline when ANY:
- Regime changed (e.g., range → uptrend)
- Dominant behavior changed (e.g., shakeout → distribution)
- Breakout state changed (attempt → confirmed, attempt → fakeout)
- Probability delta >= 0.12

### 6.4 Soft Events (Narrative Events) — NEW

To avoid empty timeline and maintain product feel:

| Event Type | Trigger |
|------------|---------|
| `zone_approached` | Price within 0.5 ATR of zone |
| `zone_tested` | Price touched zone |
| `zone_rejected` | Price reversed from zone |
| `zone_accepted` | Price closed through zone |
| `spring` | Sweep below support + reclaim (Wyckoff term) |
| `upthrust` | Sweep above resistance + rejection (Wyckoff term) |
| `absorption_clue` | High effort + low result detected |
| `volume_spike` | RVOL >= 2.0 |
| `volume_dryup` | RVOL <= 0.5 for 3+ bars |
| `new_swing` | New swing high/low formed |

### 6.5 Timeline Event Structure

```python
TimelineEvent = {
    "ts": timestamp,
    "event_type": str,
    "delta": float,          # For prob changes
    "reason_key": str,       # i18n key
    "bar_index": int,        # For click-to-locate
    "severity": str          # info, warning, critical
}
```

---

## 7. Playbook Generation (Conditional Plans)

### 7.1 Template Logic by Regime

**Uptrend:**
- Plan A: Pullback to support → continuation
- Plan B: Breakout above resistance → new leg

**Downtrend:**
- Plan A: Rally to resistance → rejection
- Plan B: Breakdown below support → new leg

**Range:**
- Plan A: Support bounce
- Plan B: Resistance fade

### 7.2 Plan Structure

```python
PlaybookPlan = {
    "name": "Plan A" | "Plan B",
    "condition_key": str,      # i18n key for condition
    "level": float,            # Key price level
    "target": float,           # Target price
    "invalidation": float,     # Stop level
    "risk_key": str            # i18n key for risk warning
}
```

### 7.3 Risk Keys

| Key | Description |
|-----|-------------|
| `risk.noise_high_1m` | 1-minute timeframe has high noise |
| `risk.liquidity_low` | Low liquidity may cause slippage |
| `risk.event_pending` | Potential market-moving events |
| `risk.volume_unconfirmed` | Volume data unavailable |
| `risk.false_breakout` | Fakeout risk elevated |
| `risk.trend_continuation` | Counter-trend risk |

---

## 8. Multi-Timeframe Logic (Future Enhancement)

### 8.1 Core Principle

- **1D**: Primary narrative (structure/regime/behavior/playbook)
- **1m/5m**: Execution confirmation (volume, breakout quality, zone interaction)

### 8.2 Output Structure (Future)

```python
AnalysisReport = {
    "primary_tf_summary": {...},   # From 1D
    "entry_tf_summary": {...},     # From 1m/5m
    "alignment": str               # aligned, conflicting, neutral
}
```

> MVP: Single timeframe. Multi-TF is V2 enhancement.

---

## 9. Default Parameters (MVP)

### 9.1 Common Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `atr_period` | 14 | Standard ATR calculation |
| `volume_period` | 30 (1m), 20 (1d) | Volume MA window |
| `swing_n` | 4 (1m), 2-3 (1d) | Fractal order |
| `regime_m` | 6 | Swing points for regime |
| `max_zones` | 5 | Top N zones to display |

### 9.2 Breakout Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `volume_threshold` | 1.8 | RVOL for confirmation |
| `result_threshold` | 0.6 | ATR multiple for result |
| `confirm_closes` | 2 | Consecutive closes needed |
| `fakeout_bars` | 3 | Quick reversal window |

### 9.3 Timeline Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `probability_threshold` | 0.12 | Delta for event emission |
| `zone_approach_atr` | 0.5 | ATR multiple for "approached" |

### 9.4 Zone Parameters by Timeframe

| Timeframe | Bin Width | Padding |
|-----------|-----------|---------|
| 1m | 0.5 × ATR | 0.35 × ATR |
| 5m | 0.5 × ATR | 0.4 × ATR |
| 1d | 0.5 × ATR | 0.5 × ATR |

---

## 10. Algorithm Summary (Product Description)

### English

> KLineLens uses a deterministic market structure engine combining swing-based zone clustering, regime classification, and a volume-confirmed breakout state machine. It infers Wyckoff-style behaviors using probabilistic scoring with VSA (Volume Spread Analysis) principles, and outputs traceable evidence linked to specific candles.

### Chinese

> KLineLens 使用确定性结构推断引擎：波段聚类支撑阻力、趋势状态识别、以及成交量确认的突破状态机。系统通过 VSA（量价分析）原则进行概率化评分推断 Wyckoff 行为，并提供可追溯证据链定位到具体 K 线。

### Prohibited Expressions

- "AI predicts price"
- "Guaranteed signal"
- "100% accurate"
- "稳赚" / "必赚"

---

## 11. Signal Evaluation System (Prediction Tracking)

### 11.1 Purpose

Track prediction accuracy over time to:
- Validate engine performance
- Identify which signal types are most reliable
- Provide feedback loop for parameter tuning
- Build user confidence through transparency

### 11.2 Evaluation Workflow

```
1. Signal Generated → 2. User Records Prediction → 3. Market Moves → 4. User Evaluates Result
```

### 11.3 What Gets Evaluated

| Evaluable Signal | Criteria |
|------------------|----------|
| `breakout_confirmed` | Did breakout lead to continuation? |
| `fakeout` | Did price return to range as predicted? |
| `breakout_attempt` | Did attempt confirm or fail? |
| `behavior_dominant` | Did predicted behavior play out? |

### 11.4 Evaluation Criteria

#### Result Types

| Result | Definition |
|--------|------------|
| `target_hit` | Price reached target within evaluation window |
| `invalidation_hit` | Price hit stop/invalidation level |
| `partial_correct` | Direction correct, target not reached |
| `direction_wrong` | Price moved opposite to prediction |
| `timeout` | No significant move within window |

#### Evaluation Window

| Timeframe | Window | Description |
|-----------|--------|-------------|
| 1m | 60 bars (1 hour) | Short-term scalp evaluation |
| 5m | 48 bars (4 hours) | Intraday evaluation |
| 1d | 10 bars (2 weeks) | Swing evaluation |

### 11.5 Statistics Calculation

```python
accuracy_rate = correct / (correct + incorrect)  # Excludes pending

by_signal_type = {
    signal_type: {
        "total": count,
        "correct": correct_count,
        "accuracy": correct_count / count
    }
    for signal_type in signal_types
}

# Confidence-weighted accuracy (optional enhancement)
weighted_accuracy = sum(confidence * is_correct) / sum(confidence)
```

### 11.6 Database Schema

```sql
CREATE TABLE signal_evaluations (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    tf TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    signal_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    predicted_behavior TEXT NOT NULL,
    entry_price REAL NOT NULL,
    target_price REAL NOT NULL,
    invalidation_price REAL NOT NULL,
    confidence REAL NOT NULL,
    notes TEXT,
    status TEXT DEFAULT 'pending',
    result TEXT,
    actual_outcome TEXT,
    evaluation_notes TEXT,
    evaluated_at TIMESTAMP,
    INDEX idx_ticker_tf (ticker, tf),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### 11.7 Display Recommendations

**Table Columns:**
1. 时间 (Created At)
2. 信号类型 (Signal Type)
3. 方向 (Direction)
4. 入场/目标/止损 (Prices)
5. 状态 (Status)
6. 结果 (Result)
7. 原因 (Notes)

**Statistics Display:**
- 总预测数 / 正确 / 错误 / 待评估
- 准确率百分比（带进度条）
- 按信号类型分解

---

## 12. Frontend Caching Strategy

### 12.1 Evidence & Timeline Daily Cache

**Purpose:** Preserve accumulated evidence/timeline across page refreshes within same trading day.

**Cache Key Format:**
```
klinelens:evidence:{ticker}:{tf}:{date}
klinelens:timeline:{ticker}:{tf}:{date}
```

**Cache Structure:**
```typescript
interface CachedData {
  date: string;           // YYYY-MM-DD
  ticker: string;
  tf: string;
  items: Evidence[] | TimelineEvent[];
  lastUpdated: string;    // ISO timestamp
}
```

### 12.2 Cache Lifecycle

1. **On Page Load:**
   - Check localStorage for today's cache
   - If exists and date matches today → load cached items
   - If date is old → clear cache, start fresh

2. **On Data Refresh:**
   - Merge new items with cached items (dedupe by bar_index)
   - Update cache in localStorage
   - Update lastUpdated timestamp

3. **Daily Cleanup:**
   - Compare cache date with today
   - If different → clear and reset

### 12.3 Merge Strategy

```typescript
function mergeEvidence(cached: Evidence[], fresh: Evidence[]): Evidence[] {
  const merged = [...cached];
  for (const item of fresh) {
    const exists = merged.some(e => e.bar_index === item.bar_index && e.type === item.type);
    if (!exists) {
      merged.push(item);
    }
  }
  return merged.sort((a, b) => b.bar_index - a.bar_index);  // Newest first
}
```

### 12.4 Storage Limits

- Max items per cache: 100
- When exceeded: Keep most recent 100, discard oldest
- localStorage quota: ~5MB per origin

---

## Appendix: Key Terms

| Term | Definition |
|------|------------|
| RVOL | Relative Volume (volume strength vs normal) |
| VSA | Volume Spread Analysis (量价分析) |
| Wyckoff | 5-phase behavior model (Accumulation/Shakeout/Markup/Distribution/Markdown) |
| FSM | Finite State Machine for breakout state transitions |
| Evidence | Traceable explanation linked to specific candles |
| Timeline | Structural narrative flow recording significant changes |
| ATR | Average True Range (volatility measure) |
| Effort | Volume intensity (RVOL) |
| Result | Price movement magnitude (range / ATR) |
| Signal Evaluation | Prediction tracking system for accuracy measurement |
