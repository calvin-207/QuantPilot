"""统一证券与行情结构：使用Decimal保存价格，时间一律带时区。"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Literal
import re

class DataQualityError(ValueError):
    """源数据不满足入库条件，不允许静默修复。"""

AssetType = Literal["stock", "etf", "index"]
Timeframe = Literal["1m", "15m", "60m", "1d"]
SYMBOL = re.compile(r"^[0-9]{6}\.(SH|SZ|BJ)$")

def decimal(value: Decimal | int | str | float, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DataQualityError(f"{name} 不是合法数值") from exc
    if not result.is_finite():
        raise DataQualityError(f"{name} 不能为 NaN 或 Infinity")
    return result

@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    asset_type: AssetType
    listed_at: str | None = None

    def __post_init__(self):
        if not SYMBOL.fullmatch(self.symbol):
            raise DataQualityError("证券代码应为6位数字.SH/.SZ/.BJ")
        if self.asset_type not in ("stock", "etf", "index"):
            raise DataQualityError("未知证券类别")
        if not self.name.strip():
            raise DataQualityError("证券名称不能为空")

@dataclass(frozen=True)
class Bar:
    symbol: str
    timeframe: Timeframe
    ts: datetime  # K线结束时刻；必须含时区
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    turnover: Decimal
    source: str
    revision: str = "v1"

    def __post_init__(self):
        if not SYMBOL.fullmatch(self.symbol):
            raise DataQualityError("证券代码无效")
        if self.timeframe not in ("1m", "15m", "60m", "1d"):
            raise DataQualityError("不支持的K线周期")
        if self.ts.tzinfo is None or self.ts.utcoffset() is None:
            raise DataQualityError("K线时间必须携带时区")
        if not self.source.strip() or not self.revision.strip():
            raise DataQualityError("来源和版本不能为空")
        for name in ("open", "high", "low", "close", "volume", "turnover"):
            object.__setattr__(self, name, decimal(getattr(self, name), name))
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise DataQualityError("价格必须大于0")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close) or self.high < self.low:
            raise DataQualityError("OHLC关系不合法")
        if self.volume < 0 or self.turnover < 0:
            raise DataQualityError("成交量、成交额不能为负")

    def as_record(self) -> dict:
        return {
            "symbol": self.symbol, "timeframe": self.timeframe,
            "ts": self.ts.astimezone(timezone.utc).isoformat(),
            "open": str(self.open), "high": str(self.high), "low": str(self.low),
            "close": str(self.close), "volume": str(self.volume),
            "turnover": str(self.turnover), "source": self.source,
            "revision": self.revision
        }
