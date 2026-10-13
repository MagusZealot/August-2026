#!/usr/bin/env python3
"""
Operator Performance Analysis - Profitability by operator
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from currency_converter import convert_to_php, get_country

FOLDER = Path(r"C:\Users\IT-40126\Documents\August 2026-20261008T011759Z-1-001\August 2026\data\raw")
REPORT_DIR = Path(r"C:\Users\IT-40126\Documents\August 2026-20261008T011759Z-1-001\August 2026\output")
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


def safe_float(val):
    if not val:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def main():
    print("=" * 60)
    print("OPERATOR PERFORMANCE ANALYSIS")
    print("=" * 60)
    print(f"Target: {FOLDER}")
    print(f"Output: {REPORT_DIR}")

    update_progress('operator_analysis', 'Starting operator analysis...', 0)

    if not FOLDER.exists():
        print(f"ERROR: Folder not found: {FOLDER}")
        update_progress('error', 'Folder not found', 0)
        return 1

    csv_files = get_all_csv_files()
    print(f"Found {len(csv_files)} CSV files")
    update_progress('operator_analysis', f'Found {len(csv_files)} CSV files', 5, {'total_files': len(csv_files)})

    if len(csv_files) == 0:
        print("ERROR: No CSV files found!")
        update_progress('error', 'No CSV files found', 0)
        return 1

    operator_data = defaultdict(lambda: {
        'total_winlose': 0.0,
        'total_debit': 0.0,
        'total_bets': 0,
        'players': set(),
        'countries': set()
    })

    for file_idx, file_path in enumerate(csv_files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    operator = row.get('operator_name', '').strip()
                    if not operator:
                        operator = 'UNKNOWN'

                    winlose = safe_float(row.get('winlose_amount', 0))
                    debit = safe_float(row.get('debit_amount', 0))
                    player_id = row.get('player_id', '').strip()
                    currency = row.get('currency', '').strip()
                    timestamp_str = row.get('formatted_debit_at', '').strip()

                    winlose_php = convert_to_php(winlose, currency, timestamp_str)
                    debit_php = convert_to_php(debit, currency, timestamp_str)
                    country = get_country(currency)

                    operator_data[operator]['total_winlose'] += winlose_php
                    operator_data[operator]['total_debit'] += debit_php
                    operator_data[operator]['total_bets'] += 1
                    if player_id:
                        operator_data[operator]['players'].add(player_id)
                    operator_data[operator]['countries'].add(country)

        except Exception as e:
            print(f"    Error: {e}")
            continue

        pct = 10 + int((file_idx / len(csv_files)) * 40)
        update_progress('operator_analysis', f'Processing file {file_idx}/{len(csv_files)}...', pct,
                        {'total_files': len(csv_files), 'processed': file_idx})

    operator_summary = []
    for operator, data in operator_data.items():
        total_winlose = data['total_winlose']
        total_debit = data['total_debit']
        total_bets = data['total_bets']

        roi = ((total_debit + total_winlose) / total_debit * 100) if total_debit > 0 else 0
        avg_bet = total_debit / total_bets if total_bets > 0 else 0

        operator_summary.append({
            'Operator': operator,
            'Total_Bets': total_bets,
            'Total_Debit': round(total_debit, 2),
            'Total_Winlose': round(total_winlose, 2),
            'Operator_ROI_%': round(roi, 2),
            'Avg_Bet': round(avg_bet, 2),
            'Unique_Players': len(data['players']),
            'Countries': ', '.join(sorted(data['countries']))
        })

    operator_summary.sort(key=lambda x: x['Total_Debit'], reverse=True)

    output_file = REPORT_DIR / "operator_performance.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Operator', 'Total_Bets', 'Total_Debit',
                                               'Total_Winlose', 'Operator_ROI_%',
                                               'Avg_Bet', 'Unique_Players', 'Countries'])
        writer.writeheader()
        writer.writerows(operator_summary)

    update_progress('operator_analysis', 'Operator analysis complete!', 100,
                    {'total_operators': len(operator_summary)})

    print(f"\n[OK] Operator performance: {REPORT_DIR / 'operator_performance.csv'}")
    print(f"     Operators analyzed: {len(operator_summary)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())