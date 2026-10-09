import pandas as pd

fund_master = pd.read_csv("data/raw/fund_master.csv")
nav_history = pd.read_csv("data/raw/live_nav_history.csv")

master_codes = set(fund_master["scheme_code"].dropna().astype(int))
nav_codes = set(nav_history["scheme_code"].dropna().astype(int))

missing_codes = master_codes - nav_codes

print("Fund Master codes:", len(master_codes))
print("NAV History codes:", len(nav_codes))
print("Missing codes:", len(missing_codes))

if len(missing_codes) > 0:
    print("Missing codes found:", missing_codes)
else:
    print("SUCCESS: All Fund Master codes exist in NAV History.")