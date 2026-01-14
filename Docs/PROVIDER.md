# KLineLens — Data Provider Spec

> Specification for market data provider integration.

---

## 1. Overview

KLineLens needs OHLCV (Open, High, Low, Close, Volume) bar data from market data providers. MVP uses a single provider with an abstraction layer for future extensibility.

---

## 2. Provider Interface

All providers must implement this interface:

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_bars(
        self,
        ticker: str,
        timeframe: str,  # "1m", "5m", "1d"
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        window: Optional[str] = None  # "1d", "5d", "1mo", "6mo"
    ) -> List[Bar]:
        """
        Fetch OHLCV bars for a ticker.

        Returns:
            List of Bar objects sorted by timestamp ascending.

        Raises:
            TickerNotFoundError: Ticker doesn't exist
            RateLimitError: Provider rate limit exceeded
            ProviderError: Other provider errors
        """
        pass

    @abstractmethod
    def validate_ticker(self, ticker: str) -> bool:
        """Check if ticker is valid and has data."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass

    @property
    @abstractmethod
    def rate_limit(self) -> dict:
        """Rate limit info: {"requests_per_minute": int, "requests_per_day": int}"""
        pass
```

### Bar Structure

```python
@dataclass
class Bar:
    t: datetime  # UTC timestamp
    o: float     # open
    h: float     # high
    l: float     # low
    c: float     # close
    v: float     # volume
```

---

## 3. MVP Provider: yfinance

### 3.1 Why yfinance?
- Free, no API key required
- Supports US stocks, ETFs, crypto
- Good enough for MVP personal use
- Well-maintained Python library

### 3.2 Implementation

```python
import yfinance as yf
from datetime import datetime, timedelta

class YFinanceProvider(MarketDataProvider):

    @property
    def name(self) -> str:
        return "yfinance"

    @property
    def rate_limit(self) -> dict:
        return {
            "requests_per_minute": 60,
            "requests_per_day": 2000
        }

    def get_bars(self, ticker: str, timeframe: str, **kwargs) -> List[Bar]:
        # Map timeframe to yfinance interval
        interval_map = {"1m": "1m", "5m": "5m", "1d": "1d"}
        interval = interval_map.get(timeframe)
        if not interval:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Determine period based on timeframe
        period = self._get_period(timeframe, kwargs.get("window"))

        # Fetch data
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval)

        if df.empty:
            raise TickerNotFoundError(f"No data for {ticker}")

        # Convert to Bar objects
        bars = []
        for idx, row in df.iterrows():
            bars.append(Bar(
                t=idx.to_pydatetime().replace(tzinfo=None),
                o=row["Open"],
                h=row["High"],
                l=row["Low"],
                c=row["Close"],
                v=row["Volume"]
            ))

        return bars

    def _get_period(self, timeframe: str, window: Optional[str]) -> str:
        if window:
            return window
        # Default periods
        defaults = {"1m": "1d", "5m": "5d", "1d": "6mo"}
        return defaults.get(timeframe, "1d")

    def validate_ticker(self, ticker: str) -> bool:
        try:
            info = yf.Ticker(ticker).info
            return info.get("regularMarketPrice") is not None
        except:
            return False
```

### 3.3 Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| 1m data max 7 days | Limited history | Use larger timeframes for longer analysis |
| ~2000 req/day | Rate limit | Cache aggressively |
| No real-time | 15-20 min delay | Acceptable for MVP |
| US market hours | No pre/post market 1m | Use 1d for extended hours |

### 3.4 Error Handling

```python
class ProviderError(Exception):
    """Base provider error."""
    pass

class TickerNotFoundError(ProviderError):
    """Ticker doesn't exist or has no data."""
    pass

class RateLimitError(ProviderError):
    """Provider rate limit exceeded."""
    pass
```

---

## 4. Supported Tickers

### 4.1 Ticker Format

| Market | Format | Examples |
|--------|--------|----------|
| US Stocks | `SYMBOL` | TSLA, AAPL, NVDA |
| US ETFs | `SYMBOL` | SPY, QQQ, IWM |
| Crypto | `SYMBOL-USD` | BTC-USD, ETH-USD |
| Forex | `PAIR=X` | EURUSD=X, GBPUSD=X |

### 4.2 Ticker Validation

```python
import re

def validate_ticker_format(ticker: str) -> bool:
    """
    Validate ticker format before calling provider.

    Valid patterns:
    - US Stock/ETF: 1-5 uppercase letters (TSLA, AAPL)
    - Crypto: SYMBOL-USD (BTC-USD)
    - Forex: PAIR=X (EURUSD=X)
    """
    patterns = [
        r"^[A-Z]{1,5}$",           # US stock
        r"^[A-Z]{2,5}-USD$",       # Crypto
        r"^[A-Z]{6}=X$",           # Forex
    ]
    return any(re.match(p, ticker.upper()) for p in patterns)
```

---

## 5. Future Providers

### 5.1 Planned Providers

| Provider | Use Case | Notes |
|----------|----------|-------|
| Alpha Vantage | Free API key, more history | Rate limited (5 req/min free) |
| Polygon.io | Real-time data | Paid, requires API key |
| Binance | Crypto only | Free, fast |
| Interactive Brokers | Professional data | Requires account |

### 5.2 Provider Factory

```python
def get_provider(name: str = None) -> MarketDataProvider:
    """
    Factory function to get provider instance.

    Args:
        name: Provider name. If None, use default from config.
    """
    name = name or config.PROVIDER

    providers = {
        "yfinance": YFinanceProvider,
        # "alphavantage": AlphaVantageProvider,
        # "polygon": PolygonProvider,
    }

    if name not in providers:
        raise ValueError(f"Unknown provider: {name}")

    return providers[name]()
```

---

## 6. Caching Strategy

### 6.1 Cache Key

```python
def cache_key(ticker: str, tf: str, window: str) -> str:
    return f"bars:{ticker.upper()}:{tf}:{window}"
```

### 6.2 TTL by Timeframe

| Timeframe | TTL | Rationale |
|-----------|-----|-----------|
| 1m | 30s | Fresh data needed |
| 5m | 60s | Moderate freshness |
| 1d | 300s | Daily data less volatile |

### 6.3 Cache Miss Handling

```python
async def get_bars_with_cache(ticker, tf, window):
    key = cache_key(ticker, tf, window)

    # Try cache first
    cached = cache.get(key)
    if cached:
        return cached

    # Fetch from provider
    try:
        bars = provider.get_bars(ticker, tf, window=window)
        cache.set(key, bars, ttl=get_ttl(tf))
        return bars
    except RateLimitError:
        # Return stale cache if available
        stale = cache.get(key, ignore_ttl=True)
        if stale:
            return stale
        raise
```

---

## 7. Testing

### 7.1 Unit Tests

```python
def test_yfinance_get_bars():
    provider = YFinanceProvider()
    bars = provider.get_bars("AAPL", "1d", window="5d")
    assert len(bars) >= 3
    assert all(b.v > 0 for b in bars)

def test_invalid_ticker():
    provider = YFinanceProvider()
    with pytest.raises(TickerNotFoundError):
        provider.get_bars("INVALID123XYZ", "1d")
```

### 7.2 Integration Tests

```python
def test_cache_hit():
    # First call - cache miss
    bars1 = get_bars_with_cache("TSLA", "1m", "1d")

    # Second call - should hit cache
    bars2 = get_bars_with_cache("TSLA", "1m", "1d")

    assert bars1 == bars2  # Same data from cache
```
