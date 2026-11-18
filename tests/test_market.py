from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
import pytest

from quant_core.market import Bar, Instrument, DataQualityError, SQLiteMarketRepository, aggregate_minutes, ingest_bars
from quant_core.market.ftshare import FTShareProvider
from quant_core.market.provider import ProviderUnavailable

CN = ZoneInfo("Asia/Shanghai")

def mkbar(n=1, symbol="600519.SH", minute=None):
    at = minute or datetime(2026, 11, 17, 9, 30, tzinfo=CN) + timedelta(minutes=n)
    return Bar(symbol, "1m", at, "10", "11", "9", "10.5", "100", "1050", "sample")

def test_ohlc_and_tz_validation():
    with pytest.raises(DataQualityError):
        Bar("600519.SH", "1d", datetime(2026, 1, 1), "10", "11", "9", "10", 1, 10, "sample")
    with pytest.raises(DataQualityError):
        Bar("600519.SH", "1d", datetime.now(timezone.utc), "10", "9", "8", "10", 1, 10, "sample")
    with pytest.raises(DataQualityError):
        Instrument("INVALID", "未知", "stock")
    with pytest.raises(DataQualityError):
        mkbar().__class__("600519.SH", "1m", mkbar().ts, "NaN", 11, 9, 10, 1, 10, "sample")

def test_minute_aggregation_no_lunch_crossing():
    morning = [mkbar(i) for i in range(1, 121)]
    afternoon = [mkbar(i, minute=datetime(2026, 11, 17, 13, 0, tzinfo=CN) + timedelta(minutes=i)) for i in range(1, 121)]
    bars = aggregate_minutes(morning + afternoon, "60m")
    assert len(bars) == 4
    assert [b.ts.astimezone(CN).strftime("%H:%M") for b in bars] == ["10:30", "11:30", "14:00", "15:00"]
    assert bars[0].volume == Decimal("6000")
    assert bars[0].high == Decimal("11")
    assert bars[-1].close == Decimal("10.5")

def test_missing_minute_does_not_invent_a_bar():
    arr = [mkbar(i) for i in range(1,16) if i != 8]
    assert aggregate_minutes(arr, "15m") == []
    with pytest.raises(DataQualityError):
        aggregate_minutes([mkbar(1),mkbar(1)], "15m")

def test_repository_idempotent_and_revision_isolation(tmp_path):
    repo = SQLiteMarketRepository(tmp_path / "market.db")
    repo.upsert_instruments([Instrument("600519.SH", "贵州茅台", "stock")])
    assert repo.list_instruments("茅台")[0]["symbol"] == "600519.SH"
    b = mkbar()
    assert repo.write_bars([b]) == 1
    assert repo.write_bars([b]) == 1
    assert len(repo.read_bars(b.symbol, "1m", b.ts, b.ts, "sample")) == 1
    changed = Bar(b.symbol,b.timeframe,b.ts,b.open,b.high,b.low,b.close,b.volume,b.turnover,"sample","v2")
    repo.write_bars([changed])
    assert len(repo.read_bars(b.symbol, "1m", b.ts,b.ts,"sample","v2")) == 1
    with pytest.raises(DataQualityError):
        repo.write_bars([b,b])
    repo.close()

def test_ingest_rejects_wrong_instrument_before_writing(tmp_path):
    repo = SQLiteMarketRepository(tmp_path / "market.db")
    class BadProvider:
        name = "sample"
        def fetch_bars(self, *args):
            return [mkbar(symbol="000001.SZ")]
    b = mkbar()
    with pytest.raises(DataQualityError):
        ingest_bars(BadProvider(),repo,b.symbol,"1m",b.ts,b.ts)
    assert not repo.read_bars(b.symbol,"1m",b.ts,b.ts,"sample")
    repo.close()

def test_ftshare_adapter_with_injected_mock_client():
    ts = datetime(2026,11,17,15,0,tzinfo=CN)
    def fake_call(name, args):
        assert name == "ft_v2_stock_candlesticks_batch"
        assert args["symbols"] == ["600519.SH"]
        return {"data": [{"symbol":"600519.SH","ts_millis":int(ts.timestamp()*1000),"open":10,"high":11,"low":9,"close":10.5,"volume":100,"turnover":1050}]}
    provider = FTShareProvider(fake_call)
    bars = provider.fetch_bars("600519.SH","1d",ts-timedelta(days=1),ts)
    assert len(bars) == 1 and bars[0].source == "FTShare"
    with pytest.raises(ProviderUnavailable):
        provider.fetch_bars("600519.SH","1m",ts-timedelta(days=1),ts)

def test_api_reads_local_data(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    filename = tmp_path/"market.db"
    monkeypatch.setenv("QUANTPILOT_MARKET_DB",str(filename))
    repo = SQLiteMarketRepository(filename)
    repo.upsert_instruments([Instrument("600519.SH","贵州茅台","stock")])
    repo.write_bars([mkbar()])
    repo.close()
    client = TestClient(app)
    assert client.get("/api/v1/market/instruments",params={"q":"贵州"}).json()["items"][0]["symbol"] == "600519.SH"
    start = datetime(2026,11,17,9,30,tzinfo=CN).isoformat()
    end = datetime(2026,11,17,10,0,tzinfo=CN).isoformat()
    res = client.get("/api/v1/market/bars",params={"symbol":"600519.SH","timeframe":"1m","start":start,"end":end,"source":"sample"})
    assert res.status_code == 200 and len(res.json()["items"]) == 1
    assert client.get("/api/v1/market/bars",params={"symbol":"600519.SH","timeframe":"1m","start":"2026-11-17T09:30:00","end":end}).status_code == 422

def test_csv_import_validation_and_atomicity(tmp_path):
    from tools.import_market_csv import load_csv
    path = tmp_path / "bars.csv"
    path.write_text(
        "symbol,timeframe,ts,open,high,low,close,volume,turnover,source,revision\n"
        "600519.SH,1m,2026-11-17T09:31:00+08:00,10,11,9,10.5,100,1050,sample,v1\n",
        encoding="utf-8"
    )
    rows = load_csv(path)
    assert len(rows) == 1 and rows[0].source == "sample"
    path.write_text(path.read_text(encoding="utf-8") + "600519.SH,1m,2026-11-17T09:31:00+08:00,10,11,9,10.5,100,1050,sample,v1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="重复"):
        load_csv(path)

def test_market_api_does_not_create_missing_db(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    db = tmp_path / "not-created.db"
    monkeypatch.setenv("QUANTPILOT_MARKET_DB", str(db))
    response = TestClient(app).get("/api/v1/market/instruments")
    assert response.status_code == 503
    assert not db.exists()
