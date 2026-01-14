
---

## docs/ENGINE_SPEC.md（第四份：算法 + 金融逻辑，清楚、专业、分类、细节）

```md
# KLineLens MVP - Engine Spec（结构识别 + 行为推断 + 叙事状态机）

## 0. 设计原则（金融专业约束）
1) **先定 Regime（市场状态）再解释行为**：趋势/震荡决定信号含义
2) **关键位是 Zone（价格带），不是一条线**：用带宽描述支撑阻力更符合实盘
3) **突破必须分阶段**：attempt/confirm/fakeout（默认不轻易“确认”）
4) **行为推断是概率解释**：不输出确定性“主力在做X”，只输出概率与证据
5) **任何剧本必须有失效条件**：Plan A/B 都要明确 invalidation
6) **1m噪声极高**：输出必须附风险提示与高周期建议（MVP至少 1d 对照）

---

## 1. 输入数据与预处理
### 1.1 输入数据结构
Bar:
- t: UTC timestamp
- o/h/l/c: float
- v: float

### 1.2 预处理
- 按时间排序、去重
- 缺失 bar（分钟缺口）处理：MVP可允许缺口存在，但需要在报告中标注 “data gaps”
- 时区：统一为 UTC（前端显示可本地化）

---

## 2. Feature 层（可解释特征）
### 2.1 波动与带宽
- ATR(14): 用于 zone 带宽、ZigZag 去噪阈值
- Range (high-low): 当前 bar 波幅
- Volatility regime（可选）：ATR 相对过去均值的分位

### 2.2 成交量相对指标（关键）
- `avg_vol = SMA(v, N)`（N: 20~50 for 1m）
- `volume_ratio = v / avg_vol`
解释：
- volume_ratio >> 1：放量
- volume_ratio ~ 1：常态
- volume_ratio << 1：缩量

### 2.3 K线形态结构特征（无需AI即可稳定）
- `body = abs(c - o)`
- `range = h - l`
- `body_ratio = body / range`（range=0 时设为 0）
- `upper_wick = h - max(o, c)`
- `lower_wick = min(o, c) - l`
- `wick_ratio_low = lower_wick / range`
- `wick_ratio_up = upper_wick / range`
解释：
- 长下影（wick_ratio_low 高）：下探被拉回（需求回收/止损扫）
- 长上影：上攻被压回（供应压制/派发嫌疑）

### 2.4 推进效率（Tape-reading 的核心替代量）
用“单位成交量推动的价格变化”近似刻画吸收/派发：
- `up_eff = max(c - o, 0) / v`
- `down_eff = max(o - c, 0) / v`
解释：
- 大量但 up_eff 很低：上方供应吸收/派发嫌疑
- 大量但 down_eff 很低：下方需求吸收/吸筹嫌疑

---

## 3. Structure 层（市场结构识别）
### 3.1 Swing Points（波峰波谷）
目标：提取结构骨架，减少 1m 噪声影响。

#### 方法A（MVP推荐）：Fractal window
- 参数 `n`：左右各 n 根K比较
- swing_high：bar.high 为 [i-n, i+n] 区间最高
- swing_low：bar.low 为 [i-n, i+n] 区间最低

默认参数建议：
- 1m: n=3~5
- 1d: n=2~3

输出：
- swing_highs: list[(t, price)]
- swing_lows: list[(t, price)]

#### 去噪（可选）：ZigZag with ATR threshold
- 当回撤/反弹幅度 < k*ATR 时忽略（k ~ 0.8~1.5）

---

### 3.2 Regime（趋势/震荡）
#### 定义
- Uptrend：Higher High + Higher Low（HH+HL）占比高
- Downtrend：Lower Low + Lower High（LL+LH）占比高
- Range：结构不一致或高低点在区间反复

#### 算法（MVP）
- 取最近 `m` 个 swing points（m=6~10）
- 统计 HH/HL、LL/LH 比例
- 取最大者为 regime
- confidence = max_ratio（或 margin）

输出：
- `regime in {uptrend, downtrend, range}`
- `confidence in [0,1]`

---

### 3.3 Support/Resistance Zones（支撑/阻力价格带）
#### 金融专业定义
- 关键位不是“精确价格”，而是一段价格带（zone）
- zone 的重要性来自：触碰次数、反转强度、停留时间、与高周期重合

#### 实现（MVP）
输入：
- swing_lows（生成 support candidates）
- swing_highs（生成 resistance candidates）
- ATR 用于 zone 带宽

步骤：
1) 对候选价格做聚类（简单分桶或 DBSCAN 均可）
   - 建议初版：按 `bin_width = 0.5 * ATR` 做分桶
2) 每个簇生成 zone：
   - zone.low = min(price) - w
   - zone.high = max(price) + w
   - w = 0.25~0.5 * ATR（可调）
3) 评分：
   - touches = 簇内点数
   - reaction_strength = 平均反转幅度（触碰后若干根K的反向移动）
   - score = a*touches + b*reaction_strength（归一化到 0~1）

输出：
- support_zones[] / resistance_zones[]（按 score 排序，取 Top K：K=3~6）

---

### 3.4 Range Box（箱体/盘整）
#### 金融定义
盘整区间通常满足：
- 上下沿反复被测试
- 波动收缩（ATR下降）
- 价格重心不明显上移/下移

#### 实现（MVP简化）
- 若 regime = range 且
- 存在一对强 zone（top support + top resistance）
- 且触碰次数 ≥ 2
则定义为 range box。

输出：
- `range_box = {support_zone, resistance_zone, duration_estimate}`

---

### 3.5 Breakout / Fakeout 状态机
#### 状态定义
- idle：无突破行为
- attempt：价格触碰并越过 zone 边界（短暂）
- confirmed：收盘在 zone 外持续 N 根K + 放量确认
- fakeout：越过后快速回到 zone 内（常见诱多/诱空）

#### 关键“确认”条件（MVP）
以向上突破阻力 zone 为例：
- attempt: high > resistance.high
- confirmed:
  - close > resistance.high + epsilon
  - volume_ratio >= Vth（默认 1.8）
  - 连续 Nc 根K收盘在外（默认 Nc=2）
- fakeout:
  - attempt 发生后 M 根K内 close 回到 zone 内（默认 M=3）
  - 或出现长上影 + 放量但不延续

输出：
- signals[]（类型、方向、相关 level、confidence、bar_time）

---

## 4. Behavior Inference（“主力行为”概率推断）
> 注意：这里的“主力”是交易者口语。工程上输出为：**基于量价与结构的行为模式概率**。

### 4.1 五类行为定义（Wyckoff/结构交易常用语义）
1) Accumulation（吸筹/吸收）：大卖压下价格不再有效下行（down_eff 低）  
2) Shakeout（洗盘/止损扫）：刺破支撑后快速回收，长下影 + 放量  
3) Markup（拉升）：突破后站稳，回踩缩量，HL结构延续  
4) Distribution（派发）：高位放量但推不上去（up_eff 低），上影线多  
5) Markdown（砸盘/下杀）：跌破后不回收，反弹弱、缩量，LL/LH延续  

### 4.2 关键特征与证据模板（MVP必须可解释）
#### (A) Accumulation（吸筹）
触发特征（示例）：
- 价格位于 support zone 附近
- volume_ratio 高（>1.5）但 down_eff 低（分位数低）
- 多次出现 “下探→收回”（wick_ratio_low 高）

score_accum 组成：
- + f1: near_support (0/1)
- + f2: volume_ratio
- + f3: (1 - down_eff_norm)
- + f4: wick_ratio_low

证据：
- “在支撑附近放量但跌不动（down_eff 低）”
- bar_time + volume_ratio + down_eff_norm

#### (B) Shakeout（洗盘）
触发特征：
- intrabar 跌破 support zone.low（low < zone.low）
- close 回到 zone 内或上方（close >= zone.low）
- wick_ratio_low 高
- volume_ratio 高

score_shakeout：
- + sweep_support (0/1)
- + reclaim (0/1)
- + wick_ratio_low
- + volume_ratio

证据：
- “刺破支撑后快速收回（sweep+reclaim）”

#### (C) Markup（拉升）
触发特征：
- breakout confirmed（结构条件）
- HL 连续出现
- 回踩缩量（pullback volume_ratio < advance volume_ratio）
- up_eff 上升（推进效率改善）

score_markup：
- + breakout_confirmed
- + hl_count_norm
- + (advance_vol - pullback_vol)
- + up_eff_norm

证据：
- “突破确认 + 回踩缩量 + 低点抬高”

#### (D) Distribution（派发）
触发特征：
- 价格位于 resistance zone 附近（或创新高后）
- volume_ratio 高但 up_eff 低（推不上去）
- 上影线多（wick_ratio_up 高）
- 多次冲高回落（rejection count）

score_dist：
- + near_resistance
- + volume_ratio
- + (1 - up_eff_norm)
- + wick_ratio_up
- + rejection_count_norm

证据：
- “高位放量但涨不动（up_eff 低）+ 上影线”

#### (E) Markdown（砸盘）
触发特征：
- breakdown confirmed（收盘持续在 support zone 下方）
- LL/LH 结构延续
- 反弹缩量
- down_eff 上升（下行推进效率高）

score_markdown：
- + breakdown_confirmed
- + ll_lh_count_norm
- + (pullback_vol_low)
- + down_eff_norm

证据：
- “跌破支撑后不回收 + 反弹弱”

### 4.3 Score -> Probability
- 将 5 个 score 做标准化（如 z-score 或 min-max）
- 用 softmax 得到概率分布
- dominant = argmax(prob)

输出：
- probabilities（五类）
- dominant
- evidence（取 dominant 对应的 Top 1~3 条证据）

---

## 5. Stateful Narrative（连续叙事状态机）
### 5.1 目的
解决“每分钟截图问LLM会忘”的问题：系统记住前态，追踪演化。

### 5.2 State 内容（按 ticker+tf 维护）
- last_regime
- last_zones_hash（zone有变化才记录）
- last_behavior_probs
- last_breakout_state
- last_updated_ts

### 5.3 事件写入规则（避免刷屏）
仅当满足任一条件，写入 timeline：
- dominant 行为变化（shakeout -> distribution）
- dominant 概率变化超过阈值（delta >= 0.12）
- breakout_state 发生变化（attempt->confirmed、attempt->fakeout）
- regime 变化（range->uptrend）

timeline event 字段：
- ts
- event_type（固定枚举）
- delta（概率变化）
- reason_key（模板 key）

---

## 6. Playbook（条件式交易剧本生成）
### 6.1 生成逻辑（MVP模板）
基于当前结构输出两条剧本：

Plan A（顺势/突破）：
- If：breakout_confirmed above resistance_zone.high with volume_ratio >= Vth
- Target：next resistance zone 或 current_price + k*ATR
- Invalidation：close back into zone（或 below resistance_zone.low）

Plan B（失效/反向）：
- If：breakdown_confirmed below support_zone.low with volume_ratio >= Vth
- Target：next support zone 或 current_price - k*ATR
- Invalidation：close back above support_zone.high

### 6.2 风险提示
- 1m 噪声高（noise_high_1m）
- 流动性风险（liquidity_risk）
- 事件风险（event_risk）

输出：
- playbook[]（使用 key + 数值，前端渲染语言）

---

## 7. 参数默认值（MVP建议）
1m：
- swing fractal n=4
- vol SMA N=30
- breakout vol threshold Vth=1.8
- confirm candles Nc=2
- fakeout window M=3
- zone width w=0.35*ATR

1d：
- swing n=2~3
- vol SMA N=20
- zone width w=0.5*ATR

（参数必须可配置，先写死默认，后续开放设置）
