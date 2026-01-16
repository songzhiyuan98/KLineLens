"""
KLineLens Playbook 生成模块

基于当前市场状态生成条件交易计划。
格式: "如果 X 发生，考虑 Y"

重要: 这些是教育/分析场景，不是交易建议。

计划模板:
- 上升趋势: Plan A (回调到支撑), Plan B (突破延续)
- 下降趋势: Plan A (阻力拒绝), Plan B (跌破延续)
- 震荡: Plan A (支撑反弹), Plan B (阻力回落)

EH 集成:
- gap_and_go: 优先顺势计划
- gap_fill_bias: 添加 gap fill 计划
- range_day_setup: 优先区间交易计划
"""

from typing import List, Dict, Optional, TYPE_CHECKING
from .models import PlaybookPlan, Zone, MarketState, Signal

if TYPE_CHECKING:
    from .extended_hours import EHContext


def _calculate_target(entry: float,
                      direction: str,
                      atr: float,
                      multiplier: float = 2.0) -> float:
    """
    根据 ATR 计算目标价格

    参数:
        entry: 入场价格
        direction: "long" 或 "short"
        atr: 当前 ATR 值
        multiplier: ATR 倍数

    返回:
        目标价格
    """
    if direction == "long":
        return round(entry + atr * multiplier, 2)
    else:
        return round(entry - atr * multiplier, 2)


def _calculate_invalidation(entry: float,
                            direction: str,
                            atr: float,
                            multiplier: float = 0.5) -> float:
    """
    根据 ATR 计算失效（止损）价格

    参数:
        entry: 入场价格
        direction: "long" 或 "short"
        atr: 当前 ATR 值
        multiplier: ATR 倍数

    返回:
        失效价格
    """
    if direction == "long":
        return round(entry - atr * multiplier, 2)
    else:
        return round(entry + atr * multiplier, 2)


def _get_nearest_zone_above(price: float, zones: List[Zone]) -> Zone:
    """获取价格上方最近的区域"""
    above_zones = [z for z in zones if z.low > price]
    if not above_zones:
        return None
    return min(above_zones, key=lambda z: z.low)


def _get_nearest_zone_below(price: float, zones: List[Zone]) -> Zone:
    """获取价格下方最近的区域"""
    below_zones = [z for z in zones if z.high < price]
    if not below_zones:
        return None
    return max(below_zones, key=lambda z: z.high)


def generate_playbook(market_state: MarketState,
                      zones: Dict[str, List[Zone]],
                      signals: List[Signal],
                      atr: float,
                      current_price: float,
                      eh_context: Optional["EHContext"] = None) -> List[PlaybookPlan]:
    """
    生成条件交易计划（含 EH 上下文影响）

    参数:
        market_state: 当前趋势分类
        zones: 支撑/阻力区域
        signals: 当前突破信号
        atr: 当前 ATR 值
        current_price: 当前收盘价
        eh_context: Extended Hours 上下文（可选）

    返回:
        PlaybookPlan 对象列表（通常 2-4 个计划）

    计划生成逻辑:

    1. 上升趋势:
       - Plan A: "回调到支撑"
       - Plan B: "突破延续"

    2. 下降趋势:
       - Plan A: "反弹拒绝"
       - Plan B: "跌破延续"

    3. 震荡:
       - Plan A: "区间支撑反弹"
       - Plan B: "区间阻力回落"

    EH 上下文影响:
    - gap_and_go: 增加顺势计划优先级
    - gap_fill_bias: 添加 gap fill 回归 YC 计划
    - range_day_setup: 增强区间策略
    """
    plans = []

    support_zones = zones.get("support", [])
    resistance_zones = zones.get("resistance", [])

    # 如果没有区域或 ATR，返回空计划
    if atr <= 0:
        return plans

    regime = market_state.regime

    if regime == "uptrend":
        # 上升趋势计划

        # Plan A: 回调到支撑
        nearest_support = _get_nearest_zone_below(current_price, support_zones)
        if nearest_support:
            entry_level = nearest_support.high
            target = _calculate_target(entry_level, "long", atr, 2.0)
            invalidation = _calculate_invalidation(entry_level, "long", atr, 0.5)

            # 如果有上方阻力，用它作为目标
            nearest_resistance = _get_nearest_zone_above(current_price, resistance_zones)
            if nearest_resistance:
                target = nearest_resistance.low

            plans.append(PlaybookPlan(
                name="Plan A",
                condition="condition.pullback_to_support",
                level=round(entry_level, 2),
                target=round(target, 2),
                invalidation=round(invalidation, 2),
                risk="risk.trend_continuation"
            ))

        # Plan B: 突破延续
        nearest_resistance = _get_nearest_zone_above(current_price, resistance_zones)
        if nearest_resistance:
            entry_level = nearest_resistance.high
            target = _calculate_target(entry_level, "long", atr, 1.5)
            invalidation = nearest_resistance.low

            plans.append(PlaybookPlan(
                name="Plan B",
                condition="condition.breakout_continuation",
                level=round(entry_level, 2),
                target=round(target, 2),
                invalidation=round(invalidation, 2),
                risk="risk.false_breakout"
            ))

    elif regime == "downtrend":
        # 下降趋势计划

        # Plan A: 反弹拒绝
        nearest_resistance = _get_nearest_zone_above(current_price, resistance_zones)
        if nearest_resistance:
            entry_level = nearest_resistance.low
            target = _calculate_target(entry_level, "short", atr, 2.0)
            invalidation = _calculate_invalidation(entry_level, "short", atr, 0.5)

            # 如果有下方支撑，用它作为目标
            nearest_support = _get_nearest_zone_below(current_price, support_zones)
            if nearest_support:
                target = nearest_support.high

            plans.append(PlaybookPlan(
                name="Plan A",
                condition="condition.resistance_rejection",
                level=round(entry_level, 2),
                target=round(target, 2),
                invalidation=round(invalidation, 2),
                risk="risk.reversal"
            ))

        # Plan B: 跌破延续
        nearest_support = _get_nearest_zone_below(current_price, support_zones)
        if nearest_support:
            entry_level = nearest_support.low
            target = _calculate_target(entry_level, "short", atr, 1.5)
            invalidation = nearest_support.high

            plans.append(PlaybookPlan(
                name="Plan B",
                condition="condition.breakdown_continuation",
                level=round(entry_level, 2),
                target=round(target, 2),
                invalidation=round(invalidation, 2),
                risk="risk.false_breakdown"
            ))

    else:  # range
        # 震荡计划

        # Plan A: 区间支撑反弹
        nearest_support = _get_nearest_zone_below(current_price, support_zones)
        nearest_resistance = _get_nearest_zone_above(current_price, resistance_zones)

        if nearest_support:
            entry_level = nearest_support.high

            # 目标是阻力区域
            if nearest_resistance:
                target = nearest_resistance.low
            else:
                target = _calculate_target(entry_level, "long", atr, 2.0)

            invalidation = nearest_support.low - atr * 0.5

            plans.append(PlaybookPlan(
                name="Plan A",
                condition="condition.support_bounce",
                level=round(entry_level, 2),
                target=round(target, 2),
                invalidation=round(invalidation, 2),
                risk="risk.range_break"
            ))

        # Plan B: 区间阻力回落
        if nearest_resistance:
            entry_level = nearest_resistance.low

            # 目标是支撑区域
            if nearest_support:
                target = nearest_support.high
            else:
                target = _calculate_target(entry_level, "short", atr, 2.0)

            invalidation = nearest_resistance.high + atr * 0.5

            plans.append(PlaybookPlan(
                name="Plan B",
                condition="condition.resistance_fade",
                level=round(entry_level, 2),
                target=round(target, 2),
                invalidation=round(invalidation, 2),
                risk="risk.range_break"
            ))

    # 添加高波动性风险提示（如果 ATR 相对较大）
    # 这是一个简化的实现，实际应该比较历史 ATR

    # ============ EH 上下文影响 ============
    if eh_context is not None:
        premarket_regime = eh_context.premarket_regime
        gap = eh_context.levels.gap
        yc = eh_context.levels.yc

        # Gap Fill Bias: 添加回归 YC 的计划
        if premarket_regime == "gap_fill_bias" and abs(gap) > atr * 0.5:
            if gap > 0:
                # 正缺口，价格可能回落到 YC
                plans.append(PlaybookPlan(
                    name="Plan EH",
                    condition="condition.gap_fill_short",
                    level=round(current_price, 2),
                    target=round(yc, 2),
                    invalidation=round(current_price + atr * 0.5, 2),
                    risk="risk.gap_continuation"
                ))
            else:
                # 负缺口，价格可能反弹到 YC
                plans.append(PlaybookPlan(
                    name="Plan EH",
                    condition="condition.gap_fill_long",
                    level=round(current_price, 2),
                    target=round(yc, 2),
                    invalidation=round(current_price - atr * 0.5, 2),
                    risk="risk.gap_continuation"
                ))

        # Gap & Go: 强化顺势计划
        elif premarket_regime == "gap_and_go":
            # 将现有的 Plan B（突破延续）提升优先级
            for plan in plans:
                if "breakout" in plan.condition or "breakdown" in plan.condition:
                    plan.name = "Plan A (EH)"  # 提升优先级

        # Range Day Setup: 确保区间计划存在
        elif premarket_regime == "range_day_setup":
            # 区间日优先观望，现有计划已足够
            pass

    return plans
