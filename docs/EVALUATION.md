# KLineLens Evaluation Report

> Backtest evaluation of the KLineLens analysis engine on real historical market data.

---

## Summary

| Metric | Result |
|--------|--------|
| **Breakout Accuracy** | 98.9% (±4.6%) |
| **Fakeout Detection Rate** | 88.9% (±31.4%) |
| **Signal Hit Rate** | 73.8% |
| **Tickers Evaluated** | 19 |
| **Total Trading Days** | 2,432 |
| **Data Period** | 6 months |
| **Timeframe** | Daily (1d) |

---

## Methodology

### Data Source
- Yahoo Finance historical OHLCV data
- Period: 6 months of daily bars
- Tickers: Mix of large-cap tech, high-volatility stocks, and major ETFs

### Evaluation Metrics

**1. Breakout Accuracy**
- Definition: Percentage of confirmed breakout signals where price continued in the breakout direction
- Criteria: Price must move at least 0.5% in the breakout direction within 10 bars
- Formula: `confirmed_breakouts / total_breakout_signals`

**2. Fakeout Detection Rate**
- Definition: Percentage of fakeout signals where price reversed back into the range
- Criteria: Price must reverse at least 1% within 5 bars after the fakeout signal
- Formula: `correct_fakeouts / total_fakeout_signals`

**3. Signal Hit Rate**
- Definition: Percentage of all signals that reached their 2% profit target
- Criteria: Price must reach 2% target within 20 bars
- Formula: `signals_hit_target / total_signals`

---

## Per-Ticker Results

| Ticker | Bars | Breakout Accuracy | Fakeout Detection | Signal Hit Rate |
|--------|------|-------------------|-------------------|-----------------|
| MSFT | 128 | 100.0% | 100.0% | 50.0% |
| GOOGL | 128 | 100.0% | - | 100.0% |
| AMZN | 128 | 100.0% | 100.0% | 33.3% |
| NVDA | 128 | - | - | - |
| TSLA | 128 | 100.0% | - | 100.0% |
| AMD | 128 | 100.0% | - | 88.9% |
| META | 128 | 100.0% | 100.0% | 64.3% |
| NFLX | 128 | 100.0% | 100.0% | 60.0% |
| CRM | 128 | 100.0% | 100.0% | 78.6% |
| SPY | 128 | 100.0% | - | 66.7% |
| QQQ | 128 | 100.0% | - | 100.0% |
| IWM | 128 | 100.0% | - | 100.0% |
| DIA | 128 | 100.0% | - | 100.0% |
| JPM | 128 | 100.0% | 100.0% | 55.6% |
| V | 128 | 100.0% | - | 60.0% |
| UNH | 128 | 100.0% | 100.0% | 80.0% |
| HD | 128 | 100.0% | - | 75.0% |
| PG | 128 | 100.0% | 100.0% | 66.7% |
| KO | 128 | 80.0% | - | 50.0% |

*Note: "-" indicates no signals of that type were generated for the ticker*

---

## Ticker Categories

### Large-Cap Tech
- MSFT, GOOGL, AMZN, NVDA, META

### High-Volatility
- TSLA, AMD, NFLX, CRM

### Major ETFs
- SPY (S&P 500)
- QQQ (Nasdaq 100)
- IWM (Russell 2000)
- DIA (Dow Jones)

### Other Blue Chips
- JPM, V, UNH, HD, PG, KO

---

## Algorithm Details

### Breakout Detection (FSM)
1. **Idle State**: Monitor for price close above resistance or below support
2. **Attempt State**: Triggered when close breaks zone with volume ratio ≥ 1.8x
3. **Confirmed State**: 2 consecutive closes outside the zone
4. **Fakeout State**: Price returns inside zone within 3 bars

### Zone Clustering
- Swing points identified using fractal algorithm (n=4)
- Zones clustered using ATR-based binning (0.5×ATR bin width)
- Maximum 5 zones per direction (support/resistance)

### Feature Calculations
- ATR: 14-period Exponential Moving Average of True Range
- Volume Ratio: Current volume / 30-period Volume MA

---

## Run Your Own Evaluation

```bash
# Clone the repository
git clone https://github.com/songzhiyuan98/KLineLens.git
cd KLineLens

# Install dependencies
pip install yfinance numpy pandas

# Run backtest
python scripts/run_backtest.py
```

### Customize Tickers

Edit `scripts/run_backtest.py` to modify:

```python
TICKERS = [
    'AAPL', 'MSFT', 'GOOGL',  # Add your tickers
]
PERIOD = '6mo'   # Data period: 1mo, 3mo, 6mo, 1y, 2y
TIMEFRAME = '1d' # Timeframe: 1d
```

---

## Limitations

1. **Lookahead Bias**: Evaluation uses future bars to verify signal accuracy (acceptable for backtesting)
2. **Survivorship Bias**: Only currently trading tickers are evaluated
3. **Market Conditions**: Results may vary in different market regimes
4. **Daily Timeframe Only**: Current evaluation is limited to daily bars

---

## Generated

- **Date**: 2024-01-14
- **Script**: `scripts/run_backtest.py`
- **Raw Data**: [BACKTEST_RESULTS.json](BACKTEST_RESULTS.json)
