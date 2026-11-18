from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal
import pytest
from quant_core.market import Bar, SQLiteMarketRepository
from tools.build_timeframes import build_timeframes

CN = ZoneInfo("Asia/Shanghai")

def make_bars(base, n):
    return [
        Bar("600519.SH", "1m", base + timedelta(minutes=i),
            Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10.5"),
            Decimal("100"), Decimal("1000"), "sample", "v1")
        for i in range(1, n + 1)
    ]

def test_build_15_and_60m_and_idempotency(tmp_path):
    repo = SQLiteMarketRepository(tmp_path/"market.db")
    base = datetime(2026,11,17,9,30,tzinfo=CN)
    bars = make_bars(base, 120)
    repo.write_bars(bars)
    end = bars[-1].ts
    out = build_timeframes(repo, "600519.SH", base, end, "sample")
    assert out == {"15m":8,"60m":2}
    assert build_timeframes(repo, "600519.SH", base, end, "sample") == out
    result = repo.read_bars("600519.SH", "60m", base, end, "sample")
    assert len(result) == 2 and result[0].volume == Decimal("6000")
    repo.close()

def test_incomplete_bucket_is_skipped(tmp_path):
    repo = SQLiteMarketRepository(tmp_path/"market.db")
    base = datetime(2026,11,17,9,30,tzinfo=CN)
    bars = [bar for i, bar in enumerate(make_bars(base, 60), start=1) if i != 8]
    repo.write_bars(bars)
    assert build_timeframes(repo, "600519.SH", base, base + timedelta(minutes=60), "sample") == {"15m":3,"60m":0}
    repo.close()

def test_truncated_source_is_rejected(tmp_path):
    repo = SQLiteMarketRepository(tmp_path/"market.db")
    base = datetime(2026,11,17,9,30,tzinfo=CN)
    repo.write_bars(make_bars(base, 15))
    with pytest.raises(ValueError, match="上限"):
        build_timeframes(repo, "600519.SH", base, base + timedelta(minutes=15), "sample", max_rows=15)
    repo.close()
