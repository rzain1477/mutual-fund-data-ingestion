
from pathlib import Path
import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Five additional schemes from the public scheme master
SCHEME_CODES = [100027, 100028, 100029, 100030, 100031]

for code in SCHEME_CODES:
    try:
        url = f"https://api.mfapi.in/mf/{code}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        result = response.json()

        records = result.get("data", [])
        if not records:
            print(f"No NAV records for scheme {code}")
            continue

        df = pd.DataFrame(records)
        df["scheme_code"] = code
        df["scheme_name"] = result.get("meta", {}).get("scheme_name", "")

        output_file = RAW_DIR / f"public_nav_{code}.csv"
        df.to_csv(output_file, index=False)

        print(f"Saved {code}: {len(df)} NAV records")

    except Exception as error:
        print(f"Failed {code}: {error}")
