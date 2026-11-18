"""Pure deterministic cross-sectional factor ranking; no data loading or trading."""
from dataclasses import dataclass
from typing import Mapping
import math

@dataclass(frozen=True)
class FactorWeight:
    name: str
    weight: float
    higher_is_better: bool = True

@dataclass(frozen=True)
class SelectedStock:
    symbol: str
    score: float
    rank: int
    factors: Mapping[str, float]

def select_top_n(
    observations: Mapping[str, Mapping[str, float]],
    factors: list[FactorWeight],
    top_n: int,
) -> list[SelectedStock]:
    """Rank a point-in-time eligible cross section; exclude incomplete rows."""
    if top_n <= 0 or not factors:
        raise ValueError("top_n must be positive and factors nonempty")
    if len({f.name for f in factors}) != len(factors):
        raise ValueError("duplicate factor names")
    if any(not math.isfinite(f.weight) or f.weight < 0 for f in factors):
        raise ValueError("factor weights must be finite and nonnegative")
    total = sum(f.weight for f in factors)
    if total <= 0:
        raise ValueError("total weight must be positive")
    valid = {
        symbol: row for symbol, row in observations.items()
        if all(f.name in row and isinstance(row[f.name], (int, float))
               and math.isfinite(row[f.name]) for f in factors)
    }
    if not valid:
        return []
    moments = {}
    for f in factors:
        vals = [row[f.name] for row in valid.values()]
        avg = sum(vals) / len(vals)
        stdev = math.sqrt(sum((x - avg) ** 2 for x in vals) / len(vals)) or 1.0
        moments[f.name] = avg, stdev
    scored = []
    for symbol, row in valid.items():
        score = sum(
            ((row[f.name] - moments[f.name][0]) / moments[f.name][1])
            * f.weight / total * (1 if f.higher_is_better else -1)
            for f in factors
        )
        scored.append((symbol, score, row))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return [
        SelectedStock(symbol, round(score, 12), idx, dict(row))
        for idx, (symbol, score, row) in enumerate(scored[:top_n], start=1)
    ]
