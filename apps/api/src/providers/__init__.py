"""
数据提供者模块

本模块提供市场数据获取的抽象层，支持多种数据源：
- TwelveDataProvider: 使用 Twelve Data 获取高质量实时数据（推荐，有可靠分钟成交量）
- YFinanceProvider: 使用 Yahoo Finance 获取免费数据（默认，无需 API Key）
- AlpacaProvider: 使用 Alpaca IEX 获取免费数据（有分钟成交量）
- AlphaVantageProvider: 使用 Alpha Vantage 获取数据（25次/天限制）

主要导出:
- MarketDataProvider: 数据提供者抽象基类
- Bar: K线数据结构
- get_provider: 根据配置获取提供者实例
- 各种异常类型
"""

from typing import Optional

from .base import MarketDataProvider, Bar, ProviderError, TickerNotFoundError, RateLimitError
from .yfinance_provider import YFinanceProvider
from .alphavantage_provider import AlphaVantageProvider
from .alpaca_provider import AlpacaProvider
from .twelvedata_provider import (
    TwelveDataProvider,
    SessionBars,
    segment_bars_by_session,
    get_yesterday_sessions,
)


def get_provider(
    name: str,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
) -> MarketDataProvider:
    """
    根据名称获取数据提供者实例

    参数:
        name: 提供者名称 ("yfinance", "alpaca", "alphavantage")
        api_key: API 密钥（某些提供者需要）
        api_secret: API Secret（Alpaca 需要）

    返回:
        MarketDataProvider 实例

    异常:
        ValueError: 未知的提供者名称
        ProviderError: 提供者初始化失败（如缺少 API Key）
    """
    providers = {
        "twelvedata": lambda: TwelveDataProvider(api_key=api_key or ""),
        "twelve_data": lambda: TwelveDataProvider(api_key=api_key or ""),  # 别名
        "yfinance": lambda: YFinanceProvider(),
        "yahoo": lambda: YFinanceProvider(),  # 别名
        "alpaca": lambda: AlpacaProvider(api_key=api_key or "", api_secret=api_secret or ""),
        "alphavantage": lambda: AlphaVantageProvider(api_key=api_key or ""),
        "alpha_vantage": lambda: AlphaVantageProvider(api_key=api_key or ""),  # 别名
    }

    factory = providers.get(name.lower())
    if not factory:
        available = ", ".join(set(k for k in providers.keys() if "_" not in k))
        raise ValueError(f"未知的数据提供者: {name}。可用: {available}")

    return factory()


__all__ = [
    "MarketDataProvider",
    "Bar",
    "ProviderError",
    "TickerNotFoundError",
    "RateLimitError",
    "TwelveDataProvider",
    "YFinanceProvider",
    "AlpacaProvider",
    "AlphaVantageProvider",
    "get_provider",
    # Extended Hours helpers
    "SessionBars",
    "segment_bars_by_session",
    "get_yesterday_sessions",
]
