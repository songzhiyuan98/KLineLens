"""
Yahoo Finance 数据提供者

使用 yfinance 库从 Yahoo Finance 获取免费的市场数据。

特点:
- 免费使用，无需 API 密钥
- 支持美股、ETF、加密货币
- 1分钟数据最多保留 7 天
- 存在约 15-20 分钟的数据延迟
- 支持 Extended Hours (prepost=True) 获取盘前盘后数据

限制:
- 每天约 2000 次请求限制
- 1分钟数据历史有限
- 非实时数据
- Extended Hours 数据可能偶尔缺失

使用示例:
    provider = YFinanceProvider()
    bars = provider.get_bars("TSLA", "1m", "1d")

    # 获取含盘前盘后的数据
    bars_eh = provider.get_bars_extended("TSLA", "1m", "2d")
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

    def get_bars_extended(
        self,
        ticker: str,
        timeframe: str,
        window: Optional[str] = None,
    ) -> List[Bar]:
        """
        获取含盘前盘后的 K 线数据 (Extended Hours)

        使用 prepost=True 参数获取盘前(04:00-09:30 ET)和盘后(16:00-20:00 ET)数据。
        这是免费获取 EH 数据的方案，用于填补开盘断层。

        注意:
        - 数据延迟约 15-20 分钟
        - EH 时段成交量较低，数据可能不完整
        - 适合用于提取关键位 (PMH/PML/AHH/AHL)，不适合实时交易

        参数:
            ticker: 股票代码（如 "TSLA", "AAPL"）
            timeframe: K线周期（"1m", "5m"）
            window: 回溯时间（如 "2d", "5d"）

        返回:
            Bar 对象列表，包含 Regular + Premarket + Afterhours 数据

        异常:
            ProviderError: 不支持的时间周期
            TickerNotFoundError: 股票代码无效或无数据
        """
        # 验证并映射时间周期（EH 只支持分钟级）
        interval_map = {
            "1m": "1m",
            "5m": "5m",
        }
        interval = interval_map.get(timeframe)
        if not interval:
            raise ProviderError(f"Extended Hours 不支持的时间周期: {timeframe}，仅支持 1m/5m")

        # 获取回溯时间，EH 模式默认用更长窗口
        period = window or "2d"

        logger.info(f"正在获取 {ticker} 的 Extended Hours 数据: 周期={timeframe}, 范围={period}")

        try:
            ticker_obj = yf.Ticker(ticker.upper())
            # 关键: prepost=True 获取盘前盘后数据
            df = ticker_obj.history(period=period, interval=interval, prepost=True)

            if df.empty:
                raise TickerNotFoundError(f"股票代码无 Extended Hours 数据: {ticker}")

            # 转换为 Bar 对象
            bars: List[Bar] = []
            for idx, row in df.iterrows():
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

            # 统计 EH 数据
            eh_count = self._count_extended_hours_bars(bars)
            logger.info(
                f"成功获取 {len(bars)} 根 K 线 (含 EH): {ticker}, "
                f"其中盘前约 {eh_count['premarket']} 根, 盘后约 {eh_count['afterhours']} 根"
            )

            return bars

        except TickerNotFoundError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "too many requests" in error_msg:
                raise RateLimitError(f"Yahoo Finance 请求频率限制: {e}")
            elif "no data" in error_msg or "not found" in error_msg:
                raise TickerNotFoundError(f"股票代码不存在: {ticker}")
            else:
                logger.error(f"获取 {ticker} Extended Hours 数据失败: {e}")
                raise ProviderError(f"Extended Hours 数据获取失败: {e}")

    def _count_extended_hours_bars(self, bars: List[Bar]) -> dict:
        """
        统计 Extended Hours K 线数量

        盘前: 04:00-09:30 ET
        盘后: 16:00-20:00 ET
        正盘: 09:30-16:00 ET
        """
        premarket = 0
        afterhours = 0

        for bar in bars:
            hour = bar.t.hour
            minute = bar.t.minute

            # 盘前: 04:00 - 09:29
            if hour < 9 or (hour == 9 and minute < 30):
                premarket += 1
            # 盘后: 16:00 - 20:00
            elif hour >= 16:
                afterhours += 1

        return {
            "premarket": premarket,
            "afterhours": afterhours,
            "regular": len(bars) - premarket - afterhours,
        }
