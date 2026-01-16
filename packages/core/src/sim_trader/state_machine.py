"""
交易状态机

管理 0DTE 交易计划的完整生命周期：
WAIT → WATCH → ARMED → ENTER → HOLD → TRIM/EXIT
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import pytz

from .types import (
    AnalysisSnapshot, TradePlanRow, TradeReview, SimTradeState,
    TradeStatus, TradeDirection, SetupType, RiskLevel,
    TradeOutcome, FailureReason
)
from .config import SimTraderConfig, DEFAULT_CONFIG
from .setups import detect_best_setup, SetupResult
from .manager import manage_position, update_target_attempts, ManageAdvice


ET = pytz.timezone("America/New_York")


class SimTradeStateMachine:
    """
    交易状态机

    负责：
    1. 接收 AnalysisSnapshot
    2. 检测 Setup
    3. 管理状态转换
    4. 输出 TradePlanRow
    5. 记录复盘数据
    """

    def __init__(
        self,
        ticker: str,
        config: SimTraderConfig = DEFAULT_CONFIG
    ):
        """
        初始化状态机

        Args:
            ticker: 标的代码
            config: 配置
        """
        self.ticker = ticker
        self.config = config

        # 初始化状态
        self._reset_state()

        # 内部追踪
        self._setup_state: Dict[str, Any] = {}
        self._last_snapshot: Optional[AnalysisSnapshot] = None

    def _reset_state(self):
        """重置状态到初始值"""
        self.current_plan = TradePlanRow(
            ts="",
            status=TradeStatus.WAIT,
            direction=TradeDirection.NONE,
            risk=RiskLevel.MED,
            reasons=["No setup detected"]
        )
        self.trades_today = 0
        self.plan_history: List[TradePlanRow] = []
        self.reviews: List[TradeReview] = []

        # Setup 追踪状态
        self._setup_state = {
            "r1_confirm": 0,
            "s1_confirm": 0,
            "yc_confirm": 0,
            "r1_reject_confirm": 0,
            "was_below_yc": False,
            "touched_r1": False,
        }

    def update(self, snapshot: AnalysisSnapshot) -> TradePlanRow:
        """
        处理新的分析快照

        这是状态机的主入口，每根 K 线调用一次。

        Args:
            snapshot: 分析快照

        Returns:
            更新后的 TradePlanRow
        """
        self._last_snapshot = snapshot

        # 检查是否在交易时间
        if not self._is_trading_time(snapshot.ts):
            return self._create_wait_plan(snapshot.ts, ["Outside trading hours"])

        # 检查是否达到每日交易上限
        if self.trades_today >= self.config.max_trades_per_day:
            if self.current_plan.status not in [TradeStatus.HOLD, TradeStatus.TRIM]:
                return self._create_wait_plan(
                    snapshot.ts,
                    [f"Daily trade limit reached ({self.trades_today}/{self.config.max_trades_per_day})"]
                )

        # 根据当前状态处理
        current_status = self.current_plan.status

        if current_status == TradeStatus.WAIT:
            return self._handle_wait(snapshot)

        elif current_status == TradeStatus.WATCH:
            return self._handle_watch(snapshot)

        elif current_status == TradeStatus.ARMED:
            return self._handle_armed(snapshot)

        elif current_status == TradeStatus.ENTER:
            return self._handle_enter(snapshot)

        elif current_status in [TradeStatus.HOLD, TradeStatus.TRIM]:
            return self._handle_position(snapshot)

        elif current_status == TradeStatus.EXIT:
            return self._handle_exit(snapshot)

        return self.current_plan

    def _handle_wait(self, snapshot: AnalysisSnapshot) -> TradePlanRow:
        """处理 WAIT 状态"""
        # 检测 setup
        result = detect_best_setup(snapshot, self._setup_state, self.config)
        self._update_setup_state(snapshot, result)

        if result.detected:
            self.current_plan = self._create_plan_from_setup(snapshot.ts, result)
            self._add_to_history()
        else:
            self.current_plan = self._create_wait_plan(snapshot.ts, result.reasons)

        return self.current_plan

    def _handle_watch(self, snapshot: AnalysisSnapshot) -> TradePlanRow:
        """处理 WATCH 状态"""
        result = detect_best_setup(snapshot, self._setup_state, self.config)
        self._update_setup_state(snapshot, result)

        if not result.detected:
            # Setup 消失，回到 WAIT
            self.current_plan = self._create_wait_plan(snapshot.ts, ["Setup invalidated"])
            self._add_to_history()
        elif result.status in [TradeStatus.ARMED, TradeStatus.ENTER]:
            # 升级状态
            self.current_plan = self._create_plan_from_setup(snapshot.ts, result)
            self._add_to_history()
        else:
            # 保持 WATCH
            self.current_plan = self._create_plan_from_setup(snapshot.ts, result)

        return self.current_plan

    def _handle_armed(self, snapshot: AnalysisSnapshot) -> TradePlanRow:
        """处理 ARMED 状态"""
        result = detect_best_setup(snapshot, self._setup_state, self.config)
        self._update_setup_state(snapshot, result)

        if not result.detected:
            # Setup 消失，回到 WAIT
            self.current_plan = self._create_wait_plan(snapshot.ts, ["Setup invalidated"])
            self._add_to_history()
        elif result.status == TradeStatus.ENTER:
            # 触发 ENTER
            self.current_plan = self._create_plan_from_setup(snapshot.ts, result)
            self.current_plan.entry_price = snapshot.price.close
            self.current_plan.entry_ts = snapshot.ts
            self._add_to_history()
        elif result.status == TradeStatus.WATCH:
            # 降级到 WATCH
            self.current_plan = self._create_plan_from_setup(snapshot.ts, result)
            self._add_to_history()
        else:
            # 保持 ARMED
            self.current_plan = self._create_plan_from_setup(snapshot.ts, result)

        return self.current_plan

    def _handle_enter(self, snapshot: AnalysisSnapshot) -> TradePlanRow:
        """处理 ENTER 状态 - 自动转入 HOLD"""
        # ENTER 后下一根 bar 自动进入 HOLD
        self.current_plan.status = TradeStatus.HOLD
        self.current_plan.ts = snapshot.ts
        self.current_plan.bars_since_entry = 1
        self.trades_today += 1
        self._add_to_history()

        return self.current_plan

    def _handle_position(self, snapshot: AnalysisSnapshot) -> TradePlanRow:
        """处理 HOLD/TRIM 状态"""
        # 更新 bars_since_entry
        self.current_plan.bars_since_entry += 1
        self.current_plan.ts = snapshot.ts

        # 更新目标测试次数
        self.current_plan.target_attempts = update_target_attempts(
            snapshot, self.current_plan
        )

        # 获取持仓管理建议
        advice = manage_position(snapshot, self.current_plan, self.config)

        if advice.action == TradeStatus.EXIT:
            self.current_plan.status = TradeStatus.EXIT
            self.current_plan.reasons = advice.reasons
            self._add_to_history()
            # 记录复盘
            self._create_review(snapshot, "signal_triggered")

        elif advice.action == TradeStatus.TRIM:
            self.current_plan.status = TradeStatus.TRIM
            self.current_plan.reasons = advice.reasons
            # 不立即 EXIT，让用户决定

        else:
            # HOLD
            self.current_plan.status = TradeStatus.HOLD
            self.current_plan.reasons = advice.reasons

        return self.current_plan

    def _handle_exit(self, snapshot: AnalysisSnapshot) -> TradePlanRow:
        """处理 EXIT 状态 - 回到 WAIT"""
        self.current_plan = self._create_wait_plan(
            snapshot.ts,
            ["Trade completed, watching for next setup"]
        )
        self._add_to_history()

        return self.current_plan

    def _create_wait_plan(self, ts: str, reasons: List[str]) -> TradePlanRow:
        """创建 WAIT 状态的计划"""
        return TradePlanRow(
            ts=ts,
            status=TradeStatus.WAIT,
            direction=TradeDirection.NONE,
            risk=RiskLevel.MED,
            reasons=reasons
        )

    def _create_plan_from_setup(self, ts: str, result: SetupResult) -> TradePlanRow:
        """从 SetupResult 创建 TradePlanRow"""
        # 生成 watchlist hint
        watchlist_hint = None
        if result.status in [TradeStatus.ARMED, TradeStatus.ENTER]:
            if result.direction == TradeDirection.CALL:
                watchlist_hint = "Watch 0DTE ATM +1 strike CALL"
            elif result.direction == TradeDirection.PUT:
                watchlist_hint = "Watch 0DTE ATM +1 strike PUT"

        # 格式化 entry/target/invalidation
        entry_underlying = None
        target_underlying = None
        invalidation = None

        if result.key_level:
            if result.direction == TradeDirection.CALL:
                entry_underlying = f">= {result.key_level:.2f} ({self.config.confirm_bars} closes)"
                if result.invalidation_level:
                    invalidation = f"< {result.invalidation_level:.2f} ({self.config.invalidate_bars} bars)"
            elif result.direction == TradeDirection.PUT:
                entry_underlying = f"<= {result.key_level:.2f} ({self.config.confirm_bars} closes)"
                if result.invalidation_level:
                    invalidation = f"> {result.invalidation_level:.2f} ({self.config.invalidate_bars} bars)"

        if result.target_level:
            target_underlying = f"{result.target_name} {result.target_level:.2f}"

        return TradePlanRow(
            ts=ts,
            status=result.status,
            direction=result.direction,
            entry_zone=f"{result.key_level_name} {result.setup_type.value.lower().replace('_', ' ')}" if result.setup_type else None,
            entry_underlying=entry_underlying,
            target_underlying=target_underlying,
            invalidation=invalidation,
            risk=result.risk,
            watchlist_hint=watchlist_hint,
            reasons=result.reasons or [],
            setup_type=result.setup_type,
        )

    def _update_setup_state(self, snapshot: AnalysisSnapshot, result: SetupResult):
        """更新 setup 追踪状态"""
        price = snapshot.price.close
        yc = snapshot.levels.YC
        r1 = snapshot.levels.R1

        # 更新确认计数
        if result.setup_type == SetupType.R1_BREAKOUT:
            self._setup_state["r1_confirm"] = result.confirm_count
        elif result.setup_type == SetupType.S1_BREAKDOWN:
            self._setup_state["s1_confirm"] = result.confirm_count
        elif result.setup_type == SetupType.YC_RECLAIM:
            self._setup_state["yc_confirm"] = result.confirm_count
        elif result.setup_type == SetupType.R1_REJECT:
            self._setup_state["r1_reject_confirm"] = result.confirm_count

        # 更新 YC 状态
        if yc and price < yc:
            self._setup_state["was_below_yc"] = True

        # 更新 R1 触及状态
        if r1 and snapshot.price.high >= r1:
            self._setup_state["touched_r1"] = True

    def _add_to_history(self):
        """添加当前计划到历史"""
        # 创建副本避免引用问题
        import copy
        self.plan_history.append(copy.deepcopy(self.current_plan))

        # 限制历史长度
        if len(self.plan_history) > 100:
            self.plan_history = self.plan_history[-100:]

    def _create_review(self, snapshot: AnalysisSnapshot, reason: str):
        """创建复盘记录"""
        if not self.current_plan.entry_ts or not self.current_plan.entry_price:
            return

        exit_price = snapshot.price.close

        # 计算结果
        if self.current_plan.direction == TradeDirection.CALL:
            pnl_pct = (exit_price - self.current_plan.entry_price) / self.current_plan.entry_price * 100
        else:
            pnl_pct = (self.current_plan.entry_price - exit_price) / self.current_plan.entry_price * 100

        if pnl_pct > 0.1:
            outcome = TradeOutcome.WIN
        elif pnl_pct < -0.1:
            outcome = TradeOutcome.LOSS
        else:
            outcome = TradeOutcome.BREAKEVEN

        review = TradeReview(
            date=snapshot.ts[:10],
            ticker=self.ticker,
            direction=self.current_plan.direction,
            setup=self.current_plan.setup_type or SetupType.R1_BREAKOUT,
            entry_ts=self.current_plan.entry_ts,
            entry_price=self.current_plan.entry_price,
            exit_ts=snapshot.ts,
            exit_price=exit_price,
            outcome=outcome,
            pnl_pct=pnl_pct,
            notes=[reason],
            signal_correct=outcome != TradeOutcome.LOSS,
        )

        self.reviews.append(review)

    def _is_trading_time(self, ts: str) -> bool:
        """检查是否在交易时间内"""
        try:
            # 解析时间戳
            if "T" in ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

            # 转换到 ET
            if dt.tzinfo is None:
                dt = ET.localize(dt)
            else:
                dt = dt.astimezone(ET)

            hour = dt.hour
            minute = dt.minute

            # 检查是否在交易时间
            start_time = self.config.trade_start_hour * 60 + self.config.trade_start_minute
            end_time = self.config.trade_end_hour * 60 + self.config.trade_end_minute
            current_time = hour * 60 + minute

            return start_time <= current_time <= end_time

        except Exception:
            # 解析失败，假设在交易时间
            return True

    def get_state(self) -> SimTradeState:
        """获取完整状态"""
        return SimTradeState(
            ticker=self.ticker,
            current_plan=self.current_plan,
            trades_today=self.trades_today,
            max_trades_per_day=self.config.max_trades_per_day,
            plan_history=self.plan_history,
            reviews=self.reviews,
        )

    def reset_daily(self):
        """每日重置"""
        self._reset_state()


def create_sim_trader(
    ticker: str,
    config: SimTraderConfig = None
) -> SimTradeStateMachine:
    """
    创建 Sim Trader 实例

    Args:
        ticker: 标的代码
        config: 配置（可选）

    Returns:
        SimTradeStateMachine 实例
    """
    return SimTradeStateMachine(
        ticker=ticker,
        config=config or DEFAULT_CONFIG
    )
