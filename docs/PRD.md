# KLineLens MVP - PRD（产品需求文档）

## 1. 背景与目标

### 1.1 背景
用户（短线交易者）经常通过截图 1 分钟 K 线给 LLM 解读盘面结构（趋势/震荡、支撑阻力、放量、洗盘/吸筹/派发等）。当前流程存在明显痛点：
- 输入成本高：每分钟截图、发送、等待回复
- 缺连续性：LLM无法稳定"继承上一分钟结构状态"，容易断片
- 缺可视化与证据：解读缺少可追溯的指标/证据展示
- 缺结构化输出：难以沉淀为可回放、可比较的"结构状态时间线"

### 1.2 产品定位
**KLineLens 是一个开源本地工具**，用户通过 Docker 在本地运行，自己配置数据源。

| 属性 | 说明 |
|------|------|
| 产品形态 | Open-source local terminal |
| 运行方式 | Docker Compose 本地启动 |
| 数据源 | 用户本地配置，默认 Yahoo Finance |
| 我们负责 | 分析引擎 + API + UI |
| 用户负责 | 数据源选择、API key（如需）、本地运行环境 |

### 1.3 产品目标（MVP）
用户输入股票代码（Ticker），系统自动拉取分钟/日线 OHLCV 数据，并输出：
1) **结构识别**：趋势/震荡状态、关键支撑阻力 Zone、突破/假突破状态
2) **行为推断（概率解释）**：吸筹/洗盘/拉升/派发/砸盘的概率 + 证据点
3) **连续叙事（Stateful Timeline）**：记录最近 N 次结构/行为的变化与原因
4) **交易剧本（条件式）**：Plan A/B（触发条件、目标位、失效线、风险提示）

### 1.4 非目标（MVP明确不做）
- 登录/注册/用户体系
- 云端托管服务
- 数据库持久化存储
- 新闻/社媒情绪面（Reddit/X）
- Level2/逐笔成交（订单流）深度推断
- 回测面板（可后续做）
- "确定性喊单"（必须是条件式 + 失效条件 + 概率解释）
- 多语言支持（MVP 仅英文）

---

## 2. 部署与运行

### 2.1 Docker Compose 一键启动
用户执行以下命令即可运行：

```bash
# 1. 克隆仓库
git clone https://github.com/user/klinelens.git
cd klinelens

# 2. 复制环境配置
cp .env.example .env
# （可选）编辑 .env 填写 provider key

# 3. 启动服务
docker compose up --build

# 4. 访问
open http://localhost:3000
```

### 2.2 环境配置（.env.example）
```bash
# Provider 配置
PROVIDER=yahoo              # yahoo | polygon | twelvedata (MVP 仅 yahoo)
TIMEZONE=UTC

# 刷新频率
REFRESH_SECONDS=60          # 前端自动刷新间隔

# 缓存配置
CACHE_TTL=60                # K 线数据缓存秒数

# 端口配置
API_PORT=8000
WEB_PORT=3000

# 可选：付费 Provider API Keys（MVP 不需要）
# POLYGON_API_KEY=
# TWELVEDATA_API_KEY=
```

### 2.3 不做公共托管服务
- 不承诺云端可用性
- 不提供线上账号
- 任何 API key 都只存在用户本地 .env
- 数据请求限流由用户自行承担

---

## 3. 用户与场景

### 3.1 核心用户
- 高频短线交易者：常盯 1m/5m K线
- 波动股/小盘票交易者：关注量价结构和关键位
- 需要"盘面叙事"辅助决策的人：希望快速得到结构解释与风险边界

### 3.2 核心场景（MVP覆盖）
1) 本地启动 Docker 容器，打开浏览器输入 ticker，进入详情页
2) 查看当前 1m 结构解读，每 60 秒自动更新一次
3) 观察结构是否从"震荡→突破尝试→确认/失败"演化
4) 切换周期（1m/5m/1d）观察高周期关键位与低周期执行对齐
5) 看"时间线"理解：为什么系统说"洗盘概率上升/派发概率上升"

---

## 4. 产品信息架构与页面

### 4.1 页面列表（MVP）
- `/` Dashboard：大搜索框（Ticker）
- `/t/{ticker}` Detail：K线 + 分析面板（结构/行为/证据/时间线/剧本）
- `/settings` Settings：设置页面

### 4.2 Dashboard 页面（/）
**需求**
- 输入框支持 ticker（大小写不敏感）
- 搜索后跳转详情页 `/t/TSLA`
- 右上角入口：Settings

**验收**
- 输入合法 ticker（字母+可选点/短横）跳转成功
- 空输入/非法格式显示提示（不跳转）

### 4.3 Detail 页面（/t/{ticker}）
**布局原则：极简、专业、信息密度高但清爽**
- 主体为 Chart + Analysis Panel
- 默认时间周期：1m（window=1d）
- 自动刷新：每 60 秒刷新 analyze

**展示内容（必须）**

A. Chart
- K线（OHLC）
- 成交量柱
- 支撑/阻力 Zone overlay（矩形/带状）
- Breakout/Fakeout Marker（标注点/段）

B. Analysis Panel（卡片式）
1) **Market State**
   - Regime：Uptrend / Downtrend / Range
   - Confidence（0-1）
   - Key Zones（Top 2 支撑 + Top 2 阻力）

2) **Behavior Probabilities**（五类）
   - Accumulation（吸筹）
   - Shakeout（洗盘）
   - Markup（拉升）
   - Distribution（派发）
   - Markdown（砸盘）
   - Dominant Narrative（主叙事：取最高概率）

3) **Evidence**（证据点，最多 3 条）
   - 每条证据必须关联 bar_time + 关键数值

4) **Timeline**（最近 N 条事件）
   - 事件类型、概率变化、原因、时间戳

5) **Playbook**（Plan A / Plan B）
   - 条件式（If…）、目标位、失效线、风险提示

C. **Provider Status**（新增）
- 当前 provider：Yahoo / Polygon / TwelveData
- 数据更新时间
- 如果报错：rate limited / provider error

**交互（必须）**
- Timeframe 切换（至少：1m / 1d；可加 5m）
- Refresh 状态提示（last updated 时间）
- 错误态：数据获取失败/限流/无数据

**验收**
- 输入 ticker 后 10 秒内可以看到图表与报告
- 每 60 秒更新时，timeline 会新增事件或提示"无明显变化"
- 切换 timeframe 会刷新 bars + report

### 4.4 Settings 页面（/settings）
**需求**
- 显示当前 Provider 状态
- 显示缓存 TTL 配置
- 未来：语言选择（MVP 仅英文）

---

## 5. 功能需求（MVP范围）

### 5.1 行情数据获取
- 支持输入 ticker 拉取 OHLCV bars
- 支持 timeframe：1m、5m、1d
- window：1d（1m）/ 5d（5m）/ 6mo（1d）

**数据源保护**
- 前端刷新频率固定（默认 60 秒）
- 切换 ticker/timeframe 时才额外请求
- 不允许 1 秒刷一次（避免触发 Yahoo 限流）

**缓存策略**
- bars 同参数 60 秒 TTL
- analyze 同参数可缓存 10-30 秒（可选）

### 5.2 结构识别（Structure）
输出：
- swing points（用于结构骨架）
- regime（trend/range + confidence）
- zones（支撑阻力：价格带 + score）
- breakout_state（attempt/confirmed/fakeout 等）
- signals（突破/拒绝/假突破标记）

### 5.3 行为推断（Behavior）
输出：
- 五类行为概率（softmax）
- 主叙事（dominant）
- evidence pack（最多 3 条证据）

### 5.4 连续叙事（Stateful Timeline）
输出：
- 最近 N 条变化事件（event_type, delta, reason_key, ts）
- 规则：只有当"结构/概率变化超过阈值"才写入 timeline

### 5.5 交易剧本（Playbook）
输出两条：
- Plan A（偏顺势/突破）
- Plan B（偏失效/反向）
每条必须包含：触发条件、目标位、失效线、风险提示

---

## 6. 数据存储

### 6.1 MVP 默认不需要数据库
| 数据类型 | 存储方式 | 说明 |
|----------|----------|------|
| bars | 内存缓存（TTL） | 重启后重新获取 |
| timeline state | 内存 state | 重启会丢失，允许 |
| 配置 | .env 文件 | 用户本地管理 |

### 6.2 V1 才加持久化（可选）
- 默认 SQLite（本地文件）
- Postgres 作为 docker profile 可选
- 需求文档里写清楚：MVP不做 DB，避免用户额外启动服务

---

## 7. 输出规范（Schema 要求）
后端必须返回结构化 JSON（不返回一大段中文长文），文本采用 key + 模板渲染方式。

最关键字段：
- market_state.regime + confidence
- zones.support/resistance（low/high/score/touches）
- behavior.probabilities + dominant + evidence[]
- timeline[]
- playbook[]

详见 `docs/API.md` 与 `docs/ENGINE_SPEC.md`。

---

## 8. 成功指标（MVP）
- 功能性：用户输入 ticker 能稳定看到结构、概率、时间线
- 响应性：首次加载 ≤ 10s，刷新 ≤ 5s（取决于 provider）
- 连续性：timeline 能反映结构演进
- 可信度：每条行为解读至少有 1 条证据点支撑
- **部署性**：docker compose up 一键启动成功

---

## 9. 风险与边界（必须声明）
- 本系统不构成投资建议，仅提供量价结构分析与概率解释
- 行为推断不代表真实"主力账户"行为，只是模式识别推断
- 1m 噪声高，建议结合更高周期验证
- **数据源风险由用户承担**：Yahoo Finance 有每日请求限制，超限会返回空数据
