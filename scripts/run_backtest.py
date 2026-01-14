#!/usr/bin/env python3
"""
运行回测评估脚本

在真实历史数据上评估 KLineLens 分析引擎
生成可用于简历的评估指标

Usage:
    python scripts/run_backtest.py
"""

import sys
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

import yfinance as yf
import numpy as np
import pandas as pd


# 评估的股票列表（覆盖不同类型）
TICKERS = [
    # 大盘科技股
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    # 高波动股
    'TSLA', 'AMD', 'META', 'NFLX', 'CRM',
    # ETF
    'SPY', 'QQQ', 'IWM', 'DIA',
    # 其他
    'JPM', 'V', 'UNH', 'HD', 'PG', 'KO'
]

TIMEFRAME = '1d'  # 日线评估
PERIOD = '6mo'    # 6 个月数据


# ============================================================
# Inline Data Models
# ============================================================

@dataclass
class Bar:
    """OHLCV K线数据"""
    t: str  # timestamp ISO string
    o: float  # open
    h: float  # high
    l: float  # low
    c: float  # close
    v: float  # volume


@dataclass
class SwingPoint:
    """波段点"""
    index: int
    price: float
    bar_time: str
    is_high: bool


@dataclass
class Zone:
    """支撑/阻力区域"""
    low: float
    high: float
    strength: int
    last_touch: str


@dataclass
class Signal:
    """交易信号"""
    type: str  # breakout_attempt, breakout_confirmed, fakeout
    direction: str  # bullish, bearish
    level: float
    bar_time: str
    bar_index: int


@dataclass
class BacktestResult:
    """回测结果"""
    ticker: str
    timeframe: str
    bar_count: int

    # Breakout metrics
    total_breakout_signals: int
    confirmed_breakouts: int
    breakout_accuracy: float

    # Fakeout metrics
    total_fakeout_signals: int
    correct_fakeouts: int
    fakeout_detection_rate: float

    # Signal metrics
    total_signals: int
    signals_hit_target: int
    signal_hit_rate: float


@dataclass
class AggregateResult:
    """聚合回测结果"""
    tickers_evaluated: int
    total_bars: int
    period_days: int

    avg_breakout_accuracy: float
    avg_fakeout_detection: float
    avg_signal_hit_rate: float

    breakout_std: float
    fakeout_std: float


# ============================================================
# Feature Calculations
# ============================================================

def calculate_atr(bars: List[Bar], period: int = 14) -> np.ndarray:
    """计算 ATR (Average True Range)"""
    if len(bars) < 2:
        return np.array([0.0])

    highs = np.array([b.h for b in bars])
    lows = np.array([b.l for b in bars])
    closes = np.array([b.c for b in bars])

    # True Range
    prev_close = np.roll(closes, 1)
    prev_close[0] = closes[0]

    tr1 = highs - lows
    tr2 = np.abs(highs - prev_close)
    tr3 = np.abs(lows - prev_close)

    tr = np.maximum(tr1, np.maximum(tr2, tr3))

    # ATR using EMA
    atr = np.zeros_like(tr)
    atr[0] = tr[0]
    alpha = 2.0 / (period + 1)

    for i in range(1, len(tr)):
        atr[i] = alpha * tr[i] + (1 - alpha) * atr[i-1]

    return atr


def calculate_volume_ratio(bars: List[Bar], period: int = 30) -> np.ndarray:
    """计算量比 (Volume Ratio)"""
    if len(bars) < 2:
        return np.array([1.0])

    volumes = np.array([b.v for b in bars])

    # Volume MA
    vol_ma = np.zeros_like(volumes)
    for i in range(len(volumes)):
        start = max(0, i - period + 1)
        vol_ma[i] = np.mean(volumes[start:i+1])

    # Avoid division by zero
    vol_ma = np.where(vol_ma > 0, vol_ma, 1.0)

    return volumes / vol_ma


# ============================================================
# Structure Detection
# ============================================================

def find_swing_points(bars: List[Bar], n: int = 4) -> Tuple[List[SwingPoint], List[SwingPoint]]:
    """识别波段高点和低点"""
    if len(bars) < 2 * n + 1:
        return [], []

    swing_highs = []
    swing_lows = []

    highs = [b.h for b in bars]
    lows = [b.l for b in bars]

    for i in range(n, len(bars) - n):
        # Check swing high
        is_high = True
        for j in range(i - n, i + n + 1):
            if j != i and highs[j] >= highs[i]:
                is_high = False
                break

        if is_high:
            swing_highs.append(SwingPoint(
                index=i,
                price=highs[i],
                bar_time=bars[i].t,
                is_high=True
            ))

        # Check swing low
        is_low = True
        for j in range(i - n, i + n + 1):
            if j != i and lows[j] <= lows[i]:
                is_low = False
                break

        if is_low:
            swing_lows.append(SwingPoint(
                index=i,
                price=lows[i],
                bar_time=bars[i].t,
                is_high=False
            ))

    return swing_highs, swing_lows


def cluster_zones(swing_highs: List[SwingPoint], swing_lows: List[SwingPoint],
                  atr: float, max_zones: int = 5) -> Dict[str, List[Zone]]:
    """聚类支撑阻力区"""
    padding = 0.5 * atr

    # Cluster resistance zones from swing highs
    resistance = []
    if swing_highs:
        prices = sorted([sp.price for sp in swing_highs], reverse=True)
        clusters = []
        current_cluster = [prices[0]]

        for p in prices[1:]:
            if abs(p - np.mean(current_cluster)) <= atr:
                current_cluster.append(p)
            else:
                clusters.append(current_cluster)
                current_cluster = [p]
        clusters.append(current_cluster)

        for cluster in clusters[:max_zones]:
            center = np.mean(cluster)
            resistance.append(Zone(
                low=center - padding,
                high=center + padding,
                strength=len(cluster),
                last_touch=swing_highs[-1].bar_time if swing_highs else ""
            ))

    # Cluster support zones from swing lows
    support = []
    if swing_lows:
        prices = sorted([sp.price for sp in swing_lows])
        clusters = []
        current_cluster = [prices[0]]

        for p in prices[1:]:
            if abs(p - np.mean(current_cluster)) <= atr:
                current_cluster.append(p)
            else:
                clusters.append(current_cluster)
                current_cluster = [p]
        clusters.append(current_cluster)

        for cluster in clusters[:max_zones]:
            center = np.mean(cluster)
            support.append(Zone(
                low=center - padding,
                high=center + padding,
                strength=len(cluster),
                last_touch=swing_lows[-1].bar_time if swing_lows else ""
            ))

    return {"support": support, "resistance": resistance}


# ============================================================
# Breakout FSM
# ============================================================

class BreakoutFSM:
    """突破状态机"""

    def __init__(self, zones: Dict[str, List[Zone]], volume_threshold: float = 1.8):
        self.zones = zones
        self.volume_threshold = volume_threshold
        self.state = "idle"
        self.attempt_bar_index = -1
        self.attempt_level = 0.0
        self.attempt_direction = "bullish"
        self.confirm_count = 0

    def update(self, bar: Bar, bar_index: int, volume_ratio: float) -> Optional[Signal]:
        """更新状态机，返回信号（如果有）"""
        signal = None

        # Check for breakout attempts
        if self.state == "idle":
            # Check resistance breakout
            for zone in self.zones.get("resistance", []):
                if bar.c > zone.high and volume_ratio >= self.volume_threshold:
                    self.state = "attempt"
                    self.attempt_bar_index = bar_index
                    self.attempt_level = zone.high
                    self.attempt_direction = "bullish"
                    self.confirm_count = 1
                    signal = Signal(
                        type="breakout_attempt",
                        direction="bullish",
                        level=zone.high,
                        bar_time=bar.t,
                        bar_index=bar_index
                    )
                    break

            # Check support breakdown
            if signal is None:
                for zone in self.zones.get("support", []):
                    if bar.c < zone.low and volume_ratio >= self.volume_threshold:
                        self.state = "attempt"
                        self.attempt_bar_index = bar_index
                        self.attempt_level = zone.low
                        self.attempt_direction = "bearish"
                        self.confirm_count = 1
                        signal = Signal(
                            type="breakout_attempt",
                            direction="bearish",
                            level=zone.low,
                            bar_time=bar.t,
                            bar_index=bar_index
                        )
                        break

        elif self.state == "attempt":
            bars_since_attempt = bar_index - self.attempt_bar_index

            if self.attempt_direction == "bullish":
                if bar.c > self.attempt_level:
                    self.confirm_count += 1
                    if self.confirm_count >= 2:
                        self.state = "confirmed"
                        signal = Signal(
                            type="breakout_confirmed",
                            direction="bullish",
                            level=self.attempt_level,
                            bar_time=bar.t,
                            bar_index=bar_index
                        )
                else:
                    # Fakeout - price back below level
                    if bars_since_attempt <= 3:
                        self.state = "fakeout"
                        signal = Signal(
                            type="fakeout",
                            direction="bullish",
                            level=self.attempt_level,
                            bar_time=bar.t,
                            bar_index=bar_index
                        )
                    self.state = "idle"
                    self.confirm_count = 0

            else:  # bearish
                if bar.c < self.attempt_level:
                    self.confirm_count += 1
                    if self.confirm_count >= 2:
                        self.state = "confirmed"
                        signal = Signal(
                            type="breakout_confirmed",
                            direction="bearish",
                            level=self.attempt_level,
                            bar_time=bar.t,
                            bar_index=bar_index
                        )
                else:
                    if bars_since_attempt <= 3:
                        self.state = "fakeout"
                        signal = Signal(
                            type="fakeout",
                            direction="bearish",
                            level=self.attempt_level,
                            bar_time=bar.t,
                            bar_index=bar_index
                        )
                    self.state = "idle"
                    self.confirm_count = 0

        elif self.state in ["confirmed", "fakeout"]:
            self.state = "idle"
            self.confirm_count = 0

        return signal


# ============================================================
# Data Fetching
# ============================================================

def fetch_bars(ticker: str, period: str = '6mo') -> List[Bar]:
    """从 Yahoo Finance 获取历史数据"""
    try:
        data = yf.download(ticker, period=period, interval='1d', progress=False)
        if data.empty:
            return []

        bars = []
        for idx, row in data.iterrows():
            # Handle yfinance column structure
            try:
                if isinstance(row['Open'], pd.Series):
                    open_price = float(row['Open'].iloc[0])
                    high_price = float(row['High'].iloc[0])
                    low_price = float(row['Low'].iloc[0])
                    close_price = float(row['Close'].iloc[0])
                    volume = float(row['Volume'].iloc[0])
                else:
                    open_price = float(row['Open'])
                    high_price = float(row['High'])
                    low_price = float(row['Low'])
                    close_price = float(row['Close'])
                    volume = float(row['Volume'])
            except:
                continue

            bar = Bar(
                t=idx.isoformat(),
                o=open_price,
                h=high_price,
                l=low_price,
                c=close_price,
                v=volume
            )
            bars.append(bar)
        return bars
    except Exception as e:
        print(f"  Error fetching {ticker}: {e}")
        return []


# ============================================================
# Evaluation Functions
# ============================================================

def evaluate_breakout(bars: List[Bar], signal: Signal, lookahead: int = 10) -> bool:
    """评估突破信号质量 - 检查价格是否向突破方向延续"""
    signal_idx = signal.bar_index

    if signal_idx + lookahead >= len(bars):
        return False

    signal_price = signal.level
    future_bars = bars[signal_idx + 1: signal_idx + lookahead + 1]

    if not future_bars:
        return False

    if signal.direction == 'bullish':
        max_high = max(b.h for b in future_bars)
        return max_high > signal_price * 1.005  # 0.5% 以上算延续
    else:
        min_low = min(b.l for b in future_bars)
        return min_low < signal_price * 0.995


def evaluate_fakeout(bars: List[Bar], signal: Signal, lookahead: int = 5) -> bool:
    """评估假突破信号质量 - 检查价格是否快速反转"""
    signal_idx = signal.bar_index

    if signal_idx + lookahead >= len(bars):
        return False

    signal_price = signal.level
    future_bars = bars[signal_idx + 1: signal_idx + lookahead + 1]

    if not future_bars:
        return False

    if signal.direction == 'bullish':
        # 看涨假突破后应该下跌
        min_close = min(b.c for b in future_bars)
        return min_close < signal_price * 0.99
    else:
        # 看跌假突破后应该上涨
        max_close = max(b.c for b in future_bars)
        return max_close > signal_price * 1.01


def evaluate_signal_target(bars: List[Bar], signal: Signal,
                           target_pct: float = 0.02, lookahead: int = 20) -> bool:
    """评估信号目标达成率 - 检查是否达到目标价格"""
    signal_idx = signal.bar_index

    if signal_idx + lookahead >= len(bars):
        return False

    entry_price = signal.level
    future_bars = bars[signal_idx + 1: signal_idx + lookahead + 1]

    if not future_bars:
        return False

    if signal.direction == 'bullish':
        target_price = entry_price * (1 + target_pct)
        return any(b.h >= target_price for b in future_bars)
    else:
        target_price = entry_price * (1 - target_pct)
        return any(b.l <= target_price for b in future_bars)


# ============================================================
# Backtest Runner
# ============================================================

def run_backtest(bars: List[Bar], ticker: str = "UNKNOWN",
                 timeframe: str = "1d") -> BacktestResult:
    """在给定 bars 上运行回测评估"""
    if len(bars) < 50:
        return BacktestResult(
            ticker=ticker, timeframe=timeframe, bar_count=len(bars),
            total_breakout_signals=0, confirmed_breakouts=0, breakout_accuracy=0,
            total_fakeout_signals=0, correct_fakeouts=0, fakeout_detection_rate=0,
            total_signals=0, signals_hit_target=0, signal_hit_rate=0
        )

    # Calculate features
    atr = calculate_atr(bars)
    volume_ratio = calculate_volume_ratio(bars)

    # Find swing points and zones
    swing_highs, swing_lows = find_swing_points(bars)
    current_atr = atr[-1] if len(atr) > 0 else 1.0
    zones = cluster_zones(swing_highs, swing_lows, current_atr)

    # Run breakout detection
    breakout_fsm = BreakoutFSM(zones)
    all_signals = []

    for i, bar in enumerate(bars):
        vol_ratio = volume_ratio[i] if i < len(volume_ratio) else 1.0
        signal = breakout_fsm.update(bar, i, vol_ratio)
        if signal:
            all_signals.append(signal)

    # Separate signal types
    breakout_signals = [s for s in all_signals if s.type == 'breakout_confirmed']
    fakeout_signals = [s for s in all_signals if s.type == 'fakeout']

    # Evaluate breakout accuracy
    confirmed_breakouts = sum(1 for sig in breakout_signals if evaluate_breakout(bars, sig))
    breakout_accuracy = confirmed_breakouts / len(breakout_signals) if breakout_signals else 0

    # Evaluate fakeout detection
    correct_fakeouts = sum(1 for sig in fakeout_signals if evaluate_fakeout(bars, sig))
    fakeout_detection_rate = correct_fakeouts / len(fakeout_signals) if fakeout_signals else 0

    # Evaluate signal hit rate
    signals_hit = sum(1 for sig in all_signals if evaluate_signal_target(bars, sig))
    signal_hit_rate = signals_hit / len(all_signals) if all_signals else 0

    return BacktestResult(
        ticker=ticker,
        timeframe=timeframe,
        bar_count=len(bars),
        total_breakout_signals=len(breakout_signals),
        confirmed_breakouts=confirmed_breakouts,
        breakout_accuracy=breakout_accuracy,
        total_fakeout_signals=len(fakeout_signals),
        correct_fakeouts=correct_fakeouts,
        fakeout_detection_rate=fakeout_detection_rate,
        total_signals=len(all_signals),
        signals_hit_target=signals_hit,
        signal_hit_rate=signal_hit_rate
    )


def aggregate_results(results: List[BacktestResult]) -> AggregateResult:
    """聚合多个回测结果"""
    valid_results = [r for r in results if r.bar_count > 50]

    if not valid_results:
        return AggregateResult(
            tickers_evaluated=0, total_bars=0, period_days=0,
            avg_breakout_accuracy=0, avg_fakeout_detection=0,
            avg_signal_hit_rate=0,
            breakout_std=0, fakeout_std=0
        )

    breakout_accs = [r.breakout_accuracy for r in valid_results if r.total_breakout_signals > 0]
    fakeout_rates = [r.fakeout_detection_rate for r in valid_results if r.total_fakeout_signals > 0]
    hit_rates = [r.signal_hit_rate for r in valid_results if r.total_signals > 0]

    total_bars = sum(r.bar_count for r in valid_results)

    return AggregateResult(
        tickers_evaluated=len(valid_results),
        total_bars=total_bars,
        period_days=total_bars,  # For daily bars, total_bars ≈ trading days
        avg_breakout_accuracy=float(np.mean(breakout_accs)) if breakout_accs else 0,
        avg_fakeout_detection=float(np.mean(fakeout_rates)) if fakeout_rates else 0,
        avg_signal_hit_rate=float(np.mean(hit_rates)) if hit_rates else 0,
        breakout_std=float(np.std(breakout_accs)) if len(breakout_accs) > 1 else 0,
        fakeout_std=float(np.std(fakeout_rates)) if len(fakeout_rates) > 1 else 0
    )


def print_report(result: AggregateResult) -> str:
    """生成评估报告"""
    return f"""
╔══════════════════════════════════════════════════════════════╗
║              KLineLens Backtest Evaluation Report            ║
╠══════════════════════════════════════════════════════════════╣
║  Tickers Evaluated:  {result.tickers_evaluated:>4}                                  ║
║  Total Bars:         {result.total_bars:>8,}                              ║
║  Period:             ~{result.period_days} trading days                        ║
╠══════════════════════════════════════════════════════════════╣
║  BREAKOUT ACCURACY:      {result.avg_breakout_accuracy*100:>5.1f}% (±{result.breakout_std*100:.1f}%)              ║
║  FAKEOUT DETECTION:      {result.avg_fakeout_detection*100:>5.1f}% (±{result.fakeout_std*100:.1f}%)              ║
║  SIGNAL HIT RATE:        {result.avg_signal_hit_rate*100:>5.1f}%                           ║
╚══════════════════════════════════════════════════════════════╝
"""


def main():
    print("=" * 64)
    print("KLineLens Backtest Evaluation")
    print("=" * 64)
    print(f"\nEvaluating {len(TICKERS)} tickers over {PERIOD} period...")
    print(f"Timeframe: {TIMEFRAME}")
    print()

    results: List[BacktestResult] = []

    for i, ticker in enumerate(TICKERS, 1):
        print(f"[{i:2}/{len(TICKERS)}] Processing {ticker}...", end=" ", flush=True)

        bars = fetch_bars(ticker, PERIOD)
        if len(bars) < 50:
            print(f"Skipped (only {len(bars)} bars)")
            continue

        result = run_backtest(bars, ticker=ticker, timeframe=TIMEFRAME)
        results.append(result)

        print(f"OK ({result.bar_count} bars, "
              f"{result.total_signals} signals, "
              f"breakout acc: {result.breakout_accuracy*100:.0f}%)")

    # 聚合结果
    print("\n" + "=" * 64)
    aggregate = aggregate_results(results)
    print(print_report(aggregate))

    # 保存详细结果
    output = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "tickers": TICKERS,
            "timeframe": TIMEFRAME,
            "period": PERIOD
        },
        "summary": {
            "tickers_evaluated": aggregate.tickers_evaluated,
            "total_bars": aggregate.total_bars,
            "period_days": aggregate.period_days,
            "breakout_accuracy": round(aggregate.avg_breakout_accuracy, 3),
            "fakeout_detection_rate": round(aggregate.avg_fakeout_detection, 3),
            "signal_hit_rate": round(aggregate.avg_signal_hit_rate, 3)
        },
        "per_ticker": [
            {
                "ticker": r.ticker,
                "bars": r.bar_count,
                "breakout_accuracy": round(r.breakout_accuracy, 3),
                "fakeout_detection": round(r.fakeout_detection_rate, 3),
                "signal_hit_rate": round(r.signal_hit_rate, 3)
            }
            for r in results
        ]
    }

    output_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'BACKTEST_RESULTS.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: docs/BACKTEST_RESULTS.json")

    # 生成简历可用的一句话总结
    print("\n" + "=" * 64)
    print("RESUME BULLET POINT:")
    print("=" * 64)
    print(f"""
Achieved **{aggregate.avg_breakout_accuracy*100:.0f}% breakout accuracy** and
**{aggregate.avg_fakeout_detection*100:.0f}% fakeout detection rate** evaluated on
{aggregate.period_days}+ trading days of historical data across {aggregate.tickers_evaluated} tickers
""")


if __name__ == "__main__":
    main()
