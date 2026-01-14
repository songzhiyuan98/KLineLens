"""
KLineLens API Server

FastAPI application for market structure analysis.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="KLineLens API",
    description="Market structure analysis API",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "klinelens-api"}


@app.get("/v1/bars")
async def get_bars(ticker: str, tf: str = "1m", window: str | None = None):
    """
    Fetch OHLCV bars for a ticker.

    - ticker: Stock symbol (e.g., TSLA)
    - tf: Timeframe (1m, 5m, 1d)
    - window: Lookback period (e.g., 1d, 5d, 1mo)
    """
    # Placeholder - will be implemented in Milestone 1
    return {
        "ticker": ticker.upper(),
        "tf": tf,
        "bar_count": 0,
        "bars": [],
        "message": "Not implemented yet - Milestone 1",
    }


@app.post("/v1/analyze")
async def analyze(data: dict):
    """
    Run structure + behavior analysis.

    Request body:
    - ticker: Stock symbol
    - tf: Timeframe
    - window: Lookback period
    """
    # Placeholder - will be implemented in Milestone 2-3
    ticker = data.get("ticker", "").upper()
    tf = data.get("tf", "1m")

    return {
        "ticker": ticker,
        "tf": tf,
        "message": "Not implemented yet - Milestone 2-3",
    }
