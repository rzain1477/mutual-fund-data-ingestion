import pandas as pd

df = pd.read_csv("data/raw/fund_master.csv")

print("FUND MASTER DATA")
print(df)

print("\nCOLUMN NAMES:")
print(df.columns.tolist())

print("\nUNIQUE FUND NAMES:", df["fund_name"].nunique())
print("UNIQUE SCHEME CODES:", df["scheme_code"].nunique())
print("DUPLICATE SCHEME CODES:", df["scheme_code"].duplicated().sum())