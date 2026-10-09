import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import requests

# Project folders
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Mutual fund scheme codes
FUNDS = {
    "125497": "HDFC Top 100 Direct",
    "119551": "SBI Bluechip",
    "120503": "ICICI Bluechip",
    "118632": "Nippon Large Cap",
    "119092": "Axis Bluechip",
    "120841": "Kotak Bluechip",
}

BASE_URL = "https://api.mfapi.in/mf/"

def fetch_nav(scheme_code, fund_name):
    url = f"{BASE_URL}{scheme_code}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        result = response.json()

        # Save the original API response
        raw_json_file = RAW_DIR / f"nav_{scheme_code}.json"
        with open(raw_json_file, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2, ensure_ascii=False)

        records = result.get("data", [])

        if not records:
            print(f"No NAV records found: {fund_name}")
            return []

        fetched_at = datetime.now(timezone.utc).isoformat()
        rows = []

        for record in records:
            rows.append({
                "scheme_code": scheme_code,
                "fund_name": fund_name,
                "date": record.get("date"),
                "nav": record.get("nav"),
                "fetched_at": fetched_at,
            })

        print(f"SUCCESS: {fund_name} - {len(rows)} records")
        return rows

    except (requests.RequestException, ValueError) as error:
        print(f"ERROR: {fund_name} - {error}")
        return []

def main():
    all_rows = []

    for scheme_code, fund_name in FUNDS.items():
        all_rows.extend(fetch_nav(scheme_code, fund_name))

    if not all_rows:
        print("No NAV data fetched. Please check your internet connection.")
        return

    df = pd.DataFrame(all_rows)

    df["date"] = pd.to_datetime(
        df["date"], format="%d-%m-%Y", errors="coerce"
    )
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    output_file = RAW_DIR / "live_nav_history.csv"
    df.to_csv(output_file, index=False)

    print("\n--- NAV DATA SUMMARY ---")
    print("Total records:", len(df))
    print("Funds fetched:", df["scheme_code"].nunique())
    print("Missing dates:", df["date"].isna().sum())
    print("Missing NAV values:", df["nav"].isna().sum())
    print("\nPreview:")
    print(df.head())
    print(f"\nSaved CSV: {output_file}")

if __name__ == "__main__":
    main()
