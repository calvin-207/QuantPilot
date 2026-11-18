"""只读行情接口：不在HTTP请求线程里触发上游数据采集。"""
from datetime import datetime
from pathlib import Path
import os
from fastapi import APIRouter, HTTPException, Query
from quant_core.market.repository import SQLiteMarketRepository

router = APIRouter(prefix="/api/v1/market", tags=["market"])

def db_path() -> str:
    return os.environ.get("QUANTPILOT_MARKET_DB", "data/quantpilot-market.sqlite3")

@router.get("/instruments")
def instruments(q: str = Query("", max_length=80), limit: int = Query(50, ge=1, le=200)):
    repo = SQLiteMarketRepository(db_path())
    try:
        return {"items": repo.list_instruments(q, limit)}
    finally:
        repo.close()

@router.get("/bars")
def bars(
    symbol: str, timeframe: str, start: datetime, end: datetime,
    source: str = "FTShare", revision: str = "v1",
    limit: int = Query(5000, ge=1, le=20000)
):
    if timeframe not in ("1m", "15m", "60m", "1d"):
        raise HTTPException(422, "不支持的行情周期")
    if start.tzinfo is None or end.tzinfo is None or start > end:
        raise HTTPException(422, "时间范围必须有效且携带时区")
    repo = SQLiteMarketRepository(db_path())
    try:
        result = repo.read_bars(symbol, timeframe, start, end, source, revision, limit)
        return {"symbol": symbol, "timeframe": timeframe, "source": source,
                "revision": revision, "items": [b.as_record() for b in result]}
    finally:
        repo.close()
