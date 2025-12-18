# YouTube Outlier Detector 🎯

A **FREE** YouTube analytics tool that identifies videos significantly outperforming a channel's typical performance. No API keys required!

## Features

- ✅ **100% Free** - Uses `yt-dlp` instead of paid YouTube APIs
- 📊 **Smart Scoring** - Combines outlier detection with recency boost
- 📈 **CSV Export** - Results saved to spreadsheet-friendly format
- 📑 **Google Sheets** - Optional integration for cloud storage
- ⚡ **Fast** - Analyzes multiple channels efficiently
- 🎨 **Customizable** - Configurable thresholds and parameters

## What is an Outlier?

An outlier video is one that performs **significantly better** than a channel's baseline. This tool:

1. Calculates each video's `views_per_day` metric
2. Establishes a baseline from the channel's recent videos
3. Identifies videos with 3x+ performance vs. baseline
4. Applies recency boost to favor newer viral content

Perfect for finding:
- 🔥 Viral videos
- 🚀 Trending content
- 💡 High-performing topics
- 📺 Format changes that worked

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install yt-dlp directly
pip install yt-dlp
```

**Note:** yt-dlp requires Python 3.7+

### 2. Add Channels

Edit `channels.txt` and add YouTube channels (one per line):

```
@mkbhd
@veritasium
https://www.youtube.com/@fireship
```

### 3. Run Analysis

```bash
python outlier_detector.py
```

That's it! Results will be saved to `outliers.csv`.

## Usage Examples

### Basic Usage

```bash
# Use default settings
python outlier_detector.py
```

### Custom Parameters

```bash
# Analyze last 60 days with 300 videos per channel
python outlier_detector.py --days-window 60 --videos-per-channel 300

# Lower threshold for smaller channels
python outlier_detector.py --min-views 1000

# Custom output file
python outlier_detector.py --output my_results.csv
```

### Google Sheets Integration

```bash
# Export to Google Sheets (requires setup - see below)
python outlier_detector.py --sheet YOUR_SHEET_ID
```

## Command Line Options

| Flag | Default | Description |
|------|---------|-------------|
| `--videos-per-channel` | 200 | Number of recent videos to fetch |
| `--baseline-videos` | 60 | Videos used for baseline calculation |
| `--days-window` | 30 | Only consider videos from last N days |
| `--min-views` | 5000 | Minimum view threshold |
| `--output` | outliers.csv | Output CSV filename |
| `--sheet` | None | Google Sheet ID (optional) |
| `--channels` | channels.txt | Input file with channel URLs |

## Scoring Algorithm

The tool uses a sophisticated scoring system:

### 1. Views Per Day
```
views_per_day = total_views / max(days_since_upload, 1)
```

### 2. Baseline Calculation
```
baseline = median(views_per_day of last 60 videos)
```

### 3. Outlier Score
```
outlier_score = views_per_day / baseline
```

### 4. Recency Boost
```
recency_boost = 1 + 0.5 * exp(-days_since_upload / 14)
```
- Recent videos (0-7 days): ~1.35-1.5x boost
- Moderate age (14 days): ~1.18x boost
- Older videos (30+ days): ~1.05x boost

### 5. Final Score
```
final_score = outlier_score * recency_boost
```

### 6. Outlier Criteria
A video is marked as an outlier if:
- `final_score >= 3.0`
- Within `days_window` (default: 30 days)
- `views >= min_views` (default: 5000)

## Output Format

### CSV Columns

| Column | Description |
|--------|-------------|
| `channel` | Channel URL or handle |
| `video_title` | Video title |
| `video_url` | Direct link to video |
| `publish_date` | Upload date (YYYY-MM-DD) |
| `days_since` | Days since upload |
| `views` | Total view count |
| `views_per_day` | Average daily views |
| `baseline_vpd` | Channel's baseline views/day |
| `outlier_score` | Performance vs baseline |
| `recency_boost` | Time-based multiplier |
| `final_score` | Overall outlier score |

### Example Output

```csv
channel,video_title,video_url,publish_date,days_since,views,views_per_day,baseline_vpd,outlier_score,recency_boost,final_score
@fireship,I built a game in 60 seconds,https://youtube.com/watch?v=abc123,2024-01-15,3.2,850000,265625,45000,5.90,1.43,8.44
```

## Google Sheets Setup (Optional)

To export results to Google Sheets:

### 1. Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Google Sheets API** and **Google Drive API**
4. Go to **IAM & Admin** → **Service Accounts**
5. Create service account
6. Create and download JSON key

### 2. Install Dependencies

```bash
pip install gspread google-auth
```

Or uncomment in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Configure Access

1. Save the JSON key as `service_account.json` in project directory
2. Create a new Google Sheet
3. Share the sheet with the service account email (found in JSON)
4. Copy the Sheet ID from URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

### 4. Run with Sheets Output

```bash
python outlier_detector.py --sheet YOUR_SHEET_ID
```

## Troubleshooting

### yt-dlp not found

```bash
pip install yt-dlp
# or
brew install yt-dlp  # macOS
```

### "No videos found for channel"

- Check channel URL format (use @handle or full URL)
- Channel may be private or have no public videos
- Try using full URL: `https://www.youtube.com/@channelname`

### "Timeout fetching channel"

- Channel has many videos (increase timeout in code)
- Network issues
- Try reducing `--videos-per-channel`

### Google Sheets errors

- Ensure `service_account.json` exists
- Check service account has access to sheet
- Install: `pip install gspread google-auth`

## How It Works

1. **Fetch Videos**: Uses `yt-dlp` to extract video metadata from channels
2. **Calculate Metrics**: Computes views-per-day for each video
3. **Establish Baseline**: Takes median of recent videos
4. **Score Videos**: Applies outlier formula with recency boost
5. **Filter Results**: Keeps only significant outliers
6. **Export Data**: Saves to CSV and/or Google Sheets

## Use Cases

### Content Creators
- Find what content resonated with your audience
- Identify successful video formats
- Discover trending topics in your niche

### Researchers
- Analyze viral content patterns
- Study channel growth strategies
- Track topic performance over time

### Marketers
- Monitor competitor performance
- Identify collaboration opportunities
- Track influencer viral content

## Performance Tips

### For Large Channels

```bash
# Reduce videos fetched to speed up analysis
python outlier_detector.py --videos-per-channel 100
```

### For Smaller Channels

```bash
# Lower minimum views threshold
python outlier_detector.py --min-views 500 --baseline-videos 30
```

### For Specific Time Periods

```bash
# Look at last 7 days only
python outlier_detector.py --days-window 7

# Or last 90 days
python outlier_detector.py --days-window 90
```

## Limitations

- **Rate Limits**: yt-dlp may be rate-limited by YouTube for excessive requests
- **Private Videos**: Cannot access private or members-only content
- **Deleted Videos**: Historical deleted videos not accessible
- **Live Accuracy**: View counts may be slightly delayed vs real-time
- **Channel Size**: Very large channels (1000+ videos) may take longer to analyze

## Technical Details

### Why yt-dlp?

`yt-dlp` is a community-maintained fork of youtube-dl with:
- ✅ No API keys required
- ✅ No quota limits
- ✅ No cost
- ✅ Actively maintained
- ✅ Extracts comprehensive metadata

### Why This Scoring Algorithm?

The scoring system balances multiple factors:

1. **Median vs Mean**: Robust to outliers in baseline calculation
2. **Recency Boost**: Exponential decay favors recent viral content
3. **Views Per Day**: Normalizes for video age (fair comparison)
4. **Threshold (3.0)**: Identifies significant outliers (3x baseline)

## Contributing

Found a bug or have a feature idea? Contributions welcome!

## License

MIT License - Use freely for personal or commercial projects.

## Acknowledgments

- Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Google Sheets integration via [gspread](https://github.com/burnash/gspread)

---

**Happy outlier hunting! 🎯**
