# QuantPilot architecture

Current implementation:
- quant_core: framework-independent, deterministic cross-sectional factor selection
- backend: FastAPI health endpoint
- tests: pure selection unit tests

Planned modules:
- Market data provider adapters and versioned point-in-time storage
- Technical indicators and multi-factor registry
- A-share selection runs, strategy versions, schedule and signals
- Event-driven backtest with T+1, suspension, price limits and transaction costs
- Portfolio analytics and web UI
- Optional upstream ETF observatory after first-import brand and license checks

Research and historical backtesting must use the same selection implementation. Market data entitlements and historical completeness must be verified before real results are displayed.
