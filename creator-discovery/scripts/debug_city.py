"""Inspect actual Excel column headers across all 45 sheets."""
import pandas as pd

xls = pd.ExcelFile('d:/Influencer Marketing/data/Vedant.xlsx')

for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    if df.empty:
        continue
    cols = list(df.columns)
    cols_lower = [str(c).strip().lower() for c in cols]
    
    # Identify which columns match phone/contact patterns
    phone_matches = [c for c, cl in zip(cols, cols_lower) if any(x in cl for x in ['contact', 'number', 'phone', 'mobile'])]
    city_matches = [c for c, cl in zip(cols, cols_lower) if 'city' in cl]
    state_matches = [c for c, cl in zip(cols, cols_lower) if 'state' in cl]
    addr_matches = [c for c, cl in zip(cols, cols_lower) if 'address' in cl or 'adrress' in cl]
    pin_matches = [c for c, cl in zip(cols, cols_lower) if 'pin' in cl]
    
    # Sample first non-null value from phone column
    phone_sample = ""
    if phone_matches:
        col = phone_matches[0]
        non_null = df[col].dropna().head(3).tolist()
        phone_sample = str(non_null)
    
    city_sample = ""
    if city_matches:
        col = city_matches[0]
        non_null = df[col].dropna().head(3).tolist()
        city_sample = str(non_null)
    
    print(f"\n=== {sheet} ({len(df)} rows) ===")
    print(f"  ALL COLS: {cols}")
    if phone_matches:
        print(f"  PHONE cols: {phone_matches} -> sample: {phone_sample}")
    if city_matches:
        print(f"  CITY cols: {city_matches} -> sample: {city_sample}")
    if state_matches:
        print(f"  STATE cols: {state_matches}")
    if addr_matches:
        print(f"  ADDR cols: {addr_matches}")
    if pin_matches:
        print(f"  PIN cols: {pin_matches}")
    if not city_matches and not state_matches and not addr_matches:
        print(f"  ** NO LOCATION COLUMNS **")
