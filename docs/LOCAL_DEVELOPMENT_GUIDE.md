# QuantPilot 本地开发与下一阶段执行手册

> 版本：2026-11-19；代码基准：GitHub `calvin-207/QuantPilot` 的 `main` 分支（查阅仓库文件，未在用户本机执行）。
> 目标：在本机独立跑通 ETF 演示看板、Python API、合法历史行情导入和时间周期聚合，再开始真实数据联调。

## 0. 先认识当前项目

QuantPilot 目前包括三部分：

1. `etf/`：Node.js 24+ 的 ETF 资金观察与异动雷达子系统，自有构建、HTTP 服务、演示快照及数据采集流程。不是 React/Vite 开发服务器。默认监听 `127.0.0.1:8080`。
2. `quant_core/`：Python 的多因子排序基础、统一证券与 K 线模型、SQLite 行情仓库、1m→15m/60m 聚合和数据源适配。
3. `backend/`：FastAPI 只读服务，包括 `/health`、`/api/v1/market/instruments`、`/api/v1/market/bars`，默认监听 `127.0.0.1:8000`。

**架构边界**：现阶段 `etf/` 页面与 Python SQLite 行情库并未直接接成统一页面；ETF 演示通过 Node 子系统内的快照显示，Python API 读取独立的 SQLite。不得认为 Python 导入 CSV 后，ETF 页面会自动刷新成该数据。

**现有能力**：ETF 演示与雷达、基础选股、标准化历史行情存储与查询。**尚未完成**：完整真实行情权限联调、历史时点股票池、完整策略/回测、券商实盘执行。

## 1. 本机环境检查

推荐 macOS / Linux；Windows 推荐 PowerShell + Python 虚拟环境，或 WSL2。以下命令主要以 macOS/Linux shell 为例。

```bash
git --version
python3 --version          # >= 3.11
node --version             # >= 24
npm --version
```

使用 Git、Python 3.11+、Node.js 24+；建议 VS Code + Python 扩展。当前 Python `pyproject.toml` 声明 FastAPI、Uvicorn、pytest、httpx；ETF `package.json` 声明 Node >=24，`wrangler` 为开发依赖。演示不需要 Docker、真实行情 Key、券商账号。

## 2. 克隆仓库、固定基线

```bash
git clone https://github.com/calvin-207/QuantPilot.git
cd QuantPilot
git checkout main
git pull --ff-only
git rev-parse --short HEAD
git status --short
```

将 `git rev-parse` 输出的 SHA 写入个人测试记录，避免后续多次更新造成环境漂移。建议首次只使用 `main` 验证，不直接修改它。

```bash
git switch -c dev/local-validation
```

如分支名已存在，改用 `git switch dev/local-validation`。

## 3. 第一条链路：ETF 演示页面

在仓库根目录：

```bash
cd etf
npm ci
cp .env.example .env
```

修改 `etf/.env` 为：

```dotenv
DATA_MODE=demo
ENABLE_RADAR=1
HOST=127.0.0.1
PORT=8080
```

演示模式不必填写 FtShare API Key。雷达开关属于**构建时**配置，更改后必须重新构建：

```bash
npm test
npm run build
npm run validate
npm start
```

浏览器访问：`http://127.0.0.1:8080`。另开终端检查：

```bash
curl -s http://127.0.0.1:8080/api/health
curl -s http://127.0.0.1:8080/api/board | head -c 500
curl -s http://127.0.0.1:8080/api/live | head -c 500
```

手工验收：品牌为 QuantPilot；首页图表能显示；切换分类、日期及深浅色模式不报错；雷达可见；`/api/health` 指示 `demo`；数据明确标注模拟，不当作真实行情。`npm run dev` 本质是 **build + start**，不是热更新式前端 HMR；前端改动后需重新构建和重启。

测试完成通过 Ctrl+C 停止。浏览器已有页面但资源未更新时，检查是否忘记 `npm run build`。

## 4. 第二条链路：Python 核心与 API

另开终端，从仓库根目录：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest -q
python tools/check_brand.py
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Windows PowerShell 的激活命令为 `.venv\Scripts\Activate.ps1`，Python 命令通常为 `py -3.11 -m venv .venv`。如果公司策略阻止 PowerShell 脚本，可使用 `.venv\Scripts\python.exe -m pytest -q` 等方式直接调用解释器。

另开终端：

```bash
curl http://127.0.0.1:8000/health
```

预期返回 `{"status":"ok","application":"QuantPilot"}`。文档接口位于 `http://127.0.0.1:8000/docs`。

**注意**：如果从未导入行情文件，`/api/v1/market/instruments` 预计返回 `503`，表示行情库未初始化；它不是服务启动失败。

## 5. 导入第一份本地 CSV（只验证格式和功能）

从仓库根目录创建 `.local/sample_bars.csv`，仅用于本地开发验证：

```bash
mkdir -p .local
cat > .local/sample_bars.csv <<'CSV'
symbol,timeframe,ts,open,high,low,close,volume,turnover,source,revision
600519.SH,1d,2026-11-17T15:00:00+08:00,10,11,9,10.5,100,1050,local-test,v1
600519.SH,1d,2026-11-18T15:00:00+08:00,10.5,12,10,11.5,120,1320,local-test,v1
CSV
python -m tools.import_market_csv .local/sample_bars.csv --db .local/market.sqlite3
```

这两个价格值为**合成测试值**，绝不代表贵州茅台真实价格或真实交易数据。请勿对外发布为市场行情。

查询：

```bash
curl -G 'http://127.0.0.1:8000/api/v1/market/instruments' --data-urlencode 'q=600519'
curl -G 'http://127.0.0.1:8000/api/v1/market/bars' \
  --data-urlencode 'symbol=600519.SH' \
  --data-urlencode 'timeframe=1d' \
  --data-urlencode 'start=2026-11-01T00:00:00+08:00' \
  --data-urlencode 'end=2026-11-30T23:59:59+08:00' \
  --data-urlencode 'source=local-test' \
  --data-urlencode 'revision=v1'
```

验收：返回两根日线；OHLC、成交量、时间与 `source` 一致；重复导入不会造成同一主键的重复记录（核实仓库的修订/幂等语义）。如果手动把 `QUANTPILOT_MARKET_DB` 改为其他路径，导入命令的 `--db` 也必须同步修改。

## 6. 1 分钟 → 15 / 60 分钟聚合验收

`tools/build_timeframes.py` 已实现聚合入口，**但本指南上一步只有两根日线，无法聚合分钟线**。先从已获授权的供应商取得至少一个完整交易日的标准化 `1m` CSV，再执行：

```bash
python -m tools.import_market_csv /path/to/authorized_1m.csv --db .local/market.sqlite3
python -m tools.build_timeframes \
  --db .local/market.sqlite3 \
  --symbol 600519.SH \
  --start '2026-11-17T09:30:00+08:00' \
  --end '2026-11-17T15:00:00+08:00' \
  --source licensed-source
```

上例日期、证券代码和 `source` 需替换成导入数据一致的值；1m CSV 使用与日线相同的列名，`timeframe=1m`。15/60 分钟只生成完整交易窗口的数据，不跨午休、不凭空填缺失分钟。**不要直接根据一天的 1m 数据推出 1 小时、15 分钟行情必然完整：先检查供应商时间戳是 bar 开始还是结束。**

## 7. 接入真实行情的正确顺序（P2.1）

当前 `quant_core/market/ftshare.py` 只有部分注入式适配，真实账户授权、分钟历史和证券元数据接口需要再联调。Node ETF 子系统的 FtShare 采集也需要独立授权。不要把 `etf/.env` 的 Key 当作 Python 行情 API 的统一配置，更不要把 Key 提交到 Git。

1. **先确定数据商**：可合法使用的范围、ETF/股票/指数覆盖、1m 历史深度、日线复权口径、调用频次、商业展示授权。
2. **验证少量证券**：任选 2 只股票、2 只 ETF、1 个指数；优先同步一小段日线和分钟线，而不是全 A 股一次性回填。
3. **规范化字段**：symbol、exchange、证券类型、交易日、时区、bar 结束时刻、OHLCV、成交额单位、复权方式、source、revision。
4. **做数据质量校验**：缺失交易日、停牌、无效 OHLC、重复主键、异常成交额、分钟条数和午休边界。
5. **先写 SQLite**：通过 `/api/v1/market/bars` 对照供应商原始记录；之后再评估 PostgreSQL/Parquet 及统一后端。
6. **核验 ETF 真实模式**：若使用 FtShare，先准备授权快照，`etf/.env` 配 `DATA_MODE=live`，后台独立采集，构建并验证页面。不要把模拟数据重命名为真实快照。

ETF 子系统的日度采集入口：`cd etf && npm run collect`，盘中采集入口：`node --env-file-if-exists=.env scripts/collect-live.mjs --watch`。**仅在完成授权、配置及历史数据核验之后执行**，避免错误/大量请求消耗配额。雷达的 60 日同进度基准需完整的既往交易日分钟样本；不完整时正确结果是“样本不足”，不是伪造数字。

## 8. 推荐的本地开发里程碑

| 阶段 | 主要工作 | 验收门槛 |
|---|---|---|
| M0 基线（优先） | 两套服务分别启动、运行 Python/Node 测试、展示演示 ETF 页面 | 健康检查通过、测试通过、品牌正确 |
| M1 数据落地 | 导入合法日线、1m，查阅 SQLite API，生成 15m/60m | 同一证券、多周期查询数据正确，缺失不造数 |
| M2 数据源联调 | Provider 接口、交易日历、增量补数、错误重试与审计 | 可重入、可核对原始响应、数据覆盖率可解释 |
| M3 证券与因子 | 历史时点证券池、技术指标、因子注册/评分 | 指标可复现，杜绝未来数据泄漏 |
| M4 回测与绩效 | T+1、涨跌停、停牌、手续费、基准比较 | 回测结果可重放、有测试样例 |
| M5 前端整合 | ETF/选股/策略/报告入口和统一后端 API | 同一证券编码和数据口径、端到端回归 |

**短期不要做**：券商自动下单、全市场实时数据大规模采集、没有授权的数据二次分发、过早重构成微服务或无明确必要的复杂数据库集群。

## 9. Codex 下一步执行任务说明（可直接粘贴）

```text
你现在在 QuantPilot 仓库本地工作。请先阅读 README.md、docs/P2_MARKET_DATA.md、docs/CODEX_TASKS.md、etf/README.md、etf/docs/data.md 和 pyproject.toml。

本轮目标：M0/M1 本地开发验收，不扩展交易策略、不连接券商、不删除版权声明。
1. 检查当前 git 分支和工作区，禁止覆盖未提交的本地修改。
2. 在本机核对 Python >=3.11、Node >=24；安装项目依赖。
3. 运行 pytest -q、python tools/check_brand.py；在 etf 执行 npm test、npm run build、npm run validate。
4. 启动 FastAPI 与 ETF Demo 服务，核验 /health、/api/health、/api/board 和浏览器页面。区分合成数据与真实数据。
5. 使用单独的合成测试 CSV 导入本地 SQLite，核验 /api/v1/market/instruments、/api/v1/market/bars。不要覆盖已有生产或授权数据。
6. 检查当前 README、运行文档与实际命令是否有差异；发现问题时提供最小修复补丁与回归测试。
7. 输出 docs/LOCAL_ACCEPTANCE_REPORT.md：环境版本、当前 commit SHA、命令、测试结果、截图位置、阻塞项、下一阶段 P2.1 的最小任务列表。
8. 任何提交使用中文 commit message；如需推送先说明变更；所有真实 API Key 和私有行情数据都不得入库。

完成标准：两条链路独立可启动，所有可运行自动测试通过，模拟数据查询正确，并明确列出真实数据尚未具备的权限与联调缺口。
```

## 10. 常见故障快速定位

| 问题 | 优先检查 |
|---|---|
| npm 命令报 Node 版本不支持 | `node -v`，必须 >=24；重新 `npm ci` |
| ETF 页面没雷达 | `.env` 里 `ENABLE_RADAR=1`，然后重新 `npm run build` |
| ETF 有图但无实时行情 | demo 是合成快照；live 需独立采集缓存，不靠页面调用数据商 |
| Python 8000 端口已占用 | 停止原进程，或换端口并同步 curl URL |
| `/api/v1/market/instruments` 报 503 | 先执行 CSV 导入；确认 DB 路径与进程工作目录一致 |
| `/bars` 返回空数组 | 核对 `symbol`、`timeframe`、`source`、`revision`、时间范围和时区 |
| 聚合生成 0 根 | 检查是否真正导入完整 `1m`，时间戳语义、午休、来源版本是否一致 |
| 前端修改不生效 | Node 子系统不是 HMR，重新构建 `dist`，重启 `npm start` |
| 提示数据不足 | 不强行补零或推断；查询供应商覆盖、停牌、交易日历 |

## 11. 验收记录（执行后填写）

- 日期 / 操作系统：
- `git rev-parse --short HEAD`：
- Python / Node / npm 版本：
- `pytest -q`：
- `npm test`：
- `npm run build` / `npm run validate`：
- ETF 地址与截图：
- Python 健康检查：
- 导入 CSV 行数 / API 返回行数：
- 真实行情供应商与授权状态：
- 当前阻塞项 / 下一个任务：

---

## 本文直接核对的源码与仓库文档

- https://github.com/calvin-207/QuantPilot/blob/main/README.md
- https://github.com/calvin-207/QuantPilot/blob/main/pyproject.toml
- https://github.com/calvin-207/QuantPilot/blob/main/docs/P2_MARKET_DATA.md
- https://github.com/calvin-207/QuantPilot/blob/main/backend/app/market_api.py
- https://github.com/calvin-207/QuantPilot/blob/main/tools/import_market_csv.py
- https://github.com/calvin-207/QuantPilot/blob/main/tools/build_timeframes.py
- https://github.com/calvin-207/QuantPilot/blob/main/etf/package.json
- https://github.com/calvin-207/QuantPilot/blob/main/etf/docs/data.md
- https://github.com/calvin-207/QuantPilot/blob/main/etf/docs/deployment.md

本文件提供源码审阅后的可执行步骤；不代表已在用户本机执行安装、联网采集、浏览器测试或读取真实行情。
