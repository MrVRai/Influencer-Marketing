"""
WhatsApp Outreach Helper & Launcher Generator for Creator Orbit
Automates WhatsApp outreach to creators from database/Excel.

Features:
- Validates & cleans Indian phone numbers (10 digits -> 91XXXXXXXXXX)
- Exports clean CSV for WA Web Plus / WAPlus CRM Chrome extensions
- Generates an interactive web launcher (branding/whatsapp_outreach_launcher.html) with 1-click WhatsApp links
"""

import os
import sys
import re
import json
import sqlite3
import urllib.parse
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/creators.db"))
CSV_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../branding/whatsapp_creators_export.csv"))
HTML_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../branding/whatsapp_outreach_launcher.html"))

DEFAULT_WA_MESSAGE = """Hey {name}! Team Creator Orbit here 👋✨

Hope you're doing great!

We’re curating a fresh creator roster for upcoming Beauty & Skincare PR hampers and barter brand campaigns at *Creator Orbit* 🎁

Make sure to follow our Instagram page so we can shortlist you for upcoming brand drops:
👉 https://instagram.com/thecreatororbit

Drop a quick "Done" here after following so we can add you to our priority list! 💙"""

def clean_phone_number(raw_phone):
    if not raw_phone or pd.isna(raw_phone):
        return None
    s = str(raw_phone).strip()
    s = re.sub(r'[^0-9]', '', s)
    
    # Check Indian number formats
    if len(s) == 10:
        return f"91{s}"
    elif len(s) == 11 and s.startswith('0'):
        return f"91{s[1:]}"
    elif len(s) == 12 and s.startswith('91'):
        return s
    elif len(s) >= 10 and len(s) <= 13:
        return s
    return None

def extract_whatsapp_creators():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, platform_id, description, extra_data FROM creators WHERE extra_data IS NOT NULL")
    rows = cur.fetchall()
    conn.close()
    
    creators = []
    seen_phones = set()
    
    for cid, name, platform_id, desc, extra_json in rows:
        try:
            extra = json.loads(extra_json)
        except:
            continue
            
        raw_phone = extra.get("phone")
        clean_phone = clean_phone_number(raw_phone)
        
        if not clean_phone or clean_phone in seen_phones:
            continue
            
        seen_phones.add(clean_phone)
        
        handle = platform_id if platform_id else (name or "Creator")
        creator_name = name if name and name.lower() != "none" and not name.startswith("http") else handle
        city = extra.get("city", "")
        
        creators.append({
            "id": cid,
            "name": creator_name,
            "handle": handle,
            "phone": clean_phone,
            "city": city,
            "niche": ", ".join(extra.get("categories", [])[:2]) or "Beauty & Skincare"
        })
        
    return creators

def generate_outputs():
    creators = extract_whatsapp_creators()
    print(f"\n📱 Found {len(creators)} creators with valid WhatsApp phone numbers!")
    
    if not creators:
        print("No creators with phone numbers found.")
        return
        
    # 1. Export CSV for Chrome Extension
    df = pd.DataFrame(creators)
    df["Custom_Message"] = df.apply(lambda r: DEFAULT_WA_MESSAGE.format(name=r["name"]), axis=1)
    df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    print(f"✅ Exported CSV for WA Web Plus / Chrome Extension at: {CSV_OUT}")
    
    # 2. Generate Interactive HTML 1-Click Launcher
    cards_html = []
    for i, c in enumerate(creators, 1):
        msg = DEFAULT_WA_MESSAGE.format(name=c["name"])
        wa_url = f"https://wa.me/{c['phone']}?text={urllib.parse.quote(msg)}"
        
        cards_html.append(f"""
        <tr class="creator-row">
          <td><strong>#{i}</strong></td>
          <td>
            <div style="font-weight:700; color:#FFF;">{c['name']}</div>
            <div style="font-size:12px; color:#94A3B8;">@{c['handle']} &bull; {c['city']}</div>
          </td>
          <td><span class="phone-badge">+{c['phone']}</span></td>
          <td><span class="niche-tag">{c['niche']}</span></td>
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
    .container {{ max-width: 1100px; margin: 0 auto; }}
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
    .niche-tag {{
      background: rgba(99, 102, 241, 0.12); color: #A5B4FC;
      padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600;
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
    <p class="sub">1-Click personalized WhatsApp messages for the Creator Orbit network.</p>
  </header>

  <div class="stats-bar">
    <div class="stat-pill">👥 Total Creators: <strong style="color:var(--primary);">{len(creators)}</strong></div>
    <div class="stat-pill">📁 CSV File: <a href="whatsapp_creators_export.csv" download style="color:var(--wa-green); text-decoration:none;">⬇️ Download CSV</a></div>
  </div>

  <div class="table-card">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Creator</th>
          <th>WhatsApp Phone</th>
          <th>Niche</th>
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
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ Generated 1-Click Interactive WhatsApp Launcher at: {HTML_OUT}")

if __name__ == "__main__":
    generate_outputs()

