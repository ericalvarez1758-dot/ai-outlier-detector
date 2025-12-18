"""
Compute Outliers
Calculates outlier scores for videos using per-channel baselines.
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


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


def parse_date(date_str: str) -> datetime:
    """
    Parse date string to datetime object.

    Args:
        date_str: Date string in various formats

    Returns:
        datetime object
    """
    if not date_str:
        raise ValueError("Empty date string")

    # Try multiple formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ'
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    # Try ISO format as fallback
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f"Could not parse date: {date_str}")


def calculate_age_days(published_at: str) -> float:
    """
    Calculate days since video was published.

    Args:
        published_at: Publish date string

    Returns:
        Days since publication
    """
    try:
        publish_date = parse_date(published_at)
        now = datetime.now(timezone.utc)
        delta = now - publish_date
        return delta.total_seconds() / 86400
    except (ValueError, AttributeError):
        return None


def is_sleep_style(title: str, description: str) -> bool:
    """
    Check if video is already in sleep/relax style.

    Args:
        title: Video title
        description: Video description

    Returns:
        True if sleep-style content
    """
    text = (title + ' ' + (description or '')).lower()

    sleep_keywords = [
        'fall asleep',
        'to sleep',
        'sleep',
        'tonight',
        'relaxing',
        'calm',
        'soothing',
        'documentary',
        'bedtime',
        'facts to hear',
        'peaceful',
        'to relax',
        'chill',
        'ambient',
        'asmr'
    ]

    return any(keyword in text for keyword in sleep_keywords)


def compute_channel_baseline(videos: List[Dict]) -> Tuple[float, float]:
    """
    Compute baseline metrics for a channel.

    Args:
        videos: List of videos from the channel

    Returns:
        Tuple of (baseline_views, baseline_vpd)
    """
    # Calculate baseline views (median)
    views_list = [v['views'] for v in videos if v['views'] > 0]
    baseline_views = calculate_median(views_list) if views_list else 0

    # Calculate baseline views per day (median)
    vpd_list = []
    for video in videos:
        if video['views'] > 0 and video.get('age_days'):
            vpd = video['views'] / max(video['age_days'], 1)
            vpd_list.append(vpd)

    baseline_vpd = calculate_median(vpd_list) if vpd_list else 0

    return baseline_views, baseline_vpd


def compute_outlier_scores(
    videos: List[Dict],
    baseline_views: float,
    baseline_vpd: float
) -> List[Dict]:
    """
    Calculate outlier scores for videos.

    Args:
        videos: List of videos
        baseline_views: Channel baseline views
        baseline_vpd: Channel baseline views per day

    Returns:
        List of videos with outlier scores
    """
    scored_videos = []

    for video in videos:
        # Calculate base outlier score
        if baseline_views > 0:
            outlier_score = video['views'] / baseline_views
        else:
            outlier_score = 0

        # Calculate VPD-based outlier score
        age_days = video.get('age_days')
        if age_days and age_days > 0:
            views_per_day = video['views'] / age_days
            outlier_score_vpd = views_per_day / baseline_vpd if baseline_vpd > 0 else 0
        else:
            views_per_day = None
            outlier_score_vpd = 0

        # Apply recency boost
        if age_days is not None:
            if age_days <= 30:
                recency_boost = 1.15
            elif age_days <= 60:
                recency_boost = 1.05
            else:
                recency_boost = 1.0

            recency_boosted_score = outlier_score * recency_boost
        else:
            recency_boost = 1.0
            recency_boosted_score = outlier_score

        # Check if sleep style
        sleep_style = is_sleep_style(video['title'], video.get('description', ''))

        # Determine bucket
        bucket = 'direct_sleep' if sleep_style else 'convertible'

        # Add scores to video
        scored_video = video.copy()
        scored_video.update({
            'views_per_day': round(views_per_day, 2) if views_per_day else None,
            'baseline_views': round(baseline_views, 2),
            'outlier_score': round(outlier_score, 2),
            'baseline_vpd': round(baseline_vpd, 2),
            'outlier_score_vpd': round(outlier_score_vpd, 2),
            'recency_boost': recency_boost,
            'recency_boosted_score': round(recency_boosted_score, 2),
            'is_sleep_style': sleep_style,
            'bucket': bucket
        })

        scored_videos.append(scored_video)

    return scored_videos


def filter_outliers(
    videos: List[Dict],
    min_outlier_score: float = 1.5
) -> List[Dict]:
    """
    Filter videos to keep only outliers.

    Args:
        videos: List of scored videos
        min_outlier_score: Minimum outlier score threshold

    Returns:
        List of outlier videos
    """
    outliers = []

    for video in videos:
        # Keep if outlier_score >= 1.5 OR outlier_score_vpd >= 1.5
        if (video['outlier_score'] >= min_outlier_score or
            video['outlier_score_vpd'] >= min_outlier_score):
            outliers.append(video)

    return outliers


def main():
    """Main execution function."""
    print("="*60)
    print("POKÉMON OUTLIER DETECTOR - SCORING")
    print("="*60)

    # Load raw videos
    input_file = 'output/raw_videos.json'
    print(f"\nLoading videos from {input_file}...")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_videos = json.load(f)
        print(f"✓ Loaded {len(all_videos)} videos")
    except FileNotFoundError:
        print(f"✗ Error: {input_file} not found")
        print("Run fetch_competitors.py first")
        sys.exit(1)

    # Calculate age for all videos
    print("\nCalculating video ages...")
    for video in all_videos:
        if video.get('published_at'):
            age = calculate_age_days(video['published_at'])
            video['age_days'] = round(age, 1) if age else None
        else:
            video['age_days'] = None

    # Group by channel
    print("\nGrouping by channel...")
    from collections import defaultdict
    videos_by_channel = defaultdict(list)

    for video in all_videos:
        videos_by_channel[video['channel']].append(video)

    print(f"✓ Found {len(videos_by_channel)} channels")

    # Compute outliers per channel
    print("\nComputing outliers per channel...")
    all_outliers = []

    for channel, videos in videos_by_channel.items():
        print(f"\n  {channel}:")
        print(f"    Total videos: {len(videos)}")

        # Compute baseline
        baseline_views, baseline_vpd = compute_channel_baseline(videos)
        print(f"    Baseline views: {baseline_views:.0f}")
        print(f"    Baseline VPD: {baseline_vpd:.2f}")

        # Score videos
        scored = compute_outlier_scores(videos, baseline_views, baseline_vpd)

        # Filter outliers
        outliers = filter_outliers(scored, min_outlier_score=1.5)
        print(f"    Outliers found: {len(outliers)}")

        # Count sleep vs convertible
        sleep_count = sum(1 for v in outliers if v['is_sleep_style'])
        convertible_count = len(outliers) - sleep_count
        print(f"      Direct sleep: {sleep_count}")
        print(f"      Convertible: {convertible_count}")

        all_outliers.extend(outliers)

    # Sort by recency-boosted score
    all_outliers.sort(key=lambda x: x['recency_boosted_score'], reverse=True)

    # Save outliers to CSV
    print(f"\n{'='*60}")
    print("SAVING OUTLIERS")
    print(f"{'='*60}")

    output_file = 'output/outliers.csv'

    fieldnames = [
        'channel', 'video_id', 'title', 'published_at', 'views', 'duration',
        'age_days', 'views_per_day', 'baseline_views', 'outlier_score',
        'baseline_vpd', 'outlier_score_vpd', 'recency_boosted_score',
        'is_sleep_style', 'bucket', 'url', 'thumbnail_url'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for outlier in all_outliers:
            # Create row with only required fields
            row = {field: outlier.get(field, '') for field in fieldnames}
            writer.writerow(row)

    print(f"✓ Saved {len(all_outliers)} outliers to {output_file}")

    # Summary stats
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total outliers: {len(all_outliers)}")

    sleep_count = sum(1 for v in all_outliers if v['is_sleep_style'])
    convertible_count = len(all_outliers) - sleep_count

    print(f"  Direct sleep: {sleep_count}")
    print(f"  Convertible: {convertible_count}")

    print(f"\nTop 5 outliers:")
    for i, video in enumerate(all_outliers[:5], 1):
        print(f"  {i}. {video['title'][:60]}...")
        print(f"     Channel: {video['channel']}")
        print(f"     Score: {video['recency_boosted_score']} ({video['bucket']})")

    print(f"\n✓ Outlier computation complete!")
    print(f"Next step: Run summarize_patterns.py to generate video ideas")


if __name__ == '__main__':
    main()
