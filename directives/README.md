# Pokémon Sleep Content Outlier Detection System

## Overview

This system analyzes competitor channels in the "Pokémon to Fall Asleep To" niche to identify winning video formats and generate new content ideas.

## Hard Rules

### 1. Pokémon Content ONLY
- Filter aggressively for Pokémon-only results
- No Animal Crossing, Mario, Zelda, or other franchises
- Validate content against Pokémon keywords

### 2. Competitors First
- Always analyze provided competitors before expanding
- Use their recent uploads to establish baselines
- Per-channel analysis (no cross-channel comparisons)

### 3. Recency Matters
- Prefer videos from last 90 days
- If unavailable, use latest 30-60 uploads per channel
- Apply recency boost to recent outliers

### 4. No Learned Averages
- All outlier scores computed per-channel using that channel's median
- Never compare channels directly to each other
- Each channel has its own baseline

### 5. No Hallucinated Data
- Use only metrics returned by TubeLab API
- If metric unavailable, explicitly state it and skip
- No assumptions or estimates

### 6. Output Separation
- **Direct Sleep Winners**: Already in "to fall asleep to" style
- **Convertible Winners**: Viral Pokémon videos adaptable to sleep format

## Target Channel

**Cozy Gamer** - Pokémon facts & lore to fall asleep to

## Competitor Channels

1. Fallasleepmon
2. Boring Gamer
3. Stellar Sleep
4. BlueBoyPhin
5. Sleepy Gamer
6. PokeSleep
7. PokeRest

## Outlier Scoring Logic

### Step 1: Establish Baseline
```python
baseline_views = median(views of recent uploads)
baseline_vpd = median(views_per_day of recent uploads)
```

### Step 2: Calculate Outlier Score
```python
outlier_score = views / baseline_views
```

### Step 3: Views Per Day (if publish date available)
```python
age_days = today - publish_date
views_per_day = views / age_days
outlier_score_vpd = views_per_day / baseline_vpd
```

### Step 4: Recency Boost
```python
if age_days <= 30:
    recency_boosted_score = outlier_score * 1.15
elif age_days <= 60:
    recency_boosted_score = outlier_score * 1.05
else:
    recency_boosted_score = outlier_score
```

### Step 5: Filtering
Keep video if:
- `outlier_score >= 1.5` OR
- `outlier_score_vpd >= 1.5`

## Sleep Classification

Mark as **"Direct Sleep"** if title or description contains:
- fall asleep
- sleep
- tonight
- relaxing
- calm
- soothing
- documentary
- bedtime
- facts to hear

Otherwise mark as **"Convertible"**

## Workflow

### 1. Data Collection (`fetch_competitors.py`)
- Fetch recent uploads from each competitor channel
- Get video stats (views, publish date, duration)
- Filter for Pokémon content only

### 2. Outlier Computation (`compute_outliers.py`)
- Calculate per-channel baselines
- Score each video
- Apply recency boost
- Filter outliers (>= 1.5x baseline)
- Classify as Direct Sleep or Convertible

### 3. Pattern Analysis (`summarize_patterns.py`)
- Extract title patterns (formulas)
- Identify thumbnail patterns (visual rules)
- Generate 25 video ideas:
  - 15 direct sleep titles
  - 10 converted titles

### 4. Master Pipeline (`run.py`)
- Execute all steps in sequence
- Handle errors gracefully
- Output to CSV and Markdown

## Output Files

### `output/outliers.csv`
Columns:
- channel
- video_id
- title
- published_at
- views
- duration
- age_days
- views_per_day
- baseline_views
- outlier_score
- baseline_vpd
- outlier_score_vpd
- recency_boosted_score
- is_sleep_style
- bucket (direct_sleep / convertible)
- url
- thumbnail_url

### `output/summary.md`
Contains:
- Top 5 outliers per competitor
- Title pattern library (10-15 formulas)
- Thumbnail pattern library (6-10 visual rules)
- 25 Cozy Gamer video ideas table:
  - Title
  - Thumbnail text (3-5 words)
  - Hook explanation
  - Source outlier(s)

## Execution

### One-Command Pipeline
```bash
python execution/run.py
```

### Environment Setup
```bash
export TUBELAB_API_KEY='your-api-key'
pip install requests
```

### Individual Steps
```bash
# Step 1: Fetch data
python execution/fetch_competitors.py

# Step 2: Compute outliers
python execution/compute_outliers.py

# Step 3: Generate summary
python execution/summarize_patterns.py
```

## Data Source

**TubeLab API ONLY**
- API key via TUBELAB_API_KEY environment variable
- Rate limiting: 10 requests per minute (handled automatically)
- No fallback to other APIs

## Quality Checks

Before finalizing output:
1. ✓ All outliers are Pokémon content
2. ✓ Per-channel baselines calculated correctly
3. ✓ Sleep classification applied
4. ✓ 25 video ideas generated (15 + 10 split)
5. ✓ No hallucinated metrics
6. ✓ CSV validates in Excel/Sheets

## Pokémon Content Validation

Videos must contain Pokémon-specific keywords in title or description:
- pokémon, pokemon
- pikachu, charizard, mewtwo (specific Pokémon)
- kanto, johto, hoenn, sinnoh, unova, kalos, alola, galar, paldea (regions)
- gen 1, gen 2, generation
- pokédex, pokedex
- legendary, mythical
- scarlet, violet, sword, shield (game titles)

**Reject if title contains:**
- animal crossing
- mario
- zelda
- stardew
- minecraft
- (other non-Pokémon games)

## Success Criteria

System successfully:
1. Identifies 20+ Pokémon outliers across competitors
2. Classifies them as Direct Sleep vs Convertible
3. Extracts clear title patterns
4. Generates 25 actionable video ideas
5. Provides source outliers for each idea
6. Outputs clean CSV and readable Markdown
