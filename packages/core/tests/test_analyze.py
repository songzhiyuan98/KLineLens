"""
analyze.py 模块集成测试

测试完整的分析流程和 AnalysisReport 输出。
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analyze import analyze_market, create_initial_state, AnalysisParams
from src.models import AnalysisReport
from tests.conftest import generate_uptrend_bars, generate_downtrend_bars, generate_range_bars


class TestAnalyzeMarket:
    """市场分析集成测试"""

    def test_returns_analysis_report(self):
        """应返回 AnalysisReport 对象"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        assert isinstance(report, AnalysisReport)

    def test_report_has_all_required_fields(self):
        """报告应包含所有必需字段"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        assert report.ticker == "TEST"
        assert report.tf == "1d"
        assert report.generated_at is not None
        assert report.bar_count == len(bars)
        assert isinstance(report.data_gaps, bool)
        assert report.market_state is not None
        assert report.zones is not None
        assert report.signals is not None
        assert report.behavior is not None
        assert report.timeline is not None
        assert report.playbook is not None

    def test_market_state_is_valid(self):
        """市场状态应有效"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        assert report.market_state.regime in ["uptrend", "downtrend", "range"]
        assert 0 <= report.market_state.confidence <= 1

    def test_zones_structure_is_valid(self):
        """区域结构应有效"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        assert "support" in report.zones
        assert "resistance" in report.zones

    def test_behavior_probabilities_sum_to_one(self):
        """行为概率应总和为 1"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        total_prob = sum(report.behavior.probabilities.values())
        assert abs(total_prob - 1.0) < 0.01  # 允许小误差

    def test_behavior_has_dominant(self):
        """应有主导行为"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        assert report.behavior.dominant in report.behavior.probabilities
        # 主导行为应该是概率最高的
        max_prob = max(report.behavior.probabilities.values())
        assert report.behavior.probabilities[report.behavior.dominant] == max_prob

    def test_ticker_is_uppercased(self):
        """股票代码应转为大写"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="test", timeframe="1d")

        assert report.ticker == "TEST"

    def test_raises_on_insufficient_bars(self):
        """K 线不足时应抛出异常"""
        bars = generate_uptrend_bars(5)

        with pytest.raises(ValueError):
            analyze_market(bars, ticker="TEST", timeframe="1d")

    def test_works_with_minimal_bars(self):
        """应能处理最小数量的 K 线"""
        bars = generate_uptrend_bars(20)  # 刚好够 ATR 计算
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        assert report is not None
        assert report.bar_count == 20

    def test_different_timeframes(self):
        """应支持不同时间周期"""
        bars = generate_uptrend_bars(100)

        for tf in ["1m", "5m", "1d"]:
            report = analyze_market(bars, ticker="TEST", timeframe=tf)
            assert report.tf == tf

    def test_playbook_has_valid_plans(self):
        """Playbook 应有有效的计划"""
        bars = generate_uptrend_bars(100)
        report = analyze_market(bars, ticker="TEST", timeframe="1d")

        # Playbook 可能为空，但如果有计划，应该有效
        for plan in report.playbook:
            assert plan.name is not None
            assert plan.condition is not None
            assert plan.level > 0
            # 目标和失效应该在合理范围内
            assert plan.target != plan.invalidation


class TestAnalysisParams:
    """分析参数测试"""

    def test_default_params(self):
        """默认参数应有合理值"""
        params = AnalysisParams()

        assert params.atr_period == 14
        assert params.volume_period == 30
        assert params.swing_n == 4
        assert params.volume_threshold == 1.8

    def test_custom_params(self):
        """应能使用自定义参数"""
        bars = generate_uptrend_bars(100)
        params = AnalysisParams(
            atr_period=10,
            swing_n=3
        )

        report = analyze_market(bars, ticker="TEST", timeframe="1d", params=params)
        assert report is not None


class TestCreateInitialState:
    """初始状态创建测试"""

    def test_creates_valid_state(self):
        """应创建有效的初始状态"""
        state = create_initial_state()

        assert state.breakout_fsm is not None
        assert state.timeline_manager is not None
        assert state.timeline_state is None

    def test_state_can_be_reused(self):
        """状态应能跨调用重用"""
        bars = generate_uptrend_bars(100)
        state = create_initial_state()

        # 第一次分析
        report1 = analyze_market(bars, ticker="TEST", timeframe="1d", state=state)

        # 添加更多 K 线（模拟增量更新）
        more_bars = generate_uptrend_bars(110)[10:]  # 前 10 根不同
        report2 = analyze_market(more_bars, ticker="TEST", timeframe="1d", state=state)

        # 两个报告都应有效
        assert report1 is not None
        assert report2 is not None


class TestDeterminism:
    """确定性测试"""

    def test_same_input_same_output(self):
        """相同输入应产生相同输出"""
        bars = generate_uptrend_bars(100)

        report1 = analyze_market(bars, ticker="TEST", timeframe="1d")
        report2 = analyze_market(bars, ticker="TEST", timeframe="1d")

        # 核心字段应相同
        assert report1.market_state.regime == report2.market_state.regime
        assert report1.behavior.dominant == report2.behavior.dominant
        assert report1.behavior.probabilities == report2.behavior.probabilities
