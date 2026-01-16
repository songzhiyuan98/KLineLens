"""
Sim Trader API 服务

提供 0DTE 交易计划的 API 层封装。
负责：
1. 从分析系统获取数据
2. 转换为 AnalysisSnapshot
3. 调用 SimTradeStateMachine
4. 返回 TradePlanRow
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz
import sys
import os


def _import_sim_trader():
    """导入 sim_trader 模块，支持 Docker 和本地环境"""
    # Docker 环境: /app/packages/core
    docker_core_path = '/app/packages/core'
    # 本地环境: packages/core
    local_core_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..', '..', '..', 'packages', 'core'
    ))

    # 检测运行环境
    if os.path.exists(docker_core_path):
        core_path = docker_core_path
    else:
        core_path = local_core_path

    # 将 core 路径添加到 sys.path
    if core_path not in sys.path:
        sys.path.insert(0, core_path)

    # 保存并临时移除 API 的 src 模块
    api_src = sys.modules.get('src')
    api_src_submodules = {k: v for k, v in sys.modules.items() if k.startswith('src.')}

    for k in list(api_src_submodules.keys()):
        del sys.modules[k]
    if api_src:
        del sys.modules['src']

    try:
        from src.sim_trader import (
            create_sim_trader,
            SimTradeStateMachine,
            SimTraderConfig,
            AnalysisSnapshot,
            PriceData,
            LevelsData,
            SignalsData,
            TradePlanRow,
            TradeStatus,
            TradeDirection,
            RiskLevel,
        )
    finally:
        # 恢复 API 的 src 模块
        if api_src:
            sys.modules['src'] = api_src
        sys.modules.update(api_src_submodules)

    return (
        create_sim_trader,
        SimTradeStateMachine,
        SimTraderConfig,
        AnalysisSnapshot,
        PriceData,
        LevelsData,
        SignalsData,
        TradePlanRow,
        TradeStatus,
        TradeDirection,
        RiskLevel,
    )


# 导入模块
(
    create_sim_trader,
    SimTradeStateMachine,
    SimTraderConfig,
    AnalysisSnapshot,
    PriceData,
    LevelsData,
    SignalsData,
    TradePlanRow,
    TradeStatus,
    TradeDirection,
    RiskLevel,
) = _import_sim_trader()

ET = pytz.timezone("America/New_York")

# 全局状态机缓存（每个 ticker 一个）
_traders: Dict[str, SimTradeStateMachine] = {}


def get_trader(ticker: str, config: SimTraderConfig = None) -> SimTradeStateMachine:
    """
    获取或创建 ticker 的状态机

    Args:
        ticker: 标的代码
        config: 配置

    Returns:
        SimTradeStateMachine 实例
    """
    if ticker not in _traders:
        _traders[ticker] = create_sim_trader(ticker, config)
    return _traders[ticker]


def reset_trader(ticker: str):
    """重置 ticker 的状态机（每日重置）"""
    if ticker in _traders:
        _traders[ticker].reset_daily()


def convert_analysis_to_snapshot(
    ticker: str,
    analysis_report: Dict[str, Any],
    bars: List[Dict[str, Any]],
    eh_context: Optional[Dict[str, Any]] = None,
    timeframe: str = "1m"
) -> AnalysisSnapshot:
    """
    将分析报告转换为 AnalysisSnapshot

    Args:
        ticker: 标的代码
        analysis_report: 分析报告
        bars: K 线数据
        eh_context: EH 上下文
        timeframe: 时间周期

    Returns:
        AnalysisSnapshot
    """
    # 获取最新 bar
    if not bars:
        raise ValueError("No bars data")

    latest_bar = bars[-1]

    # 构建价格数据
    price = PriceData(
        open=float(latest_bar.get("open", 0)),
        high=float(latest_bar.get("high", 0)),
        low=float(latest_bar.get("low", 0)),
        close=float(latest_bar.get("close", 0))
    )

    # 构建关键位数据
    levels = LevelsData()

    # 从 zones 提取 R1/R2/S1/S2
    zones = analysis_report.get("zones", [])
    current_price = price.close

    # zones 可能是 Zone 对象列表或字典列表
    try:
        resistances = []
        supports = []
        for z in zones:
            # 尝试获取 level
            if isinstance(z, dict):
                level = z.get("level", 0)
            elif hasattr(z, "level"):
                level = z.level
            else:
                continue

            if level > current_price:
                resistances.append({"level": level})
            else:
                supports.append({"level": level})

        resistances = sorted(resistances, key=lambda x: x["level"])
        supports = sorted(supports, key=lambda x: x["level"], reverse=True)

        if resistances:
            levels.R1 = resistances[0]["level"]
            if len(resistances) > 1:
                levels.R2 = resistances[1]["level"]

        if supports:
            levels.S1 = supports[0]["level"]
            if len(supports) > 1:
                levels.S2 = supports[1]["level"]
    except Exception as e:
        # zones 解析失败，忽略
        pass

    # 从 EH 上下文提取关键位
    if eh_context:
        try:
            # eh_context 可能是 dict 或 EHContext 对象
            if isinstance(eh_context, dict):
                eh_levels = eh_context.get("levels", {})
                if isinstance(eh_levels, dict):
                    levels.YC = eh_levels.get("yc")
                    levels.PMH = eh_levels.get("pmh")
                    levels.PML = eh_levels.get("pml")
                    levels.YH = eh_levels.get("yh")
                    levels.YL = eh_levels.get("yl")
            elif hasattr(eh_context, "levels"):
                eh_levels = eh_context.levels
                if hasattr(eh_levels, "yc"):
                    levels.YC = eh_levels.yc
                    levels.PMH = eh_levels.pmh
                    levels.PML = eh_levels.pml
                    levels.YH = eh_levels.yh
                    levels.YL = eh_levels.yl
        except Exception:
            pass

    # 计算 HOD/LOD
    if bars:
        levels.HOD = max(b.get("high", 0) for b in bars)
        levels.LOD = min(b.get("low", float("inf")) for b in bars)

    # 构建信号数据
    trend = analysis_report.get("trend", {})
    breakout = analysis_report.get("breakout", {})
    behavior = analysis_report.get("behavior", {})
    features = analysis_report.get("features", {})

    # 映射趋势
    regime = trend.get("regime", "range")
    if regime == "uptrend":
        trend_1m = "up"
    elif regime == "downtrend":
        trend_1m = "down"
    else:
        trend_1m = "neutral"

    # 映射 breakout quality
    breakout_state = breakout.get("state", "idle")
    if breakout_state == "confirmed":
        breakout_quality = "pass"
    elif breakout_state == "fakeout":
        breakout_quality = "fail"
    else:
        breakout_quality = "unknown"

    # 映射行为
    dominant_behavior = behavior.get("dominant", "chop")
    behavior_map = {
        "accumulation": "accumulation",
        "distribution": "distribution",
        "shakeout": "wash",
        "markup": "rally",
        "markdown": "wash",
    }
    mapped_behavior = behavior_map.get(dominant_behavior, "chop")

    # 映射 RVOL
    rvol = features.get("rvol", 1.0)
    if rvol < 0.8:
        rvol_state = "low"
    elif rvol > 1.5:
        rvol_state = "high"
    else:
        rvol_state = "ok"

    # 检查开盘保护
    opening_protection = False
    try:
        ts = latest_bar.get("time", "")
        if ts:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = ET.localize(dt)
            else:
                dt = dt.astimezone(ET)

            # 09:30-09:40 ET
            if dt.hour == 9 and 30 <= dt.minute < 40:
                opening_protection = True
    except Exception:
        pass

    signals = SignalsData(
        trend_1m=trend_1m,
        trend_5m=trend_1m if timeframe == "5m" else None,
        behavior=mapped_behavior,
        breakout_quality=breakout_quality,
        rvol_state=rvol_state,
        opening_protection=opening_protection
    )

    # 构建时间戳
    ts = latest_bar.get("time", "")
    if isinstance(ts, int):
        ts = datetime.fromtimestamp(ts, tz=ET).isoformat()

    # 获取最近收盘价
    recent_closes = [b.get("close", 0) for b in bars[-10:]]
    recent_highs = [b.get("high", 0) for b in bars[-10:]]
    recent_lows = [b.get("low", 0) for b in bars[-10:]]

    return AnalysisSnapshot(
        ts=str(ts),
        ticker=ticker,
        interval=timeframe if timeframe in ["1m", "5m"] else "1m",
        price=price,
        levels=levels,
        signals=signals,
        confidence=trend.get("confidence", 50),
        recent_closes=recent_closes,
        recent_highs=recent_highs,
        recent_lows=recent_lows
    )


def get_trade_plan(
    ticker: str,
    analysis_report: Dict[str, Any],
    bars: List[Dict[str, Any]],
    eh_context: Optional[Dict[str, Any]] = None,
    timeframe: str = "1m"
) -> Dict[str, Any]:
    """
    获取交易计划

    Args:
        ticker: 标的代码
        analysis_report: 分析报告
        bars: K 线数据
        eh_context: EH 上下文
        timeframe: 时间周期

    Returns:
        交易计划字典
    """
    # 转换为 snapshot
    snapshot = convert_analysis_to_snapshot(
        ticker, analysis_report, bars, eh_context, timeframe
    )

    # 获取状态机
    trader = get_trader(ticker)

    # 更新并获取计划
    plan = trader.update(snapshot)

    # 获取历史
    state = trader.get_state()
    history = [
        {
            "ts": p.ts[-8:-3] if len(p.ts) > 8 else p.ts,  # 提取 HH:MM
            "status": p.status.value,
            "direction": p.direction.value
        }
        for p in state.plan_history[-10:]  # 最近 10 条
    ]

    # 转换为字典
    return {
        "ticker": ticker,
        "ts": plan.ts,
        "plan": {
            "status": plan.status.value,
            "direction": plan.direction.value,
            "entryZone": plan.entry_zone,
            "entryUnderlying": plan.entry_underlying,
            "targetUnderlying": plan.target_underlying,
            "invalidation": plan.invalidation,
            "risk": plan.risk.value,
            "watchlistHint": plan.watchlist_hint,
            "reasons": plan.reasons,
            "barsSinceEntry": plan.bars_since_entry,
            "targetAttempts": plan.target_attempts,
        },
        "history": history,
        "stats": {
            "tradesToday": state.trades_today,
            "maxTradesPerDay": state.max_trades_per_day,
        }
    }


def plan_to_dict(plan: TradePlanRow) -> Dict[str, Any]:
    """将 TradePlanRow 转换为字典"""
    return {
        "ts": plan.ts,
        "status": plan.status.value,
        "direction": plan.direction.value,
        "entryZone": plan.entry_zone,
        "entryUnderlying": plan.entry_underlying,
        "targetUnderlying": plan.target_underlying,
        "invalidation": plan.invalidation,
        "risk": plan.risk.value,
        "watchlistHint": plan.watchlist_hint,
        "reasons": plan.reasons,
    }
