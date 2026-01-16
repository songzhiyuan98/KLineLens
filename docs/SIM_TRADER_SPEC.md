# SIM_TRADER_SPEC.md（方案 A：0DTE Trade Plan 模块）

> 0DTE 交易剧本模块设计文档 - 不依赖期权报价，只输出标的价格层级的交易计划

---

## 1. 模块目标（Scope）

本模块用于把分析系统输出的结构化信号转换为：

* **交易预案（WATCH/ARMED）**
* **明确进场指令（ENTER CALL / ENTER PUT）**
* **出场目标（Target）与失效条件（Invalidation）**
* **持仓管理建议（HOLD / TRIM / EXIT）**
* **复盘记录（信号是否正确、是否按规则执行）**

> ⚠️ 本模块不需要期权实时报价，不计算真实 premium。
> 它输出的是"标的（QQQ）价格层级"上的交易剧本与执行建议。

---

## 2. 与分析系统完全分离（Hard Separation）

### 分析系统负责：

* 计算信号、行为结构、趋势
* 计算 levels/zones（R1/R2/S1/S2/YC/HOD/LOD 等）
* 产出统一结构化快照 `AnalysisSnapshot`

### Trade Plan 模块负责：

* 不做任何技术指标计算
* 不重算趋势
* 只消费 `AnalysisSnapshot`
* 输出交易计划 `TradePlanRow` + 持仓建议 `ManageAdvice`

---

## 3. 输入/输出契约（Types）

### 3.1 输入：AnalysisSnapshot

最小字段：

```ts
type AnalysisSnapshot = {
  ts: string; // ISO time (ET or UTC)
  ticker: string; // "QQQ"
  interval: "1m" | "5m";

  price: {
    open: number; high: number; low: number; close: number;
  };

  levels: {
    R1?: number; R2?: number;
    S1?: number; S2?: number;
    YC?: number;
    HOD?: number; LOD?: number;
    YH?: number; YL?: number;
    PMH?: number; PML?: number;
  };

  signals: {
    trend_1m: "up" | "down" | "neutral";
    trend_5m?: "up" | "down" | "neutral";
    behavior?: "accumulation" | "distribution" | "wash" | "rally" | "chop";
    breakoutQuality?: "pass" | "fail" | "unknown";
    rvolState?: "low" | "ok" | "high";
    openingProtection?: boolean; // 09:30-09:40 ET true
  };

  confidence?: number; // 0-100
};
```

---

### 3.2 输出：TradePlanRow（用于 UI 表格）

```ts
type TradeStatus = "WAIT" | "WATCH" | "ARMED" | "ENTER" | "HOLD" | "TRIM" | "EXIT";

type TradeDirection = "CALL" | "PUT" | "NONE";

type TradePlanRow = {
  ts: string;
  status: TradeStatus;
  direction: TradeDirection;

  entryZone?: string;           // "R1 breakout" / "YC reclaim" etc.
  entryUnderlying?: string;     // ">= 624.30 (2 closes above R1)"
  targetUnderlying?: string;    // "R2 626.10"
  invalidation?: string;        // "close back below R1"

  risk: "LOW" | "MED" | "HIGH";
  watchlistHint?: string;       // "Watch 0DTE ATM +1 strike CALL"

  reasons: string[];            // 2-4 bullets
};
```

---

## 4. 核心思想：Trade Plan（交易剧本）而非 Premium

### 4.1 为什么不需要 premium？

0DTE 期权 premium 强依赖：

* theta 衰减
* IV 变化
* spread/流动性

模拟系统如果没有专业期权数据源，硬算 premium 反而会误导。

✅ 所以方案 A 只输出：

* **标的触发位（entry）**
* **标的目标位（target）**
* **标的失效位（invalidation）**
* **风险与确认条件**

执行时你去 Robinhood 对照当前 0DTE 合约 premium 即可。

---

## 5. 状态机（State Machine）

每个 ticker 每天最多 1 笔"高胜率交易"（可设置）。

状态流转：

```
WAIT → WATCH → ARMED → ENTER → HOLD → TRIM/EXIT
                 ↓
               (条件不满足回退)
                 ↓
               WAIT
```

状态定义：

| 状态 | 含义 | 触发条件 |
|------|------|----------|
| `WAIT` | 无交易机会 | 默认状态，无 setup |
| `WATCH` | 出现 setup，但未接近触发 | 价格距离关键位 > 0.3% |
| `ARMED` | 接近触发，发预警 | 价格距离关键位 <= 0.3% |
| `ENTER` | 触发条件满足，建议下单 | 所有确认条件通过 |
| `HOLD` | 已进入持仓管理 | ENTER 后下一根 bar |
| `TRIM` | 建议减仓 | 软止损条件触发 |
| `EXIT` | 建议清仓 | 硬止损条件触发 |

> 注：ENTER 后下一根 bar 自动进入 HOLD（避免一直显示 ENTER）。

---

## 6. 0DTE 策略规则（QQQ专用）

### 6.1 时间窗口

| 时段 | 美东时间 | 太平洋时间 | 说明 |
|------|----------|------------|------|
| 开盘保护 | 09:30-09:40 | 06:30-06:40 | openingProtection=true，更严格确认 |
| 黄金时段 | 09:40-11:00 | 06:40-08:00 | 最佳交易窗口 |
| 午盘 | 11:00-14:00 | 08:00-11:00 | 流动性下降，谨慎 |
| 尾盘 | 14:00-16:00 | 11:00-13:00 | theta 加速，高风险 |

推荐交易时间：**06:00–11:00 PT**（可配置）

---

### 6.2 Entry Setup（交易机会类型）

支持 4 种核心 setup：

#### Setup A：R1 Breakout（CALL）

**场景**：价格接近 R1，上破可能拉升

**触发条件**：
- `1m close > R1` 连续 **2根确认**
- `breakoutQuality == pass`
- `trend_1m == up`
- `rvolState != low`（开盘保护时强制）

**输出**：
```
status: ENTER
direction: CALL
entryUnderlying: >= R1 + buffer (2 closes)
targetUnderlying: R2 or HOD
invalidation: close < R1 (2 bars)
```

---

#### Setup B：S1 Breakdown（PUT）

**场景**：价格接近 S1，下破可能下跌

**触发条件**（对称逻辑）：
- `1m close < S1` 连续 2 根
- `breakoutQuality == pass`
- `trend_1m == down`
- `rvolState != low`

**输出**：
```
status: ENTER
direction: PUT
entryUnderlying: <= S1 - buffer (2 closes)
targetUnderlying: S2 or LOD
invalidation: close > S1 (2 bars)
```

---

#### Setup C：YC Reclaim（CALL）

**场景**：价格回踩 YC 不破，再次站上

**触发条件**：
- 价格曾跌破 YC 后重新站上
- `1m close > YC` 连续 2 根
- `trend_1m != down`

**输出**：
```
status: ENTER
direction: CALL
entryUnderlying: >= YC + buffer (reclaim)
targetUnderlying: R1 or PMH
invalidation: close < YC (2 bars)
```

适合震荡日高胜率"回补/反弹"。

---

#### Setup D：R1 Reject（PUT）

**场景**：触碰 R1 被拒绝，结构转空

**触发条件**：
- 价格触及 R1 但未能突破（wicks）
- `1m close < R1` 连续 2 根（rejection 确认）
- `trend_1m == down` 或 `behavior == distribution`

**输出**：
```
status: ENTER
direction: PUT
entryUnderlying: <= R1 - buffer (rejection)
targetUnderlying: YC or S1
invalidation: close > R1 (2 bars)
```

---

### 6.3 Buffer（避免假突破）

```
buffer = 0.05% * price
```

| 标的价格 | Buffer |
|----------|--------|
| QQQ 500 | ~0.25 |
| QQQ 600 | ~0.30 |
| QQQ 624 | ~0.31 |

可配置参数：`BUFFER_PCT = 0.0005`

---

## 7. HOLD/TRIM/EXIT（持仓管理建议）

### 7.1 EXIT（硬条件）

任一命中立即 `EXIT`：

| 条件 | 说明 |
|------|------|
| trend 反转 + 关键位失守 | CALL 单跌回 R1 下方并 2 根确认 |
| behavior 转 distribution/wash | 与 CALL 方向冲突 |
| 触发 invalidation | 预设止损位被触发 |

---

### 7.2 TRIM（软条件，0DTE 专属）

任一命中建议 `TRIM`：

| 条件 | 说明 |
|------|------|
| 时间止损 | 进场后 8–12 分钟未向 target 推进 |
| 多次冲击失败 | 目标位被测试 >= 3 次未突破 |
| 动能衰减 | rvol 变 low + chop 增强 |

---

### 7.3 HOLD（继续持有）

所有条件满足时继续 `HOLD`：

- 结构未破（关键位未失守）
- 仍朝 target 推进
- breakoutQuality 仍有效

---

## 8. Watchlist Hint（提前预警去 RH 盯合约）

当 status = ARMED 或 ENTER 时输出：

| Direction | Hint |
|-----------|------|
| CALL | `Watch 0DTE ATM +1 strike CALL` |
| PUT | `Watch 0DTE ATM +1 strike PUT` |

附加提示：
> "Prefer liquidity: highest OI/volume strike"

> 以后如果接期权数据源，再升级成具体合约 symbol 与 premium。

---

## 9. UI 显示：表格是最优解

### 9.1 推荐表格列

**Sim Trade Plan（表格）**

| 列名 | 字段 | 说明 |
|------|------|------|
| Time | ts | 时间戳 |
| Status | status | WAIT/WATCH/ARMED/ENTER/HOLD/TRIM/EXIT |
| Dir | direction | CALL/PUT/NONE |
| Entry | entryUnderlying | 入场条件 |
| Target | targetUnderlying | 目标位 |
| Invalidation | invalidation | 失效条件 |
| Risk | risk | LOW/MED/HIGH |
| Watch | watchlistHint | 合约提示 |

点击某行展开 `reasons[]`（证据链）。

### 9.2 颜色编码

| Status | 背景色 |
|--------|--------|
| WAIT | 灰色 |
| WATCH | 淡黄 |
| ARMED | 橙色 |
| ENTER | 绿色（CALL）/ 红色（PUT）|
| HOLD | 蓝色 |
| TRIM | 紫色 |
| EXIT | 深灰 |

### 9.3 放置位置

- ✅ 放在 **K 线下方**（作为新 Tab）
- 右侧栏继续保持 Summary/Trigger/Action 固定可见

---

## 10. 更新频率（性能与体验）

| 操作 | 频率 | 说明 |
|------|------|------|
| 内部状态更新 | 每 1m bar close | 足够快，不浪费资源 |
| UI 刷新 | 每 1m 或节流 3 秒 | 避免闪烁 |
| EH 数据 | 只用缓存 | 绝不盘中高频请求 |

---

## 11. 复盘记录（Post-Mortem）

每次 trade 完成后生成：

```ts
type TradeReview = {
  date: string;
  ticker: string;
  direction: "CALL" | "PUT";
  setup: "R1_BREAKOUT" | "S1_BREAKDOWN" | "YC_RECLAIM" | "R1_REJECT";

  entryTs: string;
  entryPrice: number;
  exitTs: string;
  exitPrice: number;

  outcome: "WIN" | "LOSS" | "BREAKEVEN";
  pnlPct?: number;  // 标的涨跌幅（非期权收益）

  notes: string[];

  signalCorrect: boolean;
  executionCorrect: boolean;
  failureReason?: "FAKEOUT" | "LOW_RVOL" | "OPENING_NOISE" | "BAD_CONFIRMATION" | "TIME_DECAY" | "CHOP";
};
```

### 11.1 复盘统计

| 指标 | 计算方式 |
|------|----------|
| 胜率 | WIN / (WIN + LOSS) |
| 信号准确率 | signalCorrect / total |
| 执行准确率 | executionCorrect / total |
| 常见失败原因 | 按 failureReason 分组统计 |

> 方案 A 不算真实美元收益，但可以通过 outcome + 失败原因，优化策略阈值。

---

## 12. 参数配置表（Defaults）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `BUFFER_PCT` | 0.0005 | 避免假突破的缓冲 |
| `CONFIRM_BARS` | 2 | 确认所需 K 线数 |
| `INVALIDATE_BARS` | 2 | 失效确认所需 K 线数 |
| `ARMED_DISTANCE_PCT` | 0.003 | 距离关键位 0.3% 内触发 ARMED |
| `TIME_STOP_MINUTES` | 10 | 时间止损（无进展） |
| `MAX_TARGET_ATTEMPTS` | 3 | 目标位最大测试次数 |
| `MAX_TRADES_PER_DAY` | 1 | 每日最大交易次数 |
| `OPENING_PROTECTION_MINUTES` | 10 | 开盘保护时长 |

---

## 13. 文件结构建议

```
packages/core/src/
├── sim_trader/
│   ├── __init__.py
│   ├── types.py          # AnalysisSnapshot, TradePlanRow, TradeReview
│   ├── state_machine.py  # TradeStateMachine 类
│   ├── setups.py         # 4 种 setup 检测逻辑
│   ├── manager.py        # HOLD/TRIM/EXIT 持仓管理
│   └── config.py         # 参数配置
│
apps/api/src/
├── services/
│   └── sim_trader_service.py  # API 层封装
│
apps/web/src/
├── components/
│   └── SimTradeTable.tsx      # 表格 UI 组件
```

---

## 14. API 端点设计

### GET /v1/sim-trade-plan

**请求**：
```
GET /v1/sim-trade-plan?ticker=QQQ&tf=1m
```

**响应**：
```json
{
  "ticker": "QQQ",
  "ts": "2026-01-16T09:45:00-05:00",
  "plan": {
    "status": "ARMED",
    "direction": "CALL",
    "entryZone": "R1 breakout",
    "entryUnderlying": ">= 624.30 (2 closes above R1)",
    "targetUnderlying": "R2 626.10",
    "invalidation": "close < R1 (2 bars)",
    "risk": "MED",
    "watchlistHint": "Watch 0DTE ATM +1 strike CALL",
    "reasons": [
      "Price approaching R1 (624.30)",
      "Trend 1m: up",
      "RVOL: ok (1.2x)",
      "Breakout quality: pass"
    ]
  },
  "history": [
    {
      "ts": "09:35",
      "status": "WATCH",
      "direction": "CALL"
    },
    {
      "ts": "09:42",
      "status": "ARMED",
      "direction": "CALL"
    }
  ]
}
```

---

## 15. 示例输出

### 15.1 ARMED 状态

| Time | Status | Dir | Entry | Target | Invalidation | Risk | Watch |
|------|--------|-----|-------|--------|--------------|------|-------|
| 09:42 | **ARMED** | CALL | >= 624.30 (R1) | R2 626.10 | < R1 (2 bars) | MED | 0DTE ATM+1 CALL |

**Reasons**:
- Price 0.2% from R1 (624.30)
- Trend 1m: up
- RVOL: 1.2x (ok)
- Breakout quality: pass

---

### 15.2 ENTER 状态

| Time | Status | Dir | Entry | Target | Invalidation | Risk | Watch |
|------|--------|-----|-------|--------|--------------|------|-------|
| 09:45 | **ENTER** | CALL | ✓ 624.35 (confirmed) | R2 626.10 | < 624.00 | MED | Execute now |

**Reasons**:
- 2 consecutive closes above R1
- Breakout confirmed with volume
- Target: R2 at 626.10 (+0.28%)

---

### 15.3 WAIT 状态（无机会）

| Time | Status | Dir | Entry | Target | Invalidation | Risk | Watch |
|------|--------|-----|-------|--------|--------------|------|-------|
| 10:15 | WAIT | NONE | - | - | - | - | No setup |

**Reasons**:
- Price in chop zone between S1 and R1
- No clear directional bias
- RVOL low (0.7x)

---

## 附录：与现有系统的映射

| 现有字段 | 映射到 AnalysisSnapshot |
|----------|------------------------|
| `report.trend.regime` | signals.trend_1m/5m |
| `report.behavior.dominant` | signals.behavior |
| `report.breakout.state` | signals.breakoutQuality |
| `report.zones[].level` | levels.R1/R2/S1/S2 |
| `eh_context.yc` | levels.YC |
| `eh_context.pmh/pml` | levels.PMH/PML |
| `features.rvol` | signals.rvolState |
