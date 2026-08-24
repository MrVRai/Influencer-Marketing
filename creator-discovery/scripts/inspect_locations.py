import pandas as pd
excel_path = 'd:/Influencer Marketing/data/Vedant.xlsx'
xls = pd.ExcelFile(excel_path)

total_rows_with_city = 0
total_rows_with_address = 0

for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    city_col = [c for c in df.columns if 'city' in c]
    state_col = [c for c in df.columns if 'state' in c]
    addr_col = [c for c in df.columns if 'address' in c]
    
    c_count = len(df[df[city_col[0]].notna()]) if city_col else 0
    a_count = len(df[df[addr_col[0]].notna()]) if addr_col else 0
    
    total_rows_with_city += c_count
    total_rows_with_address += a_count
    
    if c_count > 0 or a_count > 0:
        print(f"Sheet: {sheet} | Rows with City: {c_count} | Rows with Address: {a_count}")

print(f"\nTotal rows with explicit City: {total_rows_with_city}")
print(f"Total rows with Address: {total_rows_with_address}")
