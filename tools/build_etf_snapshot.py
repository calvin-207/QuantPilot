"""阶段1：用 Python 确定性生成 etf 看板 demo 快照（schema:1）。

产出同时通过两道契约门禁后才写盘：
1. 共享 JSON Schema：contracts/schemas/etf-snapshot-v1.schema.json
2. seed.mjs 跨字段规则的 Python 镜像（分类合计对账、覆盖数关系、分钟累计等）

数据全部为程序合成的演示值，provider 如实标记 Demo；权威运行时校验仍是
etf/scripts/lib/seed.mjs（tests/test_etf_snapshot.py 会再跑一次 Node 侧校验）。
写成 etf/data/demo-seed.json 后执行 npm run build 即可进入 demo 模式。
"""
from argparse import ArgumentParser
from datetime import date, timedelta
from pathlib import Path
import json
import math
import re

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

# —— 契约常量（镜像自 etf/src/server/model.js 与共享 schema，改动须两侧同步）——
CATEGORIES = ['沪深300', '中证1000', '中证500', '科创50', '中证A500', '创业板指',
              '上证50', '其他宽基', '创业板50', '双创50', '中证2000', '国证2000']
COLORS = ['#d93630', '#e8862e', '#f0b429', '#4c7bf3', '#0aa06e', '#8e44ad',
          '#16a085', '#c0392b', '#2980b9', '#7f8c8d', '#27ae60', '#d35400']
BASKET = ['510310.SH', '588000.SH', '159915.SZ', '510300.SH', '563360.SH',
          '159352.SZ', '512100.SH', '159338.SZ', '510500.SH', '159949.SZ',
          '588080.SH', '510050.SH', '510210.SH', '159845.SZ', '159952.SZ',
          '159361.SZ', '512050.SH', '159633.SZ', '560010.SH', '159919.SZ']
FORMULA = 'exchange_aligned_shares_verified_events_v3'
FLOW_POLICY = 'verified_events_public_backfill_v3'


def minute_slots() -> list[str]:
    """常规交易日分钟槽位：上午 09:30–11:30、下午 13:01–15:00，共 241 个。"""
    slots = [f"{t // 60:02d}:{t % 60:02d}" for t in range(9 * 60 + 30, 11 * 60 + 31)]
    slots += [f"{t // 60:02d}:{t % 60:02d}" for t in range(13 * 60 + 1, 15 * 60 + 1)]
    return slots


SLOTS = minute_slots()
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SYMBOL = re.compile(r"^\d{6}\.(SH|SZ)$")
CREDENTIAL = re.compile(r"ftshare_sk_[A-Za-z0-9_-]{20,}")


def r6(x: float) -> float:
    return float(f"{x:.6f}")


def weekdays(start: date, end: date) -> list[str]:
    """升序唯一工作日（与 Node 生成器一致，不含节假日修正）。"""
    days, cursor = [], start
    while cursor <= end:
        if cursor.weekday() < 5:
            days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return days


def load_universe(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        configured = json.load(f)["funds"]
    by_symbol = {fund["symbol"]: fund for fund in configured}
    missing = [s for s in BASKET if s not in by_symbol]
    if missing:
        raise ValueError(f"universe 缺少核心篮子成员: {missing}")
    return [by_symbol[s] for s in BASKET]


def build_snapshot(universe: list[dict], start: date, end: date, built_at: str) -> dict:
    calendar = weekdays(start, end)
    if len(calendar) < 2:
        raise ValueError("日期区间至少需要两个交易日")
    dates = calendar[1:]
    as_of = dates[-1]

    fund_flows, series, total = {}, {c: [] for c in CATEGORIES}, []
    for i, day in enumerate(dates):
        event = i % 13 == 0
        daily = {
            fund["symbol"]: r6((8.5 if event else 1.6) * math.sin(i / 7 + 0.4)
                               + 1.05 * math.cos(i / 5 + j / 6))
            for j, fund in enumerate(universe)
        }
        fund_flows[day] = daily
        for c in CATEGORIES:
            series[c].append(sum(daily[f["symbol"]] for f in universe if f["bucket"] == c))
        total.append(sum(series[c][i] for c in CATEGORIES))

    minutes = {}
    for i, day in enumerate(dates):
        scale = 1.55 if total[i] > 100 else 0.7 + 0.2 * (1 + math.sin(i / 3))
        bars, running, cumulative = [], 0.0, []
        for j in range(len(SLOTS)):
            value = r6(scale * (1.1 + 6.5 * math.exp(-j / 12)
                                + 3.5 * math.exp(-(240 - j) / 9) + 0.14 * math.sin(j / 8)))
            bars.append(value)
            running += value
            cumulative.append(running)
        minutes[day] = {"bars": bars, "cumulative": cumulative}

    coverage = {}
    for c in CATEGORIES:
        n = sum(1 for f in universe if f["bucket"] == c)
        coverage[c] = {"valid": [n] * len(dates), "expected": [n] * len(dates)}

    return {
        "schema": 1, "provider": "Demo", "sources": ["Synthetic examples"],
        "built_at": built_at, "formula": FORMULA, "flow_policy": FLOW_POLICY,
        "demo": {
            "as_of": as_of,
            "notice": "All market values and calendar entries are synthetic (Python generator). ETF names/codes are identifiers only.",
            "fund_flows": fund_flows,
        },
        "universe_policy": {"eligibility": "Current configured members; synthetic example only."},
        "universe": universe, "categories": CATEGORIES, "colors": COLORS,
        "calendar": calendar,
        "history": {
            "dates": dates,
            "amount": [minutes[d]["cumulative"][-1] for d in dates],
            "idx": [3150 + 2.2 * i + 88 * math.sin(i / 10) for i in range(len(dates))],
            "netflow": total,
            "flow_coverage": [len(universe)] * len(dates),
            "flow_expected": [len(universe)] * len(dates),
        },
        "broad": {"dates": dates, "cats": CATEGORIES, "colors": COLORS,
                  "total": total, "issues": {}, "series": series, "coverage": coverage},
        "minutes": minutes,
        "latest_flow_date": as_of, "latest_market_date": as_of,
        "minute_slots": SLOTS,
        "source_audit": {"provider": "Demo", "generator": "tools/build_etf_snapshot.py"},
    }


def validate_snapshot(seed: dict) -> None:
    """seed.mjs 跨字段规则的 Python 镜像；违反任何一条都拒绝写盘。"""
    problems = []

    if seed["schema"] != 1 or seed["provider"] != "Demo" or seed["formula"] != FORMULA:
        problems.append("schema/provider/formula 常量不符")
    if seed["categories"] != CATEGORIES or seed["minute_slots"] != SLOTS:
        problems.append("分类表或分钟槽位与契约常量不符")

    universe = seed["universe"]
    symbols = [f["symbol"] for f in universe]
    if len(universe) < 20 or len(set(symbols)) != len(symbols):
        problems.append("universe 不足20或存在重复")
    core = [f for f in universe if f["is_core_basket"]]
    if len(core) != 20 or any(s not in symbols for s in BASKET):
        problems.append("核心篮子必须恰好20只且全部在场")
    for fund in universe:
        if not SYMBOL.fullmatch(fund["symbol"]) or fund["bucket"] not in CATEGORIES:
            problems.append(f"成员描述不合法: {fund['symbol']}")
        if not ISO_DATE.fullmatch(fund["inception_date"]) or not ISO_DATE.fullmatch(fund["listed_date"]):
            problems.append(f"成立/上市日期不合法: {fund['symbol']}")

    def check_dates(values, label):
        if not values or any(not ISO_DATE.fullmatch(d) for d in values) or values != sorted(set(values)):
            problems.append(f"{label} 必须为升序唯一ISO日期")

    check_dates(seed["calendar"], "calendar")
    history, broad = seed["history"], seed["broad"]
    check_dates(history["dates"], "history.dates")
    check_dates(broad["dates"], "broad.dates")
    n = len(history["dates"])
    for key in ("amount", "idx", "netflow", "flow_coverage", "flow_expected"):
        if len(history[key]) != n:
            problems.append(f"history.{key} 长度与 dates 不一致")
    if broad["cats"] != CATEGORIES:
        problems.append("broad.cats 与契约常量不符")
    if len(broad["total"]) != len(broad["dates"]):
        problems.append("broad.total 长度与 dates 不一致")
    for c in CATEGORIES:
        if len(broad["series"][c]) != len(broad["dates"]):
            problems.append(f"broad.series[{c}] 长度不一致")
        cov = broad["coverage"][c]
        for key in ("valid", "expected"):
            if len(cov[key]) != len(broad["dates"]) or any(
                    not isinstance(v, int) or v < 0 for v in cov[key]):
                problems.append(f"coverage[{c}].{key} 不合法")
        for i in range(len(broad["dates"])):
            if cov["valid"][i] > cov["expected"][i]:
                problems.append(f"coverage[{c}] 第{i}日覆盖数超过预期")
            if (broad["series"][c][i] is not None) != (cov["valid"][i] == cov["expected"][i]):
                problems.append(f"series[{c}] 第{i}日与覆盖数关系不符")
    for i in range(len(broad["dates"])):
        values = [broad["series"][c][i] for c in CATEGORIES]
        if any(v is None for v in values):
            if broad["total"][i] is not None:
                problems.append(f"broad.total 第{i}日不完整应为null")
        elif abs(sum(values) - broad["total"][i]) >= 1e-6:
            problems.append(f"broad.total 第{i}日分类合计不对账")
    if seed["latest_flow_date"] not in broad["dates"]:
        problems.append("latest_flow_date 必须属于 broad.dates")

    for day, minute in seed["minutes"].items():
        for key in ("bars", "cumulative"):
            if len(minute[key]) != len(SLOTS):
                problems.append(f"minutes[{day}].{key} 槽位数不符")
        running, missing = 0.0, False
        for i, v in enumerate(minute["bars"]):
            if v is None:
                missing = True
            if missing:
                if minute["cumulative"][i] is not None:
                    problems.append(f"minutes[{day}] 缺口后累计必须为null")
            else:
                running += v
                if minute["cumulative"][i] is None or abs(running - minute["cumulative"][i]) >= 1e-6:
                    problems.append(f"minutes[{day}] 第{i}槽累计不对账")
    if CREDENTIAL.search(json.dumps(seed, ensure_ascii=False)):
        problems.append("快照中检测到疑似凭证")

    schema_path = ROOT / "contracts" / "schemas" / "etf-snapshot-v1.schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        errors = sorted(Draft202012Validator(json.load(f)).iter_errors(seed),
                        key=lambda e: list(e.absolute_path))
    problems += [f"schema {list(e.absolute_path)}: {e.message}" for e in errors]

    if problems:
        raise ValueError("快照未通过契约校验:\n" + "\n".join(problems))


def main():
    parser = ArgumentParser(description="生成 etf 看板 demo 快照（确定性合成数据）")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--universe", type=Path,
                        default=ROOT / "etf" / "config" / "universe.json")
    parser.add_argument("--start", type=date.fromisoformat, default=date(2025, 10, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 2, 27))
    parser.add_argument("--built-at", default="2026-03-01T00:00:00.000Z",
                        help="固定生成时间戳，保证确定性；可用 --built-at 覆盖")
    args = parser.parse_args()

    universe = load_universe(args.universe)
    seed = build_snapshot(universe, args.start, args.end, args.built_at)
    validate_snapshot(seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(seed, f, ensure_ascii=False, separators=(",", ":"))  # noqa: E501
        f.write("\n")
    print(f"生成完成：{len(seed['history']['dates'])} 个合成交易日，20 只核心ETF；"
          f"输出={args.output}；provider=Demo（合成数据）")


if __name__ == "__main__":
    main()
