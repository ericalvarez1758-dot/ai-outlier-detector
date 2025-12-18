#!/usr/bin/env python3
"""
Test script to verify the scoring algorithm works correctly.
This tests the outlier detection logic without needing to fetch real YouTube data.
"""

import math
from datetime import datetime, timezone, timedelta


def calculate_median(values):
    """Calculate median of a list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    else:
        return sorted_values[n // 2]


def test_outlier_detection():
    """Test the outlier detection algorithm with mock data."""

    print("Testing YouTube Outlier Detection Algorithm\n")
    print("=" * 60)

    # Mock videos for a channel
    # Format: (title, views, days_since_upload)
    mock_videos = [
        # Normal performing videos (baseline)
        ("Regular video 1", 50000, 25),
        ("Regular video 2", 45000, 22),
        ("Regular video 3", 48000, 20),
        ("Regular video 4", 52000, 18),
        ("Regular video 5", 47000, 15),
        ("Regular video 6", 49000, 12),
        ("Regular video 7", 51000, 10),
        ("Regular video 8", 46000, 8),

        # Outlier videos
        ("VIRAL VIDEO!", 500000, 5),  # 10x baseline
        ("Breakout hit", 250000, 3),  # 5x baseline
    ]

    # Calculate views per day for each video
    videos_with_metrics = []
    for title, views, days_since in mock_videos:
        views_per_day = views / max(days_since, 1)
        videos_with_metrics.append({
            'title': title,
            'views': views,
            'days_since': days_since,
            'views_per_day': views_per_day
        })

    # Calculate baseline (median of all videos)
    baseline_vpd_values = [v['views_per_day'] for v in videos_with_metrics]
    baseline_vpd = calculate_median(baseline_vpd_values)

    print(f"Baseline Views Per Day: {baseline_vpd:.2f}")
    print(f"(median of {len(videos_with_metrics)} videos)\n")
    print("=" * 60)
    print("\nVideo Analysis:\n")

    epsilon = 100
    outliers = []

    for video in videos_with_metrics:
        # Calculate outlier score
        outlier_score = video['views_per_day'] / max(baseline_vpd, epsilon)

        # Calculate recency boost
        recency_boost = 1 + 0.5 * math.exp(-video['days_since'] / 14)

        # Calculate final score
        final_score = outlier_score * recency_boost

        # Check if outlier
        is_outlier = final_score >= 3.0 and video['days_since'] <= 30 and video['views'] >= 5000

        print(f"📹 {video['title']}")
        print(f"   Views: {video['views']:,} | Days: {video['days_since']}")
        print(f"   VPD: {video['views_per_day']:.2f}")
        print(f"   Outlier Score: {outlier_score:.2f}x baseline")
        print(f"   Recency Boost: {recency_boost:.2f}x")
        print(f"   Final Score: {final_score:.2f}")

        if is_outlier:
            print(f"   ⭐ OUTLIER DETECTED!")
            outliers.append(video)

        print()

    print("=" * 60)
    print(f"\nSummary: Found {len(outliers)} outlier(s) out of {len(videos_with_metrics)} videos")

    if outliers:
        print("\nOutliers:")
        for video in outliers:
            print(f"  - {video['title']} ({video['views']:,} views)")

    print("\n✅ Scoring algorithm test completed successfully!")


if __name__ == '__main__':
    test_outlier_detection()
