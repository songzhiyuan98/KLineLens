#!/usr/bin/env python3
"""
Extended Hours 功能测试脚本

测试 YFinance prepost 数据获取。

运行方式:
    cd apps/api
    python3 scripts/test_eh.py
"""

import yfinance as yf
from datetime import datetime


def test_yfinance_prepost():
    """测试 YFinance prepost 参数"""
    print("=" * 60)
    print("测试 YFinance Extended Hours 数据获取")
    print("=" * 60)

    ticker = "TSLA"
    print(f"\n获取 {ticker} 的 Extended Hours 数据...\n")

    try:
        stock = yf.Ticker(ticker)

        # 获取带 prepost 的数据
        df = stock.history(period="2d", interval="1m", prepost=True)

        if df.empty:
            print("❌ 无数据返回")
            return

        print(f"✅ 成功获取 {len(df)} 根 K 线")

        # 统计各时段
        premarket = 0
        regular = 0
        afterhours = 0

        for idx in df.index:
            ts = idx.to_pydatetime()
            hour = ts.hour
            minute = ts.minute
            time_minutes = hour * 60 + minute

            if 240 <= time_minutes < 570:  # 04:00 - 09:30
                premarket += 1
            elif 570 <= time_minutes < 960:  # 09:30 - 16:00
                regular += 1
            elif 960 <= time_minutes <= 1200:  # 16:00 - 20:00
                afterhours += 1

        print(f"\n📊 时段统计:")
        print(f"   盘前 (04:00-09:30): {premarket} bars")
        print(f"   正盘 (09:30-16:00): {regular} bars")
        print(f"   盘后 (16:00-20:00): {afterhours} bars")

        # 显示日期分布
        dates = df.index.date
        unique_dates = sorted(set(dates))
        print(f"\n📅 日期覆盖: {unique_dates}")

        # 显示样本数据
        print(f"\n📈 样本数据:")
        print(f"   最早: {df.index[0]}")
        print(f"          O:{df.iloc[0]['Open']:.2f} H:{df.iloc[0]['High']:.2f} L:{df.iloc[0]['Low']:.2f} C:{df.iloc[0]['Close']:.2f}")
        print(f"   最新: {df.index[-1]}")
        print(f"          O:{df.iloc[-1]['Open']:.2f} H:{df.iloc[-1]['High']:.2f} L:{df.iloc[-1]['Low']:.2f} C:{df.iloc[-1]['Close']:.2f}")

        # 计算关键位
        if len(unique_dates) >= 2:
            yesterday = unique_dates[-2]
            today = unique_dates[-1]

            yesterday_df = df[df.index.date == yesterday]
            today_df = df[df.index.date == today]

            # 分离时段
            yesterday_regular = yesterday_df[
                (yesterday_df.index.hour >= 9) &
                ((yesterday_df.index.hour < 16) | ((yesterday_df.index.hour == 9) & (yesterday_df.index.minute >= 30)))
            ]
            yesterday_ah = yesterday_df[yesterday_df.index.hour >= 16]
            today_pm = today_df[
                (today_df.index.hour < 9) |
                ((today_df.index.hour == 9) & (today_df.index.minute < 30))
            ]

            print(f"\n🎯 关键位提取:")

            if len(yesterday_regular) > 0:
                yc = yesterday_regular.iloc[-1]['Close']
                yh = yesterday_regular['High'].max()
                yl = yesterday_regular['Low'].min()
                print(f"   YC (昨收): ${yc:.2f}")
                print(f"   YH (昨高): ${yh:.2f}")
                print(f"   YL (昨低): ${yl:.2f}")

            if len(yesterday_ah) > 0:
                ahh = yesterday_ah['High'].max()
                ahl = yesterday_ah['Low'].min()
                print(f"   AHH (盘后高): ${ahh:.2f}")
                print(f"   AHL (盘后低): ${ahl:.2f}")
            else:
                print(f"   AHH/AHL: 无盘后数据")

            if len(today_pm) > 0:
                pmh = today_pm['High'].max()
                pml = today_pm['Low'].min()
                print(f"   PMH (盘前高): ${pmh:.2f}")
                print(f"   PML (盘前低): ${pml:.2f}")

                if len(yesterday_regular) > 0:
                    gap = today_pm.iloc[-1]['Close'] - yc
                    gap_pct = gap / yc * 100
                    print(f"   GAP (缺口): ${gap:+.2f} ({gap_pct:+.2f}%)")
            else:
                print(f"   PMH/PML: 无盘前数据")

        print("\n✅ 测试完成")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🧪 Extended Hours (EH) 功能测试\n")
    test_yfinance_prepost()
    print()
