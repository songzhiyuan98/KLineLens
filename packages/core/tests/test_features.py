"""
features.py 模块测试

测试 ATR、成交量比率、影线比率、效率指标计算。
"""

import pytest
import numpy as np
import sys
import os

# 添加 packages/core 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features import calculate_atr, calculate_volume_ratio, calculate_wick_ratios, calculate_efficiency, calculate_features
from src.models import Bar

# 从 conftest.py 导入（pytest 自动加载）
from tests.conftest import generate_uptrend_bars


class TestCalculateATR:
    """ATR 计算测试"""

    def test_atr_returns_correct_length(self):
        """ATR 数组长度应与输入相同"""
        bars = generate_uptrend_bars(50)
        atr = calculate_atr(bars, period=14)
        assert len(atr) == len(bars)

    def test_atr_first_values_are_nan(self):
        """前 period 个值应为 NaN"""
        bars = generate_uptrend_bars(50)
        atr = calculate_atr(bars, period=14)
        assert np.all(np.isnan(atr[:14]))

    def test_atr_has_valid_values_after_period(self):
        """period 之后应有有效值"""
        bars = generate_uptrend_bars(50)
        atr = calculate_atr(bars, period=14)
        assert not np.isnan(atr[14])
        assert atr[14] > 0

    def test_atr_raises_on_insufficient_bars(self):
        """K 线不足时应抛出异常"""
        bars = generate_uptrend_bars(10)
        with pytest.raises(ValueError):
            calculate_atr(bars, period=14)


class TestCalculateVolumeRatio:
    """成交量比率测试"""

    def test_volume_ratio_returns_correct_length(self):
        """成交量比率数组长度应与输入相同"""
        bars = generate_uptrend_bars(50)
        vol_ratio = calculate_volume_ratio(bars, period=30)
        assert len(vol_ratio) == len(bars)

    def test_volume_ratio_is_around_one_for_stable_volume(self):
        """稳定成交量时比率应接近 1"""
        bars = generate_uptrend_bars(50)
        vol_ratio = calculate_volume_ratio(bars, period=30)
        # 最后几个值应该接近 1
        valid_ratios = vol_ratio[~np.isnan(vol_ratio)]
        assert np.mean(valid_ratios) > 0.5  # 应该是正数
        assert np.mean(valid_ratios) < 3.0  # 不应该太极端


class TestCalculateWickRatios:
    """影线比率测试"""

    def test_wick_ratios_in_valid_range(self):
        """影线比率应在 [0, 1] 范围内"""
        bars = generate_uptrend_bars(10)
        for bar in bars:
            wick_up, wick_low = calculate_wick_ratios(bar)
            assert 0 <= wick_up <= 1
            assert 0 <= wick_low <= 1

    def test_doji_returns_half_half(self):
        """十字星应返回 0.5, 0.5"""
        from datetime import datetime, timezone
        doji = Bar(
            t=datetime.now(timezone.utc),
            o=100.0,
            h=100.0,
            l=100.0,
            c=100.0,
            v=1000.0
        )
        wick_up, wick_low = calculate_wick_ratios(doji)
        assert wick_up == 0.5
        assert wick_low == 0.5


class TestCalculateEfficiency:
    """效率指标测试"""

    def test_bullish_bar_has_up_efficiency(self):
        """阳线应有正的上涨效率"""
        from datetime import datetime, timezone
        bullish = Bar(
            t=datetime.now(timezone.utc),
            o=100.0,
            h=102.0,
            l=99.0,
            c=101.5,
            v=1000000.0
        )
        up_eff, down_eff = calculate_efficiency(bullish, bullish.v)
        assert up_eff > 0
        assert down_eff == 0

    def test_bearish_bar_has_down_efficiency(self):
        """阴线应有正的下跌效率"""
        from datetime import datetime, timezone
        bearish = Bar(
            t=datetime.now(timezone.utc),
            o=101.0,
            h=102.0,
            l=99.0,
            c=99.5,
            v=1000000.0
        )
        up_eff, down_eff = calculate_efficiency(bearish, bearish.v)
        assert up_eff == 0
        assert down_eff > 0

    def test_zero_volume_returns_zero(self):
        """零成交量应返回零效率"""
        from datetime import datetime, timezone
        bar = Bar(
            t=datetime.now(timezone.utc),
            o=100.0,
            h=101.0,
            l=99.0,
            c=100.5,
            v=0.0
        )
        up_eff, down_eff = calculate_efficiency(bar, 0)
        assert up_eff == 0
        assert down_eff == 0


class TestCalculateFeatures:
    """综合特征计算测试"""

    def test_calculate_features_returns_all_keys(self):
        """应返回所有必需的键"""
        bars = generate_uptrend_bars(50)
        features = calculate_features(bars)

        required_keys = ['atr', 'volume_ratio', 'wick_up', 'wick_low',
                         'up_eff', 'down_eff', 'close', 'high', 'low', 'volume']
        for key in required_keys:
            assert key in features

    def test_calculate_features_arrays_same_length(self):
        """所有数组长度应相同"""
        bars = generate_uptrend_bars(50)
        features = calculate_features(bars)

        for key, arr in features.items():
            assert len(arr) == len(bars), f"{key} 长度不匹配"
