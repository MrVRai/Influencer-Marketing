import statistics
from typing import List, Dict, Union

def calculate_median_views(videos: List[Dict[str, Union[int, float, str]]]) -> int:
    """
    Calculate the median view count from a list of video dictionaries.

    Args:
        videos: A list of dictionaries, each containing a 'view_count' key (int).

    Returns:
        The median view count. Returns 0 if the list is empty.
    """
    if not videos:
        return 0
    views = [int(v.get('view_count', 0)) for v in videos]
    return int(statistics.median(views))

def calculate_engagement_rate(videos: List[Dict[str, Union[int, float, str]]]) -> float:
    """
    Calculate the engagement rate across a list of videos.
    ER = (avg_likes + avg_comments) / avg_views * 100

    Args:
        videos: A list of dictionaries, containing 'view_count', 'like_count', and 'comment_count'.

    Returns:
        Engagement rate as a percentage rounded to 2 decimals. Returns 0.0 if no views.
    """
    if not videos:
        return 0.0
    
    total_views = sum(int(v.get('view_count', 0)) for v in videos)
    total_likes = sum(int(v.get('like_count', 0)) for v in videos)
    total_comments = sum(int(v.get('comment_count', 0)) for v in videos)
    
    if total_views == 0:
        return 0.0
    
    avg_views = total_views / len(videos)
    avg_likes = total_likes / len(videos)
    avg_comments = total_comments / len(videos)
    
    er = ((avg_likes + avg_comments) / avg_views) * 100
    return round(er, 2)

def calculate_consistency_score(videos: List[Dict[str, Union[int, float, str]]]) -> float:
    """
    Calculate the consistency score using coefficient of variation of view counts.
    CV = (stdev / mean * 100)
    Lower CV means more consistent.

    Args:
        videos: A list of dictionaries containing 'view_count'.

    Returns:
        Consistency score rounded to 2 decimals. Returns 0.0 if fewer than 2 videos.
    """
    if len(videos) < 2:
        return 0.0
    
    views = [int(v.get('view_count', 0)) for v in videos]
    mean_views = statistics.mean(views)
    if mean_views == 0:
        return 0.0
    
    stdev_views = statistics.stdev(views)
    cv = (stdev_views / mean_views) * 100
    return round(cv, 2)

def estimate_cpm_rate(median_views: int, platform: str = 'youtube', integration_type: str = '60s_midroll') -> Dict[str, Union[float, int]]:
    """
    Estimate CPM rate based on platform and integration type.

    Args:
        median_views: Median views of the creator.
        platform: Platform name ('youtube', 'instagram').
        integration_type: Type of integration (e.g., '60s_midroll', 'story').

    Returns:
        Dictionary containing estimated_rate_low, estimated_rate_high, cpm_low, cpm_high.
    """
    cpm_rates = {
        'youtube': {
            '60s_midroll': (20, 35),
            '30s_preroll': (15, 25),
            'dedicated': (40, 60),
        },
        'instagram': {
            'story': (5, 10),
            'reel': (10, 20),
            'post': (8, 15),
        }
    }
    
    platform = platform.lower()
    integration_type = integration_type.lower()
    
    if platform in cpm_rates and integration_type in cpm_rates[platform]:
        cpm_low, cpm_high = cpm_rates[platform][integration_type]
    else:
        cpm_low, cpm_high = 0, 0
        
    rate_low = (median_views / 1000) * cpm_low
    rate_high = (median_views / 1000) * cpm_high
    
    return {
        'estimated_rate_low': rate_low,
        'estimated_rate_high': rate_high,
        'cpm_low': cpm_low,
        'cpm_high': cpm_high
    }

def calculate_creator_score(median_views: int, engagement_rate: float, consistency_score: float, subscriber_count: int = 0) -> float:
    """
    Calculate a composite creator score from 0 to 100.
    Weighting:
    - 40% normalized views (cap at 1M=100)
    - 30% engagement (cap at 10%=100)
    - 20% consistency (invert: 0 CV=100, 100+ CV=0)
    - 10% subscribers (cap at 1M=100)

    Args:
        median_views: Median view count.
        engagement_rate: Engagement rate percentage.
        consistency_score: Consistency score (CV).
        subscriber_count: Subscriber count.

    Returns:
        Composite score rounded to 1 decimal.
    """
    # Normalize views (cap at 1M = 100)
    view_score = min(100.0, (median_views / 1_000_000) * 100)
    
    # Normalize engagement (cap at 10% = 100)
    eng_score = min(100.0, (engagement_rate / 10.0) * 100)
    
    # Normalize consistency (invert: 0 CV = 100, 100+ CV = 0)
    consist_score = max(0.0, 100.0 - consistency_score)
    
    # Normalize subscribers (cap at 1M = 100)
    sub_score = min(100.0, (subscriber_count / 1_000_000) * 100)
    
    composite_score = (
        (view_score * 0.40) +
        (eng_score * 0.30) +
        (consist_score * 0.20) +
        (sub_score * 0.10)
    )
    
    return round(composite_score, 1)
