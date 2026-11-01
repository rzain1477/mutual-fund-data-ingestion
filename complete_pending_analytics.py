"""Advanced analytics add-on for the Mutual Fund project.

IMPORTANT: Investor transactions and sector holdings were not present in the
supplied project data. This script creates clearly labelled SIMULATED demo data
to demonstrate cohort, SIP continuity and HHI calculations. Do not present these
results as actual investor or fund data. Replace simulated inputs with verified
data before drawing real conclusions.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
RAW.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261023)

report_path = ROOT / "var_cvar_report.csv"
if not report_path.exists():
    raise FileNotFoundError("var_cvar_report.csv not found. Run this script from the project root.")
funds = pd.read_csv(report_path)
if not {"scheme_code", "fund_name"}.issubset(funds.columns):
    raise ValueError("var_cvar_report.csv must contain scheme_code and fund_name columns.")
funds = funds.drop_duplicates("scheme_code").reset_index(drop=True)
fund_codes = funds["scheme_code"].astype(str).tolist()
fund_names = dict(zip(funds["scheme_code"].astype(str), funds["fund_name"].astype(str)))

# 1. SIMULATED investor transaction records, explicitly labelled as synthetic.
n_investors = 150
investors = [f"SIM_INV_{i:04d}" for i in range(1, n_investors + 1)]
transactions = []
start, end = pd.Timestamp("2022-01-01"), pd.Timestamp("2025-12-31")
days_range = (end - start).days
for investor in investors:
    investor_start = start + pd.Timedelta(days=int(rng.integers(0, days_range - 120)))
    n_tx = int(rng.integers(3, 30))
    fund_code = str(rng.choice(fund_codes))
    current_date = investor_start
    for _ in range(n_tx):
        gap = int(rng.choice([28, 30, 31, 32, 45, 60], p=[.18, .25, .20, .17, .12, .08]))
        current_date += pd.Timedelta(days=gap)
        if current_date > end:
            break
        transactions.append({
            "investor_id": investor,
            "transaction_date": current_date.date().isoformat(),
            "scheme_code": fund_code,
            "fund_name": fund_names.get(fund_code, "Unknown fund"),
            "transaction_type": "SIP",
            "amount_inr": int(rng.choice([500, 1000, 1500, 2000, 3000, 5000])),
            "data_type": "SIMULATED_DEMO_NOT_REAL"
        })
tx = pd.DataFrame(transactions)
tx.to_csv(RAW / "SIMULATED_demo_investor_transactions.csv", index=False)
tx["transaction_date"] = pd.to_datetime(tx["transaction_date"], errors="coerce")
tx["cohort_year"] = tx.groupby("investor_id")["transaction_date"].transform("min").dt.year
investor_total = tx.groupby(["cohort_year", "investor_id"], as_index=False)["amount_inr"].sum()
cohort_base = investor_total.groupby("cohort_year", as_index=False).agg(
    investors=("investor_id", "nunique"),
    avg_invested_per_investor_inr=("amount_inr", "mean"),
    total_invested_inr=("amount_inr", "sum")
)
top_fund = (tx.groupby(["cohort_year", "fund_name"], as_index=False)["amount_inr"].sum()
            .sort_values(["cohort_year", "amount_inr"], ascending=[True, False])
            .drop_duplicates("cohort_year")
            .rename(columns={"fund_name": "top_fund_by_invested_amount"}))
cohort = cohort_base.merge(top_fund, on="cohort_year", how="left")
cohort["data_type"] = "SIMULATED_DEMO_NOT_REAL"
cohort.to_csv(REPORTS / "investor_cohort_analysis.csv", index=False)

# 2. SIP continuity for investors with at least six transactions.
continuity_rows = []
for investor, group in tx.sort_values("transaction_date").groupby("investor_id"):
    group = group.sort_values("transaction_date")
    if len(group) < 6:
        continue
    gaps = group["transaction_date"].diff().dt.days.dropna()
    avg_gap = float(gaps.mean()) if not gaps.empty else np.nan
    continuity_rows.append({
        "investor_id": investor,
        "sip_transactions": len(group),
        "average_gap_days": round(avg_gap, 2) if pd.notna(avg_gap) else np.nan,
        "at_risk_gt_35_days": bool(pd.notna(avg_gap) and avg_gap > 35),
        "data_type": "SIMULATED_DEMO_NOT_REAL"
    })
continuity = pd.DataFrame(continuity_rows)
continuity.to_csv(REPORTS / "sip_continuity_analysis.csv", index=False)

# 3. SIMULATED sector holdings; these are not actual fund portfolios.
sectors = ["Financial Services", "Information Technology", "Consumer Goods", "Healthcare",
           "Industrials", "Energy", "Materials", "Utilities", "Real Estate", "Communication Services"]
holdings_rows = []
for code in fund_codes:
    chosen_n = int(rng.integers(5, len(sectors) + 1))
    chosen = rng.choice(sectors, size=chosen_n, replace=False)
    weights = rng.dirichlet(np.ones(chosen_n) * 1.5) * 100
    for sector, weight in zip(chosen, weights):
        holdings_rows.append({
            "scheme_code": code, "fund_name": fund_names.get(code, "Unknown fund"),
            "sector": sector, "weight_pct": round(float(weight), 6),
            "data_type": "SIMULATED_DEMO_NOT_REAL"
        })
holdings = pd.DataFrame(holdings_rows)
holdings.to_csv(RAW / "SIMULATED_demo_sector_holdings.csv", index=False)
hhi_rows = []
for code, group in holdings.groupby("scheme_code"):
    weights = group["weight_pct"].clip(lower=0)
    total = weights.sum()
    if total <= 0:
        continue
    normalized_pct = weights / total * 100
    hhi = float((normalized_pct ** 2).sum())
    hhi_rows.append({
        "scheme_code": str(code), "fund_name": fund_names.get(str(code), "Unknown fund"),
        "sector_count": int(group["sector"].nunique()), "sector_hhi": round(hhi, 2),
        "concentration_interpretation": ("Higher sector concentration" if hhi >= 2500 else
                                          "Moderate sector concentration" if hhi >= 1500 else
                                          "Lower sector concentration"),
        "data_type": "SIMULATED_DEMO_NOT_REAL"
    })
hhi_df = pd.DataFrame(hhi_rows).sort_values("sector_hhi", ascending=False)
hhi_df.to_csv(REPORTS / "sector_hhi_analysis.csv", index=False)

summary = """ADVANCED ANALYTICS DATA LIMITATION
==================================
The supplied project directory did not contain verified investor transaction
history or verified portfolio/sector holdings. This script generated SIMULATED
demo datasets only to demonstrate the requested calculations.

Generated files:
- data/raw/SIMULATED_demo_investor_transactions.csv
- data/raw/SIMULATED_demo_sector_holdings.csv
- reports/investor_cohort_analysis.csv
- reports/sip_continuity_analysis.csv
- reports/sector_hhi_analysis.csv

All generated results are labelled SIMULATED_DEMO_NOT_REAL. They must not be
reported as actual investor behaviour or actual fund sector exposure. Replace
the simulated input datasets with verified transaction and holdings data before
drawing real conclusions.
"""
(REPORTS / "DATA_LIMITATIONS.txt").write_text(summary, encoding="utf-8")
print("Completed demo analytics. These results are SIMULATED, not actual data.")
print("Cohort report:", REPORTS / "investor_cohort_analysis.csv")
print("SIP continuity report:", REPORTS / "sip_continuity_analysis.csv")
print("Sector HHI report:", REPORTS / "sector_hhi_analysis.csv")
print("Limitation note:", REPORTS / "DATA_LIMITATIONS.txt")
print("Cohort rows:", len(cohort), "| SIP continuity rows:", len(continuity), "| HHI funds:", len(hhi_df))
