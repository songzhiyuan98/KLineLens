"""
KLineLens 核心引擎测试配置

提供共享的测试夹具和合成数据生成器。
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import List
import sys
import os

# 添加 packages/core 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import Bar


def generate_uptrend_bars(n: int = 100, base_price: float = 100.0) -> List[Bar]:
    """
    生成上升趋势的合成 K 线（HH/HL 结构）

    参数:
        n: K 线数量
        base_price: 起始价格

    返回:
        Bar 列表
    """
    bars = []
    price = base_price
    start_time = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)

    for i in range(n):
        # 总体趋势向上，但有波动
        trend = 0.1  # 每根 K 线平均上涨 0.1
        noise = (i % 5 - 2) * 0.3  # 周期性波动

        o = price
        c = price + trend + noise
        h = max(o, c) + abs(noise) * 0.5
        l = min(o, c) - abs(noise) * 0.3
        v = 1000000 + (i % 10) * 100000

        bars.append(Bar(
            t=start_time + timedelta(minutes=i),
            o=round(o, 2),
            h=round(h, 2),
            l=round(l, 2),
            c=round(c, 2),
            v=float(v)
        ))

        price = c

    return bars


def generate_downtrend_bars(n: int = 100, base_price: float = 100.0) -> List[Bar]:
    """
    生成下降趋势的合成 K 线（LL/LH 结构）

    参数:
        n: K 线数量
        base_price: 起始价格

    返回:
        Bar 列表
    """
    bars = []
    price = base_price
    start_time = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)

    for i in range(n):
        # 总体趋势向下，但有波动
        trend = -0.1  # 每根 K 线平均下跌 0.1
        noise = (i % 5 - 2) * 0.3

        o = price
        c = price + trend + noise
        h = max(o, c) + abs(noise) * 0.3
        l = min(o, c) - abs(noise) * 0.5
        v = 1000000 + (i % 10) * 100000

        bars.append(Bar(
            t=start_time + timedelta(minutes=i),
            o=round(o, 2),
            h=round(h, 2),
            l=round(l, 2),
            c=round(c, 2),
            v=float(v)
        ))

        price = c

    return bars


def generate_range_bars(n: int = 100, base_price: float = 100.0, range_pct: float = 0.05) -> List[Bar]:
    """
    生成震荡行情的合成 K 线

    参数:
        n: K 线数量
        base_price: 中心价格
        range_pct: 波动范围（占基础价格的百分比）

    返回:
        Bar 列表
    """
    import math

    bars = []
    start_time = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)
    range_size = base_price * range_pct

    for i in range(n):
        # 使用正弦波模拟震荡
        phase = 2 * math.pi * i / 20  # 20 根 K 线一个周期
        mid_price = base_price + range_size * math.sin(phase)

        noise = (i % 3 - 1) * 0.2

        o = mid_price - noise
        c = mid_price + noise
        h = max(o, c) + abs(noise) * 0.5
        l = min(o, c) - abs(noise) * 0.5
        v = 800000 + (i % 8) * 50000

        bars.append(Bar(
            t=start_time + timedelta(minutes=i),
            o=round(o, 2),
            h=round(h, 2),
            l=round(l, 2),
            c=round(c, 2),
            v=float(v)
        ))

    return bars


def generate_breakout_sequence(n: int = 50, base_price: float = 100.0) -> List[Bar]:
    """
    生成突破模式的合成 K 线

    参数:
        n: K 线数量
        base_price: 基础价格

    返回:
        Bar 列表（包含区间震荡 + 向上突破 + 确认）
    """
    bars = []
    start_time = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)

    # 前 30 根：区间震荡
    for i in range(30):
        noise = (i % 5 - 2) * 0.3
        o = base_price + noise
        c = base_price - noise
        h = base_price + 2
        l = base_price - 2
        v = 1000000

        bars.append(Bar(
            t=start_time + timedelta(minutes=i),
            o=round(o, 2),
            h=round(h, 2),
            l=round(l, 2),
            c=round(c, 2),
            v=float(v)
        ))

    # 后 20 根：向上突破
    price = base_price + 2
    for i in range(20):
        o = price
        c = price + 0.5
        h = c + 0.3
        l = o - 0.2
        v = 2000000  # 放量

        bars.append(Bar(
            t=start_time + timedelta(minutes=30 + i),
            o=round(o, 2),
            h=round(h, 2),
            l=round(l, 2),
            c=round(c, 2),
            v=float(v)
        ))

        price = c

    return bars


def generate_shakeout_sequence(n: int = 30, base_price: float = 100.0) -> List[Bar]:
    """
    生成洗盘模式的合成 K 线（跌破支撑后快速收回）

    参数:
        n: K 线数量
        base_price: 基础价格（支撑位）

    返回:
        Bar 列表
    """
    bars = []
    start_time = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)

    # 前 20 根：在支撑位上方震荡
    for i in range(20):
        noise = (i % 3 - 1) * 0.3
        o = base_price + 1 + noise
        c = base_price + 1 - noise
        h = base_price + 2
        l = base_price + 0.5
        v = 1000000

        bars.append(Bar(
            t=start_time + timedelta(minutes=i),
            o=round(o, 2),
            h=round(h, 2),
            l=round(l, 2),
            c=round(c, 2),
            v=float(v)
        ))

    # 洗盘 K 线：跌破支撑后收回（长下影线）
    bars.append(Bar(
        t=start_time + timedelta(minutes=20),
        o=round(base_price + 0.5, 2),
        h=round(base_price + 1, 2),
        l=round(base_price - 1.5, 2),  # 跌破支撑
        c=round(base_price + 0.8, 2),   # 收回支撑上方
        v=2500000.0  # 放量
    ))

    # 后续恢复
    for i in range(n - 21):
        o = base_price + 1
        c = base_price + 1.5
        h = c + 0.3
        l = o - 0.2
        v = 1200000

        bars.append(Bar(
            t=start_time + timedelta(minutes=21 + i),
            o=round(o, 2),
            h=round(h, 2),
            l=round(l, 2),
            c=round(c, 2),
            v=float(v)
        ))

    return bars


# Pytest fixtures

@pytest.fixture
def uptrend_bars():
    """上升趋势 K 线夹具"""
    return generate_uptrend_bars(100)


@pytest.fixture
def downtrend_bars():
    """下降趋势 K 线夹具"""
    return generate_downtrend_bars(100)


@pytest.fixture
def range_bars():
    """震荡行情 K 线夹具"""
    return generate_range_bars(100)


@pytest.fixture
def breakout_bars():
    """突破模式 K 线夹具"""
    return generate_breakout_sequence(50)


@pytest.fixture
def shakeout_bars():
    """洗盘模式 K 线夹具"""
    return generate_shakeout_sequence(30)


@pytest.fixture
def minimal_bars():
    """最小 K 线数量夹具（用于边界测试）"""
    return generate_uptrend_bars(20)
