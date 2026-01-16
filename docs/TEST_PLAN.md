# KLineLens MVP - Test Plan

## 1) Unit Tests (Core)

- **Swing Points**: Given fixed bars, output swing count and key point positions should be stable
- **Zones**: Given fixed swing prices, clustering output zones should be stable (top zone price bands don't drift)
- **Regime**: Manually constructed HH/HL sequences should be judged as uptrend; LL/LH as downtrend; mixed as range
- **Breakout State**: Construct attempt→confirmed and attempt→fakeout sequences to verify state machine
- **Behavior**: Construct "pierce support then reclaim + volume surge" bars, shakeout probability should be higher than others

## 2) Integration Tests (API)

- `/bars`: Valid ticker returns bars; invalid ticker returns TICKER_INVALID
- `/analyze`: Returns required fields not empty, zones/support/resistance at least 1 (when data exists)
- `/sim-trade-plan`: Returns valid trade plan with status, direction, entry conditions

## 3) Frontend Smoke Tests

- Dashboard input ticker -> navigates to detail page
- Timeframe switch updates chart
- Settings language toggle applies site-wide
- Auto-refresh runs without errors
- Strategy type toggle switches between Playbook and 0DTE views

## 4) Test Execution

### 4.1 API Tests
```bash
# Start API
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

Manual Test Checkpoints:
```bash
# Health check
curl http://localhost:8000/

# Get bars - normal case
curl "http://localhost:8000/v1/bars?ticker=TSLA&tf=1m"

# Error handling - invalid ticker
curl "http://localhost:8000/v1/bars?ticker=INVALIDXYZ&tf=1m"

# Error handling - invalid timeframe
curl "http://localhost:8000/v1/bars?ticker=TSLA&tf=invalid"
```

Expected Results:
| Test | Expected Status | Expected Response |
|------|-----------------|-------------------|
| Health check | 200 | `{"status": "ok", ...}` |
| Normal fetch | 200 | Contains bars array |
| Invalid ticker | 404 | `{"code": "NO_DATA", ...}` |
| Invalid timeframe | 400 | `{"code": "TIMEFRAME_INVALID", ...}` |

### 4.2 Automated Tests

```bash
# API tests
cd apps/api
pytest tests/ -v

# Core tests
cd packages/core
pytest tests/ -v
```

### 4.3 Test File Naming Convention

- `tests/test_*.py` - Test files
- `test_<module>_<function>.py` - Specific tests
- At least one test case per public function

### 4.4 Milestone Acceptance Criteria

Before milestone acceptance, must satisfy:
- [ ] All manual tests pass
- [ ] All automated tests pass
- [ ] No P0/P1 level bugs
- [ ] Documentation updated
