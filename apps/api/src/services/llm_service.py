"""
LLM Narrative 服务模块 v2

事件驱动的市场叙事生成：
- 5m: 结构分析（Hard trigger 时触发）
- 1m: 执行确认（确认/否定 5m 论点）
- 1D: 背景框架（低频，大结构）
- 聚合更新：冷却期结束后合并事件

设计原则：
- LLM 不预测价格，只解释结构
- 每个结论必须有证据支持 [#bar_index]
- 输出像终端，不像作文
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
import httpx

logger = logging.getLogger(__name__)

# ============ System Prompt (通用约束) ============

SYSTEM_PROMPT = """You are KLineLens Narrative Engine. You must:
1) Never claim certainty. Use probabilities/conditions and clear invalidation.
2) Only use the provided JSON. Do not invent prices, zones, events, or metrics.
3) Every key conclusion must cite at least 1 evidence item with [#bar_index].
4) Output must be concise, structured, and action-oriented (like a trading terminal).
5) If data_quality flags indicate missing/unreliable volume, explicitly downgrade confidence and avoid volume-confirmed language.
6) Avoid prohibited phrases: "guaranteed", "稳赚", "必赚", "100% accurate", "AI predicts price", "will definitely".
7) Use the user language as specified.
8) When referencing metrics, use exact numbers from the provided JSON.
9) Action must be one of: WAIT / WATCH / TRIGGERED (for execution signals).
10) Always interpret Effort vs Result using VSA logic when available.

In Evidence chain, try to include at least one item from each category if available:
- Zone interaction (approach/test/reject/accept)
- Breakout checklist (close x2, RVOL, Result)
- Effort vs Result (VSA: absorption/true push/dry-up/easy move)
If any category is missing, state "not observed / data unavailable".
"""

# ============ 5m 事件驱动分析 Prompt ============

PROMPT_5M_ANALYSIS = """Write an evidence-backed 5m market-structure update for KLineLens.

CONTEXT:
- This report is triggered by a structural event. Focus on WHAT changed, WHY it matters, and WHAT to watch next.
- Use provided zones/metrics/evidence only.
- Language: {lang_name}

INPUT DATA:
{analysis_json}

OUTPUT FORMAT (strict, use {lang_name}):

## TL;DR
- Regime / Breakout / Behavior (one line each)
- **Action**: WAIT / WATCH / TRIGGERED (pick one)
- **Trigger**: specific condition(s), e.g., "need RVOL ≥ 1.8 + close x2"

## What Changed
- Bullet 1 with evidence [#bar_index]
- Bullet 2 with evidence [#bar_index]
- (max 3 bullets)

## Evidence Chain
- Evidence type + plain explanation + key numbers + [#bar_index]
- (3-6 bullets, ranked by importance)

## Key Zones
| Level | Type | Distance | Significance |
| --- | --- | --- | --- |
(top 4 zones)

## Scenarios
**A (Primary)**: condition → path → invalidation
**B (Alternate)**: condition → path → invalidation

## Risk Notes
- Data quality, volume availability, provider delay
- (1-3 bullets)

STYLE: No fluff. Use "if/then" language. State low confidence reasons explicitly.
"""

# ============ 1m 执行确认 Prompt ============

PROMPT_1M_CONFIRMATION = """You are generating a 1m execution confirmation note (NOT a full analysis).
Goal: confirm or deny the higher-timeframe thesis using 1m volume+price behavior.

Language: {lang_name}

INPUT DATA:
{analysis_json}

OUTPUT FORMAT (strict, use {lang_name}):

## Status
**[CONFIRMING / NEUTRAL / CONFLICTING]**

## Checklist
| Factor | Status | Value |
| --- | --- | --- |
| Close ×2 | ✓/✗ | ... |
| RVOL ≥ 1.8 | ✓/✗ | ... |
| Result ≥ 0.6 ATR | ✓/✗ | ... |
| Absorption Clue | Present/Absent | ... |

## Micro Read
- What is visible in evidence (wicks, sweeps, dry-up/spike)
- Each bullet cites [#bar_index]
- (2-4 bullets max)

## Next Trigger
One clear condition to flip from WAIT→WATCH or WATCH→TRIGGERED.

RULES:
- Never infer "派发/吸筹" from 1m alone. Use neutral language like "absorption clue".
- If volume is unreliable/N.A., say "confirmation unavailable".
"""

# ============ 1D 背景框架 Prompt ============

PROMPT_1D_CONTEXT = """Generate a daily (1D) structural context note to support intraday decisions.
This is NOT a trade call. It's context.

Language: {lang_name}

INPUT DATA:
{analysis_json}

OUTPUT FORMAT (strict, use {lang_name}):

## Big Picture
- Regime + confidence
- Nearest major zones and distance
- Where price sits in 1D structure (near support, mid-range, near resistance)
(3 bullets)

## Key Levels
| Level | Type | Why It Matters |
| --- | --- | --- |
(top 4 zones with tests/rejections/recency)

## What Would Change the View
- Condition 1 (e.g., "daily close above zone")
- Condition 2 (e.g., "breakdown below support band")

## Risk Notes
- Event risk, volatility regime, data notes
(1-2 bullets)

RULES:
- Use only provided zone/structure inputs.
- Do not over-emphasize short-term breakout on 1D unless confirmed in 1D rules.
"""

# ============ 聚合更新 Prompt ============

PROMPT_AGGREGATED = """Summarize the last N timeline events into one concise narrative update.

Language: {lang_name}

EVENTS TO SUMMARIZE:
{events_json}

CURRENT SNAPSHOT:
{analysis_json}

OUTPUT FORMAT (use {lang_name}):

## Summary
One paragraph covering: zone approached → tested → rejected/accepted → breakout attempt/confirm/fakeout.
Focus on evolution and whether situation is improving or weakening.

## Key Evidence
- Evidence bullet 1 with [#bar_index]
- Evidence bullet 2 with [#bar_index]
- Evidence bullet 3 with [#bar_index]

## Current Status
**Action**: WAIT / WATCH / TRIGGERED
**Next Watch**: specific condition

RULES: Must cite [#bar_index] for each evidence bullet.
"""

# ============ 短评 Prompt (Quick Update) ============

PROMPT_QUICK_UPDATE = """根据提供的市场数据，用一段话解读当前盘面结构。

语言：{lang_name}

数据：
{analysis_json}

要求：
- 一段连贯的分析文字，80-120字
- 解读数据含义，说明当前结构状态
- 如果行为与趋势冲突要解释原因
- 带具体数字（价位、RVOL等）
- 不要标题、bullet、分段，就一段话
- 不要写操作建议，只做数据解读

示例：
当前价格在620附近震荡，两次尝试突破621.5阻力均未成功，RVOL仅0.78低于确认阈值1.8，说明买盘动能不足。虽然行为模式显示有资金在吸筹，但整体趋势仍偏空，属于反弹结构而非趋势反转。下方618支撑已测试2次有承接，短期关注能否放量突破或支撑失守。
"""

# ============ Data Classes ============

@dataclass
class NarrativeResult:
    """叙事生成结果"""
    summary: str
    action: str  # WAIT / WATCH / TRIGGERED
    content: str  # Full formatted content
    why: List[str] = field(default_factory=list)
    scenarios: Optional[str] = None
    risks: Optional[List[str]] = None
    quality: str = "high"  # high / limited
    report_type: str = "full"  # full / quick / confirmation / context
    triggered_by: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TriggerEvent:
    """触发事件"""
    event_type: str  # breakout_state_change, regime_shift, behavior_change, zone_change
    severity: str  # hard / soft
    description: str
    timestamp: datetime
    bar_index: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


# ============ Event Trigger Detection ============

class EventTriggerDetector:
    """
    事件触发检测器

    检测 Hard triggers 和 Soft triggers。
    """

    def __init__(self):
        self.last_state: Dict[str, Any] = {}
        self.last_zones_hash: Optional[str] = None

    def detect_triggers(
        self,
        current_state: Dict[str, Any],
        previous_state: Optional[Dict[str, Any]] = None
    ) -> List[TriggerEvent]:
        """
        检测状态变化触发的事件

        Args:
            current_state: 当前分析状态
            previous_state: 之前的分析状态（可选）

        Returns:
            触发事件列表
        """
        prev = previous_state or self.last_state
        triggers = []
        now = datetime.now()

        # Hard Trigger 1: Breakout FSM 状态变化
        curr_breakout = current_state.get("breakout", {}).get("state", "idle")
        prev_breakout = prev.get("breakout", {}).get("state", "idle")

        if curr_breakout != prev_breakout:
            triggers.append(TriggerEvent(
                event_type="breakout_state_change",
                severity="hard",
                description=f"Breakout: {prev_breakout} → {curr_breakout}",
                timestamp=now,
                details={"from": prev_breakout, "to": curr_breakout}
            ))

        # Hard Trigger 2: Regime Shift
        curr_regime = current_state.get("regime", {}).get("name", "range")
        prev_regime = prev.get("regime", {}).get("name", "range")

        if curr_regime != prev_regime:
            triggers.append(TriggerEvent(
                event_type="regime_shift",
                severity="hard",
                description=f"Regime: {prev_regime} → {curr_regime}",
                timestamp=now,
                details={"from": prev_regime, "to": curr_regime}
            ))

        # Hard Trigger 3: Dominant Behavior 变化 + Δprob ≥ 0.12
        curr_behavior = current_state.get("behavior", {})
        prev_behavior = prev.get("behavior", {})

        curr_dominant = curr_behavior.get("dominant", "")
        prev_dominant = prev_behavior.get("dominant", "")

        if curr_dominant and prev_dominant:
            curr_probs = curr_behavior.get("probabilities", {})
            prev_probs = prev_behavior.get("probabilities", {})

            # 计算最大 delta
            max_delta = 0
            for key in set(curr_probs.keys()) | set(prev_probs.keys()):
                delta = abs(curr_probs.get(key, 0) - prev_probs.get(key, 0))
                max_delta = max(max_delta, delta)

            if curr_dominant != prev_dominant and max_delta >= 0.12:
                triggers.append(TriggerEvent(
                    event_type="behavior_change",
                    severity="hard",
                    description=f"Behavior: {prev_dominant} → {curr_dominant} (Δ={max_delta:.2f})",
                    timestamp=now,
                    details={
                        "from": prev_dominant,
                        "to": curr_dominant,
                        "delta": max_delta
                    }
                ))
            elif max_delta >= 0.18:
                # 同 dominant 但概率跳变大
                triggers.append(TriggerEvent(
                    event_type="behavior_probability_jump",
                    severity="hard",
                    description=f"Behavior prob jump: Δ={max_delta:.2f}",
                    timestamp=now,
                    details={"delta": max_delta}
                ))

        # Hard Trigger 4: Key Zone 变化
        curr_zones = current_state.get("zones", [])
        zones_hash = self._hash_zones(curr_zones[:4])  # Top 4 zones

        if self.last_zones_hash and zones_hash != self.last_zones_hash:
            triggers.append(TriggerEvent(
                event_type="zone_change",
                severity="hard",
                description="Key zones configuration changed",
                timestamp=now,
                details={"zones_count": len(curr_zones)}
            ))

        self.last_zones_hash = zones_hash

        # Soft Triggers (从 timeline 中检测)
        timeline = current_state.get("timeline_recent", [])
        for event in timeline[-3:]:  # 最近 3 个事件
            event_type = event.get("event", "")
            if event_type in ["zone_approached", "zone_tested", "zone_rejected",
                             "absorption_clue", "volume_spike", "volume_dryup"]:
                triggers.append(TriggerEvent(
                    event_type=event_type,
                    severity="soft",
                    description=event.get("reason", event_type),
                    timestamp=now,
                    bar_index=event.get("bar_index"),
                    details=event
                ))

        # 更新 last_state
        self.last_state = current_state

        return triggers

    def _hash_zones(self, zones: List[Dict]) -> str:
        """计算 zones 的 hash"""
        if not zones:
            return ""
        zone_str = json.dumps(sorted([
            (z.get("level", 0), z.get("type", ""))
            for z in zones
        ]))
        return hashlib.md5(zone_str.encode()).hexdigest()[:8]


# ============ Cooldown Manager ============

class CooldownManager:
    """
    冷却管理器

    防止 LLM 调用过于频繁。
    """

    def __init__(
        self,
        hard_cooldown_minutes: int = 15,
        soft_cooldown_minutes: int = 30,
        max_calls_per_day: int = 50
    ):
        self.hard_cooldown = timedelta(minutes=hard_cooldown_minutes)
        self.soft_cooldown = timedelta(minutes=soft_cooldown_minutes)
        self.max_calls_per_day = max_calls_per_day

        # {symbol: {event_type: last_trigger_time}}
        self.last_triggers: Dict[str, Dict[str, datetime]] = {}
        # {symbol: [call_times]}
        self.daily_calls: Dict[str, List[datetime]] = {}
        # {symbol: [pending_events]}
        self.pending_events: Dict[str, List[TriggerEvent]] = {}

    def can_trigger(
        self,
        symbol: str,
        event: TriggerEvent
    ) -> bool:
        """检查是否可以触发 LLM"""
        now = datetime.now()

        # 检查日调用限制
        self._cleanup_daily_calls(symbol, now)
        if len(self.daily_calls.get(symbol, [])) >= self.max_calls_per_day:
            logger.warning(f"Daily call limit reached for {symbol}")
            return False

        # 检查冷却时间
        cooldown = self.hard_cooldown if event.severity == "hard" else self.soft_cooldown
        last_time = self.last_triggers.get(symbol, {}).get(event.event_type)

        if last_time and (now - last_time) < cooldown:
            # 在冷却期内，加入 pending
            self._add_pending(symbol, event)
            return False

        return True

    def record_trigger(self, symbol: str, event: TriggerEvent):
        """记录触发"""
        now = datetime.now()

        if symbol not in self.last_triggers:
            self.last_triggers[symbol] = {}
        self.last_triggers[symbol][event.event_type] = now

        if symbol not in self.daily_calls:
            self.daily_calls[symbol] = []
        self.daily_calls[symbol].append(now)

    def get_pending_events(self, symbol: str) -> List[TriggerEvent]:
        """获取并清空 pending 事件"""
        events = self.pending_events.get(symbol, [])
        self.pending_events[symbol] = []
        return events

    def _add_pending(self, symbol: str, event: TriggerEvent):
        """添加到 pending 列表"""
        if symbol not in self.pending_events:
            self.pending_events[symbol] = []
        # 去重
        existing_types = {e.event_type for e in self.pending_events[symbol]}
        if event.event_type not in existing_types:
            self.pending_events[symbol].append(event)

    def _cleanup_daily_calls(self, symbol: str, now: datetime):
        """清理超过 24 小时的调用记录"""
        if symbol not in self.daily_calls:
            return
        cutoff = now - timedelta(hours=24)
        self.daily_calls[symbol] = [
            t for t in self.daily_calls[symbol] if t > cutoff
        ]


# ============ LLM Service ============

class LLMService:
    """
    LLM 服务类 v2

    支持事件驱动的多周期分析。
    """

    def __init__(
        self,
        provider: Literal["openai", "gemini"] = "openai",
        api_key: str = "",
        model: str = "",
        model_full: str = "",
        base_url: Optional[str] = None,
    ):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url

        # 模型配置
        if provider == "openai":
            self.model_quick = model or "gpt-4o-mini"  # 短评/确认
            self.model_full = model_full or "gpt-4o"   # 完整分析
        else:
            self.model_quick = model or "gemini-1.5-flash"
            self.model_full = model_full or "gemini-1.5-pro"

        # 事件检测器和冷却管理
        self.trigger_detector = EventTriggerDetector()
        self.cooldown_manager = CooldownManager()

    async def generate_analysis(
        self,
        analysis_json: Dict[str, Any],
        timeframe: str = "5m",
        report_type: Literal["full", "quick", "confirmation", "context", "aggregated"] = "full",
        lang: Literal["zh", "en"] = "zh",
        triggered_by: Optional[TriggerEvent] = None,
        pending_events: Optional[List[Dict]] = None,
    ) -> NarrativeResult:
        """
        生成市场分析叙事

        Args:
            analysis_json: 分析结果 JSON
            timeframe: 时间周期 (1m, 5m, 1d)
            report_type: 报告类型
            lang: 输出语言
            triggered_by: 触发事件
            pending_events: 待聚合的事件列表

        Returns:
            NarrativeResult 对象
        """
        if not self.api_key:
            return NarrativeResult(
                summary="LLM API key not configured",
                action="WAIT",
                content="",
                error="NO_API_KEY",
                quality="limited",
                report_type=report_type
            )

        # 选择 prompt 和模型
        lang_name = "Chinese" if lang == "zh" else "English"

        if report_type == "quick":
            prompt_template = PROMPT_QUICK_UPDATE
            model = self.model_quick
        elif report_type == "confirmation" or timeframe == "1m":
            prompt_template = PROMPT_1M_CONFIRMATION
            model = self.model_quick
        elif report_type == "context" or timeframe == "1d":
            prompt_template = PROMPT_1D_CONTEXT
            model = self.model_full
        elif report_type == "aggregated":
            prompt_template = PROMPT_AGGREGATED
            model = self.model_quick
        else:  # full / 5m
            prompt_template = PROMPT_5M_ANALYSIS
            model = self.model_full

        # 构建 prompt
        if report_type == "aggregated" and pending_events:
            user_prompt = prompt_template.format(
                lang_name=lang_name,
                events_json=json.dumps(pending_events, indent=2, ensure_ascii=False),
                analysis_json=json.dumps(analysis_json, indent=2, ensure_ascii=False)
            )
        else:
            user_prompt = prompt_template.format(
                lang_name=lang_name,
                analysis_json=json.dumps(analysis_json, indent=2, ensure_ascii=False)
            )

        try:
            logger.info(f"LLM: Using {model} for {report_type} ({timeframe})")

            if self.provider == "openai":
                response = await self._call_openai(user_prompt, model)
            else:
                response = await self._call_gemini(user_prompt, model)

            # 解析响应
            result = self._parse_response(response, analysis_json, report_type)
            result.triggered_by = triggered_by.event_type if triggered_by else None
            return result

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return NarrativeResult(
                summary=f"Generation failed: {str(e)}",
                action="WAIT",
                content="",
                error=str(e),
                quality="limited",
                report_type=report_type
            )

    async def _call_openai(self, user_prompt: str, model: str) -> str:
        """调用 OpenAI API"""
        url = self.base_url or "https://api.openai.com/v1/chat/completions"

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, user_prompt: str, model: str) -> str:
        """调用 Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                params={"key": self.api_key},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": SYSTEM_PROMPT + "\n\n" + user_prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 2000
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _parse_response(
        self,
        response: str,
        analysis_json: Dict,
        report_type: str
    ) -> NarrativeResult:
        """解析 LLM 响应"""

        # 提取 Action
        action = "WAIT"
        for keyword in ["TRIGGERED", "WATCH", "WAIT"]:
            if keyword in response.upper():
                action = keyword
                break

        # 提取 Summary（TL;DR 或 Summary 部分）
        summary = ""
        if "## TL;DR" in response:
            start = response.find("## TL;DR") + len("## TL;DR")
            end = response.find("##", start)
            summary = response[start:end].strip() if end > start else response[start:start+500].strip()
        elif "[SUMMARY]" in response:
            start = response.find("[SUMMARY]") + len("[SUMMARY]")
            end = response.find("[", start)
            summary = response[start:end].strip() if end > start else response[start:start+200].strip()
        elif "## Summary" in response:
            start = response.find("## Summary") + len("## Summary")
            end = response.find("##", start)
            summary = response[start:end].strip() if end > start else response[start:start+500].strip()
        else:
            # 取前 200 字符作为 summary
            summary = response[:200].strip()

        # 提取 Why/Evidence
        why = []
        if "## Evidence Chain" in response:
            start = response.find("## Evidence Chain") + len("## Evidence Chain")
            end = response.find("##", start)
            evidence_section = response[start:end] if end > start else response[start:start+800]
            for line in evidence_section.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    why.append(line[1:].strip())
        elif "[KEY POINT]" in response:
            start = response.find("[KEY POINT]") + len("[KEY POINT]")
            end = response.find("[", start) if "[" in response[start:] else len(response)
            key_point = response[start:end].strip()
            if key_point:
                why.append(key_point)

        # 提取 Risks
        risks = []
        if "## Risk" in response:
            start = response.find("## Risk")
            end = response.find("##", start + 10)
            risk_section = response[start:end] if end > start else response[start:]
            for line in risk_section.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    risks.append(line[1:].strip())

        # 确定质量
        volume_quality = analysis_json.get("volume_quality", "")
        confidence = analysis_json.get("regime", {}).get("confidence", 1.0)
        quality = "high" if volume_quality == "reliable" and confidence >= 0.6 else "limited"

        return NarrativeResult(
            summary=summary[:500] if summary else "No summary generated",
            action=action,
            content=response,
            why=why[:6] if why else [],
            risks=risks[:3] if risks else None,
            quality=quality,
            report_type=report_type
        )


# ============ Helper Functions ============

def prepare_analysis_for_llm(
    report: Dict[str, Any],
    ticker: str,
    timeframe: str,
    price: float,
    include_evidence: bool = True
) -> Dict[str, Any]:
    """
    准备发送给 LLM 的结构化 JSON

    只包含必要的分析结果，不发送原始 OHLCV 数据。
    """
    # 提取 regime
    regime = report.get("market_state", {})

    # 提取 breakout 状态
    signals = report.get("signals", [])
    breakout_signal = next((s for s in signals if "breakout" in s.get("type", "").lower()), None)

    # 计算 confirm_closes
    confirm_closes = 0
    for s in signals:
        if s.get("type") == "breakout_confirmed":
            confirm_closes = 2
            break
        elif s.get("type") == "breakout_attempt":
            confirm_closes = 1
            break

    breakout = {
        "state": "confirmed" if confirm_closes == 2 else "attempt" if confirm_closes == 1 else "idle",
        "direction": breakout_signal.get("direction", "unknown") if breakout_signal else "none",
        "confirm_closes": f"{confirm_closes}/2",
        "rvol": report.get("volume_ratio", 0),
        "rvol_threshold": 1.8,
        "result_atr": report.get("result_atr", 0),
        "result_threshold": 0.6,
        "volume_quality": report.get("volume_quality", "unavailable")
    }

    # 提取 behavior
    behavior_data = report.get("behavior", {})
    behavior = {
        "dominant": behavior_data.get("dominant", "unknown"),
        "confidence": behavior_data.get("probabilities", {}).get(behavior_data.get("dominant", ""), 0),
        "probabilities": behavior_data.get("probabilities", {})
    }

    # 提取 zones (top 4)
    zones = []
    for zone_type in ["resistance", "support"]:
        for z in report.get("zones", {}).get(zone_type, [])[:2]:
            mid = (z.get("upper", z.get("high", 0)) + z.get("lower", z.get("low", 0))) / 2
            dist_pct = ((mid - price) / price * 100) if price else 0
            zones.append({
                "level": round(mid, 2),
                "type": "R" if zone_type == "resistance" else "S",
                "tests": z.get("touches", z.get("tests", 0)),
                "score": z.get("score", z.get("strength", 0)),
                "dist_pct": round(dist_pct, 2)
            })

    # 提取 evidence (top 5-10)
    evidence = []
    if include_evidence:
        for ev in (behavior_data.get("evidence", []))[:10]:
            evidence.append({
                "type": ev.get("type", "unknown"),
                "behavior": ev.get("behavior", ""),
                "severity": ev.get("severity", "med"),
                "bar_index": ev.get("bar_index"),
                "bar_time": ev.get("bar_time", ""),
                "metrics": ev.get("metrics", {}),
                "note": ev.get("note", "")
            })

    # 提取 timeline (最近 6 个事件)
    timeline_recent = []
    for event in report.get("timeline", [])[-6:]:
        timeline_recent.append({
            "event": event.get("event_type", "unknown"),
            "ts": event.get("ts", ""),
            "reason": event.get("reason", ""),
            "bar_index": event.get("bar_index"),
            "severity": event.get("severity", "info")
        })

    # 提取 playbook
    playbook = {}
    plans = report.get("playbook", [])
    if len(plans) >= 1:
        p = plans[0]
        playbook["planA"] = {
            "condition": p.get("condition", ""),
            "entry": p.get("level", p.get("entry", 0)),
            "target": p.get("target", 0),
            "invalidation": p.get("invalidation", 0)
        }
    if len(plans) >= 2:
        p = plans[1]
        playbook["planB"] = {
            "condition": p.get("condition", ""),
            "entry": p.get("level", p.get("entry", 0)),
            "target": p.get("target", 0),
            "invalidation": p.get("invalidation", 0)
        }

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "price": price,
        "regime": {
            "name": regime.get("regime", "unknown"),
            "confidence": regime.get("confidence", 0)
        },
        "breakout": breakout,
        "behavior": behavior,
        "zones": zones,
        "evidence": evidence,
        "timeline_recent": timeline_recent,
        "playbook": playbook,
        "volume_quality": report.get("volume_quality", "unavailable"),
        "data_quality": {
            "volume_ok": report.get("volume_quality") == "reliable",
            "gaps_flag": report.get("data_gaps", False)
        }
    }


# ============ Convenience Function ============

async def generate_narrative(
    llm_service: LLMService,
    report: Dict[str, Any],
    ticker: str,
    timeframe: str,
    price: float,
    report_type: Literal["full", "quick", "confirmation", "context"] = "full",
    lang: Literal["zh", "en"] = "zh",
) -> NarrativeResult:
    """
    便捷函数：从分析报告生成叙事

    Args:
        llm_service: LLM 服务实例
        report: analyze_market() 的原始返回
        ticker: 股票代码
        timeframe: 时间周期
        price: 当前价格
        report_type: 报告类型
        lang: 输出语言

    Returns:
        NarrativeResult 对象
    """
    analysis_json = prepare_analysis_for_llm(report, ticker, timeframe, price)
    return await llm_service.generate_analysis(
        analysis_json,
        timeframe=timeframe,
        report_type=report_type,
        lang=lang
    )
