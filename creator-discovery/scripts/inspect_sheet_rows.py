import pandas as pd
excel_path = 'd:/Influencer Marketing/data/Vedant.xlsx'
xls = pd.ExcelFile(excel_path)

for s in ['Sheet1', 'Sheet2', 'Sheet5', 'Sheet9', 'Sheet22']:
    df = pd.read_excel(xls, sheet_name=s, nrows=4)
    print(f"=== {s} ===")
    print("Cols:", df.columns.tolist())
    for idx, row in df.head(3).iterrows():
        print(f"Row {idx}: {dict(row)}")
