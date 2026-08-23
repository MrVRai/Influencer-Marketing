from langdetect import detect, DetectorFactory
from typing import List, Dict, Union
from collections import Counter

# Seed for reproducibility
DetectorFactory.seed = 0

SUPPORTED_LANGUAGES: Dict[str, str] = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'mr': 'Marathi',
    'bn': 'Bengali',
    'gu': 'Gujarati',
    'pa': 'Punjabi',
    'ur': 'Urdu',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh-cn': 'Chinese',
    'ar': 'Arabic',
    'ru': 'Russian',
    'id': 'Indonesian',
    'tr': 'Turkish',
    'th': 'Thai',
    'vi': 'Vietnamese'
}

import re

def detect_language(text: str) -> str:
    """
    Detect the primary language of the given text.
    Includes Devanagari script and Hinglish token detection.

    Args:
        text: The string to detect language for.

    Returns:
        ISO 639-1 language code. Returns 'unknown' on failure or if text is too short.
    """
    if not text or len(text.strip()) < 5:
        return 'unknown'

    # Check for Devanagari script (Hindi, Marathi, Sanskrit)
    if re.search(r'[\u0900-\u097F]', text):
        return 'hi'
    # Tamil script
    if re.search(r'[\u0B80-\u0BFF]', text):
        return 'ta'
    # Telugu script
    if re.search(r'[\u0C00-\u0C7F]', text):
        return 'te'
    # Bengali script
    if re.search(r'[\u0980-\u09FF]', text):
        return 'bn'
    # Arabic / Urdu script
    if re.search(r'[\u0600-\u06FF]', text):
        return 'ur'

    # Check for Hinglish / Romanized Hindi indicators
    hinglish_words = {
        'hai', 'hain', 'karein', 'kare', 'kaise', 'mera', 'meri', 'mere', 'aap', 'aapka',
        'aapki', 'yeh', 'woh', 'aur', 'ke', 'ki', 'ko', 'se', 'me', 'mein', 'desi',
        'bharat', 'hindi', 'batao', 'dekho', 'hoga', 'hogi', 'tarika', 'nuskhe', 'gharelu',
        'upay', 'sundar', 'khubsurat', 'swagat', 'namaste', 'shukriya', 'dosto', 'mitro'
    }
    words = set(re.findall(r'\b[a-zA-Z]{2,15}\b', text.lower()))
    if len(words.intersection(hinglish_words)) >= 2 or 'hindi' in words:
        return 'hi'

    try:
        return detect(text)
    except Exception:
        return 'unknown'

def detect_content_language(videos: List[Dict[str, Union[str, int, float]]]) -> str:
    """
    Detect the most common language across a list of videos.

    Args:
        videos: List of dictionaries, each containing 'title' and 'description'.

    Returns:
        The most common ISO 639-1 language code. Returns 'unknown' if empty or none detected.
    """
    if not videos:
        return 'unknown'
        
    langs = []
    for video in videos:
        title = video.get('title', '')
        description = video.get('description', '')
        text = f"{title} {description}".strip()
        lang = detect_language(text)
        if lang != 'unknown':
            langs.append(lang)
            
    if not langs:
        return 'unknown'
        
    counter = Counter(langs)
    most_common = counter.most_common(1)
    return most_common[0][0]


def detect_ig_creator_language(profile: Dict[str, Union[str, int, list]]) -> str:
    """
    Detect the primary content language of an Instagram creator.
    Aggregates biography + all post captions into a single rich text corpus
    before running language detection, for much higher accuracy than
    snippet-level detection.

    Args:
        profile: Instagram profile dict with keys 'biography' and 'posts'
                 (posts is a list of dicts with a 'caption' key).

    Returns:
        ISO 639-1 language code, or 'unknown'.
    """
    text_parts = []

    # Add biography (often contains language indicators)
    bio = profile.get('biography', '') or ''
    if bio:
        text_parts.append(bio)

    # Add ALL post captions in full (not truncated)
    posts = profile.get('posts', []) or []
    for post in posts:
        caption = post.get('caption', '') or ''
        if caption:
            text_parts.append(caption)

    if not text_parts:
        return 'unknown'

    # Combine everything — more text = better detection accuracy
    combined = ' '.join(text_parts)
    return detect_language(combined)

def get_language_name(code: str) -> str:
    """
    Map common ISO language codes to human-readable names.

    Args:
        code: ISO 639-1 language code.

    Returns:
        Human-readable language name, or the code itself if not found.
    """
    return SUPPORTED_LANGUAGES.get(code, code)
