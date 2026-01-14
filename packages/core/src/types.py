"""
KLineLens 核心类型定义

定义市场分析引擎使用的所有数据结构。
这些类型用于在各模块之间传递数据。

主要类型:
- Bar: OHLCV K 线数据
- Zone: 支撑/阻力区域
- Signal: 突破/假突破信号
- Evidence: 行为推断证据
- TimelineEvent: 时间线事件
- PlaybookPlan: 条件交易计划
- MarketState: 市场状态（趋势/震荡）
- Behavior: 行为推断结果
- AnalysisReport: 完整分析报告
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class Bar:
    """
    OHLCV K 线数据结构

    存储单根 K 线的完整信息。

    属性:
        t: 时间戳（UTC）
        o: 开盘价 (Open)
        h: 最高价 (High)
        l: 最低价 (Low)
        c: 收盘价 (Close)
        v: 成交量 (Volume)
    """
    t: datetime  # 时间戳（UTC）
    o: float     # 开盘价
    h: float     # 最高价
    l: float     # 最低价
    c: float     # 收盘价
    v: float     # 成交量


@dataclass
class Zone:
    """
    支撑/阻力区域

    代表一个价格区间，该区间在历史上表现出支撑或阻力特性。

    属性:
        low: 区域下边界
        high: 区域上边界
        score: 区域强度评分（基于触及次数和反应强度）
        touches: 历史触及次数
    """
    low: float    # 区域下边界价格
    high: float   # 区域上边界价格
    score: float  # 强度评分（0-1）
    touches: int  # 触及次数


@dataclass
class Signal:
    """
    突破/假突破信号

    标识潜在的突破尝试或已确认的突破/假突破事件。

    属性:
        type: 信号类型（breakout_attempt/breakout_confirmed/fakeout）
        direction: 方向（up/down）
        level: 关键价位
        confidence: 置信度（0-1）
        bar_time: 触发时间
    """
    type: str        # 信号类型: breakout_attempt, breakout_confirmed, fakeout
    direction: str   # 方向: up（向上突破）, down（向下突破）
    level: float     # 突破的关键价位
    confidence: float  # 置信度（0-1）
    bar_time: datetime  # 信号触发的 K 线时间


@dataclass
class Evidence:
    """
    行为推断证据

    记录支持某种行为判断的具体证据。

    属性:
        behavior: 行为类型（accumulation/distribution/absorption/initiative）
        bar_time: 证据发生时间
        metrics: 相关指标数值
        note: 证据说明（key 形式，用于多语言）
    """
    behavior: str              # 行为类型
    bar_time: datetime         # 证据发生时间
    metrics: Dict[str, float]  # 相关指标（如 volume_ratio, spread 等）
    note: str                  # 证据说明 key


@dataclass
class TimelineEvent:
    """
    时间线事件

    记录市场结构变化或重要事件。

    属性:
        ts: 事件时间戳
        event_type: 事件类型（regime_change/signal/zone_touch 等）
        delta: 变化量（如价格变动、概率变动）
        reason: 事件原因说明 key
    """
    ts: datetime      # 事件时间戳
    event_type: str   # 事件类型
    delta: float      # 相关变化量
    reason: str       # 原因说明 key


@dataclass
class PlaybookPlan:
    """
    条件交易计划

    基于当前市场状态生成的条件化交易建议。

    属性:
        name: 计划名称（如 "Plan A: Breakout Long"）
        condition: 触发条件描述 key
        level: 入场价位
        target: 目标价位
        invalidation: 失效价位
        risk: 风险提示 key
    """
    name: str         # 计划名称
    condition: str    # 触发条件 key
    level: float      # 入场价位
    target: float     # 目标价位
    invalidation: float  # 失效价位
    risk: str         # 风险提示 key


@dataclass
class MarketState:
    """
    市场状态

    描述当前市场的整体结构状态。

    属性:
        regime: 市场状态（uptrend/downtrend/range）
        confidence: 状态置信度（0-1）
    """
    regime: str        # 市场状态: uptrend（上升趋势）, downtrend（下降趋势）, range（震荡）
    confidence: float  # 状态置信度（0-1）


@dataclass
class Behavior:
    """
    行为推断结果

    市场参与者行为的概率推断。

    属性:
        probabilities: 各行为类型的概率
        dominant: 主导行为类型
        evidence: 支持推断的证据列表
    """
    probabilities: Dict[str, float]  # 行为概率分布
    dominant: str                     # 主导行为
    evidence: List[Evidence]          # 证据列表


@dataclass
class AnalysisReport:
    """
    完整分析报告

    市场分析引擎输出的完整结果。

    属性:
        ticker: 股票代码
        tf: 时间周期
        generated_at: 报告生成时间
        bar_count: 分析使用的 K 线数量
        data_gaps: 是否存在数据缺口
        market_state: 市场状态
        zones: 支撑阻力区域（support/resistance）
        signals: 突破/假突破信号列表
        behavior: 行为推断结果
        timeline: 时间线事件列表
        playbook: 条件交易计划列表
    """
    ticker: str                       # 股票代码
    tf: str                           # 时间周期
    generated_at: datetime            # 报告生成时间
    bar_count: int                    # K 线数量
    data_gaps: bool                   # 是否有数据缺口
    market_state: MarketState         # 市场状态
    zones: Dict[str, List[Zone]]      # 支撑阻力区域: {"support": [...], "resistance": [...]}
    signals: List[Signal]             # 信号列表
    behavior: Behavior                # 行为推断
    timeline: List[TimelineEvent]     # 时间线
    playbook: List[PlaybookPlan]      # 条件剧本
