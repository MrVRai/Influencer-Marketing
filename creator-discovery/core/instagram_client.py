import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load .env from project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)


class InstagramClient:
    """High-reliability client for fetching Instagram creator data using Apify's official instagram-scraper."""

    def __init__(self) -> None:
        """Initialize the InstagramClient with Apify token."""
        token = os.environ.get('APIFY_API_TOKEN')
        if token:
            try:
                self.client = ApifyClient(token)
                self.api_available = True
            except Exception:
                self.client = None
                self.api_available = False
        else:
            self.client = None
            self.api_available = False

    def _get_dataset_id(self, run: Any) -> Optional[str]:
        """Extract default dataset ID from Apify Run object or dict."""
        if not run:
            return None
        if hasattr(run, 'default_dataset_id') and run.default_dataset_id:
            return run.default_dataset_id
        if hasattr(run, 'defaultDatasetId') and run.defaultDatasetId:
            return run.defaultDatasetId
        if isinstance(run, dict):
            return run.get('defaultDatasetId') or run.get('default_dataset_id')
        return None

    def _parse_profile_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Apify Instagram item into standardized creator profile dict."""
        username = item.get('username') or item.get('ownerUsername') or ''
        full_name = item.get('fullName') or item.get('name') or username
        biography = item.get('biography') or item.get('bio') or ''

        # Email extraction from biography
        bio_email = None
        if biography:
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', biography)
            if email_match:
                bio_email = email_match.group(0)

        # Standardize follower counts
        followers = item.get('followersCount') or item.get('followers') or item.get('follower_count') or 0
        following = item.get('followsCount') or item.get('following') or item.get('following_count') or 0
        posts_count = item.get('postsCount') or item.get('posts') or item.get('post_count') or 0

        # Extract latest posts attached directly to profile
        raw_posts = item.get('latestPosts') or item.get('posts') or []
        parsed_posts = []
        if isinstance(raw_posts, list):
            for p in raw_posts:
                if isinstance(p, dict):
                    caption = p.get('caption') or ''
                    hashtags = ['#' + h for h in re.findall(r'#(\w+)', caption)]
                    parsed_posts.append({
                        'post_id': p.get('id') or p.get('shortCode') or '',
                        'caption': caption,
                        'like_count': int(p.get('likesCount') or p.get('likes') or 0),
                        'comment_count': int(p.get('commentsCount') or p.get('comments') or 0),
                        'timestamp': p.get('timestamp') or '',
                        'media_type': p.get('type') or 'Post',
                        'hashtags': hashtags,
                        'view_count': int(p.get('videoViewCount') or p.get('videoViews') or (int(p.get('likesCount') or 0) * 10))
                    })

        return {
            'username': username,
            'full_name': full_name,
            'biography': biography,
            'follower_count': int(followers),
            'following_count': int(following),
            'post_count': int(posts_count),
            'profile_pic_url': item.get('profilePicUrl') or item.get('profilePicUrlHD') or '',
            'is_verified': bool(item.get('verified') or item.get('isVerified') or False),
            'external_url': item.get('externalUrl') or '',
            'bio_email': bio_email,
            'posts': parsed_posts
        }

    def _build_query_variations(self, query: str) -> List[str]:
        """
        Build multiple search query variations from a base query to maximise candidate pool.
        Instagram's internal search is limited per query (~18-30 results), so we run
        multiple targeted variations to collect a larger diverse set of creators.
        """
        base = query.strip().lower()
        words = base.split()
        variations = [base]

        # Modifier sets that help find regional & niche micro-creators
        location_prefixes = ['indian', 'india', 'hindi', 'desi', 'mumbai', 'delhi']
        niche_suffixes = ['creator', 'influencer', 'blogger', 'coach', 'tips', 'vlog']
        content_words = ['reels', 'lifestyle', 'content', 'page', 'official']

        for prefix in location_prefixes:
            if prefix not in base:
                variations.append(f"{prefix} {base}")
                variations.append(f"{base} {prefix}")

        for suffix in niche_suffixes:
            if suffix not in base:
                variations.append(f"{base} {suffix}")

        for cw in content_words:
            if cw not in base:
                variations.append(f"{base} {cw}")

        # If multi-word, also try individual important words
        if len(words) > 1:
            for w in words:
                if len(w) > 3:
                    variations.append(w)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for v in variations:
            if v not in seen:
                seen.add(v)
                unique.append(v)
        return unique

    def search_profiles(self, query: str, max_results: int = 20, fetch_limit: int = None,
                        progress_callback=None) -> List[Dict[str, Any]]:
        """
        Search for Instagram creators by keyword or username.
        Runs multiple query variations in rounds to build a large candidate pool
        so that filters (follower tier, language, email) can find the desired count.

        Args:
            query: Search term or @handle
            max_results: Desired number of *matching* profiles (after filters)
            fetch_limit: Total raw candidates to collect across all rounds
            progress_callback: Optional callable(round_num, total_rounds, query_used, found_so_far)
        """
        if not self.api_available or not self.client:
            return []

        query_raw = query.strip()
        is_direct_handle = query_raw.startswith('@')
        query_clean = query_raw.lstrip('@').strip()
        all_results: List[Dict[str, Any]] = []
        seen_usernames: set = set()

        # For direct handle lookups, just fetch that one profile
        if is_direct_handle:
            try:
                input_data = {
                    'directUrls': [f'https://www.instagram.com/{query_clean}/'],
                    'resultsType': 'details',
                    'resultsLimit': 1
                }
                run = self.client.actor('apify/instagram-scraper').call(run_input=input_data)
                dataset_id = self._get_dataset_id(run)
                if dataset_id:
                    for item in self.client.dataset(dataset_id).iterate_items():
                        if item.get('username'):
                            all_results.append(self._parse_profile_item(item))
            except Exception as e:
                print(f"Error fetching Instagram handle {query_clean}: {e}")
            return all_results

        # Target: collect at least (max_results * 5) raw candidates, minimum 80
        target_pool = fetch_limit if fetch_limit else max(max_results * 5, 80)
        per_round_limit = 30  # Apify user search reliably returns ~18-30 per query

        # Build a diverse set of query variations
        query_variations = self._build_query_variations(query_clean)
        total_rounds = len(query_variations)

        for round_num, variant in enumerate(query_variations, start=1):
            # Stop if we have enough candidates
            if len(all_results) >= target_pool:
                break

            if progress_callback:
                progress_callback(round_num, total_rounds, variant, len(all_results))

            try:
                input_data = {
                    'search': variant,
                    'searchType': 'user',
                    'searchLimit': per_round_limit,
                    'resultsType': 'details',
                    'resultsLimit': per_round_limit
                }
                run = self.client.actor('apify/instagram-scraper').call(run_input=input_data)
                dataset_id = self._get_dataset_id(run)
                if dataset_id:
                    for item in self.client.dataset(dataset_id).iterate_items():
                        uname = item.get('username', '')
                        if uname and uname not in seen_usernames:
                            seen_usernames.add(uname)
                            all_results.append(self._parse_profile_item(item))
            except Exception as e:
                print(f"Error in search round {round_num} (query='{variant}'): {e}")
                continue

        return all_results

    def search_by_hashtag(self, hashtag: str, max_results: int = 20, fetch_limit: int = None) -> List[Dict[str, Any]]:
        """
        Search for Instagram creators by hashtag.
        Fetches top/recent posts for the hashtag and looks up creator profiles.
        Scrapes a wider pool (fetch_limit) to ensure enough matching profiles after filtering.
        """
        if not self.api_available or not self.client:
            return []

        hashtag = hashtag.strip().lstrip('#')
        results: List[Dict[str, Any]] = []
        pool_size = fetch_limit if fetch_limit else max(max_results * 5, 50)

        try:
            # Scrape posts with the hashtag
            input_data = {
                'directUrls': [f'https://www.instagram.com/explore/tags/{hashtag}/'],
                'resultsType': 'posts',
                'resultsLimit': pool_size
            }
            run = self.client.actor('apify/instagram-scraper').call(run_input=input_data)
            dataset_id = self._get_dataset_id(run)

            if not dataset_id:
                return []

            seen_usernames: set = set()
            hashtag_creators = []

            for item in self.client.dataset(dataset_id).iterate_items():
                owner = item.get('ownerUsername') or item.get('owner', {}).get('username') or ''
                if owner and owner not in seen_usernames:
                    seen_usernames.add(owner)
                    caption = item.get('caption') or ''
                    likes = int(item.get('likesCount') or item.get('likes') or 0)
                    comments = int(item.get('commentsCount') or item.get('comments') or 0)

                    # Extract any business emails mentioned in post caption
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', caption)
                    bio_email = email_match.group(0) if email_match else None

                    # Estimate follower count based on typical 2.5% Instagram engagement rate
                    estimated_followers = max(int(likes * 40), int(comments * 500), 15000)

                    creator_dict = {
                        'username': owner,
                        'full_name': owner,
                        'biography': caption[:150] if caption else '',
                        'follower_count': estimated_followers,
                        'following_count': 0,
                        'post_count': 1,
                        'profile_pic_url': item.get('displayUrl') or '',
                        'is_verified': bool(item.get('isVerified', False)),
                        'external_url': '',
                        'bio_email': bio_email,
                        'posts': [{
                            'post_id': item.get('id') or item.get('shortCode') or '',
                            'caption': caption,
                            'like_count': likes,
                            'comment_count': comments,
                            'timestamp': item.get('timestamp') or '',
                            'media_type': item.get('type') or 'Post',
                            'hashtags': ['#' + h for h in re.findall(r'#(\w+)', caption)],
                            'view_count': int(item.get('videoViewCount') or (likes * 10))
                        }]
                    }
                    hashtag_creators.append(creator_dict)

            return hashtag_creators

        except Exception as e:
            print(f"Error searching Instagram by hashtag: {e}")
            return results

    def get_profile_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Look up a single Instagram profile with details and recent posts."""
        if not self.api_available or not self.client:
            return None

        username = username.strip().lstrip('@')
        try:
            input_data = {
                'directUrls': [f'https://www.instagram.com/{username}/'],
                'resultsType': 'details',
                'resultsLimit': 1
            }
            run = self.client.actor('apify/instagram-scraper').call(run_input=input_data)
            dataset_id = self._get_dataset_id(run)
            if dataset_id:
                for item in self.client.dataset(dataset_id).iterate_items():
                    if item.get('username'):
                        return self._parse_profile_item(item)
            return None
        except Exception as e:
            print(f"Error getting Instagram profile for {username}: {e}")
            return None
