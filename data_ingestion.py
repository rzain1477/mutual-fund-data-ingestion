from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

csv_files = sorted(RAW_DIR.glob("*.csv"))

if not csv_files:
    print("No CSV files found in data/raw.")
    print("Please copy your provided CSV datasets into data/raw.")
else:
    quality_results = []

    for file_path in csv_files:
        print("\n" + "=" * 60)
        print(f"FILE: {file_path.name}")

        try:
            df = pd.read_csv(file_path)

            print("\nShape:")
            print(df.shape)

            print("\nData types:")
            print(df.dtypes)

            print("\nFirst 5 rows:")
            print(df.head())

            print("\nMissing values:")
            print(df.isna().sum())

            print("\nDuplicate rows:", df.duplicated().sum())

            quality_results.append({
                "file_name": file_path.name,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "missing_values": int(df.isna().sum().sum()),
                "duplicate_rows": int(df.duplicated().sum()),
            })

        except Exception as error:
            print(f"Could not read {file_path.name}: {error}")

    if quality_results:
        report = pd.DataFrame(quality_results)
        report_path = REPORTS_DIR / "data_quality_summary.csv"
        report.to_csv(report_path, index=False)

        print("\nData quality report saved to:", report_path)
        print(report.to_string(index=False))
