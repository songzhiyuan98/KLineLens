"""
KLineLens 市场结构检测模块（增强版）

检测市场结构要素:
- 分形摆动点（Swing Highs/Lows）
- 支撑/阻力区域聚类（增强版：Zone Strength 多维评分）
- 市场趋势状态（上升/下降/震荡）
- 突破状态机（增强版：3-Factor 确认）

增强功能:
- Zone Strength: tests + rejections + reaction_magnitude + recency
- 3-Factor Breakout: Structure + Volume + Result
- Click-to-locate: bar_index 支持
- Volume Quality: 成交量确认状态

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
                  max_zones: int = 5,
                  current_bar_index: int = 0) -> Dict[str, List[Zone]]:
    """
    将摆动点聚类为支撑/阻力区域（增强版）

    参数:
        swing_highs: 摆动高点列表
        swing_lows: 摆动低点列表
        atr: 当前 ATR 值
        timeframe: 时间周期（用于调整区域宽度）
        max_zones: 每侧最多返回的区域数
        current_bar_index: 当前 K 线索引（用于计算 recency）

    返回:
        {"support": [Zone, ...], "resistance": [Zone, ...]}

    增强版 Zone Strength 算法:
        zone_strength = (0.3 × tests) + (0.3 × rejections) + (0.25 × reaction_magnitude) + (0.15 × recency)
        - tests: min(触及次数, 5) / 5
        - rejections: min(反转次数, 5) / 5（暂用 tests 估算）
        - reaction_magnitude: min(最后反应/2ATR, 1)（暂用 ATR 估算）
        - recency: 1 - (bars_since_last_test / 100)

    分箱算法:
        1. 分箱宽度 = 0.5 × ATR
        2. 将摆动点分组到价格箱中
        3. 对于每个有 >= 1 个点的箱:
           - zone.low = 箱最低价 - padding
           - zone.high = 箱最高价 + padding
           - padding = 0.35 × ATR (1m) 或 0.5 × ATR (1d)
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
        """将点聚类为区域（增强版）"""
        if not points:
            return []

        # 按价格排序，保留完整信息
        sorted_points = sorted(points, key=lambda p: p.price)

        # 分箱聚类
        clusters: List[List[SwingPoint]] = []
        current_cluster = [sorted_points[0]]

        for point in sorted_points[1:]:
            if point.price - current_cluster[-1].price <= bin_width:
                current_cluster.append(point)
            else:
                if len(current_cluster) >= 1:
                    clusters.append(current_cluster)
                current_cluster = [point]

        if len(current_cluster) >= 1:
            clusters.append(current_cluster)

        # 转换为 Zone 对象（增强版评分）
        zones = []
        for cluster in clusters:
            prices = [p.price for p in cluster]
            zone_low = min(prices) - padding
            zone_high = max(prices) + padding
            touches = len(cluster)

            # 找最新的测试点
            latest_point = max(cluster, key=lambda p: p.index)
            bars_since_last = current_bar_index - latest_point.index if current_bar_index > 0 else 0

            # 增强版评分算法
            # tests: min(触及次数, 5) / 5
            tests_score = min(touches, 5) / 5.0

            # rejections: 暂用 touches * 0.8 估算（实际需要历史数据）
            rejections = int(touches * 0.8)
            rejections_score = min(rejections, 5) / 5.0

            # reaction_magnitude: 使用 ATR 作为参考（实际需要历史反应数据）
            reaction_magnitude = atr  # 暂用 ATR 作为反应幅度估算
            reaction_score = min(reaction_magnitude / (2 * atr), 1.0) if atr > 0 else 0.0

            # recency: 1 - (bars_since_last_test / 100)
            recency_score = max(1.0 - (bars_since_last / 100.0), 0.0)

            # 综合评分
            score = (0.3 * tests_score +
                     0.3 * rejections_score +
                     0.25 * reaction_score +
                     0.15 * recency_score)

            zones.append(Zone(
                low=zone_low,
                high=zone_high,
                score=round(score, 2),
                touches=touches,
                rejections=rejections,
                last_reaction=round(reaction_magnitude / atr, 2) if atr > 0 else 0.0,
                last_test_time=latest_point.bar_time
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
    突破检测有限状态机（增强版：3-Factor 确认）

    状态:
        IDLE: 无突破尝试
        ATTEMPT: 价格突破区域边界
        CONFIRMED: 突破已确认（3-Factor）
        FAKEOUT: 价格回到区域内（假突破）

    3-Factor 确认:
        Factor 1 - Structure: 连续 2 根 K 线收盘在区域外
        Factor 2 - Volume: RVOL >= 1.8
        Factor 3 - Result: range/ATR >= 0.6

        - 3/3 factors → breakout_confirmed (confidence: 0.85)
        - 2/3 factors → breakout_attempt (confidence: 0.65)
        - 1/3 factors → breakout_attempt (confidence: 0.45)
        - 回撤到区域内 within 3 bars → fakeout

    转换:
        IDLE -> ATTEMPT: 价格突破区域边界
        ATTEMPT -> CONFIRMED: 满足 3/3 或 2/3 factors
        ATTEMPT -> FAKEOUT: 在 3 根 K 线内价格回到区域内
        CONFIRMED -> IDLE: 发出信号后自动重置
        FAKEOUT -> IDLE: 发出信号后自动重置
    """

    def __init__(self,
                 volume_threshold: float = 1.8,
                 result_threshold: float = 0.6,
                 confirm_closes: int = 2,
                 fakeout_bars: int = 3):
        """
        初始化突破状态机（增强版）

        参数:
            volume_threshold: Factor 2 - 确认所需的最低 RVOL
            result_threshold: Factor 3 - 确认所需的最低 range/ATR
            confirm_closes: Factor 1 - 确认所需的连续收盘次数
            fakeout_bars: 假突破判定的最大 K 线数
        """
        self._state = BreakoutState.IDLE
        self._zone: Optional[Zone] = None
        self._direction: Optional[str] = None
        self._attempt_bar_index: Optional[int] = None
        self._consecutive_closes: int = 0
        self._volume_threshold = volume_threshold
        self._result_threshold = result_threshold
        self._confirm_closes = confirm_closes
        self._fakeout_bars = fakeout_bars
        self._max_volume_seen: float = 0.0
        self._max_result_seen: float = 0.0

    def update(self,
               bar: Bar,
               bar_index: int,
               zones: Dict[str, List[Zone]],
               rvol: float,
               atr: float = 0.0) -> Optional[Signal]:
        """
        用新 K 线更新状态机（增强版）

        参数:
            bar: 最新 K 线
            bar_index: K 线索引
            zones: 当前支撑/阻力区域
            rvol: 当前相对成交量 (RVOL)
            atr: 当前 ATR（用于计算 result factor）

        返回:
            如果状态转换产生信号则返回 Signal，否则返回 None
        """
        signal = None

        # 计算 result factor
        bar_range = bar.h - bar.l
        result = bar_range / atr if atr > 0 else 0.0

        if self._state == BreakoutState.IDLE:
            # 检查是否有突破尝试
            signal = self._check_attempt(bar, bar_index, zones, rvol, result)

        elif self._state == BreakoutState.ATTEMPT:
            # 检查是否确认或假突破
            signal = self._check_confirmation(bar, bar_index, rvol, result)

        elif self._state in (BreakoutState.CONFIRMED, BreakoutState.FAKEOUT):
            # 信号已发出，重置状态
            self.reset()

        return signal

    def _check_attempt(self,
                       bar: Bar,
                       bar_index: int,
                       zones: Dict[str, List[Zone]],
                       rvol: float,
                       result: float) -> Optional[Signal]:
        """检查是否有新的突破尝试（增强版：3-Factor）"""
        # 检查向上突破阻力
        for zone in zones.get("resistance", []):
            if bar.h > zone.high:
                self._state = BreakoutState.ATTEMPT
                self._zone = zone
                self._direction = "up"
                self._attempt_bar_index = bar_index
                self._consecutive_closes = 1 if bar.c > zone.high else 0
                self._max_volume_seen = rvol if not np.isnan(rvol) else 0.0
                self._max_result_seen = result

                # 计算 3-Factor 得分
                factors = self._count_factors(rvol, result)
                confidence, signal_type, volume_quality = self._get_signal_params(factors, rvol)

                return Signal(
                    type=signal_type,
                    direction="up",
                    level=zone.high,
                    confidence=confidence,
                    bar_time=bar.t,
                    bar_index=bar_index,
                    volume_quality=volume_quality
                )

        # 检查向下突破支撑
        for zone in zones.get("support", []):
            if bar.l < zone.low:
                self._state = BreakoutState.ATTEMPT
                self._zone = zone
                self._direction = "down"
                self._attempt_bar_index = bar_index
                self._consecutive_closes = 1 if bar.c < zone.low else 0
                self._max_volume_seen = rvol if not np.isnan(rvol) else 0.0
                self._max_result_seen = result

                # 计算 3-Factor 得分
                factors = self._count_factors(rvol, result)
                confidence, signal_type, volume_quality = self._get_signal_params(factors, rvol)

                return Signal(
                    type=signal_type,
                    direction="down",
                    level=zone.low,
                    confidence=confidence,
                    bar_time=bar.t,
                    bar_index=bar_index,
                    volume_quality=volume_quality
                )

        return None

    def _count_factors(self, rvol: float, result: float) -> int:
        """计算满足的因子数（3-Factor）"""
        factors = 0

        # Factor 1: Structure - 连续收盘
        if self._consecutive_closes >= self._confirm_closes:
            factors += 1

        # Factor 2: Volume - RVOL >= threshold
        if not np.isnan(rvol) and rvol >= self._volume_threshold:
            factors += 1

        # Factor 3: Result - range/ATR >= threshold
        if result >= self._result_threshold:
            factors += 1

        return factors

    def _get_signal_params(self, factors: int, rvol: float) -> Tuple[float, str, str]:
        """根据 factors 数量返回信号参数"""
        # Volume quality
        if np.isnan(rvol):
            volume_quality = "unavailable"
        elif rvol >= self._volume_threshold:
            volume_quality = "confirmed"
        else:
            volume_quality = "pending"

        # Signal type and confidence based on factors
        if factors >= 3:
            return (0.85, "breakout_confirmed", volume_quality)
        elif factors == 2:
            return (0.65, "breakout_attempt", volume_quality)
        else:
            return (0.45, "breakout_attempt", volume_quality)

    def _check_confirmation(self,
                            bar: Bar,
                            bar_index: int,
                            rvol: float,
                            result: float) -> Optional[Signal]:
        """检查突破是否确认或假突破（增强版：3-Factor）"""
        if self._zone is None or self._attempt_bar_index is None:
            self.reset()
            return None

        bars_since_attempt = bar_index - self._attempt_bar_index

        # 更新最大值
        if not np.isnan(rvol):
            self._max_volume_seen = max(self._max_volume_seen, rvol)
        self._max_result_seen = max(self._max_result_seen, result)

        if self._direction == "up":
            # 检查是否仍在区域外
            if bar.c > self._zone.high:
                self._consecutive_closes += 1

                # 计算 3-Factor 得分
                factors = self._count_factors(self._max_volume_seen, self._max_result_seen)

                # 3/3 factors → 确认
                if factors >= 3:
                    return self._emit_confirmed(bar, bar_index)
                # 2/3 factors 且结构已满足 → 也确认
                elif factors >= 2 and self._consecutive_closes >= self._confirm_closes:
                    return self._emit_confirmed(bar, bar_index)

            else:
                # 价格回到区域内
                if bars_since_attempt <= self._fakeout_bars:
                    return self._emit_fakeout(bar, bar_index)
                else:
                    # 超时，重置
                    self.reset()

        elif self._direction == "down":
            # 检查是否仍在区域外
            if bar.c < self._zone.low:
                self._consecutive_closes += 1

                # 计算 3-Factor 得分
                factors = self._count_factors(self._max_volume_seen, self._max_result_seen)

                # 3/3 factors → 确认
                if factors >= 3:
                    return self._emit_confirmed(bar, bar_index)
                # 2/3 factors 且结构已满足 → 也确认
                elif factors >= 2 and self._consecutive_closes >= self._confirm_closes:
                    return self._emit_confirmed(bar, bar_index)

            else:
                # 价格回到区域内
                if bars_since_attempt <= self._fakeout_bars:
                    return self._emit_fakeout(bar, bar_index)
                else:
                    # 超时，重置
                    self.reset()

        # 检查超时（长时间未确认也未假突破）
        if bars_since_attempt > self._fakeout_bars * 2:
            self.reset()

        return None

    def _emit_confirmed(self, bar: Bar, bar_index: int) -> Signal:
        """发出确认信号（增强版）"""
        self._state = BreakoutState.CONFIRMED
        level = self._zone.high if self._direction == "up" else self._zone.low

        # 确定 volume_quality
        if self._max_volume_seen >= self._volume_threshold:
            volume_quality = "confirmed"
        elif self._max_volume_seen > 0:
            volume_quality = "pending"
        else:
            volume_quality = "unavailable"

        return Signal(
            type="breakout_confirmed",
            direction=self._direction,
            level=level,
            confidence=0.85,
            bar_time=bar.t,
            bar_index=bar_index,
            volume_quality=volume_quality
        )

    def _emit_fakeout(self, bar: Bar, bar_index: int) -> Signal:
        """发出假突破信号（增强版）"""
        self._state = BreakoutState.FAKEOUT
        level = self._zone.high if self._direction == "up" else self._zone.low

        # 确定 volume_quality
        if self._max_volume_seen >= self._volume_threshold:
            volume_quality = "confirmed"
        elif self._max_volume_seen > 0:
            volume_quality = "pending"
        else:
            volume_quality = "unavailable"

        return Signal(
            type="fakeout",
            direction=self._direction,
            level=level,
            confidence=0.75,
            bar_time=bar.t,
            bar_index=bar_index,
            volume_quality=volume_quality
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
        self._max_volume_seen = 0.0
        self._max_result_seen = 0.0
