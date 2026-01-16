# Custom Strategy Development Guide

Build your own trading strategy and plug it into KLineLens.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Strategy Interface](#strategy-interface)
4. [Available Data](#available-data)
5. [State Machine Pattern](#state-machine-pattern)
6. [Frontend Integration](#frontend-integration)
7. [Testing](#testing)
8. [Examples](#examples)
9. [Best Practices](#best-practices)

---

## Overview

KLineLens uses a **pluggable strategy architecture**. You can:

1. Create a Python class implementing the strategy interface
2. Register it in the strategy registry
3. Add a frontend option in settings
4. Your strategy appears in the UI!

```
┌─────────────────────────────────────────────────────┐
│                  Your Strategy                       │
│  ┌─────────────────────────────────────────────┐   │
│  │  analyze(snapshot) → StrategySignal         │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│              KLineLens Engine                        │
│  Market Data → Analysis → Your Strategy → UI        │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### Step 1: Create Your Strategy File

```python
# packages/core/src/strategies/my_breakout_strategy.py

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class ActionType(str, Enum):
    WAIT = "WAIT"
    WATCH = "WATCH"
    ENTER = "ENTER"
    HOLD = "HOLD"
    EXIT = "EXIT"

class DirectionType(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"

@dataclass
class StrategySignal:
    """Output from your strategy"""
    action: ActionType
    direction: DirectionType = DirectionType.NONE
    entry: Optional[float] = None
    target: Optional[float] = None
    stop: Optional[float] = None
    risk: str = "MED"  # LOW, MED, HIGH
    reasons: List[str] = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []

@dataclass
class AnalysisSnapshot:
    """Input data available to your strategy"""
    # Price
    price: float
    open: float
    high: float
    low: float

    # Structure
    regime: str          # "uptrend", "downtrend", "range"
    regime_confidence: float

    # Breakout
    breakout_state: str  # "idle", "attempt", "confirmed", "fakeout"

    # Behavior
    behavior: str        # "accumulation", "distribution", "markup", etc.
    behavior_confidence: float

    # Key Levels
    r1: Optional[float]  # Next resistance
    r2: Optional[float]  # Second resistance
    s1: Optional[float]  # Next support
    s2: Optional[float]  # Second support

    # Extended Hours
    yc: Optional[float]  # Yesterday close
    pmh: Optional[float] # Premarket high
    pml: Optional[float] # Premarket low
    hod: Optional[float] # High of day
    lod: Optional[float] # Low of day

    # Volume
    rvol: float          # Relative volume
    volume_quality: str  # "reliable", "partial", "unavailable"

    # Time
    timestamp: str
    is_premarket: bool
    is_opening: bool     # First 10 minutes
    is_closing: bool     # Last 30 minutes


class MyBreakoutStrategy:
    """
    Example: Simple breakout strategy

    Enter LONG when:
    - Breakout is confirmed
    - RVOL > 1.5
    - Not in opening protection period
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.rvol_threshold = self.config.get('rvol_threshold', 1.5)
        self.opening_protection_minutes = self.config.get('opening_protection', 10)

    def analyze(self, snapshot: AnalysisSnapshot) -> StrategySignal:
        """
        Main entry point - called on every bar update

        Args:
            snapshot: Current market state and analysis

        Returns:
            StrategySignal with action and trade details
        """
        reasons = []

        # Opening protection
        if snapshot.is_opening:
            return StrategySignal(
                action=ActionType.WAIT,
                reasons=["Opening protection period"]
            )

        # Check for confirmed breakout
        if snapshot.breakout_state == "confirmed":
            # Volume confirmation
            if snapshot.rvol >= self.rvol_threshold:
                reasons.append(f"Breakout confirmed with RVOL {snapshot.rvol:.1f}x")

                # Determine direction from regime
                if snapshot.regime == "uptrend":
                    return StrategySignal(
                        action=ActionType.ENTER,
                        direction=DirectionType.LONG,
                        entry=snapshot.price,
                        target=snapshot.r1 if snapshot.r1 else snapshot.price * 1.01,
                        stop=snapshot.s1 if snapshot.s1 else snapshot.price * 0.995,
                        risk="LOW" if snapshot.rvol > 2.0 else "MED",
                        reasons=reasons
                    )
                elif snapshot.regime == "downtrend":
                    return StrategySignal(
                        action=ActionType.ENTER,
                        direction=DirectionType.SHORT,
                        entry=snapshot.price,
                        target=snapshot.s1 if snapshot.s1 else snapshot.price * 0.99,
                        stop=snapshot.r1 if snapshot.r1 else snapshot.price * 1.005,
                        risk="LOW" if snapshot.rvol > 2.0 else "MED",
                        reasons=reasons
                    )
            else:
                reasons.append(f"Breakout but low volume (RVOL {snapshot.rvol:.1f}x)")

        # Check for potential setup
        if snapshot.breakout_state == "attempt":
            return StrategySignal(
                action=ActionType.WATCH,
                direction=DirectionType.LONG if snapshot.regime == "uptrend" else DirectionType.SHORT,
                reasons=["Breakout attempt in progress"]
            )

        # Default: wait
        return StrategySignal(
            action=ActionType.WAIT,
            reasons=reasons if reasons else ["No setup detected"]
        )
```

### Step 2: Register Your Strategy

```python
# packages/core/src/strategies/__init__.py

from .my_breakout_strategy import MyBreakoutStrategy

STRATEGY_REGISTRY = {
    'playbook': PlaybookStrategy,
    '0dte': ZeroDTEStrategy,
    'my_breakout': MyBreakoutStrategy,  # Add your strategy
}

def get_strategy(name: str, config: dict = None):
    """Get strategy instance by name"""
    strategy_class = STRATEGY_REGISTRY.get(name)
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {name}")
    return strategy_class(config)
```

### Step 3: Add API Endpoint (if needed)

```python
# apps/api/src/main.py

@app.get("/v1/strategy/{strategy_name}")
async def get_strategy_signal(
    strategy_name: str,
    ticker: str,
    tf: str = "5m"
):
    """Get signal from specified strategy"""
    from packages.core.src.strategies import get_strategy

    # Get market data and analysis
    bars = await provider.get_bars(ticker, tf)
    analysis = analyze_market(bars)

    # Build snapshot
    snapshot = build_snapshot(ticker, bars, analysis)

    # Get strategy signal
    strategy = get_strategy(strategy_name)
    signal = strategy.analyze(snapshot)

    return {
        "ticker": ticker,
        "strategy": strategy_name,
        "signal": asdict(signal)
    }
```

### Step 4: Add Frontend Option

```typescript
// apps/web/src/pages/settings.tsx

// Add to StrategyType
export type StrategyType = 'playbook' | '0dte' | 'my_breakout';

// Add translation
// apps/web/src/lib/i18n.tsx
'strategy_my_breakout': '我的突破策略',
'strategy_my_breakout_desc': '基于成交量确认的突破入场策略',
```

---

## Strategy Interface

### Input: AnalysisSnapshot

Your strategy receives a snapshot of current market state:

```python
@dataclass
class AnalysisSnapshot:
    # === Price Data ===
    price: float          # Current price
    open: float           # Current bar open
    high: float           # Current bar high
    low: float            # Current bar low

    # === Recent History ===
    recent_closes: List[float]  # Last 10 closes
    recent_highs: List[float]   # Last 10 highs
    recent_lows: List[float]    # Last 10 lows

    # === Structure Analysis ===
    regime: str                  # "uptrend" | "downtrend" | "range"
    regime_confidence: float     # 0.0 - 1.0

    # === Breakout State ===
    breakout_state: str          # "idle" | "attempt" | "confirmed" | "fakeout"
    breakout_direction: str      # "up" | "down" | None
    close_count: int             # Closes above/below level

    # === Behavior ===
    behavior: str                # "accumulation" | "distribution" | "markup" | "markdown" | "shakeout"
    behavior_confidence: float

    # === Key Levels ===
    r1: Optional[float]          # Next resistance
    r2: Optional[float]          # Second resistance
    s1: Optional[float]          # Next support
    s2: Optional[float]          # Second support
    hod: Optional[float]         # High of day
    lod: Optional[float]         # Low of day

    # === Extended Hours Levels ===
    yc: Optional[float]          # Yesterday's close
    yh: Optional[float]          # Yesterday's high
    yl: Optional[float]          # Yesterday's low
    pmh: Optional[float]         # Premarket high
    pml: Optional[float]         # Premarket low
    gap: Optional[float]         # Gap from YC

    # === Volume Metrics ===
    rvol: float                  # Relative volume (vs 20-bar avg)
    effort: float                # Volume effort score
    result: float                # Price result (in ATR)
    volume_quality: str          # "reliable" | "partial" | "unavailable"

    # === Time Context ===
    timestamp: str               # ISO timestamp
    interval: str                # "1m" | "5m" | "1d"
    is_premarket: bool           # Before 9:30 ET
    is_opening: bool             # 9:30-9:40 ET
    is_closing: bool             # After 15:30 ET
    minutes_since_open: int      # Minutes since market open
```

### Output: StrategySignal

Your strategy returns a signal:

```python
@dataclass
class StrategySignal:
    # === Required ===
    action: ActionType       # WAIT | WATCH | ENTER | HOLD | EXIT

    # === Optional Trade Details ===
    direction: DirectionType # LONG | SHORT | NONE
    entry: Optional[float]   # Entry price
    target: Optional[float]  # Target price
    stop: Optional[float]    # Stop loss price
    risk: str               # LOW | MED | HIGH

    # === Metadata ===
    reasons: List[str]      # Why this signal
    confidence: float       # 0.0 - 1.0
    expires_at: Optional[str]  # When signal expires
```

---

## State Machine Pattern

For complex strategies, use a state machine:

```python
class StatefulStrategy:
    def __init__(self):
        self.state = "WAIT"
        self.position = None
        self.entry_price = None
        self.bars_in_position = 0

    def analyze(self, snapshot: AnalysisSnapshot) -> StrategySignal:
        # State transitions
        if self.state == "WAIT":
            return self._handle_wait(snapshot)
        elif self.state == "WATCH":
            return self._handle_watch(snapshot)
        elif self.state == "POSITION":
            return self._handle_position(snapshot)

    def _handle_wait(self, snapshot) -> StrategySignal:
        if self._setup_detected(snapshot):
            self.state = "WATCH"
            return StrategySignal(action=ActionType.WATCH, ...)
        return StrategySignal(action=ActionType.WAIT)

    def _handle_watch(self, snapshot) -> StrategySignal:
        if self._entry_triggered(snapshot):
            self.state = "POSITION"
            self.entry_price = snapshot.price
            return StrategySignal(action=ActionType.ENTER, ...)
        if self._setup_invalidated(snapshot):
            self.state = "WAIT"
        return StrategySignal(action=ActionType.WATCH)

    def _handle_position(self, snapshot) -> StrategySignal:
        self.bars_in_position += 1

        if self._target_hit(snapshot):
            self.state = "WAIT"
            return StrategySignal(action=ActionType.EXIT, reasons=["Target hit"])
        if self._stop_hit(snapshot):
            self.state = "WAIT"
            return StrategySignal(action=ActionType.EXIT, reasons=["Stop hit"])

        return StrategySignal(action=ActionType.HOLD)
```

---

## Frontend Integration

### Display Your Strategy in UI

The strategy signal is displayed in the "Trade Strategy" panel:

```typescript
// apps/web/src/pages/t/[ticker].tsx

// The UI automatically renders based on StrategySignal fields:
// - action → Status badge (color-coded)
// - direction → LONG/SHORT badge
// - entry/target/stop → Price levels
// - reasons → Displayed in reasons column
```

### Add Custom Columns

If your strategy has unique fields:

```typescript
// Create a custom renderer component
const MyStrategyDisplay: React.FC<{ signal: MyStrategySignal }> = ({ signal }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '...' }}>
      {/* Your custom layout */}
    </div>
  );
};
```

---

## Testing

### Unit Tests

```python
# packages/core/tests/test_my_strategy.py

import pytest
from src.strategies.my_breakout_strategy import MyBreakoutStrategy, AnalysisSnapshot

def test_enter_on_confirmed_breakout():
    strategy = MyBreakoutStrategy()

    snapshot = AnalysisSnapshot(
        price=100.0,
        breakout_state="confirmed",
        regime="uptrend",
        rvol=2.0,
        is_opening=False,
        # ... other required fields
    )

    signal = strategy.analyze(snapshot)

    assert signal.action == "ENTER"
    assert signal.direction == "LONG"
    assert signal.entry == 100.0

def test_wait_during_opening():
    strategy = MyBreakoutStrategy()

    snapshot = AnalysisSnapshot(
        price=100.0,
        breakout_state="confirmed",
        is_opening=True,
        # ...
    )

    signal = strategy.analyze(snapshot)

    assert signal.action == "WAIT"
    assert "Opening protection" in signal.reasons[0]
```

### Integration Tests

```python
# Test with real market data
def test_strategy_with_real_data():
    from src.providers import get_provider
    from src.analyzer import analyze_market

    provider = get_provider('yahoo')
    bars = provider.get_bars('QQQ', '5m')
    analysis = analyze_market(bars)

    snapshot = build_snapshot('QQQ', bars, analysis)
    strategy = MyBreakoutStrategy()
    signal = strategy.analyze(snapshot)

    # Verify signal is valid
    assert signal.action in ['WAIT', 'WATCH', 'ENTER', 'HOLD', 'EXIT']
```

---

## Examples

### Example 1: Mean Reversion Strategy

```python
class MeanReversionStrategy:
    """Buy when price drops below lower Bollinger Band"""

    def analyze(self, snapshot: AnalysisSnapshot) -> StrategySignal:
        # Calculate bands (simplified)
        closes = snapshot.recent_closes
        mean = sum(closes) / len(closes)
        std = (sum((c - mean) ** 2 for c in closes) / len(closes)) ** 0.5
        lower_band = mean - 2 * std

        if snapshot.price < lower_band and snapshot.rvol > 1.2:
            return StrategySignal(
                action=ActionType.ENTER,
                direction=DirectionType.LONG,
                entry=snapshot.price,
                target=mean,
                stop=lower_band * 0.99,
                reasons=[f"Price below 2σ band, expecting reversion to {mean:.2f}"]
            )

        return StrategySignal(action=ActionType.WAIT)
```

### Example 2: YC Reclaim Strategy

```python
class YCReclaimStrategy:
    """Trade reclaim of yesterday's close"""

    def analyze(self, snapshot: AnalysisSnapshot) -> StrategySignal:
        if not snapshot.yc:
            return StrategySignal(action=ActionType.WAIT, reasons=["No YC data"])

        price = snapshot.price
        yc = snapshot.yc

        # Price just crossed above YC
        if snapshot.recent_closes[-2] < yc < price:
            return StrategySignal(
                action=ActionType.WATCH,
                direction=DirectionType.LONG,
                reasons=[f"Price reclaiming YC {yc:.2f}"]
            )

        # Confirmed hold above YC
        if all(c > yc for c in snapshot.recent_closes[-3:]):
            return StrategySignal(
                action=ActionType.ENTER,
                direction=DirectionType.LONG,
                entry=price,
                target=snapshot.pmh or yc * 1.005,
                stop=yc * 0.998,
                reasons=["YC reclaim confirmed with 3 closes above"]
            )

        return StrategySignal(action=ActionType.WAIT)
```

### Example 3: VWAP Strategy

```python
class VWAPStrategy:
    """Trade bounces off VWAP"""

    def __init__(self, config=None):
        self.vwap_buffer = 0.001  # 0.1% buffer

    def analyze(self, snapshot: AnalysisSnapshot) -> StrategySignal:
        # You would need to add VWAP to snapshot
        vwap = snapshot.vwap  # Assume this exists

        distance_to_vwap = (snapshot.price - vwap) / vwap

        # Price near VWAP from above in uptrend
        if snapshot.regime == "uptrend" and -0.002 < distance_to_vwap < 0.001:
            return StrategySignal(
                action=ActionType.WATCH,
                direction=DirectionType.LONG,
                reasons=["Price testing VWAP support in uptrend"]
            )

        return StrategySignal(action=ActionType.WAIT)
```

---

## Best Practices

### 1. Keep It Simple
```python
# Good: Clear, single responsibility
if breakout_confirmed and volume_strong:
    return enter_long()

# Bad: Complex nested conditions
if (a and b) or (c and not d) or (e and f and g):
    if h or i:
        ...
```

### 2. Always Return a Signal
```python
def analyze(self, snapshot) -> StrategySignal:
    if condition_a:
        return signal_a
    if condition_b:
        return signal_b

    # Always have a default
    return StrategySignal(action=ActionType.WAIT, reasons=["No setup"])
```

### 3. Include Clear Reasons
```python
# Good
reasons=["Breakout confirmed", f"RVOL {rvol:.1f}x > threshold", "Above PMH"]

# Bad
reasons=["Signal triggered"]
```

### 4. Handle Missing Data
```python
def analyze(self, snapshot) -> StrategySignal:
    # Check required data
    if snapshot.volume_quality == "unavailable":
        return StrategySignal(
            action=ActionType.WAIT,
            reasons=["Volume data unavailable"]
        )

    if not snapshot.r1 or not snapshot.s1:
        return StrategySignal(
            action=ActionType.WAIT,
            reasons=["Key levels not established"]
        )
```

### 5. Use Configuration
```python
class ConfigurableStrategy:
    DEFAULT_CONFIG = {
        'rvol_threshold': 1.5,
        'min_rr': 2.0,
        'max_risk_pct': 0.5,
    }

    def __init__(self, config=None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
```

---

## Need Help?

- 📖 See existing strategies in `packages/core/src/sim_trader/`
- 💬 Open an issue on GitHub
- 📧 Check the [API documentation](API.md) for data structures
