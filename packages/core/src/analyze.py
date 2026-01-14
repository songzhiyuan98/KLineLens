"""
KLineLens 主分析协调器

市场结构分析的主入口点。
协调所有子模块生成完整的 AnalysisReport。

使用方法:
    from klinelens_core import analyze_market

    bars = [...]  # List[Bar]
    report = analyze_market(bars, ticker="TSLA", timeframe="1d")
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np

from .models import Bar, AnalysisReport, MarketState, Signal
from .features import calculate_features
from .structure import find_swing_points, cluster_zones, classify_regime, BreakoutFSM
from .behavior import infer_behavior
from .timeline import TimelineManager, TimelineState
from .playbook import generate_playbook


@dataclass
class AnalysisParams:
    """
    分析参数配置

    所有参数都有合理的 MVP 默认值。
    """
    # 特征计算
    atr_period: int = 14           # ATR 周期
    volume_period: int = 30        # 成交量均线周期

    # 结构检测
    swing_n: int = 4               # 分形阶数
    regime_m: int = 6              # 趋势判断使用的摆动点数量
    max_zones: int = 5             # 每侧最大区域数

    # 突破状态机
    volume_threshold: float = 1.8  # 确认所需成交量比率
    confirm_closes: int = 2        # 确认所需连续收盘次数
    fakeout_bars: int = 3          # 假突破判定窗口

    # 行为推断
    behavior_lookback: int = 20    # 行为评分回溯周期

    # 时间线
    probability_threshold: float = 0.12  # 事件发出的最小概率变化


@dataclass
class AnalysisState:
    """
    增量分析的持久状态

    允许跨多次 K 线更新进行连续分析，
    无需从头重新计算。
    """
    breakout_fsm: BreakoutFSM
    timeline_manager: TimelineManager
    timeline_state: Optional[TimelineState] = None


def create_initial_state(params: Optional[AnalysisParams] = None) -> AnalysisState:
    """
    创建初始分析状态

    在开始分析新股票/时间周期时使用。

    参数:
        params: 分析参数（默认使用 AnalysisParams()）

    返回:
        初始化的 AnalysisState
    """
    if params is None:
        params = AnalysisParams()

    return AnalysisState(
        breakout_fsm=BreakoutFSM(
            volume_threshold=params.volume_threshold,
            confirm_closes=params.confirm_closes,
            fakeout_bars=params.fakeout_bars
        ),
        timeline_manager=TimelineManager(
            probability_threshold=params.probability_threshold
        ),
        timeline_state=None
    )


def _validate_bars(bars: List[Bar], min_required: int) -> None:
    """验证 K 线列表满足最低要求"""
    if not bars:
        raise ValueError("K 线列表不能为空")
    if len(bars) < min_required:
        raise ValueError(f"K 线数量不足: 需要至少 {min_required} 根，当前只有 {len(bars)} 根")


def _detect_data_gaps(bars: List[Bar], timeframe: str) -> bool:
    """
    检测 K 线数据是否有缺口

    缺口检测:
        - 1m: 时间差 > 2 分钟
        - 5m: 时间差 > 10 分钟
        - 1d: 时间差 > 3 天（周末正常）

    参数:
        bars: K 线列表
        timeframe: 时间周期

    返回:
        如果检测到缺口返回 True
    """
    if len(bars) < 2:
        return False

    # 设置时间差阈值（秒）
    if timeframe == "1m":
        threshold_seconds = 2 * 60  # 2 分钟
    elif timeframe == "5m":
        threshold_seconds = 10 * 60  # 10 分钟
    else:  # 1d
        threshold_seconds = 3 * 24 * 60 * 60  # 3 天

    for i in range(1, len(bars)):
        delta = (bars[i].t - bars[i - 1].t).total_seconds()
        if delta > threshold_seconds:
            return True

    return False


def analyze_market(bars: List[Bar],
                   ticker: str = "UNKNOWN",
                   timeframe: str = "1d",
                   params: Optional[AnalysisParams] = None,
                   state: Optional[AnalysisState] = None) -> AnalysisReport:
    """
    主市场分析函数

    参数:
        bars: K 线列表（建议至少 50 根）
        ticker: 股票代码
        timeframe: 时间周期字符串（"1m", "5m", "1d"）
        params: 分析参数（默认使用 AnalysisParams()）
        state: 先前分析状态（用于增量更新）

    返回:
        完整的 AnalysisReport

    异常:
        ValueError: 如果 K 线数量少于最低要求

    实现流程:
        1. 验证输入 K 线
        2. 计算特征（ATR, 成交量比率, 影线, 效率）
        3. 查找摆动点
        4. 聚类区域
        5. 分类趋势
        6. 运行突破状态机获取信号
        7. 推断行为
        8. 更新时间线
        9. 生成 Playbook
        10. 组装并返回 AnalysisReport

    确定性:
        相同的 bars 和 params，输出相同。
        state 影响时间线事件，但不影响其他输出。
    """
    # 使用默认参数
    if params is None:
        params = AnalysisParams()

    # 1. 验证输入
    min_required = params.atr_period + 1
    _validate_bars(bars, min_required)

    # 2. 计算特征
    features = calculate_features(
        bars,
        atr_period=params.atr_period,
        volume_period=params.volume_period
    )

    # 获取当前 ATR（用于后续计算）
    current_atr = features['atr'][-1]
    if np.isnan(current_atr):
        # 如果 ATR 为 NaN，使用简单波幅
        current_atr = features['high'][-1] - features['low'][-1]

    # 3. 查找摆动点
    swing_highs, swing_lows = find_swing_points(bars, n=params.swing_n)

    # 4. 聚类区域
    zones = cluster_zones(
        swing_highs,
        swing_lows,
        current_atr,
        timeframe=timeframe,
        max_zones=params.max_zones
    )

    # 5. 分类趋势
    market_state = classify_regime(
        swing_highs,
        swing_lows,
        m=params.regime_m
    )

    # 6. 运行突破状态机
    if state is None:
        state = create_initial_state(params)

    signals = []
    for i, bar in enumerate(bars):
        vol_ratio = features['volume_ratio'][i]
        if np.isnan(vol_ratio):
            vol_ratio = 1.0

        signal = state.breakout_fsm.update(bar, i, zones, vol_ratio)
        if signal:
            signals.append(signal)

    # 7. 推断行为
    behavior = infer_behavior(
        bars,
        features,
        zones,
        market_state,
        signals
    )

    # 8. 更新时间线
    current_bar = bars[-1]
    breakout_state_str = state.breakout_fsm.get_state_str()

    timeline_events = state.timeline_manager.update(
        timestamp=current_bar.t,
        market_state=market_state,
        behavior=behavior,
        breakout_state=breakout_state_str,
        signals=signals
    )

    # 获取完整时间线历史
    all_timeline_events = state.timeline_manager.get_events(limit=10)

    # 9. 生成 Playbook
    current_price = features['close'][-1]
    playbook = generate_playbook(
        market_state,
        zones,
        signals,
        current_atr,
        current_price
    )

    # 10. 检测数据缺口
    data_gaps = _detect_data_gaps(bars, timeframe)

    # 11. 组装报告
    report = AnalysisReport(
        ticker=ticker.upper(),
        tf=timeframe,
        generated_at=datetime.now(timezone.utc),
        bar_count=len(bars),
        data_gaps=data_gaps,
        market_state=market_state,
        zones=zones,
        signals=signals,
        behavior=behavior,
        timeline=all_timeline_events,
        playbook=playbook
    )

    return report
