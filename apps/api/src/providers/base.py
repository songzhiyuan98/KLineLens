"""
数据提供者基类和类型定义

本模块定义了市场数据提供者的抽象接口和通用数据结构：
- Bar: OHLCV K线数据结构
- MarketDataProvider: 数据提供者抽象基类
- 异常类型: ProviderError, TickerNotFoundError, RateLimitError

所有具体的数据提供者（如 YFinance, Polygon）都必须继承 MarketDataProvider。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Bar:
    """
    OHLCV K线数据结构

    存储单根 K 线的所有数据，包括时间戳和量价信息。

    属性:
        t: 时间戳（UTC）
        o: 开盘价
        h: 最高价
        l: 最低价
        c: 收盘价
        v: 成交量
    """
    t: datetime  # 时间戳（UTC）
    o: float     # 开盘价 (Open)
    h: float     # 最高价 (High)
    l: float     # 最低价 (Low)
    c: float     # 收盘价 (Close)
    v: float     # 成交量 (Volume)

    def to_dict(self) -> dict:
        """
        转换为可序列化的字典格式

        返回:
            包含所有字段的字典，时间戳转为 ISO 格式字符串
        """
        return {
            "t": self.t.isoformat() + "Z",
            "o": self.o,
            "h": self.h,
            "l": self.l,
            "c": self.c,
            "v": self.v,
        }


class ProviderError(Exception):
    """
    数据提供者基础异常

    所有提供者相关的异常都继承此类。
    """
    pass


class TickerNotFoundError(ProviderError):
    """
    股票代码不存在异常

    当请求的股票代码无效或没有数据时抛出。
    """
    pass


class RateLimitError(ProviderError):
    """
    请求频率限制异常

    当超过数据提供者的 API 调用限制时抛出。
    """
    pass


class MarketDataProvider(ABC):
    """
    市场数据提供者抽象基类

    定义了获取 K 线数据的标准接口。
    所有具体的数据提供者都必须实现这个接口。

    使用示例:
        provider = YFinanceProvider()
        bars = provider.get_bars("TSLA", "1m", "1d")
    """

    @abstractmethod
    def get_bars(
        self,
        ticker: str,
        timeframe: str,
        window: Optional[str] = None,
    ) -> List[Bar]:
        """
        获取指定股票的 K 线数据

        参数:
            ticker: 股票代码（如 "TSLA", "AAPL"）
            timeframe: K线周期（"1m", "5m", "1d"）
            window: 回溯时间范围（如 "1d", "5d", "1mo", "6mo"）

        返回:
            按时间升序排列的 Bar 对象列表

        异常:
            TickerNotFoundError: 股票代码不存在或无数据
            RateLimitError: 超过 API 调用限制
            ProviderError: 其他提供者错误
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        提供者名称

        用于日志记录和调试。

        返回:
            提供者的标识名称（如 "yfinance"）
        """
        pass

    def get_default_window(self, timeframe: str) -> str:
        """
        获取指定周期的默认回溯时间

        参数:
            timeframe: K线周期

        返回:
            默认的回溯时间范围
            - 1m -> "5d"（1分钟线默认获取5天，约1500-2000根K线）
            - 5m -> "1mo"（5分钟线默认获取1个月，约1000根K线）
            - 1d -> "1y"（日线默认获取1年，约250根K线）

        注意:
            Yahoo Finance 的 1m 数据最多保留 7 天，5d 是安全选择。
            更多数据有助于结构检测和行为推断的准确性。
        """
        defaults = {
            "1m": "5d",
            "5m": "1mo",
            "1d": "1y",
        }
        return defaults.get(timeframe, "5d")
