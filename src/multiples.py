"""Valuation multiples for each company. Missing inputs give an empty ratio, never a guess."""
import numpy as np
import pandas as pd

FINANCIAL_TYPES = {"bank", "insurer"}


def _ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """num / den, empty when either is missing or the denominator is zero or negative."""
    out = num / den.where(den > 0)
    return out.replace([np.inf, -np.inf], np.nan)


def compute(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["market_cap_mad_m"] = df["price_mad"] * df["shares_m"]
    df["eps_mad"] = _ratio(df["net_income_mad_m"], df["shares_m"])
    df["pe"] = _ratio(df["market_cap_mad_m"], df["net_income_mad_m"])
    df["price_to_sales"] = _ratio(df["market_cap_mad_m"], df["revenue_mad_m"])
    df["price_to_book"] = _ratio(df["market_cap_mad_m"], df["book_equity_mad_m"])
    df["dividend_yield"] = _ratio(df["dps_mad"], df["price_mad"])
    df["payout_ratio"] = _ratio(df["dps_mad"], df["eps_mad"])

    # Enterprise value multiples only make sense for non-financial companies.
    is_corporate = ~df["type"].str.lower().isin(FINANCIAL_TYPES)
    df["enterprise_value_mad_m"] = (df["market_cap_mad_m"] + df["net_debt_mad_m"]).where(is_corporate)
    df["ev_ebitda"] = _ratio(df["enterprise_value_mad_m"], df["ebitda_mad_m"]).where(is_corporate)
    df["net_debt_ebitda"] = _ratio(df["net_debt_mad_m"], df["ebitda_mad_m"]).where(is_corporate)
    return df


def add_sector_comparison(df: pd.DataFrame, metrics=("pe", "ev_ebitda", "price_to_book", "dividend_yield")) -> pd.DataFrame:
    """Sector median of each metric, and each company's premium or discount to it."""
    df = df.copy()
    for m in metrics:
        med = df.groupby("sector")[m].transform("median")
        peers = df.groupby("sector")[m].transform("count")
        df[f"{m}_sector_median"] = med.where(peers >= 2)
        df[f"{m}_vs_sector"] = (df[m] / df[f"{m}_sector_median"] - 1)
    return df
