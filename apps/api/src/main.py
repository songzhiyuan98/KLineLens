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
from .providers import YFinanceProvider, TickerNotFoundError, RateLimitError, ProviderError

# 导入 core 模块（使用独立命名空间避免与 API 的 src 冲突）
import importlib.util
import importlib.abc

def _import_core_package():
    """将 packages/core/src 作为 'klinelens_core' 包导入"""
    core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'packages', 'core'))

    # 将 core 路径添加到 sys.path
    if core_path not in sys.path:
        sys.path.insert(0, core_path)

    # 使用 src 作为包名导入（由于 src 已存在，使用别名技术）
    # 先保存当前 API 的 src 模块
    api_src = sys.modules.get('src')

    # 临时移除，允许导入 core 的 src
    if api_src:
        del sys.modules['src']

    try:
        # 导入 core 的 src 模块
        import src as core_src_module
        return core_src_module
    finally:
        # 恢复 API 的 src 模块
        if api_src:
            sys.modules['src'] = api_src

# 导入 core 模块
_core = _import_core_package()
analyze_market = _core.analyze_market
AnalysisParams = _core.AnalysisParams
CoreBar = _core.Bar
AnalysisReport = _core.AnalysisReport

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
provider = YFinanceProvider()
cache = get_cache(default_ttl=settings.cache_ttl)


# ============ 辅助函数 ============

def report_to_dict(report: AnalysisReport) -> dict:
    """
    将 AnalysisReport 转换为 JSON 可序列化的字典

    处理 datetime 和嵌套 dataclass 的序列化。
    """
    def serialize(obj):
        """递归序列化对象"""
        if isinstance(obj, datetime):
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
