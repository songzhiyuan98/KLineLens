"""
数据提供者测试

测试 YFinanceProvider 的功能：
- 获取 K 线数据
- 错误处理
- 默认值
"""

import pytest
from datetime import datetime

from src.providers import YFinanceProvider, TickerNotFoundError, ProviderError


class TestYFinanceProvider:
    """Yahoo Finance 提供者测试类"""

    @pytest.fixture
    def provider(self):
        """创建提供者实例"""
        return YFinanceProvider()

    def test_provider_name(self, provider):
        """
        测试提供者名称

        预期:
        - 名称为 "yfinance"
        """
        assert provider.name == "yfinance"

    def test_get_default_window(self, provider):
        """
        测试默认回溯时间

        预期:
        - 1m -> 1d
        - 5m -> 5d
        - 1d -> 6mo
        """
        assert provider.get_default_window("1m") == "1d"
        assert provider.get_default_window("5m") == "5d"
        assert provider.get_default_window("1d") == "6mo"

    def test_get_bars_returns_list(self, provider):
        """
        测试获取 K 线返回列表

        预期:
        - 返回 Bar 对象列表
        - 列表非空
        """
        bars = provider.get_bars("AAPL", "1d", "5d")

        assert isinstance(bars, list)
        assert len(bars) > 0

    def test_get_bars_bar_attributes(self, provider):
        """
        测试 Bar 对象属性

        预期:
        - 包含 t, o, h, l, c, v 属性
        """
        bars = provider.get_bars("AAPL", "1d", "5d")
        bar = bars[0]

        assert hasattr(bar, "t")
        assert hasattr(bar, "o")
        assert hasattr(bar, "h")
        assert hasattr(bar, "l")
        assert hasattr(bar, "c")
        assert hasattr(bar, "v")

    def test_get_bars_timestamp_type(self, provider):
        """
        测试时间戳类型

        预期:
        - t 是 datetime 类型
        """
        bars = provider.get_bars("AAPL", "1d", "5d")
        bar = bars[0]

        assert isinstance(bar.t, datetime)

    def test_get_bars_invalid_ticker(self, provider):
        """
        测试无效股票代码

        预期:
        - 抛出 TickerNotFoundError
        """
        with pytest.raises(TickerNotFoundError):
            provider.get_bars("INVALIDTICKERXYZ123", "1d", "5d")

    def test_get_bars_invalid_timeframe(self, provider):
        """
        测试无效时间周期

        预期:
        - 抛出 ProviderError
        """
        with pytest.raises(ProviderError):
            provider.get_bars("AAPL", "invalid", "5d")

    def test_bar_to_dict(self, provider):
        """
        测试 Bar.to_dict() 方法

        预期:
        - 返回字典
        - 包含所有字段
        - 时间戳为 ISO 格式字符串
        """
        bars = provider.get_bars("AAPL", "1d", "5d")
        bar_dict = bars[0].to_dict()

        assert isinstance(bar_dict, dict)
        assert "t" in bar_dict
        assert "o" in bar_dict
        assert "h" in bar_dict
        assert "l" in bar_dict
        assert "c" in bar_dict
        assert "v" in bar_dict

        # 检查时间戳格式
        assert isinstance(bar_dict["t"], str)
        assert bar_dict["t"].endswith("Z")
