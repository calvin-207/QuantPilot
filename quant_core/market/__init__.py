"""统一行情领域：标准K线、交易时段聚合、仓储与数据提供者接口。"""
from .models import Bar, Instrument, DataQualityError
from .aggregation import aggregate_minutes
from .repository import SQLiteMarketRepository
from .provider import MarketDataProvider, ProviderUnavailable, ingest_bars

__all__ = ["Bar", "Instrument", "DataQualityError", "aggregate_minutes",
           "SQLiteMarketRepository", "MarketDataProvider", "ProviderUnavailable",
           "ingest_bars"]
