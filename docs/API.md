# KLineLens — API Contract (v1)

> REST API specification for frontend-backend communication.

---

## Base Configuration

| Item | Value |
|------|-------|
| Base URL | `/v1` |
| Response Format | JSON |
| Authentication | None (MVP) |
| Rate Limiting | Provider-dependent |

---

## Error Response Format

All errors return this structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TICKER_INVALID` | 400 | Ticker format invalid or not found |
| `TIMEFRAME_INVALID` | 400 | Unsupported timeframe value |
| `NO_DATA` | 404 | No bars available for ticker/timeframe |
| `PROVIDER_RATE_LIMITED` | 429 | Data provider rate limit exceeded |
| `PROVIDER_ERROR` | 502 | Data provider returned an error |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Endpoints

### 1. GET `/v1/bars` — Fetch OHLCV Bars

Fetch raw candlestick data for a ticker.

#### Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Stock symbol (e.g., "TSLA", "AAPL") |
| `tf` | enum | Yes | Timeframe: `1m`, `5m`, `1d` |
| `window` | string | No | Lookback period (default: `5d` for 1m, `1y` for 1d) |

#### Response 200
```json
{
  "ticker": "TSLA",
  "tf": "1m",
  "bar_count": 1950,
  "bars": [
    {
      "t": "2026-01-13T14:30:00Z",
      "o": 245.50,
      "h": 246.20,
      "l": 245.30,
      "c": 246.00,
      "v": 125000
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Requested ticker symbol |
| `tf` | string | Timeframe |
| `bar_count` | int | Number of bars returned |
| `bars` | array | Array of Bar objects |

#### Bar Object

| Field | Type | Description |
|-------|------|-------------|
| `t` | string | ISO 8601 UTC timestamp |
| `o` | float | Open price |
| `h` | float | High price |
| `l` | float | Low price |
| `c` | float | Close price |
| `v` | float | Volume (0 if unavailable) |

---

### 2. POST `/v1/analyze` — Run Analysis

Run full structure + behavior analysis on a ticker.

#### Request Body
```json
{
  "ticker": "TSLA",
  "tf": "1m",
  "window": "5d"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock symbol |
| `tf` | enum | Yes | Timeframe: `1m`, `5m`, `1d` |
| `window` | string | No | Lookback period |

#### Response 200 — AnalysisReport

```json
{
  "ticker": "TSLA",
  "tf": "1m",
  "generated_at": "2026-01-13T18:30:00Z",
  "bar_count": 1950,
  "data_gaps": false,
  "volume_quality": "reliable",

  "market_state": {
    "regime": "range",
    "confidence": 0.74
  },

  "zones": {
    "support": [
      {
        "low": 245.20,
        "high": 246.10,
        "score": 0.91,
        "touches": 4,
        "rejections": 3,
        "last_reaction": 1.2,
        "last_test_time": "2026-01-13T16:45:00Z"
      }
    ],
    "resistance": [
      {
        "low": 252.60,
        "high": 253.30,
        "score": 0.86,
        "touches": 3,
        "rejections": 2,
        "last_reaction": 0.9,
        "last_test_time": "2026-01-13T17:30:00Z"
      }
    ]
  },

  "signals": [
    {
      "type": "breakout_attempt",
      "direction": "up",
      "level": 253.30,
      "confidence": 0.68,
      "bar_time": "2026-01-13T17:45:00Z",
      "bar_index": 385,
      "volume_quality": "confirmed"
    }
  ],

  "behavior": {
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
        "type": "SWEEP",
        "behavior": "shakeout",
        "severity": "high",
        "bar_time": "2026-01-13T16:22:00Z",
        "bar_index": 298,
        "metrics": {
          "rvol": 2.1,
          "wick_ratio": 0.67,
          "effort": 2.1,
          "result": 0.4
        },
        "note": "Broke support then quickly reclaimed"
      }
    ]
  },

  "timeline": [
    {
      "ts": "2026-01-13T16:22:00Z",
      "event_type": "spring",
      "delta": 0.0,
      "reason": "Support sweep with quick reclaim",
      "bar_index": 298,
      "severity": "critical"
    },
    {
      "ts": "2026-01-13T17:00:00Z",
      "event_type": "zone_tested",
      "delta": 0.0,
      "reason": "Resistance tested",
      "bar_index": 340,
      "severity": "info"
    }
  ],

  "playbook": [
    {
      "name": "Plan A",
      "condition": "Breakout confirmed above 253.30 with volume",
      "level": 253.30,
      "target": 259.10,
      "invalidation": 251.80,
      "risk": "1-minute timeframe has high noise"
    },
    {
      "name": "Plan B",
      "condition": "Breakdown confirmed below 246.00 with volume",
      "level": 246.00,
      "target": 241.80,
      "invalidation": 247.20,
      "risk": "Low liquidity may cause slippage"
    }
  ]
}
```

---

## Schema Definitions

### AnalysisReport

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock symbol |
| `tf` | string | Timeframe |
| `generated_at` | string | ISO 8601 timestamp when report was generated |
| `bar_count` | int | Number of bars analyzed |
| `data_gaps` | bool | True if data gaps were detected |
| `volume_quality` | string | `reliable`, `partial`, `unavailable` |
| `market_state` | MarketState | Current market regime |
| `zones` | Zones | Support and resistance zones |
| `signals` | Signal[] | Breakout/fakeout signals |
| `behavior` | Behavior | Behavior inference results |
| `timeline` | TimelineEvent[] | Recent structural changes |
| `playbook` | PlaybookPlan[] | Conditional trading plans |

### MarketState

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `regime` | string | `uptrend`, `downtrend`, `range` | Current market structure |
| `confidence` | float | 0.0 - 1.0 | Confidence in regime classification |

### Zone (Enhanced)

| Field | Type | Description |
|-------|------|-------------|
| `low` | float | Lower bound of price zone |
| `high` | float | Upper bound of price zone |
| `score` | float | Zone strength score (0-1) |
| `touches` | int | Number of times zone was tested |
| `rejections` | int | Number of times price reversed from zone |
| `last_reaction` | float | Magnitude of last reaction (in ATR) |
| `last_test_time` | string | Timestamp of last zone test |

### Zones

| Field | Type | Description |
|-------|------|-------------|
| `support` | Zone[] | Support zones (sorted by score desc) |
| `resistance` | Zone[] | Resistance zones (sorted by score desc) |

### Signal (Enhanced)

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `breakout_attempt`, `breakout_confirmed`, `fakeout` |
| `direction` | string | `up` or `down` |
| `level` | float | Price level of the signal |
| `confidence` | float | Signal confidence (0-1) |
| `bar_time` | string | When the signal occurred |
| `bar_index` | int | Bar index for click-to-locate |
| `volume_quality` | string | `confirmed`, `pending`, `unavailable` |

### Behavior

| Field | Type | Description |
|-------|------|-------------|
| `probabilities` | object | Probability for each behavior class |
| `dominant` | string | Highest probability behavior |
| `evidence` | Evidence[] | Supporting evidence (max 3) |

### BehaviorProbabilities

| Field | Type | Description |
|-------|------|-------------|
| `accumulation` | float | Probability of accumulation |
| `shakeout` | float | Probability of shakeout |
| `markup` | float | Probability of markup |
| `distribution` | float | Probability of distribution |
| `markdown` | float | Probability of markdown |

### Evidence (Enhanced)

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `VOLUME_SPIKE`, `REJECTION`, `SWEEP`, `ABSORPTION`, `BREAKOUT` |
| `behavior` | string | Which behavior this evidence supports |
| `severity` | string | `low`, `med`, `high` |
| `bar_time` | string | When the evidence was observed |
| `bar_index` | int | Bar index for click-to-locate |
| `metrics` | object | Relevant metrics (see below) |
| `note` | string | Human-readable explanation |

### Evidence Metrics

| Field | Type | Description |
|-------|------|-------------|
| `rvol` | float | Relative volume (RVOL) |
| `wick_ratio` | float | Relevant wick ratio |
| `effort` | float | Volume effort (RVOL) |
| `result` | float | Price result (range/ATR) |

### TimelineEvent (Enhanced)

| Field | Type | Description |
|-------|------|-------------|
| `ts` | string | Event timestamp |
| `event_type` | string | Event type enum (see below) |
| `delta` | float | Probability change magnitude |
| `reason` | string | Human-readable reason |
| `bar_index` | int | Bar index for click-to-locate |
| `severity` | string | `info`, `warning`, `critical` |

#### Event Types — Critical (Hard Events)
- `regime_change` - Market regime changed
- `behavior_change` - Dominant behavior changed
- `breakout_confirmed` - Breakout confirmed
- `breakdown_confirmed` - Breakdown confirmed
- `fakeout_detected` - Fakeout detected
- `shakeout_prob_up`, `shakeout_prob_down`
- `accumulation_prob_up`, `accumulation_prob_down`
- `markup_prob_up`, `markup_prob_down`
- `distribution_prob_up`, `distribution_prob_down`
- `markdown_prob_up`, `markdown_prob_down`

#### Event Types — Narrative (Soft Events)
- `zone_approached` - Price approaching key zone
- `zone_tested` - Price tested zone
- `zone_rejected` - Price rejected from zone
- `zone_accepted` - Price closed through zone
- `spring` - Wyckoff spring (sweep below support + reclaim)
- `upthrust` - Wyckoff upthrust (sweep above resistance + reject)
- `absorption_clue` - High effort + low result detected
- `volume_spike` - RVOL >= 2.0
- `volume_dryup` - Volume dried up
- `volume_low` - Volume below average
- `new_swing_high` - New swing high formed
- `new_swing_low` - New swing low formed
- `initialized` - Initial analysis state

### PlaybookPlan

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | "Plan A" or "Plan B" |
| `condition` | string | Entry condition description |
| `level` | float | Key price level |
| `target` | float | Target price |
| `invalidation` | float | Stop/invalidation level |
| `risk` | string | Risk warning |

---

## Volume Quality Handling

The API includes volume quality awareness throughout:

| Quality | Meaning | Effect |
|---------|---------|--------|
| `reliable` | Volume data from reliable source (TwelveData, Polygon) | Full confirmation available |
| `partial` | Volume may be delayed or incomplete | Reduced confidence |
| `unavailable` | No volume data | Breakout cannot be confirmed |

**Frontend should display:**
- When `volume_quality = "unavailable"`: "Volume N/A - confirmation unavailable"
- When `volume_quality = "pending"`: "Awaiting volume confirmation"

---

## Example Requests

### Fetch 1-minute bars
```bash
curl "http://localhost:8000/v1/bars?ticker=TSLA&tf=1m&window=5d"
```

### Run analysis
```bash
curl -X POST "http://localhost:8000/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA", "tf": "1m", "window": "5d"}'
```

---

---

### 3. GET `/v1/eh-context` — Get Extended Hours Context

Fetch premarket/afterhours context for a ticker.

#### Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Stock symbol (e.g., "TSLA") |
| `use_eh` | bool | No | Force Yahoo EH data (default: true for 1m/5m) |

#### Response 200 — EHContext

```json
{
  "ticker": "TSLA",
  "timestamp": "2026-01-15T14:30:00Z",
  "session_status": "regular_hours",
  "levels": {
    "yc": 245.50,
    "yh": 248.20,
    "yl": 243.10,
    "pmh": 246.80,
    "pml": 244.20,
    "ahh": 247.50,
    "ahl": 244.80,
    "gap": 1.30,
    "gap_pct": 0.53
  },
  "premarket_regime": "trend_continuation",
  "bias": "bullish",
  "bias_confidence": 0.72,
  "key_zones": [
    {
      "level": 245.50,
      "role": "yc",
      "importance": "critical"
    },
    {
      "level": 246.80,
      "role": "pmh",
      "importance": "high"
    }
  ],
  "ah_risk": {
    "level": "medium",
    "reason": "AH range 1.1% with moderate volume"
  },
  "opening_action": {
    "bias": "bullish",
    "watch_level": 246.80,
    "invalidation": 244.20
  }
}
```

#### Response 404

```json
{
  "error": {
    "code": "NO_EH_DATA",
    "message": "Extended hours data not available for this ticker"
  }
}
```

---

### 4. POST `/v1/signal-evaluation` — Record Signal Prediction

Record a new signal prediction for later evaluation.

#### Request Body
```json
{
  "ticker": "TSLA",
  "tf": "1m",
  "signal_type": "breakout_confirmed",
  "direction": "up",
  "predicted_behavior": "markup",
  "entry_price": 253.30,
  "target_price": 259.10,
  "invalidation_price": 251.80,
  "confidence": 0.72,
  "notes": "Breakout with volume confirmation"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock symbol |
| `tf` | enum | Yes | Timeframe: `1m`, `5m`, `1d` |
| `signal_type` | string | Yes | Signal type (breakout_confirmed, fakeout, etc.) |
| `direction` | string | Yes | `up` or `down` |
| `predicted_behavior` | string | Yes | Expected behavior outcome |
| `entry_price` | float | Yes | Entry price level |
| `target_price` | float | Yes | Target price |
| `invalidation_price` | float | Yes | Stop/invalidation level |
| `confidence` | float | Yes | Prediction confidence (0-1) |
| `notes` | string | No | Additional notes |

#### Response 201
```json
{
  "id": "eval_20260114_001",
  "ticker": "TSLA",
  "tf": "1m",
  "created_at": "2026-01-14T18:30:00Z",
  "signal_type": "breakout_confirmed",
  "direction": "up",
  "predicted_behavior": "markup",
  "entry_price": 253.30,
  "target_price": 259.10,
  "invalidation_price": 251.80,
  "confidence": 0.72,
  "notes": "Breakout with volume confirmation",
  "status": "pending",
  "result": null,
  "actual_outcome": null,
  "evaluation_notes": null,
  "evaluated_at": null
}
```

---

### 4. GET `/v1/signal-evaluations` — Get Signal Evaluation History

Retrieve signal evaluation records for a ticker.

#### Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Stock symbol |
| `tf` | enum | No | Filter by timeframe |
| `status` | enum | No | Filter by status: `pending`, `correct`, `incorrect` |
| `limit` | int | No | Max records (default: 50) |
| `offset` | int | No | Pagination offset |

#### Response 200
```json
{
  "ticker": "TSLA",
  "total": 25,
  "records": [
    {
      "id": "eval_20260114_001",
      "ticker": "TSLA",
      "tf": "1m",
      "created_at": "2026-01-14T18:30:00Z",
      "signal_type": "breakout_confirmed",
      "direction": "up",
      "predicted_behavior": "markup",
      "entry_price": 253.30,
      "target_price": 259.10,
      "invalidation_price": 251.80,
      "confidence": 0.72,
      "notes": "Breakout with volume confirmation",
      "status": "correct",
      "result": "target_hit",
      "actual_outcome": "Price reached 260.50",
      "evaluation_notes": "Clean breakout with follow-through",
      "evaluated_at": "2026-01-14T20:15:00Z"
    }
  ],
  "statistics": {
    "total_predictions": 25,
    "correct": 18,
    "incorrect": 5,
    "pending": 2,
    "accuracy_rate": 0.78,
    "by_signal_type": {
      "breakout_confirmed": { "total": 10, "correct": 8, "accuracy": 0.80 },
      "fakeout": { "total": 8, "correct": 6, "accuracy": 0.75 },
      "breakout_attempt": { "total": 7, "correct": 4, "accuracy": 0.57 }
    }
  }
}
```

---

### 5. PUT `/v1/signal-evaluation/{id}` — Update Signal Evaluation

Update the result of a signal prediction.

#### Request Body
```json
{
  "status": "correct",
  "result": "target_hit",
  "actual_outcome": "Price reached 260.50, target was 259.10",
  "evaluation_notes": "Clean breakout with follow-through, volume sustained"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | Yes | `correct` or `incorrect` |
| `result` | string | Yes | Result type (see below) |
| `actual_outcome` | string | Yes | What actually happened |
| `evaluation_notes` | string | No | Analysis notes |

#### Result Types

| Result | Description |
|--------|-------------|
| `target_hit` | Price reached target |
| `invalidation_hit` | Price hit stop/invalidation |
| `partial_correct` | Moved in predicted direction but didn't reach target |
| `direction_wrong` | Moved opposite to prediction |
| `timeout` | No significant move within evaluation window |

#### Response 200
```json
{
  "id": "eval_20260114_001",
  "status": "correct",
  "result": "target_hit",
  "actual_outcome": "Price reached 260.50",
  "evaluation_notes": "Clean breakout with follow-through",
  "evaluated_at": "2026-01-14T20:15:00Z"
}
```

---

## Schema Definitions (Extended Hours)

### EHContext

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock symbol |
| `timestamp` | string | ISO 8601 timestamp |
| `session_status` | string | `premarket`, `regular_hours`, `afterhours`, `closed` |
| `levels` | EHLevels | Key price levels from extended hours |
| `premarket_regime` | string | `trend_continuation`, `gap_and_go`, `gap_fill_bias`, `range_day_setup` |
| `bias` | string | `bullish`, `bearish`, `neutral` |
| `bias_confidence` | float | Confidence level (0-1) |
| `key_zones` | EHKeyZone[] | Key levels with roles |
| `ah_risk` | AHRisk | Afterhours risk assessment |
| `opening_action` | OpeningAction | Opening strategy guidance |

### EHLevels

| Field | Type | Description |
|-------|------|-------------|
| `yc` | float | Yesterday's Close (磁吸位) |
| `yh` | float | Yesterday's High |
| `yl` | float | Yesterday's Low |
| `pmh` | float | Premarket High |
| `pml` | float | Premarket Low |
| `ahh` | float | Afterhours High (previous day) |
| `ahl` | float | Afterhours Low (previous day) |
| `gap` | float | Gap size (Open - YC) |
| `gap_pct` | float | Gap percentage |

### EHKeyZone

| Field | Type | Description |
|-------|------|-------------|
| `level` | float | Price level |
| `role` | string | `yc`, `pmh`, `pml`, `ahh`, `ahl`, `gap_fill` |
| `importance` | string | `critical`, `high`, `medium` |

### AHRisk

| Field | Type | Description |
|-------|------|-------------|
| `level` | string | `low`, `medium`, `high` |
| `reason` | string | Risk explanation |

### OpeningAction

| Field | Type | Description |
|-------|------|-------------|
| `bias` | string | `bullish`, `bearish`, `neutral` |
| `watch_level` | float | Key level to watch |
| `invalidation` | float | Level that invalidates bias |

### Premarket Regime Classification

| Regime | Description |
|--------|-------------|
| `trend_continuation` | PM confirms prior day direction |
| `gap_and_go` | Large gap with PM extension (momentum play) |
| `gap_fill_bias` | Gap likely to fill toward YC |
| `range_day_setup` | PM range-bound, expect consolidation |

---

## Schema Definitions (Signal Evaluation)

### SignalEvaluation

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique evaluation ID |
| `ticker` | string | Stock symbol |
| `tf` | string | Timeframe |
| `created_at` | string | When prediction was made |
| `signal_type` | string | Type of signal |
| `direction` | string | `up` or `down` |
| `predicted_behavior` | string | Expected behavior |
| `entry_price` | float | Entry price level |
| `target_price` | float | Target price |
| `invalidation_price` | float | Stop level |
| `confidence` | float | Prediction confidence |
| `notes` | string | Initial notes |
| `status` | string | `pending`, `correct`, `incorrect` |
| `result` | string | Result type |
| `actual_outcome` | string | What happened |
| `evaluation_notes` | string | Analysis notes |
| `evaluated_at` | string | When evaluated |

### EvaluationStatistics

| Field | Type | Description |
|-------|------|-------------|
| `total_predictions` | int | Total predictions made |
| `correct` | int | Correct predictions |
| `incorrect` | int | Incorrect predictions |
| `pending` | int | Awaiting evaluation |
| `accuracy_rate` | float | Overall accuracy (0-1) |
| `by_signal_type` | object | Breakdown by signal type |

---

## Notes

1. **Caching**: Bars are cached for ~60s to reduce provider load
2. **Timestamps**: All timestamps are UTC in ISO 8601 format
3. **MVP Limitation**: No authentication; intended for personal/local use
4. **Volume**: Reliable 1-minute volume requires TwelveData or Polygon provider
5. **Click-to-Locate**: `bar_index` fields enable chart highlighting features
6. **Signal Evaluation**: Stored in SQLite database, persists across sessions
7. **Daily Cache**: Evidence/Timeline use localStorage with daily TTL
8. **Future**: WebSocket endpoint for real-time updates planned for V2
