# KLineLens — Data Provider Spec

> Specification for market data provider integration.
> **User Responsibility**: Data provider rate limits and API key costs are user's responsibility.

---

## 1. Overview

KLineLens is a **local tool** — users run it on their own machine and configure their own data sources.

| Aspect | Description |
|--------|-------------|
| Default Provider | TwelveData (recommended) - real-time data + reliable volume |
| User Provides | Choice of provider, API keys (if needed) |
| Rate Limits | User's responsibility to stay within limits |
| Data Quality | Depends on chosen provider |

---

## 2. Provider Comparison

| Provider | Cost | 1m Volume | Latency | Best For |
|----------|------|-----------|---------|----------|
| **TwelveData** | Free (800/day) | ✅ Reliable | ~170ms | **Recommended for intraday** |
| Alpaca | Free | ✅ IEX | Low | Free minute confirmation |
| Yahoo | Free | ⚠️ Unstable | 15-20min | Daily structure only |
| Alpha Vantage | Free (25/day) | ✅ Good | 15-20min | Low-frequency analysis |
| Polygon | Paid | ✅ Strong | Real-time | Professional use |

---

## 3. Available Providers

### 3.1 TwelveData (Recommended)

**Status**: ✅ Implemented

| Feature | Value |
|---------|-------|
| Cost | **Free** (800 API credits/day, 8 req/min) |
| API Key | Required (免费注册) |
| Rate Limit | 800 credits/day, 8 requests/minute |
| Data Delay | **~170ms (near real-time)** |
| Timeframes | 1m, 5m, 15m, 30m, 1h, 1d |
| Coverage | US stocks, ETFs, global markets, crypto, forex |
| Volume Quality | ✅ **可靠的分钟级成交量** |

**Configuration**:
```bash
PROVIDER=twelvedata
TWELVEDATA_API_KEY=your_api_key_here
```

**Get API Key**:
1. 访问 https://twelvedata.com/
2. 注册账户（免费）
3. 在 Dashboard 获取 API Key
4. 复制到 `.env` 文件

**Advantages**:
| Feature | Benefit |
|---------|---------|
| **可靠分钟成交量** | 量价确认可用，分析更准确 |
| **接近实时** | ~170ms 延迟，适合日内交易分析 |
| 800 credits/day | 足够个人使用 |
| 全球市场覆盖 | 不仅限于美股 |

**Limitations**:
| Limitation | Impact | Workaround |
|------------|--------|------------|
| 8 req/min | 限制请求频率 | 利用缓存（60s TTL） |
| 800 credits/day | 有限免费额度 | 付费 $29/mo 或 $45/年 无限制 |

**Why TwelveData is Recommended**:
1. **Volume Reliability**: 分钟级成交量数据稳定可靠，是 VSA（量价分析）的基础
2. **Low Latency**: ~170ms 延迟，比 Yahoo Finance 的 15-20 分钟快得多
3. **3-Factor Confirmation**: 有了可靠成交量，可以启用完整的突破确认（Structure + Volume + Result）
4. **Free Tier Sufficient**: 800 credits/day 对于个人分析足够

### 3.2 Yahoo Finance (Fallback)

**Status**: ✅ Implemented

| Feature | Value |
|---------|-------|
| Cost | Free |
| API Key | Not required |
| Rate Limit | ~2000 requests/day |
| Data Delay | 15-20 minutes |
| Timeframes | 1m, 5m, 1d |
| Coverage | US stocks, ETFs, crypto, forex |
| Volume Quality | ⚠️ **分钟级数据有缺失** |

**Configuration**:
```bash
PROVIDER=yfinance
```

**Limitations**:
| Limitation | Impact | Workaround |
|------------|--------|------------|
| 1m data max 7 days | Limited history | Use 5m/1d for longer analysis |
| ~2000 req/day | Rate limit | Cache aggressively (60s TTL) |
| 15-20 min delay | Not real-time | Acceptable for structure analysis |
| **分钟成交量不稳定** | **量价确认不可靠** | 切换到 TwelveData/Alpaca |

**When to Use Yahoo**:
- 快速测试，不需要 API Key
- 加密货币数据（BTC-USD, ETH-USD）
- 日线级别分析（1d timeframe）
- ⚠️ 不推荐用于依赖量价确认的分钟级分析

### 3.3 Alpaca (Free Alternative)

**Status**: ✅ Implemented

| Feature | Value |
|---------|-------|
| Cost | **完全免费** |
| API Key | Required (免费注册) |
| Rate Limit | 无明显限制 |
| Data Delay | 接近实时 |
| Timeframes | 1m, 5m, 1d |
| Coverage | 美股 |
| Volume Quality | ✅ 分钟级成交量（IEX 口径） |

**Configuration**:
```bash
PROVIDER=alpaca
ALPACA_API_KEY=your_api_key_here
ALPACA_API_SECRET=your_api_secret_here
```

**Get API Key**:
1. 访问 https://alpaca.markets/
2. 注册账户（免费，无需入金）
3. 在 Dashboard 获取 API Key 和 Secret
4. 复制到 `.env` 文件

**Advantages**:
| Feature | Benefit |
|---------|---------|
| **完全免费** | 无请求次数限制 |
| 分钟级成交量 | IEX 交易所数据，约占全市场 2-3% |
| 接近实时 | 比 yfinance 延迟更低 |
| 专业级 API | 被量化交易广泛使用 |

**Limitations**:
| Limitation | Impact | Workaround |
|------------|--------|------------|
| IEX 口径成交量 | 非全市场成交量 | 用于趋势分析足够 |
| 仅美股 | 不支持加密货币 | 使用 yfinance 获取加密 |
| 需要 API Key | 需要注册 | 免费注册，无信用卡要求 |

### 3.4 Alpha Vantage

**Status**: ✅ Implemented

| Feature | Value |
|---------|-------|
| Cost | Free (25 req/day) |
| API Key | Required (免费注册) |
| Rate Limit | 25 requests/day (free tier) |
| Data Delay | 15-20 minutes |
| Timeframes | 1m, 5m, 1d |
| Coverage | US stocks, ETFs, forex |
| Volume Quality | ✅ 高质量分钟级成交量 |

**Configuration**:
```bash
PROVIDER=alphavantage
ALPHAVANTAGE_API_KEY=your_api_key_here
```

**Limitations**:
| Limitation | Impact | Workaround |
|------------|--------|------------|
| 25 req/day (free) | 限制请求次数 | 利用缓存，避免频繁刷新 |

### 3.5 Polygon.io (Planned)

**Status**: 🔜 Planned for V2

| Feature | Value |
|---------|-------|
| Cost | Paid (free tier available) |
| API Key | Required |
| Rate Limit | Depends on plan |
| Data Delay | Real-time (paid) / 15min (free) |
| Timeframes | 1m, 5m, 1d, custom |
| Volume Quality | ✅ 高质量全市场成交量 |

---

## 4. How to Switch Providers

### 4.1 Recommended Setup (TwelveData)

```bash
# .env file
PROVIDER=twelvedata
TWELVEDATA_API_KEY=your_api_key_here
```

### 4.2 Alternative Setups

```bash
# 免费无限制（IEX 成交量口径）
PROVIDER=alpaca
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here

# 快速测试（无需 Key，但分钟成交量不可靠）
PROVIDER=yfinance

# 低频使用（25次/天限制）
PROVIDER=alphavantage
ALPHAVANTAGE_API_KEY=your_key_here
```

### 4.3 Apply Changes

```bash
docker compose down
docker compose up
```

---

## 5. Volume Quality Impact

Volume quality directly affects analysis accuracy:

| Volume Quality | Impact on Analysis |
|----------------|-------------------|
| ✅ Reliable (TwelveData) | Full 3-factor breakout confirmation available |
| ✅ IEX (Alpaca) | Volume confirmation works, may undercount |
| ⚠️ Unstable (Yahoo) | Volume confirmation disabled, reduced confidence |

**Frontend Display**:
- Reliable volume: Normal display
- Unstable/missing: "Volume N/A - confirmation unavailable"

**Algorithm Adjustment**:
- With reliable volume: Full VSA analysis (Effort vs Result)
- Without reliable volume: Structure-only analysis, confidence -30%

---

## 6. Rate Limit Protection

### 6.1 Built-in Protection

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
│ Provider        │ ◄── Actual API call
└─────────────────┘
```

### 6.2 Configuration

```bash
# .env file
CACHE_TTL=60           # Cache duration in seconds
REFRESH_SECONDS=60     # Frontend refresh interval
```

### 6.3 Best Practices

| Do | Don't |
|----|-------|
| Wait for auto-refresh (60s) | Manually refresh every second |
| Use 1d timeframe for historical analysis | Request 1m data for months of history |
| Let cache work | Clear cache frequently |
| Monitor for rate limit errors | Ignore 429 errors |

---

## 7. Provider Interface

All providers implement this interface:

```python
class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_bars(
        self,
        ticker: str,
        timeframe: str,  # "1m", "5m", "1d"
        window: Optional[str] = None  # "1d", "5d", "1y"
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
        defaults = {"1m": "5d", "5m": "1mo", "1d": "1y"}
        return defaults.get(timeframe, "1d")
```

---

## 8. Supported Tickers

### 8.1 Ticker Format

| Market | Format | Examples |
|--------|--------|----------|
| US Stocks | `SYMBOL` | TSLA, AAPL, NVDA |
| US ETFs | `SYMBOL` | SPY, QQQ, IWM |
| Crypto | `SYMBOL-USD` or `SYMBOL/USD` | BTC-USD, ETH-USD |
| Forex | `PAIR=X` or `PAIR` | EURUSD=X, GBPUSD |

### 8.2 Provider Coverage

| Provider | US Stocks | Crypto | Forex | Global |
|----------|-----------|--------|-------|--------|
| TwelveData | ✅ | ✅ | ✅ | ✅ |
| Alpaca | ✅ | ❌ | ❌ | ❌ |
| Yahoo | ✅ | ✅ | ✅ | ⚠️ |
| Alpha Vantage | ✅ | ⚠️ | ✅ | ❌ |

---

## 9. Error Handling

### 9.1 Error Types

| Error | HTTP Code | Cause | User Action |
|-------|-----------|-------|-------------|
| NO_DATA | 404 | Invalid ticker or no data | Check ticker spelling |
| RATE_LIMITED | 429 | Too many requests | Wait and retry |
| PROVIDER_ERROR | 502 | Provider unavailable | Check provider status |
| TIMEFRAME_INVALID | 400 | Unsupported timeframe | Use 1m/5m/1d |

### 9.2 Error Response Format

```json
{
  "detail": {
    "code": "NO_DATA",
    "message": "No data available for ticker: INVALIDXYZ"
  }
}
```

---

## 10. Adding a New Provider (For Contributors)

### 10.1 Steps

1. Create provider file:
```bash
apps/api/src/providers/newprovider_provider.py
```

2. Implement interface:
```python
class NewProvider(MarketDataProvider):
    @property
    def name(self) -> str:
        return "newprovider"

    def get_bars(self, ticker, timeframe, window=None):
        # Implementation here
        pass
```

3. Register in factory:
```python
# apps/api/src/providers/__init__.py
providers = {
    "twelvedata": lambda: TwelveDataProvider(...),
    "newprovider": lambda: NewProvider(...),  # Add here
}
```

4. Update docs:
- Add provider section to this file
- Update `Docs/CONFIG.md` with new env vars
- Update `Docs/DEPLOYMENT.md` with setup instructions

---

## 11. Troubleshooting

### 11.1 No Data Returned

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

### 11.2 Rate Limit Errors

**Symptoms**: API returns 429 RATE_LIMITED

**Solutions**:
1. Increase CACHE_TTL in .env
2. Reduce REFRESH_SECONDS
3. Wait a few minutes before retrying
4. Consider TwelveData paid plan ($45/year for unlimited)

### 11.3 Provider Connection Issues

**Symptoms**: API returns 502 PROVIDER_ERROR

**Solutions**:
1. Check internet connection
2. Check if provider is up
3. Restart Docker containers
4. Check logs: `docker compose logs api`

### 11.4 Volume Shows N/A

**Symptoms**: Volume ratio shows "N/A" in UI

**Causes**:
1. Using Yahoo Finance with 1m timeframe
2. Market is closed
3. Provider volume data incomplete

**Solutions**:
1. Switch to TwelveData or Alpaca for reliable 1m volume
2. Use 1d timeframe for daily volume (more reliable)
