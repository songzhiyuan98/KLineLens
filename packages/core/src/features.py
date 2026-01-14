"""
KLineLens 特征计算模块

计算市场分析所需的技术特征。
所有函数都是纯函数，相同输入产生相同输出。

主要特征:
- ATR: 平均真实波幅，用于区域宽度计算
- Volume Ratio: 成交量比率，识别异常放量
- Wick Ratios: 影线比率，识别买卖压力
- Efficiency: 效率指标，识别吸筹/派发
"""

from typing import List, Dict, Tuple
import numpy as np
from .models import Bar


def calculate_atr(bars: List[Bar], period: int = 14) -> np.ndarray:
    """
    计算平均真实波幅（ATR）

    使用 Wilder 平滑方法计算 ATR。

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


def calculate_volume_ratio(bars: List[Bar], period: int = 30) -> np.ndarray:
    """
    计算成交量比率（相对于移动平均）

    参数:
        bars: K 线列表
        period: 成交量均线周期（默认 30）

    返回:
        成交量比率数组（volume / SMA(volume)）
        前 period-1 个值为 NaN

    说明:
        volume_ratio >= 1.8 表示异常放量（突破确认）
        volume_ratio <= 0.7 表示缩量
    """
    n = len(bars)
    volumes = np.array([bar.v for bar in bars])

    # 计算成交量简单移动平均
    volume_ratio = np.full(n, np.nan)

    for i in range(period - 1, n):
        avg_vol = np.mean(volumes[i - period + 1:i + 1])
        if avg_vol > 0:
            volume_ratio[i] = volumes[i] / avg_vol
        else:
            volume_ratio[i] = 0.0

    return volume_ratio


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
        - 'volume_ratio': 成交量比率数组
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
        current_atr = features['atr'][-1]
        is_high_volume = features['volume_ratio'][-1] >= 1.8
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

    # 计算成交量比率
    volume_ratio = calculate_volume_ratio(bars, volume_period)

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
        'volume_ratio': volume_ratio,
        'wick_up': wick_up,
        'wick_low': wick_low,
        'up_eff': up_eff,
        'down_eff': down_eff,
        'close': closes,
        'high': highs,
        'low': lows,
        'volume': volumes,
    }
