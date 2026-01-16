"""
KLineLens 主分析协调器（增强版）

市场结构分析的主入口点。
协调所有子模块生成完整的 AnalysisReport。

增强功能:
- RVOL (Relative Volume) 替代绝对成交量
- VSA (Volume Spread Analysis): Effort vs Result
- 3-Factor 突破确认: Structure + Volume + Result
- Zone Strength 多维评分
- 增强型 Evidence 和 Timeline Soft Events
- Volume Quality 评估

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
from .features import calculate_features, get_volume_quality
from .structure import find_swing_points, cluster_zones, classify_regime, BreakoutFSM, inject_eh_levels_as_zones
from .behavior import infer_behavior
from .timeline import TimelineManager, TimelineState
from .playbook import generate_playbook
from .extended_hours import EHContext, EHLevels


@dataclass
class AnalysisParams:
    """
    分析参数配置（增强版）

    所有参数都有合理的 MVP 默认值。
    """
    # 特征计算
    atr_period: int = 14           # ATR 周期
    volume_period: int = 30        # 成交量均线周期（用于 RVOL）

    # 结构检测
    swing_n: int = 4               # 分形阶数
    regime_m: int = 6              # 趋势判断使用的摆动点数量
    max_zones: int = 5             # 每侧最大区域数

    # 3-Factor 突破状态机
    volume_threshold: float = 1.8  # Factor 2: 确认所需 RVOL
    result_threshold: float = 0.6  # Factor 3: 确认所需 range/ATR
    confirm_closes: int = 2        # Factor 1: 确认所需连续收盘次数
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
            result_threshold=params.result_threshold,
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
                   state: Optional[AnalysisState] = None,
                   eh_context: Optional[EHContext] = None) -> AnalysisReport:
    """
    主市场分析函数（增强版 + EH 集成）

    参数:
        bars: K 线列表（建议至少 50 根）
        ticker: 股票代码
        timeframe: 时间周期字符串（"1m", "5m", "1d"）
        params: 分析参数（默认使用 AnalysisParams()）
        state: 先前分析状态（用于增量更新）
        eh_context: Extended Hours 上下文（可选，用于增强分析）

    返回:
        完整的 AnalysisReport（含 volume_quality）

    异常:
        ValueError: 如果 K 线数量少于最低要求

    增强版实现流程:
        1. 验证输入 K 线
        2. 计算特征（ATR, RVOL, Effort, Result, 影线, 效率）
        3. 评估成交量数据质量
        4. 查找摆动点
        5. 聚类区域（增强版 Zone Strength）
        5b. 注入 EH levels 作为关键区域（如有 eh_context）
        6. 分类趋势
        7. 运行 3-Factor 突破状态机获取信号
        8. 推断行为（含 VSA 吸收检测）
        9. 更新时间线（含 Soft Events）
        10. 生成 Playbook（含 EH context 影响）
        11. 组装并返回 AnalysisReport

    确定性:
        相同的 bars 和 params，输出相同。
        state 影响时间线事件，但不影响其他输出。

    EH 集成:
        当提供 eh_context 时:
        - YC/PMH/PML/AHH/AHL 被添加为关键 zones
        - Premarket regime 影响 playbook 建议
        - Gap 信息用于开盘策略
    """
    # 使用默认参数
    if params is None:
        params = AnalysisParams()

    # 1. 验证输入
    min_required = params.atr_period + 1
    _validate_bars(bars, min_required)

    # 2. 计算特征（包含 RVOL, Effort, Result）
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

    # 3. 评估成交量数据质量
    volume_quality = get_volume_quality(features['rvol'])

    # 4. 查找摆动点
    swing_highs, swing_lows = find_swing_points(bars, n=params.swing_n)

    # 5. 聚类区域（增强版：含 Zone Strength）
    current_bar_index = len(bars) - 1
    zones = cluster_zones(
        swing_highs,
        swing_lows,
        current_atr,
        timeframe=timeframe,
        max_zones=params.max_zones,
        current_bar_index=current_bar_index
    )

    # 5b. 注入 EH levels 作为关键区域
    current_price = features['close'][-1]
    if eh_context is not None:
        zones = inject_eh_levels_as_zones(
            zones,
            eh_context.levels,
            current_price,
            current_atr
        )

    # 6. 分类趋势
    market_state = classify_regime(
        swing_highs,
        swing_lows,
        m=params.regime_m
    )

    # 7. 运行 3-Factor 突破状态机
    if state is None:
        state = create_initial_state(params)

    signals = []
    for i, bar in enumerate(bars):
        rvol = features['rvol'][i]
        if np.isnan(rvol):
            rvol = 1.0

        atr_i = features['atr'][i]
        if np.isnan(atr_i):
            atr_i = bar.h - bar.l

        signal = state.breakout_fsm.update(bar, i, zones, rvol, atr_i)
        if signal:
            signals.append(signal)

    # 8. 推断行为（含 VSA 吸收检测）
    behavior = infer_behavior(
        bars,
        features,
        zones,
        market_state,
        signals
    )

    # 9. 更新时间线（含 Soft Events）
    current_bar = bars[-1]
    breakout_state_str = state.breakout_fsm.get_state_str()

    # 获取当前 RVOL, Effort, Result
    current_rvol = features['rvol'][-1]
    if np.isnan(current_rvol):
        current_rvol = 1.0
    current_effort = features['effort'][-1]
    current_result = features['result'][-1]

    # 转换摆动点为元组格式
    swing_highs_tuples = [(sp.index, sp.price) for sp in swing_highs]
    swing_lows_tuples = [(sp.index, sp.price) for sp in swing_lows]

    timeline_events = state.timeline_manager.update(
        timestamp=current_bar.t,
        market_state=market_state,
        behavior=behavior,
        breakout_state=breakout_state_str,
        signals=signals,
        bar=current_bar,
        bar_idx=current_bar_index,
        zones=zones,
        atr=current_atr,
        rvol=current_rvol,
        effort=current_effort,
        result=current_result,
        swing_highs=swing_highs_tuples,
        swing_lows=swing_lows_tuples
    )

    # 生成历史软事件（扫描最近 N 根 K 线）
    from .timeline import generate_soft_events
    from .models import TimelineEvent

    lookback = min(10, len(bars) - 1)
    historical_events = []

    for i in range(len(bars) - lookback, len(bars)):
        bar = bars[i]
        rvol_i = features['rvol'][i]
        if np.isnan(rvol_i):
            rvol_i = 1.0
        effort_i = features['effort'][i]
        result_i = features['result'][i]

        soft_events = generate_soft_events(
            bar=bar,
            bar_idx=i,
            zones=zones,
            atr=current_atr,
            rvol=rvol_i,
            effort=effort_i,
            result=result_i,
            swing_highs=swing_highs_tuples,
            swing_lows=swing_lows_tuples,
            previous_state=None  # 无状态比较
        )

        for event_data in soft_events[:1]:  # 每根 K 线最多 1 个软事件
            event_type, delta, reason, severity = event_data
            historical_events.append(TimelineEvent(
                ts=bar.t,
                event_type=event_type,
                delta=round(delta, 4) if isinstance(delta, float) else 0.0,
                reason=reason,
                bar_index=i,
                severity=severity
            ))

    # 合并事件（硬事件优先，软事件补充）
    all_timeline_events = state.timeline_manager.get_events(limit=10)

    # 如果事件太少，用历史软事件补充
    if len(all_timeline_events) < 5 and historical_events:
        # 去重：只保留不同类型的事件
        seen_types = set(e.event_type for e in all_timeline_events)
        for he in reversed(historical_events[-5:]):
            if he.event_type not in seen_types and len(all_timeline_events) < 8:
                all_timeline_events.append(he)
                seen_types.add(he.event_type)
        # 按时间排序
        all_timeline_events.sort(key=lambda e: e.ts, reverse=True)

    # 10. 生成 Playbook（含 EH context 影响）
    playbook = generate_playbook(
        market_state,
        zones,
        signals,
        current_atr,
        current_price,
        eh_context=eh_context
    )

    # 11. 检测数据缺口
    data_gaps = _detect_data_gaps(bars, timeframe)

    # 12. 组装报告
    report = AnalysisReport(
        ticker=ticker.upper(),
        tf=timeframe,
        generated_at=datetime.now(timezone.utc),
        bar_count=len(bars),
        data_gaps=data_gaps,
        volume_quality=volume_quality,
        market_state=market_state,
        zones=zones,
        signals=signals,
        behavior=behavior,
        timeline=all_timeline_events,
        playbook=playbook
    )

    return report
