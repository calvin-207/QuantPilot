"""P2本地SQLite仓储：方便开箱即用；生产大规模数据后续迁移PostgreSQL。"""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sqlite3
from .models import Bar, Instrument, DataQualityError

DDL = """
CREATE TABLE IF NOT EXISTS instruments(
 symbol TEXT PRIMARY KEY, name TEXT NOT NULL,
 asset_type TEXT NOT NULL, listed_at TEXT
);
CREATE TABLE IF NOT EXISTS market_bars(
 symbol TEXT NOT NULL, timeframe TEXT NOT NULL, ts TEXT NOT NULL,
 open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
 close TEXT NOT NULL, volume TEXT NOT NULL, turnover TEXT NOT NULL,
 source TEXT NOT NULL, revision TEXT NOT NULL,
 PRIMARY KEY(symbol,timeframe,ts,source,revision)
);
CREATE INDEX IF NOT EXISTS ix_market_bars_lookup
 ON market_bars(symbol,timeframe,ts);
"""

class SQLiteMarketRepository:
    def __init__(self, filename: str | Path):
        self.filename = str(filename)
        self.conn = sqlite3.connect(self.filename)
        self.conn.executescript(DDL)

    def close(self):
        self.conn.close()

    def upsert_instruments(self, items: list[Instrument]) -> None:
        with self.conn:
            self.conn.executemany(
                "INSERT INTO instruments(symbol,name,asset_type,listed_at) VALUES(?,?,?,?) "
                "ON CONFLICT(symbol) DO UPDATE SET name=excluded.name, asset_type=excluded.asset_type, listed_at=excluded.listed_at",
                [(x.symbol, x.name, x.asset_type, x.listed_at) for x in items]
            )

    def list_instruments(self, query: str = "", limit: int = 50) -> list[dict]:
        if not 1 <= limit <= 200:
            raise ValueError("limit范围为1..200")
        rows = self.conn.execute(
            "SELECT symbol,name,asset_type,listed_at FROM instruments "
            "WHERE symbol LIKE ? OR name LIKE ? ORDER BY symbol LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        return [dict(zip(("symbol","name","asset_type","listed_at"), r)) for r in rows]

    def write_bars(self, bars: list[Bar]) -> int:
        if not bars:
            return 0
        keys = [(b.symbol,b.timeframe,b.as_record()["ts"],b.source,b.revision) for b in bars]
        if len(keys) != len(set(keys)):
            raise DataQualityError("同批次存在重复K线")
        with self.conn:
            self.conn.executemany(
                "INSERT INTO market_bars(symbol,timeframe,ts,open,high,low,close,volume,turnover,source,revision)"
                " VALUES(:symbol,:timeframe,:ts,:open,:high,:low,:close,:volume,:turnover,:source,:revision)"
                " ON CONFLICT(symbol,timeframe,ts,source,revision) DO UPDATE SET"
                " open=excluded.open,high=excluded.high,low=excluded.low,close=excluded.close,"
                " volume=excluded.volume,turnover=excluded.turnover",
                [b.as_record() for b in bars]
            )
        return len(bars)

    def read_bars(self, symbol: str, timeframe: str, start: datetime, end: datetime,
                  source: str, revision: str = "v1", limit: int = 5000) -> list[Bar]:
        if not 1 <= limit <= 20000:
            raise ValueError("limit范围为1..20000")
        if start.tzinfo is None or end.tzinfo is None or start > end:
            raise ValueError("时间区间必须有效且含时区")
        from datetime import timezone
        lo = start.astimezone(timezone.utc).isoformat()
        hi = end.astimezone(timezone.utc).isoformat()
        rows = self.conn.execute(
            "SELECT symbol,timeframe,ts,open,high,low,close,volume,turnover,source,revision"
            " FROM market_bars WHERE symbol=? AND timeframe=? AND source=? AND revision=?"
            " AND ts>=? AND ts<=? ORDER BY ts LIMIT ?",
            (symbol,timeframe,source,revision,lo,hi,limit)
        ).fetchall()
        return [Bar(symbol=r[0],timeframe=r[1],ts=datetime.fromisoformat(r[2]),
                    open=Decimal(r[3]),high=Decimal(r[4]),low=Decimal(r[5]),
                    close=Decimal(r[6]),volume=Decimal(r[7]),turnover=Decimal(r[8]),
                    source=r[9],revision=r[10]) for r in rows]
