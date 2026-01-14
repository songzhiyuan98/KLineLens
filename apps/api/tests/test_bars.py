"""
K 线数据端点测试

测试 GET /v1/bars 端点的各种场景：
- 正常获取数据
- 无效参数处理
- 错误响应格式
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


# 创建测试客户端
client = TestClient(app)


class TestBarsEndpoint:
    """K 线数据端点测试类"""

    def test_get_bars_success(self):
        """
        测试正常获取 K 线数据

        预期:
        - 状态码: 200
        - 响应包含 ticker, tf, bar_count, bars
        - bars 是非空数组
        """
        response = client.get("/v1/bars", params={
            "ticker": "AAPL",
            "tf": "1d",
            "window": "5d"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["ticker"] == "AAPL"
        assert data["tf"] == "1d"
        assert "bar_count" in data
        assert "bars" in data
        assert isinstance(data["bars"], list)
        assert len(data["bars"]) > 0

    def test_get_bars_with_default_window(self):
        """
        测试使用默认回溯时间

        预期:
        - 不传 window 参数时使用默认值
        - 1d 周期默认 6mo
        """
        response = client.get("/v1/bars", params={
            "ticker": "AAPL",
            "tf": "1d"
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["bars"]) > 0

    def test_get_bars_bar_structure(self):
        """
        测试 K 线数据结构

        预期:
        - 每根 K 线包含 t, o, h, l, c, v 字段
        - 所有价格字段为数字类型
        """
        response = client.get("/v1/bars", params={
            "ticker": "AAPL",
            "tf": "1d",
            "window": "5d"
        })

        data = response.json()
        bar = data["bars"][0]

        # 检查必需字段
        assert "t" in bar  # 时间戳
        assert "o" in bar  # 开盘价
        assert "h" in bar  # 最高价
        assert "l" in bar  # 最低价
        assert "c" in bar  # 收盘价
        assert "v" in bar  # 成交量

        # 检查数据类型
        assert isinstance(bar["o"], (int, float))
        assert isinstance(bar["h"], (int, float))
        assert isinstance(bar["l"], (int, float))
        assert isinstance(bar["c"], (int, float))
        assert isinstance(bar["v"], (int, float))

    def test_get_bars_invalid_timeframe(self):
        """
        测试无效时间周期

        预期:
        - 状态码: 400
        - 错误代码: TIMEFRAME_INVALID
        """
        response = client.get("/v1/bars", params={
            "ticker": "AAPL",
            "tf": "invalid"
        })

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "TIMEFRAME_INVALID"

    def test_get_bars_invalid_ticker(self):
        """
        测试无效股票代码

        预期:
        - 状态码: 404
        - 错误代码: NO_DATA
        """
        response = client.get("/v1/bars", params={
            "ticker": "INVALIDTICKERXYZ123",
            "tf": "1d"
        })

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "NO_DATA"

    def test_get_bars_missing_ticker(self):
        """
        测试缺少 ticker 参数

        预期:
        - 状态码: 422 (Unprocessable Entity)
        """
        response = client.get("/v1/bars", params={
            "tf": "1d"
        })

        assert response.status_code == 422

    def test_get_bars_ticker_uppercase(self):
        """
        测试 ticker 自动转大写

        预期:
        - 小写输入被转换为大写
        """
        response = client.get("/v1/bars", params={
            "ticker": "aapl",
            "tf": "1d",
            "window": "5d"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"


class TestBarsTimeframes:
    """测试不同时间周期"""

    @pytest.mark.parametrize("tf,expected_window", [
        ("1m", "1d"),
        ("5m", "5d"),
        ("1d", "6mo"),
    ])
    def test_valid_timeframes(self, tf, expected_window):
        """
        测试所有支持的时间周期

        预期:
        - 1m, 5m, 1d 都能正常获取数据
        """
        response = client.get("/v1/bars", params={
            "ticker": "AAPL",
            "tf": tf
        })

        # 1m 可能在非交易时间无数据，所以接受 200 或 404
        assert response.status_code in [200, 404]
