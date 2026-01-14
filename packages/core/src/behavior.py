"""
KLineLens 行为推断模块

推断市场参与者行为的概率分布。
基于 Wyckoff 方法论的 5 种行为类型:

- accumulation: 聪明钱在支撑位吸筹
- shakeout: 洗盘（跌破支撑后快速收回）
- markup: 上涨趋势（确认突破后的持续上涨）
- distribution: 聪明钱在阻力位派发
- markdown: 下跌趋势（确认跌破后的持续下跌）

所有函数都是纯函数，确定性输出。
"""

from typing import List, Dict
import numpy as np
from .models import Bar, Zone, Signal, MarketState, Behavior, Evidence


# 行为类型常量
BEHAVIOR_ACCUMULATION = "accumulation"
BEHAVIOR_SHAKEOUT = "shakeout"
BEHAVIOR_MARKUP = "markup"
BEHAVIOR_DISTRIBUTION = "distribution"
BEHAVIOR_MARKDOWN = "markdown"

ALL_BEHAVIORS = [
    BEHAVIOR_ACCUMULATION,
    BEHAVIOR_SHAKEOUT,
    BEHAVIOR_MARKUP,
    BEHAVIOR_DISTRIBUTION,
    BEHAVIOR_MARKDOWN
]


def _is_near_zone(price: float, zones: List[Zone], threshold: float = 0.5) -> bool:
    """检查价格是否接近某个区域"""
    for zone in zones:
        zone_mid = (zone.low + zone.high) / 2
        zone_width = zone.high - zone.low
        if abs(price - zone_mid) <= zone_width * threshold:
            return True
    return False


def _get_nearest_zone(price: float, zones: List[Zone]) -> Zone:
    """获取最近的区域"""
    if not zones:
        return None

    nearest = zones[0]
    nearest_dist = abs(price - (nearest.low + nearest.high) / 2)

    for zone in zones[1:]:
        zone_mid = (zone.low + zone.high) / 2
        dist = abs(price - zone_mid)
        if dist < nearest_dist:
            nearest = zone
            nearest_dist = dist

    return nearest


def score_accumulation(bars: List[Bar],
                       features: Dict[str, np.ndarray],
                       zones: Dict[str, List[Zone]],
                       lookback: int = 20) -> float:
    """
    计算吸筹行为得分

    指标:
        - 价格接近支撑区域 (+0.3)
        - 支撑位高成交量 (+0.25)
        - 低下跌效率（需求吸收供应）(+0.25)
        - 长下影线（需求影线）(+0.2)

    返回:
        原始得分（未归一化）
    """
    if len(bars) < lookback:
        lookback = len(bars)

    score = 0.0
    support_zones = zones.get("support", [])

    if not support_zones:
        return score

    # 获取最近数据
    recent_bars = bars[-lookback:]
    close_prices = features['close'][-lookback:]
    volume_ratios = features['volume_ratio'][-lookback:]
    down_effs = features['down_eff'][-lookback:]
    wick_lows = features['wick_low'][-lookback:]

    # 1. 价格接近支撑区域
    current_price = close_prices[-1]
    if _is_near_zone(current_price, support_zones):
        score += 0.3

    # 2. 支撑位高成交量
    near_support_high_vol = 0
    for i, price in enumerate(close_prices):
        if _is_near_zone(price, support_zones):
            if not np.isnan(volume_ratios[i]) and volume_ratios[i] >= 1.5:
                near_support_high_vol += 1

    if near_support_high_vol >= 2:
        score += 0.25

    # 3. 低下跌效率（需求吸收供应）
    # 低 down_eff 意味着价格不跌，尽管有卖压
    avg_down_eff = np.nanmean(down_effs)
    if avg_down_eff < np.nanmean(features['down_eff']) * 0.7:
        score += 0.25

    # 4. 长下影线（需求影线）
    avg_wick_low = np.mean(wick_lows)
    if avg_wick_low > 0.3:
        score += 0.2

    return score


def score_shakeout(bars: List[Bar],
                   features: Dict[str, np.ndarray],
                   zones: Dict[str, List[Zone]],
                   lookback: int = 10) -> float:
    """
    计算洗盘行为得分

    指标:
        - 价格跌破支撑后收回 (+0.35)
        - 跌破时的长下影线 (+0.25)
        - 跌破时的高成交量 (+0.25)
        - 快速收回（1-3 根 K 线）(+0.15)

    返回:
        原始得分（未归一化）
    """
    if len(bars) < lookback:
        lookback = len(bars)

    score = 0.0
    support_zones = zones.get("support", [])

    if not support_zones:
        return score

    recent_bars = bars[-lookback:]
    lows = features['low'][-lookback:]
    closes = features['close'][-lookback:]
    volume_ratios = features['volume_ratio'][-lookback:]
    wick_lows = features['wick_low'][-lookback:]

    # 检查是否有"扫描-收回"模式
    for zone in support_zones:
        sweep_detected = False
        sweep_index = -1

        for i in range(len(recent_bars)):
            # 检查是否跌破支撑
            if lows[i] < zone.low:
                sweep_detected = True
                sweep_index = i

                # 检查是否收回
                if closes[i] >= zone.low:
                    # 同一根 K 线内收回（典型洗盘）
                    score += 0.35

                    # 长下影线
                    if wick_lows[i] > 0.4:
                        score += 0.25

                    # 高成交量
                    if not np.isnan(volume_ratios[i]) and volume_ratios[i] >= 1.5:
                        score += 0.25

                    return score

        # 检查后续 K 线收回
        if sweep_detected and sweep_index >= 0:
            for j in range(sweep_index + 1, min(sweep_index + 4, len(recent_bars))):
                if closes[j] >= zone.low:
                    # 快速收回
                    bars_to_reclaim = j - sweep_index
                    score += 0.35

                    if bars_to_reclaim <= 2:
                        score += 0.15

                    # 扫描时的长下影线
                    if wick_lows[sweep_index] > 0.3:
                        score += 0.25

                    return score

    return score


def score_markup(bars: List[Bar],
                 features: Dict[str, np.ndarray],
                 market_state: MarketState,
                 signals: List[Signal],
                 lookback: int = 20) -> float:
    """
    计算上涨（markup）行为得分

    指标:
        - 确认向上突破 (+0.35)
        - 趋势中的高低点抬高结构 (+0.25)
        - 回调时缩量 (+0.2)
        - 上升趋势状态 (+0.2)

    返回:
        原始得分（未归一化）
    """
    score = 0.0

    # 1. 确认向上突破
    for signal in signals:
        if signal.type == "breakout_confirmed" and signal.direction == "up":
            score += 0.35
            break

    # 2. 上升趋势状态
    if market_state.regime == "uptrend":
        score += 0.2 * market_state.confidence

    # 3. 回调时缩量
    if len(bars) >= lookback:
        closes = features['close'][-lookback:]
        volume_ratios = features['volume_ratio'][-lookback:]

        # 找到回调期（价格下跌的连续 K 线）
        pullback_volumes = []
        advance_volumes = []

        for i in range(1, len(closes)):
            if closes[i] < closes[i - 1]:  # 回调
                if not np.isnan(volume_ratios[i]):
                    pullback_volumes.append(volume_ratios[i])
            else:  # 上涨
                if not np.isnan(volume_ratios[i]):
                    advance_volumes.append(volume_ratios[i])

        if pullback_volumes and advance_volumes:
            avg_pullback_vol = np.mean(pullback_volumes)
            avg_advance_vol = np.mean(advance_volumes)

            # 回调缩量，上涨放量
            if avg_pullback_vol < avg_advance_vol * 0.8:
                score += 0.2

    # 4. 高低点抬高（通过 up_eff 代理）
    up_effs = features['up_eff'][-lookback:] if len(bars) >= lookback else features['up_eff']
    if np.nanmean(up_effs) > 0:
        score += 0.25 * min(np.nanmean(up_effs) * 1000, 1.0)

    return score


def score_distribution(bars: List[Bar],
                       features: Dict[str, np.ndarray],
                       zones: Dict[str, List[Zone]],
                       lookback: int = 20) -> float:
    """
    计算派发行为得分

    指标:
        - 价格接近阻力区域 (+0.3)
        - 阻力位高成交量 (+0.25)
        - 低上涨效率（供应压倒需求）(+0.25)
        - 长上影线（拒绝影线）(+0.2)

    返回:
        原始得分（未归一化）
    """
    if len(bars) < lookback:
        lookback = len(bars)

    score = 0.0
    resistance_zones = zones.get("resistance", [])

    if not resistance_zones:
        return score

    # 获取最近数据
    close_prices = features['close'][-lookback:]
    volume_ratios = features['volume_ratio'][-lookback:]
    up_effs = features['up_eff'][-lookback:]
    wick_ups = features['wick_up'][-lookback:]

    # 1. 价格接近阻力区域
    current_price = close_prices[-1]
    if _is_near_zone(current_price, resistance_zones):
        score += 0.3

    # 2. 阻力位高成交量
    near_resistance_high_vol = 0
    for i, price in enumerate(close_prices):
        if _is_near_zone(price, resistance_zones):
            if not np.isnan(volume_ratios[i]) and volume_ratios[i] >= 1.5:
                near_resistance_high_vol += 1

    if near_resistance_high_vol >= 2:
        score += 0.25

    # 3. 低上涨效率（供应压倒需求）
    avg_up_eff = np.nanmean(up_effs)
    if avg_up_eff < np.nanmean(features['up_eff']) * 0.7:
        score += 0.25

    # 4. 长上影线（拒绝影线）
    avg_wick_up = np.mean(wick_ups)
    if avg_wick_up > 0.3:
        score += 0.2

    return score


def score_markdown(bars: List[Bar],
                   features: Dict[str, np.ndarray],
                   market_state: MarketState,
                   signals: List[Signal],
                   lookback: int = 20) -> float:
    """
    计算下跌（markdown）行为得分

    指标:
        - 确认向下突破 (+0.35)
        - 趋势中的高低点降低结构 (+0.25)
        - 反弹时缩量 (+0.2)
        - 下降趋势状态 (+0.2)

    返回:
        原始得分（未归一化）
    """
    score = 0.0

    # 1. 确认向下突破
    for signal in signals:
        if signal.type == "breakout_confirmed" and signal.direction == "down":
            score += 0.35
            break

    # 2. 下降趋势状态
    if market_state.regime == "downtrend":
        score += 0.2 * market_state.confidence

    # 3. 反弹时缩量
    if len(bars) >= lookback:
        closes = features['close'][-lookback:]
        volume_ratios = features['volume_ratio'][-lookback:]

        # 找到反弹期（价格上涨的连续 K 线）
        bounce_volumes = []
        decline_volumes = []

        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:  # 反弹
                if not np.isnan(volume_ratios[i]):
                    bounce_volumes.append(volume_ratios[i])
            else:  # 下跌
                if not np.isnan(volume_ratios[i]):
                    decline_volumes.append(volume_ratios[i])

        if bounce_volumes and decline_volumes:
            avg_bounce_vol = np.mean(bounce_volumes)
            avg_decline_vol = np.mean(decline_volumes)

            # 反弹缩量，下跌放量
            if avg_bounce_vol < avg_decline_vol * 0.8:
                score += 0.2

    # 4. 高低点降低（通过 down_eff 代理）
    down_effs = features['down_eff'][-lookback:] if len(bars) >= lookback else features['down_eff']
    if np.nanmean(down_effs) > 0:
        score += 0.25 * min(np.nanmean(down_effs) * 1000, 1.0)

    return score


def scores_to_probabilities(scores: Dict[str, float]) -> Dict[str, float]:
    """
    使用 softmax 将原始得分转换为概率

    参数:
        scores: 行为 -> 原始得分 字典

    返回:
        行为 -> 概率 字典（总和为 1.0）

    算法:
        exp_scores = exp(scores - max(scores))  # 数值稳定性
        probabilities = exp_scores / sum(exp_scores)
    """
    if not scores:
        return {b: 0.2 for b in ALL_BEHAVIORS}

    # 转换为数组
    behaviors = list(scores.keys())
    score_values = np.array([scores[b] for b in behaviors])

    # 数值稳定的 softmax
    exp_scores = np.exp(score_values - np.max(score_values))
    probabilities = exp_scores / exp_scores.sum()

    # 转回字典
    result = {b: round(float(p), 4) for b, p in zip(behaviors, probabilities)}

    return result


def generate_evidence(bars: List[Bar],
                      dominant_behavior: str,
                      features: Dict[str, np.ndarray],
                      zones: Dict[str, List[Zone]]) -> List[Evidence]:
    """
    生成支持主导行为的证据

    参数:
        bars: 最近的 K 线
        dominant_behavior: 概率最高的行为
        features: 预计算的特征
        zones: 支撑/阻力区域

    返回:
        Evidence 对象列表（通常 2-3 个）

    证据生成规则:
        - 每个证据包含 behavior, bar_time, metrics, note
        - note 使用 i18n 格式: "evidence.{behavior}.{indicator}"
    """
    evidence_list = []

    if not bars:
        return evidence_list

    current_bar = bars[-1]
    current_price = features['close'][-1]
    current_vol_ratio = features['volume_ratio'][-1] if not np.isnan(features['volume_ratio'][-1]) else 1.0
    current_wick_up = features['wick_up'][-1]
    current_wick_low = features['wick_low'][-1]

    if dominant_behavior == BEHAVIOR_ACCUMULATION:
        # 吸筹证据
        support_zones = zones.get("support", [])
        if support_zones and _is_near_zone(current_price, support_zones):
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_ACCUMULATION,
                bar_time=current_bar.t,
                metrics={"price": current_price, "zone_low": support_zones[0].low},
                note="evidence.accumulation.near_support"
            ))

        if current_vol_ratio >= 1.5:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_ACCUMULATION,
                bar_time=current_bar.t,
                metrics={"volume_ratio": current_vol_ratio},
                note="evidence.accumulation.high_volume_at_support"
            ))

        if current_wick_low > 0.3:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_ACCUMULATION,
                bar_time=current_bar.t,
                metrics={"wick_ratio_low": current_wick_low},
                note="evidence.accumulation.demand_wick"
            ))

    elif dominant_behavior == BEHAVIOR_SHAKEOUT:
        # 洗盘证据
        support_zones = zones.get("support", [])
        if support_zones:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_SHAKEOUT,
                bar_time=current_bar.t,
                metrics={"low": current_bar.l, "zone_low": support_zones[0].low},
                note="evidence.shakeout.sweep_and_reclaim"
            ))

        if current_wick_low > 0.4:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_SHAKEOUT,
                bar_time=current_bar.t,
                metrics={"wick_ratio_low": current_wick_low},
                note="evidence.shakeout.long_lower_wick"
            ))

        if current_vol_ratio >= 1.5:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_SHAKEOUT,
                bar_time=current_bar.t,
                metrics={"volume_ratio": current_vol_ratio},
                note="evidence.shakeout.high_volume_sweep"
            ))

    elif dominant_behavior == BEHAVIOR_MARKUP:
        # 上涨证据
        evidence_list.append(Evidence(
            behavior=BEHAVIOR_MARKUP,
            bar_time=current_bar.t,
            metrics={"close": current_price},
            note="evidence.markup.uptrend_continuation"
        ))

        if current_vol_ratio >= 1.2:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_MARKUP,
                bar_time=current_bar.t,
                metrics={"volume_ratio": current_vol_ratio},
                note="evidence.markup.volume_confirmation"
            ))

    elif dominant_behavior == BEHAVIOR_DISTRIBUTION:
        # 派发证据
        resistance_zones = zones.get("resistance", [])
        if resistance_zones and _is_near_zone(current_price, resistance_zones):
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_DISTRIBUTION,
                bar_time=current_bar.t,
                metrics={"price": current_price, "zone_high": resistance_zones[0].high},
                note="evidence.distribution.near_resistance"
            ))

        if current_vol_ratio >= 1.5:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_DISTRIBUTION,
                bar_time=current_bar.t,
                metrics={"volume_ratio": current_vol_ratio},
                note="evidence.distribution.high_volume_at_resistance"
            ))

        if current_wick_up > 0.3:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_DISTRIBUTION,
                bar_time=current_bar.t,
                metrics={"wick_ratio_up": current_wick_up},
                note="evidence.distribution.rejection_wick"
            ))

    elif dominant_behavior == BEHAVIOR_MARKDOWN:
        # 下跌证据
        evidence_list.append(Evidence(
            behavior=BEHAVIOR_MARKDOWN,
            bar_time=current_bar.t,
            metrics={"close": current_price},
            note="evidence.markdown.downtrend_continuation"
        ))

        if current_vol_ratio >= 1.2:
            evidence_list.append(Evidence(
                behavior=BEHAVIOR_MARKDOWN,
                bar_time=current_bar.t,
                metrics={"volume_ratio": current_vol_ratio},
                note="evidence.markdown.volume_confirmation"
            ))

    # 限制证据数量
    return evidence_list[:3]


def infer_behavior(bars: List[Bar],
                   features: Dict[str, np.ndarray],
                   zones: Dict[str, List[Zone]],
                   market_state: MarketState,
                   signals: List[Signal]) -> Behavior:
    """
    主行为推断函数

    参数:
        bars: 完整 K 线列表
        features: 预计算的特征（来自 calculate_features()）
        zones: 支撑/阻力区域
        market_state: 当前趋势分类
        signals: 检测到的突破信号

    返回:
        包含 probabilities, dominant, evidence 的 Behavior 对象

    实现流程:
        1. 计算所有 5 种行为的原始得分
        2. 通过 softmax 转换为概率
        3. 识别主导行为（概率最高）
        4. 生成支持证据
        5. 返回 Behavior 数据类
    """
    # 1. 计算原始得分
    scores = {
        BEHAVIOR_ACCUMULATION: score_accumulation(bars, features, zones),
        BEHAVIOR_SHAKEOUT: score_shakeout(bars, features, zones),
        BEHAVIOR_MARKUP: score_markup(bars, features, market_state, signals),
        BEHAVIOR_DISTRIBUTION: score_distribution(bars, features, zones),
        BEHAVIOR_MARKDOWN: score_markdown(bars, features, market_state, signals),
    }

    # 2. 转换为概率
    probabilities = scores_to_probabilities(scores)

    # 3. 识别主导行为
    dominant = max(probabilities.keys(), key=lambda k: probabilities[k])

    # 4. 生成证据
    evidence = generate_evidence(bars, dominant, features, zones)

    # 5. 返回结果
    return Behavior(
        probabilities=probabilities,
        dominant=dominant,
        evidence=evidence
    )
