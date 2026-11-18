# QuantPilot · 量化领航

[简体中文](#简体中文) | [English](#english)

## 简体中文

**QuantPilot（量化领航）** 是面向 A 股市场的开源量化研究平台，目标是建立从行情观察、技术指标与多因子自动选股、策略信号、历史回测到组合绩效分析的完整研究闭环。

> **当前阶段：工程基础骨架。** 已有基础选股计算模块、FastAPI 健康检查及单元测试。**已将 ETF 资金观察、异动雷达、前端界面与演示数据迁入 `etf/` 子目录**，并完成 QuantPilot 品牌替换。真实行情仍需合法数据权限和密钥；**尚未**实现完整历史回测或连接券商交易。请勿将项目现阶段结果视为可执行投资建议。

### 规划功能

- **行情数据中心**：A 股、ETF、指数的日线和分钟线采集、缓存、版本管理及数据质量校验。
- **个股与 ETF 观察**：自选股、K 线、成交异动雷达、ETF 资金观察。
- **统一自动选股**：技术指标筛选、多因子评分、股票池管理和定时运行。
- **策略信号中心**：规则、参数、版本、买卖候选信号与原因追溯。
- **历史回测与绩效**：按历史时点重建股票池，模拟 A 股交易约束、手续费和调仓，输出收益、回撤与基准比较。
- **自动化研究**：定时更新行情、执行选股任务、归档结果并生成报告。

### 已实现

- `quant_core/selection.py`：独立于 Web 框架的确定性多因子排名基础函数。
- `backend/app/main.py`：FastAPI 应用与 `GET /health` 接口。
- `tests/test_selection.py`：基础选股单元测试。
- `.github/workflows/python.yml`：Python 测试工作流。
- `etf/`：已迁移 ETF 资金观察、成交异动雷达、原生前端、演示数据、采集脚本和回归测试。
- `tools/check_brand.py`：检查 ETF 页面已知旧品牌和推广入口。
- `.github/workflows/etf-ci.yml`：ETF 品牌检查、原回归测试与构建验收。

### ETF 资金观察模块（演示模式）

要求 Node.js 24+：

```bash
cd etf
npm ci
npm run build
npm test
npm start
```

默认访问 `http://127.0.0.1:8080`；启用雷达需设置 `ENABLE_RADAR=1` 并重新构建。演示数据均为合成数据，真实行情需通过独立配置的数据服务采集。

### Python 量化核心快速启动

要求 Python 3.11 或以上：

```bash
python -m pip install -e '.[dev]'
pytest -q
uvicorn backend.app.main:app --reload
```

健康检查：`http://127.0.0.1:8000/health`。

### 开发计划

1. 核实行情供应商接口权限、数据覆盖和使用成本。
2. ✅ 迁移上游 ETF 界面并在进入仓库前更换 QuantPilot 品牌；持续进行构建与回归验证。
3. 建设历史时点证券池、因子注册中心与技术指标 / 多因子统一选股。
4. 增加选股任务、信号归档、历史回放与 A 股交易规则回测。
5. 完善研究前端、绩效报告、定时任务和部署测试。

相关文档：[架构设计](docs/ARCHITECTURE.md) · [Codex 开发任务](docs/CODEX_TASKS.md) · [品牌迁移验收](docs/FIRST_PUSH_GATE.md)。

### 开源与数据声明

本项目参考 [FtShare_fincase](https://github.com/FTShare-Lab/FtShare_fincase)（MIT 许可）。上游原始版权与许可声明保留于 [LICENSES/FTSHARE_FINCASE_LICENSE](LICENSES/FTSHARE_FINCASE_LICENSE)；QuantPilot 新增原创代码使用仓库根目录的 [MIT LICENSE](LICENSE)。如引入 ECharts 分发文件，还须保留其 Apache-2.0 许可及 NOTICE。

替换旧项目的 Logo、标题和商业推广内容，**不代表可以删除被复用代码所要求的版权声明**，也不等于获得 FtShare 数据服务、API 密钥或第三方行情数据的授权。详情见 [上游来源说明](docs/UPSTREAM.md)。

当前项目不提供实盘下单功能；相关功能仅用于技术研究，不构成投资建议。

---

## English

**QuantPilot** is an open-source quantitative research platform for A-share market monitoring, technical and multi-factor stock selection, strategy signals, historical backtesting, and portfolio analytics.

> **Status: early engineering scaffold.** The current repository includes a minimal deterministic factor ranking core, FastAPI health endpoint, and unit tests. The upstream ETF observatory, including its rebranded user interface and synthetic demonstration data, is now under `etf/`. It does **not** yet include a configured live market-data feed, a complete backtesting engine, or brokerage execution.

### Planned features

- Market data ingestion, daily/minute bars, quality checks and versioned storage.
- Stock and ETF observation, charts and volume anomaly radar.
- Configurable technical-rule screening and multi-factor ranking.
- Strategy signals, versioning and scheduled selection.
- Point-in-time historical replay, A-share-aware backtests and performance reports.

### Implemented so far

- `quant_core/selection.py`: deterministic factor ranking logic.
- `backend/app/main.py`: minimal FastAPI service with `GET /health`.
- `tests/test_selection.py`: unit tests.
- `.github/workflows/python.yml`: Python CI.
- `tools/check_brand.py`: known upstream promotional UI pattern gate.
- `etf/`: migrated ETF observatory, radar, dashboard, collectors, synthetic fixtures and tests.

### ETF demo

Node.js 24+:

```bash
cd etf
npm ci
npm run build
npm test
npm start
```

### Python core quick start

Python 3.11+:

```bash
python -m pip install -e '.[dev]'
pytest -q
uvicorn backend.app.main:app --reload
```

See the [architecture](docs/ARCHITECTURE.md), [Codex tasks](docs/CODEX_TASKS.md), and [upstream UI first-import gate](docs/FIRST_PUSH_GATE.md).

### Licenses and attribution

QuantPilot references the MIT-licensed [FtShare_fincase](https://github.com/FTShare-Lab/FtShare_fincase). The original upstream MIT copyright notice is retained at [LICENSES/FTSHARE_FINCASE_LICENSE](LICENSES/FTSHARE_FINCASE_LICENSE); original QuantPilot code uses the repository's [MIT LICENSE](LICENSE). Imported third-party libraries require their own applicable notices.

Brand replacement does not waive copyright obligations or confer rights to hosted data services, API credentials, or external market datasets. See [upstream notes](docs/UPSTREAM.md).

No live brokerage trading is supported. The project is for research, not investment advice.
