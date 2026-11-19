# QuantPilot 跨语言契约（阶段 0）

本目录是 `etf/`（Node）与 Python（`quant_core` + `backend`）两个子系统的**共享数据契约层**。长期方向：Python 成为数据与计算中枢，etf 前端作为唯一展示层存活；合并发生在这一层，而不是再造一个前端。

## 内容

| 文件 | 内容 | 机器可校验 |
|---|---|---|
| `schemas/etf-snapshot-v1.schema.json` | 已发布快照（`schema: 1`）的 JSON Schema（draft 2020-12） | 是（`tests/test_contracts.py` 用 jsonschema 校验 `etf/data/demo-seed.json`） |
| `etf-api-v1.md` | 看板只读 API 的响应形状、错误码、缓存策略 | 否（形状文档；字段事实源为 `etf/src/gateway.js`） |
| `fixtures/ftshare/` | FtShare 工具响应的合成样本（全部为演示数值） | 是（外壳格式由 `tests/test_contracts.py` 校验；日K样本由 `FTShareProvider` 回放） |

## 事实源与镜像关系

运行时权威是 Node 侧实现；schema 是跨语言镜像，改任何一侧必须同步另一侧：

- 快照结构与跨字段规则（数组等长、分类合计对账、分钟累计对账、覆盖数关系、凭证泄漏检查）的权威实现：`etf/scripts/lib/seed.mjs`。JSON Schema 只表达单字段形状与常量（分类表、241 个分钟槽位、公式版本），**不重复实现对账逻辑**。
- API 响应形状权威：`etf/src/gateway.js` + `etf/src/server/{demo,read-only,service}.js`。
- FtShare 响应外壳权威：`etf/src/server/ftshare.js`（`structuredContent` 解析、截断与分页语义）。

漂移检测机制：`etf/data/demo-seed.json` 由 `npm run demo:generate` 确定性再生成，Python 契约测试每次都会用它校验 schema——Node 侧一旦改动快照形状而未升契约版本，Python 测试立即失败。

## 版本规则

- 快照内 `schema` 字段当前为 `1`；破坏性变更（删字段、改语义、改常量）必须升为 `2` 并同步 `seed.mjs` 与本 schema。
- `formula` / `flow_policy` 是计算口径版本，与快照结构版本独立演进。
- 契约文件本身以 Git 变更为准；修改任一契约文件必须在提交说明中列出两侧同步点。

## 诚实性规则

- 合成数据必须标记 `provider: "Demo"` / `synthetic: true`，不得标记或导入为真实来源（对应 `etf` 的导入校验：模拟数据不能按真实数据导入）。
- fixtures 中 `synthetic` 为 `true` 的文件禁止包含真实行情数值；替换为录制数据时须连同授权说明一起变更。
