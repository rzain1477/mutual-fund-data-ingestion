# Mutual Fund Data Ingestion and Analytics

## Project Overview
A Python-based project to fetch mutual fund Net Asset Value (NAV) data using the MFAPI, store raw data, clean NAV records, and perform data quality checks.

## Features
- Fetch NAV history for six mutual fund schemes.
- Save original API responses as JSON files.
- Combine NAV records into a CSV file.
- Clean data types and remove records with missing essential values.
- Remove duplicate records based on scheme code and date.
- Generate a data quality summary.
- Validate scheme codes between the fund master and NAV history.

## Project Structure
- `data/raw/` — Raw NAV data and fund master files.
- `data/processed/` — Cleaned NAV data.
- `notebooks/` — Analysis notebooks.
- `sql/` — SQL scripts.
- `dashboard/` — Dashboard files.
- `reports/` — Data quality reports.
- `live_nav_fetch.py` — Fetches NAV data from MFAPI.
- `data_ingestion.py` — Inspects CSV files and generates a data quality report.
- `process_nav_data.py` — Cleans and saves NAV history.
- `validate_scheme_codes.py` — Validates scheme codes.
- `requirements.txt` — Python dependencies.

## Setup
Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Project
Fetch NAV data:

```bash
python live_nav_fetch.py
```

Generate the data quality report:

```bash
python data_ingestion.py
```

Process NAV data:

```bash
python process_nav_data.py
```

Validate scheme codes:

```bash
python validate_scheme_codes.py
```

## Data Source
Mutual fund NAV data is fetched from the MFAPI service.

## Current Progress
Live NAV fetching, data quality checks, scheme code validation, and processed NAV CSV generation have been completed for the six configured schemes.

**Note:** The ten internship-provided CSV datasets and any remaining project requirements will be incorporated when they become available.
