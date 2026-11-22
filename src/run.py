"""Run the screener.

    python -m src.run

Reads data/companies.csv, writes output/screener.csv, output/screener.md and output/pe_vs_yield.png.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .multiples import add_sector_comparison, compute

ROOT = Path(__file__).resolve().parents[1]
COLS = ["ticker", "name", "sector", "price_mad", "price_date", "market_cap_mad_m", "pe", "pe_vs_sector",
        "ev_ebitda", "price_to_sales", "dividend_yield", "payout_ratio", "net_debt_ebitda"]


def fmt(df: pd.DataFrame) -> pd.DataFrame:
    out = df[COLS].copy()
    for c in ["pe", "ev_ebitda", "price_to_sales", "net_debt_ebitda"]:
        out[c] = out[c].map(lambda v: f"{v:.1f}x" if pd.notna(v) else "")
    for c in ["dividend_yield", "payout_ratio", "pe_vs_sector"]:
        out[c] = out[c].map(lambda v: f"{v:+.0%}" if c == "pe_vs_sector" and pd.notna(v) else (f"{v:.1%}" if pd.notna(v) else ""))
    out["market_cap_mad_m"] = out["market_cap_mad_m"].map(lambda v: f"{v:,.0f}")
    return out


def chart(df: pd.DataFrame, path: Path) -> None:
    d = df.dropna(subset=["pe", "dividend_yield"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(d["pe"], d["dividend_yield"] * 100, s=d["market_cap_mad_m"] / d["market_cap_mad_m"].max() * 800 + 60, color="#1F3864", alpha=0.75)
    for _, r in d.iterrows():
        ax.annotate(r["ticker"], (r["pe"], r["dividend_yield"] * 100), xytext=(6, 6), textcoords="offset points")
    ax.set_xlabel("P/E (x)")
    ax.set_ylabel("Dividend yield (%)")
    ax.set_title("Casablanca food & consumer: P/E vs dividend yield (bubble = market cap)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> pd.DataFrame:
    df = add_sector_comparison(compute(pd.read_csv(ROOT / "data" / "companies.csv")))
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "screener.csv", index=False)
    table = fmt(df.sort_values("pe"))
    (out / "screener.md").write_text(table.to_markdown(index=False), encoding="utf-8")
    chart(df, out / "pe_vs_yield.png")
    print(table.to_string(index=False))
    return df


if __name__ == "__main__":
    main()
