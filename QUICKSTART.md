# QUICK START - Run the Pokémon Outlier Detector

## You're all set! Everything is ready to run.

### Step 1: Install Dependencies
```bash
pip install requests
```

### Step 2: Set Your API Key
```bash
export TUBELAB_API_KEY='c9c18b94-8c29-482e-a639-dabfd86bd06c'
```

### Step 3: Run the Pipeline
```bash
python execution/run.py
```

## What Happens:
- ✓ Fetches videos from 7 Pokémon sleep competitors
- ✓ Filters for Pokémon-only content
- ✓ Calculates per-channel outlier scores
- ✓ Generates 25 video ideas

## Output Files:
- `output/outliers.csv` - All outliers with scores
- `output/summary.md` - 25 video ideas + patterns

## Time: ~5-10 minutes

---

## ONE-LINE RUN:
```bash
TUBELAB_API_KEY='c9c18b94-8c29-482e-a639-dabfd86bd06c' python execution/run.py
```
