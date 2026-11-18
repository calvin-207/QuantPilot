# QuantPilot · 量化领航

Open-source quantitative research platform for A-share market monitoring, technical and multifactor stock selection, strategy signals and historical backtesting.

> **Current status:** an initial Python engineering scaffold. No live market data, upstream ETF browser UI, historical backtest engine or brokerage trading is included yet.

## Current functionality

- Framework-independent deterministic factor ranking in `quant_core/selection.py`
- Minimal FastAPI application with `GET /health`
- Unit tests and GitHub Actions
- First-import upstream UI brand and license compliance gate

## Quick start

Requires Python 3.11+.

```bash
python -m pip install -e '.[dev]'
pytest -q
uvicorn backend.app.main:app --reload
```

## Roadmap

1. Validate data-provider entitlements and historical availability.
2. Import and rebrand the upstream ETF observatory **before its first appearance in the repository**.
3. Add point-in-time stock pools, technical indicators and multifactor screening.
4. Add selection tasks, historical replay, A-share-compliant backtests and performance reporting.
5. Add research UI and scheduled reports.

Read [architecture](docs/ARCHITECTURE.md), [Codex tasks](docs/CODEX_TASKS.md) and the [first-import gate](docs/FIRST_PUSH_GATE.md).

## Upstream attribution and legal notices

QuantPilot is inspired by [FtShare_fincase](https://github.com/FTShare-Lab/FtShare_fincase), released under MIT. The original copyright and permission notice is preserved at [LICENSES/FTSHARE_FINCASE_LICENSE](LICENSES/FTSHARE_FINCASE_LICENSE), and the new original code has its own MIT [LICENSE](LICENSE). Copied ECharts assets will retain their separate Apache-2.0 LICENSE and NOTICE.

Rebranding the product interface does not remove attribution obligations, provider identification or market-data license requirements. See [upstream documentation](docs/UPSTREAM.md).

No real-money trading is supported; financial research results are not investment recommendations.
