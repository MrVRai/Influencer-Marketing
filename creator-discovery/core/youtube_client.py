import os
import re
import datetime
from typing import Optional, List, Dict, Any
import dotenv
import scrapetube
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Load .env from project root
dotenv.load_dotenv()

class YouTubeClient:
    """
    A hybrid YouTube data fetcher that uses the official YouTube Data API v3 
    when available, and falls back to scrapetube when it's not.
    """
    
    def __init__(self) -> None:
        """Initialize the YouTube client, checking for API key availability."""
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.api_available = False
        self.youtube = None
        
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                self.api_available = True
            except Exception as e:
                print(f"Failed to initialize YouTube API: {e}")
                self.api_available = False

    def search_channels(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for YouTube channels matching the query.
        
        Args:
            query (str): The search term.
            max_results (int): Maximum number of results to return. Defaults to 20.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing channel information.
        """
        results = []
        try:
            if self.api_available and self.youtube:
                response = self.youtube.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    maxResults=max_results
                ).execute()
                
                for item in response.get('items', []):
                    snippet = item.get('snippet', {})
                    results.append({
                        'channel_id': snippet.get('channelId', ''),
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', '')
                    })
            else:
                channels = scrapetube.get_search(query, limit=max_results, results_type='channel')
                for channel in channels:
                    results.append({
                        'channel_id': channel.get('channelId', ''),
                        'title': channel.get('title', {}).get('simpleText', ''),
                        'description': channel.get('descriptionSnippet', {}).get('runs', [{}])[0].get('text', '') if channel.get('descriptionSnippet') else '',
                        'thumbnail_url': channel.get('thumbnail', {}).get('thumbnails', [{}])[0].get('url', '') if channel.get('thumbnail', {}).get('thumbnails') else ''
                    })
        except Exception as e:
            print(f"Error searching channels: {e}")
            
        return results

    def search_by_hashtag(self, hashtag: str, max_results: int = 30) -> List[Dict[str, Any]]:
        """
        Search for creators by hashtag. Finds videos tagged with the hashtag
        and extracts unique channel owners.

        Args:
            hashtag: The hashtag to search for (with or without #).
            max_results: Maximum number of videos to scan for unique creators.

        Returns:
            List of unique channel dicts with: channel_id, title, description, thumbnail_url.
        """
        # Clean hashtag
        hashtag = hashtag.strip().lstrip('#')
        search_query = f"#{hashtag}"

        seen_channels: dict[str, Dict[str, Any]] = {}
        try:
            if self.api_available and self.youtube:
                response = self.youtube.search().list(
                    part='snippet',
                    q=search_query,
                    type='video',
                    maxResults=min(max_results, 50),
                    order='relevance'
                ).execute()

                for item in response.get('items', []):
                    snippet = item.get('snippet', {})
                    channel_id = snippet.get('channelId', '')
                    if channel_id and channel_id not in seen_channels:
                        seen_channels[channel_id] = {
                            'channel_id': channel_id,
                            'title': snippet.get('channelTitle', ''),
                            'description': '',
                            'thumbnail_url': '',
                        }
            else:
                videos = scrapetube.get_search(search_query, limit=max_results, results_type='video')
                for video in videos:
                    channel_id = video.get('longBylineText', {}).get('runs', [{}])[0].get('navigationEndpoint', {}).get('browseEndpoint', {}).get('browseId', '')
                    channel_title = video.get('longBylineText', {}).get('runs', [{}])[0].get('text', '')
                    if channel_id and channel_id not in seen_channels:
                        seen_channels[channel_id] = {
                            'channel_id': channel_id,
                            'title': channel_title,
                            'description': '',
                            'thumbnail_url': '',
                        }
        except Exception as e:
            print(f"Error searching by hashtag: {e}")

        return list(seen_channels.values())

    def get_channel_details(self, channel_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific channel.
        
        Args:
            channel_id (str): The YouTube channel ID.
            
        Returns:
            Dict[str, Any]: A dictionary containing channel details.
        """
        try:
            if self.api_available and self.youtube:
                response = self.youtube.channels().list(
                    part='snippet,statistics,brandingSettings',
                    id=channel_id
                ).execute()
                
                items = response.get('items', [])
                if items:
                    item = items[0]
                    snippet = item.get('snippet', {})
                    statistics = item.get('statistics', {})
                    
                    return {
                        'channel_id': channel_id,
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'subscriber_count': int(statistics.get('subscriberCount', 0)),
                        'total_views': int(statistics.get('viewCount', 0)),
                        'video_count': int(statistics.get('videoCount', 0)),
                        'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                        'country': snippet.get('country', ''),
                        'custom_url': snippet.get('customUrl', '')
                    }
            
            # Fallback
            return {
                'channel_id': channel_id,
                'title': f'Channel {channel_id}',
            }
        except Exception as e:
            print(f"Error getting channel details: {e}")
            return {}

    def get_recent_videos(self, channel_id: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        Get the most recent videos from a channel.
        
        Args:
            channel_id (str): The YouTube channel ID.
            max_results (int): Maximum number of videos to return. Defaults to 15.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing video information.
        """
        results = []
        try:
            if self.api_available and self.youtube:
                search_response = self.youtube.search().list(
                    part='snippet',
                    channelId=channel_id,
                    order='date',
                    type='video',
                    maxResults=max_results
                ).execute()
                
                video_ids = [item['id']['videoId'] for item in search_response.get('items', []) if 'videoId' in item.get('id', {})]
                
                if video_ids:
                    videos_response = self.youtube.videos().list(
                        part='snippet,statistics,contentDetails',
                        id=','.join(video_ids)
                    ).execute()
                    
                    for item in videos_response.get('items', []):
                        snippet = item.get('snippet', {})
                        statistics = item.get('statistics', {})
                        content_details = item.get('contentDetails', {})
                        
                        results.append({
                            'video_id': item.get('id', ''),
                            'title': snippet.get('title', ''),
                            'published_at': snippet.get('publishedAt', ''),
                            'view_count': int(statistics.get('viewCount', 0)),
                            'like_count': int(statistics.get('likeCount', 0)),
                            'comment_count': int(statistics.get('commentCount', 0)),
                            'description': snippet.get('description', ''),
                            'duration': content_details.get('duration', '')
                        })
            else:
                videos = scrapetube.get_channel(channel_id, limit=max_results)
                for video in videos:
                    video_id = video.get('videoId', '')
                    title = video.get('title', {}).get('runs', [{}])[0].get('text', '')
                    
                    view_count_text = video.get('viewCountText', {}).get('simpleText', '0')
                    view_count = 0
                    if view_count_text:
                        match = re.search(r'([\d,]+)', view_count_text)
                        if match:
                            view_count = int(match.group(1).replace(',', ''))
                            
                    results.append({
                        'video_id': video_id,
                        'title': title,
                        'published_at': '',
                        'view_count': view_count,
                        'like_count': 0,
                        'comment_count': 0,
                        'description': '',
                        'duration': video.get('lengthText', {}).get('simpleText', '')
                    })
        except Exception as e:
            print(f"Error getting recent videos: {e}")
            
        return results

    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Get the transcript of a video.
        
        Args:
            video_id (str): The YouTube video ID.
            
        Returns:
            Optional[str]: The full transcript as a single string, or None if unavailable.
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([segment.get('text', '') for segment in transcript_list])
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            print(f"Transcript not available for {video_id}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching transcript for {video_id}: {e}")
            return None
