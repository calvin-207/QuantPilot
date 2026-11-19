# QuantPilot ETF 看板只读 API 契约（v1）

事实源：`etf/src/gateway.js`（路由与错误映射）、`etf/src/server/demo.js`（demo 响应）、`etf/src/server/read-only.js`（live 发布语义）、`etf/src/server/service.js`（live 采集语义）。本文件是跨语言镜像契约；修改路由或响应形状必须同步更新本文并升版本号。

通用规则：

- 仅 `GET`/`HEAD`；查询串长度 ≤ 256；所有响应 `content-type: application/json; charset=utf-8`。
- 响应携带 `x-data-provider` 头（取 `provider` 字段，缺省 `FTShare`）。
- 错误体统一为 `{"error": string, "code"?: string}`；错误码见文末表。
- 网页端只读已发布快照与共享缓存，任何接口都不触发 FtShare 采集，也没有任意 URL/工具透传。

## GET /api/board

返回完整快照（`contracts/schemas/etf-snapshot-v1.schema.json`），live 模式额外附加 `update_policy` 字段。live 响应 `cache-control: public, max-age=60`。

## GET /api/live

| 字段 | 类型 | 说明 |
|---|---|---|
| `provider` | string | `Demo` 或 `FTShare` |
| `formula` | string | 与快照一致 |
| `fetched_at` | ISO datetime | |
| `date` | `YYYY-MM-DD` | 由指数分钟（或日K）推断的交易日 |
| `slots` | string[241] | 同快照 `minute_slots` |
| `bars` | (number\|null)[241] | 篮子分钟成交额（亿元） |
| `cumulative` | (number\|null)[241] | 缺口即停的累计值 |
| `coverage` | integer[241] | 每分钟有行情的成员数 |
| `closes` | (number\|null)[241] | 上证指数分钟收盘 |
| `pre_close` | number\|null | 指数前收盘 |
| `amount` | number\|null | 全篮子当日累计成交额 |
| `last_complete_minute` | string\|null | 最后一个 20/20 覆盖的槽位 |
| `expected_flow_date` | string\|null | 预期最新资金归属日 |
| `trading_dates` | string[] | 交易日历 |
| `daily_batches` | integer | demo=批次总数；live 只读=0 |
| `table` | object[20] | `{symbol, code, name, price, amount, pct}` 逐ETF最新行情 |
| `warnings` | object[] | 组件级降级 `{component, code, retry_after_ms}` |
| `quote_interfaces` | string[] | live 实际使用的接口名（demo 无此字段） |
| `cache` | object | live 只读模式附加 `{mode, collected_at, checked_at, stale, last_error, refresh_seconds}` |

`cache-control`：live `public, max-age=15`。demo 由 `createDemoService` 提供形状兼容子集。

## GET /api/history

`{provider, fetched_at?, rows: [{date, amount: number|null, idx: number|null}]}`，按日期升序；`amount` 为核心篮子成交额（亿元），覆盖不全为 `null`。

## GET /api/cumulative?date=YYYY-MM-DD

`date` 必须是 `YYYY-MM-DD` 且已归档。`{provider, date, slots?, bars, cumulative, coverage}`（`slots` 仅 demo 模式提供）。未归档返回 404 `not_archived`。

## GET /api/daily?batch=N

仅 demo 模式。`batch` 为 0–2 位数字。`{provider, dates, funds: [{symbol, days: {date: {flow}}}]}`。live 模式一律 410 `visitor_collection_disabled`。

## GET /api/health

`{provider, mode: "demo"|"live", sources, configured, history_built_at, formula, flow_policy, funds, cloud_update, update_policy}`。

## 错误码

| HTTP | code | 场景 |
|---|---|---|
| 400 | — | 查询参数无效（`/api/daily` 非 1–2 位数字、`/api/cumulative` 日期格式错） |
| 404 | `not_archived` | 请求的分钟日期尚未归档 |
| 410 | `visitor_collection_disabled` | live 模式访问 `/api/daily` |
| 429 | `rate_limited` | 请求频率超限（`retry-after: 60`） |
| 503 | `cache_not_ready` | 后台行情尚未就绪，历史图表仍可用 |
| 503 | `not_configured` / `quota_exceeded` / `truncated` / `upstream_error` | 上游数据暂不可用 |
