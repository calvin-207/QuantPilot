# QuantPilot P2：统一证券行情数据中心

## 已实现

- `Instrument`：A股股票、ETF、指数统一证券标识（.SH/.SZ/.BJ）。
- `Bar`：1m/15m/60m/1d K线，带时区的结束时间、OHLC、成交量、成交额、来源与修订版本。
- 价格由 `Decimal` 保留十进制表示；不允许 NaN、负成交额、错误 OHLC、无时区时间。
- `aggregate_minutes`：使用上海交易时区按常规上午/下午交易时段聚合，缺失分钟不伪造结果，不跨午休。
- `SQLiteMarketRepository`：本地存储，按照证券、周期、结束时间、来源、修订版本幂等入库。
- `MarketDataProvider`：供应商协议，采集前验证证券、来源、周期、时点与修订版本。
- `FTShareProvider`：以**调用方传入的已鉴权工具调用器**接入股票历史日线。暂不自行处理生产凭证；分钟历史和证券元数据接口未完成权限与口径核验，主动报错。
- FastAPI：`GET /api/v1/market/instruments` 和 `GET /api/v1/market/bars`，只读本地历史缓存。

## 本地运行

```bash
python -m pip install -e '.[dev]'
pytest -q
uvicorn backend.app.main:app --reload
```

设置 `QUANTPILOT_MARKET_DB` 为 SQLite 文件路径，默认使用 `.local/market.sqlite3`。

## 导入合法历史数据

准备带有以下列的 CSV：

```csv
symbol,timeframe,ts,open,high,low,close,volume,turnover,source,revision
600519.SH,1d,2026-11-17T15:00:00+08:00,10,11,9,10.5,100,1050,licensed-source,v1
```

这里的价格只是字段格式示例，不是真实股票价格。实际使用时请替换为有权使用、已核实的数据。

```bash
python -m tools.import_market_csv ./my_authorized_bars.csv --db .local/market.sqlite3
```

随后调用：

```text
GET /api/v1/market/bars?symbol=600519.SH&timeframe=1d&start=2026-11-01T00:00:00%2B08:00&end=2026-11-30T00:00:00%2B08:00&source=licensed-source
```

注意：K线必须带时区；日K结束时间约定为交易所本地15:00。供应商原始时间戳可能具有不同定义，需要在适配层先规范化。

## 由1分钟数据生成15/60分钟K线

在完成1分钟行情导入后，执行：

```bash
python -m tools.build_timeframes \
  --db .local/market.sqlite3 \
  --symbol 600519.SH \
  --start '2026-11-17T09:30:00+08:00' \
  --end '2026-11-17T15:00:00+08:00' \
  --source licensed-source
```

聚合严格按中国A股日常交易时段计算，上午与下午分开，**缺失或不完整的15/60分钟窗口不会产出K线**；大批数据务必按日期区间分段构建，超过单次读取上限会明确失败。当前模块不处理特殊交易时段、半日交易或竞价阶段行情，这些场景需要交易日历适配后才纳入。

## 边界和后续任务

1. 这是可用的本地研发仓储，不是已完成的全市场生产级 PostgreSQL/Parquet 数据湖。
2. 真实 FtShare 实例的授权、额度、批量分页、历史覆盖和分钟数据口径尚未核验。现有 `FTShareProvider` 只验证注入的工具接口形状，不能宣称已完成实盘数据联调。
3. 数据版本目前为文本版本号；后续需要补充修订批次、快照冻结和采集审计。
4. 指数分钟、ETF净申赎计算依旧由 `etf/` 原子系统处理。
5. 后续 P2.1：证券主数据同步与多提供商真实联调、增量补数、交易日历、1m历史与数据完整率；之后再建设个股看板。
6. 历史回测必须使用Point-in-Time股票池和可用时间，不能用当前证券名单回填历史。
