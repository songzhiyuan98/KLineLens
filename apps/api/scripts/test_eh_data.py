#!/usr/bin/env python3
"""
测试 Extended Hours 数据获取

验证 TwelveData prepost=true 参数是否能返回盘前盘后数据。
"""

import os
import sys
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.providers import TwelveDataProvider, segment_bars_by_session, get_yesterday_sessions
from src.config import settings


def main():
    # 检查 API Key
    api_key = settings.twelvedata_api_key
    if not api_key:
        print("错误: 请设置 TWELVEDATA_API_KEY 环境变量")
        return 1

    print(f"使用 TwelveData API Key: {api_key[:8]}...")
    print()

    # 创建 provider
    provider = TwelveDataProvider(api_key=api_key)

    # 测试获取 TSLA 的 Extended Hours 数据
    ticker = "TSLA"
    print(f"获取 {ticker} 的 Extended Hours 数据 (2天, 1分钟线)...")
    print()

    try:
        bars = provider.get_bars_extended(ticker, "1m", "2d")
        print(f"✅ 成功获取 {len(bars)} 根 K 线")
        print()

        # 显示时间范围
        if bars:
            print(f"时间范围: {bars[0].t} 到 {bars[-1].t}")
            print()

        # 按时段分割
        segmented = segment_bars_by_session(bars)
        print(f"按日期分割: {list(segmented.keys())}")
        print()

        # 统计各时段数据
        for date_str, session in sorted(segmented.items()):
            pm_count = len(session.premarket)
            reg_count = len(session.regular)
            ah_count = len(session.afterhours)
            print(f"  {date_str}:")
            print(f"    盘前 (04:00-09:30): {pm_count} bars")
            print(f"    正盘 (09:30-16:00): {reg_count} bars")
            print(f"    盘后 (16:00-20:00): {ah_count} bars")
            print()

        # 获取昨日和今日
        yesterday, today = get_yesterday_sessions(segmented)

        if yesterday:
            print("昨日数据:")
            if yesterday.regular:
                yc = yesterday.regular[-1].c
                yh = max(b.h for b in yesterday.regular)
                yl = min(b.l for b in yesterday.regular)
                print(f"  YC (昨收): {yc:.2f}")
                print(f"  YH (昨高): {yh:.2f}")
                print(f"  YL (昨低): {yl:.2f}")
            if yesterday.afterhours:
                ahh = max(b.h for b in yesterday.afterhours)
                ahl = min(b.l for b in yesterday.afterhours)
                print(f"  AHH (盘后高): {ahh:.2f}")
                print(f"  AHL (盘后低): {ahl:.2f}")
            print()

        if today:
            print("今日数据:")
            if today.premarket:
                pmh = max(b.h for b in today.premarket)
                pml = min(b.l for b in today.premarket)
                print(f"  PMH (盘前高): {pmh:.2f}")
                print(f"  PML (盘前低): {pml:.2f}")
            else:
                print("  盘前数据不可用 (可能需要 Pro 版本或 T-1 延迟)")
            print()

        print("✅ Extended Hours 数据测试完成!")
        return 0

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
