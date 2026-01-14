"""
数据提供者模块

本模块提供市场数据获取的抽象层，支持多种数据源：
- YFinanceProvider: 使用 Yahoo Finance 获取免费数据
- 未来可扩展: Alpha Vantage, Polygon.io 等

主要导出:
- MarketDataProvider: 数据提供者抽象基类
- Bar: K线数据结构
- YFinanceProvider: Yahoo Finance 实现
- 各种异常类型
"""

from .base import MarketDataProvider, Bar, ProviderError, TickerNotFoundError, RateLimitError
from .yfinance_provider import YFinanceProvider

__all__ = [
    "MarketDataProvider",
    "Bar",
    "ProviderError",
    "TickerNotFoundError",
    "RateLimitError",
    "YFinanceProvider",
]
