from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
if not (WORKSPACE / "workspace_map.txt").exists():
    for _parent in WORKSPACE.parents:
        if (_parent / "workspace_map.txt").exists():
            WORKSPACE = _parent
            break

import os
import csv
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add src/ingest to path for currency_converter import
sys.path.insert(0, str(Path(__file__).parent))
from currency_converter import get_country

FOLDER = Path(WORKSPACE / "data" / "raw")
REPORT_DIR = Path(WORKSPACE / "output")

def extract_heatmap():
    country_hourly = defaultdict(lambda: defaultdict(int))
    csv_files = sorted(FOLDER.glob("*.csv"))
    print(f"Processing {len(csv_files)} files for country hourly heatmap...")
    
    for idx, fpath in enumerate(csv_files, 1):
        t_start = datetime.now()
        with open(fpath, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader)
            curr_idx = header.index("currency")
            time_idx = header.index("formatted_debit_at")
            
            for row in reader:
                if len(row) <= max(curr_idx, time_idx):
                    continue
                curr = row[curr_idx].strip()
                t_str = row[time_idx].strip()
                if not t_str:
                    continue
                # t_str is format "YYYY-MM-DD HH:MM:SS"
                try:
                    hour = int(t_str[11:13])
                    country = get_country(curr)
                    country_hourly[country][hour] += 1
                except (ValueError, IndexError):
                    pass
        print(f"[{idx}/{len(csv_files)}] {fpath.name} processed in {(datetime.now() - t_start).total_seconds():.1f}s")
        
    out_file = REPORT_DIR / "country_hourly_heatmap.csv"
    hours = [f"{h:02d}:00" for h in range(24)]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Country"] + hours + ["Total"])
        for country in sorted(country_hourly.keys()):
            row = [country]
            c_total = 0
            for h in range(24):
                val = country_hourly[country][h]
                row.append(val)
                c_total += val
            row.append(c_total)
            writer.writerow(row)
            
    print(f"Successfully generated {out_file}")

if __name__ == "__main__":
    extract_heatmap()

