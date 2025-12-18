#!/usr/bin/env python3
"""
TubeLab YouTube Outlier Detector - Sleep/ASMR Gaming Niche
Analyzes competitor channels using TubeLab API with sleep-specific scoring.
"""

import argparse
import csv
import json
import math
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

import requests


# Competitor channels for sleep gaming niche
COMPETITOR_CHANNELS = [
    "Fallasleepmon",
    "Boring Gamer",
    "Stellar Sleep",
    "BlueBoyPhin",
    "Sleepy Gamer",
    "PokeSleep",
    "PokeRest",
    "Cozy Gamer"
]


class TubeLabClient:
    """Client for TubeLab API interactions."""

    BASE_URL = "https://public-api.tubelab.net/v1"
    RATE_LIMIT_DELAY = 6  # 10 requests per minute = 6 seconds between requests

    def __init__(self, api_key: str):
        """Initialize TubeLab client with API key."""
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Api-Key {api_key}',
            'Content-Type': 'application/json'
        }
        self.last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't exceed rate limits (10 requests/minute)."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - time_since_last
            print(f"    Rate limiting: waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def search_channels(self, query: str) -> List[Dict]:
        """Search for channels by name."""
        self._rate_limit()

        url = f"{self.BASE_URL}/channels"
        params = {'query': query}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # TubeLab returns different structures, adapt as needed
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'channels' in data:
                return data['channels']
            else:
                return []

        except requests.exceptions.RequestException as e:
            print(f"    Error searching for channel '{query}': {e}")
            return []

    def get_channel_videos(self, channel_id: str, max_results: int = 200) -> List[Dict]:
        """Get videos for a specific channel."""
        self._rate_limit()

        url = f"{self.BASE_URL}/channels/{channel_id}/videos"
        params = {'limit': max_results}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'videos' in data:
                return data['videos']
            else:
                return []

        except requests.exceptions.RequestException as e:
            print(f"    Error getting videos for channel {channel_id}: {e}")
            return []

    def get_outliers(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search TubeLab's outlier database for a specific query."""
        self._rate_limit()

        url = f"{self.BASE_URL}/outliers"
        params = {
            'query': query,
            'limit': max_results
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'outliers' in data:
                return data['outliers']
            else:
                return []

        except requests.exceptions.RequestException as e:
            print(f"    Error searching outliers for '{query}': {e}")
            return []

    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get detailed information for a specific video."""
        self._rate_limit()

        url = f"{self.BASE_URL}/videos/{video_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"    Error getting video details for {video_id}: {e}")
            return None

    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript for a video."""
        self._rate_limit()

        url = f"{self.BASE_URL}/videos/{video_id}/transcript"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Extract transcript text
            if isinstance(data, dict) and 'transcript' in data:
                return data['transcript']
            elif isinstance(data, str):
                return data
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"    Error getting transcript for {video_id}: {e}")
            return None


def calculate_days_since_upload(publish_date_str: str) -> float:
    """Calculate days since video was uploaded."""
    try:
        # Try multiple date formats
        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
            try:
                publish_date = datetime.strptime(publish_date_str, fmt)
                if publish_date.tzinfo is None:
                    publish_date = publish_date.replace(tzinfo=timezone.utc)
                break
            except ValueError:
                continue
        else:
            # If no format worked, try parsing as ISO
            publish_date = datetime.fromisoformat(publish_date_str.replace('Z', '+00:00'))

        now = datetime.now(timezone.utc)
        delta = now - publish_date
        return delta.total_seconds() / 86400

    except Exception as e:
        print(f"    Warning: Could not parse date '{publish_date_str}': {e}")
        return 365  # Default to 1 year old


def calculate_median(values: List[float]) -> float:
    """Calculate median of a list of values."""
    if not values:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)

    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    else:
        return sorted_values[n // 2]


def calculate_sleep_niche_score(
    views: int,
    days_since: float,
    baseline_vpd: float,
    epsilon: float = 100
) -> Tuple[float, float, float, float]:
    """
    Calculate outlier score optimized for sleep/ASMR gaming niche.

    Sleep channels have evergreen content, so we need to:
    1. Heavily favor recent videos (3-6 months)
    2. Penalize videos older than 1 year
    3. Look for 2x+ performance vs baseline

    Returns:
        Tuple of (views_per_day, outlier_score, recency_boost, final_score)
    """
    # Calculate views per day
    views_per_day = views / max(days_since, 1)

    # Calculate base outlier score
    outlier_score = views_per_day / max(baseline_vpd, epsilon)

    # SLEEP-SPECIFIC RECENCY BOOST
    # This is the key change for sleep content
    if days_since <= 90:  # 0-3 months: Strong boost
        recency_boost = 2.0 + 1.0 * math.exp(-days_since / 30)
    elif days_since <= 180:  # 3-6 months: Moderate boost
        recency_boost = 1.5 + 0.5 * math.exp(-(days_since - 90) / 45)
    elif days_since <= 365:  # 6-12 months: Slight boost
        recency_boost = 1.0 + 0.3 * math.exp(-(days_since - 180) / 90)
    else:  # >1 year: PENALTY for evergreen effect
        # Penalize old videos heavily to filter out evergreen content
        penalty_factor = math.exp(-(days_since - 365) / 180)
        recency_boost = 0.5 * penalty_factor

    # Calculate final score
    final_score = outlier_score * recency_boost

    return views_per_day, outlier_score, recency_boost, final_score


def analyze_transcript(transcript: str, description: str) -> Dict[str, any]:
    """
    Analyze transcript/description to understand what made the video successful.

    Looks for:
    - Specific games mentioned
    - Sound types (rain, white noise, etc.)
    - Visual style indicators
    """
    text = (transcript or "") + " " + (description or "")
    text_lower = text.lower()

    analysis = {
        'game_mentioned': None,
        'sound_type': [],
        'packaging_elements': []
    }

    # Common sleep gaming franchises
    games = [
        'pokemon', 'pokémon', 'stardew', 'animal crossing', 'minecraft',
        'zelda', 'mario', 'slime rancher', 'spiritfarer', 'gris',
        'abzu', 'journey', 'sky', 'ooblets'
    ]

    for game in games:
        if game in text_lower:
            analysis['game_mentioned'] = game.title()
            break

    # Sound types common in sleep content
    sound_types = {
        'rain': ['rain', 'rainy', 'rainfall', 'rainforest'],
        'white_noise': ['white noise', 'static', 'ambient'],
        'nature': ['nature', 'forest', 'ocean', 'waves', 'river', 'stream'],
        'thunder': ['thunder', 'thunderstorm', 'storm'],
        'fire': ['fireplace', 'crackling', 'campfire'],
        'music': ['music', 'soundtrack', 'ost', 'theme'],
        'asmr': ['asmr', 'whisper', 'soft spoken', 'tingles']
    }

    for sound_type, keywords in sound_types.items():
        if any(keyword in text_lower for keyword in keywords):
            analysis['sound_type'].append(sound_type)

    # Packaging elements
    packaging_keywords = {
        'long_duration': ['10 hours', '8 hours', '12 hours', 'all night', 'extended'],
        'no_ads': ['no ads', 'ad-free', 'uninterrupted', 'no interruptions'],
        'black_screen': ['black screen', 'dark screen', 'no visuals'],
        'gameplay': ['gameplay', 'playthrough', 'walkthrough', 'let\'s play'],
        'cozy': ['cozy', 'comfy', 'relaxing', 'chill', 'peaceful'],
        'study': ['study', 'focus', 'concentration', 'productivity']
    }

    for element, keywords in packaging_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            analysis['packaging_elements'].append(element)

    return analysis


def analyze_competitor_channel(
    client: TubeLabClient,
    channel_name: str,
    lookback_months: int = 6,
    min_views: int = 5000,
    min_outlier_score: float = 2.0
) -> List[Dict]:
    """
    Analyze a competitor channel for outliers.

    Args:
        client: TubeLab API client
        channel_name: Name of the channel to analyze
        lookback_months: Focus on videos from last N months
        min_views: Minimum view threshold
        min_outlier_score: Minimum outlier score (2.0 = 2x baseline)

    Returns:
        List of outlier videos with analysis
    """
    print(f"\n{'='*60}")
    print(f"Analyzing: {channel_name}")
    print(f"{'='*60}")

    # Step 1: Search for channel
    print("  Searching for channel...")
    channels = client.search_channels(channel_name)

    if not channels:
        print(f"  ⚠ Channel not found: {channel_name}")
        return []

    # Take the first match (assuming it's correct)
    channel = channels[0]
    channel_id = channel.get('id') or channel.get('channel_id')
    channel_title = channel.get('title') or channel.get('name') or channel_name

    print(f"  ✓ Found: {channel_title}")

    # Get channel revenue estimate if available
    revenue_estimate = channel.get('revenue_monthly') or channel.get('estimated_monthly_revenue')
    if revenue_estimate:
        print(f"  💰 Est. Monthly Revenue: ${revenue_estimate:,}")

    # Step 2: Get videos from channel
    print("  Fetching videos...")
    videos = client.get_channel_videos(channel_id, max_results=200)

    if not videos:
        print(f"  ⚠ No videos found")
        return []

    print(f"  ✓ Found {len(videos)} videos")

    # Step 3: Filter to recent videos and calculate metrics
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_months * 30)
    recent_videos = []

    for video in videos:
        publish_date_str = video.get('publishedAt') or video.get('upload_date') or video.get('published_at')
        if not publish_date_str:
            continue

        days_since = calculate_days_since_upload(publish_date_str)
        views = video.get('viewCount') or video.get('views') or video.get('view_count') or 0

        # Add metrics to video
        video['days_since'] = days_since
        video['views'] = views
        video['views_per_day'] = views / max(days_since, 1)

        recent_videos.append(video)

    if not recent_videos:
        print(f"  ⚠ No recent videos found")
        return []

    # Step 4: Calculate baseline (median VPD of all videos)
    baseline_vpd_values = [v['views_per_day'] for v in recent_videos if v['views'] > 0]
    baseline_vpd = calculate_median(baseline_vpd_values)

    print(f"  Baseline VPD: {baseline_vpd:.2f} (median of {len(baseline_vpd_values)} videos)")

    # Step 5: Find outliers with sleep-specific scoring
    outliers = []

    for video in recent_videos:
        # Skip if below minimum views
        if video['views'] < min_views:
            continue

        # Calculate sleep-niche specific score
        vpd, outlier_score, recency_boost, final_score = calculate_sleep_niche_score(
            video['views'],
            video['days_since'],
            baseline_vpd
        )

        # Check if it's an outlier (2x+ baseline, recent videos favored)
        if outlier_score >= min_outlier_score and video['days_since'] <= (lookback_months * 30):
            video_id = video.get('id') or video.get('video_id')

            # Get additional details and transcript
            print(f"    Analyzing outlier: {video.get('title', 'Unknown')[:50]}...")

            details = client.get_video_details(video_id) if video_id else None
            transcript = client.get_video_transcript(video_id) if video_id else None
            description = video.get('description') or (details.get('description') if details else '')

            # Analyze what made it successful
            content_analysis = analyze_transcript(transcript, description)

            outlier_data = {
                'channel_name': channel_title,
                'channel_revenue_monthly': revenue_estimate,
                'video_id': video_id,
                'video_title': video.get('title'),
                'video_url': f"https://www.youtube.com/watch?v={video_id}" if video_id else '',
                'publish_date': video.get('publishedAt') or video.get('upload_date'),
                'days_since': round(video['days_since'], 1),
                'views': video['views'],
                'views_per_day': round(vpd, 2),
                'baseline_vpd': round(baseline_vpd, 2),
                'outlier_score': round(outlier_score, 2),
                'recency_boost': round(recency_boost, 2),
                'final_score': round(final_score, 2),
                'game_mentioned': content_analysis['game_mentioned'],
                'sound_types': ', '.join(content_analysis['sound_type']) if content_analysis['sound_type'] else 'None',
                'packaging_elements': ', '.join(content_analysis['packaging_elements']) if content_analysis['packaging_elements'] else 'None',
                'description': description[:200] if description else ''  # First 200 chars
            }

            outliers.append(outlier_data)

    print(f"  🎯 Found {len(outliers)} outlier(s)")

    return outliers


def write_csv_output(outliers: List[Dict], output_file: str) -> None:
    """Write outliers to CSV file."""
    if not outliers:
        print(f"\n⚠ No outliers to write")
        return

    fieldnames = [
        'channel_name', 'channel_revenue_monthly', 'video_title', 'video_url',
        'publish_date', 'days_since', 'views', 'views_per_day', 'baseline_vpd',
        'outlier_score', 'recency_boost', 'final_score',
        'game_mentioned', 'sound_types', 'packaging_elements', 'description'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(outliers)

    print(f"\n✓ Results written to {output_file}")
    print(f"  Total outliers: {len(outliers)}")


def write_google_sheets_output(outliers: List[Dict], sheet_id: str) -> None:
    """Write outliers to Google Sheet."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("\n⚠ Google Sheets output requires: pip install gspread google-auth")
        return

    if not outliers:
        print(f"\n⚠ No outliers to write to Google Sheets")
        return

    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = Credentials.from_service_account_file('service_account.json', scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1

        # Clear existing data
        sheet.clear()

        # Prepare headers
        headers = [
            'Channel', 'Monthly Revenue', 'Video Title', 'URL', 'Publish Date',
            'Days Since', 'Views', 'Views/Day', 'Baseline VPD', 'Outlier Score',
            'Recency Boost', 'Final Score', 'Game', 'Sound Types', 'Packaging', 'Description'
        ]

        rows = [headers]
        for outlier in outliers:
            rows.append([
                outlier.get('channel_name', ''),
                outlier.get('channel_revenue_monthly', ''),
                outlier.get('video_title', ''),
                outlier.get('video_url', ''),
                outlier.get('publish_date', ''),
                outlier.get('days_since', ''),
                outlier.get('views', ''),
                outlier.get('views_per_day', ''),
                outlier.get('baseline_vpd', ''),
                outlier.get('outlier_score', ''),
                outlier.get('recency_boost', ''),
                outlier.get('final_score', ''),
                outlier.get('game_mentioned', ''),
                outlier.get('sound_types', ''),
                outlier.get('packaging_elements', ''),
                outlier.get('description', '')
            ])

        sheet.update('A1', rows)
        print(f"\n✓ Results written to Google Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")

    except FileNotFoundError:
        print("\n⚠ service_account.json not found")
    except Exception as e:
        print(f"\n⚠ Error writing to Google Sheets: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='TubeLab-based outlier detector for sleep gaming niche',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--api-key',
        type=str,
        default=os.environ.get('TUBELAB_API_KEY'),
        help='TubeLab API key (or set TUBELAB_API_KEY env var)'
    )
    parser.add_argument(
        '--lookback-months',
        type=int,
        default=6,
        help='Focus on videos from last N months (default: 6)'
    )
    parser.add_argument(
        '--min-views',
        type=int,
        default=5000,
        help='Minimum view threshold (default: 5000)'
    )
    parser.add_argument(
        '--min-outlier-score',
        type=float,
        default=2.0,
        help='Minimum outlier score multiplier (default: 2.0 = 2x baseline)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='competitor_outliers.csv',
        help='Output CSV file (default: competitor_outliers.csv)'
    )
    parser.add_argument(
        '--sheet',
        type=str,
        default=None,
        help='Google Sheet ID for output (optional)'
    )

    args = parser.parse_args()

    # Check API key
    if not args.api_key:
        print("⚠ TubeLab API key required!")
        print("\nSet it via:")
        print("  export TUBELAB_API_KEY='your-key-here'")
        print("  or")
        print("  python tubelab_outlier_detector.py --api-key 'your-key-here'")
        sys.exit(1)

    print("🎯 TubeLab Outlier Detector - Sleep Gaming Niche")
    print(f"  Analyzing {len(COMPETITOR_CHANNELS)} competitor channels")
    print(f"  Settings:")
    print(f"    - Lookback period: {args.lookback_months} months")
    print(f"    - Min views: {args.min_views}")
    print(f"    - Min outlier score: {args.min_outlier_score}x baseline")
    print(f"    - Output: {args.output}")
    if args.sheet:
        print(f"    - Google Sheet: {args.sheet}")

    # Initialize TubeLab client
    client = TubeLabClient(args.api_key)

    # Analyze all competitor channels
    all_outliers = []

    for i, channel_name in enumerate(COMPETITOR_CHANNELS, 1):
        print(f"\n[{i}/{len(COMPETITOR_CHANNELS)}]")

        outliers = analyze_competitor_channel(
            client,
            channel_name,
            args.lookback_months,
            args.min_views,
            args.min_outlier_score
        )

        all_outliers.extend(outliers)

    # Sort by final score (descending)
    all_outliers.sort(key=lambda x: x['final_score'], reverse=True)

    # Write outputs
    write_csv_output(all_outliers, args.output)

    if args.sheet:
        write_google_sheets_output(all_outliers, args.sheet)

    # Summary
    if all_outliers:
        print(f"\n{'='*60}")
        print(f"🎉 Analysis Complete!")
        print(f"{'='*60}")
        print(f"  Total outliers found: {len(all_outliers)}")
        print(f"\n  Top 3 outliers:")
        for i, outlier in enumerate(all_outliers[:3], 1):
            print(f"    {i}. {outlier['video_title'][:50]}")
            print(f"       Channel: {outlier['channel_name']}")
            print(f"       Score: {outlier['final_score']} ({outlier['outlier_score']}x baseline)")
            if outlier['game_mentioned']:
                print(f"       Game: {outlier['game_mentioned']}")
            if outlier['sound_types']:
                print(f"       Sounds: {outlier['sound_types']}")
            print()


if __name__ == '__main__':
    main()
