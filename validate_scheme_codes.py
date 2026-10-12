
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"

fund_master = pd.read_csv(RAW_DIR / "fund_master.csv")
nav_history = pd.read_csv(RAW_DIR / "live_nav_history.csv")

master_codes = set(
    pd.to_numeric(fund_master["scheme_code"], errors="coerce")
    .dropna()
    .astype(int)
)

nav_codes = set(
    pd.to_numeric(nav_history["scheme_code"], errors="coerce")
    .dropna()
    .astype(int)
)

missing_codes = master_codes - nav_codes
extra_codes = nav_codes - master_codes

print("Fund Master codes:", len(master_codes))
print("NAV History codes:", len(nav_codes))
print("Missing codes:", len(missing_codes))
print("Extra codes:", len(extra_codes))

if missing_codes:
    print("Missing codes:", sorted(missing_codes))

if extra_codes:
    print("Extra codes:", sorted(extra_codes))

if not missing_codes and not extra_codes:
    print("SUCCESS: All scheme codes match.")
else:
    print("WARNING: Scheme code mismatch found.")
