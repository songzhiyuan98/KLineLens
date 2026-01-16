"""
Setup 检测模块

检测 4 种核心交易 Setup：
- R1 Breakout (CALL): R1 突破做多
- S1 Breakdown (PUT): S1 跌破做空
- YC Reclaim (CALL): YC 收复做多
- R1 Reject (PUT): R1 被拒做空
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from .types import (
    AnalysisSnapshot, SetupType, TradeDirection, RiskLevel,
    TradeStatus
)
from .config import SimTraderConfig, DEFAULT_CONFIG, get_buffer, get_armed_distance


@dataclass
class SetupResult:
    """Setup 检测结果"""
    detected: bool                      # 是否检测到 setup
    setup_type: Optional[SetupType]     # Setup 类型
    direction: TradeDirection           # 交易方向
    status: TradeStatus                 # 建议状态 (WATCH/ARMED/ENTER)

    key_level: Optional[float] = None   # 关键价位
    key_level_name: str = ""            # 关键价位名称 (如 "R1")
    target_level: Optional[float] = None # 目标价位
    target_name: str = ""               # 目标名称 (如 "R2")
    invalidation_level: Optional[float] = None  # 失效价位

    risk: RiskLevel = RiskLevel.MED     # 风险等级
    reasons: List[str] = None           # 原因列表

    # 确认状态
    confirm_count: int = 0              # 当前确认计数

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


def check_r1_breakout(
    snapshot: AnalysisSnapshot,
    confirm_count: int = 0,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> SetupResult:
    """
    检测 R1 Breakout Setup (CALL)

    触发条件：
    - 价格接近或突破 R1
    - trend_1m == up
    - breakout_quality == pass
    - rvol_state != low (开盘保护期间强制)

    Args:
        snapshot: 分析快照
        confirm_count: 当前确认计数
        config: 配置

    Returns:
        SetupResult
    """
    reasons = []
    risk = RiskLevel.MED

    # 检查 R1 是否存在
    r1 = snapshot.levels.R1
    if r1 is None:
        return SetupResult(
            detected=False,
            setup_type=None,
            direction=TradeDirection.NONE,
            status=TradeStatus.WAIT
        )

    price = snapshot.price.close
    buffer = get_buffer(price, config)
    armed_dist = get_armed_distance(price, config)

    # 计算与 R1 的距离
    distance = r1 - price
    distance_pct = distance / price * 100

    # 基础条件检查
    trend_ok = snapshot.signals.trend_1m == "up"
    breakout_ok = snapshot.signals.breakout_quality in ["pass", None]  # None 表示未知，允许
    rvol_ok = snapshot.signals.rvol_state != "low"

    # 开盘保护期间强制要求高 RVOL
    if snapshot.signals.opening_protection and config.opening_require_high_rvol:
        rvol_ok = snapshot.signals.rvol_state == "high"
        if not rvol_ok:
            reasons.append("Opening protection: requires high RVOL")

    # 收集原因
    if trend_ok:
        reasons.append(f"Trend 1m: up")
    else:
        reasons.append(f"Trend 1m: {snapshot.signals.trend_1m} (not ideal)")
        risk = RiskLevel.HIGH

    if breakout_ok:
        reasons.append(f"Breakout quality: {snapshot.signals.breakout_quality or 'unknown'}")
    else:
        reasons.append(f"Breakout quality: fail")
        risk = RiskLevel.HIGH

    if snapshot.signals.rvol_state:
        reasons.append(f"RVOL: {snapshot.signals.rvol_state}")

    # 判断状态
    if price > r1 + buffer:
        # 已突破 R1，检查确认
        new_confirm = confirm_count + 1 if price > r1 else 0

        if new_confirm >= config.confirm_bars and trend_ok and breakout_ok and rvol_ok:
            status = TradeStatus.ENTER
            reasons.insert(0, f"{new_confirm} consecutive closes above R1 ({r1:.2f})")
        else:
            status = TradeStatus.ARMED
            reasons.insert(0, f"Price above R1 ({r1:.2f}), {new_confirm}/{config.confirm_bars} confirms")

        return SetupResult(
            detected=True,
            setup_type=SetupType.R1_BREAKOUT,
            direction=TradeDirection.CALL,
            status=status,
            key_level=r1,
            key_level_name="R1",
            target_level=snapshot.levels.R2 or snapshot.levels.HOD,
            target_name="R2" if snapshot.levels.R2 else "HOD",
            invalidation_level=r1 - buffer,
            risk=risk,
            reasons=reasons,
            confirm_count=new_confirm
        )

    elif distance <= armed_dist:
        # 接近 R1，ARMED
        reasons.insert(0, f"Price {distance_pct:.2f}% from R1 ({r1:.2f})")
        return SetupResult(
            detected=True,
            setup_type=SetupType.R1_BREAKOUT,
            direction=TradeDirection.CALL,
            status=TradeStatus.ARMED,
            key_level=r1,
            key_level_name="R1",
            target_level=snapshot.levels.R2 or snapshot.levels.HOD,
            target_name="R2" if snapshot.levels.R2 else "HOD",
            invalidation_level=r1 - buffer,
            risk=risk,
            reasons=reasons,
            confirm_count=0
        )

    elif distance <= price * config.watch_distance_pct:
        # 在 WATCH 范围内
        reasons.insert(0, f"Price {distance_pct:.2f}% from R1 ({r1:.2f})")
        return SetupResult(
            detected=True,
            setup_type=SetupType.R1_BREAKOUT,
            direction=TradeDirection.CALL,
            status=TradeStatus.WATCH,
            key_level=r1,
            key_level_name="R1",
            target_level=snapshot.levels.R2 or snapshot.levels.HOD,
            target_name="R2" if snapshot.levels.R2 else "HOD",
            risk=risk,
            reasons=reasons,
            confirm_count=0
        )

    # 距离太远
    return SetupResult(
        detected=False,
        setup_type=None,
        direction=TradeDirection.NONE,
        status=TradeStatus.WAIT
    )


def check_s1_breakdown(
    snapshot: AnalysisSnapshot,
    confirm_count: int = 0,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> SetupResult:
    """
    检测 S1 Breakdown Setup (PUT)

    触发条件（与 R1 Breakout 对称）：
    - 价格接近或跌破 S1
    - trend_1m == down
    - breakout_quality == pass
    - rvol_state != low
    """
    reasons = []
    risk = RiskLevel.MED

    s1 = snapshot.levels.S1
    if s1 is None:
        return SetupResult(
            detected=False,
            setup_type=None,
            direction=TradeDirection.NONE,
            status=TradeStatus.WAIT
        )

    price = snapshot.price.close
    buffer = get_buffer(price, config)
    armed_dist = get_armed_distance(price, config)

    distance = price - s1
    distance_pct = distance / price * 100

    trend_ok = snapshot.signals.trend_1m == "down"
    breakout_ok = snapshot.signals.breakout_quality in ["pass", None]
    rvol_ok = snapshot.signals.rvol_state != "low"

    if snapshot.signals.opening_protection and config.opening_require_high_rvol:
        rvol_ok = snapshot.signals.rvol_state == "high"
        if not rvol_ok:
            reasons.append("Opening protection: requires high RVOL")

    if trend_ok:
        reasons.append(f"Trend 1m: down")
    else:
        reasons.append(f"Trend 1m: {snapshot.signals.trend_1m} (not ideal)")
        risk = RiskLevel.HIGH

    if breakout_ok:
        reasons.append(f"Breakout quality: {snapshot.signals.breakout_quality or 'unknown'}")
    else:
        risk = RiskLevel.HIGH

    if snapshot.signals.rvol_state:
        reasons.append(f"RVOL: {snapshot.signals.rvol_state}")

    if price < s1 - buffer:
        new_confirm = confirm_count + 1 if price < s1 else 0

        if new_confirm >= config.confirm_bars and trend_ok and breakout_ok and rvol_ok:
            status = TradeStatus.ENTER
            reasons.insert(0, f"{new_confirm} consecutive closes below S1 ({s1:.2f})")
        else:
            status = TradeStatus.ARMED
            reasons.insert(0, f"Price below S1 ({s1:.2f}), {new_confirm}/{config.confirm_bars} confirms")

        return SetupResult(
            detected=True,
            setup_type=SetupType.S1_BREAKDOWN,
            direction=TradeDirection.PUT,
            status=status,
            key_level=s1,
            key_level_name="S1",
            target_level=snapshot.levels.S2 or snapshot.levels.LOD,
            target_name="S2" if snapshot.levels.S2 else "LOD",
            invalidation_level=s1 + buffer,
            risk=risk,
            reasons=reasons,
            confirm_count=new_confirm
        )

    elif distance <= armed_dist:
        reasons.insert(0, f"Price {distance_pct:.2f}% from S1 ({s1:.2f})")
        return SetupResult(
            detected=True,
            setup_type=SetupType.S1_BREAKDOWN,
            direction=TradeDirection.PUT,
            status=TradeStatus.ARMED,
            key_level=s1,
            key_level_name="S1",
            target_level=snapshot.levels.S2 or snapshot.levels.LOD,
            target_name="S2" if snapshot.levels.S2 else "LOD",
            invalidation_level=s1 + buffer,
            risk=risk,
            reasons=reasons,
            confirm_count=0
        )

    elif distance <= price * config.watch_distance_pct:
        reasons.insert(0, f"Price {distance_pct:.2f}% from S1 ({s1:.2f})")
        return SetupResult(
            detected=True,
            setup_type=SetupType.S1_BREAKDOWN,
            direction=TradeDirection.PUT,
            status=TradeStatus.WATCH,
            key_level=s1,
            key_level_name="S1",
            target_level=snapshot.levels.S2 or snapshot.levels.LOD,
            target_name="S2" if snapshot.levels.S2 else "LOD",
            risk=risk,
            reasons=reasons,
            confirm_count=0
        )

    return SetupResult(
        detected=False,
        setup_type=None,
        direction=TradeDirection.NONE,
        status=TradeStatus.WAIT
    )


def check_yc_reclaim(
    snapshot: AnalysisSnapshot,
    confirm_count: int = 0,
    was_below_yc: bool = False,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> SetupResult:
    """
    检测 YC Reclaim Setup (CALL)

    触发条件：
    - 价格曾跌破 YC 后重新站上
    - 连续 2 根收盘在 YC 上方
    - trend_1m != down
    """
    reasons = []
    risk = RiskLevel.MED

    yc = snapshot.levels.YC
    if yc is None:
        return SetupResult(
            detected=False,
            setup_type=None,
            direction=TradeDirection.NONE,
            status=TradeStatus.WAIT
        )

    price = snapshot.price.close
    buffer = get_buffer(price, config)
    armed_dist = get_armed_distance(price, config)

    # 检查是否曾跌破 YC
    currently_below = price < yc
    if currently_below:
        # 记录曾在 YC 下方，为后续 reclaim 做准备
        return SetupResult(
            detected=False,
            setup_type=SetupType.YC_RECLAIM,
            direction=TradeDirection.NONE,
            status=TradeStatus.WATCH,
            key_level=yc,
            key_level_name="YC",
            reasons=["Price below YC, watching for reclaim"],
            confirm_count=0
        )

    # 价格在 YC 上方，检查是否是 reclaim
    if not was_below_yc:
        # 从未跌破过 YC，不是 reclaim setup
        return SetupResult(
            detected=False,
            setup_type=None,
            direction=TradeDirection.NONE,
            status=TradeStatus.WAIT
        )

    # 是 reclaim 场景
    trend_ok = snapshot.signals.trend_1m != "down"

    if trend_ok:
        reasons.append(f"Trend 1m: {snapshot.signals.trend_1m}")
    else:
        reasons.append(f"Trend 1m: down (caution)")
        risk = RiskLevel.HIGH

    if snapshot.signals.rvol_state:
        reasons.append(f"RVOL: {snapshot.signals.rvol_state}")

    distance = price - yc
    distance_pct = distance / price * 100

    if price > yc + buffer:
        new_confirm = confirm_count + 1

        if new_confirm >= config.confirm_bars and trend_ok:
            status = TradeStatus.ENTER
            reasons.insert(0, f"YC reclaim confirmed: {new_confirm} closes above YC ({yc:.2f})")
        else:
            status = TradeStatus.ARMED
            reasons.insert(0, f"Reclaiming YC ({yc:.2f}), {new_confirm}/{config.confirm_bars} confirms")

        return SetupResult(
            detected=True,
            setup_type=SetupType.YC_RECLAIM,
            direction=TradeDirection.CALL,
            status=status,
            key_level=yc,
            key_level_name="YC",
            target_level=snapshot.levels.R1 or snapshot.levels.PMH,
            target_name="R1" if snapshot.levels.R1 else "PMH",
            invalidation_level=yc - buffer,
            risk=risk,
            reasons=reasons,
            confirm_count=new_confirm
        )

    else:
        reasons.insert(0, f"Price {distance_pct:.2f}% above YC ({yc:.2f})")
        return SetupResult(
            detected=True,
            setup_type=SetupType.YC_RECLAIM,
            direction=TradeDirection.CALL,
            status=TradeStatus.WATCH,
            key_level=yc,
            key_level_name="YC",
            target_level=snapshot.levels.R1 or snapshot.levels.PMH,
            target_name="R1" if snapshot.levels.R1 else "PMH",
            risk=risk,
            reasons=reasons,
            confirm_count=0
        )


def check_r1_reject(
    snapshot: AnalysisSnapshot,
    confirm_count: int = 0,
    touched_r1: bool = False,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> SetupResult:
    """
    检测 R1 Reject Setup (PUT)

    触发条件：
    - 价格曾触及 R1 但未能突破（wicks）
    - 连续 2 根收盘在 R1 下方（rejection 确认）
    - trend_1m == down 或 behavior == distribution
    """
    reasons = []
    risk = RiskLevel.MED

    r1 = snapshot.levels.R1
    if r1 is None:
        return SetupResult(
            detected=False,
            setup_type=None,
            direction=TradeDirection.NONE,
            status=TradeStatus.WAIT
        )

    price = snapshot.price.close
    high = snapshot.price.high
    buffer = get_buffer(price, config)
    armed_dist = get_armed_distance(price, config)

    # 检查是否触及 R1
    touched_now = high >= r1 - buffer
    if touched_now:
        touched_r1 = True

    if not touched_r1:
        return SetupResult(
            detected=False,
            setup_type=None,
            direction=TradeDirection.NONE,
            status=TradeStatus.WAIT
        )

    # 已触及 R1，检查是否被拒
    rejected = price < r1 - buffer

    trend_ok = snapshot.signals.trend_1m == "down"
    behavior_ok = snapshot.signals.behavior in ["distribution", "wash"]

    if trend_ok:
        reasons.append(f"Trend 1m: down")
    elif behavior_ok:
        reasons.append(f"Behavior: {snapshot.signals.behavior}")
    else:
        reasons.append(f"Trend/behavior not confirming rejection")
        risk = RiskLevel.HIGH

    if snapshot.signals.rvol_state:
        reasons.append(f"RVOL: {snapshot.signals.rvol_state}")

    if rejected:
        new_confirm = confirm_count + 1

        if new_confirm >= config.confirm_bars and (trend_ok or behavior_ok):
            status = TradeStatus.ENTER
            reasons.insert(0, f"R1 rejection confirmed: {new_confirm} closes below R1 ({r1:.2f})")
        else:
            status = TradeStatus.ARMED
            reasons.insert(0, f"R1 ({r1:.2f}) rejection, {new_confirm}/{config.confirm_bars} confirms")

        return SetupResult(
            detected=True,
            setup_type=SetupType.R1_REJECT,
            direction=TradeDirection.PUT,
            status=status,
            key_level=r1,
            key_level_name="R1",
            target_level=snapshot.levels.YC or snapshot.levels.S1,
            target_name="YC" if snapshot.levels.YC else "S1",
            invalidation_level=r1 + buffer,
            risk=risk,
            reasons=reasons,
            confirm_count=new_confirm
        )

    else:
        # 还在 R1 附近，观察
        distance = r1 - price
        distance_pct = distance / price * 100
        reasons.insert(0, f"Touched R1 ({r1:.2f}), watching for rejection")

        return SetupResult(
            detected=True,
            setup_type=SetupType.R1_REJECT,
            direction=TradeDirection.PUT,
            status=TradeStatus.WATCH,
            key_level=r1,
            key_level_name="R1",
            target_level=snapshot.levels.YC or snapshot.levels.S1,
            target_name="YC" if snapshot.levels.YC else "S1",
            risk=risk,
            reasons=reasons,
            confirm_count=0
        )


def detect_best_setup(
    snapshot: AnalysisSnapshot,
    state: dict = None,
    config: SimTraderConfig = DEFAULT_CONFIG
) -> SetupResult:
    """
    检测最佳 Setup

    按优先级检测所有 setup，返回最高优先级的结果。

    优先级（从高到低）：
    1. ENTER 状态的 setup
    2. ARMED 状态的 setup
    3. WATCH 状态的 setup

    Args:
        snapshot: 分析快照
        state: 状态字典，包含历史信息
        config: 配置

    Returns:
        最佳 SetupResult
    """
    if state is None:
        state = {}

    # 获取历史状态
    r1_confirm = state.get("r1_confirm", 0)
    s1_confirm = state.get("s1_confirm", 0)
    yc_confirm = state.get("yc_confirm", 0)
    r1_reject_confirm = state.get("r1_reject_confirm", 0)
    was_below_yc = state.get("was_below_yc", False)
    touched_r1 = state.get("touched_r1", False)

    # 检测所有 setup
    results = [
        check_r1_breakout(snapshot, r1_confirm, config),
        check_s1_breakdown(snapshot, s1_confirm, config),
        check_yc_reclaim(snapshot, yc_confirm, was_below_yc, config),
        check_r1_reject(snapshot, r1_reject_confirm, touched_r1, config),
    ]

    # 按状态优先级排序
    status_priority = {
        TradeStatus.ENTER: 0,
        TradeStatus.ARMED: 1,
        TradeStatus.WATCH: 2,
        TradeStatus.WAIT: 3,
    }

    # 过滤出检测到的 setup
    detected = [r for r in results if r.detected]

    if not detected:
        return SetupResult(
            detected=False,
            setup_type=None,
            direction=TradeDirection.NONE,
            status=TradeStatus.WAIT,
            reasons=["No setup detected"]
        )

    # 按优先级排序
    detected.sort(key=lambda r: (status_priority[r.status], r.risk.value))

    return detected[0]
