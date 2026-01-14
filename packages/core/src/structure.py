"""
KLineLens 市场结构检测模块

检测市场结构要素:
- 分形摆动点（Swing Highs/Lows）
- 支撑/阻力区域聚类
- 市场趋势状态（上升/下降/震荡）
- 突破状态机（尝试/确认/假突破）

所有函数都是纯函数，确定性输出。
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np
from .models import Bar, Zone, Signal, MarketState


class BreakoutState(Enum):
    """突破状态机状态"""
    IDLE = "idle"           # 无突破活动
    ATTEMPT = "attempt"     # 价格突破区域边界
    CONFIRMED = "confirmed" # 突破已确认
    FAKEOUT = "fakeout"     # 假突破


@dataclass
class SwingPoint:
    """
    摆动点（分形高低点）

    属性:
        index: K 线索引
        price: 价格（高点用 high，低点用 low）
        bar_time: K 线时间
        is_high: True 为摆动高点，False 为摆动低点
    """
    index: int
    price: float
    bar_time: datetime
    is_high: bool


def find_swing_points(bars: List[Bar], n: int = 4) -> Tuple[List[SwingPoint], List[SwingPoint]]:
    """
    查找分形摆动高点和低点

    参数:
        bars: K 线列表
        n: 分形阶数（两侧需要的 K 线数量）

    返回:
        (swing_highs, swing_lows) - 摆动点列表元组

    算法:
        swing_high[i] = True 如果 high[i] == max(high[i-n:i+n+1])
        swing_low[i] = True 如果 low[i] == min(low[i-n:i+n+1])

    注意:
        - 前后各 n 根 K 线不能成为摆动点
        - 返回时间最近的已确认摆动点
    """
    if len(bars) < 2 * n + 1:
        return ([], [])

    swing_highs = []
    swing_lows = []

    highs = np.array([bar.h for bar in bars])
    lows = np.array([bar.l for bar in bars])

    # 查找分形高点和低点
    for i in range(n, len(bars) - n):
        # 检查高点
        window_high = highs[i - n:i + n + 1]
        if highs[i] == np.max(window_high):
            swing_highs.append(SwingPoint(
                index=i,
                price=bars[i].h,
                bar_time=bars[i].t,
                is_high=True
            ))

        # 检查低点
        window_low = lows[i - n:i + n + 1]
        if lows[i] == np.min(window_low):
            swing_lows.append(SwingPoint(
                index=i,
                price=bars[i].l,
                bar_time=bars[i].t,
                is_high=False
            ))

    return (swing_highs, swing_lows)


def cluster_zones(swing_highs: List[SwingPoint],
                  swing_lows: List[SwingPoint],
                  atr: float,
                  timeframe: str = "1d",
                  max_zones: int = 5) -> Dict[str, List[Zone]]:
    """
    将摆动点聚类为支撑/阻力区域

    参数:
        swing_highs: 摆动高点列表
        swing_lows: 摆动低点列表
        atr: 当前 ATR 值
        timeframe: 时间周期（用于调整区域宽度）
        max_zones: 每侧最多返回的区域数

    返回:
        {"support": [Zone, ...], "resistance": [Zone, ...]}

    算法:
        1. 分箱宽度 = 0.5 × ATR
        2. 将摆动点分组到价格箱中
        3. 对于每个有 >= 2 个点的箱:
           - zone.low = 箱最低价 - padding
           - zone.high = 箱最高价 + padding
           - padding = 0.35 × ATR (1m) 或 0.5 × ATR (1d)
        4. 评分 = 触及次数 + 反应强度
        5. 返回前 max_zones 个区域，按评分降序排列
    """
    if atr <= 0:
        return {"support": [], "resistance": []}

    # 根据时间周期设置 padding
    if timeframe == "1m":
        padding_mult = 0.35
    elif timeframe == "5m":
        padding_mult = 0.4
    else:  # 1d 或其他
        padding_mult = 0.5

    padding = atr * padding_mult
    bin_width = atr * 0.5

    def _cluster_points(points: List[SwingPoint]) -> List[Zone]:
        """将点聚类为区域"""
        if not points:
            return []

        # 按价格排序
        prices = sorted([p.price for p in points])

        # 分箱聚类
        clusters = []
        current_cluster = [prices[0]]

        for price in prices[1:]:
            if price - current_cluster[-1] <= bin_width:
                current_cluster.append(price)
            else:
                if len(current_cluster) >= 1:  # 至少 1 个点形成区域
                    clusters.append(current_cluster)
                current_cluster = [price]

        if len(current_cluster) >= 1:
            clusters.append(current_cluster)

        # 转换为 Zone 对象
        zones = []
        for cluster in clusters:
            zone_low = min(cluster) - padding
            zone_high = max(cluster) + padding
            touches = len(cluster)

            # 评分：触及次数归一化（简化版）
            score = min(touches / 5.0, 1.0)  # 5 次触及得满分

            zones.append(Zone(
                low=zone_low,
                high=zone_high,
                score=score,
                touches=touches
            ))

        # 按评分排序，返回前 max_zones 个
        zones.sort(key=lambda z: z.score, reverse=True)
        return zones[:max_zones]

    # 聚类支撑区域（使用摆动低点）
    support_zones = _cluster_points(swing_lows)

    # 聚类阻力区域（使用摆动高点）
    resistance_zones = _cluster_points(swing_highs)

    return {
        "support": support_zones,
        "resistance": resistance_zones
    }


def classify_regime(swing_highs: List[SwingPoint],
                    swing_lows: List[SwingPoint],
                    m: int = 6) -> MarketState:
    """
    基于摆动点结构分类市场趋势

    参数:
        swing_highs: 摆动高点列表（最新的在最后）
        swing_lows: 摆动低点列表（最新的在最后）
        m: 用于分析的近期摆动点数量

    返回:
        MarketState，包含 regime 和 confidence

    算法:
        1. 取最近 m 个摆动高点和低点
        2. 统计 Higher-Highs (HH): 当前高点 > 前一个高点
        3. 统计 Higher-Lows (HL): 当前低点 > 前一个低点
        4. 统计 Lower-Lows (LL): 当前低点 < 前一个低点
        5. 统计 Lower-Highs (LH): 当前高点 < 前一个高点

        up_score = HH + HL
        down_score = LL + LH

        如果 up_score 占优 (>= 70%): regime = "uptrend"
        如果 down_score 占优 (>= 70%): regime = "downtrend"
        否则: regime = "range"
    """
    # 需要至少 2 个摆动点来比较
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return MarketState(regime="range", confidence=0.5)

    # 取最近 m 个点
    recent_highs = swing_highs[-m:] if len(swing_highs) >= m else swing_highs
    recent_lows = swing_lows[-m:] if len(swing_lows) >= m else swing_lows

    # 统计 HH/LH
    hh_count = 0
    lh_count = 0
    for i in range(1, len(recent_highs)):
        if recent_highs[i].price > recent_highs[i - 1].price:
            hh_count += 1
        elif recent_highs[i].price < recent_highs[i - 1].price:
            lh_count += 1

    # 统计 HL/LL
    hl_count = 0
    ll_count = 0
    for i in range(1, len(recent_lows)):
        if recent_lows[i].price > recent_lows[i - 1].price:
            hl_count += 1
        elif recent_lows[i].price < recent_lows[i - 1].price:
            ll_count += 1

    # 计算总比较次数
    total_high_comparisons = max(len(recent_highs) - 1, 1)
    total_low_comparisons = max(len(recent_lows) - 1, 1)
    total_comparisons = total_high_comparisons + total_low_comparisons

    # 计算上升/下降得分
    up_score = hh_count + hl_count
    down_score = ll_count + lh_count

    # 判断趋势
    threshold = 0.6  # 60% 阈值

    if up_score / total_comparisons >= threshold:
        regime = "uptrend"
        confidence = up_score / total_comparisons
    elif down_score / total_comparisons >= threshold:
        regime = "downtrend"
        confidence = down_score / total_comparisons
    else:
        regime = "range"
        # 震荡置信度：两边得分越接近，置信度越高
        confidence = 1.0 - abs(up_score - down_score) / total_comparisons

    return MarketState(regime=regime, confidence=round(confidence, 2))


class BreakoutFSM:
    """
    突破检测有限状态机

    状态:
        IDLE: 无突破尝试
        ATTEMPT: 价格突破区域边界
        CONFIRMED: 突破已确认（成交量 + 连续收盘）
        FAKEOUT: 价格回到区域内（假突破）

    转换:
        IDLE -> ATTEMPT: 价格突破区域边界
        ATTEMPT -> CONFIRMED: volume_ratio >= 1.8 且连续 2 根 K 线收盘在区域外
        ATTEMPT -> FAKEOUT: 在 3 根 K 线内价格回到区域内
        CONFIRMED -> IDLE: 发出信号后自动重置
        FAKEOUT -> IDLE: 发出信号后自动重置
    """

    def __init__(self,
                 volume_threshold: float = 1.8,
                 confirm_closes: int = 2,
                 fakeout_bars: int = 3):
        """
        初始化突破状态机

        参数:
            volume_threshold: 确认所需的最低成交量比率
            confirm_closes: 确认所需的连续收盘次数
            fakeout_bars: 假突破判定的最大 K 线数
        """
        self._state = BreakoutState.IDLE
        self._zone: Optional[Zone] = None
        self._direction: Optional[str] = None
        self._attempt_bar_index: Optional[int] = None
        self._consecutive_closes: int = 0
        self._volume_threshold = volume_threshold
        self._confirm_closes = confirm_closes
        self._fakeout_bars = fakeout_bars

    def update(self,
               bar: Bar,
               bar_index: int,
               zones: Dict[str, List[Zone]],
               volume_ratio: float) -> Optional[Signal]:
        """
        用新 K 线更新状态机

        参数:
            bar: 最新 K 线
            bar_index: K 线索引
            zones: 当前支撑/阻力区域
            volume_ratio: 当前成交量比率

        返回:
            如果状态转换产生信号则返回 Signal，否则返回 None
        """
        signal = None

        if self._state == BreakoutState.IDLE:
            # 检查是否有突破尝试
            signal = self._check_attempt(bar, bar_index, zones, volume_ratio)

        elif self._state == BreakoutState.ATTEMPT:
            # 检查是否确认或假突破
            signal = self._check_confirmation(bar, bar_index, volume_ratio)

        elif self._state in (BreakoutState.CONFIRMED, BreakoutState.FAKEOUT):
            # 信号已发出，重置状态
            self.reset()

        return signal

    def _check_attempt(self,
                       bar: Bar,
                       bar_index: int,
                       zones: Dict[str, List[Zone]],
                       volume_ratio: float) -> Optional[Signal]:
        """检查是否有新的突破尝试"""
        # 检查向上突破阻力
        for zone in zones.get("resistance", []):
            if bar.h > zone.high:
                self._state = BreakoutState.ATTEMPT
                self._zone = zone
                self._direction = "up"
                self._attempt_bar_index = bar_index
                self._consecutive_closes = 1 if bar.c > zone.high else 0

                # 如果第一根就满足确认条件
                if bar.c > zone.high and volume_ratio >= self._volume_threshold:
                    if self._consecutive_closes >= self._confirm_closes:
                        return self._emit_confirmed(bar)

                return Signal(
                    type="breakout_attempt",
                    direction="up",
                    level=zone.high,
                    confidence=0.5,
                    bar_time=bar.t
                )

        # 检查向下突破支撑
        for zone in zones.get("support", []):
            if bar.l < zone.low:
                self._state = BreakoutState.ATTEMPT
                self._zone = zone
                self._direction = "down"
                self._attempt_bar_index = bar_index
                self._consecutive_closes = 1 if bar.c < zone.low else 0

                # 如果第一根就满足确认条件
                if bar.c < zone.low and volume_ratio >= self._volume_threshold:
                    if self._consecutive_closes >= self._confirm_closes:
                        return self._emit_confirmed(bar)

                return Signal(
                    type="breakout_attempt",
                    direction="down",
                    level=zone.low,
                    confidence=0.5,
                    bar_time=bar.t
                )

        return None

    def _check_confirmation(self,
                            bar: Bar,
                            bar_index: int,
                            volume_ratio: float) -> Optional[Signal]:
        """检查突破是否确认或假突破"""
        if self._zone is None or self._attempt_bar_index is None:
            self.reset()
            return None

        bars_since_attempt = bar_index - self._attempt_bar_index

        if self._direction == "up":
            # 检查是否仍在区域外
            if bar.c > self._zone.high:
                self._consecutive_closes += 1

                # 检查确认条件
                if (self._consecutive_closes >= self._confirm_closes and
                        volume_ratio >= self._volume_threshold):
                    return self._emit_confirmed(bar)

            else:
                # 价格回到区域内
                if bars_since_attempt <= self._fakeout_bars:
                    return self._emit_fakeout(bar)
                else:
                    # 超时，重置
                    self.reset()

        elif self._direction == "down":
            # 检查是否仍在区域外
            if bar.c < self._zone.low:
                self._consecutive_closes += 1

                # 检查确认条件
                if (self._consecutive_closes >= self._confirm_closes and
                        volume_ratio >= self._volume_threshold):
                    return self._emit_confirmed(bar)

            else:
                # 价格回到区域内
                if bars_since_attempt <= self._fakeout_bars:
                    return self._emit_fakeout(bar)
                else:
                    # 超时，重置
                    self.reset()

        # 检查超时（长时间未确认也未假突破）
        if bars_since_attempt > self._fakeout_bars * 2:
            self.reset()

        return None

    def _emit_confirmed(self, bar: Bar) -> Signal:
        """发出确认信号"""
        self._state = BreakoutState.CONFIRMED
        level = self._zone.high if self._direction == "up" else self._zone.low
        return Signal(
            type="breakout_confirmed",
            direction=self._direction,
            level=level,
            confidence=0.8,
            bar_time=bar.t
        )

    def _emit_fakeout(self, bar: Bar) -> Signal:
        """发出假突破信号"""
        self._state = BreakoutState.FAKEOUT
        level = self._zone.high if self._direction == "up" else self._zone.low
        return Signal(
            type="fakeout",
            direction=self._direction,
            level=level,
            confidence=0.7,
            bar_time=bar.t
        )

    def get_state(self) -> BreakoutState:
        """返回当前状态"""
        return self._state

    def get_state_str(self) -> str:
        """返回当前状态字符串"""
        return self._state.value

    def reset(self) -> None:
        """重置状态机"""
        self._state = BreakoutState.IDLE
        self._zone = None
        self._direction = None
        self._attempt_bar_index = None
        self._consecutive_closes = 0
