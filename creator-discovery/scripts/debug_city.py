"""Check what categories look like and what clean niche labels should be."""
import sqlite3, json

db_path = 'd:/Influencer Marketing/creator-discovery/data/creators.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT extra_data FROM creators WHERE json_extract(extra_data,'$.categories') IS NOT NULL LIMIT 100")
rows = cur.fetchall()

all_cats = {}
for row in rows:
    ed = json.loads(row['extra_data'])
    for cat in ed.get('categories', []):
        all_cats[cat] = all_cats.get(cat, 0) + 1

print("All category values (top 50):")
for cat, count in sorted(all_cats.items(), key=lambda x: -x[1])[:50]:
    print(f"  {count:3d}x  {cat!r}")
