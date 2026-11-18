"""只读行情接口：不在HTTP请求里调用供应商，也不自动创建空数据库。"""
from datetime import datetime
from pathlib import Path
import os
from fastapi import APIRouter, HTTPException, Query
from quant_core.market.repository import SQLiteMarketRepository
from quant_core.market.models import SYMBOL

router = APIRouter(prefix="/api/v1/market", tags=["market"])

def db_path() -> Path:
    return Path(os.environ.get("QUANTPILOT_MARKET_DB", ".local/market.sqlite3"))

def open_market_db() -> SQLiteMarketRepository:
    filename = db_path()
    if not filename.is_file():
        raise HTTPException(503, "行情库尚未初始化，请先导入已授权的历史数据")
    return SQLiteMarketRepository(filename)

@router.get("/instruments")
def instruments(q: str = Query("", max_length=80), limit: int = Query(50, ge=1, le=200)):
    repo = open_market_db()
    try:
        return {"items": repo.list_instruments(q, limit)}
    finally:
        repo.close()

@router.get("/bars")
def bars(
    symbol: str = Query(..., max_length=9),
    timeframe: str = Query(..., max_length=3),
    start: datetime = Query(...),
    end: datetime = Query(...),
    source: str = Query("FTShare", min_length=1, max_length=80),
    revision: str = Query("v1", min_length=1, max_length=80),
    limit: int = Query(5000, ge=1, le=20000)
):
    if not SYMBOL.fullmatch(symbol) or timeframe not in ("1m", "15m", "60m", "1d"):
        raise HTTPException(422, "证券代码或行情周期不合法")
    if start.tzinfo is None or end.tzinfo is None or start > end:
        raise HTTPException(422, "时间范围必须有效且携带时区")
    repo = open_market_db()
    try:
        result = repo.read_bars(symbol, timeframe, start, end, source, revision, limit)
        return {"symbol": symbol, "timeframe": timeframe, "source": source,
                "revision": revision, "items": [b.as_record() for b in result]}
    finally:
        repo.close()
