
from pathlib import Path
import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

url = "https://api.mfapi.in/mf"

try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    schemes = response.json()
    df = pd.DataFrame(schemes)

    output_file = RAW_DIR / "public_scheme_master.csv"
    df.to_csv(output_file, index=False)

    print("Download successful!")
    print("Total schemes:", len(df))
    print("Columns:", list(df.columns))
    print("Preview:")
    print(df.head())
    print("Saved to:", output_file)

except Exception as error:
    print("Download failed:", error)
