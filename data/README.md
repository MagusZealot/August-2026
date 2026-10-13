# Data Directory

This directory contains raw data files that are **NOT committed to Git** due to size.

## File Discovery Behavior

Scripts discover files via **glob patterns** — not a fixed count of 27:

| Script(s) | Pattern | Scope |
|-----------|---------|-------|
| Steps 1-5, 6, 13 | `*.csv` / `*EXPORT_CSV*.csv` / `mnt_game_probability_he_YYYYMMDD.csv` | **All matching files** |
| Steps 7-8 | Random 5 `*EXPORT_CSV*.csv` (sampled via `random.sample()`) | **5 randomly sampled** (performance + representativeness) |

**Adding more files:** Drop new CSVs into `raw/` or `probability/` — steps 1-6 and 13 auto-process them on next pipeline run. Steps 7-8 stay limited to 5 exports (Step 7 uses random sampling).

---

## Required Files

### `raw/` — Transaction Export CSVs (~9.5 GB total)
Place raw CSV export files here. Each file is ~300-377 MB.

**Naming pattern:** `YYYY-MM-DD-HH-MM-SS_EXPORT_CSV_XXXXX_XXX_0.csv`

**Example files:**
- `2026-10-06-13-38-11_EXPORT_CSV_45625_808_0.csv`
- `2026-10-06-14-02-59_EXPORT_CSV_45627_085_0.csv`
- ... (25 more files spanning 2026-10-06 through 2026-10-07)
- `2026-10-07-17-46-44_EXPORT_CSV_45680_721_0.csv`

**Columns expected:** `player_id`, `operator_name`, `game_name`, `currency`, `debit_amount`, `credit_amount`, `winlose`, `formatted_debit_at`, `device_type`, `bet_id`

### `probability/` — Game Probability / House Edge Snapshots
Daily published CSV snapshots from the probability feed.

**Naming pattern:** `mnt_game_probability_he_YYYYMMDD.csv`

**Date range:** 2025-01-31 through present (cached through 2026-10-11)

**Also includes:** `_manifest.json` — records scan range and unavailable dates (e.g., missing interval 2026-01-13 through 2026-01-29)

Each snapshot is under 100 KB.

### Dealer and table pace snapshots
The combined dealer/table pace ingest automatically fetches daily dealer and
table snapshots and caches them in `round_dealer_time/` and
`round_table_time/`, respectively. The unified pipeline combines these feeds
into `output/round_dealer_table_time_data.json` and generates
`output/dashboards/round_dealer_table_time_dashboard.html`. Dealer and table
records are distinct source observations; the feed does not provide dealer-to-
table pairings. The standalone dealer and table dashboards have been retired.

---

## Data Flow Overview

```mermaid
flowchart TD
    RAW[("raw/<br/>27 CSV exports · ~9.5 GB<br/>300-377 MB each")]
    PROB[("probability/<br/>daily HE snapshots<br/>2025-01-31 → present")]
    PACE[("round_dealer_time/ + round_table_time/<br/>cached daily dealer + table pace snapshots")]

    RAW --> PIPE["16-step pipeline<br/>py scripts/generate_all_dashboards.py"]
    PROB --> PIPE
    PACE --> PIPE

    PIPE --> REPORTS[/"output/reports/<br/>whale · chaser · operator<br/>heatmap · time-series CSVs"/]
    PIPE --> DATA[/"output/data/<br/>player indexes · behavior<br/>dossier payloads"/]
    PIPE --> CHUNKS[/"output/chunks/<br/>trajectory chunks · ~180 MB"/]
    PIPE --> DASH[/"output/dashboards/<br/>bi_dashboard.html<br/>player_behavior_dashboard.html<br/>game_probability_dashboard.html<br/>round_dealer_table_time_dashboard.html"/]
    PIPE --> PACE_OUT[/"output/round_dealer_table_time_data.json"/]
    PIPE --> PROGRESS[/"output/progress/<br/>progress.json (live status)"/]
```

---

## Pipeline Usage

Run the full pipeline to process these files:
```bash
py scripts/generate_all_dashboards.py
```

See `workspace_map.txt` for complete data flow documentation (sections 2A, 4, 6).