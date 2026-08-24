import pandas as pd
excel_path = 'd:/Influencer Marketing/data/Vedant.xlsx'
xls = pd.ExcelFile(excel_path)

for s in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=s, nrows=1)
    cols = [str(c).strip() for c in df.columns if not str(c).startswith('Unnamed')]
    print(f"{s} ({len(df.columns)} cols): {cols}")
