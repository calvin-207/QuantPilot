"""将已授权的标准化行情CSV导入QuantPilot本地数据库。

CSV: symbol,timeframe,ts,open,high,low,close,volume,turnover,source,revision
ts必须是带时区的ISO8601 K线结束时刻。工具不从互联网上自行下载行情。
"""
from argparse import ArgumentParser
import csv
from datetime import datetime
from pathlib import Path
from quant_core.market import Bar, SQLiteMarketRepository

COLUMNS = ("symbol","timeframe","ts","open","high","low","close",
           "volume","turnover","source","revision")

def load_csv(filename: Path) -> list[Bar]:
    rows = []
    with filename.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or any(c not in reader.fieldnames for c in COLUMNS):
            raise ValueError("CSV列不完整，必须包含 " + ",".join(COLUMNS))
        for line, row in enumerate(reader, start=2):
            try:
                rows.append(Bar(
                    symbol=row["symbol"], timeframe=row["timeframe"],
                    ts=datetime.fromisoformat(row["ts"]), open=row["open"],
                    high=row["high"], low=row["low"], close=row["close"],
                    volume=row["volume"], turnover=row["turnover"],
                    source=row["source"], revision=row["revision"]
                ))
            except (ValueError, KeyError) as exc:
                raise ValueError(f"CSV第{line}行不合法：{exc}") from exc
    if len({(b.symbol,b.timeframe,b.ts,b.source,b.revision) for b in rows}) != len(rows):
        raise ValueError("CSV包含重复的行情主键")
    return rows

def main():
    parser = ArgumentParser(description="导入经授权的标准化行情CSV")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--db", type=Path, default=Path(".local/market.sqlite3"))
    args = parser.parse_args()
    rows = load_csv(args.csv)  # 所有行校验成功后再写入
    args.db.parent.mkdir(parents=True, exist_ok=True)
    repo = SQLiteMarketRepository(args.db)
    try:
        count = repo.write_bars(rows)
    finally:
        repo.close()
    print(f"导入成功：{count} 根K线；SQLite={args.db}")

if __name__ == "__main__":
    main()
