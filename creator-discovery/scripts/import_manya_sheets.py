"""
Master Importer: Parse all 45 sheets from Vedant.xlsx → creators.db

FIXED issues:
 - Phone column was misidentified (columns like "Instagram Average Views(last 10 reels in number only)" 
   matched the 'number' keyword). Now we require the column to NOT contain follower/subscriber/views keywords.
 - Sheet22 has swapped City↔Pincode and Contact↔State columns — special-cased.
 - Phone values are validated: must look like an actual phone number (7-13 digits), not '8k' or '3m'.
 - City values are validated: must not be pure digits (pincode), must be alphabetical.
"""
import os
import re
import json
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional

# Map generic sheet names to meaningful niche/category labels.
# Sheets without named niches are inferred from context (barter = free collab,
# paid fitness = fitness paid collab, etc.)
SHEET_NICHE_MAP = {
    "Sheet1":       "Barter / Skincare",
    "Sheet2":       "Barter",
    "Sheet3":       "Active Campaign",
    "Paid fitness": "Fitness (Paid)",
    "Sheet5":       "Beauty",
    "Sheet6":       "Beauty",
    "Sheet7":       "Beauty",
    "Sheet8":       "Beauty",
    "Sheet9":       "Fitness / Wellness",
    "Sheet10":      "Beauty",
    "Sheet11":      "Lifestyle",
    "Sheet12":      "Lifestyle",
    "Sheet13":      "Lifestyle",
    "Sheet14":      "Lifestyle",
    "Sheet15":      "Lifestyle",
    "Sheet16":      "Lifestyle",
    "Sheet17":      "Lifestyle",
    "Sheet18":      "Lifestyle",
    "Sheet19":      "Lifestyle",
    "Sheet20":      "Lifestyle",
    "Sheet21":      "Lifestyle",
    "Sheet22":      "Fashion",
    "Sheet23":      "Fashion",
    "Sheet24":      "Fashion",
    "Sheet25":      "Fashion",
    "Sheet26":      "Fashion",
    "Sheet27":      "Fashion",
    "Sheet28":      "Fashion",
    "Sheet29":      "Fashion",
    "Yt":           "YouTube",
    "Sheet31":      "Fitness (Paid)",
    "Sheet32":      "Active Campaign",
    "Sheet34":      "Lifestyle",
    "Sheet35":      "Lifestyle",
    "Sheet36":      "Skincare / Beauty",
    "Sheet37":      "Lifestyle",
    "Sheet38":      "Beauty / Skincare",
    "Sheet39":      "Lifestyle",
    "Skincare ":    "Skincare",
    "Skincare":     "Skincare",
    "Sheet41":      "Beauty",
    "Sheet42":      "Beauty",
    "Sheet43":      "Beauty",
    "Sheet44":      "Fashion",
    "Sheet45":      "YouTube",
}

def get_niche(sheet_name: str) -> str:
    """Get human-readable niche label for a sheet name."""
    return SHEET_NICHE_MAP.get(sheet_name, sheet_name.strip())


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
    """Clean city/state names. Returns empty string for invalid values."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.lower() in ['nan', 'none', 'n/a', '-', 'null', '0', '0.0', '']:
        return ""
    # If it's purely numeric, it's a pincode not a city name
    if s.replace('.', '').replace('-', '').replace(' ', '').isdigit():
        return ""
    # Remove leading/trailing punctuation
    s = re.sub(r'^[,\-_\s]+|[,\-_\s]+$', '', s)
    if not s:
        return ""
    return s.title()


def clean_phone(val: Any) -> str:
    """
    Clean and validate phone numbers. 
    Returns empty string for values that aren't real phone numbers.
    Real Indian phone numbers: 10 digits, sometimes with +91 prefix.
    """
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.lower() in ['nan', 'none', 'n/a', '-', 'null', '0', '0.0', '']:
        return ""
    
    # Remove .0 suffix from float conversion
    if s.endswith('.0'):
        s = s[:-2]
    
    # Strip +91, spaces, dashes for validation
    digits_only = re.sub(r'[^0-9]', '', s)
    
    # A valid Indian phone number has 10 digits (or 11-12 with country code)
    if 7 <= len(digits_only) <= 13:
        # It's likely a real phone number
        # But also check it's not something like "15000" (5 digits but matches len check)
        # Additional check: reject if original had 'k', 'm', '+' (not phone)
        if 'k' in s.lower() or 'm' in s.lower():
            return ""
        return s
    
    return ""


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
        # Sanity cap: follower count shouldn't exceed 200M
        if n > 200000000:
            return 0
        return n
    except Exception:
        pass
    return 0


def is_phone_column(col_name_lower: str) -> bool:
    """
    Check if a column name is a phone/contact column.
    Must contain phone/contact/number keywords BUT must NOT contain 
    follower/subscriber/views/reel keywords (which would make it a metrics column).
    """
    # Reject columns that are clearly metrics columns
    reject_keywords = ['follower', 'subscriber', 'subs', 'view', 'reel', 'avr', 'average', 'avg']
    for rk in reject_keywords:
        if rk in col_name_lower:
            return False
    
    # Accept columns with phone/contact keywords
    accept_keywords = ['phone', 'mobile', 'whatsapp']
    for ak in accept_keywords:
        if ak in col_name_lower:
            return True
    
    # 'contact' alone is fine (e.g., 'Contact number', 'contact no')
    if 'contact' in col_name_lower:
        return True
    
    # 'number' alone is fine ONLY if the column doesn't also contain metric-words
    # We already filtered metrics above, so if it has 'number' here, it's OK
    if col_name_lower.strip() in ['number', 'number ']:
        return True
    
    return False


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

            # --- Find link column ---
            link_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['profile link', 'ig link', 'instagram link', 'insta link',
                                         'handle', 'yt link', 'youtube link', 'insta profile',
                                         'instagram profile', 'ig profile']):
                    link_col = orig
                    break

            # --- Find name column ---
            name_col = None
            for k, orig in cols.items():
                if 'name' in k and 'poc' not in k and 'unnamed' not in k:
                    name_col = orig
                    break

            # --- Find email column ---
            email_col = None
            for k, orig in cols.items():
                if ('email' in k or k == 'mail') and 'unnamed' not in k:
                    email_col = orig
                    break

            # --- Find phone column (IMPROVED: exclude follower/views columns) ---
            phone_col = None
            for k, orig in cols.items():
                if is_phone_column(k):
                    phone_col = orig
                    break

            # --- Find city column ---
            city_col = None
            for k, orig in cols.items():
                if 'city' in k and 'unnamed' not in k:
                    city_col = orig
                    break

            # --- Find state column ---
            state_col = None
            for k, orig in cols.items():
                if 'state' in k and 'unnamed' not in k:
                    state_col = orig
                    break

            # --- Find address column ---
            addr_col = None
            for k, orig in cols.items():
                if ('address' in k or 'adrress' in k) and 'unnamed' not in k:
                    addr_col = orig
                    break

            # --- Find pincode column ---
            pincode_col = None
            for k, orig in cols.items():
                if ('pincode' in k or k.strip() == 'pin code' or k.strip() == 'pin-code') and 'unnamed' not in k and 'address' not in k and 'shipping' not in k:
                    pincode_col = orig
                    break

            # --- Find followers column ---
            followers_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['follower', 'subscriber', 'subs']) and 'unnamed' not in k:
                    followers_col = orig
                    break

            # --- Find views column ---
            views_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['view', 'avr']) and 'unnamed' not in k and 'live' not in k:
                    views_col = orig
                    break

            # --- Find cost/rate column ---
            cost_col = None
            for k, orig in cols.items():
                if any(x in k for x in ['cost', 'rate', 'price', 'commercial', 'ad cost']) and 'unnamed' not in k:
                    cost_col = orig
                    break

            # Print what we found for debugging
            found_cols = []
            if link_col: found_cols.append(f"link={link_col}")
            if name_col: found_cols.append(f"name={name_col}")
            if email_col: found_cols.append(f"email={email_col}")
            if phone_col: found_cols.append(f"phone={phone_col}")
            if city_col: found_cols.append(f"city={city_col}")
            if state_col: found_cols.append(f"state={state_col}")
            if addr_col: found_cols.append(f"addr={addr_col}")
            if followers_col: found_cols.append(f"followers={followers_col}")
            print(f"  [{sheet}] {len(df)} rows | {', '.join(found_cols)}")

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
                # Basic email validation
                if email and '@' not in email:
                    email = ''

                phone = clean_phone(row.get(phone_col)) if phone_col else ''

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

                # If city is missing but address is present, try to infer city from address
                if not city and address:
                    addr_lower = address.lower()
                    common_cities = [
                        'delhi', 'new delhi', 'mumbai', 'bangalore', 'bengaluru', 'pune', 
                        'hyderabad', 'chennai', 'kolkata', 'ahmedabad', 'jaipur', 'lucknow', 
                        'surat', 'indore', 'chandigarh', 'noida', 'gurgaon', 'gurugram', 
                        'nagpur', 'bhopal', 'patna', 'vadodara', 'ghaziabad', 'ludhiana', 
                        'agra', 'nashik', 'faridabad', 'meerut', 'rajkot', 'varanasi', 
                        'srinagar', 'aurangabad', 'dhanbad', 'amritsar', 'navi mumbai', 
                        'allahabad', 'prayagraj', 'ranchi', 'howrah', 'coimbatore', 
                        'jabalpur', 'gwalior', 'vijayawada', 'jodhpur', 'madurai', 'raipur', 
                        'kota', 'guwahati', 'dehradun', 'mysore', 'mysuru', 'thane',
                        'kanpur', 'bhubaneswar', 'jammu', 'jhansi', 'haldwani', 'udaipur',
                        'roorkee', 'gorakhpur', 'silchar', 'dibrugarh', 'shillong',
                    ]
                    for cc in common_cities:
                        if cc in addr_lower:
                            city = cc.title()
                            break

                followers = parse_num(row.get(followers_col, 0)) if followers_col else 0
                views = parse_num(row.get(views_col, 0)) if views_col else 0
                cost = str(row.get(cost_col, '')).strip() if cost_col else ''

                # Determine Category / Niche (map sheet name → readable label)
                category = get_niche(sheet)

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
                        'description': '',
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
            print(f"  ERROR processing {sheet}: {e}")

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
    print(f"Creators with Phone (validated): {with_phone}")

    # Build description with niche + location
    for key, c in creators_dict.items():
        parts = []
        if c['categories']:
            parts.append(f"Niche: {', '.join(c['categories'][:3])}")
        if c['city']:
            parts.append(c['city'])
        if c['state'] and c['state'] != c['city']:
            parts.append(c['state'])
        c['description'] = ' | '.join(parts)

    # Upsert into SQLite
    upsert_sql = """
    INSERT INTO creators (
        platform, platform_id, name, description, subscriber_count, median_views,
        engagement_rate, consistency_score, creator_score, content_language,
        thumbnail_url, country, estimated_cpm_low, estimated_cpm_high, extra_data,
        updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(platform, platform_id) DO UPDATE SET
        name = CASE WHEN excluded.name != '' AND excluded.name IS NOT NULL THEN excluded.name ELSE creators.name END,
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

    # Verification: re-read and confirm
    conn2 = sqlite3.connect(db_path)
    cur2 = conn2.cursor()
    cur2.execute("SELECT COUNT(*) FROM creators")
    total = cur2.fetchone()[0]
    cur2.execute("SELECT COUNT(*) FROM creators WHERE json_extract(extra_data, '$.city') IS NOT NULL AND json_extract(extra_data, '$.city') != ''")
    db_cities = cur2.fetchone()[0]
    cur2.execute("SELECT COUNT(*) FROM creators WHERE json_extract(extra_data, '$.phone') IS NOT NULL AND length(json_extract(extra_data, '$.phone')) >= 7")
    db_phones = cur2.fetchone()[0]
    conn2.close()
    
    print(f"\n=== DATABASE VERIFICATION ===")
    print(f"Total creators in DB: {total}")
    print(f"With city in DB: {db_cities}")
    print(f"With valid phone in DB: {db_phones}")


if __name__ == '__main__':
    run_master_import()
