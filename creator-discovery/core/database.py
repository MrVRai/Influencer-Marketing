import sqlite3
import os
import json
import datetime
from typing import Optional, List, Dict, Any

class CreatorDatabase:
    """SQLite database layer for storing creator data, sponsorship data, and campaign rosters."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database connection and ensure tables exist."""
        if db_path is None:
            self.db_path = 'd:/Influencer Marketing/creator-discovery/data/creators.db'
        else:
            self.db_path = db_path
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        """Helper to get a database connection with dict-like row access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create tables if they do not exist."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Creators table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS creators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    platform_id TEXT NOT NULL,
                    name TEXT,
                    description TEXT,
                    subscriber_count INTEGER,
                    median_views INTEGER,
                    engagement_rate REAL,
                    consistency_score REAL,
                    creator_score REAL,
                    content_language TEXT,
                    thumbnail_url TEXT,
                    country TEXT,
                    estimated_cpm_low REAL,
                    estimated_cpm_high REAL,
                    extra_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, platform_id)
                )
            ''')
            
            # Sponsors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sponsors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL,
                    brand_name TEXT NOT NULL,
                    source TEXT,
                    promo_code TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(creator_id) REFERENCES creators(id)
                )
            ''')
            
            # Campaign rosters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaign_rosters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Campaign creators table (junction table)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaign_creators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    creator_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'shortlisted',
                    notes TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(campaign_id) REFERENCES campaign_rosters(id),
                    FOREIGN KEY(creator_id) REFERENCES creators(id)
                )
            ''')
            conn.commit()

    def upsert_creator(self, data: Dict[str, Any]) -> int:
        """
        Insert or update (on conflict platform+platform_id) a creator.
        Returns the creator id.
        """
        platform = data.get('platform')
        platform_id = data.get('platform_id')
        
        if not platform or not platform_id:
            raise ValueError("Both 'platform' and 'platform_id' are required in data.")

        extra_data = data.get('extra_data')
        if isinstance(extra_data, dict):
            extra_data = json.dumps(extra_data)

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO creators (
                    platform, platform_id, name, description, subscriber_count,
                    median_views, engagement_rate, consistency_score, creator_score,
                    content_language, thumbnail_url, country, estimated_cpm_low,
                    estimated_cpm_high, extra_data, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(platform, platform_id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    subscriber_count=excluded.subscriber_count,
                    median_views=excluded.median_views,
                    engagement_rate=excluded.engagement_rate,
                    consistency_score=excluded.consistency_score,
                    creator_score=excluded.creator_score,
                    content_language=excluded.content_language,
                    thumbnail_url=excluded.thumbnail_url,
                    country=excluded.country,
                    estimated_cpm_low=excluded.estimated_cpm_low,
                    estimated_cpm_high=excluded.estimated_cpm_high,
                    extra_data=excluded.extra_data,
                    updated_at=CURRENT_TIMESTAMP
            ''', (
                platform, platform_id, data.get('name'), data.get('description'),
                data.get('subscriber_count'), data.get('median_views'), data.get('engagement_rate'),
                data.get('consistency_score'), data.get('creator_score'), data.get('content_language'),
                data.get('thumbnail_url'), data.get('country'), data.get('estimated_cpm_low'),
                data.get('estimated_cpm_high'), extra_data
            ))
            conn.commit()
            
            # Fetch the ID of the upserted row
            cursor.execute('SELECT id FROM creators WHERE platform = ? AND platform_id = ?', 
                           (platform, platform_id))
            row = cursor.fetchone()
            return row['id']

    def add_sponsor(self, creator_id: int, brand_name: str, source: str, promo_code: Optional[str] = None):
        """Insert sponsor record."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sponsors (creator_id, brand_name, source, promo_code)
                VALUES (?, ?, ?, ?)
            ''', (creator_id, brand_name, source, promo_code))
            conn.commit()

    def search_creators(self, platform: Optional[str] = None, language: Optional[str] = None,
                        min_subscribers: Optional[int] = None, max_subscribers: Optional[int] = None,
                        min_engagement: Optional[float] = None, min_views: Optional[int] = None,
                        sort_by: str = 'creator_score', limit: int = 50) -> List[Dict[str, Any]]:
        """Query creators with optional filters. Returns list of dicts."""
        query = "SELECT * FROM creators WHERE 1=1"
        params = []

        if platform:
            query += " AND platform = ?"
            params.append(platform)
        if language:
            query += " AND content_language = ?"
            params.append(language)
        if min_subscribers is not None:
            query += " AND subscriber_count >= ?"
            params.append(min_subscribers)
        if max_subscribers is not None:
            query += " AND subscriber_count <= ?"
            params.append(max_subscribers)
        if min_engagement is not None:
            query += " AND engagement_rate >= ?"
            params.append(min_engagement)
        if min_views is not None:
            query += " AND median_views >= ?"
            params.append(min_views)

        # Allow simple safe sorting
        valid_sort_columns = {'creator_score', 'subscriber_count', 'median_views', 'engagement_rate', 'created_at'}
        if sort_by in valid_sort_columns:
            query += f" ORDER BY {sort_by} DESC"
        else:
            query += " ORDER BY creator_score DESC"

        query += " LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_creator_sponsors(self, creator_id: int) -> List[Dict[str, Any]]:
        """Get all sponsors for a creator."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sponsors WHERE creator_id = ? ORDER BY detected_at DESC", (creator_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def create_campaign(self, name: str) -> int:
        """Create campaign roster, return id."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO campaign_rosters (campaign_name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid

    def add_to_campaign(self, campaign_id: int, creator_id: int, notes: str = ''):
        """Add creator to campaign."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO campaign_creators (campaign_id, creator_id, notes)
                VALUES (?, ?, ?)
            ''', (campaign_id, creator_id, notes))
            conn.commit()

    def get_campaign_creators(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Get all creators in a campaign with their details (JOIN)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, cc.status, cc.notes, cc.added_at
                FROM creators c
                JOIN campaign_creators cc ON c.id = cc.creator_id
                WHERE cc.campaign_id = ?
            ''', (campaign_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_campaigns(self) -> List[Dict[str, Any]]:
        """List all campaigns."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaign_rosters ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_creator_by_platform_id(self, platform: str, platform_id: str) -> Optional[Dict[str, Any]]:
        """Find a specific creator."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM creators WHERE platform = ? AND platform_id = ?", (platform, platform_id))
            row = cursor.fetchone()
            return dict(row) if row else None
