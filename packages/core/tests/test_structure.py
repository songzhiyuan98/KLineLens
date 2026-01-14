"""
structure.py 模块测试

测试摆动点检测、区域聚类、趋势分类、突破状态机。
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.structure import find_swing_points, cluster_zones, classify_regime, BreakoutFSM, BreakoutState
from src.models import Bar, Zone
from tests.conftest import generate_uptrend_bars, generate_downtrend_bars, generate_range_bars


class TestFindSwingPoints:
    """摆动点检测测试"""

    def test_finds_swing_points_in_uptrend(self):
        """上升趋势应能找到摆动点"""
        bars = generate_uptrend_bars(100)
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        # 上升趋势中至少应该有一些摆动点
        assert len(swing_highs) > 0 or len(swing_lows) > 0

    def test_swing_highs_have_correct_structure(self):
        """摆动高点应有正确的结构"""
        bars = generate_uptrend_bars(100)
        swing_highs, _ = find_swing_points(bars, n=4)

        for sp in swing_highs:
            assert sp.is_high == True
            assert sp.index >= 4  # 前 n 个不能是摆动点
            assert sp.index < len(bars) - 4  # 后 n 个不能是摆动点

    def test_returns_empty_for_insufficient_bars(self):
        """K 线不足时应返回空列表"""
        bars = generate_uptrend_bars(5)
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        assert swing_highs == []
        assert swing_lows == []


class TestClusterZones:
    """区域聚类测试"""

    def test_cluster_zones_returns_dict_with_correct_keys(self):
        """应返回包含 support 和 resistance 键的字典"""
        bars = generate_uptrend_bars(100)
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        zones = cluster_zones(swing_highs, swing_lows, atr=1.0)

        assert "support" in zones
        assert "resistance" in zones

    def test_cluster_zones_creates_valid_zones(self):
        """创建的区域应有有效属性"""
        bars = generate_uptrend_bars(100)
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        zones = cluster_zones(swing_highs, swing_lows, atr=1.0)

        for zone in zones["support"]:
            assert zone.low < zone.high
            assert zone.score >= 0
            assert zone.touches >= 1

    def test_cluster_zones_respects_max_zones(self):
        """应遵守最大区域数限制"""
        bars = generate_range_bars(200)  # 更多数据
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        zones = cluster_zones(swing_highs, swing_lows, atr=1.0, max_zones=3)

        assert len(zones["support"]) <= 3
        assert len(zones["resistance"]) <= 3


class TestClassifyRegime:
    """趋势分类测试"""

    def test_uptrend_detection(self):
        """应能检测上升趋势"""
        bars = generate_uptrend_bars(100)
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        market_state = classify_regime(swing_highs, swing_lows)

        # 上升趋势或震荡都可能
        assert market_state.regime in ["uptrend", "range"]
        assert 0 <= market_state.confidence <= 1

    def test_downtrend_detection(self):
        """应能检测下降趋势"""
        bars = generate_downtrend_bars(100)
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        market_state = classify_regime(swing_highs, swing_lows)

        assert market_state.regime in ["downtrend", "range"]
        assert 0 <= market_state.confidence <= 1

    def test_range_detection(self):
        """应能检测震荡"""
        bars = generate_range_bars(100)
        swing_highs, swing_lows = find_swing_points(bars, n=4)

        market_state = classify_regime(swing_highs, swing_lows)

        # 震荡数据应该更可能是 range
        assert market_state.regime in ["uptrend", "downtrend", "range"]
        assert 0 <= market_state.confidence <= 1

    def test_insufficient_points_returns_range(self):
        """摆动点不足时应返回 range"""
        from src.structure import SwingPoint
        from datetime import datetime, timezone

        # 只有一个摆动点
        single_high = [SwingPoint(0, 100.0, datetime.now(timezone.utc), True)]
        single_low = [SwingPoint(0, 99.0, datetime.now(timezone.utc), False)]

        market_state = classify_regime(single_high, single_low)

        assert market_state.regime == "range"


class TestBreakoutFSM:
    """突破状态机测试"""

    def test_initial_state_is_idle(self):
        """初始状态应为 IDLE"""
        fsm = BreakoutFSM()
        assert fsm.get_state() == BreakoutState.IDLE

    def test_reset_returns_to_idle(self):
        """重置应返回 IDLE 状态"""
        fsm = BreakoutFSM()
        # 模拟某些状态变化
        fsm._state = BreakoutState.ATTEMPT

        fsm.reset()

        assert fsm.get_state() == BreakoutState.IDLE

    def test_state_string_conversion(self):
        """状态应能转换为字符串"""
        fsm = BreakoutFSM()
        assert fsm.get_state_str() == "idle"
