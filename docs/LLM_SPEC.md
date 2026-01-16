# KLineLens — LLM Narrative Spec

> AI 解读模块规范：事件驱动 + EH 上下文感知

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **不预测价格** | LLM 只解释结构，不做价格预测 |
| **证据驱动** | 每个结论必须有 [#bar_index] 证据支持 |
| **时间感知** | 根据当前时间决定发送哪些 EH 数据 |
| **简洁终端风格** | 输出像交易终端，不像作文 |
| **Volume 质量感知** | 无量数据时明确降低置信度 |

---

## 2. 报告类型

| 类型 | 触发条件 | 模型 | 用途 |
|------|----------|------|------|
| `quick` | 用户点击"生成短评" | gpt-4o-mini | 80-120字快速解读 |
| `full` | 5m Hard Event 触发 | gpt-4o | 完整结构分析 |
| `confirmation` | 1m 确认/否定 | gpt-4o-mini | 执行级别确认 |
| `context` | 1D 背景 | gpt-4o | 大结构框架 |
| `aggregated` | 冷却期后聚合 | gpt-4o-mini | 多事件汇总 |

---

## 3. EH 上下文集成

### 3.1 时间窗口定义（美东时间 ET）

| 时段 | 时间范围 | EH 重要性 | 发送内容 |
|------|----------|-----------|----------|
| **盘前** | 04:00-09:30 | 🔴 关键 | 完整 EH Context |
| **开盘** | 09:30-10:00 | 🟠 重要 | EH Context + Gap 分析强调 |
| **盘中** | 10:00-15:00 | 🟡 参考 | 仅 YC/PMH/PML（如果价格在附近）|
| **尾盘** | 15:00-16:00 | 🟢 低 | 最小化 EH，除非价格在关键位 |
| **盘后** | 16:00-20:00 | ⚪ 忽略 | 不发送前日 EH |

### 3.2 发送逻辑伪代码

```python
def should_include_eh_context(current_time_et: datetime, price: float, eh_levels: EHLevels) -> dict:
    """
    根据当前时间和价格位置决定是否发送 EH 数据

    Returns:
        {
            "include": bool,
            "level": "full" | "partial" | "minimal" | "none",
            "emphasis": str  # 强调哪些方面
        }
    """
    hour = current_time_et.hour
    minute = current_time_et.minute

    # 盘前 (04:00-09:30)
    if hour < 9 or (hour == 9 and minute < 30):
        return {
            "include": True,
            "level": "full",
            "emphasis": "premarket_regime_and_gap"
        }

    # 开盘 (09:30-10:00)
    if hour == 9 and minute >= 30:
        return {
            "include": True,
            "level": "full",
            "emphasis": "gap_fill_vs_continuation"
        }

    # 盘中 (10:00-15:00)
    if 10 <= hour < 15:
        # 检查价格是否在 EH 关键位附近 (0.5% 以内)
        near_eh_level = is_price_near_eh_levels(price, eh_levels, threshold_pct=0.5)

        if near_eh_level:
            return {
                "include": True,
                "level": "partial",
                "emphasis": f"price_at_{near_eh_level}"  # e.g., "price_at_yc"
            }
        else:
            return {
                "include": False,
                "level": "minimal",
                "emphasis": "none"
            }

    # 尾盘 (15:00-16:00)
    if 15 <= hour < 16:
        return {
            "include": False,
            "level": "minimal",
            "emphasis": "closing_structure"
        }

    # 盘后/休市
    return {
        "include": False,
        "level": "none",
        "emphasis": "none"
    }


def is_price_near_eh_levels(price: float, levels: EHLevels, threshold_pct: float = 0.5) -> str:
    """检查价格是否在 EH 关键位附近"""

    checks = [
        ("yc", levels.yc),
        ("pmh", levels.pmh),
        ("pml", levels.pml),
        ("ahh", levels.ahh),
        ("ahl", levels.ahl),
    ]

    for name, level in checks:
        if level and abs(price - level) / price * 100 <= threshold_pct:
            return name

    return ""
```

### 3.3 EH 数据结构（发送给 LLM）

```python
eh_context_for_llm = {
    "session": "premarket" | "opening" | "regular" | "closing" | "afterhours",
    "time_et": "09:45",
    "regime": "gap_and_go" | "gap_fill_bias" | "trend_continuation" | "range_day_setup",
    "bias": "bullish" | "bearish" | "neutral",
    "bias_confidence": 0.72,

    # Gap 信息
    "gap": {
        "direction": "up" | "down",
        "size": 1.30,
        "size_pct": 0.53,
        "status": "unfilled" | "partially_filled" | "filled"
    },

    # 关键位（仅发送相关的）
    "key_levels": {
        "yc": 245.50,      # 始终发送
        "pmh": 246.80,     # 盘前/开盘发送
        "pml": 244.20,     # 盘前/开盘发送
        "gap_fill_target": 245.50  # gap_fill_bias 时发送
    },

    # 盘前形态描述
    "pm_structure": "PM extended gap direction, holding above PMH"
}
```

---

## 4. Prompt 更新

### 4.1 Quick Update (短评) - 增强版

```
根据提供的市场数据，用一段话解读当前盘面结构。

语言：{lang_name}

数据：
{analysis_json}

{eh_section}

要求：
- 一段连贯的分析文字，80-150字
- 解读数据含义，说明当前结构状态
- 如果行为与趋势冲突要解释原因
- 带具体数字（价位、RVOL等）
- 不要标题、bullet、分段，就一段话
- 不要写操作建议，只做数据解读
{eh_instruction}

示例（含 EH）：
开盘跳空高开1.3%后回落测试YC(245.50)，盘前形态为gap_fill_bias，当前价格在PMH(246.80)下方整理。RVOL 0.85偏低，缺乏明确方向。若回补缺口至YC有支撑反弹机会，否则关注245下方是否破位。整体偏向观望。
```

其中 `{eh_section}` 和 `{eh_instruction}` 根据时间动态生成：

**盘前/开盘时段：**
```
EH 上下文：
{eh_context_json}

额外要求：
- 必须提及盘前形态（{regime}）和 Gap 方向
- 解释当前价格相对 PMH/PML/YC 的位置
- 如果是 gap_fill_bias，说明 gap 回补的可能性
- 如果是 gap_and_go，说明顺势延续的条件
```

**盘中时段（价格在 EH 关键位附近）：**
```
参考位：
- YC: {yc}（价格距离 {dist_yc}%）

额外要求：
- 提及价格与 YC 的关系（是否被吸引/突破）
```

**盘中时段（价格远离 EH）：**
```
（不发送 EH 数据）
```

### 4.2 5m Full Analysis - EH 增强

```
Write an evidence-backed 5m market-structure update for KLineLens.

CONTEXT:
- This report is triggered by a structural event.
- Focus on WHAT changed, WHY it matters, and WHAT to watch next.
- Language: {lang_name}

INPUT DATA:
{analysis_json}

{eh_section}

OUTPUT FORMAT (strict, use {lang_name}):

## TL;DR
- Regime / Breakout / Behavior (one line each)
{eh_tldr_line}
- **Action**: WAIT / WATCH / TRIGGERED (pick one)
- **Trigger**: specific condition(s)

## What Changed
- Bullet 1 with evidence [#bar_index]
- Bullet 2 with evidence [#bar_index]
- (max 3 bullets)

{eh_context_section}

## Evidence Chain
- Evidence type + explanation + numbers + [#bar_index]
- (3-6 bullets)

## Key Zones
| Level | Type | Distance | Significance |
| --- | --- | --- | --- |
(top 4 zones, include EH levels if relevant)

## Scenarios
**A (Primary)**: condition → path → invalidation
**B (Alternate)**: condition → path → invalidation
{eh_scenario_note}

## Risk Notes
- Data quality, volume, provider delay
{eh_risk_note}

STYLE: No fluff. Use "if/then" language.
```

其中 EH 相关占位符：

**`{eh_tldr_line}`（盘前/开盘）：**
```
- EH Regime: {regime} / Bias: {bias} / Gap: {gap_pct}%
```

**`{eh_context_section}`（盘前/开盘）：**
```
## EH Context
- Premarket Regime: {regime}
- Gap: {direction} {size} ({pct}%)
- Key Levels: YC {yc}, PMH {pmh}, PML {pml}
- Interpretation: {pm_structure}
```

**`{eh_scenario_note}`（gap_fill_bias 时）：**
```
> Gap Fill Note: If price fails at current level, watch for reversion to YC ({yc}).
```

**`{eh_risk_note}`（盘前/开盘）：**
```
- EH data based on premarket session, may shift at open
```

---

## 5. prepare_analysis_for_llm 更新

### 5.1 新增字段

```python
def prepare_analysis_for_llm(
    report: Dict[str, Any],
    ticker: str,
    timeframe: str,
    price: float,
    include_evidence: bool = True,
    eh_context: Optional[Dict] = None,  # 新增
    current_time_et: Optional[datetime] = None  # 新增
) -> Dict[str, Any]:
    """
    准备发送给 LLM 的结构化 JSON

    新增：
    - eh_context: EH 上下文数据
    - current_time_et: 当前美东时间（用于时间感知逻辑）
    """

    # ... 现有逻辑 ...

    # 新增：EH 上下文处理
    eh_data = None
    if eh_context and timeframe in ["1m", "5m"]:
        eh_decision = should_include_eh_context(current_time_et, price, eh_context)

        if eh_decision["include"]:
            eh_data = {
                "session": get_session_name(current_time_et),
                "regime": eh_context.get("premarket_regime"),
                "bias": eh_context.get("bias"),
                "bias_confidence": eh_context.get("bias_confidence"),
                "gap": {
                    "size": eh_context.get("levels", {}).get("gap"),
                    "size_pct": eh_context.get("levels", {}).get("gap_pct"),
                },
                "levels": filter_eh_levels_by_relevance(
                    eh_context.get("levels", {}),
                    eh_decision["level"]
                ),
                "emphasis": eh_decision["emphasis"]
            }

    result = {
        # ... 现有字段 ...
        "eh": eh_data  # 新增
    }

    return result
```

### 5.2 辅助函数

```python
def filter_eh_levels_by_relevance(levels: Dict, level: str) -> Dict:
    """根据重要性级别过滤 EH levels"""

    if level == "full":
        return {
            "yc": levels.get("yc"),
            "pmh": levels.get("pmh"),
            "pml": levels.get("pml"),
            "ahh": levels.get("ahh"),
            "ahl": levels.get("ahl"),
        }
    elif level == "partial":
        return {
            "yc": levels.get("yc"),
            "pmh": levels.get("pmh"),
            "pml": levels.get("pml"),
        }
    elif level == "minimal":
        return {
            "yc": levels.get("yc"),
        }
    else:
        return {}


def get_session_name(time_et: datetime) -> str:
    """获取当前交易时段名称"""
    hour = time_et.hour
    minute = time_et.minute

    if hour < 9 or (hour == 9 and minute < 30):
        return "premarket"
    elif hour == 9 and minute >= 30:
        return "opening"
    elif 10 <= hour < 15:
        return "regular"
    elif 15 <= hour < 16:
        return "closing"
    else:
        return "afterhours"
```

---

## 6. Playbook 数据增强

### 6.1 Plan EH 类型

当 EH context 存在且为 `gap_fill_bias` 时，playbook 可能包含 `Plan EH`：

```python
{
    "name": "Plan EH",
    "condition": "condition.gap_fill_short",  # or gap_fill_long
    "level": current_price,
    "target": yc,
    "invalidation": current_price + atr * 0.5,
    "risk": "risk.gap_continuation"
}
```

### 6.2 LLM 解读要求

- 如果 playbook 包含 Plan EH，必须在解读中提及
- 解释 gap fill 的逻辑：价格倾向于回归 YC
- 说明失效条件：价格突破 PMH/PML 后 gap fill 失效

---

## 7. 示例输出

### 7.1 盘前短评（9:15 ET）

```
盘前跳空高开1.8%，形态为gap_and_go，价格持续在PMH(248.50)上方运行。RVOL达到2.3，显示买盘强劲。开盘后若能守住247.20支撑并突破249阻力，顺势做多结构成立。风险在于开盘瞬间波动可能触发假突破，建议观察前10分钟成交量确认。
```

### 7.2 开盘短评（9:45 ET）

```
开盘后价格从跳空高点248.50回落至YC(245.20)附近震荡，形态转为gap_fill_bias。RVOL 0.92正常，无明确方向。当前价格在PMH(248.50)和YC(245.20)之间整理，若跌破YC完成缺口回补，下方看244支撑；若反弹站稳247则重回gap_and_go。观望为主。
```

### 7.3 盘中短评（11:30 ET，价格远离 EH）

```
价格在253-255区间窄幅震荡，RVOL 0.65持续萎缩，市场观望情绪浓厚。上方255阻力测试3次未果，下方253支撑暂时有效。行为模式显示轻微吸筹，但量能不足难以突破。关注午盘后是否有放量选向。
```

---

## 8. 实现检查清单

- [ ] 更新 `prepare_analysis_for_llm()` 添加 EH 参数
- [ ] 实现 `should_include_eh_context()` 时间判断逻辑
- [ ] 更新 `PROMPT_QUICK_UPDATE` 支持 EH 占位符
- [ ] 更新 `PROMPT_5M_ANALYSIS` 支持 EH section
- [ ] 前端传递 EH context 到 narrative API
- [ ] 测试不同时段的 EH 数据发送逻辑
- [ ] 测试 playbook Plan EH 的解读

---

## 附录：禁止用语

| 禁止 | 原因 |
|------|------|
| "guaranteed" / "稳赚" / "必赚" | 误导性 |
| "100% accurate" | 不可能 |
| "AI predicts price" | 超出能力范围 |
| "will definitely" | 确定性表述 |
| "you should buy/sell" | 投资建议 |
