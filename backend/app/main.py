"""QuantPilot API：统一行情只读接口，后台采集与回测将在后续阶段加入。"""
from fastapi import FastAPI
from .market_api import router as market_router

app = FastAPI(title="QuantPilot", version="0.2.0")
app.include_router(market_router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "application": "QuantPilot"}
