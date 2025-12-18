"""
TubeLab API Client with Rate Limiting
Handles all interactions with TubeLab API for Pokémon outlier detection.
"""

import os
import time
from typing import Dict, List, Optional

import requests


class TubeLabClient:
    """Client for TubeLab API with automatic rate limiting."""

    BASE_URL = "https://public-api.tubelab.net/v1"
    RATE_LIMIT_DELAY = 6  # 10 requests per minute = 6 seconds between requests

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TubeLab client.

        Args:
            api_key: TubeLab API key (or uses TUBELAB_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('TUBELAB_API_KEY')
        if not self.api_key:
            raise ValueError(
                "TubeLab API key required. Set TUBELAB_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.headers = {
            'Authorization': f'Api-Key {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.last_request_time = 0
        self.request_count = 0

    def _rate_limit(self):
        """Ensure we don't exceed rate limits (10 requests/minute)."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make API request with error handling.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data or None if error
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None  # Not found is not an error, just return None
            print(f"    HTTP Error {e.response.status_code}: {e}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"    Request Error: {e}")
            return None

    def search_channels(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for channels by name.

        Args:
            query: Channel name to search
            limit: Maximum results

        Returns:
            List of channel dictionaries
        """
        params = {'query': query, 'limit': limit}
        data = self._make_request('channels', params)

        if not data:
            return []

        # Handle different response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'channels' in data:
            return data['channels']
        elif isinstance(data, dict) and 'data' in data:
            return data['data'] if isinstance(data['data'], list) else [data['data']]
        else:
            return []

    def get_channel_videos(
        self,
        channel_id: str,
        limit: int = 60
    ) -> List[Dict]:
        """
        Get recent videos from a channel.

        Args:
            channel_id: Channel ID from TubeLab
            limit: Maximum videos to fetch

        Returns:
            List of video dictionaries
        """
        params = {'limit': limit}
        data = self._make_request(f'channels/{channel_id}/videos', params)

        if not data:
            return []

        # Handle different response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'videos' in data:
            return data['videos']
        elif isinstance(data, dict) and 'data' in data:
            return data['data'] if isinstance(data['data'], list) else [data['data']]
        else:
            return []

    def get_outliers(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search TubeLab's outlier database.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of outlier video dictionaries
        """
        params = {'query': query, 'limit': limit}
        data = self._make_request('outliers', params)

        if not data:
            return []

        # Handle different response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'outliers' in data:
            return data['outliers']
        elif isinstance(data, dict) and 'data' in data:
            return data['data'] if isinstance(data['data'], list) else [data['data']]
        else:
            return []

    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed information for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Video details dictionary or None
        """
        return self._make_request(f'videos/{video_id}')

    def get_stats(self) -> Dict:
        """Get client usage statistics."""
        return {
            'total_requests': self.request_count,
            'estimated_cost': self.request_count * 0.01  # Rough estimate
        }


def test_client():
    """Test the TubeLab client."""
    try:
        client = TubeLabClient()
        print("✓ TubeLab client initialized")

        # Test channel search
        print("\nTesting channel search for 'PokeSleep'...")
        channels = client.search_channels('PokeSleep', limit=3)
        if channels:
            print(f"✓ Found {len(channels)} channel(s)")
            for ch in channels[:1]:
                print(f"  - {ch.get('name') or ch.get('title')}")
        else:
            print("⚠ No channels found")

        print(f"\nTotal requests made: {client.request_count}")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == '__main__':
    test_client()
