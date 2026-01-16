"""
Sim Trader 配置参数

定义 0DTE 交易计划模块的所有可配置参数。
参数可以通过环境变量覆盖。
"""

from dataclasses import dataclass
import os


@dataclass
class SimTraderConfig:
    """
    Sim Trader 配置

    所有参数都有合理的默认值，可根据交易风格调整。
    """

    # ============ 突破确认参数 ============

    # 避免假突破的缓冲百分比 (0.05% = 0.0005)
    buffer_pct: float = 0.0005

    # 确认所需的 K 线数（连续收盘在关键位之上/下）
    confirm_bars: int = 2

    # 失效确认所需的 K 线数
    invalidate_bars: int = 2

    # ============ 状态触发参数 ============

    # 距离关键位多近触发 ARMED 状态 (0.3% = 0.003)
    armed_distance_pct: float = 0.003

    # 距离关键位多近触发 WATCH 状态 (1% = 0.01)
    watch_distance_pct: float = 0.01

    # ============ 持仓管理参数 ============

    # 时间止损：入场后多少分钟无进展建议 TRIM
    time_stop_minutes: int = 10

    # 目标位最大测试次数，超过建议 TRIM
    max_target_attempts: int = 3

    # 每日最大交易次数
    max_trades_per_day: int = 1

    # ============ 开盘保护参数 ============

    # 开盘保护时长（分钟）- 09:30 后的分钟数
    opening_protection_minutes: int = 10

    # 开盘保护期间是否要求高 RVOL
    opening_require_high_rvol: bool = True

    # ============ 时间窗口参数（美东时间 ET）============

    # 交易开始时间（小时）
    trade_start_hour: int = 9
    trade_start_minute: int = 40

    # 交易结束时间（小时）- 超过此时间不新建仓位
    trade_end_hour: int = 15
    trade_end_minute: int = 0

    # ============ 风险评估参数 ============

    # 低 RVOL 阈值
    low_rvol_threshold: float = 0.8

    # 高 RVOL 阈值
    high_rvol_threshold: float = 1.5

    # 低置信度阈值（低于此值提高风险等级）
    low_confidence_threshold: float = 60.0

    # ============ 目标计算参数 ============

    # 默认目标为下一个 zone，如果没有则使用 ATR 倍数
    default_target_atr_multiple: float = 1.5

    # 默认止损 ATR 倍数
    default_stop_atr_multiple: float = 0.5

    @classmethod
    def from_env(cls) -> "SimTraderConfig":
        """从环境变量加载配置"""
        return cls(
            buffer_pct=float(os.getenv("SIM_BUFFER_PCT", "0.0005")),
            confirm_bars=int(os.getenv("SIM_CONFIRM_BARS", "2")),
            invalidate_bars=int(os.getenv("SIM_INVALIDATE_BARS", "2")),
            armed_distance_pct=float(os.getenv("SIM_ARMED_DISTANCE_PCT", "0.003")),
            watch_distance_pct=float(os.getenv("SIM_WATCH_DISTANCE_PCT", "0.01")),
            time_stop_minutes=int(os.getenv("SIM_TIME_STOP_MINUTES", "10")),
            max_target_attempts=int(os.getenv("SIM_MAX_TARGET_ATTEMPTS", "3")),
            max_trades_per_day=int(os.getenv("SIM_MAX_TRADES_PER_DAY", "1")),
            opening_protection_minutes=int(os.getenv("SIM_OPENING_PROTECTION_MINUTES", "10")),
        )


# 默认配置实例
DEFAULT_CONFIG = SimTraderConfig()


def get_buffer(price: float, config: SimTraderConfig = DEFAULT_CONFIG) -> float:
    """
    计算价格缓冲值

    Args:
        price: 当前价格
        config: 配置

    Returns:
        缓冲值（绝对价格）

    示例:
        QQQ 624 时，buffer = 624 * 0.0005 = 0.312
    """
    return price * config.buffer_pct


def get_armed_distance(price: float, config: SimTraderConfig = DEFAULT_CONFIG) -> float:
    """
    计算 ARMED 触发距离

    Args:
        price: 当前价格
        config: 配置

    Returns:
        ARMED 触发距离（绝对价格）

    示例:
        QQQ 624 时，distance = 624 * 0.003 = 1.872
    """
    return price * config.armed_distance_pct


def get_watch_distance(price: float, config: SimTraderConfig = DEFAULT_CONFIG) -> float:
    """
    计算 WATCH 触发距离

    Args:
        price: 当前价格
        config: 配置

    Returns:
        WATCH 触发距离（绝对价格）

    示例:
        QQQ 624 时，distance = 624 * 0.01 = 6.24
    """
    return price * config.watch_distance_pct
