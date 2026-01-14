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
| `window` | string | No | Lookback period (default: `1d` for 1m, `6mo` for 1d) |

#### Response 200
```json
{
  "ticker": "TSLA",
  "tf": "1m",
  "bar_count": 390,
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
| `v` | float | Volume |

---

### 2. POST `/v1/analyze` — Run Analysis

Run full structure + behavior analysis on a ticker.

#### Request Body
```json
{
  "ticker": "TSLA",
  "tf": "1m",
  "window": "1d"
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
  "bar_count": 390,
  "data_gaps": false,

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
        "touches": 4
      }
    ],
    "resistance": [
      {
        "low": 252.60,
        "high": 253.30,
        "score": 0.86,
        "touches": 3
      }
    ]
  },

  "signals": [
    {
      "type": "breakout_attempt",
      "direction": "up",
      "level": 253.30,
      "confidence": 0.68,
      "bar_time": "2026-01-13T17:45:00Z"
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
        "behavior": "shakeout",
        "bar_time": "2026-01-13T16:22:00Z",
        "metrics": {
          "volume_ratio": 2.1,
          "wick_ratio_low": 0.67
        },
        "note": "Broke support then quickly reclaimed"
      }
    ]
  },

  "timeline": [
    {
      "ts": "2026-01-13T16:22:00Z",
      "event_type": "shakeout_prob_up",
      "delta": 0.15,
      "reason": "Support sweep with quick reclaim"
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

### Zone

| Field | Type | Description |
|-------|------|-------------|
| `low` | float | Lower bound of price zone |
| `high` | float | Upper bound of price zone |
| `score` | float | Zone strength score (0-1) |
| `touches` | int | Number of times zone was tested |

### Zones

| Field | Type | Description |
|-------|------|-------------|
| `support` | Zone[] | Support zones (sorted by score desc) |
| `resistance` | Zone[] | Resistance zones (sorted by score desc) |

### Signal

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `breakout_attempt`, `breakout_confirmed`, `fakeout` |
| `direction` | string | `up` or `down` |
| `level` | float | Price level of the signal |
| `confidence` | float | Signal confidence (0-1) |
| `bar_time` | string | When the signal occurred |

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

### Evidence

| Field | Type | Description |
|-------|------|-------------|
| `behavior` | string | Which behavior this evidence supports |
| `bar_time` | string | When the evidence was observed |
| `metrics` | object | Relevant metrics (volume_ratio, wick_ratio, etc.) |
| `note` | string | Human-readable explanation |

### TimelineEvent

| Field | Type | Description |
|-------|------|-------------|
| `ts` | string | Event timestamp |
| `event_type` | string | Event type enum (see below) |
| `delta` | float | Probability change magnitude |
| `reason` | string | Human-readable reason |

#### Event Types
- `shakeout_prob_up`, `shakeout_prob_down`
- `accumulation_prob_up`, `accumulation_prob_down`
- `markup_prob_up`, `markup_prob_down`
- `distribution_prob_up`, `distribution_prob_down`
- `markdown_prob_up`, `markdown_prob_down`
- `regime_change`
- `breakout_confirmed`, `breakdown_confirmed`
- `fakeout_detected`

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

## Example Requests

### Fetch 1-minute bars
```bash
curl "http://localhost:8000/v1/bars?ticker=TSLA&tf=1m&window=1d"
```

### Run analysis
```bash
curl -X POST "http://localhost:8000/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA", "tf": "1m", "window": "1d"}'
```

---

## Notes

1. **Caching**: Bars are cached for ~60s to reduce provider load
2. **Timestamps**: All timestamps are UTC in ISO 8601 format
3. **MVP Limitation**: No authentication; intended for personal/local use
4. **Future**: WebSocket endpoint for real-time updates planned for V1
