import sqlite3
import json

conn = sqlite3.connect('d:/Influencer Marketing/creator-discovery/data/creators.db')
cur = conn.cursor()
cur.execute('SELECT platform_id, name, extra_data FROM creators LIMIT 30')
rows = cur.fetchall()

print("=== Sample 30 Creators in DB ===")
for r in rows:
    extra = json.loads(r[2]) if r[2] else {}
    city = extra.get('city', '')
    state = extra.get('state', '')
    print(f"Handle: @{r[0]} | Name: {r[1]} | City: '{city}' | State: '{state}'")

cur.execute('SELECT COUNT(*) FROM creators')
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM creators WHERE extra_data LIKE '%\"city\": \"\"%' AND extra_data LIKE '%\"state\": \"\"%'")
empty_count = cur.fetchone()[0]

print(f"\nTotal: {total} | Empty City/State: {empty_count} | Has City/State: {total - empty_count}")
