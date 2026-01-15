"""
KLineLens 时间线状态机模块（增强版）

跟踪市场状态变化，在发生重大变化时发出事件。
解决 "LLM 忘记上下文" 问题，通过维护跨更新的状态叙事。

事件类型:
1. Hard Events (重大变化):
   - regime_change: 趋势状态改变（uptrend -> range 等）
   - behavior_change: 主导行为改变
   - *_prob_up/*_prob_down: 行为概率变化 >= 0.12
   - breakout_confirmed/breakdown_confirmed: 突破确认
   - fakeout_detected: 假突破检测

2. Soft Events (市场叙事，增强版):
   - zone_approached: 价格接近关键区域（distance <= 0.5 ATR）
   - zone_tested: 价格测试区域
   - zone_rejected: 价格被区域拒绝
   - zone_accepted: 价格穿越区域
   - spring: Wyckoff Spring（扫止损 + 快速回收）
   - upthrust: Wyckoff Upthrust（假突破 + 快速回落）
   - absorption_clue: VSA 吸收信号（高 Effort + 低 Result）
   - volume_spike: 成交量放大（RVOL >= 2.0）
   - volume_dryup: 成交量萎缩（RVOL <= 0.5）
   - new_swing_high/new_swing_low: 新高/低点形成

增强功能:
   - bar_index: 支持 click-to-locate
   - severity: info, warning, critical
   - RVOL 替代 volume_ratio
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from .models import TimelineEvent, MarketState, Behavior, Signal, Bar, Zone
import numpy as np


@dataclass
class TimelineState:
    """
    市场状态快照，用于变化检测

    属性:
        timestamp: 状态快照时间
        regime: 市场趋势状态
        dominant_behavior: 主导行为类型
        behavior_probabilities: 完整概率分布
        breakout_state: 当前突破状态机状态
        active_signals: 活跃（未解决）的信号列表
        last_swing_high_idx: 最近摆动高点索引
        last_swing_low_idx: 最近摆动低点索引
    """
    timestamp: datetime
    regime: str
    dominant_behavior: str
    behavior_probabilities: Dict[str, float]
    breakout_state: str
    active_signals: List[Signal] = field(default_factory=list)
    last_swing_high_idx: int = -1
    last_swing_low_idx: int = -1


def generate_soft_events(
    bar: Bar,
    bar_idx: int,
    zones: Dict[str, List[Zone]],
    atr: float,
    rvol: float,
    effort: float,
    result: float,
    swing_highs: List[Tuple[int, float]],
    swing_lows: List[Tuple[int, float]],
    previous_state: Optional['TimelineState']
) -> List[Tuple[str, float, str, str]]:
    """
    生成软事件（市场叙事，增强版）

    软事件不代表交易信号，而是解释性的市场状态描述。

    参数:
        bar: 当前 K 线
        bar_idx: K 线索引
        zones: 支撑/阻力区域
        atr: 当前 ATR
        rvol: 相对成交量 (RVOL)
        effort: VSA Effort (= RVOL)
        result: VSA Result (= range/ATR)
        swing_highs: 摆动高点列表 [(idx, price), ...]
        swing_lows: 摆动低点列表 [(idx, price), ...]
        previous_state: 先前状态

    返回:
        (event_type, delta, reason, severity) 元组列表
    """
    events = []
    close = bar.c
    high = bar.h
    low = bar.l
    open_price = bar.o

    # 1. Zone events: approached / tested / rejected / accepted
    approach_threshold = 0.5 * atr  # 接近阈值（增强：0.5 ATR）
    touch_threshold = 0.15 * atr    # 触碰阈值

    for zone in zones.get('resistance', [])[:2]:
        zone_mid = (zone.low + zone.high) / 2
        dist = zone.low - high

        # 价格穿越区域（收盘在区域上方）
        if close > zone.high:
            events.append((
                "zone_accepted",
                zone_mid,
                "event.zone.resistance_accepted",
                "warning"
            ))
            break
        # 价格被区域拒绝（触及后回落）
        elif high >= zone.low and close < zone.low:
            events.append((
                "zone_rejected",
                zone_mid,
                "event.zone.resistance_rejected",
                "info"
            ))
            break
        # 价格测试区域
        elif dist <= touch_threshold and dist >= -touch_threshold:
            events.append((
                "zone_tested",
                zone_mid,
                "event.zone.resistance_tested",
                "info"
            ))
            break
        # 价格接近区域
        elif dist > 0 and dist <= approach_threshold:
            events.append((
                "zone_approached",
                zone_mid,
                "event.zone.resistance_approached",
                "info"
            ))
            break

    for zone in zones.get('support', [])[:2]:
        zone_mid = (zone.low + zone.high) / 2
        dist = low - zone.high

        # 价格穿越区域（收盘在区域下方）
        if close < zone.low:
            events.append((
                "zone_accepted",
                zone_mid,
                "event.zone.support_accepted",
                "warning"
            ))
            break
        # 价格被区域拒绝（触及后反弹）
        elif low <= zone.high and close > zone.high:
            events.append((
                "zone_rejected",
                zone_mid,
                "event.zone.support_rejected",
                "info"
            ))
            break
        # 价格测试区域
        elif dist >= -touch_threshold and dist <= touch_threshold:
            events.append((
                "zone_tested",
                zone_mid,
                "event.zone.support_tested",
                "info"
            ))
            break
        # 价格接近区域
        elif dist < 0 and dist >= -approach_threshold:
            events.append((
                "zone_approached",
                zone_mid,
                "event.zone.support_approached",
                "info"
            ))
            break

    # 2. Spring / Upthrust detection (Wyckoff)
    bar_range = high - low
    if bar_range > 0:
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low

        # Spring: 跌破支撑后快速收回（下影线 > 50% 且收盘在支撑上方）
        for zone in zones.get('support', [])[:2]:
            if low < zone.low and close >= zone.low:
                wick_ratio = lower_wick / bar_range
                if wick_ratio >= 0.4:
                    events.append((
                        "spring",
                        zone.low,
                        "event.wyckoff.spring",
                        "critical"
                    ))
                    break

        # Upthrust: 突破阻力后快速回落（上影线 > 50% 且收盘在阻力下方）
        for zone in zones.get('resistance', [])[:2]:
            if high > zone.high and close <= zone.high:
                wick_ratio = upper_wick / bar_range
                if wick_ratio >= 0.4:
                    events.append((
                        "upthrust",
                        zone.high,
                        "event.wyckoff.upthrust",
                        "critical"
                    ))
                    break

    # 3. VSA Absorption clue (高 Effort + 低 Result)
    if not np.isnan(effort) and not np.isnan(result):
        if effort >= 1.5 and result <= 0.6:
            events.append((
                "absorption_clue",
                effort,
                "event.vsa.absorption",
                "warning"
            ))

    # 4. Volume events (using RVOL)
    if not np.isnan(rvol):
        if rvol >= 2.0:
            events.append((
                "volume_spike",
                rvol,
                "event.volume.spike",
                "warning"
            ))
        elif rvol <= 0.5:
            events.append((
                "volume_dryup",
                rvol,
                "event.volume.dryup",
                "info"
            ))

    # 5. New swing point formed
    if swing_highs and previous_state:
        latest_high_idx = swing_highs[-1][0] if swing_highs else -1
        if latest_high_idx > previous_state.last_swing_high_idx and latest_high_idx >= bar_idx - 5:
            events.append((
                "new_swing_high",
                swing_highs[-1][1],
                "event.swing.new_high",
                "info"
            ))

    if swing_lows and previous_state:
        latest_low_idx = swing_lows[-1][0] if swing_lows else -1
        if latest_low_idx > previous_state.last_swing_low_idx and latest_low_idx >= bar_idx - 5:
            events.append((
                "new_swing_low",
                swing_lows[-1][1],
                "event.swing.new_low",
                "info"
            ))

    return events


class TimelineManager:
    """
    管理时间线事件生成

    比较当前状态与先前状态，在检测到重大变化时发出事件。

    事件发出规则:
        - 趋势状态改变（uptrend -> range 等）
        - 主导行为改变
        - 行为概率变化 >= probability_threshold
        - 突破状态改变（idle -> attempt -> confirmed/fakeout）
    """

    def __init__(self,
                 probability_threshold: float = 0.12,
                 max_events: int = 50):
        """
        初始化时间线管理器

        参数:
            probability_threshold: 发出事件的最小概率变化
            max_events: 保留的最大历史事件数
        """
        self._previous_state: Optional[TimelineState] = None
        self._events: List[TimelineEvent] = []
        self._probability_threshold = probability_threshold
        self._max_events = max_events

    def should_emit_event(self,
                          old_state: Optional[TimelineState],
                          new_state: TimelineState) -> List[Tuple[str, float, str]]:
        """
        判断是否应该发出事件

        参数:
            old_state: 先前状态（首次更新时为 None）
            new_state: 当前状态

        返回:
            (event_type, delta, reason_key) 元组列表

        事件类型:
            - "regime_change": 趋势状态改变
            - "behavior_shift": 主导行为改变
            - "probability_spike": 概率变化 >= 阈值
            - "breakout_attempt": 进入尝试状态
            - "breakout_confirmed": 确认突破
            - "fakeout": 检测到假突破
        """
        events_to_emit = []

        if old_state is None:
            # 首次更新，发出初始化事件
            events_to_emit.append((
                "initialized",
                0.0,
                f"event.initialized.{new_state.regime}_{new_state.dominant_behavior}"
            ))
            return events_to_emit

        # 1. 检查趋势状态改变
        if old_state.regime != new_state.regime:
            events_to_emit.append((
                "regime_change",
                0.0,
                f"event.regime_change.{old_state.regime}_to_{new_state.regime}"
            ))

        # 2. 检查主导行为改变
        if old_state.dominant_behavior != new_state.dominant_behavior:
            events_to_emit.append((
                "behavior_shift",
                0.0,
                f"event.behavior_shift.{old_state.dominant_behavior}_to_{new_state.dominant_behavior}"
            ))

        # 3. 检查概率尖峰
        for behavior, new_prob in new_state.behavior_probabilities.items():
            old_prob = old_state.behavior_probabilities.get(behavior, 0.0)
            delta = new_prob - old_prob

            if abs(delta) >= self._probability_threshold:
                direction = "up" if delta > 0 else "down"
                events_to_emit.append((
                    f"{behavior}_prob_{direction}",
                    delta,
                    f"event.probability.{behavior}_{direction}"
                ))

        # 4. 检查突破状态改变
        if old_state.breakout_state != new_state.breakout_state:
            if new_state.breakout_state == "attempt":
                events_to_emit.append((
                    "breakout_attempt",
                    0.0,
                    "event.breakout.attempt"
                ))
            elif new_state.breakout_state == "confirmed":
                events_to_emit.append((
                    "breakout_confirmed",
                    0.0,
                    "event.breakout.confirmed"
                ))
            elif new_state.breakout_state == "fakeout":
                events_to_emit.append((
                    "fakeout_detected",
                    0.0,
                    "event.breakout.fakeout"
                ))

        return events_to_emit

    def update(self,
               timestamp: datetime,
               market_state: MarketState,
               behavior: Behavior,
               breakout_state: str,
               signals: List[Signal],
               bar: Optional[Bar] = None,
               bar_idx: int = 0,
               zones: Optional[Dict[str, List[Zone]]] = None,
               atr: float = 0.0,
               rvol: float = 1.0,
               effort: float = np.nan,
               result: float = np.nan,
               swing_highs: Optional[List[Tuple[int, float]]] = None,
               swing_lows: Optional[List[Tuple[int, float]]] = None) -> List[TimelineEvent]:
        """
        用新状态更新时间线（增强版）

        参数:
            timestamp: 当前 K 线时间戳
            market_state: 当前市场趋势
            behavior: 当前行为推断
            breakout_state: 当前突破状态机状态字符串
            signals: 当前信号
            bar: 当前 K 线（用于软事件）
            bar_idx: K 线索引
            zones: 区域数据
            atr: 当前 ATR
            rvol: 相对成交量 (RVOL)
            effort: VSA Effort
            result: VSA Result
            swing_highs: 摆动高点列表
            swing_lows: 摆动低点列表

        返回:
            新的 TimelineEvent 对象列表（可能为空）
        """
        # 获取最新摆动点索引
        last_high_idx = swing_highs[-1][0] if swing_highs else -1
        last_low_idx = swing_lows[-1][0] if swing_lows else -1

        # 创建新状态快照
        new_state = TimelineState(
            timestamp=timestamp,
            regime=market_state.regime,
            dominant_behavior=behavior.dominant,
            behavior_probabilities=behavior.probabilities.copy(),
            breakout_state=breakout_state,
            active_signals=signals.copy() if signals else [],
            last_swing_high_idx=last_high_idx,
            last_swing_low_idx=last_low_idx
        )

        # 检查是否应该发出硬事件 (event_type, delta, reason)
        hard_events = self.should_emit_event(self._previous_state, new_state)

        # 生成软事件（如果有足够信息）(event_type, delta, reason, severity)
        soft_events = []
        if bar is not None and zones is not None and atr > 0:
            soft_events = generate_soft_events(
                bar=bar,
                bar_idx=bar_idx,
                zones=zones,
                atr=atr,
                rvol=rvol,
                effort=effort,
                result=result,
                swing_highs=swing_highs or [],
                swing_lows=swing_lows or [],
                previous_state=self._previous_state
            )

        # 创建事件对象
        new_events = []

        # 处理硬事件（严重程度根据事件类型确定）
        for event_type, delta, reason_key in hard_events:
            # 硬事件严重程度映射
            if event_type in ("regime_change", "breakout_confirmed", "breakdown_confirmed"):
                severity = "critical"
            elif event_type in ("behavior_shift", "fakeout_detected"):
                severity = "warning"
            else:
                severity = "info"

            event = TimelineEvent(
                ts=timestamp,
                event_type=event_type,
                delta=round(delta, 4) if isinstance(delta, float) else delta,
                reason=reason_key,
                bar_index=bar_idx,
                severity=severity
            )
            new_events.append(event)
            self._events.append(event)

        # 软事件只在没有硬事件时添加（避免重复）
        if not hard_events:
            for soft_event in soft_events[:2]:  # 最多添加 2 个软事件
                event_type, delta, reason_key, severity = soft_event
                event = TimelineEvent(
                    ts=timestamp,
                    event_type=event_type,
                    delta=round(delta, 4) if isinstance(delta, float) else delta,
                    reason=reason_key,
                    bar_index=bar_idx,
                    severity=severity
                )
                new_events.append(event)
                self._events.append(event)

        # 修剪事件历史
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        # 更新先前状态
        self._previous_state = new_state

        return new_events

    def get_events(self, limit: Optional[int] = None) -> List[TimelineEvent]:
        """
        获取时间线事件

        参数:
            limit: 返回的最大事件数（最新的在前）

        返回:
            TimelineEvent 对象列表
        """
        events = list(reversed(self._events))  # 最新的在前
        if limit:
            events = events[:limit]
        return events

    def get_state(self) -> Optional[TimelineState]:
        """返回当前状态快照"""
        return self._previous_state

    def reset(self) -> None:
        """重置时间线管理器到初始状态"""
        self._previous_state = None
        self._events = []
