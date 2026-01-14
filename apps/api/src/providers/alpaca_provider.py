"""
Alpaca 数据提供者

使用 Alpaca Markets API 获取免费的市场数据（IEX 数据源）。

特点:
- 完全免费，无请求次数限制
- 分钟级成交量数据（IEX 口径，非全市场）
- 接近实时数据
- 支持美股

限制:
- 成交量是 IEX 交易所数据（约占全市场 2-3%）
- 需要 API Key（免费注册）
- 仅支持美股

注册地址: https://alpaca.markets/

使用示例:
    provider = AlpacaProvider(api_key="xxx", api_secret="yyy")
    bars = provider.get_bars("TSLA", "1m", "1d")
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from .base import Bar, MarketDataProvider, ProviderError, TickerNotFoundError, RateLimitError

logger = logging.getLogger(__name__)

# Alpaca Data API 基础 URL（免费 IEX 数据）
BASE_URL = "https://data.alpaca.markets/v2"


class AlpacaProvider(MarketDataProvider):
    """
    Alpaca 数据提供者

    通过 Alpaca Markets REST API 获取 K 线数据。
    使用免费的 IEX 数据源，需要 API Key。
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        初始化 Alpaca 提供者

        参数:
            api_key: Alpaca API Key
            api_secret: Alpaca API Secret
        """
        if not api_key or not api_secret:
            raise ProviderError(
                "Alpaca 需要 API Key 和 Secret，请设置 ALPACA_API_KEY 和 ALPACA_API_SECRET 环境变量。"
                "免费注册：https://alpaca.markets/"
            )
        self._api_key = api_key
        self._api_secret = api_secret
        self._headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }

    @property
    def name(self) -> str:
        """返回提供者名称"""
        return "alpaca"

    def get_bars(
        self,
        ticker: str,
        timeframe: str,
        window: Optional[str] = None,
    ) -> List[Bar]:
        """
        从 Alpaca 获取 K 线数据

        参数:
            ticker: 股票代码（如 "TSLA", "AAPL"）
            timeframe: K线周期（"1m", "5m", "1d"）
            window: 回溯时间（如 "1d", "5d", "1mo"）

        返回:
            Bar 对象列表，按时间升序排列

        异常:
            ProviderError: 不支持的时间周期或 API 错误
            TickerNotFoundError: 股票代码无效或无数据
            RateLimitError: 超过请求限制
        """
        ticker = ticker.upper()

        # Alpaca 时间周期格式
        timeframe_map = {
            "1m": "1Min",
            "5m": "5Min",
            "1d": "1Day",
        }
        alpaca_tf = timeframe_map.get(timeframe)
        if not alpaca_tf:
            raise ProviderError(f"不支持的时间周期: {timeframe}")

        # 计算时间范围
        end = datetime.utcnow()
        start = self._calculate_start(window or self.get_default_window(timeframe), timeframe)

        logger.info(f"正在获取 {ticker} 的 K 线数据: 周期={timeframe}, 范围={start} - {end}")

        # 构建请求
        url = f"{BASE_URL}/stocks/{ticker}/bars"
        params = {
            "timeframe": alpaca_tf,
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "feed": "iex",  # 使用免费的 IEX 数据
            "limit": 10000,
        }

        try:
            response = requests.get(url, headers=self._headers, params=params, timeout=30)

            # 处理错误响应
            if response.status_code == 401:
                raise ProviderError("Alpaca API 认证失败，请检查 API Key 和 Secret")
            elif response.status_code == 403:
                raise ProviderError("Alpaca API 权限不足")
            elif response.status_code == 404:
                raise TickerNotFoundError(f"股票代码不存在: {ticker}")
            elif response.status_code == 429:
                raise RateLimitError("Alpaca API 请求频率限制")
            elif response.status_code != 200:
                raise ProviderError(f"Alpaca API 错误: {response.status_code} - {response.text}")

            data = response.json()
            bars_data = data.get("bars", [])

            if not bars_data:
                raise TickerNotFoundError(f"股票代码无数据: {ticker}")

            # 解析响应
            bars = []
            for bar in bars_data:
                # Alpaca 返回格式: {"t": "2024-01-15T14:30:00Z", "o": 100.0, "h": 101.0, ...}
                ts = datetime.strptime(bar["t"], "%Y-%m-%dT%H:%M:%SZ")
                bars.append(Bar(
                    t=ts,
                    o=float(bar["o"]),
                    h=float(bar["h"]),
                    l=float(bar["l"]),
                    c=float(bar["c"]),
                    v=float(bar["v"]),
                ))

            # 按时间升序排列
            bars.sort(key=lambda b: b.t)

            logger.info(f"成功获取 {len(bars)} 根 K 线: {ticker}")
            return bars

        except requests.exceptions.Timeout:
            raise ProviderError("Alpaca API 请求超时")
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Alpaca API 请求失败: {e}")

    def _calculate_start(self, window: str, timeframe: str) -> datetime:
        """根据 window 计算开始时间"""
        now = datetime.utcnow()

        window_map = {
            "1d": timedelta(days=1),
            "5d": timedelta(days=5),
            "1mo": timedelta(days=30),
            "3mo": timedelta(days=90),
            "6mo": timedelta(days=180),
            "1y": timedelta(days=365),
        }

        delta = window_map.get(window, timedelta(days=1))
        return now - delta

    def get_default_window(self, timeframe: str) -> str:
        """获取指定周期的默认回溯时间"""
        defaults = {
            "1m": "1d",
            "5m": "5d",
            "1d": "6mo",
        }
        return defaults.get(timeframe, "1d")
