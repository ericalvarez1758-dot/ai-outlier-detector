"""
Fetch Competitor Data
Collects recent uploads from competitor channels and filters for Pokémon content.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tubelab_client import TubeLabClient


def load_competitors(file_path: str = 'input/competitors.txt') -> List[str]:
    """Load competitor channel names from file."""
    competitors = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                competitors.append(line)
    return competitors


def load_pokemon_keywords(file_path: str = 'input/pokemon_keywords.txt') -> Set[str]:
    """Load Pokémon validation keywords."""
    keywords = set()
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith('#'):
                keywords.add(line)
    return keywords


def is_pokemon_content(title: str, description: str, keywords: Set[str]) -> bool:
    """
    Check if video is Pokémon content.

    Args:
        title: Video title
        description: Video description
        keywords: Set of Pokémon keywords

    Returns:
        True if content is Pokémon-related
    """
    text = (title + ' ' + (description or '')).lower()

    # Check for Pokémon keywords
    for keyword in keywords:
        if keyword in text:
            # Found Pokémon keyword - now check for exclusions
            exclusions = [
                'animal crossing',
                'mario',
                'zelda',
                'stardew',
                'minecraft',
                'terraria',
                'slime rancher',
                'fortnite'
            ]

            for exclusion in exclusions:
                if exclusion in text:
                    return False  # Non-Pokémon game mentioned

            return True

    return False


def normalize_video_data(video: Dict, channel_name: str) -> Dict:
    """
    Normalize video data from TubeLab response.

    Args:
        video: Raw video data from API
        channel_name: Name of the channel

    Returns:
        Normalized video dictionary
    """
    # Extract video ID
    video_id = (
        video.get('id') or
        video.get('video_id') or
        video.get('videoId') or
        ''
    )

    # Extract title
    title = (
        video.get('title') or
        video.get('snippet', {}).get('title') or
        ''
    )

    # Extract description
    description = (
        video.get('description') or
        video.get('snippet', {}).get('description') or
        ''
    )

    # Extract views
    views = (
        video.get('views') or
        video.get('viewCount') or
        video.get('view_count') or
        video.get('statistics', {}).get('viewCount') or
        0
    )

    # Ensure views is an integer
    try:
        views = int(views)
    except (ValueError, TypeError):
        views = 0

    # Extract publish date
    published_at = (
        video.get('publishedAt') or
        video.get('published_at') or
        video.get('upload_date') or
        video.get('snippet', {}).get('publishedAt') or
        None
    )

    # Extract duration (in seconds)
    duration = (
        video.get('duration') or
        video.get('length_seconds') or
        video.get('contentDetails', {}).get('duration') or
        None
    )

    # Extract thumbnail URL
    thumbnail_url = (
        video.get('thumbnail') or
        video.get('thumbnail_url') or
        video.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url') or
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else None
    )

    return {
        'channel': channel_name,
        'video_id': video_id,
        'title': title,
        'description': description,
        'published_at': published_at,
        'views': views,
        'duration': duration,
        'url': f"https://www.youtube.com/watch?v={video_id}" if video_id else '',
        'thumbnail_url': thumbnail_url
    }


def fetch_channel_data(
    client: TubeLabClient,
    channel_name: str,
    pokemon_keywords: Set[str],
    videos_per_channel: int = 60
) -> List[Dict]:
    """
    Fetch and filter videos from a single channel.

    Args:
        client: TubeLab API client
        channel_name: Name of channel to fetch
        pokemon_keywords: Set of Pokémon keywords for filtering
        videos_per_channel: Number of recent videos to fetch

    Returns:
        List of normalized video dictionaries (Pokémon content only)
    """
    print(f"\n{'='*60}")
    print(f"Fetching: {channel_name}")
    print(f"{'='*60}")

    # Search for channel
    print("  Searching for channel...")
    channels = client.search_channels(channel_name, limit=5)

    if not channels:
        print(f"  ✗ Channel not found: {channel_name}")
        return []

    # Take first match
    channel = channels[0]
    channel_id = channel.get('id') or channel.get('channel_id') or channel.get('channelId')
    channel_title = channel.get('name') or channel.get('title') or channel_name

    print(f"  ✓ Found: {channel_title} (ID: {channel_id})")

    # Get channel videos
    print(f"  Fetching up to {videos_per_channel} recent videos...")
    videos = client.get_channel_videos(channel_id, limit=videos_per_channel)

    if not videos:
        print(f"  ✗ No videos found")
        return []

    print(f"  ✓ Retrieved {len(videos)} videos")

    # Normalize and filter for Pokémon content
    print("  Filtering for Pokémon content...")
    pokemon_videos = []

    for video in videos:
        normalized = normalize_video_data(video, channel_title)

        # Skip if missing critical data
        if not normalized['video_id'] or not normalized['title']:
            continue

        # Check if Pokémon content
        if is_pokemon_content(
            normalized['title'],
            normalized['description'],
            pokemon_keywords
        ):
            pokemon_videos.append(normalized)

    print(f"  ✓ Found {len(pokemon_videos)} Pokémon videos")

    return pokemon_videos


def main():
    """Main execution function."""
    print("="*60)
    print("POKÉMON OUTLIER DETECTOR - DATA COLLECTION")
    print("="*60)

    # Initialize client
    try:
        client = TubeLabClient()
        print("✓ TubeLab client initialized")
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("\nSet your API key:")
        print("  export TUBELAB_API_KEY='your-key-here'")
        sys.exit(1)

    # Load competitors
    print("\nLoading competitor list...")
    competitors = load_competitors()
    print(f"✓ Loaded {len(competitors)} competitors")

    # Load Pokémon keywords
    print("Loading Pokémon keywords...")
    pokemon_keywords = load_pokemon_keywords()
    print(f"✓ Loaded {len(pokemon_keywords)} keywords")

    # Fetch data from each competitor
    all_videos = []

    for i, channel_name in enumerate(competitors, 1):
        print(f"\n[{i}/{len(competitors)}]")

        videos = fetch_channel_data(
            client,
            channel_name,
            pokemon_keywords,
            videos_per_channel=60
        )

        all_videos.extend(videos)

    # Save raw data
    print(f"\n{'='*60}")
    print("SAVING DATA")
    print(f"{'='*60}")

    output_file = 'output/raw_videos.json'
    os.makedirs('output', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_videos, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(all_videos)} Pokémon videos to {output_file}")

    # Stats
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total competitors analyzed: {len(competitors)}")
    print(f"Total Pokémon videos found: {len(all_videos)}")
    print(f"Average per channel: {len(all_videos) / len(competitors):.1f}")

    stats = client.get_stats()
    print(f"\nAPI requests made: {stats['total_requests']}")

    # Videos by channel
    print(f"\nVideos by channel:")
    from collections import Counter
    channel_counts = Counter(v['channel'] for v in all_videos)
    for channel, count in channel_counts.most_common():
        print(f"  {channel}: {count} videos")


if __name__ == '__main__':
    main()
