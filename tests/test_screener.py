"""Tests use small made-up numbers chosen so the answers are easy to check by hand."""
import math

import pandas as pd
import pytest

from src.dcf import DCFInputs, value_per_share
from src.multiples import add_sector_comparison, compute


def frame(rows):
    cols = ["ticker", "sector", "type", "price_mad", "shares_m", "revenue_mad_m", "ebitda_mad_m",
            "net_income_mad_m", "net_debt_mad_m", "book_equity_mad_m", "dps_mad"]
    return pd.DataFrame(rows, columns=cols)


def test_basic_multiples():
    df = compute(frame([["AAA", "S", "corporate", 100, 10, 500, 200, 100, 400, 800, 5]]))
    r = df.iloc[0]
    assert r.market_cap_mad_m == 1000
    assert r.pe == 10
    assert r.enterprise_value_mad_m == 1400
    assert r.ev_ebitda == 7
    assert r.dividend_yield == 0.05
    assert r.payout_ratio == 0.5
    assert r.price_to_book == 1.25


def test_missing_and_negative_inputs_give_empty_ratios():
    df = compute(frame([["BBB", "S", "corporate", 50, 10, 300, None, -20, None, None, 0]]))
    r = df.iloc[0]
    assert math.isnan(r.pe)          # loss making: P/E not meaningful
    assert math.isnan(r.ev_ebitda)   # no EBITDA collected
    assert r.price_to_sales == pytest.approx(500 / 300)


def test_banks_have_no_ev_multiples():
    df = compute(frame([["BNK", "Banks", "bank", 100, 10, 0, 300, 100, 5000, 900, 4]]))
    r = df.iloc[0]
    assert math.isnan(r.enterprise_value_mad_m) and math.isnan(r.ev_ebitda)
    assert r.pe == 10 and r.price_to_book == pytest.approx(1000 / 900)


def test_sector_median_needs_two_peers():
    df = add_sector_comparison(compute(frame([
        ["A", "S1", "corporate", 10, 10, 100, 20, 10, 0, 50, 1],   # P/E 10
        ["B", "S1", "corporate", 20, 10, 100, 20, 10, 0, 50, 1],   # P/E 20
        ["C", "S2", "corporate", 10, 10, 100, 20, 10, 0, 50, 1],   # alone in its sector
    ])))
    assert df.loc[0, "pe_sector_median"] == 15
    assert df.loc[0, "pe_vs_sector"] == pytest.approx(10 / 15 - 1)
    assert math.isnan(df.loc[2, "pe_sector_median"])


def test_dcf_matches_hand_calculation():
    i = DCFInputs(revenue=100, growth=[0.0], ebitda_margin=[0.2], da_pct=0.05, capex_pct=0.05,
                  nwc_pct_change=0.1, tax_rate=0.3, wacc=0.1, terminal_growth=0.0, net_debt=10, shares_m=1)
    res = value_per_share(i)
    # FCF = (20 - 5) * 0.7 + 5 - 5 - 0 = 10.5 ; TV = 105 ; EV = 10.5/1.1 + 105/1.1 = 105
    assert res["fcf"][0] == pytest.approx(10.5)
    assert res["enterprise_value"] == pytest.approx(105)
    assert res["value_per_share"] == pytest.approx(95)


def test_dcf_rejects_wacc_below_growth():
    with pytest.raises(ValueError):
        value_per_share(DCFInputs(100, [0.0], [0.2], 0.05, 0.05, 0.1, 0.3, 0.02, 0.03, 0, 1))
