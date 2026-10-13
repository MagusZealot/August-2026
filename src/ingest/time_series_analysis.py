#!/usr/bin/env python3
"""
Time-Series Analysis by Country - Peak traffic hours
"""
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
if not (WORKSPACE / "workspace_map.txt").exists():
    for _parent in WORKSPACE.parents:
        if (_parent / "workspace_map.txt").exists():
            WORKSPACE = _parent
            break


import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from currency_converter import CURRENCY_COUNTRY

FOLDER = Path(WORKSPACE / "data" / "raw")
REPORT_DIR = Path(WORKSPACE / "output")
REPORT_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = REPORT_DIR / "progress.json"


def update_progress(stage, message, progress=None, details=None):
    data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stage': stage,
        'message': message,
        'progress': progress,
        'details': details or {}
    }
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_csv_files():
    return sorted(FOLDER.glob("*.csv"))


def main():
    print("=" * 60)
    print("TIME-SERIES ANALYSIS BY COUNTRY")
    print("=" * 60)
    print(f"Target: {FOLDER}")
    print(f"Output: {REPORT_DIR}")

    update_progress('time_series', 'Starting time-series analysis...', 0)

    if not FOLDER.exists():
        print(f"ERROR: Folder not found: {FOLDER}")
        update_progress('error', 'Folder not found', 0)
        return 1

    csv_files = get_all_csv_files()
    print(f"Found {len(csv_files)} CSV files")
    update_progress('time_series', f'Found {len(csv_files)} CSV files', 5, {'total_files': len(csv_files)})

    if len(csv_files) == 0:
        print("ERROR: No CSV files found!")
        update_progress('error', 'No CSV files found', 0)
        return 1

    hourly_data = defaultdict(int)
    country_hourly = defaultdict(lambda: defaultdict(int))

    for file_idx, file_path in enumerate(csv_files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    timestamp_str = row.get('formatted_debit_at', '').strip()
                    currency = row.get('currency', '').strip()

                    if not timestamp_str:
                        continue

                    try:
                        ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        hour = ts.hour
                        hourly_data[hour] += 1

                        country = CURRENCY_COUNTRY.get(currency, 'Unknown')
                        country_hourly[country][hour] += 1
                    except ValueError:
                        pass

        except Exception as e:
            print(f"    Error: {e}")
            continue

        pct = 10 + int((file_idx / len(csv_files)) * 40)
        update_progress('time_series', f'Processing file {file_idx}/{len(csv_files)}...', pct,
                        {'total_files': len(csv_files), 'processed': file_idx})

    country_summary = []
    for country in sorted(country_hourly.keys()):
        hours = country_hourly[country]
        total_country_bets = sum(hours.values())
        peak_hour, peak_count = max(hours.items(), key=lambda x: x[1])

        country_summary.append({
            'Country': country,
            'Total_Bets': total_country_bets,
            'Peak_Hour': f"{peak_hour:02d}:00",
            'Peak_Bets': peak_count,
            'Peak_Percentage': round((peak_count / total_country_bets) * 100, 2)
        })

    output_file = REPORT_DIR / "time_series_analysis.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Country', 'Total_Bets', 'Peak_Hour',
                                               'Peak_Bets', 'Peak_Percentage'])
        writer.writeheader()
        writer.writerows(country_summary)

    hourly_output = REPORT_DIR / "hourly_traffic.csv"
    with open(hourly_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Hour', 'Total_Bets'])
        for hour, count in sorted(hourly_data.items()):
            writer.writerow([f"{hour:02d}:00", count])

    update_progress('time_series', 'Time-series analysis complete!', 100,
                    {'countries': len(country_summary), 'total_bets': sum(hourly_data.values())})

    print(f"\n[OK] Time-series analysis: {REPORT_DIR / 'time_series_analysis.csv'}")
    print(f"[OK] Hourly traffic: {REPORT_DIR / 'hourly_traffic.csv'}")
    print(f"     Countries analyzed: {len(country_summary)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())