# TubeLab Outlier Detector - Sleep Gaming Niche 🎯😴

Advanced competitor analysis tool using TubeLab API, optimized for sleep/ASMR gaming channels.

## 🎯 What This Does

Analyzes your **specific competitor list** to find what's working in the sleep gaming niche:

### Competitors Analyzed:
1. **Fallasleepmon**
2. **Boring Gamer**
3. **Stellar Sleep**
4. **BlueBoyPhin**
5. **Sleepy Gamer**
6. **PokeSleep**
7. **PokeRest**
8. **Cozy Gamer**

## 🧠 Sleep-Niche Specific Intelligence

### Why This Is Different

Sleep/ASMR gaming content is **evergreen** - old videos continue getting views forever. Standard outlier detection fails because:
- ❌ Old videos accumulate views over time (false positives)
- ❌ Recent viral content gets buried by high-performing evergreen videos
- ❌ Can't distinguish between "slow burn" and "true breakout"

### Our Solution: Recency-Focused Scoring

```
Videos 0-3 months old:   STRONG BOOST (2-3x multiplier)
Videos 3-6 months old:   MODERATE BOOST (1.5-2x multiplier)
Videos 6-12 months old:  SLIGHT BOOST (1.0-1.3x multiplier)
Videos >1 year old:      PENALTY (0.5x and decreasing)
```

This finds **truly viral recent content** while filtering out evergreen performers.

## 🚀 Quick Start

### 1. Get TubeLab API Key

1. Sign up at [TubeLab.net](https://tubelab.net/pricing) ($29/month)
2. Go to your dashboard and generate an API key
3. Set it as an environment variable:

```bash
export TUBELAB_API_KEY='your-api-key-here'
```

Or create a `.env` file:
```
TUBELAB_API_KEY=your-api-key-here
```

### 2. Install Dependencies

```bash
pip install requests
# Optional for Google Sheets:
# pip install gspread google-auth
```

### 3. Run Competitor Analysis

```bash
python tubelab_outlier_detector.py
```

That's it! Results saved to `competitor_outliers.csv`

## 📊 What You Get

### CSV Output Columns:

| Column | Description |
|--------|-------------|
| **channel_name** | Competitor channel name |
| **channel_revenue_monthly** | Est. monthly revenue from TubeLab |
| **video_title** | Video title |
| **video_url** | Direct link |
| **publish_date** | Upload date |
| **days_since** | Days since upload |
| **views** | Total views |
| **views_per_day** | Normalized performance |
| **baseline_vpd** | Channel's average |
| **outlier_score** | Performance multiplier (2.0 = 2x baseline) |
| **recency_boost** | Time-based boost applied |
| **final_score** | Overall outlier score |
| **game_mentioned** | Detected game (Pokemon, Stardew, etc.) |
| **sound_types** | Audio elements (rain, ASMR, etc.) |
| **packaging_elements** | Format (10 hours, black screen, etc.) |
| **description** | First 200 chars of description |

### Example Output:

```csv
channel_name,channel_revenue_monthly,video_title,outlier_score,game_mentioned,sound_types,packaging_elements
PokeSleep,5000,Pokemon Sleep Rain Sounds 10 Hours,4.2,Pokemon,"rain, nature","long_duration, no_ads, cozy"
```

## 🎮 Content Analysis Features

### Automatic Detection of:

**🎯 Games Mentioned:**
- Pokemon/Pokémon
- Stardew Valley
- Animal Crossing
- Minecraft
- Zelda
- Mario
- And more...

**🔊 Sound Types:**
- Rain/rainfall
- White noise
- Nature sounds (forest, ocean, river)
- Thunder/storms
- Fire/crackling
- Music/soundtracks
- ASMR elements

**📦 Packaging Elements:**
- Long duration (10 hours, 8 hours, etc.)
- No ads/ad-free
- Black screen
- Gameplay/walkthrough
- Cozy/relaxing vibes
- Study/focus positioning

## ⚙️ Configuration Options

### Basic Usage

```bash
# Default settings (6 months lookback, 2x baseline minimum)
python tubelab_outlier_detector.py
```

### Custom Settings

```bash
# Look back 3 months, require 3x performance
python tubelab_outlier_detector.py --lookback-months 3 --min-outlier-score 3.0

# Lower threshold for smaller channels
python tubelab_outlier_detector.py --min-views 1000 --min-outlier-score 1.5

# Custom output file
python tubelab_outlier_detector.py --output december_analysis.csv
```

### All Options

```bash
python tubelab_outlier_detector.py \
  --api-key YOUR_KEY \              # TubeLab API key
  --lookback-months 6 \              # Focus on last 6 months
  --min-views 5000 \                 # Minimum view threshold
  --min-outlier-score 2.0 \          # 2x baseline minimum
  --output competitor_outliers.csv \ # Output file
  --sheet GOOGLE_SHEET_ID            # Optional: export to Sheets
```

## 📈 Google Sheets Integration

### Setup

1. Follow the Google Sheets setup from main README
2. Get your Sheet ID from the URL
3. Run with `--sheet` flag:

```bash
python tubelab_outlier_detector.py --sheet YOUR_SHEET_ID
```

Results will be automatically uploaded and formatted!

## 🧮 Scoring Algorithm Details

### Step 1: Calculate Views Per Day
```python
views_per_day = total_views / days_since_upload
```

### Step 2: Establish Baseline
```python
baseline = median(views_per_day of all channel videos)
```

### Step 3: Calculate Outlier Score
```python
outlier_score = views_per_day / baseline
# 2.0 = 2x better than average
# 3.0 = 3x better than average
```

### Step 4: Apply Sleep-Niche Recency Boost

```python
if days_since <= 90:  # 0-3 months
    recency_boost = 2.0 + exp(-days_since / 30)  # 2.0-3.0x
elif days_since <= 180:  # 3-6 months
    recency_boost = 1.5 + 0.5 * exp(...)         # 1.5-2.0x
elif days_since <= 365:  # 6-12 months
    recency_boost = 1.0 + 0.3 * exp(...)         # 1.0-1.3x
else:  # >1 year - PENALTY
    recency_boost = 0.5 * exp(...)               # 0.5x and decreasing
```

### Step 5: Final Score
```python
final_score = outlier_score * recency_boost
```

### Filtering Criteria
- ✅ `outlier_score >= 2.0` (2x baseline minimum)
- ✅ Within lookback period (default: 6 months)
- ✅ Meets minimum views (default: 5000)

## 📊 Understanding Your Results

### High Final Score (>6.0)
- 🔥 **Recent viral hit** - Study this!
- Likely hit the algorithm in the last 3 months
- Check packaging, game choice, sound type

### Medium Final Score (3.0-6.0)
- 🌟 **Strong performer** - Worth analyzing
- Doing 2-3x better than channel average
- May indicate format or topic shift

### Low Final Score (<3.0)
- Filtered out - not an outlier
- Either too old or not significantly outperforming

### Revenue Insights
- Check `channel_revenue_monthly` column
- Identifies which competitors are monetizing well
- Compare outlier frequency vs. revenue

## 💡 How to Use This Data

### 1. Identify Patterns
Look for commonalities in top outliers:
- Same game appearing multiple times?
- Specific sound type dominating?
- Packaging element that's working?

### 2. Competitive Intelligence
- Which competitor has highest revenue?
- What are they doing differently?
- Are they in a different niche (different games)?

### 3. Content Strategy
- Test formats that are working for competitors
- Avoid oversaturated topics (unless you can differentiate)
- Consider sound types you haven't tried

### 4. Timing Insights
- Are outliers recent (algorithm change)?
- Seasonal patterns (certain games)?
- New game releases driving views?

## 🔧 Troubleshooting

### "API key required"
```bash
export TUBELAB_API_KEY='your-key-here'
# or
python tubelab_outlier_detector.py --api-key 'your-key-here'
```

### "Channel not found"
- TubeLab may not have indexed the channel yet
- Try alternate channel name spelling
- Check if channel exists on TubeLab's database

### "No outliers found"
- Try lowering `--min-outlier-score 1.5`
- Increase `--lookback-months 12`
- Lower `--min-views 1000`

### Rate limit errors
- Script automatically handles rate limiting (10 req/min)
- If you see delays, this is normal
- TubeLab enforces 10 requests per minute

### Missing transcript data
- Not all videos have transcripts
- Sleep videos often have no speech (silent/music only)
- Falls back to description analysis

## 📋 Rate Limits

TubeLab API limits:
- **10 requests per minute** (handled automatically)
- Analyzing 8 competitors ≈ 5-10 minutes
- Each channel requires 2-3 API calls

Script includes automatic rate limiting with progress indicators.

## 💰 Costs

### TubeLab Subscription
- **$29/month** for API access
- Includes 400K+ channels database
- 4M+ outliers pre-analyzed
- Credits-based system (monitor usage)

### vs. Free yt-dlp Version
- yt-dlp: Free but no revenue data, no outlier database
- TubeLab: Paid but pre-analyzed outliers + revenue estimates
- **For competitor analysis: TubeLab is worth it**

## 🎯 Competitor List

Currently hardcoded in script:
```python
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
```

To add/remove competitors, edit `tubelab_outlier_detector.py` line 27.

## 📚 Next Steps

1. **Run the analysis** on all 8 competitors
2. **Export to Google Sheets** for team collaboration
3. **Identify top 3 patterns** from outliers
4. **Test one format** from competitor outliers
5. **Track your own performance** using the free yt-dlp version

## 🤝 Support

- TubeLab API docs: https://tubelab.net/docs/api
- TubeLab support: Available 24/7 via their dashboard

---

**Happy competitor hunting! 🎯😴**
