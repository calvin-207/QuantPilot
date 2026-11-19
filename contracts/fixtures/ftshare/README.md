# FtShare 合成响应样本

**全部数值均为程序编造的演示样本，不含任何真实行情、份额或净值数据。** 这些文件的作用是：在没有真实 API 凭证时，对两个适配层做接口形状与口径的回归测试——Python 侧 `quant_core/market/ftshare.py`（注入 `call_tool` 回放）与 Node 侧 `etf/src/server/ftshare.js` 及其采集器（后续接入）。真实凭证到位后，同一套样本升级为录制样本的占位骨架，形状不变、数值替换为已授权的录制值。

## 外壳格式

每个文件是一个样本：

```json
{
  "tool": "ft_v4_stock_realtime_minute_kline",
  "synthetic": true,
  "arguments": { },
  "response": { "metadata": { "truncated": false }, "data": [] }
}
```

- `tool` + `arguments`：本样本对应的典型调用（`arguments` 是文档性质，回放器按需改写参数）。
- `response`：MCP `tools/call` 的 `structuredContent` 形状——`data` 为行数组（日历接口为对象），`metadata.truncated` 为截断标记（两侧适配层都会拒绝截断批次），分页接口带 `metadata.pagination.has_more`。
- `synthetic` 必须为 `true`；改成 `false` 前必须先替换为已授权的真实录制数据。

## 覆盖的接口

对照 `etf/docs/chart-interfaces.md` 的九图输入：

| 样本文件 | 接口 | 消费方 |
|---|---|---|
| `ft_v2_stock_candlesticks_batch.day.json` | 股票口径日K（ETF兼容） | Python `FTShareProvider`；Node 前收盘 |
| `ft_v2_etf_candlesticks_batch.day.json` | ETF 日K | Node 历史成交额 |
| `ft_v1_index_candlesticks.day.json` | 指数日K | Node 指数叠加 |
| `ft_v4_stock_realtime_minute_kline.json` | ETF 实时分钟 | Node 分钟图/雷达 |
| `ft_v4_index_realtime_minute_kline.json` | 指数实时分钟 | Node 分钟图指数 |
| `ft_v4_stock_realtime_day_kline.json` | ETF 当日行情 | Node 实时表格 |
| `ft_v2_etf_share.json` | ETF 份额 | Node 净申赎 |
| `ft_v2_etf_net_value.json` | ETF 净值 | Node 净申赎/折算 |
| `ft_v1_time_trading_calendar.json` | 交易日历 | Node 日期对齐 |

样本日期统一落在 demo 快照日历内（2026-02-25 至 2026-02-27），与 `etf/data/demo-seed.json` 可联合使用。
