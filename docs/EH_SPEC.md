# Extended Hours (EH) System Specification

> Premarket/Afterhours Structure Completion Engine for KLineLens
>
> Version: 1.0 Draft

---

## 0. Executive Summary

### 0.1 What This Is

An **Extended Hours Context Provider** that:
1. Fills the "overnight gap" in market structure analysis
2. Provides opening-day "prior" for regular session trading
3. Generates key levels that persist as high-priority S/R zones

### 0.2 What This Is NOT

- NOT a premarket trading system
- NOT a real-time premarket alert system
- NOT a prediction engine for premarket price direction

### 0.3 Core Value

| Problem | Solution |
|---------|----------|
| Opening "map" is blank | Pre-populate PMH/PML/YC/AHH/AHL levels |
| Day-type unknown | Classify premarket structure (Gap-and-Go, Gap-Fill, etc.) |
| Overnight behavior invisible | Detect EH absorption/distribution patterns |

---

## 1. Data Requirements

### 1.1 Required Data Segments

| Segment | Time (ET) | Priority | Min Timeframe |
|---------|-----------|----------|---------------|
| Yesterday Regular | 09:30-16:00 | Required | 1m |
| Afterhours (AH) | 16:00-20:00 | Required | 1m |
| Premarket (PM) | 04:00-09:30 | Required | 1m |

**Note:** Only need 1-minute bars with OHLCV. No tick data required.

### 1.2 Data Sources for Extended Hours

#### Option A: Yahoo Finance (推荐 MVP 方案 - 免费)

Yahoo Finance 通过 `prepost=True` 参数免费提供盘前盘后数据：

```python
# yfinance 获取 Extended Hours
provider = YFinanceProvider()
bars = provider.get_bars_extended("TSLA", "1m", "2d")
```

**特点:**
| 功能 | 支持情况 | 说明 |
|------|---------|------|
| 盘前 (04:00-09:30 ET) | ✅ | 可提取 PMH/PML |
| 盘后 (16:00-20:00 ET) | ✅ | 可提取 AHH/AHL |
| 成本 | **免费** | 无需 API Key |
| 延迟 | 15-20 分钟 | 非实时，但足够结构分析 |
| 数据稳定性 | ⚠️ 偶尔缺失 | 用于关键位提取足够 |

**MVP 推荐用法:**
- TwelveData 做正盘主数据源（可靠成交量）
- Yahoo Finance 补充盘前盘后数据（免费）
- 达到 `partial` 或延迟版 `complete` 模式

#### Option B: TwelveData Extended Hours

TwelveData API supports extended hours via the `prepost` parameter:

```
GET /time_series?symbol=TSLA&interval=1min&prepost=true
```

**API Parameters:**
- `prepost=true`: Include premarket and afterhours data
- Endpoints supported: `/time_series`, `/quote`, `/price`, `/eod`
- Supported intervals: 1min, 5min, 15min, 30min

**Coverage:**
- Historical data: 04:00 AM - 8:00 PM ET
- Real-time data: 7:00 AM - 8:00 PM ET (Pro plan required)

**Limitations:**
- **Historical EH data**: Available only for records older than 1 day (free tier OK)
- **Real-time EH data**: Requires Pro plan ($79/month)
- Extended hours volume is sparse
- Only U.S. markets supported (no Canadian/international tickers)
- Response includes `is_extended_hours` boolean field

#### 数据源对比

| 方案 | 成本 | 延迟 | 可达模式 | 推荐场景 |
|------|------|------|----------|----------|
| Yahoo Finance | 免费 | 15-20分钟 | partial/complete (延迟) | **MVP 推荐** |
| TwelveData Free | 免费 | T-1 | partial | 仅历史 EH |
| TwelveData Pro | $79/月 | 实时 | complete | 专业用户 |

**MVP Strategy:**
- 使用 Yahoo Finance `prepost=True` 获取盘前盘后数据（免费）
- 解决开盘断层问题，提取 PMH/PML/AHH/AHL
- 15-20 分钟延迟对于结构分析可接受

### 1.3 Data Quality Tiers (Core Mechanism)

**This is the most critical design decision for MVP:**

| Tier | Data Available | What Works | What's Disabled |
|------|----------------|------------|-----------------|
| `complete` | Today's PM (real-time) + Yesterday's AH + Regular | Full EH analysis | Nothing |
| `partial` | Yesterday's AH + Regular (T-1) | YC/YH/YL/AHH/AHL levels, AH risk assessment | PM regime, PM absorption, today's gap |
| `minimal` | Only Regular session | YC/YH/YL only | All EH-specific analysis |

**MVP Default: `partial` (T-1 mode)**

Most users won't have Pro tier, so the system must be designed around `partial` as the default:

```python
# Data quality determines what gets computed
if data_quality == "complete":
    # Full analysis available
    compute_pm_regime()
    compute_pm_absorption()
    compute_gap_analysis()
elif data_quality == "partial":
    # T-1 mode: only historical EH
    compute_yc_yh_yl()
    compute_ah_levels()
    compute_ah_risk()
    # SKIP: pm_regime, pm_absorption, today's gap
    pm_regime = "unavailable"
elif data_quality == "minimal":
    # Emergency fallback
    compute_yc_yh_yl()
    # Everything else unavailable
```

**UI Implications:**

| Tier | Display |
|------|---------|
| `complete` | Full EH panel with regime, bias, zones |
| `partial` | "T-1 Mode: Using yesterday's structure" + YC/YH/YL/AHH/AHL |
| `minimal` | "EH data unavailable: YC mode only" |

---

## 2. EH-Specific Normalization

### 2.1 Why Different Thresholds

Extended hours characteristics:
- **Low volume**: 5-10% of regular session
- **Wide spreads**: 2-5x normal spread
- **Jump prices**: Gaps between trades
- **More fakeouts**: Thin liquidity causes more false signals

**Critical Rule:** Never compare EH metrics to regular session baselines.

### 2.2 EH-RVOL (Extended Hours Relative Volume)

```python
# Premarket RVOL (compare to premarket history, NOT regular session)
PM_RVOL = PMVolume[t] / AvgPMVolume[same_time_window, past_N_days]

# Afterhours RVOL
AH_RVOL = AHVolume[t] / AvgAHVolume[same_time_window, past_N_days]
```

**Parameters:**
- `N = 10`: Look back 10 trading days
- Time windows: 30-minute buckets within EH session

**Interpretation:**

| EH-RVOL | Meaning |
|---------|---------|
| < 0.5 | Very quiet (no conviction) |
| 0.5 - 1.5 | Normal for EH |
| > 1.5 | Elevated activity (pay attention) |
| > 2.5 | Unusual spike (likely news-driven) |

### 2.3 EH Range Score

```python
EH_range = PMH - PML  # or AHH - AHL for afterhours
EH_range_score = EH_range / AvgEHRange[past_N_days]
```

**Interpretation:**

| Score | Meaning |
|-------|---------|
| < 0.5 | Compressed (potential energy) |
| 0.5 - 1.2 | Normal |
| > 1.2 | Expanded (breakout day potential) |
| > 2.0 | High volatility day setup |

---

## 3. Key Levels Extraction

### 3.1 Level Definitions

| Level | Definition | Priority |
|-------|------------|----------|
| `YC` | Yesterday close (16:00 ET) | Highest |
| `YH` | Yesterday high | High |
| `YL` | Yesterday low | High |
| `PMH` | Premarket high | High |
| `PML` | Premarket low | High |
| `AHH` | Afterhours high | Medium |
| `AHL` | Afterhours low | Medium |
| `GAP` | Estimated open - YC | Derived |

### 3.2 Level Calculation

```python
def extract_eh_levels(
    yesterday_bars: List[Bar],  # 09:30-16:00 ET
    afterhours_bars: List[Bar], # 16:00-20:00 ET
    premarket_bars: List[Bar],  # 04:00-09:30 ET
) -> EHLevels:

    return EHLevels(
        yc=yesterday_bars[-1].c,
        yh=max(bar.h for bar in yesterday_bars),
        yl=min(bar.l for bar in yesterday_bars),
        pmh=max(bar.h for bar in premarket_bars) if premarket_bars else None,
        pml=min(bar.l for bar in premarket_bars) if premarket_bars else None,
        ahh=max(bar.h for bar in afterhours_bars) if afterhours_bars else None,
        ahl=min(bar.l for bar in afterhours_bars) if afterhours_bars else None,
        gap=premarket_bars[-1].c - yesterday_bars[-1].c if premarket_bars else 0,
    )
```

### 3.3 Level Role Assignment

Each level gets a role based on price position:

```python
def assign_level_roles(levels: EHLevels, current_price: float) -> Dict[str, str]:
    roles = {}

    # YC is always a magnet (gap-fill target)
    roles["YC"] = "magnet"

    # PMH/PML are breakout/breakdown triggers
    if current_price < levels.pmh:
        roles["PMH"] = "breakout_trigger"
    else:
        roles["PMH"] = "support_flip"  # Was resistance, now support

    if current_price > levels.pml:
        roles["PML"] = "breakdown_trigger"
    else:
        roles["PML"] = "resistance_flip"

    # YH/YL are major reference levels
    roles["YH"] = "major_resistance" if current_price < levels.yh else "conquered"
    roles["YL"] = "major_support" if current_price > levels.yl else "lost"

    return roles
```

---

## 4. Premarket Regime Classification

> ⚠️ **REQUIRES `data_quality: complete`**
>
> This entire section requires **today's real-time premarket data**.
> In T-1 mode (`partial`), premarket regime classification is **DISABLED**.
>
> **Why:** Using yesterday's premarket to classify today's regime is a logical error
> that will cause incorrect trading decisions.

### 4.0 Data Quality Gate

```python
def classify_premarket_regime(...) -> Tuple[str, float]:
    # CRITICAL: Check data quality first
    if data_quality != "complete":
        return ("unavailable", 0.0)

    # Only proceed if we have today's PM data
    if not pm_bars or len(pm_bars) < 10:
        return ("unavailable", 0.0)

    # ... classification logic ...
```

**UI Display for `unavailable`:**
```
Premarket Regime: —
"Real-time premarket data required (Pro tier)"
```

### 4.1 Four Premarket Regimes

| Regime | Conditions | Implication |
|--------|------------|-------------|
| **Trend-Continuation** | PM direction = Yesterday direction, EH_range_score > 0.8 | Momentum day likely |
| **Gap-and-Go** | \|GAP\| > 1% of YC, PM doesn't fill gap | Continuation beyond gap |
| **Gap-Fill Bias** | \|GAP\| > 0.5%, PM trending toward YC | Gap likely to fill |
| **Range Day Setup** | EH_range_score < 0.6, EH_RVOL < 0.8 | Choppy/range day |

### 4.2 Classification Algorithm (requires `complete` mode)

```python
def classify_premarket_regime(
    levels: EHLevels,
    yesterday_direction: str,  # "up" | "down"
    pm_bars: List[Bar],
    eh_range_score: float,
    eh_rvol: float,
) -> Tuple[str, float]:  # (regime, confidence)

    gap_pct = levels.gap / levels.yc if levels.yc else 0

    # Calculate PM direction
    pm_direction = "up" if pm_bars[-1].c > pm_bars[0].o else "down"

    # Check if PM is filling gap
    pm_moved_toward_yc = (
        (levels.gap > 0 and pm_bars[-1].c < levels.pmh - 0.3 * (levels.pmh - levels.yc)) or
        (levels.gap < 0 and pm_bars[-1].c > levels.pml + 0.3 * (levels.yc - levels.pml))
    )

    # Classification logic
    if eh_range_score < 0.6 and eh_rvol < 0.8:
        return ("range_day_setup", 0.7)

    if abs(gap_pct) > 0.01:  # > 1% gap
        if pm_moved_toward_yc:
            return ("gap_fill_bias", 0.65)
        else:
            return ("gap_and_go", 0.6)

    if pm_direction == yesterday_direction and eh_range_score > 0.8:
        return ("trend_continuation", 0.7)

    # Default
    return ("range_day_setup", 0.5)
```

### 4.3 Bias Inference

```python
def infer_premarket_bias(
    regime: str,
    levels: EHLevels,
    pm_bars: List[Bar],
) -> str:  # "bullish" | "bearish" | "slightly_bullish" | "slightly_bearish" | "neutral"

    current = pm_bars[-1].c

    if regime == "gap_and_go":
        return "bullish" if levels.gap > 0 else "bearish"

    if regime == "gap_fill_bias":
        # Bias toward gap fill = opposite of gap direction
        return "slightly_bearish" if levels.gap > 0 else "slightly_bullish"

    if regime == "trend_continuation":
        return "bullish" if current > levels.yc else "bearish"

    return "neutral"
```

---

## 5. EH Behavior Detection

### 5.0 Data Quality Requirements

| Pattern | Required Data Quality | Notes |
|---------|----------------------|-------|
| PM Absorption | `complete` only | Requires today's PM bars |
| PM Distribution | `complete` only | Requires today's PM bars |
| AH Drift | `partial` or `complete` | Uses yesterday's AH (T-1 OK) |
| AH Reversal | `partial` or `complete` | Uses yesterday's AH (T-1 OK) |

**In T-1 mode (`partial`):** Only AH patterns are available. PM patterns return `null`.

### 5.1 EH-Specific Behavior Patterns

Extended hours has its own behavior vocabulary (simplified from regular session):

| Pattern | Detection | Meaning | Data Quality |
|---------|-----------|---------|--------------|
| **PM Absorption** | Multiple tests of PML/YC without break, elevated EH_RVOL | Buyers defending | `complete` |
| **PM Distribution** | Multiple tests of PMH without break, elevated EH_RVOL | Sellers capping | `complete` |
| **AH Drift** | Gradual move on low volume after close | Continuation signal | `partial`+ |
| **AH Reversal** | Sharp move opposite to day's direction on decent volume | Next-day caution | `partial`+ |

### 5.2 Absorption Detection

```python
def detect_pm_absorption(
    pm_bars: List[Bar],
    levels: EHLevels,
    eh_rvol: float,
) -> Optional[Dict]:
    """
    Detect premarket absorption (demand or supply)
    """
    pml = levels.pml
    pmh = levels.pmh
    yc = levels.yc

    # Count tests of key levels
    pml_tests = sum(1 for bar in pm_bars if bar.l <= pml * 1.002 and bar.c > pml)
    pmh_tests = sum(1 for bar in pm_bars if bar.h >= pmh * 0.998 and bar.c < pmh)
    yc_tests = sum(1 for bar in pm_bars if abs(bar.l - yc) / yc < 0.003 and bar.c > yc)

    # Demand absorption: multiple PML/YC tests with reclaim
    if pml_tests >= 2 and eh_rvol > 0.8:
        return {
            "type": "demand_absorption",
            "level": pml,
            "tests": pml_tests,
            "confidence": min(0.3 + pml_tests * 0.15, 0.8),
        }

    # Supply absorption: multiple PMH tests with rejection
    if pmh_tests >= 2 and eh_rvol > 0.8:
        return {
            "type": "supply_absorption",
            "level": pmh,
            "tests": pmh_tests,
            "confidence": min(0.3 + pmh_tests * 0.15, 0.8),
        }

    return None
```

---

## 6. Afterhours Risk Assessment

### 6.1 Purpose

Predict afterhours risk profile for next-day planning (NOT price prediction).

### 6.2 Risk Factors

```python
def assess_afterhours_risk(
    regular_bars: List[Bar],  # Today's regular session
    features: Dict,
) -> Dict:
    """
    Assess afterhours risk profile based on regular session close
    """
    # 1. Close position in range
    day_range = max(bar.h for bar in regular_bars) - min(bar.l for bar in regular_bars)
    close = regular_bars[-1].c
    low = min(bar.l for bar in regular_bars)
    close_position = (close - low) / day_range if day_range > 0 else 0.5

    # 2. Late session volume (last 30 minutes)
    late_bars = regular_bars[-30:]  # Last 30 1-minute bars
    late_volume = sum(bar.v for bar in late_bars)
    avg_30min_volume = sum(bar.v for bar in regular_bars) / (len(regular_bars) / 30)
    late_rvol = late_volume / avg_30min_volume if avg_30min_volume > 0 else 1.0

    # 3. Was it a trend day?
    # Count bars closing in trend direction
    up_closes = sum(1 for bar in regular_bars if bar.c > bar.o)
    is_trend_day = abs(up_closes / len(regular_bars) - 0.5) > 0.15
    trend_direction = "up" if up_closes > len(regular_bars) / 2 else "down"

    # Risk assessment
    if close_position > 0.8:  # Closed near high
        if late_rvol > 1.3 and trend_direction == "up":
            risk = "low"
            behavior = "continuation"
        else:
            risk = "medium"
            behavior = "mean_revert"
    elif close_position < 0.2:  # Closed near low
        if late_rvol > 1.3 and trend_direction == "down":
            risk = "low"
            behavior = "continuation"
        else:
            risk = "medium"
            behavior = "mean_revert"
    else:  # Closed in middle
        risk = "medium"
        behavior = "drift"

    # High risk override
    if not is_trend_day and late_rvol < 0.7:
        risk = "high"  # Indecision going into close

    return {
        "risk": risk,
        "likely_behavior": behavior,
        "close_position": close_position,
        "late_rvol": late_rvol,
        "is_trend_day": is_trend_day,
    }
```

---

## 7. Output: EHContext

### 7.1 Field Availability by Data Quality

| Field | `complete` | `partial` (T-1) | `minimal` |
|-------|------------|-----------------|-----------|
| `levels.yc/yh/yl` | ✅ | ✅ | ✅ |
| `levels.ahh/ahl` | ✅ | ✅ | ❌ |
| `levels.pmh/pml` | ✅ | ❌ | ❌ |
| `levels.gap` | ✅ | ❌ (use 0) | ❌ |
| `premarket_regime` | ✅ | ❌ (`"unavailable"`) | ❌ |
| `premarket_bias` | ✅ | ❌ (`"neutral"`) | ❌ |
| `eh_range_score` | ✅ | ❌ (use 0) | ❌ |
| `eh_rvol` | ✅ | ❌ (use 0) | ❌ |
| `pm_absorption` | ✅ | ❌ (`null`) | ❌ |
| `ah_risk` | ✅ | ✅ | ❌ |
| `key_zones` | Full list | YC/YH/YL/AHH/AHL only | YC/YH/YL only |

### 7.2 Data Structure

```python
@dataclass
class EHContext:
    """
    Extended Hours Context - Prior for regular session analysis

    IMPORTANT: Many fields are only populated when data_quality == "complete".
    In T-1 mode (partial), PM-related fields are unavailable.
    """
    # Key Levels (always available, but PM levels only in complete mode)
    levels: EHLevels

    # Premarket Analysis (ONLY in complete mode)
    premarket_regime: str  # "unavailable" if partial/minimal
    premarket_bias: str    # "neutral" if partial/minimal
    regime_confidence: float  # 0.0 if partial/minimal

    # EH Metrics (ONLY in complete mode)
    eh_range_score: float   # 0.0 if partial/minimal
    eh_rvol: float          # 0.0 if partial/minimal

    # Key Zones with Roles (filtered by available levels)
    key_zones: List[Dict]   # [{zone: "YC", price: 424.10, role: "magnet"}, ...]

    # Behavior Detection
    pm_absorption: Optional[Dict]  # None if partial/minimal (requires PM)
    ah_risk: Optional[Dict]        # Available in partial+ (uses yesterday's AH)

    # Expected Behaviors (filtered by what's available)
    expected_behaviors: List[str]  # i18n keys

    # Metadata
    generated_at: datetime
    data_quality: str  # complete, partial, minimal


@dataclass
class EHLevels:
    """Key price levels from extended hours"""
    yc: float              # Yesterday close (always available)
    yh: float              # Yesterday high (always available)
    yl: float              # Yesterday low (always available)
    pmh: Optional[float]   # Premarket high (complete only)
    pml: Optional[float]   # Premarket low (complete only)
    ahh: Optional[float]   # Afterhours high (partial+)
    ahl: Optional[float]   # Afterhours low
    gap: float             # Estimated gap (PM last - YC)
```

### 7.3 JSON Output Examples

#### Example A: `complete` mode (with real-time PM data)

```json
{
  "levels": {
    "yc": 424.10,
    "yh": 427.80,
    "yl": 421.90,
    "pmh": 426.20,
    "pml": 423.40,
    "ahh": 425.10,
    "ahl": 423.90,
    "gap": 1.85
  },
  "premarket_regime": "gap_fill_bias",
  "premarket_bias": "slightly_bearish",
  "regime_confidence": 0.65,
  "eh_range_score": 1.35,
  "eh_rvol": 0.82,
  "key_zones": [
    {"zone": "YC", "price": 424.10, "role": "magnet"},
    {"zone": "PMH", "price": 426.20, "role": "breakout_trigger"},
    {"zone": "PML", "price": 423.40, "role": "breakdown_trigger"},
    {"zone": "YH", "price": 427.80, "role": "major_resistance"},
    {"zone": "YL", "price": 421.90, "role": "major_support"}
  ],
  "pm_absorption": {
    "type": "demand_absorption",
    "level": 423.40,
    "tests": 3,
    "confidence": 0.75
  },
  "ah_risk": {
    "risk": "medium",
    "likely_behavior": "mean_revert",
    "close_position": 0.62,
    "late_rvol": 1.15,
    "is_trend_day": false
  },
  "expected_behaviors": [
    "eh.expect.gap_fill_test",
    "eh.expect.pmh_resistance",
    "eh.expect.yc_magnet"
  ],
  "generated_at": "2026-01-15T09:25:00Z",
  "data_quality": "complete"
}
```

#### Example B: `partial` mode (T-1, MVP default)

```json
{
  "levels": {
    "yc": 424.10,
    "yh": 427.80,
    "yl": 421.90,
    "pmh": null,
    "pml": null,
    "ahh": 425.10,
    "ahl": 423.90,
    "gap": 0
  },
  "premarket_regime": "unavailable",
  "premarket_bias": "neutral",
  "regime_confidence": 0.0,
  "eh_range_score": 0.0,
  "eh_rvol": 0.0,
  "key_zones": [
    {"zone": "YC", "price": 424.10, "role": "magnet"},
    {"zone": "YH", "price": 427.80, "role": "major_resistance"},
    {"zone": "YL", "price": 421.90, "role": "major_support"},
    {"zone": "AHH", "price": 425.10, "role": "ah_high"},
    {"zone": "AHL", "price": 423.90, "role": "ah_low"}
  ],
  "pm_absorption": null,
  "ah_risk": {
    "risk": "medium",
    "likely_behavior": "mean_revert",
    "close_position": 0.62,
    "late_rvol": 1.15,
    "is_trend_day": false
  },
  "expected_behaviors": [
    "eh.expect.yc_magnet",
    "eh.expect.ah_structure_reference"
  ],
  "generated_at": "2026-01-15T09:25:00Z",
  "data_quality": "partial",
  "data_quality_note": "T-1 mode: Using yesterday's structure. Real-time premarket requires Pro tier."
}
```

#### Example C: `minimal` mode (fallback)

```json
{
  "levels": {
    "yc": 424.10,
    "yh": 427.80,
    "yl": 421.90,
    "pmh": null,
    "pml": null,
    "ahh": null,
    "ahl": null,
    "gap": 0
  },
  "premarket_regime": "unavailable",
  "premarket_bias": "neutral",
  "regime_confidence": 0.0,
  "eh_range_score": 0.0,
  "eh_rvol": 0.0,
  "key_zones": [
    {"zone": "YC", "price": 424.10, "role": "magnet"},
    {"zone": "YH", "price": 427.80, "role": "major_resistance"},
    {"zone": "YL", "price": 421.90, "role": "major_support"}
  ],
  "pm_absorption": null,
  "ah_risk": null,
  "expected_behaviors": [
    "eh.expect.yc_magnet"
  ],
  "generated_at": "2026-01-15T09:25:00Z",
  "data_quality": "minimal",
  "data_quality_note": "EH data unavailable. Only YC/YH/YL levels provided."
}
```

---

## 8. Integration with Regular Session Analysis

### 8.1 Zone Priority Injection

When EH context is available, inject levels into zone priority:

```python
def inject_eh_zones(
    eh_context: EHContext,
    regular_zones: Dict[str, List[Zone]],
    current_price: float,
) -> Dict[str, List[Zone]]:
    """
    Inject EH levels as high-priority zones into regular analysis
    """
    levels = eh_context.levels

    # Create zones from EH levels
    eh_zones = []

    # PMH as resistance (if price below)
    if levels.pmh and current_price < levels.pmh:
        eh_zones.append(Zone(
            low=levels.pmh * 0.998,
            high=levels.pmh * 1.002,
            score=0.9,  # High priority
            touches=1,
            rejections=0,
        ))

    # PML as support (if price above)
    if levels.pml and current_price > levels.pml:
        eh_zones.append(Zone(
            low=levels.pml * 0.998,
            high=levels.pml * 1.002,
            score=0.9,
            touches=1,
            rejections=0,
        ))

    # YC as magnet zone
    eh_zones.append(Zone(
        low=levels.yc * 0.998,
        high=levels.yc * 1.002,
        score=0.85,
        touches=1,
        rejections=0,
    ))

    # Merge with existing zones (EH zones take priority)
    # ... merge logic

    return merged_zones
```

### 8.2 Opening Protection Mode

First 10 minutes after open, apply stricter confirmation:

```python
def apply_opening_protection(
    signal: Signal,
    eh_context: EHContext,
    minutes_since_open: int,
) -> Signal:
    """
    Apply stricter confirmation during opening period
    """
    if minutes_since_open > 10:
        return signal

    # During opening protection:
    # 1. Require 2 candles for breakout confirmation (not 1)
    # 2. Only high-grade signals for EH levels

    key_levels = [
        eh_context.levels.pmh,
        eh_context.levels.pml,
        eh_context.levels.yc,
        eh_context.levels.yh,
        eh_context.levels.yl,
    ]

    is_at_key_level = any(
        abs(signal.level - level) / level < 0.003
        for level in key_levels if level
    )

    if is_at_key_level and signal.type == "breakout_attempt":
        # Downgrade confidence during opening
        signal.confidence *= 0.7
        signal.volume_quality = "pending"  # Require confirmation

    return signal
```

### 8.3 AnalysisReport Enhancement

Add EH context to the main analysis report:

```python
@dataclass
class AnalysisReport:
    # ... existing fields ...

    # Extended Hours Context (optional, populated pre-market)
    eh_context: Optional[EHContext] = None
```

---

## 9. API Endpoint Design

### 9.1 New Endpoint: `/v1/eh-context`

```
GET /v1/eh-context?ticker=TSLA
```

**Response:**
```json
{
  "ticker": "TSLA",
  "eh_context": { ... },  // EHContext object
  "status": "complete"    // complete, partial, unavailable
}
```

### 9.2 Enhanced `/v1/analyze` Endpoint

Add optional `include_eh` parameter:

```
POST /v1/analyze
{
  "ticker": "TSLA",
  "tf": "1m",
  "include_eh": true  // Include EH context in response
}
```

---

## 10. Implementation Plan

### 10.1 File Structure

```
packages/core/src/
├── extended_hours.py    # NEW: EH analysis module
├── models.py            # UPDATE: Add EHContext, EHLevels
├── analyze.py           # UPDATE: Integrate EH context

apps/api/src/
├── providers/
│   └── twelvedata_provider.py  # UPDATE: Support extended_hours param
├── main.py              # UPDATE: Add /v1/eh-context endpoint
```

### 10.2 Implementation Order

1. **Phase 1: Data Layer**
   - Update TwelveData provider to fetch extended hours data
   - Add helper to segment bars by session (regular/PM/AH)

2. **Phase 2: Core EH Module**
   - Create `extended_hours.py` with:
     - `extract_eh_levels()`
     - `calculate_eh_metrics()`
     - `classify_premarket_regime()`
     - `detect_pm_absorption()`
     - `assess_afterhours_risk()`
     - `build_eh_context()`

3. **Phase 3: Integration**
   - Add EHContext to models
   - Update analyze.py to optionally include EH
   - Add `/v1/eh-context` endpoint

4. **Phase 4: Frontend**
   - Display EH levels on chart
   - Show EH context panel
   - Opening protection indicator

### 10.3 Testing Strategy

```
packages/core/tests/
├── test_extended_hours.py
│   ├── test_extract_eh_levels()
│   ├── test_eh_metrics_calculation()
│   ├── test_premarket_regime_classification()
│   ├── test_absorption_detection()
│   ├── test_afterhours_risk_assessment()
│   └── test_integration_with_analyze()
```

**Synthetic Test Data:**
- Gap-up with premarket continuation
- Gap-down with gap-fill behavior
- Low-volume premarket (range setup)
- High-volume premarket breakout

---

## 11. Parameters

### 11.1 EH Analysis Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `eh_rvol_lookback` | 10 | Days to calculate EH RVOL baseline |
| `eh_range_lookback` | 10 | Days to calculate EH range baseline |
| `gap_significant_pct` | 0.5 | Gap % to consider significant |
| `gap_large_pct` | 1.0 | Gap % to consider large |
| `absorption_min_tests` | 2 | Min level tests for absorption |
| `absorption_rvol_threshold` | 0.8 | Min EH RVOL for absorption detection |
| `opening_protection_minutes` | 10 | Minutes to apply opening protection |

### 11.2 Zone Priority Weights

| Zone Type | Base Score |
|-----------|------------|
| PMH/PML | 0.9 |
| YC | 0.85 |
| YH/YL | 0.8 |
| AHH/AHL | 0.7 |

---

## 12. i18n Keys

### 12.1 Premarket Regime

```json
{
  "eh.regime.trend_continuation": "趋势延续",
  "eh.regime.gap_and_go": "跳空延续",
  "eh.regime.gap_fill_bias": "补缺口倾向",
  "eh.regime.range_day_setup": "震荡日格局"
}
```

### 12.2 Expected Behaviors

```json
{
  "eh.expect.gap_fill_test": "可能测试缺口补回",
  "eh.expect.pmh_resistance": "盘前高点可能构成阻力",
  "eh.expect.pml_support": "盘前低点可能构成支撑",
  "eh.expect.yc_magnet": "昨收价可能成为磁吸位",
  "eh.expect.trend_continuation": "趋势可能延续",
  "eh.expect.breakout_potential": "突破潜力较大"
}
```

### 12.3 Risk Assessment

```json
{
  "eh.risk.low": "低风险",
  "eh.risk.medium": "中等风险",
  "eh.risk.high": "高风险",
  "eh.behavior.continuation": "延续",
  "eh.behavior.mean_revert": "回归均值",
  "eh.behavior.drift": "漂移"
}
```

### 12.4 Data Quality Messages

```json
{
  "eh.quality.complete": "完整模式",
  "eh.quality.partial": "T-1 模式",
  "eh.quality.minimal": "仅 YC 模式",
  "eh.quality.partial_note": "使用昨日结构数据。实时盘前需要 Pro 版本。",
  "eh.quality.minimal_note": "扩展时段数据不可用。仅提供 YC/YH/YL。",
  "eh.regime.unavailable": "不可用",
  "eh.regime.unavailable_note": "实时盘前数据需要 Pro 版本",
  "eh.expect.ah_structure_reference": "参考昨日盘后结构"
}
```

---

## Appendix A: TwelveData Extended Hours Verification

### API Call Example

```bash
# Historical extended hours (free tier, T-1 delay)
curl "https://api.twelvedata.com/time_series?symbol=TSLA&interval=1min&outputsize=500&prepost=true&apikey=YOUR_KEY"
```

### Expected Response

Should include bars with timestamps outside 09:30-16:00 ET:
- Premarket: 04:00-09:29 ET
- Afterhours: 16:01-20:00 ET

Each bar includes `is_extended_hours` field:
```json
{
  "datetime": "2026-01-14 07:30:00",
  "open": "425.50",
  "high": "425.80",
  "low": "425.30",
  "close": "425.60",
  "volume": "1234"
}
```

### Data Quality Tiers

| Tier | Data Available | `data_quality` Value |
|------|----------------|----------------------|
| Complete | PM + AH + Regular (all 1m) | `complete` |
| Partial | PM missing, AH + Regular available | `partial` |
| Minimal | Only Regular session | `minimal` |

### Fallback Strategy

If TwelveData extended hours unavailable:
1. Use Yahoo Finance for daily-level gap data (YC/YH/YL)
2. Mark `data_quality: "minimal"`
3. Only provide YC/YH/YL levels
4. Skip PM/AH specific analysis (regime, absorption)
5. Display notice: "Extended hours data unavailable"

---

## Appendix B: Market Hours Reference

| Session | ET Time | UTC Time (Winter) |
|---------|---------|-------------------|
| Premarket | 04:00-09:30 | 09:00-14:30 |
| Regular | 09:30-16:00 | 14:30-21:00 |
| Afterhours | 16:00-20:00 | 21:00-01:00 |

Note: During DST, subtract 1 hour from UTC times.
