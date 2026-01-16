"""
Sim Trader 类型定义

定义 0DTE 交易计划模块的所有数据类型：
- AnalysisSnapshot: 从分析系统接收的输入
- TradePlanRow: 输出给 UI 的交易计划
- TradeReview: 复盘记录
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from enum import Enum


# ============ 枚举类型 ============

class TradeStatus(str, Enum):
    """交易状态"""
    WAIT = "WAIT"      # 无交易机会
    WATCH = "WATCH"    # 出现 setup，但未接近触发
    ARMED = "ARMED"    # 接近触发，发预警
    ENTER = "ENTER"    # 触发条件满足，建议下单
    HOLD = "HOLD"      # 已进入持仓管理
    TRIM = "TRIM"      # 建议减仓
    EXIT = "EXIT"      # 建议清仓


class TradeDirection(str, Enum):
    """交易方向"""
    CALL = "CALL"
    PUT = "PUT"
    NONE = "NONE"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


class SetupType(str, Enum):
    """交易 Setup 类型"""
    R1_BREAKOUT = "R1_BREAKOUT"      # R1 突破做多
    S1_BREAKDOWN = "S1_BREAKDOWN"    # S1 跌破做空
    YC_RECLAIM = "YC_RECLAIM"        # YC 收复做多
    R1_REJECT = "R1_REJECT"          # R1 被拒做空


class FailureReason(str, Enum):
    """失败原因"""
    FAKEOUT = "FAKEOUT"              # 假突破
    LOW_RVOL = "LOW_RVOL"            # 量能不足
    OPENING_NOISE = "OPENING_NOISE"  # 开盘噪音
    BAD_CONFIRMATION = "BAD_CONFIRMATION"  # 确认失败
    TIME_DECAY = "TIME_DECAY"        # 时间衰减
    CHOP = "CHOP"                    # 震荡行情


class TradeOutcome(str, Enum):
    """交易结果"""
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"


# ============ 输入类型 ============

@dataclass
class PriceData:
    """价格数据"""
    open: float
    high: float
    low: float
    close: float


@dataclass
class LevelsData:
    """关键价位数据"""
    R1: Optional[float] = None
    R2: Optional[float] = None
    S1: Optional[float] = None
    S2: Optional[float] = None
    YC: Optional[float] = None      # Yesterday's Close
    HOD: Optional[float] = None     # High of Day
    LOD: Optional[float] = None     # Low of Day
    YH: Optional[float] = None      # Yesterday's High
    YL: Optional[float] = None      # Yesterday's Low
    PMH: Optional[float] = None     # Premarket High
    PML: Optional[float] = None     # Premarket Low


@dataclass
class SignalsData:
    """信号数据"""
    trend_1m: Literal["up", "down", "neutral"]
    trend_5m: Optional[Literal["up", "down", "neutral"]] = None
    behavior: Optional[Literal["accumulation", "distribution", "wash", "rally", "chop"]] = None
    breakout_quality: Optional[Literal["pass", "fail", "unknown"]] = None
    rvol_state: Optional[Literal["low", "ok", "high"]] = None
    opening_protection: bool = False  # 09:30-09:40 ET


@dataclass
class AnalysisSnapshot:
    """
    分析快照 - 从分析系统接收的输入

    这是 Sim Trader 模块的唯一输入，包含所有做出交易决策所需的数据。
    """
    ts: str                    # ISO 时间戳 (ET or UTC)
    ticker: str                # 标的代码 (如 "QQQ")
    interval: Literal["1m", "5m"]

    price: PriceData           # 当前价格数据
    levels: LevelsData         # 关键价位
    signals: SignalsData       # 信号数据

    confidence: Optional[float] = None  # 0-100 置信度

    # 用于状态追踪的历史数据
    recent_closes: List[float] = field(default_factory=list)  # 最近 N 根 K 线收盘价
    recent_highs: List[float] = field(default_factory=list)   # 最近 N 根 K 线最高价
    recent_lows: List[float] = field(default_factory=list)    # 最近 N 根 K 线最低价


# ============ 输出类型 ============

@dataclass
class TradePlanRow:
    """
    交易计划行 - 输出给 UI 的表格数据

    用于显示当前交易状态和建议。
    """
    ts: str                                # 时间戳
    status: TradeStatus                    # 当前状态
    direction: TradeDirection              # 交易方向

    entry_zone: Optional[str] = None       # 入场区域描述 (如 "R1 breakout")
    entry_underlying: Optional[str] = None # 入场价格条件 (如 ">= 624.30 (2 closes)")
    target_underlying: Optional[str] = None # 目标价位 (如 "R2 626.10")
    invalidation: Optional[str] = None     # 失效条件 (如 "close < R1 (2 bars)")

    risk: RiskLevel = RiskLevel.MED        # 风险等级
    watchlist_hint: Optional[str] = None   # 合约提示 (如 "Watch 0DTE ATM +1 CALL")

    reasons: List[str] = field(default_factory=list)  # 2-4 条证据/原因

    # 内部追踪字段
    setup_type: Optional[SetupType] = None  # 当前 setup 类型
    entry_price: Optional[float] = None     # 实际入场价格（ENTER 后记录）
    entry_ts: Optional[str] = None          # 入场时间
    bars_since_entry: int = 0               # 入场后经过的 K 线数
    target_attempts: int = 0                # 目标位测试次数


@dataclass
class TradeReview:
    """
    交易复盘记录

    用于记录每笔交易的结果和分析失败原因。
    """
    date: str                              # 交易日期
    ticker: str                            # 标的代码
    direction: TradeDirection              # 交易方向
    setup: SetupType                       # Setup 类型

    entry_ts: str                          # 入场时间
    entry_price: float                     # 入场价格
    exit_ts: str                           # 出场时间
    exit_price: float                      # 出场价格

    outcome: TradeOutcome                  # 交易结果
    pnl_pct: Optional[float] = None        # 标的涨跌幅（非期权收益）

    notes: List[str] = field(default_factory=list)  # 备注

    signal_correct: bool = False           # 信号是否正确
    execution_correct: bool = False        # 执行是否正确
    failure_reason: Optional[FailureReason] = None  # 失败原因


@dataclass
class SimTradeState:
    """
    Sim Trader 内部状态

    追踪当前交易计划的完整状态。
    """
    ticker: str
    current_plan: TradePlanRow

    # 今日交易统计
    trades_today: int = 0
    max_trades_per_day: int = 1

    # 历史记录
    plan_history: List[TradePlanRow] = field(default_factory=list)
    reviews: List[TradeReview] = field(default_factory=list)

    # 确认计数器
    confirm_count: int = 0      # 当前确认的 K 线数
    invalidate_count: int = 0   # 当前失效确认的 K 线数
