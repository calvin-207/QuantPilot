"""FtShare 历史日K适配：由调用方注入已有鉴权的MCP工具客户端。

本模块不擅自向未知公网端点发送API Key；实时K线及分钟历史
需要分别验证账号权限、接口返回口径，再添加适配。
"""
from datetime import datetime, timezone
from typing import Callable
from .models import Bar, DataQualityError
from .provider import ProviderUnavailable

class FTShareProvider:
    name = "FTShare"

    def __init__(self, call_tool: Callable[[str, dict], dict], revision: str = "v1"):
        self._call_tool = call_tool
        self.revision = revision

    def fetch_instruments(self):
        raise ProviderUnavailable("证券主数据接口尚未完成权限验证")

    def fetch_bars(self, symbol: str, timeframe: str, start: datetime, end: datetime):
        if timeframe != "1d":
            raise ProviderUnavailable("分钟历史接口尚未完成权限与时间戳口径验证")
        if start.tzinfo is None or end.tzinfo is None or start > end:
            raise ValueError("时间区间必须含时区")
        data = self._call_tool("ft_v2_stock_candlesticks_batch", {
            "symbols": [symbol],
            "interval_unit": "Day",
            "adjust_kind": "none",
            "since_ts_millis": int(start.timestamp() * 1000),
            "until_ts_millis": int(end.timestamp() * 1000),
            "limit": 1000
        })
        if data.get("metadata", {}).get("truncated"):
            raise ProviderUnavailable("FtShare结果被截断，不允许写入不完整批次")
        if not isinstance(data.get("data"), list):
            raise ProviderUnavailable("FtShare未返回有效行情列表")
        result = []
        for item in data["data"]:
            if item.get("symbol") != symbol:
                raise DataQualityError("FtShare返回证券代码不匹配")
            if "ts_millis" not in item or "volume" not in item or "turnover" not in item:
                raise DataQualityError("FtShare记录缺少必要行情字段")
            ts = datetime.fromtimestamp(int(item["ts_millis"]) / 1000, tz=timezone.utc)
            if not start <= ts <= end:
                raise DataQualityError("FtShare返回区间外的数据")
            result.append(Bar(
                symbol=symbol, timeframe="1d", ts=ts,
                open=item["open"], high=item["high"], low=item["low"],
                close=item["close"], volume=item["volume"],
                turnover=item["turnover"], source=self.name, revision=self.revision
            ))
        return sorted(result, key=lambda x: x.ts)
