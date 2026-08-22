import re
from typing import List, Dict, Any, Optional
from collections import Counter

SPONSOR_PHRASES = [
    r'(?:sponsored|presented) by ([\w\s&.]+)',
    r'thanks to ([\w\s&.]+) for (?:sponsoring|making)',
    r'partnered with ([\w\s&.]+)',
    r'brought to you by ([\w\s&.]+)',
    r'in (?:collaboration|partnership) with ([\w\s&.]+)',
    r'today\'s sponsor (?:is )?([\w\s&.]+)',
    r'use (?:my |our )?(?:code|link) ([\w\d]+)',
]

AFFILIATE_DOMAINS = [
    'amzn.to', 'bit.ly', 'tinyurl.com', 'linktr.ee', 'stan.store',
    'beacons.ai', 'geni.us', 'howl.me', 'rstyle.me', 'shopmy.us', 'go.magik.ly'
]

PROMO_CODE_PATTERN = r'(?:code|coupon|promo)[:\s]+["\']?([A-Z0-9_-]{3,20})["\']?'


class SponsorDetector:
    """
    Detects brand sponsorships from video descriptions, transcripts, and Instagram captions.
    """

    def detect_from_description(self, description: str) -> Dict[str, Any]:
        """
        Scans description text against SPONSOR_PHRASES (case-insensitive) to extract brand names.
        Also scans for affiliate links and promo codes.
        
        Returns:
            dict: {'brands': list[str], 'affiliate_links': list[str], 'promo_codes': list[str], 'is_sponsored': bool}
        """
        brands = []
        for pattern in SPONSOR_PHRASES:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                # The first group contains the brand or code
                brands.append(match.group(1).strip())
                
        affiliate_links = []
        for domain in AFFILIATE_DOMAINS:
            # Look for the domain in the description
            domain_pattern = r'(?:https?://)?(?:www\.)?' + re.escape(domain) + r'[^\s]*'
            matches = re.finditer(domain_pattern, description, re.IGNORECASE)
            for match in matches:
                affiliate_links.append(match.group(0).strip())

        promo_codes = []
        matches = re.finditer(PROMO_CODE_PATTERN, description, re.IGNORECASE)
        for match in matches:
            promo_codes.append(match.group(1).strip())

        is_sponsored = bool(brands or affiliate_links or promo_codes)
        
        return {
            'brands': list(set(brands)),
            'affiliate_links': list(set(affiliate_links)),
            'promo_codes': list(set(promo_codes)),
            'is_sponsored': is_sponsored
        }

    def detect_from_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Scans transcript text for sponsorships, using same logic as detect_from_description,
        along with transcript-specific patterns.
        
        Returns:
            dict: {'brands': list[str], 'affiliate_links': list[str], 'promo_codes': list[str], 'is_sponsored': bool}
        """
        result = self.detect_from_description(transcript)
        brands = set(result['brands'])
        
        additional_phrases = [
            r'and now a word from ([\w\s&.]+)',
            r'let me tell you about ([\w\s&.]+)',
            r'i want to talk to you about ([\w\s&.]+)'
        ]
        
        for pattern in additional_phrases:
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            for match in matches:
                brands.add(match.group(1).strip())
                
        result['brands'] = list(brands)
        result['is_sponsored'] = bool(result['brands'] or result['affiliate_links'] or result['promo_codes'])
        return result

    def analyze_channel_sponsors(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a list of video dicts and runs sponsor detection on descriptions and transcripts.
        
        Returns:
            dict: Aggregated sponsor statistics.
        """
        total_sponsored = 0
        brand_counter = Counter()
        all_promo_codes = []
        all_affiliate_links = []
        
        for video in videos:
            description = video.get('description', '')
            transcript = video.get('transcript')
            
            desc_result = self.detect_from_description(description) if description else {
                'brands': [], 'affiliate_links': [], 'promo_codes': [], 'is_sponsored': False
            }
            
            transcript_result = self.detect_from_transcript(transcript) if transcript else {
                'brands': [], 'affiliate_links': [], 'promo_codes': [], 'is_sponsored': False
            }
            
            video_brands = set(desc_result['brands'] + transcript_result['brands'])
            video_links = set(desc_result['affiliate_links'] + transcript_result['affiliate_links'])
            video_codes = set(desc_result['promo_codes'] + transcript_result['promo_codes'])
            
            if desc_result['is_sponsored'] or transcript_result['is_sponsored']:
                total_sponsored += 1
                
            for brand in video_brands:
                brand_counter[brand] += 1
                
            all_affiliate_links.extend(video_links)
            all_promo_codes.extend(video_codes)
            
        total_videos = len(videos)
        sponsor_rate = (total_sponsored / total_videos * 100) if total_videos > 0 else 0.0
        
        return {
            'total_sponsored_videos': total_sponsored,
            'sponsor_rate': sponsor_rate,
            'brand_frequency': dict(brand_counter),
            'all_promo_codes': list(set(all_promo_codes)),
            'all_affiliate_links': list(set(all_affiliate_links))
        }

    def detect_instagram_sponsors(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes Instagram posts (caption and hashtags) for sponsorships.
        
        Returns:
            dict: Aggregated Instagram sponsor statistics.
        """
        sponsored_tags = {'#ad', '#sponsored', '#collab', '#partnership', '#gifted', '#paidpartnership'}
        total_sponsored = 0
        brand_counter = Counter()
        found_tags = []
        
        for post in posts:
            caption = post.get('caption', '')
            hashtags = post.get('hashtags', [])
            
            norm_hashtags = [h.lower() if h.startswith('#') else f'#{h.lower()}' for h in hashtags]
            
            post_sponsored_tags = [tag for tag in norm_hashtags if tag in sponsored_tags]
            
            desc_result = self.detect_from_description(caption) if caption else {
                'brands': [], 'affiliate_links': [], 'promo_codes': [], 'is_sponsored': False
            }
            
            is_sponsored = bool(post_sponsored_tags) or desc_result['is_sponsored']
            
            if is_sponsored:
                total_sponsored += 1
                
            found_tags.extend(post_sponsored_tags)
            
            for brand in desc_result['brands']:
                brand_counter[brand] += 1
                
        total_posts = len(posts)
        sponsor_rate = (total_sponsored / total_posts * 100) if total_posts > 0 else 0.0
        
        return {
            'total_sponsored_posts': total_sponsored,
            'sponsor_rate': sponsor_rate,
            'brand_frequency': dict(brand_counter),
            'sponsored_hashtags_found': list(set(found_tags))
        }
