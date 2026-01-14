# KLineLens MVP - Test Plan

## 1) 单元测试（Core）
- swing points: 给固定 bars，输出 swing 数量与关键点位置稳定
- zones: 给固定 swing prices，聚类输出 zones 稳定（top zone 价格带不漂）
- regime: 人工构造 HH/HL 序列应判 uptrend；LL/LH 判 downtrend；混合判 range
- breakout state: 构造 attempt->confirmed 与 attempt->fakeout 两种序列验证状态机
- behavior: 构造“刺破支撑后收回 + 放量”的 bars，shakeout 概率应高于其他类

## 2) 集成测试（API）
- /bars：有效 ticker 返回 bars；无效 ticker 返回 TICKER_INVALID
- /analyze：返回必需字段不为空，zones/support/resistance 至少 1 个（有数据时）

## 3) 前端冒烟测试
- Dashboard 输入 ticker -> 详情页
- 切 timeframe 更新
- Settings 切语言全站更新
- 自动刷新不报错
