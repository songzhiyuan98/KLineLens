"""
KLineLens 核心类型定义

定义市场分析引擎使用的所有数据结构。
这些类型用于在各模块之间传递数据。

主要类型:
- Bar: OHLCV K 线数据
- Zone: 支撑/阻力区域（增强版：含 rejections, reaction, recency）
- Signal: 突破/假突破信号（增强版：含 bar_index, volume_quality）
- Evidence: 行为推断证据（增强版：含 type, severity, bar_index, VSA metrics）
- TimelineEvent: 时间线事件（增强版：含 bar_index, severity, soft events）
- PlaybookPlan: 条件交易计划
- MarketState: 市场状态（趋势/震荡）
- Behavior: 行为推断结果
- AnalysisReport: 完整分析报告（增强版：含 volume_quality）
"""

from dataclasses import dataclass, field
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
    支撑/阻力区域（增强版）

    代表一个价格区间，该区间在历史上表现出支撑或阻力特性。
    增强版包含更多维度的强度评估指标。

    属性:
        low: 区域下边界
        high: 区域上边界
        score: 区域强度评分（基于 tests + rejections + reaction + recency）
        touches: 历史触及次数（测试次数）
        rejections: 价格从该区域反转的次数（反应次数）
        last_reaction: 最后一次反应的幅度（以 ATR 为单位）
        last_test_time: 最后一次测试的时间

    强度评分算法:
        zone_strength = (0.3 × tests) + (0.3 × rejections) + (0.25 × reaction_magnitude) + (0.15 × recency)
        - tests: min(触及次数, 5) / 5（上限 5 次）
        - rejections: min(反转次数, 5) / 5
        - reaction_magnitude: min(最后反应/2ATR, 1)
        - recency: 1 - (bars_since_last_test / 100)（越近越高）
    """
    low: float    # 区域下边界价格
    high: float   # 区域上边界价格
    score: float  # 强度评分（0-1）
    touches: int  # 触及次数（测试次数）
    rejections: int = 0  # 反转次数
    last_reaction: float = 0.0  # 最后反应幅度（ATR）
    last_test_time: Optional[datetime] = None  # 最后测试时间


@dataclass
class Signal:
    """
    突破/假突破信号（增强版）

    标识潜在的突破尝试或已确认的突破/假突破事件。
    增强版支持 3-Factor 确认和 click-to-locate 功能。

    属性:
        type: 信号类型（breakout_attempt/breakout_confirmed/fakeout）
        direction: 方向（up/down）
        level: 关键价位
        confidence: 置信度（0-1）
        bar_time: 触发时间
        bar_index: K 线索引（用于 click-to-locate）
        volume_quality: 成交量确认状态（confirmed/pending/unavailable）

    3-Factor 突破确认:
        1. Structure: 2 连续收盘在区域外
        2. Volume: RVOL >= 1.8
        3. Result: range/ATR >= 0.6

        - 3/3 factors → breakout_confirmed
        - 2/3 factors → breakout_attempt (高置信)
        - 1/3 factors → breakout_attempt (低置信)
        - 回撤到区域内 within 3 bars → fakeout
    """
    type: str        # 信号类型: breakout_attempt, breakout_confirmed, fakeout
    direction: str   # 方向: up（向上突破）, down（向下突破）
    level: float     # 突破的关键价位
    confidence: float  # 置信度（0-1）
    bar_time: datetime  # 信号触发的 K 线时间
    bar_index: int = -1  # K 线索引（click-to-locate）
    volume_quality: str = "pending"  # 成交量确认: confirmed, pending, unavailable


@dataclass
class Evidence:
    """
    行为推断证据（增强版）

    记录支持某种行为判断的具体证据。
    增强版包含 VSA 指标、严重程度和 click-to-locate 功能。

    属性:
        type: 证据类型（VOLUME_SPIKE/REJECTION/SWEEP/ABSORPTION/BREAKOUT）
        behavior: 行为类型（accumulation/shakeout/markup/distribution/markdown）
        severity: 严重程度（low/med/high）
        bar_time: 证据发生时间
        bar_index: K 线索引（用于 click-to-locate）
        metrics: 相关指标数值（含 VSA 指标）
        note: 证据说明（key 形式，用于多语言）

    证据类型说明:
        - VOLUME_SPIKE: 成交量放大（RVOL >= 2.0）
        - REJECTION: 价格拒绝/反转（长影线）
        - SWEEP: 扫止损（快速穿越后回收）
        - ABSORPTION: VSA 吸收（高 Effort + 低 Result）
        - BREAKOUT: 突破确认

    VSA Metrics:
        - rvol: 相对成交量
        - wick_ratio: 影线比率
        - effort: 成交量强度（= RVOL）
        - result: 价格推进（= range/ATR）
    """
    type: str                  # 证据类型: VOLUME_SPIKE, REJECTION, SWEEP, ABSORPTION, BREAKOUT
    behavior: str              # 行为类型
    severity: str              # 严重程度: low, med, high
    bar_time: datetime         # 证据发生时间
    bar_index: int             # K 线索引（click-to-locate）
    metrics: Dict[str, float]  # 相关指标（含 rvol, wick_ratio, effort, result）
    note: str                  # 证据说明 key


@dataclass
class TimelineEvent:
    """
    时间线事件（增强版）

    记录市场结构变化或重要事件。
    增强版支持 Soft Events 和 click-to-locate 功能。

    属性:
        ts: 事件时间戳
        event_type: 事件类型（Hard Events + Soft Events）
        delta: 变化量（如价格变动、概率变动）
        reason: 事件原因说明 key
        bar_index: K 线索引（用于 click-to-locate）
        severity: 严重程度（info/warning/critical）

    Hard Events（关键事件，影响状态）:
        - regime_change: 市场状态变化
        - behavior_change: 主导行为变化
        - breakout_confirmed: 突破确认
        - breakdown_confirmed: 破位确认
        - fakeout_detected: 假突破检测
        - *_prob_up/*_prob_down: 概率变化 >= 0.12

    Soft Events（叙事事件，增强上下文）:
        - zone_approached: 价格接近关键区域（distance <= 0.5 ATR）
        - zone_tested: 价格测试区域
        - zone_rejected: 价格被区域拒绝
        - zone_accepted: 价格穿越区域
        - spring: Wyckoff Spring（扫止损 + 快速回收）
        - upthrust: Wyckoff Upthrust（假突破 + 快速回落）
        - absorption_clue: VSA 吸收信号（高 Effort + 低 Result）
        - volume_spike: 成交量放大（RVOL >= 2.0）
        - volume_dryup: 成交量萎缩（RVOL <= 0.5）
        - new_swing_high: 新高点形成
        - new_swing_low: 新低点形成
    """
    ts: datetime      # 事件时间戳
    event_type: str   # 事件类型
    delta: float      # 相关变化量
    reason: str       # 原因说明 key
    bar_index: int = -1  # K 线索引（click-to-locate）
    severity: str = "info"  # 严重程度: info, warning, critical


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
    完整分析报告（增强版）

    市场分析引擎输出的完整结果。
    增强版包含成交量质量评估，影响分析置信度。

    属性:
        ticker: 股票代码
        tf: 时间周期
        generated_at: 报告生成时间
        bar_count: 分析使用的 K 线数量
        data_gaps: 是否存在数据缺口
        volume_quality: 成交量数据质量（reliable/partial/unavailable）
        market_state: 市场状态
        zones: 支撑阻力区域（support/resistance）
        signals: 突破/假突破信号列表
        behavior: 行为推断结果
        timeline: 时间线事件列表
        playbook: 条件交易计划列表

    Volume Quality 影响:
        - reliable: 完整 VSA 分析可用，3-Factor 确认可用
        - partial: VSA 分析可用但置信度降低
        - unavailable: 仅结构分析可用，置信度 -30%
    """
    ticker: str                       # 股票代码
    tf: str                           # 时间周期
    generated_at: datetime            # 报告生成时间
    bar_count: int                    # K 线数量
    data_gaps: bool                   # 是否有数据缺口
    volume_quality: str               # 成交量质量: reliable, partial, unavailable
    market_state: MarketState         # 市场状态
    zones: Dict[str, List[Zone]]      # 支撑阻力区域: {"support": [...], "resistance": [...]}
    signals: List[Signal]             # 信号列表
    behavior: Behavior                # 行为推断
    timeline: List[TimelineEvent]     # 时间线
    playbook: List[PlaybookPlan]      # 条件剧本
