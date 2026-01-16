"""
KLineLens API 服务器主模块

FastAPI 应用程序入口，提供市场数据和分析接口。

接口列表:
- GET /: 健康检查
- GET /v1/bars: 获取 K 线数据
- POST /v1/analyze: 运行市场分析

启动方式:
    uvicorn src.main:app --reload --port 8000

访问文档:
    http://localhost:8000/docs
"""

import asyncio
import json
import logging
import sys
import os
from typing import Optional, Any
from dataclasses import asdict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .config import settings
from .cache import get_cache, cache_key
from .providers import get_provider, TickerNotFoundError, RateLimitError, ProviderError
from .services.llm_service import LLMService, generate_narrative, prepare_analysis_for_llm
from .database import SignalEvaluationDB, SignalEvaluation, generate_eval_id, WatchlistDB, WatchlistItem
from .websocket_manager import init_websocket, get_websocket_manager, RealtimePrice

# 导入 core 模块
# 支持两种环境：
# 1. Docker: core 挂载在 /app/core (作为 src 包)
# 2. 本地开发: core 在 ../../../packages/core

def _import_core_package():
    """导入 core 分析模块"""
    # Docker 环境: /app/packages/core
    docker_core_path = '/app/packages/core'
    # 本地环境: packages/core
    local_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'packages', 'core'))

    # 检测运行环境
    if os.path.exists(docker_core_path):
        core_path = docker_core_path
    else:
        core_path = local_core_path

    # 将 core 路径添加到 sys.path
    if core_path not in sys.path:
        sys.path.insert(0, core_path)

    # 保存并临时移除 API 的 src 模块
    api_src = sys.modules.get('src')
    api_src_submodules = {k: v for k, v in sys.modules.items() if k.startswith('src.')}

    for k in api_src_submodules:
        del sys.modules[k]
    if api_src:
        del sys.modules['src']

    try:
        # 导入 core 的 src 包
        from src import analyze as core_analyze
        from src import models as core_models
        from src import extended_hours as core_eh
    finally:
        # 恢复 API 的 src 模块
        if api_src:
            sys.modules['src'] = api_src
        sys.modules.update(api_src_submodules)

    return (
        core_analyze.analyze_market,
        core_analyze.AnalysisParams,
        core_models.Bar,
        core_models.AnalysisReport,
        # Extended Hours
        core_eh.build_eh_context,
        core_eh.get_yesterday_bars,
        core_eh.EHContext,
        core_eh.EHLevels,
        # New EH functions
        core_eh.split_bars_by_session,
        core_eh.build_eh_context_from_bars,
        core_eh.SessionBars,
    )

# 导入 core 模块
(
    analyze_market,
    AnalysisParams,
    CoreBar,
    AnalysisReport,
    # Extended Hours
    build_eh_context,
    get_yesterday_bars,
    EHContext,
    EHLevels,
    # New EH functions
    split_bars_by_session,
    build_eh_context_from_bars,
    SessionBars,
) = _import_core_package()

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 应用
app = FastAPI(
    title="KLineLens API",
    description="市场结构分析 API - 提供 K 线数据和行为分析",
    version="0.1.0",
)

# 配置 CORS 中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据提供者和缓存
# 根据配置选择数据提供者
# - yfinance: 免费，无需 Key（默认）
# - alpaca: 免费，需要 Key，有分钟成交量（推荐）
# - alphavantage: 25次/天限制
def _get_provider_api_key():
    """根据 provider 类型获取对应的 API 凭证"""
    if settings.provider == "twelvedata":
        return settings.twelvedata_api_key, None
    elif settings.provider == "alpaca":
        return settings.alpaca_api_key, settings.alpaca_api_secret
    elif settings.provider == "alphavantage":
        return settings.alphavantage_api_key, None
    return None, None

api_key, api_secret = _get_provider_api_key()
provider = get_provider(
    name=settings.provider,
    api_key=api_key,
    api_secret=api_secret,
)
logger.info(f"使用数据提供者: {provider.name}")
cache = get_cache(default_ttl=settings.cache_ttl)

# 初始化 Signal Evaluation 数据库
eval_db = SignalEvaluationDB()
logger.info(f"Signal Evaluation DB 初始化完成: {eval_db.db_path}")

# 初始化 Watchlist 数据库
watchlist_db = WatchlistDB()
logger.info(f"Watchlist DB 初始化完成 (最大 {watchlist_db.MAX_ITEMS} 个)")

# 初始化 LLM 服务（用于生成叙事报告）
llm_service = LLMService(
    provider=settings.llm_provider,
    api_key=settings.llm_api_key,
    model=settings.llm_model or "",
    model_full=settings.llm_model_full or "",
    base_url=settings.llm_base_url or None,
)
if settings.llm_api_key:
    logger.info(f"LLM 服务已配置: {settings.llm_provider}")
else:
    logger.warning("LLM API Key 未配置，叙事生成功能不可用")


# ============ WebSocket 实时数据 ============

@app.on_event("startup")
async def startup_event():
    """
    应用启动事件

    初始化 WebSocket 连接到 TwelveData，并订阅所有自选股。
    """
    if settings.provider == "twelvedata" and settings.twelvedata_api_key:
        try:
            ws_manager = await init_websocket(settings.twelvedata_api_key)
            logger.info("TwelveData WebSocket 已初始化")

            # 订阅所有自选股
            watchlist = watchlist_db.list()
            if watchlist:
                for item in watchlist:
                    await ws_manager.subscribe(item.ticker)
                logger.info(f"已订阅 {len(watchlist)} 个自选股: {[w.ticker for w in watchlist]}")
            else:
                logger.info("自选股列表为空，无需订阅")
        except Exception as e:
            logger.warning(f"WebSocket 初始化失败（将使用轮询模式）: {e}")
    else:
        logger.info("WebSocket 未启用（非 TwelveData 提供者或未配置 API Key）")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    ws_manager = get_websocket_manager()
    if ws_manager:
        await ws_manager.disconnect()
        logger.info("WebSocket 已关闭")


# ============ 辅助函数 ============

def report_to_dict(report: AnalysisReport) -> dict:
    """
    将 AnalysisReport 转换为 JSON 可序列化的字典

    处理 datetime 和嵌套 dataclass 的序列化。
    """
    def serialize(obj):
        """递归序列化对象"""
        if isinstance(obj, datetime):
            # 处理时区信息：如果是 timezone-aware，转换为 UTC 并使用 Z 后缀
            if obj.tzinfo is not None:
                # 转换为 UTC 字符串，去掉 +00:00，用 Z 代替
                utc_str = obj.strftime('%Y-%m-%dT%H:%M:%S')
                return utc_str + "Z"
            else:
                # naive datetime，直接添加 Z
                return obj.isoformat() + "Z"
        elif hasattr(obj, '__dataclass_fields__'):
            return {k: serialize(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize(item) for item in obj]
        else:
            return obj

    return serialize(report)


# ============ 数据模型 ============

class ErrorResponse(BaseModel):
    """
    错误响应模型

    用于返回标准化的错误信息。
    """
    code: str  # 错误代码
    message: str  # 错误消息
    details: Optional[dict] = None  # 详细信息（可选）


class BarsResponse(BaseModel):
    """
    K 线数据响应模型

    返回指定股票的 K 线数据列表。
    """
    ticker: str  # 股票代码
    tf: str  # 时间周期
    bar_count: int  # K 线数量
    bars: list  # K 线数据列表


class AnalyzeRequest(BaseModel):
    """
    分析请求模型

    用于 POST /v1/analyze 接口的请求体。
    """
    ticker: str  # 股票代码
    tf: str = "1m"  # 时间周期，默认 1 分钟
    window: Optional[str] = None  # 回溯时间范围


class NarrativeRequest(BaseModel):
    """
    叙事生成请求模型 v2

    用于 POST /v1/narrative 接口的请求体。

    report_type 选项:
    - full: 完整 5m 结构分析报告（使用 gpt-4o）
    - quick: 简短更新（2-4 句，使用 gpt-4o-mini）
    - confirmation: 1m 执行确认（确认/否定高级别论点）
    - context: 1D 背景框架（大结构上下文）
    """
    ticker: str  # 股票代码
    tf: str = "5m"  # 时间周期（默认 5m）
    window: Optional[str] = None  # 回溯时间范围
    report_type: str = "full"  # full / quick / confirmation / context
    lang: str = "zh"  # 输出语言 (zh / en)


class SignalEvaluationRequest(BaseModel):
    """
    信号评估创建请求模型

    用于 POST /v1/signal-evaluation 接口的请求体。
    """
    ticker: str  # 股票代码
    tf: str  # 时间周期: 1m, 5m, 1d
    signal_type: str  # 信号类型
    direction: str  # up / down
    predicted_behavior: str  # 预测行为
    entry_price: float  # 入场价
    target_price: float  # 目标价
    invalidation_price: float  # 止损价
    confidence: float  # 置信度 0-1
    notes: Optional[str] = None  # 备注


class SignalEvaluationUpdateRequest(BaseModel):
    """
    信号评估更新请求模型

    用于 PUT /v1/signal-evaluation/{id} 接口的请求体。
    """
    status: str  # correct / incorrect
    result: str  # target_hit / invalidation_hit / partial_correct / direction_wrong / timeout
    actual_outcome: str  # 实际结果描述
    evaluation_notes: Optional[str] = None  # 评估备注


# ============ API 接口 ============

@app.get("/")
async def root():
    """
    健康检查接口

    返回服务状态和当前使用的数据提供者。
    """
    return {
        "status": "ok",
        "service": "klinelens-api",
        "provider": provider.name
    }


@app.get("/v1/bars", response_model=BarsResponse)
async def get_bars(
    ticker: str = Query(..., description="股票代码（如 TSLA, AAPL）"),
    tf: str = Query("1m", description="时间周期: 1m, 5m, 1d"),
    window: Optional[str] = Query(None, description="回溯时间（如 1d, 5d, 1mo）"),
):
    """
    获取 K 线数据接口

    从数据提供者获取指定股票的 OHLCV K 线数据。
    支持缓存，相同请求在 TTL 内会返回缓存数据。

    参数:
        ticker: 股票代码（如 TSLA, AAPL, BTC-USD）
        tf: 时间周期（1m=1分钟, 5m=5分钟, 1d=日线）
        window: 回溯时间（默认: 1m->1d, 5m->5d, 1d->6mo）

    返回:
        包含 K 线数据的响应对象

    错误:
        400: 时间周期无效
        404: 股票代码不存在或无数据
        429: 请求频率超限
        502: 数据提供者错误
    """
    # 验证时间周期
    if tf not in ("1m", "5m", "1d"):
        raise HTTPException(
            status_code=400,
            detail={"code": "TIMEFRAME_INVALID", "message": f"无效的时间周期: {tf}"}
        )

    # 获取默认回溯时间
    actual_window = window or provider.get_default_window(tf)

    # 先检查缓存
    key = cache_key(ticker, tf, actual_window)
    cached_bars = cache.get(key)
    if cached_bars is not None:
        logger.info(f"缓存命中: {ticker}")
        return BarsResponse(
            ticker=ticker.upper(),
            tf=tf,
            bar_count=len(cached_bars),
            bars=cached_bars,
        )

    # 缓存未命中，从提供者获取数据
    try:
        bars = provider.get_bars(ticker, tf, actual_window)

        # 转换为字典格式用于 JSON 响应
        bars_data = [bar.to_dict() for bar in bars]

        # 存入缓存
        cache.set(key, bars_data)

        return BarsResponse(
            ticker=ticker.upper(),
            tf=tf,
            bar_count=len(bars_data),
            bars=bars_data,
        )

    except TickerNotFoundError as e:
        # 股票代码不存在
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_DATA", "message": str(e)}
        )
    except RateLimitError as e:
        # 请求频率超限
        raise HTTPException(
            status_code=429,
            detail={"code": "PROVIDER_RATE_LIMITED", "message": str(e)}
        )
    except ProviderError as e:
        # 其他提供者错误
        raise HTTPException(
            status_code=502,
            detail={"code": "PROVIDER_ERROR", "message": str(e)}
        )


@app.post("/v1/analyze")
async def analyze(request: AnalyzeRequest):
    """
    市场分析接口

    运行完整的市场结构分析，返回:
    - 市场状态（趋势/震荡）
    - 支撑阻力区域
    - 突破/假突破信号
    - 行为概率推断
    - 时间线事件
    - 条件交易剧本

    参数:
        ticker: 股票代码（如 TSLA, AAPL）
        tf: 时间周期（1m, 5m, 1d）
        window: 回溯时间（可选）

    返回:
        完整的 AnalysisReport JSON

    错误:
        400: 时间周期无效或数据不足
        404: 股票代码不存在
        429: 请求频率超限
        502: 数据提供者错误
    """
    # 验证时间周期
    if request.tf not in ("1m", "5m", "1d"):
        raise HTTPException(
            status_code=400,
            detail={"code": "TIMEFRAME_INVALID", "message": f"无效的时间周期: {request.tf}"}
        )

    # 获取默认回溯时间
    actual_window = request.window or provider.get_default_window(request.tf)

    # 获取 K 线数据（复用 /v1/bars 的逻辑）
    key = cache_key(request.ticker, request.tf, actual_window)
    cached_bars = cache.get(key)

    try:
        if cached_bars is not None:
            logger.info(f"分析: 缓存命中 {request.ticker}")
            # 从缓存的字典格式转换为 CoreBar
            from dateutil.parser import isoparse
            core_bars = [
                CoreBar(
                    t=isoparse(bar["t"].replace("Z", "+00:00")),
                    o=bar["o"],
                    h=bar["h"],
                    l=bar["l"],
                    c=bar["c"],
                    v=bar["v"]
                )
                for bar in cached_bars
            ]
        else:
            logger.info(f"分析: 获取数据 {request.ticker}")
            # 从提供者获取数据
            api_bars = provider.get_bars(request.ticker, request.tf, actual_window)

            # 存入缓存
            bars_data = [bar.to_dict() for bar in api_bars]
            cache.set(key, bars_data)

            # 转换为 CoreBar（API Bar 和 Core Bar 结构相同）
            core_bars = [
                CoreBar(t=bar.t, o=bar.o, h=bar.h, l=bar.l, c=bar.c, v=bar.v)
                for bar in api_bars
            ]

        # 运行市场分析
        report = analyze_market(
            bars=core_bars,
            ticker=request.ticker,
            timeframe=request.tf
        )

        # 转换为 JSON 并返回
        return report_to_dict(report)

    except TickerNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_DATA", "message": str(e)}
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail={"code": "PROVIDER_RATE_LIMITED", "message": str(e)}
        )
    except ValueError as e:
        # 数据不足等分析错误
        raise HTTPException(
            status_code=400,
            detail={"code": "ANALYSIS_ERROR", "message": str(e)}
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "PROVIDER_ERROR", "message": str(e)}
        )


async def get_eh_context_internal(ticker: str, tf: str = "1m") -> Optional[Any]:
    """
    内部函数：获取 EH 上下文

    Args:
        ticker: 股票代码
        tf: 时间周期

    Returns:
        EHContext 对象，或 None
    """
    ticker = ticker.upper()
    key = cache_key(ticker, tf, "eh-context-internal")

    # 检查缓存（使用不同 key 避免冲突）
    cached = cache.get(key)
    if cached:
        # 返回缓存的字典
        return type('EHContext', (), cached)()  # 简单对象模拟

    try:
        from .providers.yfinance_provider import YFinanceProvider
        yf_provider = YFinanceProvider()
        eh_bars = yf_provider.get_bars_extended(ticker, tf, "2d")

        if eh_bars and len(eh_bars) >= 100:
            core_bars = [
                CoreBar(t=bar.t, o=bar.o, h=bar.h, l=bar.l, c=bar.c, v=bar.v)
                for bar in eh_bars
            ]
            eh_context = build_eh_context_from_bars(core_bars)

            # 缓存
            ctx_dict = eh_context_to_dict(eh_context)
            cache.set(key, ctx_dict, ttl=60)

            return eh_context
    except Exception as e:
        logger.warning(f"内部 EH 上下文获取失败: {e}")

    return None


@app.get("/v1/eh-context")
async def get_eh_context(
    ticker: str = Query(..., description="股票代码（如 TSLA, AAPL）"),
    tf: str = Query("1m", description="时间周期: 1m, 5m"),
    use_eh: bool = Query(True, description="是否尝试获取 Extended Hours 数据"),
):
    """
    获取 Extended Hours 上下文

    提供盘前/盘后的关键位和市场先验信息。

    数据质量级别:
    - complete: 所有 EH 数据可用（今日盘前 + 昨日盘后）
    - partial: 仅历史 EH 数据（昨日盘后）
    - minimal: 仅 YC/YH/YL

    数据源策略 (MVP):
    - 优先使用 YFinance 的 prepost=True 获取免费 EH 数据
    - 回退到普通数据（minimal 模式）

    参数:
        ticker: 股票代码
        tf: 时间周期（默认 1m，仅支持 1m/5m）
        use_eh: 是否尝试获取 EH 数据（默认 True）

    返回:
        EHContext 对象，包含:
        - levels: 关键价位 (YC, YH, YL, 可能有 PMH, PML, AHH, AHL)
        - premarket_regime: 盘前形态（complete 模式）
        - key_zones: 带角色的关键区域列表
        - ah_risk: 盘后风险评估
        - data_quality: 数据质量级别
    """
    ticker = ticker.upper()
    key = cache_key(ticker, tf, f"eh-context-{use_eh}")

    # 检查缓存
    cached = cache.get(key)
    if cached:
        return cached

    try:
        # 尝试获取 Extended Hours 数据
        eh_bars = None
        if use_eh and tf in ("1m", "5m"):
            # 尝试使用 YFinance 获取 EH 数据（免费）
            try:
                from .providers.yfinance_provider import YFinanceProvider
                yf_provider = YFinanceProvider()
                eh_bars = yf_provider.get_bars_extended(ticker, tf, "2d")
                logger.info(f"YFinance EH 数据获取成功: {ticker}, {len(eh_bars)} bars")
            except Exception as e:
                logger.warning(f"YFinance EH 数据获取失败，回退到普通模式: {e}")
                eh_bars = None

        if eh_bars and len(eh_bars) >= 100:
            # 使用 EH 数据构建上下文
            core_bars = [
                CoreBar(t=bar.t, o=bar.o, h=bar.h, l=bar.l, c=bar.c, v=bar.v)
                for bar in eh_bars
            ]

            # 使用新的 session 分割和构建函数
            eh_context = build_eh_context_from_bars(core_bars)

            # 添加数据来源信息
            result = eh_context_to_dict(eh_context)
            result["data_source"] = "yfinance_prepost"

        else:
            # 回退到普通数据（minimal 模式）
            window = "3d" if tf == "1m" else "5d"
            bars = provider.get_bars(ticker, tf, window)

            if len(bars) < 100:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INSUFFICIENT_DATA",
                        "message": f"数据不足: 需要至少 100 根 K 线，实际 {len(bars)}"
                    }
                )

            # 转换为 core Bar 类型
            core_bars = [
                CoreBar(t=bar.t, o=bar.o, h=bar.h, l=bar.l, c=bar.c, v=bar.v)
                for bar in bars
            ]

            # 分离昨日和今日数据
            yesterday_bars, today_bars = get_yesterday_bars(core_bars)

            if not yesterday_bars:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "NO_YESTERDAY_DATA",
                        "message": "无法获取昨日数据，请确保有足够的历史 K 线"
                    }
                )

            # 构建 EH 上下文（minimal 模式）
            eh_context = build_eh_context(
                yesterday_bars=yesterday_bars,
                today_bars=today_bars,
                yesterday_afterhours=None,
                today_premarket=None,
                current_price=today_bars[-1].c if today_bars else None,
            )

            result = eh_context_to_dict(eh_context)
            result["data_source"] = "regular_only"

        # 缓存（较短 TTL，因为 EH 数据敏感）
        cache.set(key, result, ttl=30)

        return result

    except TickerNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_DATA", "message": str(e)}
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail={"code": "PROVIDER_RATE_LIMITED", "message": str(e)}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "EH_ERROR", "message": str(e)}
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "PROVIDER_ERROR", "message": str(e)}
        )


def eh_context_to_dict(ctx: EHContext) -> dict:
    """将 EHContext 转换为 JSON 可序列化字典"""
    return {
        "levels": {
            "yc": ctx.levels.yc,
            "yh": ctx.levels.yh,
            "yl": ctx.levels.yl,
            "pmh": ctx.levels.pmh,
            "pml": ctx.levels.pml,
            "ahh": ctx.levels.ahh,
            "ahl": ctx.levels.ahl,
            "gap": ctx.levels.gap,
        },
        "premarket_regime": ctx.premarket_regime,
        "premarket_bias": ctx.premarket_bias,
        "regime_confidence": ctx.regime_confidence,
        "eh_range_score": ctx.eh_range_score,
        "eh_rvol": ctx.eh_rvol,
        "key_zones": [
            {"zone": z.zone, "price": z.price, "role": z.role}
            for z in ctx.key_zones
        ],
        "pm_absorption": ctx.pm_absorption,
        "ah_risk": {
            "risk": ctx.ah_risk.risk,
            "likely_behavior": ctx.ah_risk.likely_behavior,
            "close_position": ctx.ah_risk.close_position,
            "late_rvol": ctx.ah_risk.late_rvol,
            "is_trend_day": ctx.ah_risk.is_trend_day,
        } if ctx.ah_risk else None,
        "expected_behaviors": ctx.expected_behaviors,
        "generated_at": ctx.generated_at.isoformat() + "Z",
        "data_quality": ctx.data_quality,
        "data_quality_note": ctx.data_quality_note,
    }


@app.post("/v1/narrative")
async def narrative(request: NarrativeRequest):
    """
    生成市场叙事报告 v2

    使用 LLM 基于分析结果生成人类可读的市场解读。
    基于事件驱动架构，支持多周期分析策略。

    report_type 模式:
    - full: 完整 5m 结构分析（用于手动刷新，gpt-4o）
    - quick: 简短更新（2-4 句，事件触发，gpt-4o-mini）
    - confirmation: 1m 执行确认（确认/否定 5m 论点）
    - context: 1D 背景框架（大结构上下文）

    参数:
        ticker: 股票代码
        tf: 时间周期 (1m, 5m, 1d)
        window: 回溯时间（可选）
        report_type: full / quick / confirmation / context
        lang: 输出语言 (zh / en)

    返回:
        包含 summary, action, content, why, risks, quality, report_type 的叙事报告

    错误:
        400: 参数无效或分析错误
        404: 股票代码不存在
        429: 请求频率超限
        502: 提供者或 LLM 错误
        503: LLM 服务不可用
    """
    # 验证参数
    if request.tf not in ("1m", "5m", "1d"):
        raise HTTPException(
            status_code=400,
            detail={"code": "TIMEFRAME_INVALID", "message": f"无效的时间周期: {request.tf}"}
        )

    valid_report_types = ("full", "quick", "confirmation", "context")
    if request.report_type not in valid_report_types:
        raise HTTPException(
            status_code=400,
            detail={"code": "REPORT_TYPE_INVALID", "message": f"无效的报告类型: {request.report_type}"}
        )

    if request.lang not in ("zh", "en"):
        raise HTTPException(
            status_code=400,
            detail={"code": "LANG_INVALID", "message": f"无效的语言: {request.lang}"}
        )

    # 检查 LLM 服务是否可用
    if not settings.llm_api_key:
        raise HTTPException(
            status_code=503,
            detail={"code": "LLM_NOT_CONFIGURED", "message": "LLM API Key 未配置"}
        )

    # 获取默认回溯时间
    actual_window = request.window or provider.get_default_window(request.tf)

    # 复用分析逻辑获取数据和报告
    key = cache_key(request.ticker, request.tf, actual_window)
    cached_bars = cache.get(key)

    try:
        if cached_bars is not None:
            logger.info(f"叙事: 缓存命中 {request.ticker}")
            from dateutil.parser import isoparse
            core_bars = [
                CoreBar(
                    t=isoparse(bar["t"].replace("Z", "+00:00")),
                    o=bar["o"],
                    h=bar["h"],
                    l=bar["l"],
                    c=bar["c"],
                    v=bar["v"]
                )
                for bar in cached_bars
            ]
        else:
            logger.info(f"叙事: 获取数据 {request.ticker}")
            api_bars = provider.get_bars(request.ticker, request.tf, actual_window)
            bars_data = [bar.to_dict() for bar in api_bars]
            cache.set(key, bars_data)
            core_bars = [
                CoreBar(t=bar.t, o=bar.o, h=bar.h, l=bar.l, c=bar.c, v=bar.v)
                for bar in api_bars
            ]

        # 运行市场分析
        report = analyze_market(
            bars=core_bars,
            ticker=request.ticker,
            timeframe=request.tf
        )

        # 获取当前价格（最后一根 K 线的收盘价）
        current_price = core_bars[-1].c if core_bars else 0

        # 转换报告为字典
        report_dict = report_to_dict(report)

        # 获取 EH 上下文（仅 1m/5m 周期）
        eh_context_data = None
        if request.tf in ("1m", "5m"):
            try:
                eh_ctx = await get_eh_context_internal(request.ticker, request.tf)
                if eh_ctx:
                    eh_context_data = {
                        "premarket_regime": eh_ctx.premarket_regime,
                        "bias": eh_ctx.bias,
                        "bias_confidence": eh_ctx.bias_confidence,
                        "levels": {
                            "yc": eh_ctx.levels.yc,
                            "yh": eh_ctx.levels.yh,
                            "yl": eh_ctx.levels.yl,
                            "pmh": eh_ctx.levels.pmh,
                            "pml": eh_ctx.levels.pml,
                            "ahh": eh_ctx.levels.ahh,
                            "ahl": eh_ctx.levels.ahl,
                            "gap": eh_ctx.levels.gap,
                            "gap_pct": eh_ctx.levels.gap_pct,
                        }
                    }
            except Exception as e:
                logger.warning(f"获取 EH 上下文失败: {e}")

        # 准备 LLM 输入数据（结构化 JSON，不发送原始 OHLCV）
        analysis_json = prepare_analysis_for_llm(
            report=report_dict,
            ticker=request.ticker,
            timeframe=request.tf,
            price=current_price,
            include_evidence=True,
            eh_context=eh_context_data
        )

        # 生成叙事
        result = await llm_service.generate_analysis(
            analysis_json=analysis_json,
            timeframe=request.tf,
            report_type=request.report_type,
            lang=request.lang,
        )

        # 返回结果
        return {
            "ticker": request.ticker,
            "timeframe": request.tf,
            "report_type": result.report_type,
            "lang": request.lang,
            "narrative": {
                "summary": result.summary,
                "action": result.action,
                "content": result.content,  # 完整格式化内容
                "why": result.why,
                "risks": result.risks,
                "quality": result.quality,
                "triggered_by": result.triggered_by,
            },
            "error": result.error,
        }

    except TickerNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_DATA", "message": str(e)}
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail={"code": "PROVIDER_RATE_LIMITED", "message": str(e)}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "ANALYSIS_ERROR", "message": str(e)}
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "PROVIDER_ERROR", "message": str(e)}
        )


# ============ Signal Evaluation API ============

@app.post("/v1/signal-evaluation", status_code=201)
async def create_signal_evaluation(request: SignalEvaluationRequest):
    """
    创建信号评估记录

    记录一个新的信号预测，用于后续评估。

    参数:
        ticker: 股票代码
        tf: 时间周期 (1m, 5m, 1d)
        signal_type: 信号类型 (breakout_confirmed, fakeout, etc.)
        direction: up / down
        predicted_behavior: 预测行为
        entry_price: 入场价
        target_price: 目标价
        invalidation_price: 止损价
        confidence: 置信度 (0-1)
        notes: 备注 (可选)

    返回:
        创建的评估记录
    """
    # 验证参数
    if request.tf not in ("1m", "5m", "1d"):
        raise HTTPException(
            status_code=400,
            detail={"code": "TIMEFRAME_INVALID", "message": f"无效的时间周期: {request.tf}"}
        )

    if request.direction not in ("up", "down"):
        raise HTTPException(
            status_code=400,
            detail={"code": "DIRECTION_INVALID", "message": f"无效的方向: {request.direction}"}
        )

    if not 0 <= request.confidence <= 1:
        raise HTTPException(
            status_code=400,
            detail={"code": "CONFIDENCE_INVALID", "message": "置信度必须在 0-1 之间"}
        )

    # 创建评估记录
    evaluation = SignalEvaluation(
        id=generate_eval_id(),
        ticker=request.ticker.upper(),
        tf=request.tf,
        created_at=datetime.utcnow().isoformat() + "Z",
        signal_type=request.signal_type,
        direction=request.direction,
        predicted_behavior=request.predicted_behavior,
        entry_price=request.entry_price,
        target_price=request.target_price,
        invalidation_price=request.invalidation_price,
        confidence=request.confidence,
        notes=request.notes,
        status="pending",
    )

    try:
        created = eval_db.create(evaluation)
        return {
            "id": created.id,
            "ticker": created.ticker,
            "tf": created.tf,
            "created_at": created.created_at,
            "signal_type": created.signal_type,
            "direction": created.direction,
            "predicted_behavior": created.predicted_behavior,
            "entry_price": created.entry_price,
            "target_price": created.target_price,
            "invalidation_price": created.invalidation_price,
            "confidence": created.confidence,
            "notes": created.notes,
            "status": created.status,
            "result": created.result,
            "actual_outcome": created.actual_outcome,
            "evaluation_notes": created.evaluation_notes,
            "evaluated_at": created.evaluated_at,
        }
    except Exception as e:
        logger.error(f"创建评估记录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "数据库错误"}
        )


@app.get("/v1/signal-evaluations")
async def list_signal_evaluations(
    ticker: str = Query(..., description="股票代码"),
    tf: Optional[str] = Query(None, description="时间周期过滤: 1m, 5m, 1d"),
    status: Optional[str] = Query(None, description="状态过滤: pending, correct, incorrect"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移"),
):
    """
    获取信号评估历史记录

    返回指定股票的评估记录列表和统计信息。

    参数:
        ticker: 股票代码 (必需)
        tf: 时间周期过滤 (可选)
        status: 状态过滤 (可选)
        limit: 返回数量限制 (默认 50)
        offset: 分页偏移 (默认 0)

    返回:
        评估记录列表和统计信息
    """
    # 验证参数
    if tf and tf not in ("1m", "5m", "1d"):
        raise HTTPException(
            status_code=400,
            detail={"code": "TIMEFRAME_INVALID", "message": f"无效的时间周期: {tf}"}
        )

    if status and status not in ("pending", "correct", "incorrect"):
        raise HTTPException(
            status_code=400,
            detail={"code": "STATUS_INVALID", "message": f"无效的状态: {status}"}
        )

    try:
        # 获取记录列表
        records = eval_db.list(
            ticker=ticker.upper(),
            tf=tf,
            status=status,
            limit=limit,
            offset=offset
        )

        # 获取总数
        total = eval_db.count(ticker=ticker.upper(), tf=tf, status=status)

        # 获取统计信息
        statistics = eval_db.get_statistics(ticker=ticker.upper(), tf=tf)

        return {
            "ticker": ticker.upper(),
            "total": total,
            "records": [
                {
                    "id": r.id,
                    "ticker": r.ticker,
                    "tf": r.tf,
                    "created_at": r.created_at,
                    "signal_type": r.signal_type,
                    "direction": r.direction,
                    "predicted_behavior": r.predicted_behavior,
                    "entry_price": r.entry_price,
                    "target_price": r.target_price,
                    "invalidation_price": r.invalidation_price,
                    "confidence": r.confidence,
                    "notes": r.notes,
                    "status": r.status,
                    "result": r.result,
                    "actual_outcome": r.actual_outcome,
                    "evaluation_notes": r.evaluation_notes,
                    "evaluated_at": r.evaluated_at,
                }
                for r in records
            ],
            "statistics": {
                "total_predictions": statistics.total_predictions,
                "correct": statistics.correct,
                "incorrect": statistics.incorrect,
                "pending": statistics.pending,
                "accuracy_rate": statistics.accuracy_rate,
                "by_signal_type": statistics.by_signal_type,
            }
        }
    except Exception as e:
        logger.error(f"获取评估记录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "数据库错误"}
        )


@app.put("/v1/signal-evaluation/{eval_id}")
async def update_signal_evaluation(eval_id: str, request: SignalEvaluationUpdateRequest):
    """
    更新信号评估结果

    更新预测的最终结果。

    参数:
        eval_id: 评估记录 ID
        status: correct / incorrect
        result: 结果类型 (target_hit, invalidation_hit, partial_correct, direction_wrong, timeout)
        actual_outcome: 实际发生的情况
        evaluation_notes: 评估备注 (可选)

    返回:
        更新后的评估记录
    """
    # 验证参数
    if request.status not in ("correct", "incorrect"):
        raise HTTPException(
            status_code=400,
            detail={"code": "STATUS_INVALID", "message": f"无效的状态: {request.status}"}
        )

    valid_results = ("target_hit", "invalidation_hit", "partial_correct", "direction_wrong", "timeout")
    if request.result not in valid_results:
        raise HTTPException(
            status_code=400,
            detail={"code": "RESULT_INVALID", "message": f"无效的结果类型: {request.result}"}
        )

    try:
        updated = eval_db.update(
            eval_id=eval_id,
            status=request.status,
            result=request.result,
            actual_outcome=request.actual_outcome,
            evaluation_notes=request.evaluation_notes
        )

        if updated is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND", "message": f"评估记录不存在: {eval_id}"}
            )

        return {
            "id": updated.id,
            "status": updated.status,
            "result": updated.result,
            "actual_outcome": updated.actual_outcome,
            "evaluation_notes": updated.evaluation_notes,
            "evaluated_at": updated.evaluated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新评估记录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "数据库错误"}
        )


@app.delete("/v1/signal-evaluation/{eval_id}")
async def delete_signal_evaluation(eval_id: str):
    """
    删除信号评估记录

    参数:
        eval_id: 评估记录 ID

    返回:
        删除确认
    """
    try:
        deleted = eval_db.delete(eval_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND", "message": f"评估记录不存在: {eval_id}"}
            )
        return {"deleted": True, "id": eval_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除评估记录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "数据库错误"}
        )


# ============ Watchlist (自选股) API ============

@app.get("/v1/watchlist")
async def get_watchlist():
    """
    获取自选股列表

    返回所有自选股及其实时状态。
    """
    try:
        items = watchlist_db.list()
        ws_manager = get_websocket_manager()

        result = []
        for item in items:
            # 获取实时价格（如果有）
            realtime = None
            if ws_manager:
                price_data = ws_manager.get_latest_price(item.ticker)
                if price_data:
                    realtime = {
                        "price": price_data.price,
                        "change": price_data.day_change,
                        "change_pct": price_data.day_change_pct,
                        "timestamp": price_data.timestamp.isoformat() if price_data.timestamp else None,
                    }

            result.append({
                "ticker": item.ticker,
                "added_at": item.added_at,
                "note": item.note,
                "realtime": realtime,
            })

        return {
            "count": len(items),
            "max": watchlist_db.MAX_ITEMS,
            "items": result,
        }
    except Exception as e:
        logger.error(f"获取自选股列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "数据库错误"}
        )


@app.post("/v1/watchlist/{ticker}", status_code=201)
async def add_to_watchlist(ticker: str, note: Optional[str] = None):
    """
    添加股票到自选股

    同时订阅 WebSocket 实时数据。
    最多添加 8 个股票（TwelveData 免费额度限制）。

    参数:
        ticker: 股票代码
        note: 可选备注

    返回:
        添加结果
    """
    ticker = ticker.upper()

    try:
        success, message = watchlist_db.add(ticker, note)

        if not success:
            raise HTTPException(
                status_code=400,
                detail={"code": "ADD_FAILED", "message": message}
            )

        # 订阅 WebSocket
        ws_manager = get_websocket_manager()
        if ws_manager:
            await ws_manager.subscribe(ticker)
            logger.info(f"已订阅 WebSocket: {ticker}")

        return {
            "success": True,
            "ticker": ticker,
            "message": message,
            "count": watchlist_db.count(),
            "max": watchlist_db.MAX_ITEMS,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加自选股失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "数据库错误"}
        )


@app.delete("/v1/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str):
    """
    从自选股移除

    同时取消 WebSocket 订阅。

    参数:
        ticker: 股票代码

    返回:
        移除结果
    """
    ticker = ticker.upper()

    try:
        success, message = watchlist_db.remove(ticker)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND", "message": message}
            )

        # 取消 WebSocket 订阅
        ws_manager = get_websocket_manager()
        if ws_manager:
            await ws_manager.unsubscribe(ticker)
            logger.info(f"已取消 WebSocket 订阅: {ticker}")

        return {
            "success": True,
            "ticker": ticker,
            "message": message,
            "count": watchlist_db.count(),
            "max": watchlist_db.MAX_ITEMS,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除自选股失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "数据库错误"}
        )


@app.get("/v1/watchlist/{ticker}/status")
async def get_watchlist_status(ticker: str):
    """
    检查股票是否在自选股列表

    参数:
        ticker: 股票代码

    返回:
        是否在自选股列表及实时数据状态
    """
    ticker = ticker.upper()

    is_watched = watchlist_db.is_in_watchlist(ticker)
    ws_manager = get_websocket_manager()

    realtime = None
    if is_watched and ws_manager:
        price_data = ws_manager.get_latest_price(ticker)
        if price_data:
            realtime = {
                "price": price_data.price,
                "change": price_data.day_change,
                "change_pct": price_data.day_change_pct,
                "timestamp": price_data.timestamp.isoformat() if price_data.timestamp else None,
            }

    return {
        "ticker": ticker,
        "is_watched": is_watched,
        "has_realtime": realtime is not None,
        "realtime": realtime,
        "count": watchlist_db.count(),
        "max": watchlist_db.MAX_ITEMS,
    }


# ============ 实时数据流 API ============

@app.get("/v1/stream/status")
async def stream_status():
    """
    WebSocket 连接状态

    返回当前 WebSocket 连接状态和已订阅的 symbols。
    """
    ws_manager = get_websocket_manager()

    if ws_manager is None:
        return {
            "enabled": False,
            "connected": False,
            "subscribed_symbols": [],
            "message": "WebSocket 未配置（需要 TwelveData API Key）"
        }

    return {
        "enabled": True,
        "connected": ws_manager.is_connected,
        "subscribed_symbols": list(ws_manager.subscribed_symbols),
        "cached_prices": {
            symbol: {
                "price": p.price,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None
            }
            for symbol, p in ws_manager.get_all_prices().items()
        }
    }


@app.get("/v1/stream/{ticker}")
async def stream_price(ticker: str):
    """
    实时价格 SSE 流

    通过 Server-Sent Events 推送实时价格更新。
    需要 TwelveData WebSocket 支持。

    参数:
        ticker: 股票代码（如 QQQ, AAPL）

    返回:
        SSE 事件流，每次价格更新推送一条消息

    事件格式:
        event: price
        data: {"symbol": "QQQ", "price": 520.50, "timestamp": "...", "change": 1.25, "change_pct": 0.24}
    """
    ticker = ticker.upper()
    ws_manager = get_websocket_manager()

    if ws_manager is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "WEBSOCKET_NOT_AVAILABLE", "message": "实时数据服务未启用"}
        )

    # 只为自选股提供实时数据流
    if not watchlist_db.is_in_watchlist(ticker):
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_IN_WATCHLIST", "message": f"{ticker} 不在自选股列表中，无法获取实时数据"}
        )

    async def event_generator():
        """生成 SSE 事件"""
        last_price = None

        while True:
            try:
                # 获取最新价格
                price_data = ws_manager.get_latest_price(ticker)

                if price_data and (last_price is None or price_data.price != last_price):
                    last_price = price_data.price
                    yield {
                        "event": "price",
                        "data": json.dumps({
                            "symbol": price_data.symbol,
                            "price": price_data.price,
                            "timestamp": price_data.timestamp.isoformat() if price_data.timestamp else None,
                            "change": price_data.day_change,
                            "change_pct": price_data.day_change_pct,
                        })
                    }

                # 等待一小段时间再检查
                await asyncio.sleep(0.2)

            except asyncio.CancelledError:
                logger.info(f"SSE 连接关闭: {ticker}")
                break
            except Exception as e:
                logger.error(f"SSE 事件生成错误: {e}")
                break

    return EventSourceResponse(event_generator())


@app.get("/v1/realtime/{ticker}")
async def get_realtime_price(ticker: str):
    """
    获取实时价格（单次请求）

    返回 WebSocket 缓存的最新价格，或从 REST API 获取。

    参数:
        ticker: 股票代码

    返回:
        最新价格数据
    """
    ticker = ticker.upper()
    ws_manager = get_websocket_manager()

    # 优先使用 WebSocket 缓存的价格
    if ws_manager:
        price_data = ws_manager.get_latest_price(ticker)
        if price_data:
            return {
                "ticker": ticker,
                "price": price_data.price,
                "timestamp": price_data.timestamp.isoformat() if price_data.timestamp else None,
                "change": price_data.day_change,
                "change_pct": price_data.day_change_pct,
                "source": "websocket",
                "latency": "realtime"
            }

        # 如果没有缓存，尝试订阅
        await ws_manager.subscribe(ticker)

    # 回退到 REST API
    try:
        bars = provider.get_bars(ticker, "1m", "1d")
        if bars:
            latest = bars[-1]
            return {
                "ticker": ticker,
                "price": latest.c,
                "timestamp": latest.t.isoformat() if latest.t else None,
                "open": latest.o,
                "high": latest.h,
                "low": latest.l,
                "volume": latest.v,
                "source": "rest",
                "latency": f"{settings.cache_ttl}s"
            }
    except Exception as e:
        logger.error(f"获取实时价格失败: {e}")

    raise HTTPException(
        status_code=404,
        detail={"code": "NO_DATA", "message": f"无法获取 {ticker} 的价格数据"}
    )
