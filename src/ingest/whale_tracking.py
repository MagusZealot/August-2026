#!/usr/bin/env python3
"""
Whale Tracking Analysis - Pareto Principle (Top 20% generating 80% of debit)
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
from currency_converter import convert_to_php, get_country

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


def safe_float(val):
    if not val:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def main():
    print("=" * 60)
    print("WHALE TRACKING ANALYSIS")
    print("=" * 60)
    print(f"Target: {FOLDER}")
    print(f"Output: {REPORT_DIR}")

    update_progress('whale_tracking', 'Starting whale tracking analysis...', 0)

    if not FOLDER.exists():
        print(f"ERROR: Folder not found: {FOLDER}")
        update_progress('error', 'Folder not found', 0)
        return 1

    csv_files = get_all_csv_files()
    print(f"Found {len(csv_files)} CSV files")
    update_progress('whale_tracking', f'Found {len(csv_files)} CSV files', 5, {'total_files': len(csv_files)})

    if len(csv_files) == 0:
        print("ERROR: No CSV files found!")
        update_progress('error', 'No CSV files found', 0)
        return 1

    player_debit = defaultdict(float)
    player_bets = defaultdict(int)
    player_sessions = defaultdict(list)
    player_countries = defaultdict(set)

    for file_idx, file_path in enumerate(csv_files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    player_id = row.get('player_id', '').strip()
                    if not player_id:
                        continue

                    debit = safe_float(row.get('debit_amount', 0))
                    currency = row.get('currency', '').strip()
                    timestamp_str = row.get('formatted_debit_at', '').strip()

                    debit_php = convert_to_php(debit, currency, timestamp_str)
                    country = get_country(currency)

                    player_debit[player_id] += debit_php
                    player_bets[player_id] += 1
                    player_countries[player_id].add(currency)

                    if timestamp_str:
                        try:
                            ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            player_sessions[player_id].append(ts)
                        except ValueError:
                            pass

        except Exception as e:
            print(f"    Error: {e}")
            continue

        pct = 5 + int((file_idx / len(csv_files)) * 40)
        update_progress('whale_tracking', f'Processing file {file_idx}/{len(csv_files)}...', pct,
                        {'total_files': len(csv_files), 'processed': file_idx})

    total_debit = sum(player_debit.values())
    sorted_players = sorted(player_debit.items(), key=lambda x: x[1], reverse=True)

    cumulative_debit = 0
    whale_count_80 = 0
    whale_threshold_80 = 0

    for idx, (player_id, debit) in enumerate(sorted_players, 1):
        cumulative_debit += debit
        cumulative_pct = (cumulative_debit / total_debit) * 100

        if cumulative_pct >= 80 and whale_count_80 == 0:
            whale_threshold_80 = debit
            whale_count_80 = idx

    whales = [(pid, debit) for pid, debit in sorted_players if debit >= whale_threshold_80]

    update_progress('whale_tracking', 'Analyzing whale behavior...', 50,
                    {'total_players': len(player_debit), 'whales': len(whales)})

    whale_sessions = []
    for player_id, debit in whales[:20]:
        sessions = player_sessions.get(player_id, [])
        if sessions:
            sessions_sorted = sorted(sessions)
            session_times = []
            for i in range(0, len(sessions_sorted) - 1, 2):
                if i + 1 < len(sessions_sorted):
                    duration = (sessions_sorted[i+1] - sessions_sorted[i]).total_seconds() / 3600
                    session_times.append(duration)

            avg_session = sum(session_times) / len(session_times) if session_times else 0
            countries = list(player_countries.get(player_id, ['Unknown']))

            whale_sessions.append({
                'player_id': player_id,
                'total_debit': debit,
                'total_bets': player_bets[player_id],
                'avg_session_hours': round(avg_session, 2),
                'session_count': len(sessions),
                'countries': ', '.join(countries)
            })

    if whale_sessions:
        output_file = REPORT_DIR / "whale_analysis.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['player_id', 'total_debit', 'total_bets',
                                                   'avg_session_hours', 'session_count', 'countries'])
            writer.writeheader()
            writer.writerows(whale_sessions)

    update_progress('whale_tracking', 'Whale tracking complete!', 100,
                    {'total_players': len(player_debit), 'whales': len(whales)})

    print(f"\n[OK] Whale analysis: {REPORT_DIR / 'whale_analysis.csv'}")
    print(f"     Found {len(whales)} whales ({whale_count_80} players = 80% of debit)")
    return 0


if __name__ == "__main__":
    sys.exit(main())