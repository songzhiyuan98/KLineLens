"""
KLineLens 时间线状态机模块

跟踪市场状态变化，在发生重大变化时发出事件。
解决 "LLM 忘记上下文" 问题，通过维护跨更新的状态叙事。

事件发出规则:
- 趋势状态改变（uptrend -> range 等）
- 主导行为改变
- 行为概率变化 >= 0.12
- 突破状态改变（idle -> attempt -> confirmed/fakeout）
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from .models import TimelineEvent, MarketState, Behavior, Signal


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
    """
    timestamp: datetime
    regime: str
    dominant_behavior: str
    behavior_probabilities: Dict[str, float]
    breakout_state: str
    active_signals: List[Signal] = field(default_factory=list)


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
               signals: List[Signal]) -> List[TimelineEvent]:
        """
        用新状态更新时间线

        参数:
            timestamp: 当前 K 线时间戳
            market_state: 当前市场趋势
            behavior: 当前行为推断
            breakout_state: 当前突破状态机状态字符串
            signals: 当前信号

        返回:
            新的 TimelineEvent 对象列表（可能为空）
        """
        # 创建新状态快照
        new_state = TimelineState(
            timestamp=timestamp,
            regime=market_state.regime,
            dominant_behavior=behavior.dominant,
            behavior_probabilities=behavior.probabilities.copy(),
            breakout_state=breakout_state,
            active_signals=signals.copy() if signals else []
        )

        # 检查是否应该发出事件
        events_to_emit = self.should_emit_event(self._previous_state, new_state)

        # 创建事件对象
        new_events = []
        for event_type, delta, reason_key in events_to_emit:
            event = TimelineEvent(
                ts=timestamp,
                event_type=event_type,
                delta=round(delta, 4),
                reason=reason_key
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
