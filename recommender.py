
import pandas as pd
import numpy as np
from pathlib import Path

root = Path(__file__).resolve().parent
files = [root / "data" / "processed" / "cleaned_nav_history.csv"]
files += list((root / "data" / "raw").glob("public_nav_*.csv"))

frames = []

for file in files:
    if not file.exists():
        continue

    df = pd.read_csv(file)

    if "scheme_name" in df.columns:
        df = df.rename(columns={"scheme_name": "fund_name"})

    required = ["scheme_code", "fund_name", "date", "nav"]
    if all(col in df.columns for col in required):
        frames.append(df[required])

if not frames:
    print("ERROR: No valid NAV data files were found.")
    raise SystemExit(1)

nav = pd.concat(frames, ignore_index=True)
nav["date"] = pd.to_datetime(nav["date"], dayfirst=True, errors="coerce")
nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
nav = nav.dropna(subset=["date", "nav"])
nav = nav[nav["nav"] > 0]
nav = nav.drop_duplicates(["scheme_code", "date"])

results = []

for code, group in nav.groupby("scheme_code"):
    group = group.sort_values("date")
    returns = group["nav"].pct_change()
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

    if len(returns) < 30 or returns.std() == 0:
        continue

    results.append({
        "scheme_code": str(code),
        "fund_name": group["fund_name"].iloc[0],
        "sharpe_ratio": returns.mean() / returns.std() * np.sqrt(252),
        "annual_volatility": returns.std() * np.sqrt(252)
    })

funds = pd.DataFrame(results)

if funds.empty:
    print("ERROR: No valid return series could be calculated.")
    raise SystemExit(1)

n = min(3, len(funds))
labels = ["Low", "Moderate", "High"][:n]

funds["risk_grade"] = pd.qcut(
    funds["annual_volatility"].rank(method="first"),
    q=n,
    labels=labels
)

print("Available schemes:", len(funds))
choice = input("Enter risk profile (Low/Moderate/High): ").strip().title()

if choice not in ["Low", "Moderate", "High"]:
    print("ERROR: Please enter Low, Moderate, or High.")
else:
    matched = funds[funds["risk_grade"] == choice]
    print("\nTop fund recommendations for", choice, "risk profile:")

    if matched.empty:
        print("No funds are available in this risk category.")
    else:
        print(
            matched.sort_values("sharpe_ratio", ascending=False)[
                ["scheme_code", "fund_name", "risk_grade", "sharpe_ratio"]
            ].head(3).to_string(index=False)
        )

print(
    "\nNote: Risk grades are estimated using historical volatility "
    "and are not official fund ratings."
)
