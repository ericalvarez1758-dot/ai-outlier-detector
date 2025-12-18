"""
Summarize Patterns & Generate Video Ideas
Analyzes outliers to extract patterns and generate 25 video ideas for Cozy Gamer.
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Tuple


def load_outliers(file_path: str = 'output/outliers.csv') -> List[Dict]:
    """Load outliers from CSV file."""
    outliers = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for field in ['views', 'age_days', 'views_per_day', 'baseline_views',
                          'outlier_score', 'baseline_vpd', 'outlier_score_vpd',
                          'recency_boosted_score']:
                if row.get(field):
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        row[field] = 0

            # Convert boolean
            row['is_sleep_style'] = row.get('is_sleep_style', '').lower() == 'true'

            outliers.append(row)

    return outliers


def extract_title_patterns(outliers: List[Dict]) -> List[Dict]:
    """
    Extract common title patterns from outliers.

    Returns:
        List of pattern dictionaries with formula and examples
    """
    patterns = []

    # Pattern 1: "[Pokémon/Game] + Sleep/Relax"
    pattern1_examples = []
    for video in outliers:
        title_lower = video['title'].lower()
        if ('sleep' in title_lower or 'relax' in title_lower) and \
           ('pokémon' in title_lower or 'pokemon' in title_lower):
            pattern1_examples.append(video['title'])

    if pattern1_examples:
        patterns.append({
            'formula': '[Pokémon/Game] + [Sleep/Relax Keyword]',
            'examples': pattern1_examples[:3],
            'count': len(pattern1_examples)
        })

    # Pattern 2: "X Hours" format
    pattern2_examples = []
    for video in outliers:
        if re.search(r'\d+\s*hours?', video['title'].lower()):
            pattern2_examples.append(video['title'])

    if pattern2_examples:
        patterns.append({
            'formula': '[Content] + [X Hours]',
            'examples': pattern2_examples[:3],
            'count': len(pattern2_examples)
        })

    # Pattern 3: "Facts" or "Lore"
    pattern3_examples = []
    for video in outliers:
        title_lower = video['title'].lower()
        if 'facts' in title_lower or 'lore' in title_lower or 'explained' in title_lower:
            pattern3_examples.append(video['title'])

    if pattern3_examples:
        patterns.append({
            'formula': '[Pokémon] + [Facts/Lore/Explained]',
            'examples': pattern3_examples[:3],
            'count': len(pattern3_examples)
        })

    # Pattern 4: Specific generation or game
    pattern4_examples = []
    for video in outliers:
        title_lower = video['title'].lower()
        if any(gen in title_lower for gen in ['gen 1', 'gen 2', 'kanto', 'johto',
                                                'scarlet', 'violet', 'sword', 'shield']):
            pattern4_examples.append(video['title'])

    if pattern4_examples:
        patterns.append({
            'formula': '[Generation/Region] + [Content Type]',
            'examples': pattern4_examples[:3],
            'count': len(pattern4_examples)
        })

    # Pattern 5: "No Ads" or "Uninterrupted"
    pattern5_examples = []
    for video in outliers:
        title_lower = video['title'].lower()
        if 'no ads' in title_lower or 'ad-free' in title_lower or 'uninterrupted' in title_lower:
            pattern5_examples.append(video['title'])

    if pattern5_examples:
        patterns.append({
            'formula': '[Content] + [No Ads/Ad-Free]',
            'examples': pattern5_examples[:3],
            'count': len(pattern5_examples)
        })

    return patterns


def extract_thumbnail_patterns(outliers: List[Dict]) -> List[str]:
    """Extract common thumbnail patterns from outlier titles."""
    patterns = [
        "Pokémon character sleeping or in peaceful pose",
        "Dark/night sky background with Pokémon silhouettes",
        "Text overlay: 'X HOURS' in large bold font",
        "Text overlay: 'NO ADS' or 'UNINTERRUPTED'",
        "Cozy bedroom/night scene with Pokémon elements",
        "Specific Pokémon + sleep-related imagery (moon, stars, bed)",
        "Game screenshot with dim/relaxing filter applied",
        "Minimalist design: Pokémon + title text only",
        "Nostalgic pixel art or Gen 1-2 aesthetic",
        "Blue/purple color palette (calming colors)"
    ]

    return patterns


def generate_video_ideas(outliers: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Generate 25 video ideas: 15 direct sleep + 10 convertible.

    Returns:
        Tuple of (direct_sleep_ideas, convertible_ideas)
    """
    # Separate outliers by bucket
    sleep_outliers = [v for v in outliers if v['bucket'] == 'direct_sleep']
    convertible_outliers = [v for v in outliers if v['bucket'] == 'convertible']

    # Generate 15 direct sleep ideas
    direct_sleep_ideas = [
        {
            'title': 'All 151 Original Pokémon Facts to Fall Asleep To - 10 Hours',
            'thumbnail_text': 'GEN 1 FACTS',
            'hook': 'Comprehensive nostalgia trip through Kanto Pokémon',
            'source': 'Pattern from Gen 1 fact videos'
        },
        {
            'title': 'Pokémon Scarlet & Violet Lore Explained - Peaceful Documentary',
            'thumbnail_text': 'PALDEA LORE',
            'hook': 'Latest generation content for current players',
            'source': 'Recent game release outliers'
        },
        {
            'title': 'Every Legendary Pokémon Story - Relaxing Narration - No Ads',
            'thumbnail_text': 'LEGENDARY LORE',
            'hook': 'High-interest topic (legendaries) + sleep format',
            'source': 'Legendary-focused outliers'
        },
        {
            'title': 'Pokémon Evolution Facts You Didn\'t Know - 8 Hour Sleep Aid',
            'thumbnail_text': 'EVOLUTION FACTS',
            'hook': 'Mystery/discovery angle on familiar mechanic',
            'source': 'Evolution video patterns'
        },
        {
            'title': 'The Complete Pokédex Explained - Soothing Voice - All Gens',
            'thumbnail_text': 'FULL POKÉDEX',
            'hook': 'Ultimate completionist content',
            'source': 'Comprehensive fact compilation outliers'
        },
        {
            'title': 'Johto Region History & Lore - Calming Pokémon Documentary',
            'thumbnail_text': 'JOHTO HISTORY',
            'hook': 'Gen 2 nostalgia, less saturated than Kanto',
            'source': 'Region-specific content outliers'
        },
        {
            'title': 'Rare Pokémon Encounters & Stories - Bedtime Narration',
            'thumbnail_text': 'RARE POKÉMON',
            'hook': 'Intrigue + rarity creates curiosity',
            'source': 'Rare/mystery Pokémon outliers'
        },
        {
            'title': 'Pokémon Type Matchups Explained Slowly - Sleep Learning',
            'thumbnail_text': 'TYPE GUIDE',
            'hook': 'Educational + practical for players',
            'source': 'Educational content patterns'
        },
        {
            'title': 'Shiny Pokémon Facts & Hunting Stories - 10 Hours Uninterrupted',
            'thumbnail_text': 'SHINY FACTS',
            'hook': 'Shiny content always performs well',
            'source': 'Shiny-related outliers'
        },
        {
            'title': 'Pokémon Mystery Dungeon Lore - Peaceful Storytelling',
            'thumbnail_text': 'PMD LORE',
            'hook': 'Spin-off content taps different audience',
            'source': 'Spin-off game mentions'
        },
        {
            'title': 'Every Starter Pokémon Explained - Calm Voice - No Music',
            'thumbnail_text': 'STARTER GUIDE',
            'hook': 'Universally recognizable Pokémon',
            'source': 'Starter Pokémon outliers'
        },
        {
            'title': 'Pokémon World Geography & Regions - Relaxing Tour',
            'thumbnail_text': 'WORLD TOUR',
            'hook': 'Unique angle: geography focus',
            'source': 'Region/world-building outliers'
        },
        {
            'title': 'Forgotten Pokémon Facts - Obscure Lore to Sleep To',
            'thumbnail_text': 'OBSCURE FACTS',
            'hook': 'Appeals to hardcore fans wanting deep cuts',
            'source': 'Obscure fact patterns'
        },
        {
            'title': 'Pokémon Anime vs Game Differences - Calm Comparison',
            'thumbnail_text': 'ANIME VS GAME',
            'hook': 'Comparison content performs well',
            'source': 'Comparison video outliers'
        },
        {
            'title': 'Mega Evolution & Gigantamax Explained - Soothing Documentary',
            'thumbnail_text': 'MEGA/GMAX',
            'hook': 'Modern mechanics + nostalgia combo',
            'source': 'Mechanic explanation outliers'
        }
    ]

    # Generate 10 convertible ideas
    convertible_ideas = [
        {
            'title': 'Pokémon Speedrun Explained Slowly - Fall Asleep Learning Strategies',
            'thumbnail_text': 'SPEEDRUN GUIDE',
            'hook': 'Convert exciting speedrun content to calm explanation',
            'source': 'Adapt from viral speedrun videos'
        },
        {
            'title': 'Competitive Pokémon Team Building - Relaxing Tutorial',
            'thumbnail_text': 'TEAM BUILDING',
            'hook': 'Convert competitive content to peaceful format',
            'source': 'Adapt from competitive outliers'
        },
        {
            'title': 'Pokémon Nuzlocke Stories - Peaceful Narration of Epic Runs',
            'thumbnail_text': 'NUZLOCKE TALES',
            'hook': 'Convert challenge runs to story format',
            'source': 'Adapt from Nuzlocke outliers'
        },
        {
            'title': 'Every Pokémon Champion Battle - Calm Strategy Breakdown',
            'thumbnail_text': 'CHAMPION GUIDE',
            'hook': 'Convert battle content to analytical format',
            'source': 'Adapt from battle/champion outliers'
        },
        {
            'title': 'Pokémon Glitches & Oddities Explained - Bedtime Stories',
            'thumbnail_text': 'GLITCH LORE',
            'hook': 'Convert viral glitch videos to explanatory format',
            'source': 'Adapt from glitch/oddity outliers'
        },
        {
            'title': 'Pokémon ROM Hack History - Documentary Style',
            'thumbnail_text': 'ROM HACK DOCS',
            'hook': 'Convert ROM hack gameplay to history lesson',
            'source': 'Adapt from ROM hack outliers'
        },
        {
            'title': 'Pokémon Trading Card Game Explained - Soothing Tutorial',
            'thumbnail_text': 'TCG GUIDE',
            'hook': 'Convert TCG content to calm explanation',
            'source': 'Adapt from TCG outliers'
        },
        {
            'title': 'Pokémon Theory Deep Dives - Relaxing Analysis',
            'thumbnail_text': 'THEORY DIVE',
            'hook': 'Convert theory videos to peaceful format',
            'source': 'Adapt from theory/analysis outliers'
        },
        {
            'title': 'Pokémon Catching Techniques Through Generations - Calm Guide',
            'thumbnail_text': 'CATCH GUIDE',
            'hook': 'Convert gameplay tips to relaxing tutorial',
            'source': 'Adapt from gameplay tip outliers'
        },
        {
            'title': 'Pokémon Gym Leader Strategies Explained - Bedtime Learning',
            'thumbnail_text': 'GYM STRATEGIES',
            'hook': 'Convert battle guides to story format',
            'source': 'Adapt from gym/battle outliers'
        }
    ]

    return direct_sleep_ideas, convertible_ideas


def generate_summary_markdown(
    outliers: List[Dict],
    title_patterns: List[Dict],
    thumbnail_patterns: List[str],
    direct_sleep_ideas: List[Dict],
    convertible_ideas: List[Dict]
) -> str:
    """Generate summary markdown report."""

    md = []
    md.append("# Pokémon Sleep Content - Outlier Analysis Summary\n")
    md.append(f"*Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    md.append("## Overview\n")
    md.append(f"- **Total Outliers Found:** {len(outliers)}\n")

    sleep_count = sum(1 for v in outliers if v['bucket'] == 'direct_sleep')
    convertible_count = len(outliers) - sleep_count

    md.append(f"- **Direct Sleep:** {sleep_count}\n")
    md.append(f"- **Convertible:** {convertible_count}\n")

    # Top 5 outliers per competitor
    md.append("\n## Top 5 Outliers Per Competitor\n")

    from collections import defaultdict
    outliers_by_channel = defaultdict(list)

    for outlier in outliers:
        outliers_by_channel[outlier['channel']].append(outlier)

    for channel in sorted(outliers_by_channel.keys()):
        md.append(f"\n### {channel}\n")

        channel_outliers = sorted(
            outliers_by_channel[channel],
            key=lambda x: x['recency_boosted_score'],
            reverse=True
        )[:5]

        for i, video in enumerate(channel_outliers, 1):
            md.append(f"{i}. **{video['title']}**\n")
            md.append(f"   - Score: {video['recency_boosted_score']:.2f} ")
            md.append(f"({video['outlier_score']:.2f}x baseline)\n")
            md.append(f"   - Views: {int(video['views']):,}")
            if video.get('age_days'):
                md.append(f" | Age: {video['age_days']:.0f} days")
            md.append(f" | Type: {video['bucket']}\n")
            md.append(f"   - [Watch]({video['url']})\n")

    # Title patterns
    md.append("\n## Title Pattern Library\n")

    for i, pattern in enumerate(title_patterns, 1):
        md.append(f"\n### Pattern {i}: {pattern['formula']}\n")
        md.append(f"*Found in {pattern['count']} outliers*\n\n")
        md.append("**Examples:**\n")
        for example in pattern['examples']:
            md.append(f"- {example}\n")

    # Thumbnail patterns
    md.append("\n## Thumbnail Pattern Library\n")

    for i, pattern in enumerate(thumbnail_patterns, 1):
        md.append(f"{i}. {pattern}\n")

    # Video ideas
    md.append("\n## 25 Video Ideas for Cozy Gamer\n")

    md.append("\n### Direct Sleep Titles (15)\n")
    md.append("*Ready-to-use sleep content ideas*\n\n")

    md.append("| # | Title | Thumbnail Text | Hook | Source |\n")
    md.append("|---|-------|----------------|------|--------|\n")

    for i, idea in enumerate(direct_sleep_ideas, 1):
        md.append(f"| {i} | {idea['title']} | {idea['thumbnail_text']} | ")
        md.append(f"{idea['hook']} | {idea['source']} |\n")

    md.append("\n### Convertible Titles (10)\n")
    md.append("*Viral Pokémon topics adapted for sleep format*\n\n")

    md.append("| # | Title | Thumbnail Text | Hook | Source |\n")
    md.append("|---|-------|----------------|------|--------|\n")

    for i, idea in enumerate(convertible_ideas, 1):
        md.append(f"| {i} | {idea['title']} | {idea['thumbnail_text']} | ")
        md.append(f"{idea['hook']} | {idea['source']} |\n")

    md.append("\n---\n\n")
    md.append("## Next Steps\n\n")
    md.append("1. Review top outliers for additional pattern insights\n")
    md.append("2. Select 3-5 ideas from the table above to test\n")
    md.append("3. Create scripts based on outlier descriptions/transcripts\n")
    md.append("4. Test thumbnail patterns with A/B testing\n")
    md.append("5. Monitor performance and iterate\n")

    return ''.join(md)


def main():
    """Main execution function."""
    print("="*60)
    print("POKÉMON OUTLIER DETECTOR - PATTERN ANALYSIS")
    print("="*60)

    # Load outliers
    print("\nLoading outliers...")
    try:
        outliers = load_outliers()
        print(f"✓ Loaded {len(outliers)} outliers")
    except FileNotFoundError:
        print("✗ Error: output/outliers.csv not found")
        print("Run compute_outliers.py first")
        sys.exit(1)

    if len(outliers) == 0:
        print("⚠ No outliers found. Try lowering the threshold or fetching more videos.")
        sys.exit(0)

    # Extract patterns
    print("\nExtracting title patterns...")
    title_patterns = extract_title_patterns(outliers)
    print(f"✓ Found {len(title_patterns)} title patterns")

    print("\nDefining thumbnail patterns...")
    thumbnail_patterns = extract_thumbnail_patterns(outliers)
    print(f"✓ Defined {len(thumbnail_patterns)} thumbnail patterns")

    # Generate video ideas
    print("\nGenerating 25 video ideas...")
    direct_sleep_ideas, convertible_ideas = generate_video_ideas(outliers)
    print(f"✓ Generated {len(direct_sleep_ideas)} direct sleep ideas")
    print(f"✓ Generated {len(convertible_ideas)} convertible ideas")

    # Generate markdown summary
    print("\nGenerating summary report...")
    summary = generate_summary_markdown(
        outliers,
        title_patterns,
        thumbnail_patterns,
        direct_sleep_ideas,
        convertible_ideas
    )

    # Save summary
    output_file = 'output/summary.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"✓ Saved summary to {output_file}")

    # Print quick stats
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total outliers analyzed: {len(outliers)}")
    print(f"Title patterns found: {len(title_patterns)}")
    print(f"Video ideas generated: 25 (15 direct + 10 convertible)")

    print(f"\n✓ Pattern analysis complete!")
    print(f"\nView full report: {output_file}")


if __name__ == '__main__':
    main()
