"""
Extended Hours (EH) System - 盘前盘后结构补全模块

提供盘前/盘后的关键位提取和上下文分析，作为正盘分析的"先验"。

数据质量分级:
- complete: 今日 PM 实时 + 昨日 AH + Regular（需要 TwelveData Pro）
- partial: 昨日 AH + Regular (T-1)（需要 TwelveData Pro）
- minimal: 仅 Regular session（免费版默认）

MVP 策略:
- 默认 minimal 模式（从 regular session 提取 YC/YH/YL）
- Pro 用户可获得 partial/complete 模式
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time as dt_time
from typing import List, Dict, Optional, Tuple

# 尝试从 models 导入 Bar，如果失败则定义本地版本
try:
    from .models import Bar
except ImportError:
    from dataclasses import dataclass as dc

    @dc
    class Bar:
        t: datetime
        o: float
        h: float
        l: float
        c: float
        v: float


# ============ Data Structures ============

@dataclass
class EHLevels:
    """
    Extended Hours 关键价位

    Attributes:
        yc: 昨日收盘价 (Yesterday Close) - 磁吸位
        yh: 昨日最高价 (Yesterday High)
        yl: 昨日最低价 (Yesterday Low)
        pmh: 盘前最高价 (Premarket High) - 仅 complete 模式
        pml: 盘前最低价 (Premarket Low) - 仅 complete 模式
        ahh: 盘后最高价 (Afterhours High) - partial+ 模式
        ahl: 盘后最低价 (Afterhours Low) - partial+ 模式
        gap: 缺口大小 (今日估计开盘 - YC) - 仅 complete 模式
    """
    yc: float              # 昨日收盘（始终可用）
    yh: float              # 昨日最高（始终可用）
    yl: float              # 昨日最低（始终可用）
    pmh: Optional[float] = None   # 盘前最高（complete only）
    pml: Optional[float] = None   # 盘前最低（complete only）
    ahh: Optional[float] = None   # 盘后最高（partial+）
    ahl: Optional[float] = None   # 盘后最低（partial+）
    gap: float = 0.0              # 缺口（complete only）


@dataclass
class EHKeyZone:
    """关键区域"""
    zone: str       # 区域名称: YC, YH, YL, PMH, PML, AHH, AHL
    price: float    # 价格
    role: str       # 角色: magnet, major_resistance, major_support, breakout_trigger, etc.


@dataclass
class AHRisk:
    """
    盘后风险评估

    基于正盘收盘状态预测盘后/次日风险特征。
    """
    risk: str                  # low, medium, high
    likely_behavior: str       # continuation, mean_revert, drift
    close_position: float      # 收盘在日内区间的位置 (0-1)
    late_rvol: float          # 尾盘成交量相对强度
    is_trend_day: bool        # 是否趋势日


@dataclass
class EHContext:
    """
    Extended Hours 上下文 - 正盘系统的先验输入

    根据 data_quality 不同，部分字段可能不可用:
    - complete: 所有字段可用
    - partial: PM 相关字段不可用
    - minimal: 仅 YC/YH/YL 可用
    """
    # 关键价位
    levels: EHLevels

    # 盘前分析（仅 complete 模式）
    premarket_regime: str      # trend_continuation, gap_and_go, gap_fill_bias, range_day_setup, unavailable
    premarket_bias: str        # bullish, bearish, slightly_bullish, slightly_bearish, neutral
    regime_confidence: float   # 0.0 if unavailable

    # EH 指标（仅 complete 模式）
    eh_range_score: float      # PM 波动强度（0 if unavailable）
    eh_rvol: float             # PM 成交量强度（0 if unavailable）

    # 关键区域（根据可用数据过滤）
    key_zones: List[EHKeyZone]

    # 行为检测
    pm_absorption: Optional[Dict] = None  # 盘前吸收（complete only）
    ah_risk: Optional[AHRisk] = None      # 盘后风险（partial+）

    # 预期行为
    expected_behaviors: List[str] = field(default_factory=list)

    # 元数据
    generated_at: datetime = field(default_factory=datetime.utcnow)
    data_quality: str = "minimal"  # complete, partial, minimal
    data_quality_note: str = ""


# ============ Level Extraction ============

def extract_eh_levels_minimal(
    yesterday_bars: List[Bar],
) -> EHLevels:
    """
    从昨日 regular session 数据提取关键位（minimal 模式）

    这是免费版默认模式，只需要 regular session 数据。

    参数:
        yesterday_bars: 昨日 regular session K 线（09:30-16:00 ET）

    返回:
        EHLevels: 包含 YC/YH/YL
    """
    if not yesterday_bars:
        raise ValueError("昨日 K 线数据为空")

    return EHLevels(
        yc=yesterday_bars[-1].c,  # 最后一根 K 线的收盘价
        yh=max(bar.h for bar in yesterday_bars),
        yl=min(bar.l for bar in yesterday_bars),
        pmh=None,
        pml=None,
        ahh=None,
        ahl=None,
        gap=0.0,
    )


def extract_eh_levels_partial(
    yesterday_regular: List[Bar],
    yesterday_afterhours: List[Bar],
) -> EHLevels:
    """
    从昨日数据提取关键位（partial 模式，T-1）

    需要 TwelveData Pro 的历史 EH 数据。

    参数:
        yesterday_regular: 昨日 regular session K 线
        yesterday_afterhours: 昨日盘后 K 线

    返回:
        EHLevels: 包含 YC/YH/YL + AHH/AHL
    """
    levels = extract_eh_levels_minimal(yesterday_regular)

    if yesterday_afterhours:
        levels.ahh = max(bar.h for bar in yesterday_afterhours)
        levels.ahl = min(bar.l for bar in yesterday_afterhours)

    return levels


def extract_eh_levels_complete(
    yesterday_regular: List[Bar],
    yesterday_afterhours: List[Bar],
    today_premarket: List[Bar],
) -> EHLevels:
    """
    提取完整关键位（complete 模式）

    需要 TwelveData Pro 的实时 EH 数据。

    参数:
        yesterday_regular: 昨日 regular session K 线
        yesterday_afterhours: 昨日盘后 K 线
        today_premarket: 今日盘前 K 线

    返回:
        EHLevels: 所有字段填充
    """
    levels = extract_eh_levels_partial(yesterday_regular, yesterday_afterhours)

    if today_premarket:
        levels.pmh = max(bar.h for bar in today_premarket)
        levels.pml = min(bar.l for bar in today_premarket)
        # 缺口 = 盘前最后价 - 昨收
        levels.gap = today_premarket[-1].c - levels.yc

    return levels


# ============ Key Zones Generation ============

def generate_key_zones(
    levels: EHLevels,
    current_price: Optional[float] = None,
    data_quality: str = "minimal",
) -> List[EHKeyZone]:
    """
    根据关键位生成带角色的关键区域列表

    参数:
        levels: EH 关键位
        current_price: 当前价格（用于判断角色）
        data_quality: 数据质量级别

    返回:
        关键区域列表，按重要性排序
    """
    zones = []

    # YC 始终是磁吸位
    zones.append(EHKeyZone(
        zone="YC",
        price=levels.yc,
        role="magnet",
    ))

    # YH/YL
    if current_price:
        yh_role = "major_resistance" if current_price < levels.yh else "conquered"
        yl_role = "major_support" if current_price > levels.yl else "lost"
    else:
        yh_role = "major_resistance"
        yl_role = "major_support"

    zones.append(EHKeyZone(zone="YH", price=levels.yh, role=yh_role))
    zones.append(EHKeyZone(zone="YL", price=levels.yl, role=yl_role))

    # AHH/AHL (partial+ 模式)
    if levels.ahh is not None:
        ah_role = "ah_high"
        zones.append(EHKeyZone(zone="AHH", price=levels.ahh, role=ah_role))

    if levels.ahl is not None:
        zones.append(EHKeyZone(zone="AHL", price=levels.ahl, role="ah_low"))

    # PMH/PML (complete 模式)
    if levels.pmh is not None:
        if current_price and current_price < levels.pmh:
            pm_role = "breakout_trigger"
        else:
            pm_role = "support_flip"
        zones.append(EHKeyZone(zone="PMH", price=levels.pmh, role=pm_role))

    if levels.pml is not None:
        if current_price and current_price > levels.pml:
            pm_role = "breakdown_trigger"
        else:
            pm_role = "resistance_flip"
        zones.append(EHKeyZone(zone="PML", price=levels.pml, role=pm_role))

    return zones


# ============ AH Risk Assessment ============

def assess_afterhours_risk(
    regular_bars: List[Bar],
) -> AHRisk:
    """
    基于正盘收盘状态评估盘后风险

    这个功能不需要 EH 数据，只需要正盘数据即可。

    参数:
        regular_bars: 正盘 K 线数据

    返回:
        AHRisk: 盘后风险评估
    """
    if len(regular_bars) < 30:
        return AHRisk(
            risk="medium",
            likely_behavior="drift",
            close_position=0.5,
            late_rvol=1.0,
            is_trend_day=False,
        )

    # 1. 收盘在日内区间的位置
    day_high = max(bar.h for bar in regular_bars)
    day_low = min(bar.l for bar in regular_bars)
    day_range = day_high - day_low
    close = regular_bars[-1].c

    if day_range > 0:
        close_position = (close - day_low) / day_range
    else:
        close_position = 0.5

    # 2. 尾盘成交量（最后 30 根）
    late_bars = regular_bars[-30:]
    late_volume = sum(bar.v for bar in late_bars)
    avg_30_volume = sum(bar.v for bar in regular_bars) / (len(regular_bars) / 30) if len(regular_bars) >= 30 else late_volume
    late_rvol = late_volume / avg_30_volume if avg_30_volume > 0 else 1.0

    # 3. 是否趋势日（收盘方向一致性）
    up_closes = sum(1 for bar in regular_bars if bar.c > bar.o)
    close_ratio = up_closes / len(regular_bars)
    is_trend_day = abs(close_ratio - 0.5) > 0.15
    trend_direction = "up" if close_ratio > 0.5 else "down"

    # 4. 风险评估
    if close_position > 0.8:  # 收盘接近高点
        if late_rvol > 1.3 and trend_direction == "up":
            risk = "low"
            behavior = "continuation"
        else:
            risk = "medium"
            behavior = "mean_revert"
    elif close_position < 0.2:  # 收盘接近低点
        if late_rvol > 1.3 and trend_direction == "down":
            risk = "low"
            behavior = "continuation"
        else:
            risk = "medium"
            behavior = "mean_revert"
    else:  # 收盘在中间
        risk = "medium"
        behavior = "drift"

    # 高风险覆盖
    if not is_trend_day and late_rvol < 0.7:
        risk = "high"  # 收盘前犹豫

    return AHRisk(
        risk=risk,
        likely_behavior=behavior,
        close_position=close_position,
        late_rvol=late_rvol,
        is_trend_day=is_trend_day,
    )


# ============ Main Builder ============

def build_eh_context(
    yesterday_bars: List[Bar],
    today_bars: Optional[List[Bar]] = None,
    yesterday_afterhours: Optional[List[Bar]] = None,
    today_premarket: Optional[List[Bar]] = None,
    current_price: Optional[float] = None,
) -> EHContext:
    """
    构建 EH 上下文

    根据提供的数据自动确定 data_quality 级别:
    - 有今日盘前数据 → complete
    - 有昨日盘后数据 → partial
    - 仅有正盘数据 → minimal

    参数:
        yesterday_bars: 昨日正盘 K 线（必需）
        today_bars: 今日正盘 K 线（可选，用于 current_price）
        yesterday_afterhours: 昨日盘后 K 线（可选）
        today_premarket: 今日盘前 K 线（可选）
        current_price: 当前价格（可选）

    返回:
        EHContext: 完整的 EH 上下文
    """
    if not yesterday_bars:
        raise ValueError("昨日 K 线数据为空")

    # 确定数据质量级别
    if today_premarket and len(today_premarket) >= 10:
        data_quality = "complete"
        levels = extract_eh_levels_complete(
            yesterday_bars, yesterday_afterhours or [], today_premarket
        )
        note = ""
    elif yesterday_afterhours and len(yesterday_afterhours) >= 5:
        data_quality = "partial"
        levels = extract_eh_levels_partial(yesterday_bars, yesterday_afterhours)
        note = "T-1 mode: Using yesterday's structure. Real-time premarket requires Pro tier."
    else:
        data_quality = "minimal"
        levels = extract_eh_levels_minimal(yesterday_bars)
        note = "EH data unavailable. Only YC/YH/YL levels provided."

    # 获取当前价格
    if current_price is None and today_bars:
        current_price = today_bars[-1].c

    # 生成关键区域
    key_zones = generate_key_zones(levels, current_price, data_quality)

    # 盘后风险评估（不需要 EH 数据）
    ah_risk = assess_afterhours_risk(yesterday_bars)

    # 预期行为
    expected_behaviors = ["eh.expect.yc_magnet"]
    if data_quality == "partial":
        expected_behaviors.append("eh.expect.ah_structure_reference")
    elif data_quality == "complete":
        expected_behaviors.extend([
            "eh.expect.gap_fill_test" if abs(levels.gap) > levels.yc * 0.005 else None,
            "eh.expect.pmh_resistance" if levels.pmh else None,
            "eh.expect.pml_support" if levels.pml else None,
        ])
        expected_behaviors = [b for b in expected_behaviors if b]

    # 盘前分析（仅 complete 模式）
    if data_quality == "complete":
        premarket_regime = "range_day_setup"  # TODO: 实现分类算法
        premarket_bias = "neutral"
        regime_confidence = 0.5
        eh_range_score = 1.0  # TODO: 计算
        eh_rvol = 1.0  # TODO: 计算
    else:
        premarket_regime = "unavailable"
        premarket_bias = "neutral"
        regime_confidence = 0.0
        eh_range_score = 0.0
        eh_rvol = 0.0

    return EHContext(
        levels=levels,
        premarket_regime=premarket_regime,
        premarket_bias=premarket_bias,
        regime_confidence=regime_confidence,
        eh_range_score=eh_range_score,
        eh_rvol=eh_rvol,
        key_zones=key_zones,
        pm_absorption=None,  # TODO: complete 模式实现
        ah_risk=ah_risk,
        expected_behaviors=expected_behaviors,
        generated_at=datetime.utcnow(),
        data_quality=data_quality,
        data_quality_note=note,
    )


# ============ Helper: Session Segmentation ============

# 美股交易时段 (ET)
# Premarket:  04:00 - 09:30
# Regular:    09:30 - 16:00
# Afterhours: 16:00 - 20:00

def get_session_type(bar: Bar) -> str:
    """
    判断 K 线所属的交易时段

    参数:
        bar: K 线数据（时间戳假设为 ET）

    返回:
        "premarket" | "regular" | "afterhours"
    """
    hour = bar.t.hour
    minute = bar.t.minute
    time_minutes = hour * 60 + minute

    # 盘前: 04:00 - 09:29 (240 - 569)
    if 240 <= time_minutes < 570:
        return "premarket"
    # 正盘: 09:30 - 15:59 (570 - 959)
    elif 570 <= time_minutes < 960:
        return "regular"
    # 盘后: 16:00 - 20:00 (960 - 1200)
    elif 960 <= time_minutes <= 1200:
        return "afterhours"
    else:
        # 非交易时间，归类为最近的时段
        if time_minutes < 240:
            return "afterhours"  # 凌晨属于前一天盘后
        return "afterhours"


@dataclass
class SessionBars:
    """
    按交易时段分组的 K 线数据

    用于 EH 分析，将连续的 K 线分割成:
    - yesterday_regular: 昨日正盘
    - yesterday_afterhours: 昨日盘后
    - today_premarket: 今日盘前
    - today_regular: 今日正盘（可能为空，如果还没开盘）
    """
    yesterday_regular: List[Bar] = field(default_factory=list)
    yesterday_afterhours: List[Bar] = field(default_factory=list)
    today_premarket: List[Bar] = field(default_factory=list)
    today_regular: List[Bar] = field(default_factory=list)

    @property
    def has_yesterday_data(self) -> bool:
        """是否有昨日数据"""
        return len(self.yesterday_regular) > 0

    @property
    def has_afterhours(self) -> bool:
        """是否有盘后数据"""
        return len(self.yesterday_afterhours) > 0

    @property
    def has_premarket(self) -> bool:
        """是否有盘前数据"""
        return len(self.today_premarket) > 0

    def get_data_quality(self) -> str:
        """
        根据可用数据确定质量级别

        返回:
            "complete" | "partial" | "minimal"
        """
        if self.has_premarket and len(self.today_premarket) >= 10:
            return "complete"
        elif self.has_afterhours and len(self.yesterday_afterhours) >= 5:
            return "partial"
        else:
            return "minimal"


def split_bars_by_session(bars: List[Bar]) -> SessionBars:
    """
    将 K 线数据按交易时段分割

    这是 EH 系统的核心辅助函数，将 YFinance/TwelveData 返回的
    含 Extended Hours 的 K 线分割成四个部分。

    参数:
        bars: 按时间升序的 K 线列表（含 EH 数据）

    返回:
        SessionBars: 分割后的数据结构

    示例:
        >>> bars = provider.get_bars_extended("TSLA", "1m", "2d")
        >>> sessions = split_bars_by_session(bars)
        >>> print(f"昨日正盘: {len(sessions.yesterday_regular)} bars")
        >>> print(f"今日盘前: {len(sessions.today_premarket)} bars")
    """
    if not bars:
        return SessionBars()

    # 按日期分组
    by_date = split_bars_by_day(bars)
    dates = sorted(by_date.keys())

    result = SessionBars()

    if len(dates) == 0:
        return result

    elif len(dates) == 1:
        # 只有一天数据
        today = dates[0]
        for bar in by_date[today]:
            session = get_session_type(bar)
            if session == "premarket":
                result.today_premarket.append(bar)
            elif session == "regular":
                result.today_regular.append(bar)
            # afterhours 归到 today 的话没有意义，跳过

    else:
        # 多天数据，取最后两天
        yesterday = dates[-2]
        today = dates[-1]

        # 处理昨日数据
        for bar in by_date[yesterday]:
            session = get_session_type(bar)
            if session == "regular":
                result.yesterday_regular.append(bar)
            elif session == "afterhours":
                result.yesterday_afterhours.append(bar)
            # 昨日盘前不太有用，跳过

        # 处理今日数据
        for bar in by_date[today]:
            session = get_session_type(bar)
            if session == "premarket":
                result.today_premarket.append(bar)
            elif session == "regular":
                result.today_regular.append(bar)
            # 今日盘后在盘中分析时还没发生

    return result


def split_bars_by_day(
    bars: List[Bar],
    timezone: str = "America/New_York",
) -> Dict[str, List[Bar]]:
    """
    按日期分割 K 线数据

    参数:
        bars: K 线列表（假设时间戳是 ET 或 UTC）
        timezone: 时区（用于日期划分）

    返回:
        Dict[date_str, List[Bar]]: 按日期分组的数据
    """
    by_date: Dict[str, List[Bar]] = {}

    for bar in bars:
        date_str = bar.t.date().isoformat()
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(bar)

    return by_date


def get_yesterday_bars(
    bars: List[Bar],
) -> Tuple[Optional[List[Bar]], Optional[List[Bar]]]:
    """
    从 K 线数据中分离昨日和今日数据

    参数:
        bars: 按时间升序的 K 线列表

    返回:
        (yesterday_bars, today_bars)
    """
    by_date = split_bars_by_day(bars)
    dates = sorted(by_date.keys())

    if len(dates) == 0:
        return None, None
    elif len(dates) == 1:
        # 只有一天数据，假设是今天
        return None, by_date[dates[0]]
    else:
        # 最后一天是今天，倒数第二天是昨天
        return by_date[dates[-2]], by_date[dates[-1]]


# ============ High-Level Builder from Raw Bars ============

def build_eh_context_from_bars(
    bars: List[Bar],
    current_price: Optional[float] = None,
) -> EHContext:
    """
    从含 Extended Hours 的 K 线直接构建 EHContext

    这是 API 层调用的主入口，会自动:
    1. 分割 bars 为 Regular/PM/AH
    2. 确定 data_quality 级别
    3. 提取关键位
    4. 生成完整的 EHContext

    参数:
        bars: YFinance/TwelveData get_bars_extended() 返回的数据
        current_price: 当前价格（可选）

    返回:
        EHContext: 完整的 EH 上下文

    示例:
        >>> bars = provider.get_bars_extended("TSLA", "1m", "2d")
        >>> eh_ctx = build_eh_context_from_bars(bars)
        >>> print(eh_ctx.data_quality)  # "complete" or "partial"
    """
    # 1. 分割数据
    sessions = split_bars_by_session(bars)

    if not sessions.has_yesterday_data:
        raise ValueError("缺少昨日数据，无法构建 EH 上下文")

    # 2. 获取当前价格
    if current_price is None:
        if sessions.today_regular:
            current_price = sessions.today_regular[-1].c
        elif sessions.today_premarket:
            current_price = sessions.today_premarket[-1].c

    # 3. 调用原有的 build_eh_context
    return build_eh_context(
        yesterday_bars=sessions.yesterday_regular,
        today_bars=sessions.today_regular if sessions.today_regular else None,
        yesterday_afterhours=sessions.yesterday_afterhours if sessions.has_afterhours else None,
        today_premarket=sessions.today_premarket if sessions.has_premarket else None,
        current_price=current_price,
    )
