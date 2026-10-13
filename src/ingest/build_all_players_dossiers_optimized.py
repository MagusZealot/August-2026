#!/usr/bin/env python3
"""
build_all_players_dossiers_optimized.py

Optimized version with:
- Currency conversion as a separate, cached step (LRU + disk cache in converter)
- Trajectory construction as a separate step
- Concurrent processing of files (multiprocessing)
- Optimizations: detect time-ordered sequences to skip sorting, use typed arrays,
  avoid unnecessary work, process faster with larger buffers
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
import time
import sys
from pathlib import Path
from collections import defaultdict, deque
from array import array
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

# Add src/ingest to path for currency_converter import
sys.path.insert(0, str(Path(__file__).parent))
from currency_converter import convert_to_php, get_country, CURRENCY_COUNTRY

FOLDER = Path(WORKSPACE / "data" / "raw")
REPORT_DIR = Path(WORKSPACE / "output")

CHUNK_SIZE = 1000
MAX_WORKERS = min(os.cpu_count() or 2, 4)  # conservative to avoid heavy API contention

FLAG_MAP = {
    "Indonesia": "ID", "Vietnam": "VN", "China": "CN", "Bangladesh": "BD",
    "Thailand": "TH", "Malaysia": "MY", "India": "IN", "Myanmar": "MM",
    "Philippines": "PH", "Cambodia": "KH", "Laos": "LA", "Singapore": "SG",
    "South Korea": "KR", "Japan": "JP", "USA": "US", "Hong Kong": "HK",
    "Taiwan": "TW", "Nepal": "NP", "Turkey": "TR", "Crypto": "CR", "Unknown": "??",
}
