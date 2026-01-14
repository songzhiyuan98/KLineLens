# KLineLens MVP - PRD（产品需求文档）

## 1. 背景与目标
### 1.1 背景
用户（短线交易者）经常通过截图 1 分钟 K 线给 LLM 解读盘面结构（趋势/震荡、支撑阻力、放量、洗盘/吸筹/派发等）。当前流程存在明显痛点：
- 输入成本高：每分钟截图、发送、等待回复
- 缺连续性：LLM无法稳定“继承上一分钟结构状态”，容易断片
- 缺可视化与证据：解读缺少可追溯的指标/证据展示
- 缺结构化输出：难以沉淀为可回放、可比较的“结构状态时间线”

### 1.2 产品目标（MVP）
KLineLens MVP 目标是：  
用户输入股票代码（Ticker），系统自动拉取分钟/日线 OHLCV 数据，并输出：
1) **结构识别**：趋势/震荡状态、关键支撑阻力 Zone、突破/假突破状态  
2) **行为推断（概率解释）**：吸筹/洗盘/拉升/派发/砸盘的概率 + 证据点  
3) **连续叙事（Stateful Timeline）**：记录最近 N 次结构/行为的变化与原因  
4) **交易剧本（条件式）**：Plan A/B（触发条件、目标位、失效线、风险提示）  
并以极简页面展示，不做登录注册。

### 1.3 非目标（MVP明确不做）
- 登录/注册/用户体系
- 新闻/社媒情绪面（Reddit/X）
- Level2/逐笔成交（订单流）深度推断
- 回测面板（可后续做）
- “确定性喊单”（必须是条件式 + 失效条件 + 概率解释）

---

## 2. 用户与场景
### 2.1 核心用户
- 高频短线交易者：常盯 1m/5m K线
- 波动股/小盘票交易者：关注量价结构和关键位
- 需要“盘面叙事”辅助决策的人：希望快速得到结构解释与风险边界

### 2.2 核心场景（MVP覆盖）
1) 盘中打开网站输入 ticker，进入详情页，查看当前 1m 结构解读  
2) 每 60 秒自动更新一次，观察结构是否从“震荡→突破尝试→确认/失败”演化  
3) 用户切换周期（1m/5m/1d）观察高周期关键位与低周期执行对齐  
4) 用户看“时间线”理解：为什么系统说“洗盘概率上升/派发概率上升”

---

## 3. 产品信息架构与页面
### 3.1 页面列表（MVP）
- `/` Dashboard：大搜索框（Ticker）
- `/t/{ticker}` Detail：K线 + 分析面板（结构/行为/证据/时间线/剧本）
- `/settings` Settings：语言选择（中文/English）

### 3.2 Dashboard 页面（/）
**需求**
- 输入框支持 ticker（大小写不敏感）
- 支持搜索建议（可选）：输入时显示常见 ticker（MVP可不做）
- 搜索后跳转详情页 `/t/TSLA`
- 右上角入口：Settings（语言切换）

**验收**
- 输入合法 ticker（字母+可选点/短横）跳转成功
- 空输入/非法格式显示提示（不跳转）

### 3.3 Detail 页面（/t/{ticker}）
**布局原则：极简、专业、信息密度高但清爽**
- 主体为 Chart + Analysis Panel
- 默认时间周期：1m（window=1d）
- 自动刷新：每 60 秒刷新 analyze（bars可按需要刷新或缓存）

**展示内容（必须）**
A. Chart
- K线（OHLC）
- 成交量柱
- 支撑/阻力 Zone overlay（矩形/带状）
- Breakout/Fakeout Marker（标注点/段）

B. Analysis Panel（卡片式）
1) Market State
   - Regime：Uptrend / Downtrend / Range
   - Confidence（0-1）
   - Key Zones（Top 2 支撑 + Top 2 阻力）

2) Behavior Probabilities（五类）
   - Accumulation（吸筹）
   - Shakeout（洗盘）
   - Markup（拉升）
   - Distribution（派发）
   - Markdown（砸盘）
   - Dominant Narrative（主叙事：取最高概率）

3) Evidence（证据点，最多 3 条）
   - 每条证据必须关联 bar_time + 关键数值（volume_ratio / wick_ratio / reclaim 等）
   - 证据文本必须基于规则模板（非拍脑袋）

4) Timeline（最近 N 条事件）
   - 事件类型（例如：shakeout_prob_up）
   - 概率变化 delta
   - 原因 reason_key（前端按语言渲染）
   - 时间戳

5) Playbook（Plan A / Plan B）
   - 条件式（If…）
   - 目标位（Target）
   - 失效线（Invalidation）
   - 风险提示（Risk）

**交互（必须）**
- Timeframe 切换（至少：1m / 1d；可加 5m）
- Refresh 状态提示（last updated 时间）
- 错误态：数据获取失败/限流/无数据

**验收**
- 输入 ticker 后 10 秒内可以看到图表与报告（在 provider 正常情况下）
- 每 60 秒更新时，timeline 会新增事件或提示“无明显变化”
- 切换 timeframe 会刷新 bars + report，显示对应关键位

### 3.4 Settings 页面（/settings）
**需求**
- 选择语言：中文 / English
- 保存为本地持久化（localStorage 或 cookie）
- 切回任意页面立即生效
- 默认语言：中文（可配置）

---

## 4. 功能需求（MVP范围）
### 4.1 行情数据获取
- 支持输入 ticker 拉取 OHLCV bars
- 支持 timeframe：1m、1d（MVP必需）
- window：1d（1m）/ 6mo（1d）等（可配置默认）

**非功能**
- 缓存：同 ticker+tf+window 在短时间内复用（减少限流）
- 失败重试：provider 出错可重试一次
- 错误提示：明确原因（限流/无权限/无数据）

### 4.2 结构识别（Structure）
输出：
- swing points（用于结构骨架）
- regime（trend/range + confidence）
- zones（支撑阻力：价格带 + score）
- breakout_state（attempt/confirmed/fakeout 等）
- signals（突破/拒绝/假突破标记）

### 4.3 行为推断（Behavior, 概率解释）
输出：
- 五类行为概率（softmax）
- 主叙事（dominant）
- evidence pack（最多 3 条证据）

### 4.4 连续叙事（Stateful Timeline）
输出：
- 最近 N 条变化事件（event_type, delta, reason_key, ts）
- 规则：只有当“结构/概率变化超过阈值”才写入 timeline，避免刷屏

### 4.5 交易剧本（Playbook）
输出两条：
- Plan A（偏顺势/突破）
- Plan B（偏失效/反向）
每条必须包含：
- 触发条件（If）
- 目标位（Target：下一阻力/支撑 zone 或 ATR 外扩）
- 失效线（Invalidation：回到 zone 内/跌破关键位）
- 风险提示（流动性/波动/事件风险）

---

## 5. 输出规范（Schema 要求）
后端必须返回结构化 JSON（不返回一大段中文长文），文本采用 key + 模板渲染方式。

最关键字段：
- market_state.regime + confidence
- zones.support/resistance（low/high/score/touches）
- behavior.probabilities + dominant + evidence[]
- timeline[]
- playbook[]

详见 `Docs/API.md` 与 `Docs/ENGINE_SPEC.md`。

---

## 6. 成功指标（MVP）
- 功能性：用户输入 ticker 能稳定看到结构、概率、时间线
- 响应性：首次加载 ≤ 10s，刷新 ≤ 5s（取决于 provider）
- 连续性：timeline 能反映结构演进（突破尝试→确认/失败、洗盘概率上升等）
- 可信度：每条行为解读至少有 1 条证据点支撑（可追溯到 bar_time）

---

## 7. 风险与边界（必须声明）
- 本系统不构成投资建议，仅提供量价结构分析与概率解释
- 行为推断不代表真实“主力账户”行为，只是模式识别推断
- 1m 噪声高，建议结合更高周期验证（产品内提示）
