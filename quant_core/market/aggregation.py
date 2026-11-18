"""A股分钟聚合：K线时间按区间结束时刻；不跨午休，不补造缺失分钟。"""
from collections import defaultdict
from datetime import datetime, time
from zoneinfo import ZoneInfo
from .models import Bar, DataQualityError

CN = ZoneInfo("Asia/Shanghai")

def _slot(ts: datetime) -> tuple[str, int] | None:
    local = ts.astimezone(CN)
    minute = local.hour * 60 + local.minute
    # 标准分钟K线以结束时刻标注：09:31..11:30、13:01..15:00。
    morning = 9 * 60 + 30
    afternoon = 13 * 60
    if morning < minute <= 11 * 60 + 30:
        return "am", minute - morning
    if afternoon < minute <= 15 * 60:
        return "pm", minute - afternoon
    return None

def aggregate_minutes(rows: list[Bar], target: str) -> list[Bar]:
    """仅完整的15/60根连续分钟输出一根K线；缺失时直接跳过。"""
    if target not in ("15m", "60m"):
        raise ValueError("仅支持由1m聚合成15m或60m")
    if not rows:
        return []
    n = int(target[:-1])
    symbol = rows[0].symbol
    source = rows[0].source
    revision = rows[0].revision
    groups: dict[tuple[str, str, int], list[tuple[int, Bar]]] = defaultdict(list)
    seen = set()
    for bar in rows:
        if bar.timeframe != "1m" or bar.symbol != symbol or bar.source != source or bar.revision != revision:
            raise DataQualityError("聚合输入的证券、周期、来源及数据版本必须一致")
        local = bar.ts.astimezone(CN)
        slot = _slot(bar.ts)
        if not slot:
            raise DataQualityError("发现A股常规交易时段以外的分钟K线")
        key = (local.date().isoformat(), slot[0], (slot[1] - 1) // n)
        unique = (key[0], slot[0], slot[1])
        if unique in seen:
            raise DataQualityError("重复分钟记录")
        seen.add(unique)
        groups[key].append((slot[1], bar))
    result = []
    for key, items in groups.items():
        items.sort(key=lambda pair: pair[0])
        first = key[2] * n + 1
        if [i for i, _ in items] != list(range(first, first + n)):
            continue
        bars = [bar for _, bar in items]
        result.append(Bar(
            symbol=symbol, timeframe=target, ts=bars[-1].ts,
            open=bars[0].open, high=max(b.high for b in bars),
            low=min(b.low for b in bars), close=bars[-1].close,
            volume=sum((b.volume for b in bars), start=bars[0].volume * 0),
            turnover=sum((b.turnover for b in bars), start=bars[0].turnover * 0),
            source=source, revision=revision
        ))
    return sorted(result, key=lambda x: x.ts)
