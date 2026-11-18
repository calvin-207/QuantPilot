import pytest
from quant_core.selection import FactorWeight, select_top_n

def test_higher_factor_wins():
    result = select_top_n(
        {"A": {"mom": 2.0}, "B": {"mom": 1.0}},
        [FactorWeight("mom", 1.0)], 2
    )
    assert [r.symbol for r in result] == ["A", "B"]
    assert [r.rank for r in result] == [1, 2]

def test_lower_is_better():
    result = select_top_n(
        {"A": {"risk": 2.0}, "B": {"risk": 1.0}},
        [FactorWeight("risk", 1.0, higher_is_better=False)], 1
    )
    assert result[0].symbol == "B"

def test_missing_factor_does_not_get_fabricated():
    result = select_top_n(
        {"A": {"mom": 2.0}, "B": {}},
        [FactorWeight("mom", 1.0)], 5
    )
    assert [r.symbol for r in result] == ["A"]

def test_bad_weights_rejected():
    with pytest.raises(ValueError):
        select_top_n({"A": {"mom": 1.0}}, [FactorWeight("mom", -1)], 1)
