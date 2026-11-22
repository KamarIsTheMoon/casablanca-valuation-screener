"""Standard DCF for non-financial companies, same logic as the Excel model in mutandis-valuation."""
from dataclasses import dataclass


@dataclass
class DCFInputs:
    revenue: float              # last actual year, MAD m
    growth: list[float]         # one rate per forecast year
    ebitda_margin: list[float]
    da_pct: float               # D&A as % of revenue
    capex_pct: float            # capex as % of revenue
    nwc_pct_change: float       # change in working capital as % of change in revenue
    tax_rate: float
    wacc: float
    terminal_growth: float
    net_debt: float
    shares_m: float
    minorities: float = 0.0


def value_per_share(i: DCFInputs) -> dict:
    if i.wacc <= i.terminal_growth:
        raise ValueError("WACC must be higher than terminal growth.")
    if len(i.growth) != len(i.ebitda_margin):
        raise ValueError("growth and ebitda_margin need one value per year.")
    rev_prev, pv_sum, fcfs = i.revenue, 0.0, []
    for t, (g, m) in enumerate(zip(i.growth, i.ebitda_margin), start=1):
        rev = rev_prev * (1 + g)
        ebitda, da = rev * m, rev * i.da_pct
        nopat = (ebitda - da) * (1 - i.tax_rate)
        fcf = nopat + da - rev * i.capex_pct - (rev - rev_prev) * i.nwc_pct_change
        fcfs.append(fcf)
        pv_sum += fcf / (1 + i.wacc) ** t
        rev_prev = rev
    n = len(fcfs)
    tv = fcfs[-1] * (1 + i.terminal_growth) / (i.wacc - i.terminal_growth)
    pv_tv = tv / (1 + i.wacc) ** n
    ev = pv_sum + pv_tv
    equity = ev - i.net_debt - i.minorities
    return {"fcf": fcfs, "enterprise_value": ev, "equity_value": equity,
            "value_per_share": equity / i.shares_m, "terminal_value_share": pv_tv / ev}
