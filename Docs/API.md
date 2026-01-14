# KLineLens MVP - API Contract（v1）

## Base
- Base URL: `/v1`
- Response: JSON
- Error: JSON `{ "error": { "code": "...", "message": "...", "details": {...} } }`

---

## 1) Get Bars
### GET `/v1/bars`
Query:
- `ticker` (string, required)
- `tf` (enum: `1m|5m|1d`, required)
- `window` (string, optional; default by tf e.g. `1d` for 1m)

Response 200:
```json
{
  "ticker": "TSLA",
  "tf": "1m",
  "bars": [
    {"t":"2026-01-13T18:00:00Z","o":0,"h":0,"l":0,"c":0,"v":0}
  ]
}
Errors:

TICKER_INVALID

NO_DATA

PROVIDER_RATE_LIMITED

PROVIDER_ERROR

2) Analyze
POST /v1/analyze
Body:

json
复制代码
{
  "ticker": "TSLA",
  "tf": "1m",
  "window": "1d"
}
Response 200 (AnalysisReport - abbreviated):

json
{
  "ticker":"TSLA",
  "tf":"1m",
  "generated_at":"...",
  "market_state":{"regime":"range","confidence":0.74},
  "zones":{
    "support":[{"low":245.2,"high":246.1,"score":0.91,"touches":4}],
    "resistance":[{"low":252.6,"high":253.3,"score":0.86,"touches":3}]
  },
  "signals":[
    {"type":"breakout_attempt","direction":"up","level":253.3,"confidence":0.68,"bar_time":"..."}
  ],
  "behavior":{
    "probabilities":{"accumulation":0.21,"shakeout":0.62,"markup":0.06,"distribution":0.09,"markdown":0.02},
    "dominant":"shakeout",
    "evidence":[
      {"behavior":"shakeout","bar_time":"...","volume_ratio":2.1,"wick_ratio":0.67,"note_key":"broke_support_then_reclaimed"}
    ]
  },
  "timeline":[
    {"ts":"...","event_type":"shakeout_prob_up","delta":0.15,"reason_key":"support_sweep_reclaim"}
  ],
  "playbook":[
    {"name_key":"plan_a","if_key":"breakout_confirmed","level":253.3,"target":259.1,"invalidation":251.8,"risk_key":"noise_high_1m"},
    {"name_key":"plan_b","if_key":"breakdown_confirmed","level":246.0,"target":241.8,"invalidation":247.2,"risk_key":"liquidity_risk"}
  ]
}