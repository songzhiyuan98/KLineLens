"""
持仓管理模块

处理 HOLD/TRIM/EXIT 状态的判断逻辑。
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from .types import (
    AnalysisSnapshot, TradePlanRow, TradeStatus, TradeDirection,
    SetupType, RiskLevel
)
from .config import SimTraderConfig, DEFAULT_CONFIG, get_buffer


@dataclass
class ManageAdvice:
    """持仓管理建议"""
    action: TradeStatus           # HOLD / TRIM / EXIT
    reasons: List[str]            # 原因列表
    urgency: str = "normal"       # normal / urgent


def check_exit_conditions(
    snapshot: AnalysisSnapshot,
    plan: TradePlanRow,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> Optional[ManageAdvice]:
    """
    检查硬止损条件（EXIT）

    任一条件满足立即建议 EXIT：
    1. trend 反转 + 关键位失守
    2. behavior 与方向冲突
    3. invalidation 被触发

    Args:
        snapshot: 当前分析快照
        plan: 当前交易计划
        config: 配置

    Returns:
        ManageAdvice 或 None
    """
    reasons = []
    price = snapshot.price.close

    # 条件 1: 检查 invalidation
    if plan.invalidation:
        # 解析 invalidation 价格（假设格式如 "< 624.00"）
        inv_price = plan.entry_price  # 默认用入场价
        if plan.setup_type in [SetupType.R1_BREAKOUT, SetupType.YC_RECLAIM]:
            # CALL 单，跌破 invalidation 出场
            key_level = _extract_key_level(plan)
            if key_level and price < key_level - get_buffer(price, config):
                reasons.append(f"Price below key level {key_level:.2f}")
        elif plan.setup_type in [SetupType.S1_BREAKDOWN, SetupType.R1_REJECT]:
            # PUT 单，涨破 invalidation 出场
            key_level = _extract_key_level(plan)
            if key_level and price > key_level + get_buffer(price, config):
                reasons.append(f"Price above key level {key_level:.2f}")

    # 条件 2: 趋势反转
    if plan.direction == TradeDirection.CALL:
        if snapshot.signals.trend_1m == "down":
            reasons.append("Trend 1m reversed to down")
    elif plan.direction == TradeDirection.PUT:
        if snapshot.signals.trend_1m == "up":
            reasons.append("Trend 1m reversed to up")

    # 条件 3: 行为冲突
    if plan.direction == TradeDirection.CALL:
        if snapshot.signals.behavior in ["distribution", "wash"]:
            reasons.append(f"Behavior turned {snapshot.signals.behavior}")
    elif plan.direction == TradeDirection.PUT:
        if snapshot.signals.behavior in ["accumulation", "rally"]:
            reasons.append(f"Behavior turned {snapshot.signals.behavior}")

    if reasons:
        return ManageAdvice(
            action=TradeStatus.EXIT,
            reasons=reasons,
            urgency="urgent"
        )

    return None


def check_trim_conditions(
    snapshot: AnalysisSnapshot,
    plan: TradePlanRow,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> Optional[ManageAdvice]:
    """
    检查软止损条件（TRIM）

    任一条件满足建议 TRIM：
    1. 时间止损：入场后 N 分钟无进展
    2. 多次冲击目标失败
    3. 动能衰减

    Args:
        snapshot: 当前分析快照
        plan: 当前交易计划
        config: 配置

    Returns:
        ManageAdvice 或 None
    """
    reasons = []

    # 条件 1: 时间止损
    if plan.bars_since_entry >= config.time_stop_minutes:
        # 检查是否有进展
        if plan.entry_price:
            price = snapshot.price.close
            if plan.direction == TradeDirection.CALL:
                progress = (price - plan.entry_price) / plan.entry_price * 100
                if progress < 0.1:  # 不到 0.1% 进展
                    reasons.append(f"Time stop: {plan.bars_since_entry} bars, no progress")
            elif plan.direction == TradeDirection.PUT:
                progress = (plan.entry_price - price) / plan.entry_price * 100
                if progress < 0.1:
                    reasons.append(f"Time stop: {plan.bars_since_entry} bars, no progress")

    # 条件 2: 多次冲击目标失败
    if plan.target_attempts >= config.max_target_attempts:
        reasons.append(f"Target tested {plan.target_attempts}x without breaking")

    # 条件 3: 动能衰减
    if snapshot.signals.rvol_state == "low" and snapshot.signals.behavior == "chop":
        reasons.append("Momentum fading: low RVOL + chop")

    if reasons:
        return ManageAdvice(
            action=TradeStatus.TRIM,
            reasons=reasons,
            urgency="normal"
        )

    return None


def check_hold_conditions(
    snapshot: AnalysisSnapshot,
    plan: TradePlanRow,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> ManageAdvice:
    """
    检查继续持有条件（HOLD）

    所有条件满足时继续 HOLD：
    1. 结构未破
    2. 仍朝目标推进
    3. breakout_quality 仍有效

    Args:
        snapshot: 当前分析快照
        plan: 当前交易计划
        config: 配置

    Returns:
        ManageAdvice
    """
    reasons = []
    price = snapshot.price.close

    # 检查结构
    if plan.direction == TradeDirection.CALL:
        if snapshot.signals.trend_1m in ["up", "neutral"]:
            reasons.append(f"Structure intact: trend {snapshot.signals.trend_1m}")
    elif plan.direction == TradeDirection.PUT:
        if snapshot.signals.trend_1m in ["down", "neutral"]:
            reasons.append(f"Structure intact: trend {snapshot.signals.trend_1m}")

    # 检查进展
    if plan.entry_price:
        if plan.direction == TradeDirection.CALL:
            progress = (price - plan.entry_price) / plan.entry_price * 100
            if progress > 0:
                reasons.append(f"Progressing toward target: +{progress:.2f}%")
        elif plan.direction == TradeDirection.PUT:
            progress = (plan.entry_price - price) / plan.entry_price * 100
            if progress > 0:
                reasons.append(f"Progressing toward target: +{progress:.2f}%")

    # 检查 breakout quality
    if snapshot.signals.breakout_quality == "pass":
        reasons.append("Breakout quality: pass")

    if not reasons:
        reasons.append("No adverse conditions detected")

    return ManageAdvice(
        action=TradeStatus.HOLD,
        reasons=reasons,
        urgency="normal"
    )


def manage_position(
    snapshot: AnalysisSnapshot,
    plan: TradePlanRow,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> ManageAdvice:
    """
    综合持仓管理

    按优先级检查：EXIT > TRIM > HOLD

    Args:
        snapshot: 当前分析快照
        plan: 当前交易计划
        config: 配置

    Returns:
        ManageAdvice
    """
    # 1. 检查 EXIT 条件
    exit_advice = check_exit_conditions(snapshot, plan, config)
    if exit_advice:
        return exit_advice

    # 2. 检查 TRIM 条件
    trim_advice = check_trim_conditions(snapshot, plan, config)
    if trim_advice:
        return trim_advice

    # 3. 默认 HOLD
    return check_hold_conditions(snapshot, plan, config)


def update_target_attempts(
    snapshot: AnalysisSnapshot,
    plan: TradePlanRow
) -> int:
    """
    更新目标位测试次数

    如果价格触及目标位但未突破，增加计数。

    Args:
        snapshot: 当前分析快照
        plan: 当前交易计划

    Returns:
        更新后的测试次数
    """
    if not plan.target_underlying:
        return plan.target_attempts

    # 尝试解析目标价格
    target_price = _extract_target_price(plan)
    if not target_price:
        return plan.target_attempts

    high = snapshot.price.high
    low = snapshot.price.low
    close = snapshot.price.close

    if plan.direction == TradeDirection.CALL:
        # CALL 单目标在上方
        if high >= target_price * 0.999 and close < target_price:
            return plan.target_attempts + 1
    elif plan.direction == TradeDirection.PUT:
        # PUT 单目标在下方
        if low <= target_price * 1.001 and close > target_price:
            return plan.target_attempts + 1

    return plan.target_attempts


def _extract_key_level(plan: TradePlanRow) -> Optional[float]:
    """从 plan 中提取关键价位"""
    # 这个实现比较简单，实际可能需要更复杂的解析
    if plan.entry_underlying:
        # 尝试从 entry_underlying 提取数字
        import re
        match = re.search(r'[\d.]+', plan.entry_underlying)
        if match:
            return float(match.group())
    return plan.entry_price


def _extract_target_price(plan: TradePlanRow) -> Optional[float]:
    """从 plan 中提取目标价格"""
    if plan.target_underlying:
        import re
        match = re.search(r'[\d.]+', plan.target_underlying)
        if match:
            return float(match.group())
    return None
