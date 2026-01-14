"""
轻量级回测评估模块

在真实历史数据上评估分析引擎的信号质量：
- Breakout Accuracy: 突破信号后价格是否延续
- Fakeout Detection Rate: 假突破识别准确率
- Signal Hit Rate: 信号触发后目标达成率
- Timeline Precision: 事件触发质量
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

try:
    from .models import Bar, Signal, AnalysisReport
    from .analyze import analyze_market, AnalysisParams
except ImportError:
    from models import Bar, Signal, AnalysisReport
    from analyze import analyze_market, AnalysisParams


@dataclass
class BacktestResult:
    """回测结果"""
    ticker: str
    timeframe: str
    bar_count: int

    # Breakout metrics
    total_breakout_signals: int
    confirmed_breakouts: int
    breakout_accuracy: float  # 突破后价格延续的比例

    # Fakeout metrics
    total_fakeout_signals: int
    correct_fakeouts: int
    fakeout_detection_rate: float  # 正确识别假突破的比例

    # Signal metrics
    total_signals: int
    signals_hit_target: int
    signal_hit_rate: float  # 信号触发后达到目标的比例

    # Timeline metrics
    total_events: int
    meaningful_events: int
    timeline_precision: float  # 有意义事件的比例


@dataclass
class AggregateResult:
    """聚合回测结果"""
    tickers_evaluated: int
    total_bars: int
    period_days: int

    avg_breakout_accuracy: float
    avg_fakeout_detection: float
    avg_signal_hit_rate: float
    avg_timeline_precision: float

    # 置信区间
    breakout_std: float
    fakeout_std: float


def evaluate_breakout(bars: List[Bar], signal: Signal, lookahead: int = 10) -> bool:
    """
    评估突破信号质量

    判断：突破信号后 lookahead 根 K 线内，价格是否向突破方向延续
    """
    # 找到信号对应的 bar index
    signal_time = datetime.fromisoformat(signal.bar_time.replace('Z', '+00:00'))
    signal_idx = None

    for i, bar in enumerate(bars):
        bar_time = datetime.fromisoformat(bar.t.replace('Z', '+00:00'))
        if abs((bar_time - signal_time).total_seconds()) < 60:
            signal_idx = i
            break

    if signal_idx is None or signal_idx + lookahead >= len(bars):
        return False

    signal_price = signal.level
    future_bars = bars[signal_idx + 1: signal_idx + lookahead + 1]

    if signal.direction == 'bullish':
        # 看涨突破：后续最高价应该高于信号价格
        max_high = max(b.h for b in future_bars)
        return max_high > signal_price * 1.005  # 0.5% 以上算延续
    else:
        # 看跌突破：后续最低价应该低于信号价格
        min_low = min(b.l for b in future_bars)
        return min_low < signal_price * 0.995


def evaluate_fakeout(bars: List[Bar], signal: Signal, lookahead: int = 5) -> bool:
    """
    评估假突破信号质量

    判断：假突破信号后，价格是否快速反转回区间内
    """
    signal_time = datetime.fromisoformat(signal.bar_time.replace('Z', '+00:00'))
    signal_idx = None

    for i, bar in enumerate(bars):
        bar_time = datetime.fromisoformat(bar.t.replace('Z', '+00:00'))
        if abs((bar_time - signal_time).total_seconds()) < 60:
            signal_idx = i
            break

    if signal_idx is None or signal_idx + lookahead >= len(bars):
        return False

    signal_price = signal.level
    future_bars = bars[signal_idx + 1: signal_idx + lookahead + 1]

    # 假突破应该反转：价格回到信号价格的另一侧
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
    """
    评估信号目标达成率

    判断：信号后 lookahead 根 K 线内，是否达到 target_pct 的盈利目标
    """
    signal_time = datetime.fromisoformat(signal.bar_time.replace('Z', '+00:00'))
    signal_idx = None

    for i, bar in enumerate(bars):
        bar_time = datetime.fromisoformat(bar.t.replace('Z', '+00:00'))
        if abs((bar_time - signal_time).total_seconds()) < 60:
            signal_idx = i
            break

    if signal_idx is None or signal_idx + lookahead >= len(bars):
        return False

    entry_price = signal.level
    future_bars = bars[signal_idx + 1: signal_idx + lookahead + 1]

    if signal.direction == 'bullish':
        target_price = entry_price * (1 + target_pct)
        return any(b.h >= target_price for b in future_bars)
    else:
        target_price = entry_price * (1 - target_pct)
        return any(b.l <= target_price for b in future_bars)


def run_backtest(bars: List[Bar], ticker: str = "UNKNOWN",
                 timeframe: str = "1d") -> BacktestResult:
    """
    在给定 bars 上运行回测评估
    """
    if len(bars) < 50:
        return BacktestResult(
            ticker=ticker, timeframe=timeframe, bar_count=len(bars),
            total_breakout_signals=0, confirmed_breakouts=0, breakout_accuracy=0,
            total_fakeout_signals=0, correct_fakeouts=0, fakeout_detection_rate=0,
            total_signals=0, signals_hit_target=0, signal_hit_rate=0,
            total_events=0, meaningful_events=0, timeline_precision=0
        )

    # 滑动窗口分析
    window_size = 100
    step = 20

    all_breakout_signals = []
    all_fakeout_signals = []
    all_signals = []
    all_events = []

    for start in range(0, len(bars) - window_size, step):
        window_bars = bars[start:start + window_size]

        try:
            report = analyze_market(window_bars, ticker=ticker, timeframe=timeframe)

            for signal in report.signals:
                if signal.type == 'breakout_confirmed':
                    all_breakout_signals.append((window_bars, signal))
                elif signal.type == 'fakeout':
                    all_fakeout_signals.append((window_bars, signal))
                all_signals.append((window_bars, signal))

            for event in report.timeline:
                all_events.append(event)

        except Exception:
            continue

    # 评估 breakout accuracy
    confirmed_breakouts = sum(
        1 for bars, sig in all_breakout_signals
        if evaluate_breakout(bars, sig)
    )
    breakout_accuracy = (
        confirmed_breakouts / len(all_breakout_signals)
        if all_breakout_signals else 0
    )

    # 评估 fakeout detection
    correct_fakeouts = sum(
        1 for bars, sig in all_fakeout_signals
        if evaluate_fakeout(bars, sig)
    )
    fakeout_detection_rate = (
        correct_fakeouts / len(all_fakeout_signals)
        if all_fakeout_signals else 0
    )

    # 评估 signal hit rate
    signals_hit = sum(
        1 for bars, sig in all_signals
        if evaluate_signal_target(bars, sig)
    )
    signal_hit_rate = signals_hit / len(all_signals) if all_signals else 0

    # 评估 timeline precision
    meaningful_events = sum(
        1 for e in all_events
        if e.event_type in ['breakout_confirmed', 'fakeout_detected', 'regime_change']
    )
    timeline_precision = meaningful_events / len(all_events) if all_events else 0

    return BacktestResult(
        ticker=ticker,
        timeframe=timeframe,
        bar_count=len(bars),
        total_breakout_signals=len(all_breakout_signals),
        confirmed_breakouts=confirmed_breakouts,
        breakout_accuracy=breakout_accuracy,
        total_fakeout_signals=len(all_fakeout_signals),
        correct_fakeouts=correct_fakeouts,
        fakeout_detection_rate=fakeout_detection_rate,
        total_signals=len(all_signals),
        signals_hit_target=signals_hit,
        signal_hit_rate=signal_hit_rate,
        total_events=len(all_events),
        meaningful_events=meaningful_events,
        timeline_precision=timeline_precision
    )


def aggregate_results(results: List[BacktestResult]) -> AggregateResult:
    """聚合多个回测结果"""
    valid_results = [r for r in results if r.bar_count > 50]

    if not valid_results:
        return AggregateResult(
            tickers_evaluated=0, total_bars=0, period_days=0,
            avg_breakout_accuracy=0, avg_fakeout_detection=0,
            avg_signal_hit_rate=0, avg_timeline_precision=0,
            breakout_std=0, fakeout_std=0
        )

    breakout_accs = [r.breakout_accuracy for r in valid_results if r.total_breakout_signals > 0]
    fakeout_rates = [r.fakeout_detection_rate for r in valid_results if r.total_fakeout_signals > 0]
    hit_rates = [r.signal_hit_rate for r in valid_results if r.total_signals > 0]
    precisions = [r.timeline_precision for r in valid_results if r.total_events > 0]

    total_bars = sum(r.bar_count for r in valid_results)

    return AggregateResult(
        tickers_evaluated=len(valid_results),
        total_bars=total_bars,
        period_days=total_bars // 390 if total_bars > 0 else 0,  # ~390 1min bars per day
        avg_breakout_accuracy=np.mean(breakout_accs) if breakout_accs else 0,
        avg_fakeout_detection=np.mean(fakeout_rates) if fakeout_rates else 0,
        avg_signal_hit_rate=np.mean(hit_rates) if hit_rates else 0,
        avg_timeline_precision=np.mean(precisions) if precisions else 0,
        breakout_std=np.std(breakout_accs) if len(breakout_accs) > 1 else 0,
        fakeout_std=np.std(fakeout_rates) if len(fakeout_rates) > 1 else 0
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
║  TIMELINE PRECISION:     {result.avg_timeline_precision*100:>5.1f}%                           ║
╚══════════════════════════════════════════════════════════════╝
"""
