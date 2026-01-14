"""
Yahoo Finance 数据提供者

使用 yfinance 库从 Yahoo Finance 获取免费的市场数据。

特点:
- 免费使用，无需 API 密钥
- 支持美股、ETF、加密货币
- 1分钟数据最多保留 7 天
- 存在约 15-20 分钟的数据延迟

限制:
- 每天约 2000 次请求限制
- 1分钟数据历史有限
- 非实时数据

使用示例:
    provider = YFinanceProvider()
    bars = provider.get_bars("TSLA", "1m", "1d")
"""

import logging
from typing import List, Optional

import yfinance as yf

from .base import Bar, MarketDataProvider, ProviderError, TickerNotFoundError, RateLimitError

# 配置日志记录器
logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """
    Yahoo Finance 数据提供者

    通过 yfinance 库获取 K 线数据的具体实现。
    支持多种时间周期和回溯范围。
    """

    @property
    def name(self) -> str:
        """返回提供者名称"""
        return "yfinance"

    def get_bars(
        self,
        ticker: str,
        timeframe: str,
        window: Optional[str] = None,
    ) -> List[Bar]:
        """
        从 Yahoo Finance 获取 K 线数据

        参数:
            ticker: 股票代码（如 "TSLA", "AAPL", "BTC-USD"）
            timeframe: K线周期（"1m", "5m", "1d"）
            window: 回溯时间（如 "1d", "5d", "1mo"）

        返回:
            Bar 对象列表，按时间升序排列

        异常:
            ProviderError: 不支持的时间周期
            TickerNotFoundError: 股票代码无效或无数据
            RateLimitError: 超过请求限制
        """
        # 验证并映射时间周期
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "1d": "1d",
        }
        interval = interval_map.get(timeframe)
        if not interval:
            raise ProviderError(f"不支持的时间周期: {timeframe}")

        # 获取回溯时间，如果未指定则使用默认值
        period = window or self.get_default_window(timeframe)

        logger.info(f"正在获取 {ticker} 的 K 线数据: 周期={timeframe}, 范围={period}")

        try:
            # 从 yfinance 获取数据
            ticker_obj = yf.Ticker(ticker.upper())
            df = ticker_obj.history(period=period, interval=interval)

            # 检查是否有数据返回
            if df.empty:
                raise TickerNotFoundError(f"股票代码无数据: {ticker}")

            # 将 DataFrame 转换为 Bar 对象列表
            bars: List[Bar] = []
            for idx, row in df.iterrows():
                # 处理时区 - 转换为无时区的 UTC 时间
                ts = idx.to_pydatetime()
                if ts.tzinfo is not None:
                    ts = ts.replace(tzinfo=None)

                bars.append(Bar(
                    t=ts,
                    o=float(row["Open"]),
                    h=float(row["High"]),
                    l=float(row["Low"]),
                    c=float(row["Close"]),
                    v=float(row["Volume"]),
                ))

            logger.info(f"成功获取 {len(bars)} 根 K 线: {ticker}")
            return bars

        except TickerNotFoundError:
            # 直接重新抛出已知异常
            raise
        except Exception as e:
            # 根据错误信息判断异常类型
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "too many requests" in error_msg:
                raise RateLimitError(f"Yahoo Finance 请求频率限制: {e}")
            elif "no data" in error_msg or "not found" in error_msg:
                raise TickerNotFoundError(f"股票代码不存在: {ticker}")
            else:
                logger.error(f"获取 {ticker} 数据失败: {e}")
                raise ProviderError(f"数据获取失败: {e}")
