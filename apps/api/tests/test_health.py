"""
健康检查端点测试

测试 GET / 端点是否正常工作。
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


# 创建测试客户端
client = TestClient(app)


class TestHealthEndpoint:
    """健康检查端点测试类"""

    def test_health_check_returns_ok(self):
        """
        测试健康检查返回正常状态

        预期:
        - 状态码: 200
        - 响应包含 status: "ok"
        """
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "klinelens-api"
        assert "provider" in data

    def test_health_check_returns_provider_name(self):
        """
        测试健康检查返回提供者名称

        预期:
        - 响应包含 provider 字段
        - provider 值为 "yfinance"
        """
        response = client.get("/")
        data = response.json()

        assert data["provider"] == "yfinance"
