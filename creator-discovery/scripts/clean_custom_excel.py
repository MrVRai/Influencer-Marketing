"""
Custom Creator Excel Cleaner & Phone Validator for Creator Orbit
Cleans raw creator Excel files with 'Name' and 'Number' columns:
- Strips float trailing zeros (e.g. .0 / .00)
- Cleans non-digit characters, spaces, dashes, +91 prefixes
- Strictly validates 10-digit Indian phone numbers (starting with 6, 7, 8, 9)
- Formats for WhatsApp (91XXXXXXXXXX)
- Exports cleaned Excel, CSV for Edge extensions, and updates 1-click launcher HTML
"""

import os
import sys
import re
import json
import urllib.parse
import argparse
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_WA_MESSAGE = """Hey {name}! Team Creator Orbit here 👋✨

Hope you're doing great!

We’re curating a fresh creator roster for upcoming Beauty & Skincare PR hampers and barter brand campaigns at *Creator Orbit* 🎁

Make sure to follow our Instagram page so we can shortlist you for upcoming brand drops:
👉 https://instagram.com/thecreatororbit

Drop a quick "Done" here after following so we can add you to our priority list! 💙"""

def clean_phone_value(raw_val):
    if raw_val is None or pd.isna(raw_val):
        return None, "Empty / Missing value"
        
    s = str(raw_val).strip()
    
    # 1. Remove float trailing zeros (.0 / .00)
    if s.endswith('.0'):
        s = s[:-2]
    elif s.endswith('.00'):
        s = s[:-3]
    elif '.' in s:
        # e.g. 9876543210.000 -> take before decimal if decimal part is all zeros
        parts = s.split('.')
        if len(parts) == 2 and parts[1].replace('0', '') == '':
            s = parts[0]
            
    # 2. Strip scientific notation if present (e.g. 9.876543E+09)
    if 'e+' in s.lower() or 'e' in s.lower():
        try:
            val_float = float(raw_val)
            s = f"{int(val_float)}"
        except Exception:
            pass

    # 3. Strip all non-numeric characters
    digits = re.sub(r'[^0-9]', '', s)
    
    # 4. Handle leading prefixes
    # If 12 digits starting with 91 -> strip 91 to get 10-digit base
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    # If 11 digits starting with 0 -> strip 0
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
        
    # 5. Strict 10-digit validation
    if len(digits) != 10:
        return None, f"Invalid length ({len(digits)} digits): {raw_val}"
        
    # Check if starting digit is valid Indian mobile (6, 7, 8, 9)
    if digits[0] not in ['6', '7', '8', '9']:
        return None, f"Invalid starting digit '{digits[0]}': {raw_val}"
        
    return digits, "Valid"

def find_column(df, possible_names):
    cols_lower = {str(c).strip().lower(): c for c in df.columns}
    for name in possible_names:
        if name.lower() in cols_lower:
            return cols_lower[name.lower()]
    return None

def process_excel_file(file_path, output_excel=None):
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        return
        
    print(f"\n📂 Reading input file: {file_path}")
    
    # Read file (Excel or CSV)
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, dtype=str)
    else:
        df = pd.read_excel(file_path, dtype=str)
        
    print(f"Found {len(df)} total rows. Columns: {list(df.columns)}")
    
    # Identify Name and Number columns
    name_col = find_column(df, ['Name', 'Creator Name', 'Creator', 'Full Name', 'Username'])
    num_col = find_column(df, ['Number', 'Phone', 'Phone Number', 'Contact', 'Contact Number', 'WhatsApp', 'Mobile', 'Mobile Number'])
    
    if not num_col:
        print(f"❌ Could not find a 'Number' or 'Phone' column in the sheet. Available columns: {list(df.columns)}")
        return
        
    if not name_col:
        print("⚠️ 'Name' column not found, using 'Creator' as default name.")
        df['Name'] = 'Creator'
        name_col = 'Name'
        
    valid_rows = []
    invalid_rows = []
    seen_numbers = set()
    
    for idx, row in df.iterrows():
        raw_name = row.get(name_col)
        raw_num = row.get(num_col)
        
        name = str(raw_name).strip() if (raw_name is not None and not pd.isna(raw_name)) else "Creator"
        if name.lower() in ['nan', 'none', '']:
            name = "Creator"
            
        clean_digits, status = clean_phone_value(raw_num)
        
        if clean_digits:
            if clean_digits in seen_numbers:
                invalid_rows.append({
                    "Original_Row": idx + 2,
                    "Name": name,
                    "Raw_Number": raw_num,
                    "Reason": "Duplicate number (already added)"
                })
                continue
                
            seen_numbers.add(clean_digits)
            valid_rows.append({
                "Name": name,
                "Clean_10_Digit": clean_digits,
                "WhatsApp_Phone": f"91{clean_digits}",
                "Custom_Message": DEFAULT_WA_MESSAGE.format(name=name)
            })
        else:
            invalid_rows.append({
                "Original_Row": idx + 2,
                "Name": name,
                "Raw_Number": str(raw_num),
                "Reason": status
            })

    # Summary
    print("\n" + "="*60)
    print("📊 DATA CLEANING & VALIDATION SUMMARY")
    print("="*60)
    print(f"Total Rows Checked : {len(df)}")
    print(f"✅ Valid 10-Digit Numbers: {len(valid_rows)}")
    print(f"❌ Invalid / Duplicates  : {len(invalid_rows)}")
    print("="*60)

    # 1. Save Cleaned Excel
    if not output_excel:
        output_excel = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/cleaned_creators.xlsx"))
        
    os.makedirs(os.path.dirname(output_excel), exist_ok=True)
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        pd.DataFrame(valid_rows).to_excel(writer, sheet_name="Valid_Creators", index=False)
        if invalid_rows:
            pd.DataFrame(invalid_rows).to_excel(writer, sheet_name="Invalid_Rows", index=False)
            
    print(f"✅ Cleaned Excel saved at: {output_excel}")

    # 2. Update WhatsApp Bulk CSV
    csv_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../branding/whatsapp_creators_export.csv"))
    valid_df = pd.DataFrame(valid_rows)
    export_df = pd.DataFrame({
        "name": valid_df["Name"],
        "phone": valid_df["WhatsApp_Phone"],
        "Custom_Message": valid_df["Custom_Message"]
    })
    export_df.to_csv(csv_out, index=False, encoding="utf-8-sig")
    print(f"✅ Updated WhatsApp Edge CSV at: {csv_out}")

    # 3. Update WhatsApp HTML Launcher
    html_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../branding/whatsapp_outreach_launcher.html"))
    cards_html = []
    for i, r in enumerate(valid_rows, 1):
        wa_url = f"https://wa.me/{r['WhatsApp_Phone']}?text={urllib.parse.quote(r['Custom_Message'])}"
        cards_html.append(f"""
        <tr class="creator-row">
          <td><strong>#{i}</strong></td>
          <td>
            <div style="font-weight:700; color:#FFF;">{r['Name']}</div>
          </td>
          <td><span class="phone-badge">+{r['WhatsApp_Phone']}</span></td>
          <td>
            <a href="{wa_url}" target="_blank" class="wa-btn" onclick="markSent(this)">
              💬 Send WhatsApp ➔
            </a>
          </td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Creator Orbit — WhatsApp Outreach Launcher</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0B0F19;
      --card-bg: #131B2E;
      --primary: #6366F1;
      --wa-green: #25D366;
      --border: #1E293B;
      --text: #F8FAFC;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 40px 20px;
    }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    header {{ text-align: center; margin-bottom: 30px; }}
    h1 {{ font-size: 32px; font-weight: 800; color: #FFF; margin-bottom: 8px; }}
    p.sub {{ color: #94A3B8; font-size: 15px; }}
    
    .stats-bar {{
      display: flex; gap: 20px; justify-content: center; margin-bottom: 30px;
    }}
    .stat-pill {{
      background: var(--card-bg); border: 1px solid var(--border);
      padding: 10px 24px; border-radius: 9999px; font-size: 14px; font-weight: 700;
    }}
    
    .table-card {{
      background: var(--card-bg); border: 1px solid var(--border);
      border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #0E1524; padding: 16px 20px; text-align: left; font-size: 13px; color: #94A3B8; text-transform: uppercase; }}
    td {{ padding: 16px 20px; border-top: 1px solid var(--border); font-size: 14px; }}
    
    .phone-badge {{
      background: rgba(37, 211, 102, 0.12); color: var(--wa-green);
      padding: 4px 10px; border-radius: 6px; font-family: monospace; font-weight: 700;
    }}
    .wa-btn {{
      display: inline-block; background: #25D366; color: #000;
      padding: 8px 16px; border-radius: 8px; font-weight: 800; font-size: 13px;
      text-decoration: none; transition: 0.2s;
    }}
    .wa-btn:hover {{ background: #20BA5A; transform: translateY(-1px); }}
    .wa-btn.sent {{ background: #334155; color: #94A3B8; }}
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>💬 WhatsApp Creator Outreach Launcher</h1>
    <p class="sub">1-Click personalized WhatsApp messages for validated creators.</p>
  </header>

  <div class="stats-bar">
    <div class="stat-pill">👥 Valid Creators: <strong style="color:var(--primary);">{len(valid_rows)}</strong></div>
    <div class="stat-pill">📁 Cleaned Excel: <strong style="color:var(--wa-green);">data/cleaned_creators.xlsx</strong></div>
  </div>

  <div class="table-card">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Creator Name</th>
          <th>WhatsApp Phone</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {"".join(cards_html)}
      </tbody>
    </table>
  </div>
</div>

<script>
function markSent(btn) {{
  btn.classList.add('sent');
  btn.innerHTML = '✅ Sent';
}}
</script>
</body>
</html>
"""
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ Updated 1-Click Interactive Launcher at: {html_out}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean custom creator Excel sheet and validate phone numbers")
    parser.add_argument("file", nargs="?", default="data/custom_creators.xlsx", help="Path to your custom Excel file (e.g. data/my_sheet.xlsx)")
    args = parser.parse_args()
    
    target_file = args.file
    if not os.path.exists(target_file):
        # Check alternative common locations
        candidates = [
            "data/custom_creators.xlsx",
            "data/creators.xlsx",
            "data/creators_list.xlsx",
            "data/Vedant.xlsx"
        ]
        for c in candidates:
            if os.path.exists(c):
                target_file = c
                break
                
    process_excel_file(target_file)

