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

import logging
import sys
import os
from typing import Optional
from dataclasses import asdict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .cache import get_cache, cache_key
from .providers import get_provider, TickerNotFoundError, RateLimitError, ProviderError
from .services.llm_service import LLMService, generate_narrative, prepare_analysis_for_llm
from .database import SignalEvaluationDB, SignalEvaluation, generate_eval_id

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
    finally:
        # 恢复 API 的 src 模块
        if api_src:
            sys.modules['src'] = api_src
        sys.modules.update(api_src_submodules)

    return (
        core_analyze.analyze_market,
        core_analyze.AnalysisParams,
        core_models.Bar,
        core_models.AnalysisReport
    )

# 导入 core 模块
analyze_market, AnalysisParams, CoreBar, AnalysisReport = _import_core_package()

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

        # 准备 LLM 输入数据（结构化 JSON，不发送原始 OHLCV）
        analysis_json = prepare_analysis_for_llm(
            report=report_dict,
            ticker=request.ticker,
            timeframe=request.tf,
            price=current_price,
            include_evidence=True
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
