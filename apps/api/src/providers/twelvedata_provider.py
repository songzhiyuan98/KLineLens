"""
Twelve Data 数据提供者

使用 Twelve Data API 获取高质量的市场数据。

特点:
- 实时数据（美股、外汇、加密货币）
- 可靠的分钟级成交量数据
- 低延迟 (~170ms WebSocket, REST 每分钟更新)
- 99.95% SLA 保证
- 支持 Extended Hours (prepost=true)

Free 计划:
- 800 次/天, 8 次/分钟
- 美股/外汇/加密货币实时数据
- 完整 OHLCV 数据
- 历史 Extended Hours 数据 (T-1 延迟)

Grow/Pro 计划:
- 无每日限制
- 实时 Extended Hours 数据

注册地址: https://twelvedata.com/

使用示例:
    provider = TwelveDataProvider(api_key="your_api_key")
    bars = provider.get_bars("TSLA", "1m", "5d")
    bars_eh = provider.get_bars_extended("TSLA", "1m", "2d")  # 含盘前盘后
"""

import logging
from datetime import datetime, timedelta, time as dt_time
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

import requests

from .base import Bar, MarketDataProvider, ProviderError, TickerNotFoundError, RateLimitError

logger = logging.getLogger(__name__)

# Twelve Data API 基础 URL
BASE_URL = "https://api.twelvedata.com"


class TwelveDataProvider(MarketDataProvider):
    """
    Twelve Data 数据提供者

    通过 Twelve Data REST API 获取高质量 K 线数据。
    支持实时美股、外汇、加密货币数据，包含可靠的成交量。
    """

    def __init__(self, api_key: str):
        """
        初始化 Twelve Data 提供者

        参数:
            api_key: Twelve Data API Key
        """
        if not api_key:
            raise ProviderError(
                "Twelve Data 需要 API Key，请设置 TWELVEDATA_API_KEY 环境变量。"
                "免费注册：https://twelvedata.com/"
            )
        self._api_key = api_key

    @property
    def name(self) -> str:
        """返回提供者名称"""
        return "twelvedata"

    def get_bars(
        self,
        ticker: str,
        timeframe: str,
        window: Optional[str] = None,
    ) -> List[Bar]:
        """
        从 Twelve Data 获取 K 线数据

        参数:
            ticker: 股票代码（如 "TSLA", "AAPL", "BTC/USD"）
            timeframe: K线周期（"1m", "5m", "1d"）
            window: 回溯时间（如 "5d", "1mo", "1y"）

        返回:
            Bar 对象列表，按时间升序排列

        异常:
            ProviderError: 不支持的时间周期或 API 错误
            TickerNotFoundError: 股票代码无效或无数据
            RateLimitError: 超过请求限制
        """
        ticker = ticker.upper()

        # Twelve Data 时间周期格式
        timeframe_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "1d": "1day",
        }
        td_interval = timeframe_map.get(timeframe)
        if not td_interval:
            raise ProviderError(f"不支持的时间周期: {timeframe}")

        # 计算输出数量（根据 window）
        actual_window = window or self.get_default_window(timeframe)
        outputsize = self._calculate_outputsize(actual_window, timeframe)

        logger.info(f"正在获取 {ticker} 的 K 线数据: 周期={timeframe}, 数量={outputsize}")

        # 构建请求
        url = f"{BASE_URL}/time_series"
        params = {
            "symbol": ticker,
            "interval": td_interval,
            "outputsize": outputsize,
            "apikey": self._api_key,
            "timezone": "UTC",
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            # 检查 API 错误
            if data.get("status") == "error":
                error_code = data.get("code", 0)
                error_msg = data.get("message", "Unknown error")

                if error_code == 401:
                    raise ProviderError("Twelve Data API 认证失败，请检查 API Key")
                elif error_code == 429:
                    raise RateLimitError(f"Twelve Data API 请求频率限制: {error_msg}")
                elif error_code == 400 or "not found" in error_msg.lower():
                    raise TickerNotFoundError(f"股票代码不存在: {ticker}")
                else:
                    raise ProviderError(f"Twelve Data API 错误: {error_msg}")

            # 解析响应
            values = data.get("values", [])
            if not values:
                raise TickerNotFoundError(f"股票代码无数据: {ticker}")

            # 解析 K 线数据
            bars = []
            for item in values:
                # Twelve Data 返回格式: {"datetime": "2024-01-15 14:30:00", "open": "100.0", ...}
                try:
                    # 解析时间戳（可能有多种格式）
                    datetime_str = item["datetime"]
                    if len(datetime_str) == 10:  # 日线格式 "2024-01-15"
                        ts = datetime.strptime(datetime_str, "%Y-%m-%d")
                    else:  # 分钟线格式 "2024-01-15 14:30:00"
                        ts = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

                    # 成交量可能为空（某些资产类型）
                    volume = float(item.get("volume", 0) or 0)

                    bars.append(Bar(
                        t=ts,
                        o=float(item["open"]),
                        h=float(item["high"]),
                        l=float(item["low"]),
                        c=float(item["close"]),
                        v=volume,
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"跳过无效数据: {item}, 错误: {e}")
                    continue

            if not bars:
                raise TickerNotFoundError(f"股票代码无有效数据: {ticker}")

            # Twelve Data 返回倒序（最新在前），需要反转
            bars.reverse()

            logger.info(f"成功获取 {len(bars)} 根 K 线: {ticker}")
            return bars

        except requests.exceptions.Timeout:
            raise ProviderError("Twelve Data API 请求超时")
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Twelve Data API 请求失败: {e}")

    def _calculate_outputsize(self, window: str, timeframe: str) -> int:
        """
        根据 window 和 timeframe 计算需要获取的 K 线数量

        参数:
            window: 回溯时间（如 "5d", "1mo"）
            timeframe: K 线周期

        返回:
            outputsize 参数值
        """
        # 每个周期的分钟数
        tf_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "1d": 1440,  # 日线按天计算
        }

        # 窗口对应的天数
        window_days = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
        }

        days = window_days.get(window, 5)
        minutes_per_tf = tf_minutes.get(timeframe, 1)

        if timeframe == "1d":
            # 日线直接返回天数
            return min(days, 5000)  # Twelve Data 最大 5000
        else:
            # 分钟线：假设每天 6.5 小时交易时间
            trading_minutes_per_day = 390  # 6.5 * 60
            total_bars = (days * trading_minutes_per_day) // minutes_per_tf
            return min(total_bars, 5000)

    def get_default_window(self, timeframe: str) -> str:
        """
        获取指定周期的默认回溯时间

        Twelve Data 有可靠的数据，可以获取更多历史数据。

        返回:
            - 1m -> "5d"（约 2000 根 K 线）
            - 5m -> "1mo"（约 1000 根 K 线）
            - 1d -> "1y"（约 250 根 K 线）
        """
        defaults = {
            "1m": "5d",
            "5m": "1mo",
            "1d": "1y",
        }
        return defaults.get(timeframe, "5d")

    def get_bars_extended(
        self,
        ticker: str,
        timeframe: str,
        window: Optional[str] = None,
    ) -> List[Bar]:
        """
        从 Twelve Data 获取包含 Extended Hours 的 K 线数据

        使用 prepost=true 参数获取盘前(04:00-09:30 ET)和盘后(16:00-20:00 ET)数据。

        注意:
        - Free 计划: 历史 EH 数据有 T-1 延迟（只能获取昨天及之前的 EH 数据）
        - Pro 计划: 实时 EH 数据

        参数:
            ticker: 股票代码（如 "TSLA", "AAPL"）
            timeframe: K线周期（"1m", "5m", "15m", "30m"）
            window: 回溯时间（如 "2d", "5d"）

        返回:
            Bar 对象列表，按时间升序排列，包含 EH 数据

        异常:
            ProviderError: 不支持的时间周期或 API 错误
            TickerNotFoundError: 股票代码无效或无数据
            RateLimitError: 超过请求限制
        """
        ticker = ticker.upper()

        # Extended Hours 仅支持分钟级别周期
        timeframe_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
        }
        td_interval = timeframe_map.get(timeframe)
        if not td_interval:
            raise ProviderError(f"Extended Hours 不支持的时间周期: {timeframe}（仅支持 1m/5m/15m/30m）")

        # EH 数据需要更多 bars（每天约 16 小时而非 6.5 小时）
        actual_window = window or "2d"
        outputsize = self._calculate_outputsize_extended(actual_window, timeframe)

        logger.info(f"正在获取 {ticker} 的 Extended Hours K 线数据: 周期={timeframe}, 数量={outputsize}")

        # 构建请求 - 关键是 prepost=true
        url = f"{BASE_URL}/time_series"
        params = {
            "symbol": ticker,
            "interval": td_interval,
            "outputsize": outputsize,
            "apikey": self._api_key,
            "timezone": "America/New_York",  # 使用 ET 时区便于分割
            "prepost": "true",  # 关键参数：获取 Extended Hours 数据
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            # 检查 API 错误
            if data.get("status") == "error":
                error_code = data.get("code", 0)
                error_msg = data.get("message", "Unknown error")

                if error_code == 401:
                    raise ProviderError("Twelve Data API 认证失败，请检查 API Key")
                elif error_code == 429:
                    raise RateLimitError(f"Twelve Data API 请求频率限制: {error_msg}")
                elif error_code == 400 or "not found" in error_msg.lower():
                    raise TickerNotFoundError(f"股票代码不存在: {ticker}")
                else:
                    raise ProviderError(f"Twelve Data API 错误: {error_msg}")

            # 解析响应
            values = data.get("values", [])
            if not values:
                raise TickerNotFoundError(f"股票代码无数据: {ticker}")

            # 解析 K 线数据
            bars = []
            for item in values:
                try:
                    datetime_str = item["datetime"]
                    if len(datetime_str) == 10:
                        ts = datetime.strptime(datetime_str, "%Y-%m-%d")
                    else:
                        ts = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

                    volume = float(item.get("volume", 0) or 0)

                    bars.append(Bar(
                        t=ts,
                        o=float(item["open"]),
                        h=float(item["high"]),
                        l=float(item["low"]),
                        c=float(item["close"]),
                        v=volume,
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"跳过无效数据: {item}, 错误: {e}")
                    continue

            if not bars:
                raise TickerNotFoundError(f"股票代码无有效数据: {ticker}")

            # 反转为时间升序
            bars.reverse()

            logger.info(f"成功获取 {len(bars)} 根 Extended Hours K 线: {ticker}")
            return bars

        except requests.exceptions.Timeout:
            raise ProviderError("Twelve Data API 请求超时")
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Twelve Data API 请求失败: {e}")

    def _calculate_outputsize_extended(self, window: str, timeframe: str) -> int:
        """
        计算 Extended Hours 数据需要的 outputsize

        EH 每天约 16 小时（04:00-20:00 ET），比 regular session 的 6.5 小时更多。
        """
        tf_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
        }

        window_days = {
            "1d": 1,
            "2d": 2,
            "3d": 3,
            "5d": 5,
            "1mo": 30,
        }

        days = window_days.get(window, 2)
        minutes_per_tf = tf_minutes.get(timeframe, 1)

        # Extended hours: 04:00-20:00 ET = 16 hours = 960 minutes
        eh_minutes_per_day = 960
        total_bars = (days * eh_minutes_per_day) // minutes_per_tf

        return min(total_bars, 5000)


# ============ Session Segmentation Helpers ============

@dataclass
class SessionBars:
    """
    按交易时段分割的 K 线数据

    Attributes:
        regular: 正盘时段 (09:30-16:00 ET)
        premarket: 盘前时段 (04:00-09:30 ET)
        afterhours: 盘后时段 (16:00-20:00 ET)
    """
    regular: List[Bar]
    premarket: List[Bar]
    afterhours: List[Bar]


def segment_bars_by_session(bars: List[Bar]) -> Dict[str, SessionBars]:
    """
    将 K 线数据按交易日和时段分割

    假设 bars 的时间戳是 ET (America/New_York) 时区。

    时段定义:
    - Premarket: 04:00-09:29 ET
    - Regular: 09:30-15:59 ET
    - Afterhours: 16:00-19:59 ET

    参数:
        bars: 按时间升序排列的 K 线列表（时间戳应为 ET）

    返回:
        Dict[date_str, SessionBars]: 按日期分组的各时段数据
    """
    # 时段边界 (ET)
    PREMARKET_START = dt_time(4, 0)
    REGULAR_START = dt_time(9, 30)
    AFTERHOURS_START = dt_time(16, 0)
    AFTERHOURS_END = dt_time(20, 0)

    # 按日期分组
    by_date: Dict[str, Dict[str, List[Bar]]] = {}

    for bar in bars:
        bar_time = bar.t.time()
        bar_date = bar.t.date().isoformat()

        if bar_date not in by_date:
            by_date[bar_date] = {
                "premarket": [],
                "regular": [],
                "afterhours": [],
            }

        # 分类到对应时段
        if PREMARKET_START <= bar_time < REGULAR_START:
            by_date[bar_date]["premarket"].append(bar)
        elif REGULAR_START <= bar_time < AFTERHOURS_START:
            by_date[bar_date]["regular"].append(bar)
        elif AFTERHOURS_START <= bar_time < AFTERHOURS_END:
            by_date[bar_date]["afterhours"].append(bar)
        # 其他时间忽略（如凌晨 00:00-04:00）

    # 转换为 SessionBars
    result: Dict[str, SessionBars] = {}
    for date_str, sessions in by_date.items():
        result[date_str] = SessionBars(
            regular=sessions["regular"],
            premarket=sessions["premarket"],
            afterhours=sessions["afterhours"],
        )

    return result


def get_yesterday_sessions(
    segmented: Dict[str, SessionBars]
) -> Tuple[Optional[SessionBars], Optional[SessionBars]]:
    """
    从分割后的数据中获取昨日和今日的 sessions

    返回:
        (yesterday_sessions, today_sessions)
        如果数据不足，对应值为 None
    """
    dates = sorted(segmented.keys())

    if len(dates) == 0:
        return None, None
    elif len(dates) == 1:
        return segmented[dates[0]], None
    else:
        # 最后一天是今天（可能不完整），倒数第二天是昨天
        return segmented[dates[-2]], segmented[dates[-1]]
