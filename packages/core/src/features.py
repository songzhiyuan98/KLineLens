"""
KLineLens 特征计算模块

计算市场分析所需的技术特征。
所有函数都是纯函数，相同输入产生相同输出。

主要特征:
- ATR: 平均真实波幅，用于区域宽度计算和归一化
- RVOL: 相对成交量（Relative Volume），成交量强度 vs 正常水平
- Effort vs Result: VSA 核心指标，推断主力行为
- Wick Ratios: 影线比率，识别买卖压力
- Efficiency: 效率指标，识别吸筹/派发
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from .models import Bar


def calculate_atr(bars: List[Bar], period: int = 14) -> np.ndarray:
    """
    计算平均真实波幅（ATR）

    使用 Wilder 平滑方法计算 ATR。
    用于所有归一化和阈值控制：zone bin width, breakout result, distance-to-zone

    参数:
        bars: K 线列表（最少需要 period + 1 根）
        period: ATR 周期（默认 14）

    返回:
        ATR 数组，长度与 bars 相同
        前 period 个值为 NaN

    算法:
        TR[i] = max(H[i] - L[i], |H[i] - C[i-1]|, |L[i] - C[i-1]|)
        ATR[period] = mean(TR[1:period+1])
        ATR[i] = ATR[i-1] * (period-1)/period + TR[i] / period

    异常:
        ValueError: 如果 bars 数量少于 period + 1
    """
    if len(bars) < period + 1:
        raise ValueError(f"ATR 计算需要至少 {period + 1} 根 K 线，当前只有 {len(bars)} 根")

    n = len(bars)
    highs = np.array([bar.h for bar in bars])
    lows = np.array([bar.l for bar in bars])
    closes = np.array([bar.c for bar in bars])

    # 计算真实波幅 (True Range)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]  # 第一根只用 H-L

    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)

    # 计算 ATR（使用 Wilder 平滑）
    atr = np.full(n, np.nan)

    # 第一个 ATR 值是前 period 个 TR 的简单平均
    atr[period] = np.mean(tr[1:period + 1])

    # 后续使用 Wilder 平滑
    for i in range(period + 1, n):
        atr[i] = atr[i - 1] * (period - 1) / period + tr[i] / period

    return atr


def calculate_rvol(bars: List[Bar], period: int = 30) -> np.ndarray:
    """
    计算相对成交量 RVOL (Relative Volume)

    CRITICAL: 永远不要使用绝对成交量进行判断，必须使用相对成交量。

    参数:
        bars: K 线列表
        period: 成交量均线周期（默认 30 for 1m, 20 for 1d）

    返回:
        RVOL 数组（volume / SMA(volume)）
        前 period-1 个值为 NaN
        如果成交量为 0 或不可用，返回 NaN

    RVOL 解释:
        < 0.7  : 低量（dry-up，枯竭）
        0.7-1.3: 正常
        1.3-1.8: 放量
        >= 1.8 : 高量（spike，确认信号）

    N/A 处理:
        如果 volume = 0 或缺失 → RVOL = NaN
        前端显示 "Volume N/A - confirmation unavailable"
        信号置信度降低 30%
    """
    n = len(bars)
    volumes = np.array([bar.v for bar in bars])

    # 计算 RVOL
    rvol = np.full(n, np.nan)

    for i in range(period - 1, n):
        # 检查当前成交量是否有效
        if volumes[i] <= 0:
            rvol[i] = np.nan
            continue

        # 计算均线（排除 0 值）
        window_vols = volumes[i - period + 1:i + 1]
        valid_vols = window_vols[window_vols > 0]

        if len(valid_vols) < period * 0.5:  # 如果超过一半数据无效
            rvol[i] = np.nan
        elif np.mean(valid_vols) > 0:
            rvol[i] = volumes[i] / np.mean(valid_vols)
        else:
            rvol[i] = np.nan

    return rvol


# 保持向后兼容的别名
def calculate_volume_ratio(bars: List[Bar], period: int = 30) -> np.ndarray:
    """向后兼容别名，请使用 calculate_rvol"""
    return calculate_rvol(bars, period)


def calculate_wick_ratios(bar: Bar) -> Tuple[float, float]:
    """
    计算单根 K 线的上下影线比率

    参数:
        bar: 单根 K 线

    返回:
        (wick_ratio_up, wick_ratio_low) 元组
        每个比率在 [0, 1] 范围内

    算法:
        如果是阳线 (close >= open):
            upper_wick = high - close（上方拒绝）
            lower_wick = open - low（下方需求）
        如果是阴线 (close < open):
            upper_wick = high - open
            lower_wick = close - low

        wick_ratio_up = upper_wick / range
        wick_ratio_low = lower_wick / range

    金融逻辑:
        - 长上影线：卖压/供应拒绝
        - 长下影线：买盘/需求支撑
    """
    total_range = bar.h - bar.l

    if total_range <= 0:
        # Doji 或无效数据
        return (0.5, 0.5)

    if bar.c >= bar.o:
        # 阳线
        upper_wick = bar.h - bar.c
        lower_wick = bar.o - bar.l
    else:
        # 阴线
        upper_wick = bar.h - bar.o
        lower_wick = bar.c - bar.l

    wick_ratio_up = upper_wick / total_range
    wick_ratio_low = lower_wick / total_range

    return (wick_ratio_up, wick_ratio_low)


def calculate_efficiency(bar: Bar, volume: float) -> Tuple[float, float]:
    """
    计算方向效率（价格移动/成交量）

    参数:
        bar: 单根 K 线
        volume: 成交量（或归一化成交量）

    返回:
        (up_efficiency, down_efficiency) 元组
        值越高表示该方向移动效率越高

    算法:
        up_move = close - open（如果是阳线）
        down_move = open - close（如果是阴线）

        up_eff = up_move / volume
        down_eff = down_move / volume

    金融逻辑:
        - 低 up_eff + 高成交量 在阻力位 = 派发（供应压倒需求）
        - 低 down_eff + 高成交量 在支撑位 = 吸筹（需求吸收供应）
    """
    if volume <= 0:
        return (0.0, 0.0)

    up_move = max(bar.c - bar.o, 0)
    down_move = max(bar.o - bar.c, 0)

    up_eff = up_move / volume
    down_eff = down_move / volume

    return (up_eff, down_eff)


def calculate_effort_result(bars: List[Bar],
                           rvol: np.ndarray,
                           atr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算 Effort vs Result (VSA 核心指标)

    Volume Spread Analysis: 用 Effort（成交量）和 Result（价格推进）推断主力行为

    参数:
        bars: K 线列表
        rvol: 相对成交量数组
        atr: ATR 数组

    返回:
        (effort, result) 元组，两个数组

    算法:
        effort = RVOL（成交量强度）
        result = true_range / ATR（价格推进强度）

    四象限解释（VSA 核心）:
        | Effort | Result | 解释                          |
        |--------|--------|-------------------------------|
        | High   | High   | 真突破 / 趋势推进             |
        | High   | Low    | 吸筹/派发（Absorption）⭐      |
        | Low    | High   | 控盘推进 / 脉冲               |
        | Low    | Low    | 量能枯竭 / 盘整               |

    关键洞察:
        High Effort + Low Result = 主力活动（关键位置的吸收）
    """
    n = len(bars)

    # Effort = RVOL（直接使用）
    effort = rvol.copy()

    # Result = true_range / ATR
    result = np.full(n, np.nan)

    for i in range(n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue

        true_range = bars[i].h - bars[i].l
        result[i] = true_range / atr[i]

    return (effort, result)


def is_high_effort_low_result(effort: float, result: float,
                              effort_threshold: float = 1.5,
                              result_threshold: float = 0.6) -> bool:
    """
    判断是否为高 Effort 低 Result（VSA 吸收模式）

    参数:
        effort: RVOL 值
        result: result 值 (range/ATR)
        effort_threshold: Effort 阈值（默认 1.5）
        result_threshold: Result 阈值（默认 0.6）

    返回:
        True 如果是吸收模式

    金融意义:
        高成交量但价格没有大幅移动 = 主力在关键位置吸收筹码
    """
    if np.isnan(effort) or np.isnan(result):
        return False

    return effort >= effort_threshold and result <= result_threshold


def calculate_features(bars: List[Bar],
                       atr_period: int = 14,
                       volume_period: int = 30) -> Dict[str, np.ndarray]:
    """
    计算所有特征

    参数:
        bars: K 线列表
        atr_period: ATR 周期
        volume_period: 成交量均线周期

    返回:
        包含所有特征的字典:
        - 'atr': ATR 数组
        - 'rvol': 相对成交量数组 (RVOL)
        - 'volume_ratio': rvol 的别名（向后兼容）
        - 'effort': Effort 数组（VSA）
        - 'result': Result 数组（VSA）
        - 'wick_up': 上影线比率数组
        - 'wick_low': 下影线比率数组
        - 'up_eff': 上涨效率数组
        - 'down_eff': 下跌效率数组
        - 'close': 收盘价数组
        - 'high': 最高价数组
        - 'low': 最低价数组
        - 'volume': 成交量数组

    使用示例:
        features = calculate_features(bars)
        current_rvol = features['rvol'][-1]
        is_high_volume = features['rvol'][-1] >= 1.8
        is_absorption = is_high_effort_low_result(features['effort'][-1], features['result'][-1])
    """
    n = len(bars)

    # 基础数据数组
    closes = np.array([bar.c for bar in bars])
    highs = np.array([bar.h for bar in bars])
    lows = np.array([bar.l for bar in bars])
    volumes = np.array([bar.v for bar in bars])

    # 计算 ATR
    if len(bars) >= atr_period + 1:
        atr = calculate_atr(bars, atr_period)
    else:
        # 数据不足时使用简单波幅
        atr = highs - lows

    # 计算 RVOL（相对成交量）
    rvol = calculate_rvol(bars, volume_period)

    # 计算 Effort vs Result（VSA 核心）
    effort, result = calculate_effort_result(bars, rvol, atr)

    # 计算影线比率
    wick_up = np.zeros(n)
    wick_low = np.zeros(n)
    for i, bar in enumerate(bars):
        wick_up[i], wick_low[i] = calculate_wick_ratios(bar)

    # 计算效率指标
    up_eff = np.zeros(n)
    down_eff = np.zeros(n)
    for i, bar in enumerate(bars):
        up_eff[i], down_eff[i] = calculate_efficiency(bar, volumes[i])

    return {
        'atr': atr,
        'rvol': rvol,
        'volume_ratio': rvol,  # 向后兼容别名
        'effort': effort,
        'result': result,
        'wick_up': wick_up,
        'wick_low': wick_low,
        'up_eff': up_eff,
        'down_eff': down_eff,
        'close': closes,
        'high': highs,
        'low': lows,
        'volume': volumes,
    }


def get_volume_quality(rvol: np.ndarray, min_valid_ratio: float = 0.7) -> str:
    """
    评估成交量数据质量

    参数:
        rvol: RVOL 数组
        min_valid_ratio: 有效数据的最小比例

    返回:
        'reliable': 数据可靠（>= 70% 有效）
        'partial': 数据部分可用（50-70% 有效）
        'unavailable': 数据不可用（< 50% 有效）
    """
    if len(rvol) == 0:
        return "unavailable"

    valid_count = np.sum(~np.isnan(rvol))
    valid_ratio = valid_count / len(rvol)

    if valid_ratio >= min_valid_ratio:
        return "reliable"
    elif valid_ratio >= 0.5:
        return "partial"
    else:
        return "unavailable"
