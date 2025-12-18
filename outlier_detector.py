#!/usr/bin/env python3
"""
YouTube Outlier Detector - Free version using yt-dlp
Finds videos that are significantly outperforming a channel's baseline.
"""

import argparse
import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def get_channel_videos(channel_url: str, max_videos: int) -> List[Dict]:
    """
    Fetch video data for a channel using yt-dlp.

    Args:
        channel_url: Channel URL or @handle
        max_videos: Maximum number of videos to fetch

    Returns:
        List of video dictionaries with metadata
    """
    print(f"  Fetching up to {max_videos} videos from {channel_url}...")

    # Normalize channel URL
    if channel_url.startswith('@'):
        # Convert @handle to full URL
        channel_url = f"https://www.youtube.com/{channel_url}/videos"
    elif not channel_url.startswith('http'):
        # Assume it's a handle without @
        channel_url = f"https://www.youtube.com/@{channel_url}/videos"
    elif '/videos' not in channel_url and '/c/' not in channel_url:
        # Add /videos to URL if not present
        channel_url = f"{channel_url.rstrip('/')}/videos"

    # Construct yt-dlp command
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--print', '%(id)s|||%(title)s|||%(view_count)s|||%(upload_date)s|||%(url)s',
        '--playlist-end', str(max_videos),
        '--no-warnings',
        '--skip-download',
        channel_url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"  ⚠ Error fetching channel: {result.stderr}")
            return []

        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line or '|||' not in line:
                continue

            parts = line.split('|||')
            if len(parts) < 5:
                continue

            video_id, title, view_count, upload_date, url = parts

            # Skip if views are unavailable
            if view_count == 'NA' or not view_count:
                continue

            try:
                views = int(view_count)
            except (ValueError, TypeError):
                continue

            # Parse upload date (format: YYYYMMDD)
            try:
                publish_date = datetime.strptime(upload_date, '%Y%m%d').replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            videos.append({
                'id': video_id,
                'title': title,
                'views': views,
                'publish_date': publish_date,
                'url': url if url.startswith('http') else f'https://www.youtube.com/watch?v={video_id}'
            })

        print(f"  ✓ Found {len(videos)} videos with valid data")
        return videos

    except subprocess.TimeoutExpired:
        print(f"  ⚠ Timeout fetching channel")
        return []
    except Exception as e:
        print(f"  ⚠ Error: {e}")
        return []


def calculate_days_since_upload(publish_date: datetime) -> float:
    """Calculate days since video was uploaded."""
    now = datetime.now(timezone.utc)
    delta = now - publish_date
    return delta.total_seconds() / 86400  # Convert to days


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


def analyze_channel(
    channel_url: str,
    videos_per_channel: int,
    baseline_videos: int,
    days_window: int,
    min_views: int
) -> List[Dict]:
    """
    Analyze a channel and find outlier videos.

    Args:
        channel_url: Channel URL or @handle
        videos_per_channel: Number of recent videos to fetch
        baseline_videos: Number of videos to use for baseline calculation
        days_window: Only consider videos from last N days
        min_views: Minimum view threshold

    Returns:
        List of outlier video dictionaries
    """
    # Fetch videos
    videos = get_channel_videos(channel_url, videos_per_channel)

    if not videos:
        print(f"  ⚠ No videos found for {channel_url}")
        return []

    # Calculate views per day for all videos
    epsilon = 100  # Small value to avoid division by zero

    for video in videos:
        days_since = calculate_days_since_upload(video['publish_date'])
        video['days_since'] = days_since
        video['views_per_day'] = video['views'] / max(days_since, 1)

    # Calculate baseline from most recent baseline_videos
    baseline_count = min(baseline_videos, len(videos))
    baseline_vpd_values = [v['views_per_day'] for v in videos[:baseline_count]]
    baseline_vpd = calculate_median(baseline_vpd_values)

    print(f"  Baseline VPD (median of {baseline_count} videos): {baseline_vpd:.2f}")

    # Find outliers
    outliers = []

    for video in videos:
        # Check if video is within days window
        if video['days_since'] > days_window:
            continue

        # Check minimum views threshold
        if video['views'] < min_views:
            continue

        # Calculate outlier score
        outlier_score = video['views_per_day'] / max(baseline_vpd, epsilon)

        # Calculate recency boost
        recency_boost = 1 + 0.5 * math.exp(-video['days_since'] / 14)

        # Calculate final score
        final_score = outlier_score * recency_boost

        # Mark as outlier if score >= 3.0
        if final_score >= 3.0:
            outliers.append({
                'channel': channel_url,
                'video_title': video['title'],
                'video_url': video['url'],
                'publish_date': video['publish_date'].strftime('%Y-%m-%d'),
                'days_since': round(video['days_since'], 1),
                'views': video['views'],
                'views_per_day': round(video['views_per_day'], 2),
                'baseline_vpd': round(baseline_vpd, 2),
                'outlier_score': round(outlier_score, 2),
                'recency_boost': round(recency_boost, 2),
                'final_score': round(final_score, 2)
            })

    if outliers:
        print(f"  🎯 Found {len(outliers)} outlier(s)")
    else:
        print(f"  No outliers found")

    return outliers


def write_csv_output(outliers: List[Dict], output_file: str) -> None:
    """Write outliers to CSV file."""
    if not outliers:
        print(f"\n⚠ No outliers to write")
        return

    fieldnames = [
        'channel', 'video_title', 'video_url', 'publish_date', 'days_since',
        'views', 'views_per_day', 'baseline_vpd', 'outlier_score',
        'recency_boost', 'final_score'
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
        print("  Skipping Google Sheets output...")
        return

    if not outliers:
        print(f"\n⚠ No outliers to write to Google Sheets")
        return

    try:
        # Define scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Load credentials from service account JSON
        creds = Credentials.from_service_account_file(
            'service_account.json',
            scopes=scopes
        )

        client = gspread.authorize(creds)

        # Open spreadsheet
        sheet = client.open_by_key(sheet_id).sheet1

        # Clear existing data
        sheet.clear()

        # Prepare data
        headers = [
            'Channel', 'Video Title', 'Video URL', 'Publish Date', 'Days Since',
            'Views', 'Views/Day', 'Baseline VPD', 'Outlier Score',
            'Recency Boost', 'Final Score'
        ]

        rows = [headers]
        for outlier in outliers:
            rows.append([
                outlier['channel'],
                outlier['video_title'],
                outlier['video_url'],
                outlier['publish_date'],
                outlier['days_since'],
                outlier['views'],
                outlier['views_per_day'],
                outlier['baseline_vpd'],
                outlier['outlier_score'],
                outlier['recency_boost'],
                outlier['final_score']
            ])

        # Write to sheet
        sheet.update('A1', rows)

        print(f"\n✓ Results written to Google Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")

    except FileNotFoundError:
        print("\n⚠ service_account.json not found. Skipping Google Sheets output.")
        print("  See README for setup instructions.")
    except Exception as e:
        print(f"\n⚠ Error writing to Google Sheets: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Find YouTube video outliers using free yt-dlp tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python outlier_detector.py
  python outlier_detector.py --videos-per-channel 300 --days-window 60
  python outlier_detector.py --sheet YOUR_SHEET_ID
  python outlier_detector.py --output my_outliers.csv

Input file (channels.txt) format:
  https://www.youtube.com/@channelname
  @channelname
  https://www.youtube.com/c/ChannelName
        """
    )

    parser.add_argument(
        '--videos-per-channel',
        type=int,
        default=200,
        help='Number of recent videos to fetch per channel (default: 200)'
    )
    parser.add_argument(
        '--baseline-videos',
        type=int,
        default=60,
        help='Number of videos for baseline calculation (default: 60)'
    )
    parser.add_argument(
        '--days-window',
        type=int,
        default=30,
        help='Only consider videos from last N days (default: 30)'
    )
    parser.add_argument(
        '--min-views',
        type=int,
        default=5000,
        help='Minimum view threshold (default: 5000)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='outliers.csv',
        help='Output CSV file (default: outliers.csv)'
    )
    parser.add_argument(
        '--sheet',
        type=str,
        default=None,
        help='Google Sheet ID for output (optional)'
    )
    parser.add_argument(
        '--channels',
        type=str,
        default='channels.txt',
        help='Input file with channel URLs (default: channels.txt)'
    )

    args = parser.parse_args()

    # Check if yt-dlp is installed
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ yt-dlp not found. Please install it:")
        print("  pip install yt-dlp")
        print("  or: brew install yt-dlp")
        sys.exit(1)

    # Read channels from file
    channels_file = Path(args.channels)
    if not channels_file.exists():
        print(f"⚠ Channels file not found: {args.channels}")
        print(f"\nCreate a {args.channels} file with one channel URL or @handle per line:")
        print("  @mkbhd")
        print("  https://www.youtube.com/@veritasium")
        sys.exit(1)

    channels = []
    with open(channels_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                channels.append(line)

    if not channels:
        print(f"⚠ No channels found in {args.channels}")
        sys.exit(1)

    print(f"🔍 YouTube Outlier Detector")
    print(f"  Analyzing {len(channels)} channel(s)")
    print(f"  Settings:")
    print(f"    - Videos per channel: {args.videos_per_channel}")
    print(f"    - Baseline videos: {args.baseline_videos}")
    print(f"    - Days window: {args.days_window}")
    print(f"    - Min views: {args.min_views}")
    print(f"    - Output: {args.output}")
    if args.sheet:
        print(f"    - Google Sheet: {args.sheet}")
    print()

    # Analyze all channels
    all_outliers = []

    for i, channel in enumerate(channels, 1):
        print(f"[{i}/{len(channels)}] Analyzing: {channel}")

        outliers = analyze_channel(
            channel,
            args.videos_per_channel,
            args.baseline_videos,
            args.days_window,
            args.min_views
        )

        all_outliers.extend(outliers)
        print()

    # Sort by final score (descending)
    all_outliers.sort(key=lambda x: x['final_score'], reverse=True)

    # Write outputs
    write_csv_output(all_outliers, args.output)

    if args.sheet:
        write_google_sheets_output(all_outliers, args.sheet)

    # Summary
    if all_outliers:
        print(f"\n🎉 Analysis complete!")
        print(f"  Top outlier: {all_outliers[0]['video_title']}")
        print(f"  Score: {all_outliers[0]['final_score']}")


if __name__ == '__main__':
    main()
