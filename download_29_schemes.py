import json, time, re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw'
PROCESSED = ROOT / 'data' / 'processed'
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / 'var_cvar_report.csv'

BASE = 'https://api.mfapi.in/mf'

def get_json(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 MutualFundAnalytics/1.0'})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def existing_codes():
    codes = set()
    if REPORT.exists():
        try:
            df = pd.read_csv(REPORT)
            if 'scheme_code' in df:
                codes |= set(df['scheme_code'].astype(str).str.replace(r'\.0$', '', regex=True))
        except Exception:
            pass
    for f in [PROCESSED/'cleaned_nav_history.csv', PROCESSED/'nav_40_schemes.csv', RAW/'live_nav_history.csv']:
        if f.exists():
            try:
                df = pd.read_csv(f, usecols=['scheme_code'])
                codes |= set(df['scheme_code'].astype(str).str.replace(r'\.0$', '', regex=True))
            except Exception:
                pass
    for f in RAW.glob('public_nav_*.csv'):
        try:
            df = pd.read_csv(f, usecols=['scheme_code'])
            codes |= set(df['scheme_code'].astype(str).str.replace(r'\.0$', '', regex=True))
        except Exception:
            pass
    return {x for x in codes if x and x.lower() != 'nan'}

# Search popular Indian equity funds; prefer Direct Plan - Growth variants.
queries = [
 'Parag Parikh Flexi Cap', 'Mirae Asset Large Cap', 'Nippon India Small Cap',
 'Quant Small Cap', 'SBI Small Cap', 'HDFC Mid-Cap Opportunities',
 'Motilal Oswal Midcap', 'Kotak Emerging Equity', 'ICICI Prudential Value Discovery',
 'HDFC Flexi Cap', 'JM Flexicap', 'UTI Nifty 50 Index', 'ICICI Prudential Nifty 50 Index',
 'Navi Nifty 50 Index', 'Motilal Oswal Nasdaq 100', 'Tata Small Cap',
 'Canara Robeco Bluechip Equity', 'Franklin India Flexi Cap', 'DSP Midcap',
 'Edelweiss Mid Cap', 'Invesco India Largecap', 'Bandhan Small Cap',
 'HSBC Small Cap', 'Aditya Birla Sun Life Frontline Equity', 'Tata Large Cap',
 'SBI Focused Equity', 'HDFC Focused 30', 'ICICI Prudential Bluechip',
 'Axis Midcap', 'Kotak Flexicap', 'UTI Flexi Cap', 'PGIM India Midcap Opportunities',
 'Quant Active Fund', 'SBI Contra', 'Nippon India Growth', 'HDFC Small Cap',
 'ICICI Prudential Equity & Debt', 'Tata Digital India', 'SBI Technology Opportunities',
 'Nippon India Pharma'
]

have = existing_codes()
print(f'Existing unique scheme codes found: {len(have)}')
selected = []
seen = set(have)
for q in queries:
    if len(selected) >= 29:
        break
    try:
        results = get_json(BASE + '/search?q=' + __import__('urllib.parse').parse.quote(q))
        if not isinstance(results, list):
            continue
        # Prefer direct growth, then other growth options. Exclude IDCW/dividend/bonus options.
        def score(x):
            n = str(x.get('schemeName','')).lower()
            return (0 if 'direct plan' in n else 1, 0 if 'growth' in n else 1, len(n))
        results = sorted(results, key=score)
        candidate = None
        for x in results:
            code = str(x.get('schemeCode',''))
            name = str(x.get('schemeName',''))
            low = name.lower()
            if not code or code in seen:
                continue
            if 'growth' not in low:
                continue
            if any(k in low for k in ['idcw','dividend','bonus','regular plan - idcw']):
                continue
            candidate = {'scheme_code': code, 'fund_name': name}
            break
        if candidate:
            selected.append(candidate)
            seen.add(candidate['scheme_code'])
            print(f"Selected {len(selected):02d}/29: {candidate['scheme_code']} | {candidate['fund_name']}")
    except Exception as e:
        print(f'Search failed for {q}: {e}')
    time.sleep(0.2)

if len(selected) < 29:
    print(f'Could find only {len(selected)} new schemes from curated searches. Trying general scheme list...')
    offset = 0
    while len(selected) < 29 and offset < 50000:
        try:
            batch = get_json(f'{BASE}?limit=1000&offset={offset}')
        except Exception as e:
            print('Scheme list request failed:', e)
            break
        if not batch:
            break
        # Use likely active direct-growth equity names; keep distinct codes.
        for x in batch:
            code = str(x.get('schemeCode',''))
            name = str(x.get('schemeName',''))
            low = name.lower()
            if not code or code in seen or 'direct plan' not in low or 'growth' not in low:
                continue
            if any(k in low for k in ['debt','liquid','overnight','money market','gilt','idcw','dividend','arbitrage','elss','index fund - direct plan - growth']):
                continue
            selected.append({'scheme_code':code,'fund_name':name})
            seen.add(code)
            print(f"Selected {len(selected):02d}/29: {code} | {name}")
            if len(selected) >= 29:
                break
        offset += 1000
        time.sleep(0.2)

if not selected:
    raise SystemExit('No schemes were selected. Check internet connection and try again.')

all_nav = []
report_rows = []
for i, s in enumerate(selected, 1):
    code = s['scheme_code']
    try:
        payload = get_json(f'{BASE}/{code}')
        meta = payload.get('meta', {})
        data = payload.get('data', [])
        if not data:
            print(f'Skipped no NAV data: {code} {s["fund_name"]}')
            continue
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
        df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
        df = df.dropna(subset=['date','nav']).query('nav > 0').sort_values('date')
        df = df.drop_duplicates('date')
        if len(df) < 30:
            print(f'Skipped too little history: {code} ({len(df)} rows)')
            continue
        df['scheme_code'] = code
        df['fund_name'] = meta.get('scheme_name') or s['fund_name']
        df['fetched_at'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        all_nav.append(df[['scheme_code','fund_name','date','nav','fetched_at']])
        returns = df['nav'].pct_change().dropna()
        var95 = returns.quantile(0.05)
        cvar95 = returns[returns <= var95].mean()
        report_rows.append({'scheme_code':code,'fund_name':df['fund_name'].iloc[0], 'VaR_95':var95, 'CVaR_95':cvar95, 'observations':len(returns), 'data_source':'MFapi.in'})
        print(f'Fetched {i}/{len(selected)}: {code} ({len(df)} NAV rows)')
    except Exception as e:
        print(f'Failed {code}: {e}')
    time.sleep(0.25)

if all_nav:
    extra = pd.concat(all_nav, ignore_index=True)
    extra['date'] = pd.to_datetime(extra['date']).dt.strftime('%Y-%m-%d')
    extra.to_csv(PROCESSED/'additional_29_scheme_nav.csv', index=False)
    # Merge with available processed NAV, if present, without overwriting source files.
    base_frames = []
    source_files = [PROCESSED/'cleaned_nav_history.csv', RAW/'live_nav_history.csv'] + list(RAW.glob('public_nav_*.csv'))
    for f in source_files:
        if f.exists():
            try:
                old = pd.read_csv(f)
                if {'scheme_code','date','nav'}.issubset(old.columns):
                    if 'fund_name' not in old.columns:
                        old['fund_name'] = old['scheme_code'].astype(str)
                    if 'scheme_name' in old.columns:
                        old['fund_name'] = old['fund_name'].fillna(old['scheme_name'])
                    if 'fetched_at' not in old.columns:
                        old['fetched_at'] = ''
                    base_frames.append(old[['scheme_code','fund_name','date','nav','fetched_at']])
            except Exception as e:
                print(f'Could not merge existing file {f.name}: {e}')
    combined = pd.concat(base_frames+[extra], ignore_index=True) if base_frames else extra.copy()
    combined['scheme_code'] = combined['scheme_code'].astype(str).str.replace(r'\.0$','',regex=True)
    combined['date'] = pd.to_datetime(combined['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    combined = combined.dropna(subset=['date','nav']).drop_duplicates(['scheme_code','date'])
    combined.to_csv(PROCESSED/'nav_40_schemes.csv', index=False)

if report_rows:
    new_report = pd.DataFrame(report_rows)
    if REPORT.exists():
        try:
            old_report = pd.read_csv(REPORT)
        except Exception:
            old_report = pd.DataFrame()
        if not old_report.empty:
            old_report['scheme_code'] = old_report['scheme_code'].astype(str).str.replace(r'\.0$','',regex=True)
            new_report['scheme_code'] = new_report['scheme_code'].astype(str)
            merged = pd.concat([old_report, new_report], ignore_index=True, sort=False).drop_duplicates('scheme_code', keep='last')
        else:
            merged = new_report
    else:
        merged = new_report
    merged.to_csv(REPORT, index=False)
    print('\nUpdated var_cvar_report.csv')
    print('Unique scheme codes in report:', merged['scheme_code'].nunique())
    print('New schemes successfully fetched:', len(report_rows))
else:
    print('No additional NAV histories were successfully downloaded.')
