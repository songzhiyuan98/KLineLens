# KLineLens MVP - Plan

## Milestone 0: Repo & Infra
- monorepo 初始化
- web/api/core 基础运行
- 环境变量与配置

## Milestone 1: Market Data
- Provider 接入（先一个）
- GET /v1/bars
- 基础缓存、错误处理

## Milestone 2: Core Structure
- swing points
- zones（support/resistance）
- regime（trend/range）
- breakout state machine

## Milestone 3: Behavior + Timeline + Playbook
- behavior scores -> probabilities
- evidence pack
- stateful timeline（内存版）
- playbook 模板

## Milestone 4: Web Terminal + Settings Language
- Dashboard 大搜索框 -> /t/{ticker}
- Detail 图表 + overlays + 面板卡片
- /settings 语言切换（localStorage）
- 每60秒刷新 analyze

## MVP验收标准
- / 输入 ticker 可进入详情页
- 1m K线展示 + zones + signals
- 行为概率 + 证据 + timeline + playbook 全部可见
- Settings 切换语言全站生效
