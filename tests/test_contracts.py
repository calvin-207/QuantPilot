"""阶段0跨语言契约测试：快照schema、FtShare样本外壳与适配层回放。

事实源与镜像关系见 contracts/README.md。demo-seed.json 由 Node 确定性再生成，
本文件用它校验共享 schema，Node 侧形状漂移会在此立即暴露。
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import json

import pytest
from jsonschema import Draft202012Validator

from quant_core.market.ftshare import FTShareProvider
from quant_core.market.provider import ProviderUnavailable

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
CN = timezone(timedelta(hours=8))

FIXTURE_ENVELOPE = {
    "type": "object",
    "required": ["tool", "synthetic", "arguments", "response"],
    "properties": {
        "tool": {"type": "string", "pattern": "^ft_v[0-9]_"},
        "synthetic": {"const": True},
        "arguments": {"type": "object"},
        "response": {
            "type": "object",
            "required": ["data"],
            "properties": {
                "data": {},
                "metadata": {"type": "object"},
            },
        },
        "$comment": {"type": "string"},
    },
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validator(schema_path: Path) -> Draft202012Validator:
    return Draft202012Validator(load_json(schema_path))


def test_demo_seed_matches_shared_snapshot_schema():
    """Node 确定性生成的 demo 快照必须通过共享 JSON Schema。"""
    seed = load_json(ROOT / "etf" / "data" / "demo-seed.json")
    errors = sorted(validator(CONTRACTS / "schemas" / "etf-snapshot-v1.schema.json")
                    .iter_errors(seed), key=lambda e: list(e.absolute_path))
    assert not errors, "\n".join(
        f"{list(e.absolute_path)}: {e.message}" for e in errors
    )


def test_ftshare_fixtures_conform_to_envelope():
    """全部样本必须是显式合成、带接口名与标准响应外壳。"""
    fixture_dir = CONTRACTS / "fixtures" / "ftshare"
    files = sorted(fixture_dir.glob("*.json"))
    assert files, "FtShare 样本目录为空"
    envelope = Draft202012Validator(FIXTURE_ENVELOPE)
    for path in files:
        fixture = load_json(path)
        errors = list(envelope.iter_errors(fixture))
        assert not errors, f"{path.name}: " + "; ".join(e.message for e in errors)


def test_ftshare_provider_replays_day_kline_fixture():
    """注入 call_tool 回放日K样本：FTShareProvider 应产出排序正确的 Bar。"""
    fixture = load_json(CONTRACTS / "fixtures" / "ftshare"
                        / "ft_v2_stock_candlesticks_batch.day.json")

    def call_tool(name: str, arguments: dict) -> dict:
        assert name == fixture["tool"]
        assert arguments["symbols"] == ["510300.SH"]
        return deepcopy(fixture["response"])

    provider = FTShareProvider(call_tool)
    bars = provider.fetch_bars(
        "510300.SH", "1d",
        datetime(2026, 2, 25, tzinfo=CN), datetime(2026, 2, 28, tzinfo=CN),
    )
    assert [b.ts for b in bars] == sorted(b.ts for b in bars)
    assert len(bars) == 3
    assert all(b.symbol == "510300.SH" and b.source == "FTShare" for b in bars)
    assert bars[0].close == Decimal("1.08")
    assert bars[-1].close == Decimal("1.14")


def test_ftshare_provider_rejects_truncated_batch():
    """契约：截断批次不允许进入入库链路。"""
    fixture = load_json(CONTRACTS / "fixtures" / "ftshare"
                        / "ft_v2_stock_candlesticks_batch.day.json")
    response = deepcopy(fixture["response"])
    response["metadata"]["truncated"] = True

    provider = FTShareProvider(lambda name, args: deepcopy(response))
    with pytest.raises(ProviderUnavailable):
        provider.fetch_bars(
            "510300.SH", "1d",
            datetime(2026, 2, 25, tzinfo=CN), datetime(2026, 2, 28, tzinfo=CN),
        )
