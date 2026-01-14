"""
Alpha Vantage 数据提供者

使用 Alpha Vantage API 获取高质量的市场数据。

特点:
- 免费 tier: 25 requests/day
- 高质量分钟级成交量数据
- 支持美股、ETF、加密货币、外汇
- 需要 API Key（免费注册）

限制:
- 免费版每天 25 次请求
- 需要注册获取 API Key
- 分钟数据仅美股交易时段

注册地址: https://www.alphavantage.co/support/#api-key

使用示例:
    provider = AlphaVantageProvider(api_key="YOUR_API_KEY")
    bars = provider.get_bars("TSLA", "1m", "1d")
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from .base import Bar, MarketDataProvider, ProviderError, TickerNotFoundError, RateLimitError

logger = logging.getLogger(__name__)

# Alpha Vantage API 基础 URL
BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageProvider(MarketDataProvider):
    """
    Alpha Vantage 数据提供者

    通过 Alpha Vantage REST API 获取 K 线数据。
    需要 API Key，可在官网免费注册获取。
    """

    def __init__(self, api_key: str):
        """
        初始化 Alpha Vantage 提供者

        参数:
            api_key: Alpha Vantage API 密钥
        """
        if not api_key:
            raise ProviderError("Alpha Vantage 需要 API Key，请设置 ALPHAVANTAGE_API_KEY 环境变量")
        self._api_key = api_key

    @property
    def name(self) -> str:
        """返回提供者名称"""
        return "alphavantage"

    def get_bars(
        self,
        ticker: str,
        timeframe: str,
        window: Optional[str] = None,
    ) -> List[Bar]:
        """
        从 Alpha Vantage 获取 K 线数据

        参数:
            ticker: 股票代码（如 "TSLA", "AAPL"）
            timeframe: K线周期（"1m", "5m", "1d"）
            window: 回溯时间（如 "1d", "5d", "1mo"）- 主要影响返回数据量

        返回:
            Bar 对象列表，按时间升序排列

        异常:
            ProviderError: 不支持的时间周期或 API 错误
            TickerNotFoundError: 股票代码无效或无数据
            RateLimitError: 超过请求限制
        """
        ticker = ticker.upper()
        logger.info(f"正在获取 {ticker} 的 K 线数据: 周期={timeframe}")

        if timeframe in ("1m", "5m"):
            return self._get_intraday(ticker, timeframe, window)
        elif timeframe == "1d":
            return self._get_daily(ticker, window)
        else:
            raise ProviderError(f"不支持的时间周期: {timeframe}")

    def _get_intraday(self, ticker: str, timeframe: str, window: Optional[str]) -> List[Bar]:
        """获取分钟级数据"""
        interval_map = {"1m": "1min", "5m": "5min"}
        interval = interval_map.get(timeframe)

        # 根据 window 决定获取多少数据
        # full: 最近 30 天, compact: 最近 100 个数据点
        outputsize = "full" if window in ("5d", "1mo", "6mo") else "compact"

        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": ticker,
            "interval": interval,
            "apikey": self._api_key,
            "outputsize": outputsize,
            "datatype": "json",
        }

        data = self._make_request(params)

        # 解析响应
        time_series_key = f"Time Series ({interval})"
        if time_series_key not in data:
            if "Note" in data:
                raise RateLimitError(f"Alpha Vantage API 调用限制: {data['Note']}")
            if "Error Message" in data:
                raise TickerNotFoundError(f"股票代码无效: {ticker}")
            raise ProviderError(f"API 响应格式异常: {data}")

        time_series = data[time_series_key]
        bars = self._parse_time_series(time_series, window)

        logger.info(f"成功获取 {len(bars)} 根 K 线: {ticker}")
        return bars

    def _get_daily(self, ticker: str, window: Optional[str]) -> List[Bar]:
        """获取日线数据"""
        # 根据 window 决定获取多少数据
        outputsize = "full" if window in ("1mo", "6mo", "1y") else "compact"

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "apikey": self._api_key,
            "outputsize": outputsize,
            "datatype": "json",
        }

        data = self._make_request(params)

        # 解析响应
        time_series_key = "Time Series (Daily)"
        if time_series_key not in data:
            if "Note" in data:
                raise RateLimitError(f"Alpha Vantage API 调用限制: {data['Note']}")
            if "Error Message" in data:
                raise TickerNotFoundError(f"股票代码无效: {ticker}")
            raise ProviderError(f"API 响应格式异常: {data}")

        time_series = data[time_series_key]
        bars = self._parse_time_series(time_series, window, is_daily=True)

        logger.info(f"成功获取 {len(bars)} 根日线: {ticker}")
        return bars

    def _make_request(self, params: dict) -> dict:
        """发送 API 请求"""
        try:
            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise ProviderError("Alpha Vantage API 请求超时")
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Alpha Vantage API 请求失败: {e}")

    def _parse_time_series(
        self,
        time_series: dict,
        window: Optional[str],
        is_daily: bool = False,
    ) -> List[Bar]:
        """解析时间序列数据为 Bar 列表"""
        bars = []

        # 计算时间过滤范围
        cutoff = self._calculate_cutoff(window, is_daily)

        for timestamp_str, values in time_series.items():
            # 解析时间戳
            if is_daily:
                ts = datetime.strptime(timestamp_str, "%Y-%m-%d")
            else:
                ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            # 应用时间过滤
            if cutoff and ts < cutoff:
                continue

            # Alpha Vantage 字段格式
            bars.append(Bar(
                t=ts,
                o=float(values["1. open"]),
                h=float(values["2. high"]),
                l=float(values["3. low"]),
                c=float(values["4. close"]),
                v=float(values["5. volume"]),
            ))

        # 按时间升序排列
        bars.sort(key=lambda b: b.t)
        return bars

    def _calculate_cutoff(self, window: Optional[str], is_daily: bool) -> Optional[datetime]:
        """根据 window 计算时间截止点"""
        if not window:
            window = "6mo" if is_daily else "1d"

        now = datetime.now()

        window_map = {
            "1d": timedelta(days=1),
            "5d": timedelta(days=5),
            "1mo": timedelta(days=30),
            "3mo": timedelta(days=90),
            "6mo": timedelta(days=180),
            "1y": timedelta(days=365),
        }

        delta = window_map.get(window)
        if delta:
            return now - delta
        return None

    def get_default_window(self, timeframe: str) -> str:
        """
        获取指定周期的默认回溯时间

        Alpha Vantage 分钟数据可获取更长历史。
        """
        defaults = {
            "1m": "1d",
            "5m": "5d",
            "1d": "6mo",
        }
        return defaults.get(timeframe, "1d")
