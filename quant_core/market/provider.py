"""行情供应商协议；真实采集必须由有权限的服务实现。"""
from datetime import datetime
from typing import Protocol, Sequence
from .models import Bar, Instrument, DataQualityError
from .repository import SQLiteMarketRepository

class ProviderUnavailable(RuntimeError):
    """服务未授权、无网络或无可用数据时显式失败。"""

class MarketDataProvider(Protocol):
    name: str
    def fetch_instruments(self) -> Sequence[Instrument]: ...
    def fetch_bars(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> Sequence[Bar]: ...

def ingest_bars(provider: MarketDataProvider, repository: SQLiteMarketRepository,
                symbol: str, timeframe: str, start: datetime, end: datetime) -> int:
    """先检查完整批次，再一次写入；不允许供应商返回别的证券或混合版本。"""
    if start.tzinfo is None or end.tzinfo is None or start > end:
        raise ValueError("时间区间无效")
    bars = list(provider.fetch_bars(symbol, timeframe, start, end))
    if any(b.symbol != symbol or b.timeframe != timeframe or b.source != provider.name
           or not (start <= b.ts <= end) for b in bars):
        raise DataQualityError("供应商返回了不匹配证券、周期、来源或区间的数据")
    timestamps = [b.ts for b in bars]
    if len(timestamps) != len(set(timestamps)) or timestamps != sorted(timestamps):
        raise DataQualityError("供应商K线存在重复或乱序")
    if len({b.revision for b in bars}) > 1:
        raise DataQualityError("单批次不可混合数据修订版本")
    return repository.write_bars(bars)
