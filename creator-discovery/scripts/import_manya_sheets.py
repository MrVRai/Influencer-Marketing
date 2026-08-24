import os
import re
import json
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional

def clean_handle(link_or_handle: Any) -> Optional[str]:
    """Extract clean Instagram/YouTube handle from link, text, or @handle."""
    if pd.isna(link_or_handle):
        return None
    val = str(link_or_handle).strip()
    if not val or val.lower() in ['nan', 'none', 'n/a', '-', '']:
        return None
    
    # Instagram URL format
    m = re.search(r'instagram\.com/([a-zA-Z0-9_\.\-]+)', val, re.IGNORECASE)
    if m:
        handle = m.group(1).split('?')[0].strip('/').strip()
        if handle and handle.lower() not in ['p', 'reel', 'stories', 'explore', 'tv', 'reels']:
            return handle.lower()
            
    # YouTube URL format
    m_yt = re.search(r'youtube\.com/(?:c/|channel/|user/|@)?([a-zA-Z0-9_\.\-]+)', val, re.IGNORECASE)
    if m_yt:
        yt_handle = m_yt.group(1).split('?')[0].strip('/').strip()
        if yt_handle:
            return yt_handle.lower()

    # @handle format
    m2 = re.search(r'@([a-zA-Z0-9_\.\-]+)', val)
    if m2:
        clean = m2.group(1).strip()
        if len(clean) >= 2:
            return clean.lower()
            
    # Raw username string (no spaces, reasonable length)
    if ' ' not in val and '.' not in val and len(val) >= 3 and not val.isdigit() and '/' not in val:
        return val.lower().lstrip('@')
        
    return None

def clean_location(val: Any) -> str:
    """Clean city/state names."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.lower() in ['nan', 'none', 'n/a', '-', 'null', '0', '']:
        return ""
    # Remove leading/trailing punctuation and title case
    s = re.sub(r'^[,\-_\s]+|[,\-_\s]+$', '', s)
    return s.title()

def parse_num(val: Any) -> int:
    """Parse follower/view counts like 120k, 1.5M, 15000, 15,000."""
    if pd.isna(val):
        return 0
    s = str(val).strip().lower().replace(',', '').replace('+', '').replace(' ', '')
    try:
        if 'k' in s:
            n = int(float(s.replace('k', '')) * 1000)
        elif 'm' in s or 'cr' in s:
            n = int(float(s.replace('m', '').replace('cr', '')) * 1000000)
        elif s.replace('.', '').isdigit():
            n = int(float(s))
        else:
            return 0
        # Sanity cap: follower count shouldn't exceed 200M (avoids phone number misparsing)
        if n > 200000000:
            return 0
        return n
    except Exception:
        pass
    return 0

def run_master_import():
    excel_path = 'd:/Influencer Marketing/data/Vedant.xlsx'
    db_path = 'd:/Influencer Marketing/creator-discovery/data/creators.db'
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    xls = pd.ExcelFile(excel_path)
    print(f"Loading all {len(xls.sheet_names)} sheets from {excel_path}...")
    
    creators_dict: Dict[str, Dict[str, Any]] = {}
    total_raw_rows = 0
    
    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            if df.empty or len(df.columns) == 0:
                continue
                
            total_raw_rows += len(df)
            
            # Map column names case-insensitively with stripped whitespace
            cols = {str(c).strip().lower(): c for c in df.columns}
            
            # Find specific columns
            link_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['profile link', 'ig link', 'instagram link', 'insta link', 'handle', 'yt link', 'youtube link', 'insta profile', 'instagram profile']):
                    link_col = orig
                    break
            
            name_col = None
            for k, orig in cols.items():
                if 'name' in k and 'poc' not in k:
                    name_col = orig
                    break
                    
            email_col = None
            for k, orig in cols.items():
                if 'email' in k or 'mail' in k:
                    email_col = orig
                    break
                    
            phone_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['contact', 'number', 'phone', 'mobile']):
                    phone_col = orig
                    break
                    
            city_col = None
            for k, orig in cols.items():
                if 'city' in k:
                    city_col = orig
                    break
                    
            state_col = None
            for k, orig in cols.items():
                if 'state' in k:
                    state_col = orig
                    break
                    
            addr_col = None
            for k, orig in cols.items():
                if 'address' in k or 'adrress' in k:
                    addr_col = orig
                    break
                    
            pincode_col = None
            for k, orig in cols.items():
                if 'pin' in k:
                    pincode_col = orig
                    break
                    
            followers_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['follower', 'subscriber', 'subs']):
                    followers_col = orig
                    break
                    
            views_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['view', 'views', 'avr']):
                    views_col = orig
                    break
                    
            cost_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['cost', 'rate', 'price', 'commercial']):
                    cost_col = orig
                    break

            for _, row in df.iterrows():
                # 1. Identify handle
                handle = None
                if link_col:
                    handle = clean_handle(row.get(link_col))
                if not handle and name_col:
                    val = str(row.get(name_col, ''))
                    if 'instagram.com' in val.lower() or 'youtube.com' in val.lower() or val.startswith('@'):
                        handle = clean_handle(val)
                        
                name = str(row.get(name_col, '')).strip() if name_col else ''
                if name.lower() in ['nan', 'none', 'n/a', 'null', '']:
                    name = ''
                    
                email = str(row.get(email_col, '')).strip() if email_col else ''
                if email.lower() in ['nan', 'none', 'n/a', '-', 'null']:
                    email = ''
                    
                phone = str(row.get(phone_col, '')).strip() if phone_col else ''
                if phone.lower() in ['nan', 'none', 'n/a', '-', 'null', '0.0']:
                    phone = ''
                elif phone.endswith('.0'):
                    phone = phone[:-2]
                    
                city = clean_location(row.get(city_col)) if city_col else ''
                state = clean_location(row.get(state_col)) if state_col else ''
                address = str(row.get(addr_col, '')).strip() if addr_col else ''
                if address.lower() in ['nan', 'none', 'n/a', 'null']:
                    address = ''
                pincode = str(row.get(pincode_col, '')).strip() if pincode_col else ''
                if pincode.lower() in ['nan', 'none', 'n/a', 'null', '0.0']:
                    pincode = ''
                elif pincode.endswith('.0'):
                    pincode = pincode[:-2]
                    
                # If city is missing but address is present, check if city can be inferred from address
                if not city and address:
                    addr_lower = address.lower()
                    common_cities = ['delhi', 'mumbai', 'bangalore', 'bengaluru', 'pune', 'hyderabad', 'chennai', 'kolkata', 'ahmedabad', 'jaipur', 'lucknow', 'surat', 'indore', 'chandigarh', 'noida', 'gurgaon', 'gurugram', 'nagpur', 'bhopal', 'patna', 'vadodara', 'ghaziabad', 'ludhiana', 'agra', 'nashik', 'faridabad', 'meerut', 'rajkot', 'varanasi', 'srinagar', 'aurangabad', 'dhanbad', 'amritsar', 'navi mumbai', 'allahabad', 'prayagraj', 'ranchi', 'howrah', 'coimbatore', 'jabalpur', 'gwalior', 'vijayawada', 'jodhpur', 'madurai', 'raipur', 'kota', 'guwahati', 'dehradun', 'mysore', 'mysuru', 'ichalkaranji', 'nainital', 'thane']
                    for cc in common_cities:
                        if cc in addr_lower:
                            city = cc.title()
                            break

                followers = parse_num(row.get(followers_col, 0)) if followers_col else 0
                views = parse_num(row.get(views_col, 0)) if views_col else 0
                cost = str(row.get(cost_col, '')).strip() if cost_col else ''
                
                # Determine Category / Niche
                category = sheet.strip()

                # Determine key for creator
                if handle:
                    key = handle
                elif name and (email or phone or city):
                    key = re.sub(r'[^a-zA-Z0-9_]', '', name.lower().replace(' ', '_'))
                elif email:
                    key = email.split('@')[0].lower()
                elif phone:
                    key = f"creator_{phone}"
                else:
                    continue  # Not enough identifying info

                if not name:
                    name = handle or key.replace('_', ' ').title()

                if key not in creators_dict:
                    creators_dict[key] = {
                        'platform': 'instagram',
                        'platform_id': handle or key,
                        'name': name,
                        'description': f"Niche: {category} | {city} {state}".strip(' | '),
                        'subscriber_count': int(followers),
                        'median_views': int(views if views > 0 else max(int(followers * 0.1), 500)),
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
                        'city': city,
                        'state': state,
                        'address': address,
                        'pincode': pincode,
                        'categories': [category],
                        'costs': [cost] if cost and cost.lower() not in ['nan', 'none', '0'] else [],
                        'source_sheets': [sheet]
                    }
                else:
                    # Comprehensive merge
                    c = creators_dict[key]
                    if followers > c['subscriber_count']:
                        c['subscriber_count'] = int(followers)
                    if views > c['median_views']:
                        c['median_views'] = int(views)
                    if email and not c['bio_email']:
                        c['bio_email'] = email
                    if phone and not c['phone']:
                        c['phone'] = phone
                    if city and not c['city']:
                        c['city'] = city
                    if state and not c['state']:
                        c['state'] = state
                    if address and not c['address']:
                        c['address'] = address
                    if pincode and not c['pincode']:
                        c['pincode'] = pincode
                    if handle and c['platform_id'] == key and not c['platform_id'].startswith('@'):
                        c['platform_id'] = handle
                    if name and c['name'] == c['platform_id']:
                        c['name'] = name
                    if category not in c['categories']:
                        c['categories'].append(category)
                    if sheet not in c['source_sheets']:
                        c['source_sheets'].append(sheet)
                    if cost and cost not in c['costs'] and cost.lower() not in ['nan', 'none', '0']:
                        c['costs'].append(cost)

        except Exception as e:
            print(f"Error processing {sheet}: {e}")

    print(f"\nProcessing Complete!")
    print(f"Total raw rows processed: {total_raw_rows}")
    print(f"Total UNIQUE creators merged: {len(creators_dict)}")
    
    with_city = sum(1 for c in creators_dict.values() if c['city'])
    with_state = sum(1 for c in creators_dict.values() if c['state'])
    with_email = sum(1 for c in creators_dict.values() if c['bio_email'])
    with_phone = sum(1 for c in creators_dict.values() if c['phone'])
    
    print(f"Creators with City: {with_city}")
    print(f"Creators with State: {with_state}")
    print(f"Creators with Email: {with_email}")
    print(f"Creators with Phone: {with_phone}")

    # Upsert into SQLite
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
            'address': c['address'],
            'pincode': c['pincode'],
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
            int(c['subscriber_count']),
            int(c['median_views']),
            float(c['engagement_rate']),
            float(c['consistency_score']),
            float(c['creator_score']),
            c['content_language'],
            c['thumbnail_url'],
            c['country'],
            float(c['estimated_cpm_low']),
            float(c['estimated_cpm_high']),
            json.dumps(extra)
        ))
        imported_count += 1
        
    conn.commit()
    conn.close()
    print(f"Successfully updated {imported_count} creators in database!")

if __name__ == '__main__':
    run_master_import()
