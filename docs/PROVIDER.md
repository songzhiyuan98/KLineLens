# KLineLens — Data Provider Spec

> Specification for market data provider integration.
> **User Responsibility**: Data provider rate limits and API key costs are user's responsibility.

---

## 1. Overview

KLineLens is a **local tool** — users run it on their own machine and configure their own data sources.

| Aspect | Description |
|--------|-------------|
| Default Provider | Yahoo Finance (yfinance) - free, no API key |
| User Provides | Choice of provider, API keys (if needed) |
| Rate Limits | User's responsibility to stay within limits |
| Data Quality | Depends on chosen provider |

---

## 2. Available Providers

### 2.1 Yahoo Finance (MVP - Default)

**Status**: ✅ Implemented

| Feature | Value |
|---------|-------|
| Cost | Free |
| API Key | Not required |
| Rate Limit | ~2000 requests/day |
| Data Delay | 15-20 minutes |
| Timeframes | 1m, 5m, 1d |
| Coverage | US stocks, ETFs, crypto, forex |

**Configuration**:
```bash
PROVIDER=yahoo
```

**Limitations**:
| Limitation | Impact | Workaround |
|------------|--------|------------|
| 1m data max 7 days | Limited history | Use 5m/1d for longer analysis |
| ~2000 req/day | Rate limit | Cache aggressively (60s TTL) |
| 15-20 min delay | Not real-time | Acceptable for structure analysis |
| No pre/post market 1m | Limited extended hours | Use 1d for extended hours |

**Rate Limit Protection**:
- Frontend enforces 60s minimum refresh interval
- Backend caches responses for 60 seconds
- Do NOT manually refresh faster than 60s

### 2.2 Polygon.io (V1 - Planned)

**Status**: 🔜 Planned for V1

| Feature | Value |
|---------|-------|
| Cost | Paid (free tier available) |
| API Key | Required |
| Rate Limit | Depends on plan |
| Data Delay | Real-time (paid) / 15min (free) |
| Timeframes | 1m, 5m, 1d, custom |

**Configuration**:
```bash
PROVIDER=polygon
POLYGON_API_KEY=your_api_key_here
```

### 2.3 TwelveData (V1 - Planned)

**Status**: 🔜 Planned for V1

| Feature | Value |
|---------|-------|
| Cost | Paid (free tier available) |
| API Key | Required |
| Rate Limit | 8 req/min (free) |
| Data Delay | Real-time (paid) |
| Timeframes | 1m, 5m, 1d, custom |

**Configuration**:
```bash
PROVIDER=twelvedata
TWELVEDATA_API_KEY=your_api_key_here
```

---

## 3. How to Switch Providers

### 3.1 Change Provider

1. Edit `.env` file:
```bash
# Change from yahoo to polygon
PROVIDER=polygon
POLYGON_API_KEY=your_key_here
```

2. Restart services:
```bash
docker compose down
docker compose up
```

### 3.2 Provider-Specific Notes

**Yahoo Finance**:
- No key needed, just set `PROVIDER=yahoo`
- Best for personal use with moderate request frequency

**Polygon.io** (V1):
- Get API key from https://polygon.io
- Free tier: 5 API calls/min, EOD data
- Paid tier: Real-time data, higher limits

**TwelveData** (V1):
- Get API key from https://twelvedata.com
- Free tier: 800 API credits/day
- Good global market coverage

---

## 4. Rate Limit Protection

### 4.1 Built-in Protection

KLineLens implements multiple layers of rate limit protection:

```
User Request
     │
     ▼
┌─────────────────┐
│ Frontend        │ ◄── Debounce: 60s minimum between refreshes
│ (Next.js)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ API Cache       │ ◄── TTL: 60s (configurable via CACHE_TTL)
│ (In-Memory)     │     Same request returns cached data
└────────┬────────┘
         │ Cache miss
         ▼
┌─────────────────┐
│ Provider        │ ◄── Actual API call to Yahoo/Polygon/etc
│ (yfinance)      │
└─────────────────┘
```

### 4.2 Configuration

```bash
# .env file
CACHE_TTL=60           # Cache duration in seconds
REFRESH_SECONDS=60     # Frontend refresh interval
```

### 4.3 Best Practices

| Do | Don't |
|----|-------|
| Wait for auto-refresh (60s) | Manually refresh every second |
| Use 1d timeframe for historical analysis | Request 1m data for months of history |
| Let cache work | Clear cache frequently |
| Monitor for rate limit errors | Ignore 429 errors |

---

## 5. Provider Interface

All providers implement this interface:

```python
class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_bars(
        self,
        ticker: str,
        timeframe: str,  # "1m", "5m", "1d"
        window: Optional[str] = None  # "1d", "5d", "6mo"
    ) -> List[Bar]:
        """Fetch OHLCV bars for a ticker."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass

    def get_default_window(self, timeframe: str) -> str:
        """Default window for each timeframe."""
        defaults = {"1m": "1d", "5m": "5d", "1d": "6mo"}
        return defaults.get(timeframe, "1d")
```

---

## 6. Supported Tickers

### 6.1 Ticker Format

| Market | Format | Examples |
|--------|--------|----------|
| US Stocks | `SYMBOL` | TSLA, AAPL, NVDA |
| US ETFs | `SYMBOL` | SPY, QQQ, IWM |
| Crypto | `SYMBOL-USD` | BTC-USD, ETH-USD |
| Forex | `PAIR=X` | EURUSD=X, GBPUSD=X |

### 6.2 Validation

Tickers are validated before calling the provider:
- Must match expected format
- Provider checks if ticker exists
- Returns 404 NO_DATA if invalid

---

## 7. Error Handling

### 7.1 Error Types

| Error | HTTP Code | Cause | User Action |
|-------|-----------|-------|-------------|
| NO_DATA | 404 | Invalid ticker or no data | Check ticker spelling |
| RATE_LIMITED | 429 | Too many requests | Wait and retry |
| PROVIDER_ERROR | 502 | Provider unavailable | Check provider status |
| TIMEFRAME_INVALID | 400 | Unsupported timeframe | Use 1m/5m/1d |

### 7.2 Error Response Format

```json
{
  "detail": {
    "code": "NO_DATA",
    "message": "No data available for ticker: INVALIDXYZ"
  }
}
```

---

## 8. Adding a New Provider (For Contributors)

### 8.1 Steps

1. Create provider file:
```bash
apps/api/src/providers/polygon_provider.py
```

2. Implement interface:
```python
class PolygonProvider(MarketDataProvider):
    @property
    def name(self) -> str:
        return "polygon"

    def get_bars(self, ticker, timeframe, window=None):
        # Implementation here
        pass
```

3. Register in factory:
```python
# apps/api/src/providers/__init__.py
def get_provider(name: str) -> MarketDataProvider:
    providers = {
        "yahoo": YFinanceProvider,
        "polygon": PolygonProvider,  # Add here
    }
    return providers[name]()
```

4. Update docs:
- Add provider section to this file
- Update `docs/CONFIG.md` with new env vars
- Update `docs/DEPLOYMENT.md` with setup instructions

---

## 9. Troubleshooting

### 9.1 No Data Returned

**Symptoms**: API returns 404 NO_DATA

**Causes**:
1. Invalid ticker format
2. Provider doesn't cover this market
3. Rate limit exceeded (silent fail)
4. Market is closed (1m data)

**Solutions**:
```bash
# Check if ticker works
curl "http://localhost:8000/v1/bars?ticker=AAPL&tf=1d"

# Check provider status
curl http://localhost:8000/

# Wait if rate limited
sleep 60 && curl "http://localhost:8000/v1/bars?ticker=TSLA&tf=1m"
```

### 9.2 Rate Limit Errors

**Symptoms**: API returns 429 RATE_LIMITED

**Solutions**:
1. Increase CACHE_TTL in .env
2. Reduce REFRESH_SECONDS
3. Wait a few minutes before retrying
4. Consider using a paid provider

### 9.3 Provider Connection Issues

**Symptoms**: API returns 502 PROVIDER_ERROR

**Solutions**:
1. Check internet connection
2. Check if provider (Yahoo Finance) is up
3. Restart Docker containers
4. Check logs: `docker compose logs api`
