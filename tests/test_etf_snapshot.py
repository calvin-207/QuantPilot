"""阶段1测试：Python 生成的 etf demo 快照必须通过两侧契约门禁。

- Python 侧：共享 JSON Schema + seed.mjs 规则的 Python 镜像（validate_snapshot）
- Node 侧：直接调用权威校验器 etf/scripts/lib/seed.mjs 的 validateSeed
"""
from datetime import date
from pathlib import Path
import json
import shutil
import subprocess

import pytest

from tools.build_etf_snapshot import BASKET, build_snapshot, load_universe, validate_snapshot

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def snapshot() -> dict:
    universe = load_universe(ROOT / "etf" / "config" / "universe.json")
    seed = build_snapshot(universe, date(2025, 10, 1), date(2026, 2, 27),
                          "2026-03-01T00:00:00.000Z")
    validate_snapshot(seed)
    return seed


def test_python_validation_gates_pass(snapshot):
    """build_snapshot 产物通过共享 schema 与 Python 镜像规则（fixture 已断言）。"""
    assert snapshot["provider"] == "Demo"
    assert snapshot["schema"] == 1


def test_generation_is_deterministic():
    universe = load_universe(ROOT / "etf" / "config" / "universe.json")
    args = (universe, date(2025, 10, 1), date(2026, 2, 27), "2026-03-01T00:00:00.000Z")
    first = json.dumps(build_snapshot(*args), sort_keys=True)
    second = json.dumps(build_snapshot(*args), sort_keys=True)
    assert first == second


def test_demo_service_consumption_contract(snapshot):
    """createDemoService 直接消费的字段必须齐备（demo.js 的读取路径）。"""
    dates = snapshot["history"]["dates"]
    as_of = snapshot["demo"]["as_of"]
    assert as_of == dates[-1]
    assert as_of in snapshot["minutes"], "demo.live 需要观察日的分钟样本"
    for day in dates:
        flows = snapshot["demo"]["fund_flows"][day]
        assert all(symbol in flows for symbol in BASKET), f"{day} 缺少核心成员日度流量"
    assert [f["symbol"] for f in snapshot["universe"]] == BASKET, "表格顺序即 BASKET 顺序"
    assert all(f["name"] for f in snapshot["universe"])


def test_corrupted_snapshot_is_rejected(snapshot):
    broken = json.loads(json.dumps(snapshot))
    broken["broad"]["total"][3] = broken["broad"]["total"][3] + 5.0
    with pytest.raises(ValueError, match="不对账"):
        validate_snapshot(broken)

    gapped = json.loads(json.dumps(snapshot))
    day = gapped["demo"]["as_of"]
    gapped["minutes"][day]["bars"][10] = None
    with pytest.raises(ValueError, match="累计"):
        validate_snapshot(gapped)


@pytest.mark.skipif(shutil.which("node") is None, reason="需要 Node 运行时")
def test_node_authoritative_validator_accepts(snapshot, tmp_path):
    """权威门禁：etf/scripts/lib/seed.mjs 的 validateSeed 必须接受 Python 产物。"""
    target = tmp_path / "python-demo-seed.json"
    with target.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False)
    script = (
        "import { readFileSync } from 'node:fs';\n"
        f"import {{ validateSeed }} from '{(ROOT / 'etf' / 'scripts' / 'lib' / 'seed.mjs').as_uri()}';\n"
        "validateSeed(JSON.parse(readFileSync(process.argv[1], 'utf8')), 'demo');\n"
        "console.log('seed-ok');\n"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script, str(target)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "seed-ok" in result.stdout
