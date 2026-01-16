# KLineLens — LLM Narrative Specification

> AI Interpretation Module Specification: Event-driven + EH Context-aware

---

## 1. Design Principles

| Principle | Description |
|-----------|-------------|
| **No Price Predictions** | LLM only explains structure, does not predict prices |
| **Evidence-driven** | Every conclusion must have [#bar_index] evidence support |
| **Time-aware** | Decide which EH data to send based on current time |
| **Concise Terminal Style** | Output like a trading terminal, not an essay |
| **Volume Quality Awareness** | Explicitly lower confidence when volume data is missing |

---

## 2. Report Types

| Type | Trigger Condition | Model | Purpose |
|------|-------------------|-------|---------|
| `quick` | User clicks "Generate Quick Update" | gpt-4o-mini | 80-120 word quick interpretation |
| `full` | 5m Hard Event triggered | gpt-4o | Complete structure analysis |
| `confirmation` | 1m confirmation/denial | gpt-4o-mini | Execution level confirmation |
| `context` | 1D background | gpt-4o | Big picture framework |
| `aggregated` | After cooldown period | gpt-4o-mini | Multi-event summary |

---

## 3. EH Context Integration

### 3.1 Time Window Definitions (Eastern Time ET)

| Session | Time Range | EH Importance | Content Sent |
|---------|------------|---------------|--------------|
| **Premarket** | 04:00-09:30 | 🔴 Critical | Full EH Context |
| **Opening** | 09:30-10:00 | 🟠 Important | EH Context + Gap analysis emphasis |
| **Regular** | 10:00-15:00 | 🟡 Reference | Only YC/PMH/PML (if price nearby) |
| **Closing** | 15:00-16:00 | 🟢 Low | Minimize EH, unless at key levels |
| **Afterhours** | 16:00-20:00 | ⚪ Ignore | Don't send previous day EH |

### 3.2 Sending Logic Pseudocode

```python
def should_include_eh_context(current_time_et: datetime, price: float, eh_levels: EHLevels) -> dict:
    """
    Decide whether to send EH data based on current time and price position

    Returns:
        {
            "include": bool,
            "level": "full" | "partial" | "minimal" | "none",
            "emphasis": str  # What to emphasize
        }
    """
    hour = current_time_et.hour
    minute = current_time_et.minute

    # Premarket (04:00-09:30)
    if hour < 9 or (hour == 9 and minute < 30):
        return {
            "include": True,
            "level": "full",
            "emphasis": "premarket_regime_and_gap"
        }

    # Opening (09:30-10:00)
    if hour == 9 and minute >= 30:
        return {
            "include": True,
            "level": "full",
            "emphasis": "gap_fill_vs_continuation"
        }

    # Regular session (10:00-15:00)
    if 10 <= hour < 15:
        # Check if price is near EH key levels (within 0.5%)
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

    # Closing (15:00-16:00)
    if 15 <= hour < 16:
        return {
            "include": False,
            "level": "minimal",
            "emphasis": "closing_structure"
        }

    # Afterhours/Closed
    return {
        "include": False,
        "level": "none",
        "emphasis": "none"
    }


def is_price_near_eh_levels(price: float, levels: EHLevels, threshold_pct: float = 0.5) -> str:
    """Check if price is near EH key levels"""

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

### 3.3 EH Data Structure (Sent to LLM)

```python
eh_context_for_llm = {
    "session": "premarket" | "opening" | "regular" | "closing" | "afterhours",
    "time_et": "09:45",
    "regime": "gap_and_go" | "gap_fill_bias" | "trend_continuation" | "range_day_setup",
    "bias": "bullish" | "bearish" | "neutral",
    "bias_confidence": 0.72,

    # Gap info
    "gap": {
        "direction": "up" | "down",
        "size": 1.30,
        "size_pct": 0.53,
        "status": "unfilled" | "partially_filled" | "filled"
    },

    # Key levels (only send relevant ones)
    "key_levels": {
        "yc": 245.50,      # Always send
        "pmh": 246.80,     # Send during premarket/opening
        "pml": 244.20,     # Send during premarket/opening
        "gap_fill_target": 245.50  # Send when gap_fill_bias
    },

    # Premarket structure description
    "pm_structure": "PM extended gap direction, holding above PMH"
}
```

---

## 4. Prompt Updates

### 4.1 Quick Update - Enhanced Version

```
Based on the provided market data, interpret the current market structure in one paragraph.

Language: {lang_name}

Data:
{analysis_json}

{eh_section}

Requirements:
- One coherent analysis paragraph, 80-150 words
- Interpret data meaning, explain current structure state
- If behavior conflicts with trend, explain why
- Include specific numbers (price levels, RVOL, etc.)
- No titles, bullets, or sections - just one paragraph
- No trading recommendations, only data interpretation
{eh_instruction}

Example (with EH):
Opening gapped up 1.3% then pulled back to test YC(245.50), premarket regime is gap_fill_bias, current price consolidating below PMH(246.80). RVOL 0.85 on the low side, no clear direction. If gap fills to YC with support bounce opportunity, otherwise watch for breakdown below 245. Overall waiting mode.
```

Where `{eh_section}` and `{eh_instruction}` are dynamically generated based on time:

**Premarket/Opening session:**
```
EH Context:
{eh_context_json}

Additional Requirements:
- Must mention premarket regime ({regime}) and Gap direction
- Explain current price position relative to PMH/PML/YC
- If gap_fill_bias, explain gap fill probability
- If gap_and_go, explain continuation conditions
```

**Regular session (price near EH key levels):**
```
Reference Levels:
- YC: {yc} (price distance {dist_yc}%)

Additional Requirements:
- Mention price relationship to YC (being attracted/breaking)
```

**Regular session (price far from EH):**
```
(No EH data sent)
```

### 4.2 5m Full Analysis - EH Enhanced

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

Where EH-related placeholders:

**`{eh_tldr_line}` (premarket/opening):**
```
- EH Regime: {regime} / Bias: {bias} / Gap: {gap_pct}%
```

**`{eh_context_section}` (premarket/opening):**
```
## EH Context
- Premarket Regime: {regime}
- Gap: {direction} {size} ({pct}%)
- Key Levels: YC {yc}, PMH {pmh}, PML {pml}
- Interpretation: {pm_structure}
```

**`{eh_scenario_note}` (when gap_fill_bias):**
```
> Gap Fill Note: If price fails at current level, watch for reversion to YC ({yc}).
```

**`{eh_risk_note}` (premarket/opening):**
```
- EH data based on premarket session, may shift at open
```

---

## 5. prepare_analysis_for_llm Updates

### 5.1 New Fields

```python
def prepare_analysis_for_llm(
    report: Dict[str, Any],
    ticker: str,
    timeframe: str,
    price: float,
    include_evidence: bool = True,
    eh_context: Optional[Dict] = None,  # New
    current_time_et: Optional[datetime] = None  # New
) -> Dict[str, Any]:
    """
    Prepare structured JSON to send to LLM

    New:
    - eh_context: EH context data
    - current_time_et: Current Eastern Time (for time-aware logic)
    """

    # ... existing logic ...

    # New: EH context processing
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
        # ... existing fields ...
        "eh": eh_data  # New
    }

    return result
```

### 5.2 Helper Functions

```python
def filter_eh_levels_by_relevance(levels: Dict, level: str) -> Dict:
    """Filter EH levels by importance level"""

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
    """Get current trading session name"""
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

## 6. Playbook Data Enhancement

### 6.1 Plan EH Type

When EH context exists and is `gap_fill_bias`, playbook may include `Plan EH`:

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

### 6.2 LLM Interpretation Requirements

- If playbook contains Plan EH, must mention in interpretation
- Explain gap fill logic: price tends to revert to YC
- Explain invalidation conditions: gap fill fails if price breaks PMH/PML

---

## 7. Example Outputs

### 7.1 Premarket Quick Update (9:15 ET)

```
Premarket gapped up 1.8%, regime is gap_and_go, price continues running above PMH(248.50). RVOL at 2.3 showing strong buying. After open, if 247.20 support holds and breaks 249 resistance, trend-following long structure established. Risk is opening volatility may trigger fakeout, recommend watching first 10 minutes volume for confirmation.
```

### 7.2 Opening Quick Update (9:45 ET)

```
After open, price pulled back from gap high 248.50 to consolidate near YC(245.20), regime shifted to gap_fill_bias. RVOL 0.92 normal, no clear direction. Price currently consolidating between PMH(248.50) and YC(245.20), if breaks below YC completing gap fill, watch 244 support below; if bounces and holds 247 then back to gap_and_go. Waiting mode.
```

### 7.3 Regular Session Quick Update (11:30 ET, far from EH)

```
Price in tight 253-255 range, RVOL 0.65 continues shrinking, market in wait-and-see mode. 255 resistance tested 3 times without breaking, 253 support holding for now. Behavior pattern shows mild accumulation but insufficient volume for breakout. Watch for afternoon volume expansion to pick direction.
```

---

## 8. Implementation Checklist

- [ ] Update `prepare_analysis_for_llm()` to add EH parameters
- [ ] Implement `should_include_eh_context()` time-based logic
- [ ] Update `PROMPT_QUICK_UPDATE` to support EH placeholders
- [ ] Update `PROMPT_5M_ANALYSIS` to support EH sections
- [ ] Frontend passes EH context to narrative API
- [ ] Test EH data sending logic at different times
- [ ] Test playbook Plan EH interpretation

---

## Appendix: Prohibited Language

| Prohibited | Reason |
|------------|--------|
| "guaranteed" / "sure win" | Misleading |
| "100% accurate" | Impossible |
| "AI predicts price" | Beyond capabilities |
| "will definitely" | Certainty expression |
| "you should buy/sell" | Investment advice |
