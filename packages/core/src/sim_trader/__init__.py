"""
Sim Trader 模块

0DTE 交易计划模块 - 将分析系统的结构化信号转换为可执行的交易计划。

主要组件：
- types: 类型定义 (AnalysisSnapshot, TradePlanRow, TradeReview)
- config: 配置参数
- setups: 4 种 Setup 检测 (R1 Breakout, S1 Breakdown, YC Reclaim, R1 Reject)
- manager: 持仓管理 (HOLD/TRIM/EXIT)
- state_machine: 状态机

使用示例：

    from sim_trader import create_sim_trader, AnalysisSnapshot, PriceData, LevelsData, SignalsData

    # 创建状态机
    trader = create_sim_trader("QQQ")

    # 构建快照
    snapshot = AnalysisSnapshot(
        ts="2026-01-16T09:45:00-05:00",
        ticker="QQQ",
        interval="1m",
        price=PriceData(open=624.0, high=624.5, low=623.8, close=624.3),
        levels=LevelsData(R1=624.5, R2=626.0, S1=622.0, YC=623.0),
        signals=SignalsData(trend_1m="up", rvol_state="ok")
    )

    # 更新状态机
    plan = trader.update(snapshot)

    # 使用计划
    print(f"Status: {plan.status}")
    print(f"Direction: {plan.direction}")
    print(f"Entry: {plan.entry_underlying}")
"""

from .types import (
    # 枚举
    TradeStatus,
    TradeDirection,
    RiskLevel,
    SetupType,
    FailureReason,
    TradeOutcome,

    # 输入类型
    PriceData,
    LevelsData,
    SignalsData,
    AnalysisSnapshot,

    # 输出类型
    TradePlanRow,
    TradeReview,
    SimTradeState,
)

from .config import (
    SimTraderConfig,
    DEFAULT_CONFIG,
    get_buffer,
    get_armed_distance,
    get_watch_distance,
)

from .setups import (
    SetupResult,
    check_r1_breakout,
    check_s1_breakdown,
    check_yc_reclaim,
    check_r1_reject,
    detect_best_setup,
)

from .manager import (
    ManageAdvice,
    check_exit_conditions,
    check_trim_conditions,
    check_hold_conditions,
    manage_position,
)

from .state_machine import (
    SimTradeStateMachine,
    create_sim_trader,
)

__all__ = [
    # 枚举
    "TradeStatus",
    "TradeDirection",
    "RiskLevel",
    "SetupType",
    "FailureReason",
    "TradeOutcome",

    # 输入类型
    "PriceData",
    "LevelsData",
    "SignalsData",
    "AnalysisSnapshot",

    # 输出类型
    "TradePlanRow",
    "TradeReview",
    "SimTradeState",

    # 配置
    "SimTraderConfig",
    "DEFAULT_CONFIG",
    "get_buffer",
    "get_armed_distance",
    "get_watch_distance",

    # Setup 检测
    "SetupResult",
    "check_r1_breakout",
    "check_s1_breakdown",
    "check_yc_reclaim",
    "check_r1_reject",
    "detect_best_setup",

    # 持仓管理
    "ManageAdvice",
    "check_exit_conditions",
    "check_trim_conditions",
    "check_hold_conditions",
    "manage_position",

    # 状态机
    "SimTradeStateMachine",
    "create_sim_trader",
]
