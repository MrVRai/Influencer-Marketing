import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load .env from the project root (assuming core is 2 levels deep)
# d:/Influencer Marketing/creator-discovery/core/instagram_client.py
# .env is typically at d:/Influencer Marketing/creator-discovery/.env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

class InstagramClient:
    """Client for fetching Instagram creator data using Apify."""
    
    def __init__(self) -> None:
        """Initialize the InstagramClient with Apify token."""
        token = os.environ.get('APIFY_API_TOKEN')
        if token:
            self.client = ApifyClient(token)
            self.api_available = True
        else:
            self.client = None
            self.api_available = False

    def search_profiles(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for Instagram profiles based on a query.
        
        Args:
            query (str): The search query (e.g., username or keyword).
            max_results (int, optional): Maximum number of results to return. Defaults to 20.
            
        Returns:
            list[dict]: A list of profile dictionaries.
        """
        if not self.api_available or not self.client:
            return []
            
        try:
            input_data = {
                'search': query,
                'resultsLimit': max_results
            }
            
            run = self.client.actor('apify/instagram-profile-scraper').call(run_input=input_data)
            
            if not run or 'defaultDatasetId' not in run:
                return []
                
            results: List[Dict[str, Any]] = []
            email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
            
            for item in self.client.dataset(run['defaultDatasetId']).iterate_items():
                biography = item.get('biography', '')
                
                # Extract email
                bio_email = None
                if biography:
                    email_match = email_pattern.search(biography)
                    if email_match:
                        bio_email = email_match.group(0)
                        
                profile_data = {
                    'username': item.get('username'),
                    'full_name': item.get('fullName'),
                    'biography': biography,
                    'follower_count': int(item.get('followersCount', 0) or 0),
                    'following_count': int(item.get('followsCount', 0) or 0),
                    'post_count': int(item.get('postsCount', 0) or 0),
                    'profile_pic_url': item.get('profilePicUrl'),
                    'is_verified': bool(item.get('isVerified', False)),
                    'external_url': item.get('externalUrl'),
                    'bio_email': bio_email
                }
                results.append(profile_data)
                
            return results
            
        except Exception:
            return []

    def search_by_hashtag(self, hashtag: str, max_results: int = 30) -> List[Dict[str, Any]]:
        """
        Search for Instagram creators by hashtag. Scrapes posts with the hashtag
        and extracts unique profile owners.

        Args:
            hashtag: The hashtag to search for (with or without #).
            max_results: Maximum number of posts to scan for unique creators.

        Returns:
            List of unique profile dicts with: username, full_name, biography,
            follower_count, following_count, post_count, profile_pic_url,
            is_verified, external_url, bio_email.
        """
        if not self.api_available or not self.client:
            return []

        # Clean hashtag
        hashtag = hashtag.strip().lstrip('#')

        try:
            input_data = {
                'hashtags': [hashtag],
                'resultsLimit': max_results,
            }

            run = self.client.actor('apify/instagram-hashtag-scraper').call(run_input=input_data)

            if not run or 'defaultDatasetId' not in run:
                return []

            # Extract unique usernames from hashtag posts
            seen_usernames: set = set()
            usernames_to_lookup: list = []

            for item in self.client.dataset(run['defaultDatasetId']).iterate_items():
                owner = item.get('ownerUsername', '') or item.get('owner', {}).get('username', '')
                if owner and owner not in seen_usernames:
                    seen_usernames.add(owner)
                    usernames_to_lookup.append(owner)

            # Now fetch profile details for each unique creator
            results: List[Dict[str, Any]] = []
            email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')

            for username in usernames_to_lookup[:max_results]:
                try:
                    profile_input = {
                        'usernames': [username],
                    }
                    profile_run = self.client.actor('apify/instagram-profile-scraper').call(run_input=profile_input)

                    if not profile_run or 'defaultDatasetId' not in profile_run:
                        # Return basic info if profile lookup fails
                        results.append({
                            'username': username,
                            'full_name': username,
                            'biography': '',
                            'follower_count': 0,
                            'following_count': 0,
                            'post_count': 0,
                            'profile_pic_url': None,
                            'is_verified': False,
                            'external_url': None,
                            'bio_email': None,
                        })
                        continue

                    for profile_item in self.client.dataset(profile_run['defaultDatasetId']).iterate_items():
                        biography = profile_item.get('biography', '')
                        bio_email = None
                        if biography:
                            email_match = email_pattern.search(biography)
                            if email_match:
                                bio_email = email_match.group(0)

                        results.append({
                            'username': profile_item.get('username', username),
                            'full_name': profile_item.get('fullName', username),
                            'biography': biography,
                            'follower_count': int(profile_item.get('followersCount', 0) or 0),
                            'following_count': int(profile_item.get('followsCount', 0) or 0),
                            'post_count': int(profile_item.get('postsCount', 0) or 0),
                            'profile_pic_url': profile_item.get('profilePicUrl'),
                            'is_verified': bool(profile_item.get('isVerified', False)),
                            'external_url': profile_item.get('externalUrl'),
                            'bio_email': bio_email,
                        })
                        break  # Only take first result per username

                except Exception:
                    results.append({
                        'username': username,
                        'full_name': username,
                        'biography': '',
                        'follower_count': 0,
                        'following_count': 0,
                        'post_count': 0,
                        'profile_pic_url': None,
                        'is_verified': False,
                        'external_url': None,
                        'bio_email': None,
                    })

            return results

        except Exception:
            return []

    def get_recent_posts(self, username: str, max_results: int = 12) -> List[Dict[str, Any]]:
        """
        Fetch recent posts for a given Instagram user.
        
        Args:
            username (str): The Instagram username.
            max_results (int, optional): Maximum number of posts to fetch. Defaults to 12.
            
        Returns:
            list[dict]: A list of post dictionaries.
        """
        if not self.api_available or not self.client:
            return []
            
        try:
            input_data = {
                'username': [username],
                'resultsLimit': max_results
            }
            
            run = self.client.actor('apify/instagram-post-scraper').call(run_input=input_data)
            
            if not run or 'defaultDatasetId' not in run:
                return []
                
            results: List[Dict[str, Any]] = []
            hashtag_pattern = re.compile(r'#(\w+)')
            
            for item in self.client.dataset(run['defaultDatasetId']).iterate_items():
                caption = item.get('caption', '')
                
                # Extract hashtags
                hashtags = []
                if caption:
                    hashtags = ['#' + match for match in hashtag_pattern.findall(caption)]
                    
                post_data = {
                    'post_id': item.get('id'),
                    'caption': caption,
                    'like_count': int(item.get('likesCount', 0) or 0),
                    'comment_count': int(item.get('commentsCount', 0) or 0),
                    'timestamp': item.get('timestamp'),
                    'media_type': item.get('type'),
                    'hashtags': hashtags
                }
                results.append(post_data)
                
            return results
            
        except Exception:
            return []

    def detect_sponsored_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect sponsored posts and extract brand names if possible.
        
        Args:
            posts (list[dict]): A list of post dictionaries.
            
        Returns:
            list[dict]: A list of sponsored post dictionaries.
        """
        try:
            indicators = [
                '#ad', '#sponsored', '#collab', '#partnership', '#gifted', '#paidpartnership',
                'paid partnership with', 'sponsored by', 'in collaboration with'
            ]
            
            brand_patterns = [
                re.compile(r'paid partnership with\s+(@?[\w\.]+)', re.IGNORECASE),
                re.compile(r'sponsored by\s+(@?[\w\.]+)', re.IGNORECASE),
                re.compile(r'in collaboration with\s+(@?[\w\.]+)', re.IGNORECASE)
            ]
            
            results: List[Dict[str, Any]] = []
            
            for post in posts:
                caption = post.get('caption', '')
                if not caption:
                    continue
                    
                caption_lower = caption.lower()
                detected_indicators = []
                
                for indicator in indicators:
                    if indicator in caption_lower:
                        detected_indicators.append(indicator)
                        
                if detected_indicators:
                    possible_brand: Optional[str] = None
                    for pattern in brand_patterns:
                        match = pattern.search(caption)
                        if match:
                            possible_brand = match.group(1)
                            break
                            
                    sponsored_post = {
                        'post_id': post.get('post_id'),
                        'caption': caption,
                        'detected_indicators': detected_indicators,
                        'possible_brand': possible_brand
                    }
                    results.append(sponsored_post)
                    
            return results
            
        except Exception:
            return []
