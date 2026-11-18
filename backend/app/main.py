"""QuantPilot API (scaffold; no live quotes or backtesting yet)."""
from fastapi import FastAPI

app = FastAPI(title="QuantPilot", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "application": "QuantPilot"}
