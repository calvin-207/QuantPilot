"""从已导入的1分钟K线生成15分钟、60分钟K线。

仅处理完整交易时段的有效分钟，不填补缺口；输入记录触及读取上限时拒绝处理，
避免数据库结果被截断却误认为聚合完整。
"""
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from quant_core.market import SQLiteMarketRepository, aggregate_minutes

def build_timeframes(
    repository: SQLiteMarketRepository, symbol: str, start: datetime, end: datetime,
    source: str, revision: str = "v1", max_rows: int = 20000
) -> dict[str, int]:
    if not 1 <= max_rows <= 20000:
        raise ValueError("max_rows范围为1..20000")
    rows = repository.read_bars(symbol, "1m", start, end, source, revision, max_rows)
    if len(rows) >= max_rows:
        raise ValueError("读取达到上限，请缩短日期范围以避免缺漏")
    result = {}
    for target in ("15m", "60m"):
        aggregated = aggregate_minutes(rows, target)
        repository.write_bars(aggregated)
        result[target] = len(aggregated)
    return result

def main():
    parser = ArgumentParser(description="从本地1分钟K线构建A股15分钟/60分钟K线")
    parser.add_argument("--db", type=Path, default=Path(".local/market.sqlite3"))
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start", required=True, help="ISO日期时间（包含时区）")
    parser.add_argument("--end", required=True, help="ISO日期时间（包含时区）")
    parser.add_argument("--source", required=True)
    parser.add_argument("--revision", default="v1")
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error("行情数据库不存在，请先导入合法数据")
    repo = SQLiteMarketRepository(args.db)
    try:
        counts = build_timeframes(repo, args.symbol, datetime.fromisoformat(args.start),
                                  datetime.fromisoformat(args.end), args.source, args.revision)
    finally:
        repo.close()
    print(f"聚合完成：15分钟 {counts['15m']} 根；60分钟 {counts['60m']} 根")

if __name__ == "__main__":
    main()
