# KLineLens MVP - Architecture

## 1) 总览
MVP采用 Monorepo + 三层结构：
- Web（Next.js）：页面渲染、图表、语言设置
- API（FastAPI）：数据获取与分析接口
- Core Engine（Python package）：结构/行为/叙事核心算法（可单测）

## 2) 目录结构建议
kline-lens/
  apps/
    web/
    api/
  packages/
    core/
  Docs/
  infra/

## 3) 数据流
1. Web 请求 bars：`GET /v1/bars`
2. Web 请求分析：`POST /v1/analyze`
3. API：
   - 调用 MarketDataProvider 拉取 OHLCV（可缓存）
   - 调用 core.analyze_market(bars, params)
   - 返回 AnalysisReport JSON
4. Web 渲染：
   - 图表：bars + overlays（zones/markers）
   - 面板：report（state/behavior/timeline/playbook）

## 4) 缓存策略（MVP最小）
- 内存缓存：ticker+tf+window -> bars（TTL 30~60s）
- （可选）Redis：多实例部署时共享缓存
- timeline state：MVP可先内存；后续迁移 Redis

## 5) 可扩展点（为V1/V2留口）
- 多数据源 provider：provider abstraction
- worker 预计算：定时刷新 bars、预生成 report
- snapshots/replay：存 Postgres 形成复盘功能
- LLM narration：在 report JSON 之上生成自然语言，不影响算法 determinism
