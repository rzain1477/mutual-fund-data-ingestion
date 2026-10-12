
from pathlib import Path
import pandas as pd

# Project folders
BASE_DIR = Path(__file__).resolve().parent
RAW_FILE = BASE_DIR / "data" / "raw" / "live_nav_history.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Check input file
if not RAW_FILE.exists():
    print("ERROR: live_nav_history.csv not found.")
else:
    df = pd.read_csv(RAW_FILE)

    print("Original rows:", len(df))

    # Convert columns to correct data types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    # Remove rows with missing essential values
    df = df.dropna(subset=["scheme_code", "date", "nav"])

    # Remove duplicate fund-date records
    df = df.drop_duplicates(
        subset=["scheme_code", "date"],
        keep="last"
    )

    # Sort by fund and date
    df = df.sort_values(
        ["scheme_code", "date"]
    ).reset_index(drop=True)

    # Save processed data
    output_file = PROCESSED_DIR / "cleaned_nav_history.csv"
    df.to_csv(output_file, index=False)

    print("\n--- PROCESSING SUMMARY ---")
    print("Cleaned rows:", len(df))
    print("Funds:", df["scheme_code"].nunique())
    print("Missing values:")
    print(df.isna().sum())
    print("\nPreview:")
    print(df.head())
    print("\nSaved to:", output_file)
