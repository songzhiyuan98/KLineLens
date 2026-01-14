"""
Type definitions for KLineLens core engine.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class Bar:
    """OHLCV bar data."""
    t: datetime  # UTC timestamp
    o: float     # open
    h: float     # high
    l: float     # low
    c: float     # close
    v: float     # volume


@dataclass
class Zone:
    """Support/Resistance zone."""
    low: float
    high: float
    score: float
    touches: int


@dataclass
class Signal:
    """Breakout/Fakeout signal."""
    type: str       # breakout_attempt, breakout_confirmed, fakeout
    direction: str  # up, down
    level: float
    confidence: float
    bar_time: datetime


@dataclass
class Evidence:
    """Evidence item for behavior inference."""
    behavior: str
    bar_time: datetime
    metrics: Dict[str, float]
    note: str


@dataclass
class TimelineEvent:
    """Timeline event."""
    ts: datetime
    event_type: str
    delta: float
    reason: str


@dataclass
class PlaybookPlan:
    """Conditional trading plan."""
    name: str
    condition: str
    level: float
    target: float
    invalidation: float
    risk: str


@dataclass
class MarketState:
    """Market regime state."""
    regime: str      # uptrend, downtrend, range
    confidence: float


@dataclass
class Behavior:
    """Behavior inference result."""
    probabilities: Dict[str, float]
    dominant: str
    evidence: List[Evidence]


@dataclass
class AnalysisReport:
    """Complete analysis report."""
    ticker: str
    tf: str
    generated_at: datetime
    bar_count: int
    data_gaps: bool
    market_state: MarketState
    zones: Dict[str, List[Zone]]  # support, resistance
    signals: List[Signal]
    behavior: Behavior
    timeline: List[TimelineEvent]
    playbook: List[PlaybookPlan]
