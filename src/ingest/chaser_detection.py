#!/usr/bin/env python3
"""
Chaser Detection - Problem Gambling Indicator (Consecutive losses + debit spike)
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from currency_converter import convert_to_php

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
    print("CHASER DETECTION (Problem Gambling)")
    print("=" * 60)
    print(f"Target: {FOLDER}")
    print(f"Output: {REPORT_DIR}")

    update_progress('chaser_detection', 'Starting chaser detection...', 0)

    if not FOLDER.exists():
        print(f"ERROR: Folder not found: {FOLDER}")
        update_progress('error', 'Folder not found', 0)
        return 1

    csv_files = get_all_csv_files()
    print(f"Found {len(csv_files)} CSV files")
    update_progress('chaser_detection', f'Found {len(csv_files)} CSV files', 5, {'total_files': len(csv_files)})

    if len(csv_files) == 0:
        print("ERROR: No CSV files found!")
        update_progress('error', 'No CSV files found', 0)
        return 1

    player_sequences = defaultdict(list)

    for file_idx, file_path in enumerate(csv_files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    player_id = row.get('player_id', '').strip()
                    if not player_id:
                        continue

                    timestamp_str = row.get('formatted_debit_at', '').strip()
                    currency = row.get('currency', '').strip()
                    winlose = safe_float(row.get('winlose_amount', 0))
                    debit = safe_float(row.get('debit_amount', 0))

                    winlose_php = convert_to_php(winlose, currency, timestamp_str)
                    debit_php = convert_to_php(debit, currency, timestamp_str)

                    if timestamp_str:
                        try:
                            ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            player_sequences[player_id].append((ts, winlose_php, debit_php))
                        except ValueError:
                            pass

        except Exception as e:
            print(f"    Error: {e}")
            continue

        pct = 10 + int((file_idx / len(csv_files)) * 40)
        update_progress('chaser_detection', f'Processing file {file_idx}/{len(csv_files)}...', pct,
                        {'total_files': len(csv_files), 'processed': file_idx})

    update_progress('chaser_detection', 'Analyzing player sequences...', 55,
                    {'total_players': len(player_sequences)})

    chasers = []
    chase_threshold_losses = 3
    chase_spike_multiplier = 3

    for player_id, sequence in player_sequences.items():
        if len(sequence) < 5:
            continue

        sequence.sort(key=lambda x: x[0])

        consecutive_losses = 0
        loss_start_idx = 0
        chase_events = []

        for idx, (ts, winlose, debit) in enumerate(sequence):
            if winlose < 0:
                if consecutive_losses == 0:
                    loss_start_idx = idx
                consecutive_losses += 1
            else:
                if consecutive_losses >= chase_threshold_losses:
                    loss_bets = sequence[loss_start_idx:idx]
                    avg_loss_debit = sum(b[2] for b in loss_bets) / len(loss_bets) if loss_bets else 0

                    post_loss_bets = sequence[idx:idx+3]
                    if post_loss_bets:
                        spike_debits = [b[2] for b in post_loss_bets]
                        max_spike = max(spike_debits)

                        if avg_loss_debit > 0 and max_spike > avg_loss_debit * chase_spike_multiplier:
                            chase_events.append({
                                'loss_streak': consecutive_losses,
                                'avg_loss_debit': avg_loss_debit,
                                'spike_debit': max_spike,
                                'spike_multiplier': max_spike / avg_loss_debit
                            })

                consecutive_losses = 0

        if chase_events:
            worst_chase = max(chase_events, key=lambda x: x['spike_multiplier'])

            chasers.append({
                'player_id': player_id,
                'total_bets': len(sequence),
                'chase_events': len(chase_events),
                'max_consecutive_losses': worst_chase['loss_streak'],
                'avg_loss_debit': round(worst_chase['avg_loss_debit'], 2),
                'spike_debit': round(worst_chase['spike_debit'], 2),
                'spike_multiplier': round(worst_chase['spike_multiplier'], 2),
                'total_debit': round(sum(b[2] for b in sequence), 2),
                'total_winlose': round(sum(b[1] for b in sequence), 2)
            })

    chasers.sort(key=lambda x: x['spike_multiplier'], reverse=True)

    if chasers:
        output_file = REPORT_DIR / "chaser_detection.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['player_id', 'total_bets', 'chase_events',
                                                   'max_consecutive_losses', 'avg_loss_debit',
                                                   'spike_debit', 'spike_multiplier',
                                                   'total_debit', 'total_winlose'])
            writer.writeheader()
            writer.writerows(chasers)

    update_progress('chaser_detection', 'Chaser detection complete!', 100,
                    {'total_players': len(player_sequences), 'chasers': len(chasers)})

    print(f"\n[OK] Chaser detection: {REPORT_DIR / 'chaser_detection.csv'}")
    print(f"     Flagged {len(chasers)} chasers")
    return 0


if __name__ == "__main__":
    sys.exit(main())