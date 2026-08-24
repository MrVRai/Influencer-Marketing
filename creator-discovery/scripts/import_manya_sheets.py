import os
import re
import json
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional

def clean_handle(link_or_handle: Any) -> Optional[str]:
    """Extract clean Instagram handle from link, text, or @handle."""
    if pd.isna(link_or_handle):
        return None
    val = str(link_or_handle).strip()
    if not val or val.lower() in ['nan', 'none', 'n/a', '-', '']:
        return None
    
    # Clean URL format https://instagram.com/handle/
    m = re.search(r'instagram\.com/([a-zA-Z0-9_\.\-]+)', val, re.IGNORECASE)
    if m:
        handle = m.group(1).split('?')[0].strip('/').strip()
        if handle and handle.lower() not in ['p', 'reel', 'stories', 'explore', 'tv']:
            return handle.lower()
            
    # Clean @handle format
    m2 = re.search(r'@?([a-zA-Z0-9_\.\-]+)', val)
    if m2:
        clean = m2.group(1).strip()
        if len(clean) >= 2 and not clean.isdigit():
            return clean.lower()
    return None

def parse_num(val: Any) -> int:
    """Parse follower/view counts like 120k, 1.5M, 15000, 15,000."""
    if pd.isna(val):
        return 0
    s = str(val).strip().lower().replace(',', '').replace('+', '').replace(' ', '')
    try:
        if 'k' in s:
            return int(float(s.replace('k', '')) * 1000)
        elif 'm' in s or 'cr' in s:
            return int(float(s.replace('m', '').replace('cr', '')) * 1000000)
        elif s.replace('.', '').isdigit():
            return int(float(s))
    except Exception:
        pass
    return 0

def run_import():
    excel_path = 'd:/Influencer Marketing/data/Vedant.xlsx'
    db_path = 'd:/Influencer Marketing/creator-discovery/data/creators.db'
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    xls = pd.ExcelFile(excel_path)
    print(f"Loading {len(xls.sheet_names)} sheets from {excel_path}...")
    
    creators_dict: Dict[str, Dict[str, Any]] = {}
    total_raw_rows = 0
    
    for sheet_idx, sheet in enumerate(xls.sheet_names, 1):
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.columns = [str(c).strip() for c in df.columns]
            total_raw_rows += len(df)
            
            # Identify key columns dynamically
            col_map = {}
            for col in df.columns:
                cl = col.lower()
                if any(k in cl for k in ['instagram profile', 'ig link', 'profile link', 'insta link', 'instagram link', 'ig handle', 'instagram handle']):
                    col_map['ig_link'] = col
                elif any(k in cl for k in ['name', 'creator name', 'influencer name']) and 'poc' not in cl:
                    if 'name' not in col_map:
                        col_map['name'] = col
                elif 'email' in cl:
                    col_map['email'] = col
                elif any(k in cl for k in ['follower', 'subscribers', 'subscriber']):
                    col_map['followers'] = col
                elif any(k in cl for k in ['average view', 'avg views', 'views', 'avg view']):
                    col_map['views'] = col
                elif any(k in cl for k in ['contact number', 'contact no', 'phone', 'mobile']):
                    col_map['phone'] = col
                elif 'city' in cl:
                    col_map['city'] = col
                elif 'state' in cl:
                    col_map['state'] = col
                elif any(k in cl for k in ['cost', 'rate', 'price', 'commercial']):
                    col_map['cost'] = col
                elif 'category' in cl or 'niche' in cl:
                    col_map['category'] = col

            for _, row in df.iterrows():
                # Extract handle
                handle = None
                if 'ig_link' in col_map:
                    handle = clean_handle(row.get(col_map['ig_link']))
                
                # Fallback: check if 'Name' column actually contains a link or handle
                if not handle and 'name' in col_map:
                    val = str(row.get(col_map['name'], ''))
                    if 'instagram.com' in val.lower() or val.startswith('@'):
                        handle = clean_handle(val)
                
                if not handle:
                    continue
                    
                name = str(row.get(col_map.get('name', ''), handle)).strip()
                if name.lower() in ['nan', 'none', '', 'n/a']:
                    name = handle
                    
                followers = parse_num(row.get(col_map.get('followers', 0), 0))
                views = parse_num(row.get(col_map.get('views', 0), 0))
                email = str(row.get(col_map.get('email', ''), '')).strip()
                if email.lower() in ['nan', 'none', 'n/a', '-']:
                    email = ''
                phone = str(row.get(col_map.get('phone', ''), '')).strip()
                if phone.lower() in ['nan', 'none', 'n/a', '-']:
                    phone = ''
                city = str(row.get(col_map.get('city', ''), '')).strip()
                state = str(row.get(col_map.get('state', ''), '')).strip()
                cost = str(row.get(col_map.get('cost', ''), '')).strip()
                
                # Determine Category / Niche from sheet name or category column
                category = str(row.get(col_map.get('category', ''), '')).strip()
                if not category or category.lower() in ['nan', 'none', 'n/a']:
                    category = sheet.strip()

                if handle not in creators_dict:
                    creators_dict[handle] = {
                        'platform': 'instagram',
                        'platform_id': handle,
                        'name': name,
                        'description': f"Niche: {category} | Location: {city} {state}".strip(' | Location: '),
                        'subscriber_count': followers,
                        'median_views': views if views > 0 else max(int(followers * 0.1), 500),
                        'engagement_rate': 3.5,
                        'consistency_score': 85.0,
                        'creator_score': 75.0,
                        'content_language': 'hi',
                        'thumbnail_url': '',
                        'country': 'India',
                        'estimated_cpm_low': 10.0,
                        'estimated_cpm_high': 25.0,
                        'bio_email': email,
                        'phone': phone,
                        'city': city if city.lower() not in ['nan', 'none'] else '',
                        'state': state if state.lower() not in ['nan', 'none'] else '',
                        'categories': [category],
                        'costs': [cost] if cost and cost.lower() not in ['nan', 'none', '0'] else [],
                        'source_sheets': [sheet]
                    }
                else:
                    # Merge data
                    c = creators_dict[handle]
                    if followers > c['subscriber_count']:
                        c['subscriber_count'] = followers
                    if views > c['median_views']:
                        c['median_views'] = views
                    if email and not c['bio_email']:
                        c['bio_email'] = email
                    if phone and not c['phone']:
                        c['phone'] = phone
                    if category not in c['categories']:
                        c['categories'].append(category)
                    if sheet not in c['source_sheets']:
                        c['source_sheets'].append(sheet)
                    if cost and cost not in c['costs'] and cost.lower() not in ['nan', 'none', '0']:
                        c['costs'].append(cost)

        except Exception as e:
            print(f"Error processing sheet {sheet}: {e}")

    print(f"\nProcessing Complete!")
    print(f"Total raw rows across 45 sheets: {total_raw_rows}")
    print(f"Total UNIQUE cleaned creators found: {len(creators_dict)}")
    
    # Save to SQLite
    upsert_sql = """
    INSERT INTO creators (
        platform, platform_id, name, description, subscriber_count, median_views,
        engagement_rate, consistency_score, creator_score, content_language,
        thumbnail_url, country, estimated_cpm_low, estimated_cpm_high, extra_data,
        updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(platform, platform_id) DO UPDATE SET
        name = excluded.name,
        description = excluded.description,
        subscriber_count = max(creators.subscriber_count, excluded.subscriber_count),
        median_views = max(creators.median_views, excluded.median_views),
        extra_data = excluded.extra_data,
        updated_at = CURRENT_TIMESTAMP;
    """
    
    imported_count = 0
    for handle, c in creators_dict.items():
        extra = {
            'bio_email': c['bio_email'],
            'phone': c['phone'],
            'city': c['city'],
            'state': c['state'],
            'categories': c['categories'],
            'commercial_notes': ", ".join(c['costs']),
            'source_sheets': c['source_sheets'],
            'is_verified': False
        }
        
        cur.execute(upsert_sql, (
            c['platform'],
            c['platform_id'],
            c['name'],
            c['description'],
            c['subscriber_count'],
            c['median_views'],
            c['engagement_rate'],
            c['consistency_score'],
            c['creator_score'],
            c['content_language'],
            c['thumbnail_url'],
            c['country'],
            c['estimated_cpm_low'],
            c['estimated_cpm_high'],
            json.dumps(extra)
        ))
        imported_count += 1
        
    conn.commit()
    conn.close()
    print(f"Successfully inserted/updated {imported_count} creators in creators.db!")

if __name__ == '__main__':
    run_import()
