#!/usr/bin/env python3
"""
Master Pipeline - Pokémon Outlier Detector
Runs the complete outlier detection and analysis pipeline.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def print_header(title: str):
    """Print section header."""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def run_step(script_name: str, description: str) -> bool:
    """
    Run a pipeline step.

    Args:
        script_name: Name of Python script to run
        description: Description of the step

    Returns:
        True if successful, False otherwise
    """
    print_header(f"STEP: {description}")

    script_path = Path(__file__).parent / script_name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False
        )
        print(f"\n✓ {description} - COMPLETE")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} - FAILED")
        print(f"Error code: {e.returncode}")
        return False

    except Exception as e:
        print(f"\n✗ {description} - ERROR")
        print(f"Error: {e}")
        return False


def check_environment() -> bool:
    """Check if environment is properly configured."""
    print_header("ENVIRONMENT CHECK")

    # Check API key
    api_key = os.environ.get('TUBELAB_API_KEY')
    if not api_key:
        print("✗ TUBELAB_API_KEY environment variable not set")
        print("\nPlease set your API key:")
        print("  export TUBELAB_API_KEY='your-api-key-here'")
        return False

    print("✓ TUBELAB_API_KEY is set")

    # Check input files exist
    required_files = [
        'input/competitors.txt',
        'input/pokemon_keywords.txt'
    ]

    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"✗ Required file missing: {file_path}")
            return False
        print(f"✓ {file_path} found")

    # Check/create output directory
    os.makedirs('output', exist_ok=True)
    print("✓ Output directory ready")

    return True


def upload_to_google_sheets():
    """Upload outliers to Google Sheets."""
    print_header("UPLOADING TO GOOGLE SHEETS")

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import csv

        # Check if credentials file exists
        if not os.path.exists('credentials.json'):
            print("⚠ credentials.json not found - skipping Google Sheets upload")
            return False

        print("✓ Found credentials.json")

        # Load outliers from CSV
        if not os.path.exists('output/outliers.csv'):
            print("⚠ outliers.csv not found - skipping upload")
            return False

        with open('output/outliers.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            outliers = list(reader)

        if len(outliers) == 0:
            print("⚠ No outliers to upload")
            return False

        print(f"✓ Loaded {len(outliers)} outliers from CSV")

        # Setup credentials
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
        client = gspread.authorize(creds)

        print("✓ Authenticated with Google")

        # Open or create the sheet
        try:
            spreadsheet = client.open('YT outlier')
            sheet = spreadsheet.sheet1
            print("✓ Opened existing 'YT outlier' sheet")
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create('YT outlier')
            sheet = spreadsheet.sheet1
            print("✓ Created new 'YT outlier' sheet")

        # Clear existing data
        sheet.clear()
        print("✓ Cleared existing data")

        # Prepare headers
        headers = [
            'Channel', 'Video Title', 'Thumbnail', 'URL', 'Publish Date',
            'Days Since', 'Views', 'Views/Day', 'Baseline VPD',
            'Outlier Score', 'Recency Boost', 'Final Score',
            'Type', 'Bucket'
        ]

        # Prepare data rows
        rows = [headers]

        for outlier in outliers:
            # Use =IMAGE() formula for thumbnail
            thumbnail_formula = f'=IMAGE("{outlier.get("thumbnail_url", "")}")' if outlier.get('thumbnail_url') else ''

            row = [
                outlier.get('channel', ''),
                outlier.get('title', ''),
                thumbnail_formula,  # Thumbnail with IMAGE formula
                outlier.get('url', ''),
                outlier.get('published_at', ''),
                outlier.get('age_days', ''),
                outlier.get('views', ''),
                outlier.get('views_per_day', ''),
                outlier.get('baseline_vpd', ''),
                outlier.get('outlier_score', ''),
                outlier.get('recency_boost', ''),
                outlier.get('recency_boosted_score', ''),
                'Sleep' if outlier.get('is_sleep_style', '').lower() == 'true' else 'Normal',
                outlier.get('bucket', '')
            ]
            rows.append(row)

        # Upload all data at once
        sheet.update('A1', rows)
        print(f"✓ Uploaded {len(outliers)} outliers to Google Sheets")

        # Format the sheet
        sheet.format('A1:N1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })

        # Set column widths
        sheet.set_column_width('B', 400)  # Video Title
        sheet.set_column_width('C', 150)  # Thumbnail

        print(f"✓ Sheet URL: {spreadsheet.url}")

        return True

    except ImportError:
        print("⚠ gspread not installed - skipping Google Sheets upload")
        return False
    except Exception as e:
        print(f"✗ Error uploading to Google Sheets: {e}")
        return False


def print_results():
    """Print final results summary."""
    print_header("PIPELINE COMPLETE")

    # Check output files
    output_files = {
        'output/raw_videos.json': 'Raw video data',
        'output/outliers.csv': 'Outlier spreadsheet',
        'output/summary.md': 'Analysis summary'
    }

    print("Output files:")
    for file_path, description in output_files.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} ({size:,} bytes) - {description}")
        else:
            print(f"  ✗ {file_path} - MISSING")

    # Try to show quick stats
    try:
        import csv

        with open('output/outliers.csv', 'r') as f:
            reader = csv.DictReader(f)
            outliers = list(reader)

        sleep_count = sum(1 for v in outliers if v.get('is_sleep_style', '').lower() == 'true')
        convertible_count = len(outliers) - sleep_count

        print(f"\nResults:")
        print(f"  Total outliers: {len(outliers)}")
        print(f"  Direct sleep: {sleep_count}")
        print(f"  Convertible: {convertible_count}")

        print(f"\nTop 3 outliers:")
        for i, outlier in enumerate(outliers[:3], 1):
            print(f"  {i}. {outlier['title'][:60]}...")
            print(f"     Channel: {outlier['channel']}")
            print(f"     Score: {outlier.get('recency_boosted_score', 'N/A')}")

    except Exception as e:
        print(f"\n⚠ Could not read outliers.csv: {e}")

    print(f"\n📊 Next step: Review output/summary.md for video ideas")


def main():
    """Run the complete pipeline."""
    start_time = datetime.now()

    print("="*60)
    print("POKÉMON OUTLIER DETECTOR - MASTER PIPELINE")
    print("="*60)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 0: Environment check
    if not check_environment():
        print("\n✗ Environment check failed. Aborting.")
        sys.exit(1)

    # Step 1: Fetch competitor data
    if not run_step('fetch_competitors.py', 'Fetch Competitor Data'):
        print("\n✗ Pipeline failed at Step 1")
        sys.exit(1)

    # Step 2: Compute outliers
    if not run_step('compute_outliers.py', 'Compute Outlier Scores'):
        print("\n✗ Pipeline failed at Step 2")
        sys.exit(1)

    # Step 3: Generate summary
    if not run_step('summarize_patterns.py', 'Generate Patterns & Ideas'):
        print("\n✗ Pipeline failed at Step 3")
        sys.exit(1)

    # Step 4: Upload to Google Sheets
    upload_to_google_sheets()

    # Print results
    print_results()

    # Calculate duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'='*60}")
    print(f"✓ PIPELINE COMPLETE")
    print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
