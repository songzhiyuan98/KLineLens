# KLineLens — Engine Spec

> Algorithm + Financial Logic: Structure Recognition + Behavior Inference + Stateful Narrative

---

## 0. Design Principles (Financial Constraints)

| Principle | Description |
|-----------|-------------|
| **Regime First** | Determine trend/range before interpreting behavior signals |
| **Zones over Lines** | Key levels are price BANDS, not single prices |
| **Breakout Stages** | attempt → confirmed → fakeout (don't confirm too easily) |
| **Probability Output** | Never claim certainty; output probabilities + evidence |
| **Invalidation Required** | Every playbook must have explicit invalidation conditions |
| **1m Noise Warning** | Always include risk notes for high-noise timeframes |

---

## 1. Input Data & Preprocessing

### 1.1 Bar Structure
```python
Bar = {
    "t": "2026-01-13T18:00:00Z",  # UTC timestamp
    "o": float,  # open
    "h": float,  # high
    "l": float,  # low
    "c": float,  # close
    "v": float   # volume
}
```

### 1.2 Preprocessing Steps
1. Sort by timestamp ascending
2. Remove duplicates
3. Handle gaps: MVP allows gaps, report includes `data_gaps` flag if detected
4. Timezone: All timestamps in UTC (frontend localizes for display)

---

## 2. Feature Layer (Interpretable Metrics)

### 2.1 Volatility & Range
| Feature | Formula | Purpose |
|---------|---------|---------|
| `ATR(14)` | Average True Range over 14 bars | Zone width, ZigZag threshold |
| `range` | `high - low` | Current bar volatility |

### 2.2 Volume Relative Indicators
| Feature | Formula | Interpretation |
|---------|---------|----------------|
| `avg_vol` | `SMA(volume, N)` | N=30 for 1m, N=20 for 1d |
| `volume_ratio` | `volume / avg_vol` | >1.5 = high volume, <0.7 = low volume |

### 2.3 Candlestick Structure
| Feature | Formula | Interpretation |
|---------|---------|----------------|
| `body` | `abs(close - open)` | Price movement direction strength |
| `body_ratio` | `body / range` | 0 = doji, 1 = marubozu |
| `upper_wick` | `high - max(open, close)` | Supply pressure above |
| `lower_wick` | `min(open, close) - low` | Demand absorption below |
| `wick_ratio_up` | `upper_wick / range` | High = rejection from above |
| `wick_ratio_low` | `lower_wick / range` | High = demand recovery |

### 2.4 Move Efficiency (Tape-reading Proxy)
| Feature | Formula | Interpretation |
|---------|---------|----------------|
| `up_eff` | `max(close - open, 0) / volume` | Low with high volume = supply absorption |
| `down_eff` | `max(open - close, 0) / volume` | Low with high volume = demand absorption |

---

## 3. Structure Layer (Market Structure Detection)

### 3.1 Swing Points (Fractal Method)

**Algorithm:**
- Parameter: `n` (window size, look left/right n bars)
- `swing_high`: bar where `high` is the highest in `[i-n, i+n]`
- `swing_low`: bar where `low` is the lowest in `[i-n, i+n]`

**Default Parameters:**
| Timeframe | n |
|-----------|---|
| 1m | 4 |
| 5m | 3 |
| 1d | 2-3 |

**Output:**
```python
swing_highs: List[{"t": timestamp, "price": float}]
swing_lows: List[{"t": timestamp, "price": float}]
```

**Optional Noise Filter:** ZigZag with ATR threshold (ignore moves < 0.8-1.5 * ATR)

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
3. Regime = argmax(pattern_count)
4. Confidence = max_ratio or margin between top two

**Output:**
```python
{
    "regime": "uptrend" | "downtrend" | "range",
    "confidence": 0.0 - 1.0
}
```

---

### 3.3 Support/Resistance Zones

**Principle:** Key levels are price BANDS, not exact prices.

**Algorithm:**
1. **Input:** swing_lows → support candidates, swing_highs → resistance candidates
2. **Clustering:** Group by price bins (bin_width = 0.5 * ATR)
3. **Zone generation:**
   - `zone.low = min(cluster_prices) - w`
   - `zone.high = max(cluster_prices) + w`
   - `w = 0.35 * ATR` (adjustable)
4. **Scoring:**
   - `touches` = cluster point count
   - `reaction_strength` = avg reversal magnitude after touch
   - `score = normalize(a * touches + b * reaction_strength)`

**Output:**
```python
support_zones: List[{"low": float, "high": float, "score": float, "touches": int}]
resistance_zones: List[{"low": float, "high": float, "score": float, "touches": int}]
# Return Top K zones (K = 3-6)
```

---

### 3.4 Range Box (Consolidation Detection)

**Conditions:**
- Regime = `range`
- Strong support zone + strong resistance zone exist
- Both zones touched >= 2 times

**Output:**
```python
range_box: {
    "support_zone": Zone,
    "resistance_zone": Zone,
    "duration_bars": int
}
```

---

### 3.5 Breakout / Fakeout State Machine

**States:**
| State | Definition |
|-------|------------|
| `idle` | No breakout activity |
| `attempt` | Price crosses zone boundary |
| `confirmed` | Close outside zone + volume + duration |
| `fakeout` | Attempt followed by quick return to zone |

**Confirmation Rules (Upside Breakout Example):**
```
attempt:
  - high > resistance.high

confirmed:
  - close > resistance.high + epsilon
  - volume_ratio >= Vth (default: 1.8)
  - consecutive Nc closes outside (default: Nc = 2)

fakeout:
  - Within M bars (default: M = 3) after attempt
  - close returns inside zone
  - OR: long upper wick + high volume but no follow-through
```

**Output:**
```python
signals: List[{
    "type": "breakout_attempt" | "breakout_confirmed" | "fakeout",
    "direction": "up" | "down",
    "level": float,
    "confidence": float,
    "bar_time": timestamp
}]
```

---

## 4. Behavior Inference (5-Class Probabilities)

> "Institutional behavior" is trading slang. Output = pattern-based probability inference.

### 4.1 Behavior Classes (Wyckoff-inspired)

| Class | Definition | Key Signals |
|-------|------------|-------------|
| **Accumulation** | Absorption at support | High volume + low down_eff + demand wicks |
| **Shakeout** | Stop hunt + reclaim | Break support → quick reclaim + long lower wick |
| **Markup** | Breakout + continuation | Confirmed breakout + HL structure + pullback on low volume |
| **Distribution** | Supply at resistance | High volume + low up_eff + rejection wicks |
| **Markdown** | Breakdown + continuation | Confirmed breakdown + LH structure + weak bounces |

### 4.2 Score Components

#### (A) Accumulation Score
```
+ near_support (0/1)
+ volume_ratio (normalized)
+ (1 - down_eff_norm)
+ wick_ratio_low
```
**Evidence template:** "High volume at support but price won't drop (low down_eff)"

#### (B) Shakeout Score
```
+ sweep_support (0/1): low < support.low
+ reclaim (0/1): close >= support.low
+ wick_ratio_low
+ volume_ratio
```
**Evidence template:** "Broke support then quickly reclaimed (sweep + reclaim)"

#### (C) Markup Score
```
+ breakout_confirmed (0/1)
+ hl_count_norm
+ (advance_vol - pullback_vol)
+ up_eff_norm
```
**Evidence template:** "Breakout confirmed + higher lows + pullback on low volume"

#### (D) Distribution Score
```
+ near_resistance (0/1)
+ volume_ratio
+ (1 - up_eff_norm)
+ wick_ratio_up
+ rejection_count_norm
```
**Evidence template:** "High volume at resistance but price won't rise (low up_eff)"

#### (E) Markdown Score
```
+ breakdown_confirmed (0/1)
+ ll_lh_count_norm
+ low pullback_vol
+ down_eff_norm
```
**Evidence template:** "Breakdown confirmed + lower highs + weak bounces"

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
behavior: {
    "probabilities": {
        "accumulation": 0.21,
        "shakeout": 0.62,
        "markup": 0.06,
        "distribution": 0.09,
        "markdown": 0.02
    },
    "dominant": "shakeout",
    "evidence": [
        {
            "behavior": "shakeout",
            "bar_time": "...",
            "volume_ratio": 2.1,
            "wick_ratio": 0.67,
            "note_key": "broke_support_then_reclaimed"
        }
    ]
}
```

---

## 5. Stateful Narrative (Timeline State Machine)

### 5.1 Purpose
Solve the "LLM forgets context" problem: system remembers previous state and tracks evolution.

### 5.2 State Store (per ticker + timeframe)
```python
State = {
    "last_regime": str,
    "last_zones_hash": str,
    "last_behavior_probs": Dict[str, float],
    "last_breakout_state": str,
    "last_updated_ts": timestamp
}
```

### 5.3 Event Write Rules (Avoid Noise)
Write to timeline only when ANY condition is met:
- Dominant behavior changed (e.g., shakeout → distribution)
- Dominant probability delta >= 0.12
- Breakout state changed (attempt → confirmed, attempt → fakeout)
- Regime changed (range → uptrend)

### 5.4 Timeline Event Structure
```python
timeline_event = {
    "ts": timestamp,
    "event_type": "shakeout_prob_up" | "regime_change" | "breakout_confirmed" | ...,
    "delta": float,  # probability change
    "reason_key": str  # template key for i18n
}
```

---

## 6. Playbook Generation (Conditional Trading Plans)

### 6.1 Template Logic

**Plan A (Trend Continuation / Breakout):**
```
If: breakout_confirmed above {resistance_zone.high} with volume_ratio >= {Vth}
Target: next resistance zone OR current_price + k * ATR
Invalidation: close back into zone OR below {resistance_zone.low}
Risk: {risk_key}
```

**Plan B (Invalidation / Reversal):**
```
If: breakdown_confirmed below {support_zone.low} with volume_ratio >= {Vth}
Target: next support zone OR current_price - k * ATR
Invalidation: close back above {support_zone.high}
Risk: {risk_key}
```

### 6.2 Risk Keys
| Key | Description |
|-----|-------------|
| `noise_high_1m` | 1-minute timeframe has high noise |
| `liquidity_risk` | Low liquidity may cause slippage |
| `event_risk` | Potential market-moving events |

### 6.3 Output
```python
playbook: [
    {
        "name_key": "plan_a",
        "if_key": "if_breakout_confirmed",
        "level": 253.3,
        "target": 259.1,
        "invalidation": 251.8,
        "risk_key": "noise_high_1m"
    },
    {
        "name_key": "plan_b",
        "if_key": "if_breakdown_confirmed",
        "level": 246.0,
        "target": 241.8,
        "invalidation": 247.2,
        "risk_key": "liquidity_risk"
    }
]
```

---

## 7. Default Parameters (MVP)

### 7.1 1-Minute Timeframe
| Parameter | Value |
|-----------|-------|
| Swing fractal n | 4 |
| Volume SMA N | 30 |
| Breakout volume threshold Vth | 1.8 |
| Confirm candles Nc | 2 |
| Fakeout window M | 3 |
| Zone width w | 0.35 * ATR |

### 7.2 1-Day Timeframe
| Parameter | Value |
|-----------|-------|
| Swing fractal n | 2-3 |
| Volume SMA N | 20 |
| Zone width w | 0.5 * ATR |

> All parameters must be configurable. Start with defaults, allow override via API params in future.
