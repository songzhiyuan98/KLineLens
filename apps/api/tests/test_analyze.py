"""
/v1/analyze 端点测试

测试市场分析 API 的完整集成。
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestAnalyzeEndpoint:
    """分析端点测试"""

    def test_analyze_success(self):
        """成功的分析请求应返回完整报告"""
        # 使用 mock 数据避免真实 API 调用
        mock_bars = self._generate_mock_bars(50)

        with patch('src.main.provider.get_bars', return_value=mock_bars):
            with patch('src.main.cache.get', return_value=None):
                response = client.post(
                    "/v1/analyze",
                    json={"ticker": "TSLA", "tf": "1d"}
                )

        assert response.status_code == 200
        data = response.json()

        # 验证报告结构
        assert data["ticker"] == "TSLA"
        assert data["tf"] == "1d"
        assert "generated_at" in data
        assert data["bar_count"] == 50
        assert "market_state" in data
        assert "zones" in data
        assert "signals" in data
        assert "behavior" in data
        assert "timeline" in data
        assert "playbook" in data

    def test_analyze_market_state_structure(self):
        """市场状态应有正确结构"""
        mock_bars = self._generate_mock_bars(50)

        with patch('src.main.provider.get_bars', return_value=mock_bars):
            with patch('src.main.cache.get', return_value=None):
                response = client.post(
                    "/v1/analyze",
                    json={"ticker": "AAPL", "tf": "1d"}
                )

        data = response.json()
        market_state = data["market_state"]

        assert "regime" in market_state
        assert market_state["regime"] in ["uptrend", "downtrend", "range"]
        assert "confidence" in market_state
        assert 0 <= market_state["confidence"] <= 1

    def test_analyze_behavior_structure(self):
        """行为推断应有正确结构"""
        mock_bars = self._generate_mock_bars(50)

        with patch('src.main.provider.get_bars', return_value=mock_bars):
            with patch('src.main.cache.get', return_value=None):
                response = client.post(
                    "/v1/analyze",
                    json={"ticker": "MSFT", "tf": "1d"}
                )

        data = response.json()
        behavior = data["behavior"]

        assert "probabilities" in behavior
        assert "dominant" in behavior
        assert "evidence" in behavior

        # 概率应总和为 1
        probs = behavior["probabilities"]
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01

    def test_analyze_zones_structure(self):
        """区域应有正确结构"""
        mock_bars = self._generate_mock_bars(100)

        with patch('src.main.provider.get_bars', return_value=mock_bars):
            with patch('src.main.cache.get', return_value=None):
                response = client.post(
                    "/v1/analyze",
                    json={"ticker": "GOOG", "tf": "1d"}
                )

        data = response.json()
        zones = data["zones"]

        assert "support" in zones
        assert "resistance" in zones
        assert isinstance(zones["support"], list)
        assert isinstance(zones["resistance"], list)

    def test_analyze_invalid_timeframe(self):
        """无效时间周期应返回 400"""
        response = client.post(
            "/v1/analyze",
            json={"ticker": "TSLA", "tf": "invalid"}
        )

        assert response.status_code == 400
        assert "TIMEFRAME_INVALID" in response.json()["detail"]["code"]

    def test_analyze_invalid_ticker(self):
        """无效股票代码应返回 404"""
        from src.providers import TickerNotFoundError

        with patch('src.main.provider.get_bars', side_effect=TickerNotFoundError("无效代码")):
            with patch('src.main.cache.get', return_value=None):
                response = client.post(
                    "/v1/analyze",
                    json={"ticker": "INVALID_XXX", "tf": "1d"}
                )

        assert response.status_code == 404
        assert "NO_DATA" in response.json()["detail"]["code"]

    def test_analyze_insufficient_bars(self):
        """K 线不足应返回 400"""
        mock_bars = self._generate_mock_bars(5)  # 太少

        with patch('src.main.provider.get_bars', return_value=mock_bars):
            with patch('src.main.cache.get', return_value=None):
                response = client.post(
                    "/v1/analyze",
                    json={"ticker": "TSLA", "tf": "1d"}
                )

        assert response.status_code == 400
        assert "ANALYSIS_ERROR" in response.json()["detail"]["code"]

    def test_analyze_ticker_uppercased(self):
        """股票代码应转为大写"""
        mock_bars = self._generate_mock_bars(50)

        with patch('src.main.provider.get_bars', return_value=mock_bars):
            with patch('src.main.cache.get', return_value=None):
                response = client.post(
                    "/v1/analyze",
                    json={"ticker": "tsla", "tf": "1d"}
                )

        assert response.status_code == 200
        assert response.json()["ticker"] == "TSLA"

    def _generate_mock_bars(self, n: int):
        """生成模拟 K 线数据"""
        from src.providers.base import Bar

        bars = []
        base_price = 100.0
        start_time = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)

        for i in range(n):
            # 模拟上升趋势
            price = base_price + i * 0.1
            noise = (i % 5 - 2) * 0.3

            bars.append(Bar(
                t=start_time + timedelta(minutes=i),
                o=price,
                h=price + abs(noise) + 0.5,
                l=price - abs(noise) - 0.3,
                c=price + noise,
                v=1000000 + i * 10000
            ))

        return bars
