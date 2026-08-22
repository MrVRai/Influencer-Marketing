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

def detect_language(text: str) -> str:
    """
    Detect the primary language of the given text.

    Args:
        text: The string to detect language for.

    Returns:
        ISO 639-1 language code. Returns 'unknown' on failure or if text is too short.
    """
    if not text or len(text.strip()) < 10:
        return 'unknown'
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

def get_language_name(code: str) -> str:
    """
    Map common ISO language codes to human-readable names.

    Args:
        code: ISO 639-1 language code.

    Returns:
        Human-readable language name, or the code itself if not found.
    """
    return SUPPORTED_LANGUAGES.get(code, code)
