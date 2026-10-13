from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
if not (WORKSPACE / "workspace_map.txt").exists():
    for _parent in WORKSPACE.parents:
        if (_parent / "workspace_map.txt").exists():
            WORKSPACE = _parent
            break

import json
from pathlib import Path
from collections import defaultdict

DATA_FILE = Path(WORKSPACE / "output" / "dashboard_data.json")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    master_data = json.load(f)

json_str = json.dumps(master_data)

# ── MERGE PER-FILE DOSSIER INDICES INTO UNIFIED INDEX ──────────────────────
REPORT_DIR = Path(WORKSPACE / "output")
CHUNK_DIR = REPORT_DIR / "dossier_chunks"
CHUNK_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_SIZE = 1000

def merge_per_file_dossiers():
    """Merge 27 per-file indices into unified index + re-chunk trajectories."""
    print("Merging per-file dossier indices...")
    
    # Collect all player data from per-file indices
    player_data = {}  # pid -> {index_entry, detail_chunks}
    
    for f_idx in range(27):
        idx_path = REPORT_DIR / f"all_players_index_{f_idx:02d}.json"
        if not idx_path.exists():
            continue
        
        with open(idx_path, "r", encoding="utf-8") as f:
            idx = json.load(f)
        
        # Load all detail chunks for this file ONCE (avoid re-reading/parsing
        # the same ~1-5MB chunk file for every player entry).
        chunk_details = {}
        chunk_dir = REPORT_DIR / f"dossier_chunks_{f_idx:02d}"
        for cid in range(idx["meta"]["total_chunks"]):
            chunk_path = chunk_dir / f"chunk_{cid:04d}.js"
            if chunk_path.exists():
                with open(chunk_path, "r", encoding="utf-8") as cf:
                    content = cf.read()
                    if content.startswith("window.DOSSIER_CHUNK_"):
                        content = content.split("=", 1)[1].rstrip(";")
                        chunk_details.update(json.loads(content))

        for entry in idx.get("players", []):
            pid = entry["pid"]
            if pid not in player_data:
                player_data[pid] = {
                    "index_entry": entry,
                    "total_debit": entry["debit"],
                    "total_winlose": entry["winlose"],
                    "total_bets": entry["bets"],
                    "chunks": []
                }
            else:
                # Accumulate
                player_data[pid]["total_debit"] += entry["debit"]
                player_data[pid]["total_winlose"] += entry["winlose"]
                player_data[pid]["total_bets"] += entry["bets"]

            if pid in chunk_details:
                player_data[pid]["chunks"].append((f_idx, chunk_details[pid]))
    
    # Rebuild unified index sorted by total debit
    unified_entries = []
    for pid, data in player_data.items():
        entry = data["index_entry"].copy()
        entry["debit"] = round(data["total_debit"], 2)
        entry["winlose"] = round(data["total_winlose"], 2)
        entry["bets"] = data["total_bets"]
        entry["avg_bet"] = round(data["total_debit"] / data["total_bets"], 2) if data["total_bets"] else 0.0
        unified_entries.append((data["total_debit"], pid, entry, data["chunks"]))
    
    unified_entries.sort(key=lambda x: x[0], reverse=True)
    
    # Re-chunk and write unified chunks
    unified_chunks = defaultdict(dict)
    final_index_entries = []
    
    for rank, (total_debit, pid, entry, chunks) in enumerate(unified_entries):
        entry["id"] = rank
        final_index_entries.append(entry)
        
        # Concatenate trajectories from all chunks chronologically by timestamps
        if chunks:
            # Sort chunks by first timestamp
            sorted_chunks = sorted(chunks, key=lambda x: x[1].get("first_seen", "") if x[1].get("first_seen") else "")
            
            merged_detail = {}
            merged_balance_series = []
            merged_timestamps = []
            merged_games = {}
            merged_hours = [0] * 24
            merged_devices = {}
            merged_operators = {}
            merged_recent_rounds = []
            
            first_seen = None
            last_seen = None
            peak_balance = 0.0
            min_balance = float('inf')
            total_balance_points = 0
            balance_sum = 0.0
            
            for f_idx, detail in sorted_chunks:
                # Track first/last seen
                if detail.get("first_seen"):
                    if first_seen is None or detail["first_seen"] < first_seen:
                        first_seen = detail["first_seen"]
                if detail.get("last_seen"):
                    if last_seen is None or detail["last_seen"] > last_seen:
                        last_seen = detail["last_seen"]
                
                # Merge balance_series and timestamps
                if "balance_series" in detail and "timestamps" in detail:
                    bs = detail["balance_series"]
                    ts = detail["timestamps"]
                    for b, t in zip(bs, ts):
                        merged_balance_series.append(b)
                        merged_timestamps.append(t)
                        balance_sum += b
                        total_balance_points += 1
                        if b > peak_balance:
                            peak_balance = b
                        if b < min_balance:
                            min_balance = b
                
                # Merge games
                for g in detail.get("games", []):
                    game_name = g.get("game", "Unknown")
                    if game_name not in merged_games:
                        merged_games[game_name] = {"game": game_name, "bets": 0, "debit": 0.0, "credit": 0.0, "wins": 0, "losses": 0}
                    merged_games[game_name]["bets"] += g.get("bets", 0)
                    merged_games[game_name]["debit"] += g.get("debit", 0.0)
                    merged_games[game_name]["credit"] += g.get("credit", 0.0)
                    merged_games[game_name]["wins"] += g.get("wins", 0)
                    merged_games[game_name]["losses"] += g.get("losses", 0)
                
                # Merge hours
                for h_idx, h_val in enumerate(detail.get("hours", [])):
                    if h_idx < 24:
                        merged_hours[h_idx] += h_val
                
                # Merge devices
                for dev, count in detail.get("devices", {}).items():
                    merged_devices[dev] = merged_devices.get(dev, 0) + count
                
                # Merge operators
                for op, count in detail.get("operators", {}).items():
                    merged_operators[op] = merged_operators.get(op, 0) + count
                
                # Merge recent_rounds (keep last 100 chronologically)
                merged_recent_rounds.extend(detail.get("recent_rounds", []))
            
            # Sort recent rounds by time and keep last 100
            merged_recent_rounds.sort(key=lambda x: x.get("time", ""))
            merged_recent_rounds = merged_recent_rounds[-100:]
            
            # Calculate win rates for games
            merged_games_list = []
            for g in merged_games.values():
                total = g["wins"] + g["losses"]
                g["win_rate_pct"] = round(g["wins"] / total * 100, 2) if total > 0 else 0.0
                merged_games_list.append(g)
            
            # Use base detail from first chunk and update with merged data
            merged_detail = sorted_chunks[0][1].copy()
            merged_detail["balance_series"] = merged_balance_series
            merged_detail["timestamps"] = merged_timestamps
            merged_detail["first_seen"] = first_seen
            merged_detail["last_seen"] = last_seen
            merged_detail["peak_balance"] = peak_balance
            merged_detail["min_balance"] = min_balance if min_balance != float('inf') else 0.0
            merged_detail["avg_balance"] = round(balance_sum / total_balance_points, 2) if total_balance_points > 0 else 0.0
            merged_detail["games"] = merged_games_list
            merged_detail["hours"] = merged_hours
            merged_detail["devices"] = merged_devices
            merged_detail["operators"] = merged_operators
            merged_detail["recent_rounds"] = merged_recent_rounds
            
            chunk_id = rank // CHUNK_SIZE
            unified_chunks[chunk_id][pid] = merged_detail
    
    # Write unified index
    unified_index = {
        "meta": {
            "total_players": len(final_index_entries),
            "total_rows": sum(e["bets"] for e in final_index_entries),
            "files": 27,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chunk_size": CHUNK_SIZE,
            "total_chunks": (len(final_index_entries) + CHUNK_SIZE - 1) // CHUNK_SIZE,
        },
        "players": final_index_entries,
    }
    
    INDEX_FILE = REPORT_DIR / "all_players_index.json"
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(unified_index, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  -> {INDEX_FILE.name} ({INDEX_FILE.stat().st_size:,} bytes)")
    
    # Write unified chunks
    for cid in sorted(unified_chunks.keys()):
        js = "window.DOSSIER_CHUNK_%04d = " % cid + json.dumps(unified_chunks[cid], ensure_ascii=False, separators=(",", ":")) + ";"
        cpath = CHUNK_DIR / ("chunk_%04d.js" % cid)
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(js)
    print(f"  -> {len(unified_chunks)} unified chunks in dossier_chunks/")
    
    return unified_index

# Load or build the unified index. Per-export chunks may contain fields added
# after the aggregate was created (for example, timestamps used by the dossier
# activity calendar), so rebuild whenever a source index is newer.
INDEX_FILE = REPORT_DIR / "all_players_index.json"
source_indexes = [REPORT_DIR / f"all_players_index_{f_idx:02d}.json" for f_idx in range(27)]
source_indexes = [path for path in source_indexes if path.exists()]
rebuild_unified = (
    not INDEX_FILE.exists()
    or any(path.stat().st_mtime > INDEX_FILE.stat().st_mtime for path in source_indexes)
)
if rebuild_unified:
    print("Unified dossier index is missing or stale; rebuilding from per-file indices...")
    from datetime import datetime
    unified_index = merge_per_file_dossiers()
else:
    with open(INDEX_FILE, "r", encoding="utf-8") as inf:
        unified_index = json.load(inf)

index_meta = unified_index.get("meta", {})
index_players = unified_index.get("players", [])

DOSSIER_DATA_FILE = Path(WORKSPACE / "output" / "individual_dossiers_data.json")
with open(DOSSIER_DATA_FILE, "r", encoding="utf-8") as df:
    detailed_operators = json.load(df).get("operators", [])

combined_dossier = {
    "meta": index_meta,
    "players": index_players,
    "operators": detailed_operators,
}
dossier_json_str = json.dumps(combined_dossier, ensure_ascii=False)

# Load dossier section resources (plain HTML/JS injected via placeholders)
SECTIONS_DIR = Path(__file__).parent / "sections"

def _read_section(name):
    p = SECTIONS_DIR / name
    if p.exists():
        with open(p, "r", encoding="utf-8") as sf:
            return sf.read()
    return ""

DOSSIER_NAV_HTML = _read_section("nav_buttons.html")
DOSSIER_TABS_HTML = _read_section("tab_players.html") + "\n" + _read_section("tab_operators.html")
DOSSIER_SLIDES_HTML = _read_section("slides.html")
DOSSIER_JS = _read_section("dossier.js")

html_template = f'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Oriental Gaming Title BI & Risk Intelligence Console</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Apache ECharts -->
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <!-- FontAwesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">

  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace']
          }},
          colors: {{
            brand: {{
              50: '#eef2ff',
              100: '#e0e7ff',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
              900: '#1e1b4b'
            }},
            dark: {{
              bg: '#0a0d14',
              surface: '#111726',
              card: '#161f36',
              border: '#1f2d4d',
              muted: '#64748b'
            }}
          }}
        }}
      }}
    }}
  </script>

  <style>
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    .glass-card {{
      background: rgba(22, 31, 54, 0.7);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.07);
    }}
    .light .glass-card {{
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(0, 0, 0, 0.08);
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
    }}
    .chart-box {{
      min-height: 400px;
      width: 100%;
    }}
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(10, 13, 20, 0.5);
    }}
    ::-webkit-scrollbar-thumb {{
      background: #334155;
      border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: #475569;
    }}
    .nav-tab.active {{
      background: #4f46e5;
      color: #ffffff;
      box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.39);
    }}
    .slide {{
      display: none;
    }}
    .slide.active {{
      display: block;
      animation: fadeIn 0.3s ease-in-out;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    @media print {{
      .no-print {{ display: none !important; }}
      body {{ background: white !important; color: black !important; }}
      .glass-card {{ border: 1px solid #ccc !important; background: white !important; }}
    }}
  </style>
</head>
<body class="bg-[#0a0d14] text-slate-100 min-h-screen transition-colors duration-200">

  <!-- MASTER CONTAINER -->
  <div class="flex flex-col min-h-screen">

    <!-- TOP HEADER -->
    <header class="sticky top-0 z-50 bg-[#0c1222]/90 backdrop-blur-md border-b border-slate-800 px-6 py-4 no-print">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">
            <i class="fa-solid fa-chart-line text-lg"></i>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                ORIENTAL GAMING TITLE <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-semibold tracking-wider">BI CONSOLE</span>
              </h1>
              <span class="text-xs text-emerald-400 flex items-center gap-1 font-mono">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> LIVE AUDIT
              </span>
            </div>
            <p class="text-xs text-slate-400">Four-Pillar Executive Intelligence: Whales, Risk Tilts, Traffic Patterns & B2B Profitability</p>
          </div>
        </div>

        <!-- Global Header Stats Pill -->
        <div class="hidden xl:flex items-center gap-6 px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Total Debit</span>
            <span class="font-bold text-indigo-400 font-mono">586.64B</span>
          </div>
          <div class="w-px h-6 bg-slate-800"></div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Net GGR</span>
            <span class="font-bold text-emerald-400 font-mono">+10.15B</span>
          </div>
          <div class="w-px h-6 bg-slate-800"></div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Total Bets</span>
            <span class="font-bold text-slate-200 font-mono">18.28M</span>
          </div>
          <div class="w-px h-6 bg-slate-800"></div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Whale Share</span>
            <span class="font-bold text-amber-400 font-mono">247.92B (42.3%)</span>
          </div>
        </div>

        <!-- Mode & Utility Switchers -->
        <div class="flex items-center gap-2">
          <a href="player_behavior_dashboard.html" class="px-3.5 py-2 rounded-lg bg-cyan-950/60 hover:bg-cyan-900 text-cyan-300 text-xs font-semibold flex items-center gap-2 border border-cyan-700/50 transition" title="Open Player Behavioral Intelligence Deep-Dive">
            <i class="fa-solid fa-gamepad text-cyan-400"></i>
            <span>Behavior Telemetry</span>
          </a>
          <a href="game_probability_dashboard.html" class="px-3.5 py-2 rounded-lg bg-emerald-950/60 hover:bg-emerald-900 text-emerald-300 text-xs font-semibold flex items-center gap-2 border border-emerald-700/50 transition" title="Open Game Probability & House-Edge Dashboard">
            <i class="fa-solid fa-dice text-emerald-400"></i>
            <span>Probability &amp; HE</span>
          </a>
          <button id="viewToggleBtn" onclick="togglePresentationMode()" class="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition">
            <i class="fa-solid fa-person-chalkboard text-indigo-400"></i>
            <span id="viewModeLabel">Presentation Mode</span>
          </button>
          <button onclick="toggleTheme()" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition" title="Toggle Light/Dark Theme">
            <i id="themeIcon" class="fa-solid fa-moon"></i>
          </button>
          <button onclick="window.print()" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition" title="Print Executive Brief">
            <i class="fa-solid fa-print"></i>
          </button>
        </div>
      </div>

      <!-- NAVIGATION TABS (DASHBOARD MODE) -->
      <div id="dashboardNav" class="max-w-7xl mx-auto mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between overflow-x-auto gap-2">
        <div class="flex items-center gap-2">
          <button onclick="switchTab('overview')" class="nav-tab active px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-gauge-high"></i> Overview Cockpit
          </button>
          <button onclick="switchTab('whales')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-gem text-amber-400"></i> 1. VIP Whales
          </button>
          <button onclick="switchTab('chasers')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-shield-halved text-rose-400"></i> 2. Risk & Chasers
          </button>
          <button onclick="switchTab('traffic')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-clock text-cyan-400"></i> 3. Traffic & Timing
          </button>
          <button onclick="switchTab('operators')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-building-columns text-emerald-400"></i> 4. B2B Operators
          </button>
          <button onclick="switchTab('strategy')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-chess-knight text-purple-400"></i> 5. Strategic Roadmap
          </button>
{DOSSIER_NAV_HTML}        </div>
        <div class="text-[11px] text-slate-400 font-mono hidden md:block">
          Dataset: August 2026 Audit (27 Exports | 18.28M Bets)
        </div>
      </div>
    </header>

    <!-- MAIN BODY CONTENT -->
    <main class="flex-1 max-w-7xl mx-auto w-full p-6">

      <!-- ========================================================================= -->
      <!-- TAB 0: EXECUTIVE OVERVIEW COCKPIT -->
      <!-- ========================================================================= -->
      <section id="tab-overview" class="tab-pane space-y-6">
        <!-- Hero Banner -->
        <div class="glass-card rounded-2xl p-6 relative overflow-hidden bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-500/20">
          <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div class="max-w-3xl space-y-2">
              <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold">
                <i class="fa-solid fa-brain"></i> Advanced Multi-Faceted Business Intelligence
              </div>
              <h2 class="text-2xl lg:text-3xl font-extrabold tracking-tight text-white">
                Executive Audit: Concentration, Player Safety & Market Domination
              </h2>
              <p class="text-slate-300 text-sm leading-relaxed">
                Analysis of <strong>18,275,592 bets</strong> across <strong>750 operators</strong> and <strong>18 national jurisdictions</strong> reveals intense revenue concentration among VIP whales, high-risk loss-chasing behavioral tipping points, dramatic 2.58x server traffic swings, and monopolistic B2B partner dominance.
              </p>
            </div>
            <div class="flex flex-wrap lg:flex-col gap-3 shrink-0">
              <button onclick="switchTab('whales')" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition">
                <span>Inspect Whales</span> <i class="fa-solid fa-arrow-right"></i>
              </button>
              <button onclick="togglePresentationMode()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center justify-center gap-2 transition">
                <i class="fa-solid fa-play"></i> Launch Presentation
              </button>
            </div>
          </div>
        </div>

        <!-- 4 Pillars Core KPI Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Pillar 1 Card -->
          <div onclick="switchTab('whales')" class="glass-card rounded-2xl p-5 hover:border-amber-500/40 cursor-pointer transition group">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <i class="fa-solid fa-crown"></i> 1. VIP Concentration
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/10 text-amber-300 font-mono">Pareto Top 20</span>
            </div>
            <div class="text-2xl font-extrabold text-white font-mono">247.92 Billion</div>
            <div class="text-xs text-slate-400 mt-1">42.3% of Total Gross Debit</div>
            <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span class="text-slate-400">Indonesia: 72.0%</span>
              <span class="text-amber-400 group-hover:translate-x-1 transition font-semibold">Explore <i class="fa-solid fa-chevron-right text-[10px]"></i></span>
            </div>
          </div>

          <!-- Pillar 2 Card -->
          <div onclick="switchTab('chasers')" class="glass-card rounded-2xl p-5 hover:border-rose-500/40 cursor-pointer transition group">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                <i class="fa-solid fa-triangle-exclamation"></i> 2. Chaser Tilt Risk
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-400/10 text-rose-300 font-mono" id="navChaserFlagged">— Flagged</span>
            </div>
            <div class="text-2xl font-extrabold text-white font-mono">67.7% Net Losers</div>
            <div class="text-xs text-slate-400 mt-1">Peak Spike: 7,500x after 3 Losses</div>
            <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span class="text-slate-400">Tilt Threshold: 3 Losses</span>
              <span class="text-rose-400 group-hover:translate-x-1 transition font-semibold">Explore <i class="fa-solid fa-chevron-right text-[10px]"></i></span>
            </div>
          </div>

          <!-- Pillar 3 Card -->
          <div onclick="switchTab('traffic')" class="glass-card rounded-2xl p-5 hover:border-cyan-500/40 cursor-pointer transition group">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                <i class="fa-solid fa-server"></i> 3. Traffic & Timing
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-cyan-400/10 text-cyan-300 font-mono">18.28M Bets</span>
            </div>
            <div class="text-2xl font-extrabold text-white font-mono">18:00 & 20:00</div>
            <div class="text-xs text-slate-400 mt-1">Global Peak Traffic (>1.05M Bets/hr)</div>
            <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span class="text-slate-400">China 20h | BD 21h</span>
              <span class="text-cyan-400 group-hover:translate-x-1 transition font-semibold">Explore <i class="fa-solid fa-chevron-right text-[10px]"></i></span>
            </div>
          </div>

          <!-- Pillar 4 Card -->
          <div onclick="switchTab('operators')" class="glass-card rounded-2xl p-5 hover:border-emerald-500/40 cursor-pointer transition group">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <i class="fa-solid fa-handshake"></i> 4. B2B Profitability
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-300 font-mono">750 Partners</span>
            </div>
            <div class="text-2xl font-extrabold text-white font-mono">99.7% Monopoly</div>
            <div class="text-xs text-slate-400 mt-1">m88provnd Dominates Vietnam</div>
            <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span class="text-slate-400">Hold Rate: Up to 8.24%</span>
              <span class="text-emerald-400 group-hover:translate-x-1 transition font-semibold">Explore <i class="fa-solid fa-chevron-right text-[10px]"></i></span>
            </div>
          </div>
        </div>

        <!-- Executive Summary Dual Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-bolt text-indigo-400"></i> 24-Hour Global Betting Load vs Regional Pulses
                </h3>
                <p class="text-xs text-slate-400">Overall server load across 24 hours with peak scaling window</p>
              </div>
            </div>
            <div id="overviewTrafficChart" class="chart-box" style="height: 340px;"></div>
          </div>

          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-pie-chart text-amber-400"></i> Revenue Concentration & Risk Exposure
                </h3>
                <p class="text-xs text-slate-400">Whale debit share vs general turnover & Chaser win/loss ratio</p>
              </div>
            </div>
            <div id="overviewPillarChart" class="chart-box" style="height: 340px;"></div>
          </div>
        </div>

        <!-- Executive Findings Matrix -->
        <div class="glass-card rounded-2xl p-6">
          <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <i class="fa-solid fa-clipboard-check text-indigo-400"></i> Executive Findings & Strategic Directives
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div class="p-4 rounded-xl bg-slate-900/90 border border-amber-500/20 space-y-2">
              <div class="font-bold text-amber-400 flex items-center gap-2">
                <i class="fa-solid fa-crown"></i> Whale Exposure
              </div>
              <p class="text-slate-300">
                Top 20 whales account for <strong id="execWhaleDebit">—</strong>. The largest whale country controls <strong id="execWhaleTopCountryPct">—</strong> of whale debit. Avg session length is only <strong>11.4 minutes</strong>, proving whales rely on rapid burst betting rather than extended play.
              </p>
              <div class="text-[11px] text-amber-300/80 font-mono">Action: VIP Concierge & Liquidity Rings</div>
            </div>

            <div class="p-4 rounded-xl bg-slate-900/90 border border-rose-500/20 space-y-2">
              <div class="font-bold text-rose-400 flex items-center gap-2">
                <i class="fa-solid fa-triangle-exclamation"></i> Tilt Intervention
              </div>
              <p class="text-slate-300" id="execTiltText">
                <strong>—</strong> chasers detected. <strong>—</strong> end as net losers. Chasing begins decisively at <strong>3 consecutive losses</strong> (— trigger rate). Spikes reach up to <strong>—</strong> loss-bet debit.
              </p>
              <div class="text-[11px] text-rose-300/80 font-mono">Action: Automated Soft-Cooldowns at L3</div>
            </div>

            <div class="p-4 rounded-xl bg-slate-900/90 border border-cyan-500/20 space-y-2">
              <div class="font-bold text-cyan-400 flex items-center gap-2">
                <i class="fa-solid fa-clock"></i> Regional Push Windows
              </div>
              <p class="text-slate-300">
                Server load swings <strong>2.58x</strong>. Asian markets peak strictly in local evening slots (China 20:00, India/BD 21:00, Japan 19:00). High density markets (Japan 34.3% in 1 hr) require scheduled flash promotions.
              </p>
              <div class="text-[11px] text-cyan-300/80 font-mono">Action: Scale Cloud 16:00; Flash Push 18:30</div>
            </div>

            <div class="p-4 rounded-xl bg-slate-900/90 border border-emerald-500/20 space-y-2">
              <div class="font-bold text-emerald-400 flex items-center gap-2">
                <i class="fa-solid fa-building-columns"></i> B2B Skin Hegemony
              </div>
              <p class="text-slate-300">
                Total operator turnover $586.6B with $10.15B GGR. <strong>m88provnd</strong> controls <strong>99.7% of Vietnam</strong> ($163.5B). Indonesian skins show highest profit retention (up to 8.24% hold).
              </p>
              <div class="text-[11px] text-emerald-300/80 font-mono">Action: Protect Key Skins & Diversify VN</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 1: VIP & REVENUE CONCENTRATION (WHALES) -->
      <!-- ========================================================================= -->
      <section id="tab-whales" class="tab-pane hidden space-y-6">
        <!-- Section Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
              <i class="fa-solid fa-gem"></i> Area 1: Financial Backbone & Pareto Analysis
            </div>
            <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">VIP & Revenue Concentration (The "Whales")</h2>
            <p class="text-xs text-slate-400">Deep-dive into the top 20 players generating the majority of casino turnover</p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="exportTableToCSV('whalesTable', 'whale_analysis_top20.csv')" class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition">
              <i class="fa-solid fa-download text-amber-400"></i> Export Top 20 CSV
            </button>
          </div>
        </div>

        <!-- Whale KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Top 20 Total Turnover</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1">247.92 Billion</div>
            <span class="text-[11px] text-slate-400">42.3% of total casino wagering</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Total Wagers Placed</span>
            <div class="text-2xl font-extrabold text-white font-mono mt-1">161,507</div>
            <span class="text-[11px] text-slate-400">Avg Bet: 1,535,035 per wager</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Average Session Length</span>
            <div class="text-2xl font-extrabold text-cyan-400 font-mono mt-1">0.19 Hours</div>
            <span class="text-[11px] text-slate-400">~11.4 mins (Burst betting, not grinding)</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Geographic Hegemony</span>
            <div class="text-2xl font-extrabold text-emerald-400 font-mono mt-1">Indonesia (72.0%)</div>
            <span class="text-[11px] text-slate-400">14 of 20 whales originated in IDR</span>
          </div>
        </div>

        <!-- Whale Group Dossier -->
        <div class="glass-card rounded-2xl p-5 bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border border-amber-500/20">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
                <i class="fa-solid fa-users text-amber-400 text-xl"></i>
              </div>
              <div>
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-gem text-amber-400"></i> Whale Group Dossier
                </h3>
                <p class="text-xs text-slate-400">Aggregate behavioral & financial profile of the top 20 VIP whales</p>
              </div>
            </div>
            <span class="text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-300 font-mono font-semibold">20 Profiles</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-5">
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-amber-400 font-mono" id="whaleGroupTotalDebit">7.27B</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Total Debit</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-white font-mono" id="whaleGroupTotalBets">123,924</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Total Wagers</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-cyan-400 font-mono" id="whaleGroupAvgSession">0.74h</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Avg Session</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-emerald-400 font-mono" id="whaleGroupCountries">4</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Countries</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-rose-400 font-mono" id="whaleGroupConcentration">42.3%</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">of Casino Debit</div>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- Geographic Breakdown -->
            <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase font-semibold mb-3 flex items-center gap-1.5">
                <i class="fa-solid fa-earth-asia text-emerald-400"></i> Geographic Composition
              </div>
              <div class="space-y-2" id="whaleGroupGeoBreakdown">
                <!-- Populated by JS -->
              </div>
            </div>

            <!-- Behavioral Archetypes -->
            <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase font-semibold mb-3 flex items-center gap-1.5">
                <i class="fa-solid fa-mask text-indigo-400"></i> Behavioral Archetypes
              </div>
              <div class="space-y-2" id="whaleGroupArchetypes">
                <!-- Populated by JS -->
              </div>
            </div>

            <!-- Key Insights -->
            <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase font-semibold mb-3 flex items-center gap-1.5">
                <i class="fa-solid fa-lightbulb text-amber-400"></i> Key Group Insights
              </div>
              <ul class="text-xs text-slate-300 space-y-2" id="whaleGroupInsights">
                <!-- Populated by JS -->
              </ul>
            </div>
          </div>
        </div>

        <!-- Charts: Scatter Plot & Geographic Donut -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Scatter Plot (Engagement vs Spend) -->
          <div class="glass-card rounded-2xl p-5 lg:col-span-2">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-arrows-to-dot text-amber-400"></i> Engagement vs. Spend: The "Grinder" vs. "Burst" Dichotomy
                </h3>
                <p class="text-xs text-slate-400">Scatter plot of Avg Session Hours (X) vs Total Debit (Y). Bubble size reflects Total Bets.</p>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-slate-400">Scale:</span>
                <button id="scatterScaleBtn" onclick="toggleScatterScale()" class="px-2.5 py-1 rounded bg-slate-800 text-xs text-slate-300 border border-slate-700 font-mono">Logarithmic</button>
              </div>
            </div>
            <div id="whaleScatterChart" class="chart-box" style="height: 420px;"></div>
            <div class="mt-3 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 flex items-start gap-3">
              <i class="fa-solid fa-lightbulb text-amber-400 text-base mt-0.5"></i>
              <div>
                <strong>Crucial Analytical Takeaway:</strong> The top 3 biggest spenders (<code>JB_I804659I</code> at 33.85B, <code>3345123__ORGA_1</code> at 28.94B, and <code>c00083161879</code> at 26.55B) have average session lengths under <strong>13 minutes</strong> (0.10h - 0.22h). In extreme contrast, player <code>C0000001526929</code> logged 61,264 bets with an average session of <strong>36 seconds (0.01h)</strong>, exhibiting high-frequency automated/bot execution. Sustained grinders like <code>xnabati01</code> (0.58h) are rare exceptions.
              </div>
            </div>
          </div>

          <!-- Geographic Distribution Donut & Breakdown -->
          <div class="glass-card rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2 mb-1">
                <i class="fa-solid fa-earth-asia text-emerald-400"></i> Geographic VIP Distribution
              </h3>
              <p class="text-xs text-slate-400 mb-4">Total debit contribution by player country of origin</p>
              <div id="whaleGeoChart" class="chart-box" style="height: 280px;"></div>
            </div>
            <div class="space-y-3 pt-3 border-t border-slate-800">
              <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded-full bg-indigo-500"></span>
                  <span class="text-xs font-semibold text-white">Indonesia</span>
                  <span class="text-[10px] text-slate-400">(14 Players)</span>
                </div>
                <div class="text-right">
                  <span class="text-xs font-bold text-slate-200 font-mono">178.60B</span>
                  <span class="text-[10px] text-indigo-400 block font-semibold">72.04% Share</span>
                </div>
              </div>
              <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                  <span class="text-xs font-semibold text-white">Vietnam</span>
                  <span class="text-[10px] text-slate-400">(6 Players)</span>
                </div>
                <div class="text-right">
                  <span class="text-xs font-bold text-slate-200 font-mono">69.31B</span>
                  <span class="text-[10px] text-emerald-400 block font-semibold">27.96% Share</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top 20 Whale Leaderboard Table -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-list-ol text-amber-400"></i> Top 20 Whale Leaderboard
              </h3>
              <p class="text-xs text-slate-400">Complete ranking of the elite financial drivers with behavioral archetypes</p>
            </div>
            <div class="flex items-center gap-3">
              <input type="text" id="whaleSearchInput" onkeyup="filterWhaleTable()" placeholder="Search Player ID or Country..." class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500">
            </div>
          </div>

          <div class="overflow-x-auto">
            <table id="whalesTable" class="w-full text-left text-xs">
              <thead class="bg-slate-900/80 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                <tr>
                  <th class="py-3 px-3">Rank</th>
                  <th class="py-3 px-3">Player ID</th>
                  <th class="py-3 px-3">Origin</th>
                  <th class="py-3 px-3 text-right">Total Debit</th>
                  <th class="py-3 px-3 text-right">Total Bets</th>
                  <th class="py-3 px-3 text-right">Avg Bet Size</th>
                  <th class="py-3 px-3 text-right">Avg Session</th>
                  <th class="py-3 px-3 text-center">Behavioral Archetype</th>
                  <th class="py-3 px-3 text-center">Dossier</th>
                </tr>
              </thead>
              <tbody id="whalesTableBody" class="divide-y divide-slate-800/60 font-mono">
                <!-- Dynamically Populated -->
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 2: RESPONSIBLE GAMING & RISK PROFILES (CHASERS) -->
      <!-- ========================================================================= -->
      <section id="tab-chasers" class="tab-pane hidden space-y-6">
        <!-- Section Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
              <i class="fa-solid fa-shield-halved"></i> Area 2: Compliance, Player Safety & Chaser Detection
            </div>
            <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">Responsible Gaming & Risk Profiles</h2>
            <p class="text-xs text-slate-400">Identification of loss-chasing patterns, psychological tilt thresholds, and net financial outcomes</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs px-3 py-1.5 rounded-lg bg-rose-950/60 border border-rose-800/60 text-rose-300 font-medium">
              <i class="fa-solid fa-flag text-rose-400 mr-1"></i> <span id="area2Flagged">—</span> Problem Chasers Flagged
            </span>
          </div>
        </div>

        <!-- Chaser Risk KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Extreme Multiplier Record</span>
            <div class="text-2xl font-extrabold text-rose-400 font-mono mt-1" id="kpiExtremeSpike">7,500.0x Spike</div>
            <span class="text-[11px] text-slate-400">Player <code>NGC2Javin888</code> (10k -> 75M)</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Net Loser Percentage</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1" id="kpiNetLoserPct">67.67% Losers</div>
            <span class="text-[11px] text-slate-400" id="kpiNetLoserCount">8,105 players suffered net loss</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Primary Tilt Trigger</span>
            <div class="text-2xl font-extrabold text-cyan-400 font-mono mt-1">3 Consecutive Losses</div>
            <span class="text-[11px] text-slate-400" id="kpiL3Pct">33.5% of chasers tilt at streak #3</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Total Net Chaser Harm</span>
            <div class="text-2xl font-extrabold text-rose-400 font-mono mt-1" id="kpiChaserHarm">-238.40 Million</div>
            <span class="text-[11px] text-slate-400">Net cumulative loss for chasers</span>
          </div>
        </div>

        <!-- Chaser Group Dossier -->
        <div class="glass-card rounded-2xl p-5 bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border border-rose-500/20">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-rose-500/20 flex items-center justify-center">
                <i class="fa-solid fa-users text-rose-400 text-xl"></i>
              </div>
              <div>
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-shield-halved text-rose-400"></i> Chaser Group Dossier
                </h3>
                <p class="text-xs text-slate-400">Aggregate risk profile & behavioral patterns of <span id="chaserGroupSubtitle">—</span> flagged loss-chasers</p>
              </div>
            </div>
            <span class="text-xs px-2 py-1 rounded-full bg-rose-500/20 text-rose-300 font-mono font-semibold" id="chaserGroupProfiles">— Profiles</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-5">
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-rose-400 font-mono" id="chaserGroupTotalDebit">22.61B</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Total Debit</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-white font-mono" id="chaserGroupTotalCount">11,978</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Total Flagged</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-amber-400 font-mono" id="chaserGroupNetLosers">67.7%</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Net Losers</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-cyan-400 font-mono" id="chaserGroupTotalHarm">-238.4M</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Net P&L</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
              <div class="text-2xl font-extrabold text-indigo-400 font-mono" id="chaserGroupMaxSpike">7,500x</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-wider">Peak Spike</div>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- Risk Tier Distribution -->
            <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase font-semibold mb-3 flex items-center gap-1.5">
                <i class="fa-solid fa-layer-group text-rose-400"></i> Risk Tier Distribution
              </div>
              <div class="space-y-2" id="chaserGroupRiskTiers">
                <!-- Populated by JS -->
              </div>
            </div>

            <!-- Tilt Threshold Analysis -->
            <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase font-semibold mb-3 flex items-center gap-1.5">
                <i class="fa-solid fa-chart-line text-amber-400"></i> Tilt Threshold Analysis
              </div>
              <div class="space-y-2" id="chaserGroupTiltThresholds">
                <!-- Populated by JS -->
              </div>
            </div>

            <!-- Key Risk Insights -->
            <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase font-semibold mb-3 flex items-center gap-1.5">
                <i class="fa-solid fa-triangle-exclamation text-rose-400"></i> Key Risk Insights
              </div>
              <ul class="text-xs text-slate-300 space-y-2" id="chaserGroupInsights">
                <!-- Populated by JS -->
              </ul>
            </div>
          </div>
        </div>

        <!-- Charts: Risk Severity Tiers & Loss Streak Thresholds -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Risk Severity Tiers Chart -->
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-layer-group text-rose-400"></i> Risk Severity Tiers (by Spike Multiplier)
                </h3>
                <p class="text-xs text-slate-400">Distribution of chaser population across bet escalation tiers</p>
              </div>
            </div>
            <div id="chaserTiersChart" class="chart-box" style="height: 340px;"></div>
          </div>

          <!-- Tilt Threshold (Max Consecutive Losses) -->
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-chart-line text-amber-400"></i> Loss Thresholds: The "Tilt" Curve
                </h3>
                <p class="text-xs text-slate-400">Player count at exact consecutive loss streak triggering panic spikes</p>
              </div>
            </div>
            <div id="chaserTiltChart" class="chart-box" style="height: 340px;"></div>
          </div>
        </div>

        <!-- Financial Impact of Chasers Dual Breakdown -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="glass-card rounded-2xl p-5 lg:col-span-1">
            <h3 class="text-base font-bold text-white flex items-center gap-2 mb-1">
              <i class="fa-solid fa-scale-unbalanced text-cyan-400"></i> Financial Reality of Chasing
            </h3>
            <p class="text-xs text-slate-400 mb-4">Does erratic bet spiking help players recover?</p>
            <div id="chaserOutcomePie" class="chart-box" style="height: 240px;"></div>
            <div class="mt-4 p-3 rounded-xl bg-rose-950/40 border border-rose-900/40 text-xs text-rose-200">
              <strong>Definitive Proof:</strong> 67.7% of all chasers lose money overall. The illusion that escalating bets can recover deficits is statistically debunked by the data. Chasing merely compounds drawdown.
            </div>
          </div>

          <!-- Case Study Spotlight: Extreme Chasers -->
          <div class="glass-card rounded-2xl p-5 lg:col-span-2">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-user-ninja text-rose-400"></i> Extreme Case Studies: The 1,000x+ Super-Chasers
                </h3>
                <p class="text-xs text-slate-400">Detailed forensics on the highest risk profiles identified in the database</p>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
              <div class="p-3.5 rounded-xl bg-slate-900/90 border border-rose-500/30">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>NGC2Javin888</span>
                  <span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">7,500x Spike</span>
                </div>
                <div class="text-sm font-bold text-white font-mono">10K -> 75,000,000</div>
                <div class="text-[11px] text-slate-400 mt-2 space-y-0.5">
                  <div>Streak: <strong>3 Losses</strong></div>
                  <div>Debit: <strong>8.54 Billion</strong></div>
                  <div>Win/Loss: <span class="text-emerald-400 font-mono">+266.9M</span></div>
                </div>
              </div>

              <div class="p-3.5 rounded-xl bg-slate-900/90 border border-amber-500/30">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>p02mtfly95</span>
                  <span class="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">2,149x Spike</span>
                </div>
                <div class="text-sm font-bold text-white font-mono">1.00 -> 2,149.32</div>
                <div class="text-[11px] text-slate-400 mt-2 space-y-0.5">
                  <div>Streak: <strong>5 Losses</strong></div>
                  <div>Debit: <strong>5.28 Million</strong></div>
                  <div>Win/Loss: <span class="text-rose-400 font-mono">-169,791 (Net Loser)</span></div>
                </div>
              </div>

              <div class="p-3.5 rounded-xl bg-slate-900/90 border border-rose-500/30">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>C0000001479248</span>
                  <span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">1,500x Spike</span>
                </div>
                <div class="text-sm font-bold text-white font-mono">20K -> 30,000,000</div>
                <div class="text-[11px] text-slate-400 mt-2 space-y-0.5">
                  <div>Streak: <strong>3 Losses</strong></div>
                  <div>Debit: <strong>13.93 Billion</strong></div>
                  <div>Win/Loss: <span class="text-emerald-400 font-mono">+462.0M</span></div>
                </div>
              </div>
            </div>

            <!-- Recommended RG Interventions Table -->
            <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2">
              <div class="font-bold text-indigo-300 flex items-center gap-2">
                <i class="fa-solid fa-gavel"></i> Mandatory Regulatory & Player Protection Recommendations:
              </div>
              <ul class="list-disc list-inside text-slate-300 space-y-1">
                <li><strong>Loss-Streak Intervention at L3:</strong> Trigger automated in-game reality check dialogs when a player records 3 consecutive losses, where 33.5% of chasing initiates.</li>
                <li><strong>Bet Acceleration Throttle:</strong> Enforce hard limit preventing single bet increases exceeding 10x previous session baseline within a 15-minute losing window.</li>
                <li><strong>Dual-Track VIP Compliance:</strong> High spenders like <code>NGC2Javin888</code> who exhibit both whale status and 7,500x spikes must undergo mandatory Anti-Money Laundering (AML) and Source of Wealth (SoW) compliance audits.</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Top Extreme Chasers Table -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-table-list text-rose-400"></i> High-Risk Chaser Registry (Top Spikes)
              </h3>
              <p class="text-xs text-slate-400">Accounts flagged with the highest bet escalation multipliers</p>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-900/80 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                <tr>
                  <th class="py-3 px-3">Player ID</th>
                  <th class="py-3 px-3 text-right">Spike Multiplier</th>
                  <th class="py-3 px-3 text-center">Loss Streak</th>
                  <th class="py-3 px-3 text-right">Avg Loss Debit</th>
                  <th class="py-3 px-3 text-right">Spike Debit</th>
                  <th class="py-3 px-3 text-right">Total Bets</th>
                  <th class="py-3 px-3 text-right">Total Debit</th>
                  <th class="py-3 px-3 text-right">Total Win/Lose</th>
                  <th class="py-3 px-3 text-center">Status</th>
                  <th class="py-3 px-3 text-center">Dossier</th>
                </tr>
              </thead>
              <tbody id="chasersTableBody" class="divide-y divide-slate-800/60 font-mono">
                <!-- Dynamically Populated -->
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 3: TRAFFIC OPTIMIZATION & MARKETING TIMING -->
      <!-- ========================================================================= -->
      <section id="tab-traffic" class="tab-pane hidden space-y-6">
        <!-- Section Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold">
              <i class="fa-solid fa-clock"></i> Area 3: IT Load Anticipation & Marketing Geo-Targeting
            </div>
            <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">Traffic Optimization & Marketing Timing</h2>
            <p class="text-xs text-slate-400">24-hour global server load curve, regional heatmaps, and hourly engagement density</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs px-3 py-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 font-medium">
              <i class="fa-solid fa-server mr-1"></i> Peak Window: 18:00 - 21:00 UTC
            </span>
          </div>
        </div>

        <!-- Traffic KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Global Peak Hour</span>
            <div class="text-2xl font-extrabold text-cyan-400 font-mono mt-1">18:00 & 20:00</div>
            <span class="text-[11px] text-slate-400">1,055,522 bets at 18:00</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Trough Load Hour</span>
            <div class="text-2xl font-extrabold text-slate-300 font-mono mt-1">02:00 (409K Bets)</div>
            <span class="text-[11px] text-slate-400">Safe cold-backup window</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Peak-to-Trough Swing</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1">2.58x Volatility</div>
            <span class="text-[11px] text-slate-400">Auto-scaling capacity ratio</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Most Concentrated Market</span>
            <div class="text-2xl font-extrabold text-rose-400 font-mono mt-1">Japan (34.3% @ 19h)</div>
            <span class="text-[11px] text-slate-400">Narrow flash marketing window</span>
          </div>
        </div>

        <!-- Global Peak Traffic Curve (Line/Area Chart) -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-chart-area text-cyan-400"></i> Global Peak Traffic Curve (24-Hour Betting Volume)
              </h3>
              <p class="text-xs text-slate-400">Hourly betting totals across all 27 files (18.28M bets) with server scaling thresholds</p>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <span class="inline-flex items-center gap-1.5 text-slate-300">
                <span class="w-3 h-3 rounded-full bg-cyan-500"></span> Bets Placed
              </span>
              <span class="inline-flex items-center gap-1.5 text-rose-400">
                <span class="w-3 h-3 rounded-full bg-rose-500/40 border border-rose-500"></span> Critical Capacity Zone
              </span>
            </div>
          </div>
          <div id="trafficCurveChart" class="chart-box" style="height: 380px;"></div>
        </div>

        <!-- Regional Heatmap (18 Countries x 24 Hours) -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-table-cells text-indigo-400"></i> Regional Peak Traffic Heatmap (Country vs Hour Matrix)
              </h3>
              <p class="text-xs text-slate-400">Y-Axis: 18 Countries | X-Axis: 24 Hours. Demonstrates exact local peak windows for marketing automation.</p>
            </div>
            <div class="flex items-center gap-2">
              <button id="heatmapNormalizeBtn" onclick="toggleHeatmapNormalize()" class="px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-700 hover:bg-slate-700 transition">
                <i class="fa-solid fa-sliders text-indigo-400 mr-1"></i> Mode: <span id="heatmapModeLabel">Country Relative (Normalized)</span>
              </button>
            </div>
          </div>
          <div id="trafficHeatmapChart" class="chart-box" style="height: 520px;"></div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 text-xs">
            <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <span class="font-bold text-amber-400">China (Peak: 20:00)</span>
              <p class="text-slate-400 mt-1">772,720 bets at 20:00. Massive sheer volume driving the global curve. Push campaigns best at 19:30.</p>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <span class="font-bold text-cyan-400">Bangladesh & India (Peak: 21:00)</span>
              <p class="text-slate-400 mt-1">BD concentrates 33.0% of all bets at 21:00; India spikes 12,778 bets. Regional bonus drops at 20:45.</p>
            </div>
            <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <span class="font-bold text-emerald-400">Vietnam (Peak: 09:00 Morning)</span>
              <p class="text-slate-400 mt-1">Unlike other markets, Vietnam shows a heavy morning peak (30,597 bets at 09:00). Morning breakfast offers work best.</p>
            </div>
          </div>
        </div>

        <!-- Engagement Density Bar Chart -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-chart-column text-amber-400"></i> Market Engagement Density (% Volume in Peak Hour)
              </h3>
              <p class="text-xs text-slate-400">High % = Concentrated Flash Markets; Low % = Steady Round-the-Clock Markets</p>
            </div>
          </div>
          <div id="trafficDensityChart" class="chart-box" style="height: 380px;"></div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 4: B2B OPERATOR PROFITABILITY -->
      <!-- ========================================================================= -->
      <section id="tab-operators" class="tab-pane hidden space-y-6">
        <!-- Section Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
              <i class="fa-solid fa-building-columns"></i> Area 4: B2B Skins, Partner Retentions & Market Dominance
            </div>
            <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">B2B Operator Profitability & Dominance</h2>
            <p class="text-xs text-slate-400">Analysis of 750 operators, profit margins, volume vs value segmentation, and regional monopolies</p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="exportTableToCSV('operatorsTable', 'operator_performance_top50.csv')" class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition">
              <i class="fa-solid fa-download text-emerald-400"></i> Export Top 50 CSV
            </button>
          </div>
        </div>

        <!-- Operator KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Total Operator Turnover</span>
            <div class="text-2xl font-extrabold text-emerald-400 font-mono mt-1">586.64 Billion</div>
            <span class="text-[11px] text-slate-400">750 tracked skin integrations</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Net Operator GGR</span>
            <div class="text-2xl font-extrabold text-white font-mono mt-1">+10.15 Billion</div>
            <span class="text-[11px] text-slate-400">Gross Gaming Revenue generated</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Largest Single Skin</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1">m88provnd (163.5B)</div>
            <span class="text-[11px] text-slate-400">Controls 99.7% of Vietnam volume</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Peak Hold Rate Margin</span>
            <div class="text-2xl font-extrabold text-indigo-400 font-mono mt-1">8.24% Retention</div>
            <span class="text-[11px] text-slate-400">mog803Hoki311 (Top per-bet yield)</span>
          </div>
        </div>

        <!-- Charts: Operator ROI Ranking & Volume vs Value Bubble Plot -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Operator ROI / Hold Rate Comparison -->
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-percent text-emerald-400"></i> Operator Hold Margin % Ranking
                </h3>
                <p class="text-xs text-slate-400">Net casino retention margin per bet turnover (100% - RTP) for high-volume operators</p>
              </div>
            </div>
            <div id="operatorRoiChart" class="chart-box" style="height: 380px;"></div>
          </div>

          <!-- Volume vs Value Bubble Chart -->
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-soap text-cyan-400"></i> Volume vs. Value Matrix (Turnover vs Value)
                </h3>
                <p class="text-xs text-slate-400">X: Total Bets | Y: Total Debit | Bubble Size: Unique Players</p>
              </div>
            </div>
            <div id="operatorBubbleChart" class="chart-box" style="height: 380px;"></div>
          </div>
        </div>

        <!-- Regional Monopolies Matrix -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-chess-rook text-amber-400"></i> Regional Market Monopolies & Skin Penetration
              </h3>
              <p class="text-xs text-slate-400">Leading operator per country and degree of market monopolization</p>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div class="p-4 rounded-xl bg-slate-900/90 border border-emerald-500/30 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <i class="fa-solid fa-star"></i> Vietnam (VND)
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold font-mono">99.7% MONOPOLY</span>
              </div>
              <div class="text-base font-extrabold text-white">m88provnd</div>
              <div class="text-xs text-slate-400 space-y-0.5">
                <div>Debit: <strong class="text-slate-200 font-mono">163.53 Billion</strong></div>
                <div>GGR Generated: <strong class="text-emerald-400 font-mono">+3.26 Billion</strong></div>
                <div>Players: <strong class="text-slate-200">863</strong> | Bets: <strong class="text-slate-200 font-mono">429,220</strong></div>
              </div>
              <div class="text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                Near 100% concentration in Vietnam makes m88provnd the single most critical partner in the casino's portfolio.
              </div>
            </div>

            <div class="p-4 rounded-xl bg-slate-900/90 border border-indigo-500/30 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-indigo-400 flex items-center gap-1.5">
                  <i class="fa-solid fa-flag"></i> Indonesia (IDR)
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold font-mono">22.6% Competitive</span>
              </div>
              <div class="text-base font-extrabold text-white">mog313qq288idr1</div>
              <div class="text-xs text-slate-400 space-y-0.5">
                <div>Debit: <strong class="text-slate-200 font-mono">88.12 Billion</strong></div>
                <div>GGR Generated: <strong class="text-emerald-400 font-mono">+1.07 Billion</strong></div>
                <div>Key Competitors: <code>mog309sg8IDNSport</code> (14.4%), <code>mog809nxtidr</code> (11.3%)</div>
              </div>
              <div class="text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                Highly diversified and competitive ecosystem with over 20 active tier-1 skins.
              </div>
            </div>

            <div class="p-4 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                  <i class="fa-solid fa-flag"></i> South Korea (KRW)
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-bold font-mono">36.7% Leader</span>
              </div>
              <div class="text-base font-extrabold text-white">mog780krw</div>
              <div class="text-xs text-slate-400 space-y-0.5">
                <div>Debit: <strong class="text-slate-200 font-mono">11.14 Billion</strong></div>
                <div>GGR Generated: <strong class="text-emerald-400 font-mono">+277.3 Million</strong></div>
                <div>Bets: <strong class="text-slate-200 font-mono">652,153</strong> | Players: <strong class="text-slate-200">379</strong></div>
              </div>
              <div class="text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                Massive bet volume engine with steady margins (2.49% hold). Followed by <code>mog853krw</code> (7.79B).
              </div>
            </div>
          </div>
        </div>

        <!-- Master Top 50 Operators Table -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-table-list text-emerald-400"></i> Top 50 B2B Partner Brands
              </h3>
              <p class="text-xs text-slate-400">Master ranking of operators by total turnover with profit retention metrics</p>
            </div>
            <input type="text" id="operatorSearchInput" onkeyup="filterOperatorTable()" placeholder="Search Operator or Country..." class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500">
          </div>
          <div class="overflow-x-auto">
            <table id="operatorsTable" class="w-full text-left text-xs">
              <thead class="bg-slate-900/80 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                <tr>
                  <th class="py-3 px-3">Operator</th>
                  <th class="py-3 px-3">Country</th>
                  <th class="py-3 px-3 text-right">Total Debit</th>
                  <th class="py-3 px-3 text-right">Net GGR</th>
                  <th class="py-3 px-3 text-right">Hold %</th>
                  <th class="py-3 px-3 text-right">Raw RTP (ROI)</th>
                  <th class="py-3 px-3 text-right">Total Bets</th>
                  <th class="py-3 px-3 text-right">Unique Players</th>
                  <th class="py-3 px-3 text-right">Avg Bet</th>
                  <th class="py-3 px-3 text-center">Dossier</th>
                </tr>
              </thead>
              <tbody id="operatorsTableBody" class="divide-y divide-slate-800/60 font-mono">
                <!-- Dynamically Populated -->
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 5: STRATEGIC ROADMAP & RECOMMENDATIONS -->
      <!-- ========================================================================= -->
      <section id="tab-strategy" class="tab-pane hidden space-y-6">
        <div class="glass-card rounded-2xl p-6 bg-gradient-to-r from-purple-950/40 via-slate-900 to-slate-900 border border-purple-500/20">
          <div class="max-w-3xl space-y-2">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-semibold">
              <i class="fa-solid fa-chess-knight"></i> Executive Playbook
            </div>
            <h2 class="text-2xl font-extrabold text-white tracking-tight">Four-Pillar Executive Action Plan & Roadmap</h2>
            <p class="text-xs text-slate-300">Actionable operational, technical, and commercial recommendations synthesized from data evidence.</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Pillar 1 Strategy -->
          <div class="glass-card rounded-2xl p-5 border-l-4 border-l-amber-500">
            <h3 class="text-base font-bold text-white flex items-center gap-2 mb-2">
              <i class="fa-solid fa-gem text-amber-400"></i> Pillar 1: VIP Whale Safeguarding & Retention
            </h3>
            <ul class="text-xs text-slate-300 space-y-2.5">
              <li><strong>Dedicated Indonesian VIP Concierge:</strong> Since 72% of top whale debit originates in Indonesia, establish round-the-clock Bahasa Indonesia VIP account managers with instant telegram/WhatsApp support.</li>
              <li><strong>Micro-Session Rapid Wagering Infrastructure:</strong> Whales average 11.4-minute sessions. Optimize mobile UI for instantaneous bet placement, ultra-low latency WebSocket feeds, and rapid re-betting capabilities.</li>
              <li><strong>Liquidity Hedging for Top 3 Whales:</strong> Players like <code>JB_I804659I</code> (33.8B debit) require dynamic risk-hedging algorithms to mitigate catastrophic single-round house variance.</li>
            </ul>
          </div>

          <!-- Pillar 2 Strategy -->
          <div class="glass-card rounded-2xl p-5 border-l-4 border-l-rose-500">
            <h3 class="text-base font-bold text-white flex items-center gap-2 mb-2">
              <i class="fa-solid fa-shield-halved text-rose-400"></i> Pillar 2: Responsible Gaming & Algorithmic Tilt Dampener
            </h3>
            <ul class="text-xs text-slate-300 space-y-2.5">
              <li><strong>Loss-Streak 3 Auto-Intervention:</strong> Data proves <span id="pillarL3Pct">33.5%</span> of chasers initiate erratic spikes after 3 consecutive losses. Deploy automated subtle UI friction (e.g., 3-second spin cooldown, reality-check balance prompt).</li>
              <li><strong>Spike Multiplier Hard Caps:</strong> Implement dynamic risk controls capping consecutive bet spikes at 50x session baseline to prevent reckless 7,500x escalations that bankrupt players.</li>
              <li><strong>Player Safety Dashboard for Regulators:</strong> Package chaser detection telemetry into compliance reports to demonstrate proactive ESG and gaming integrity to tier-1 licensing bodies.</li>
            </ul>
          </div>

          <!-- Pillar 3 Strategy -->
          <div class="glass-card rounded-2xl p-5 border-l-4 border-l-cyan-500">
            <h3 class="text-base font-bold text-white flex items-center gap-2 mb-2">
              <i class="fa-solid fa-server text-cyan-400"></i> Pillar 3: IT Cloud Elasticity & Precision Geo-Push Timing
            </h3>
            <ul class="text-xs text-slate-300 space-y-2.5">
              <li><strong>Proactive Server Scale-Up at 16:00 UTC:</strong> Rather than reactive autoscaling, pre-warm database clusters and game server instances at 16:00 UTC to seamlessly absorb the 18:00 - 21:00 peak (>1.05M bets/hour).</li>
              <li><strong>Scheduled Nightly Maintenance:</strong> Confine database vacuuming and system patching strictly to 01:30 - 03:30 UTC when traffic drops to 409k bets.</li>
              <li><strong>Timezone-Synchronized Marketing Drops:</strong> Push automated bonuses at 19:15 for China (peaks 20:00), 20:15 for Bangladesh/India (peaks 21:00), and 08:15 for Vietnam (morning peak 09:00).</li>
            </ul>
          </div>

          <!-- Pillar 4 Strategy -->
          <div class="glass-card rounded-2xl p-5 border-l-4 border-l-emerald-500">
            <h3 class="text-base font-bold text-white flex items-center gap-2 mb-2">
              <i class="fa-solid fa-handshake text-emerald-400"></i> Pillar 4: B2B Commercial Optimization & Key Skin Risk
            </h3>
            <ul class="text-xs text-slate-300 space-y-2.5">
              <li><strong>Protect Vietnam Monopolist (m88provnd):</strong> m88provnd provides 163.5B (99.7% of Vietnam debit). Provide dedicated SLA, custom game exclusivity, and revenue-share incentives to prevent churn to competitors.</li>
              <li><strong>Expand Indonesian Skin Network:</strong> The Indonesian market is decentralized across 20+ skins with healthy 3%-8% hold margins. Accelerate onboarding of IDR affiliates.</li>
              <li><strong>Audit Zero-Retention Skins:</strong> Operators with negative hold (players won net funds, e.g. <code>mog803Garuda</code> with -0.99% margin) should undergo immediate game RTP verification and syndicate collusion checks.</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- PRESENTATION DECK MODE (FULLSCREEN SLIDES) -->
      <!-- ========================================================================= -->
      <section id="presentationDeck" class="hidden space-y-6">
        <!-- Presentation Navigation Bar -->
        <div class="flex items-center justify-between bg-slate-900/90 border border-slate-800 p-4 rounded-2xl">
          <div class="flex items-center gap-3">
            <button onclick="togglePresentationMode()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition">
              <i class="fa-solid fa-xmark mr-1"></i> Exit Presentation
            </button>
            <span class="text-xs text-slate-400 font-mono">Slide <span id="currentSlideNum" class="text-white font-bold">1</span> of 8</span>
          </div>

          <div class="flex items-center gap-2">
            <button onclick="prevSlide()" class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow transition">
              <i class="fa-solid fa-chevron-left mr-1"></i> Prev
            </button>
            <button onclick="nextSlide()" class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow transition">
              Next <i class="fa-solid fa-chevron-right ml-1"></i>
            </button>
          </div>
        </div>

        <!-- SLIDE 1 -->
        <div id="slide-1" class="slide active glass-card rounded-2xl p-8 space-y-6 min-h-[580px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-bold border border-indigo-500/30">
            SLIDE 1 // EXECUTIVE OVERVIEW
          </div>
          <h2 class="text-3xl font-black text-white">August 2026 Operations Audit: The 4 Strategic Pillars</h2>
          <p class="text-slate-300 text-base max-w-4xl">
            A comprehensive quantitative investigation across 18,275,592 wagers, 750 partner operators, and 18 countries. We examine the structural concentration of wealth, behavioral risk indicators, server scaling requirements, and B2B partner profitability.
          </p>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span class="text-xs text-slate-400 block font-semibold">Total Debit Turnover</span>
              <span class="text-2xl font-bold text-indigo-400 font-mono">586.64B</span>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span class="text-xs text-slate-400 block font-semibold">Total Gross Bets</span>
              <span class="text-2xl font-bold text-white font-mono">18.28 Million</span>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span class="text-xs text-slate-400 block font-semibold">Top 20 Whale Share</span>
              <span class="text-2xl font-bold text-amber-400 font-mono">247.92B (42.3%)</span>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span class="text-xs text-slate-400 block font-semibold">Flagged Chasers</span>
              <span class="text-2xl font-bold text-rose-400 font-mono" id="slideFlaggedChasers">— (—% Net Loss)</span>
            </div>
          </div>
        </div>

        <!-- SLIDE 2 -->
        <div id="slide-2" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[580px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold border border-amber-500/30">
            SLIDE 2 // VIP REVENUE CONCENTRATION
          </div>
          <h2 class="text-3xl font-black text-white">Whale Analytics: Rapid Burst Bets Over Long Grinds</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p>
                <strong>The 80/20 Rule in Action:</strong> The top 20 players generate an astounding <strong>$247.92 Billion</strong>.
              </p>
              <p>
                <strong>Geographic Concentration:</strong> Indonesia produces <strong>72.04%</strong> of whale turnover ($178.6B), with Vietnam capturing the remaining <strong>27.96%</strong> ($69.3B).
              </p>
              <p>
                <strong>Debunking the "Grinder" Myth:</strong> The average whale session is merely <strong>0.19 hours (11.4 minutes)</strong>! Our highest value players do not sit for hours; they make massive, decisive, quick betting sequences.
              </p>
            </div>
            <div id="slideWhaleGeoChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 3 -->
        <div id="slide-3" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[580px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/30">
            SLIDE 3 // RESPONSIBLE GAMING & PLAYER SAFETY
          </div>
          <h2 class="text-3xl font-black text-white">Anatomy of Loss-Chasing: The 3-Streak Psychological Tilt</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p>
                <strong><span id="slideChaserCount">—</span> Chasers Identified:</strong> Flagged when consecutive losses trigger bet-size spikes up to <strong>7,500x</strong> baseline.
              </p>
              <p>
                <strong>The Tipping Point:</strong> Over <strong><span id="slideL3Pct">—</span>%</strong> of all chasing behavior ignites at precisely <strong>3 consecutive losses</strong>. Streaks 3 through 5 account for 71.8% of all panic bets.
              </p>
              <p>
                <strong>Chasing Fails:</strong> <strong><span id="slideNetLoserPct">—</span>% of chasers end up in net negative drawdown</strong>, confirming that erratic bets deepen financial loss rather than recovering it.
              </p>
            </div>
            <div id="slideChaserTiltChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 4 -->
        <div id="slide-4" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[580px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold border border-cyan-500/30">
            SLIDE 4 // TRAFFIC & TIMING STRATEGY
          </div>
          <h2 class="text-3xl font-black text-white">Traffic Volatility & Precision Push Marketing Windows</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p>
                <strong>2.58x Server Load Swing:</strong> Traffic surges from 409,381 bets at 02:00 UTC to <strong>1,055,522 bets at 18:00 UTC</strong> and 1,053,018 at 20:00 UTC.
              </p>
              <p>
                <strong>Regional Timezone Divergence:</strong>
                <br>• <strong>China:</strong> 20:00 Peak (772,720 bets)
                <br>• <strong>Bangladesh:</strong> 21:00 Peak (33.0% concentrated in 1 hour)
                <br>• <strong>Japan:</strong> 19:00 Peak (34.3% concentrated in 1 hour)
                <br>• <strong>Vietnam:</strong> 09:00 Morning Peak (30,597 bets)
              </p>
            </div>
            <div id="slideTrafficChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 5 -->
        <div id="slide-5" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[580px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold border border-emerald-500/30">
            SLIDE 5 // B2B OPERATOR ECONOMICS
          </div>
          <h2 class="text-3xl font-black text-white">Partner Profitability & Regional Hegemonies</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p>
                <strong>The Vietnam Monopolist:</strong> <code>m88provnd</code> commands <strong>99.7% of the Vietnam market</strong> ($163.5B debit, $3.26B net GGR). It is the enterprise's most vital single partner.
              </p>
              <p>
                <strong>Highest Yield Skins:</strong> Operators like <code>mog803Hoki311</code> (8.24% hold) and <code>m88proidr</code> (6.60% hold) generate the highest casino profit per bet dollar.
              </p>
              <p>
                <strong>Volume vs. Value Split:</strong> Some skins operate with few whales (<code>mog310jb</code>: 44 players, 37.1B debit), while others operate as mass low-roller engines (<code>mog809trgidr</code>: 8,143 players).
              </p>
            </div>
            <div id="slideOperatorBubbleChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 6 -->
        <div id="slide-6" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[580px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-bold border border-purple-500/30">
            SLIDE 6 // EXECUTIVE ACTION PLAN
          </div>
          <h2 class="text-3xl font-black text-white">Strategic Roadmap: Immediate Implementation Directives</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 text-xs">
            <div class="p-4 rounded-xl bg-slate-900 border border-amber-500/30 space-y-2">
              <span class="font-bold text-amber-400 block text-sm">1. Whale Retention & Protection</span>
              <p class="text-slate-300">Deploy dedicated Indonesian VIP managers for the 14 IDR whales. Build latency-optimized fast-betting interfaces to cater to their ~11-minute burst gaming behavior.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-rose-500/30 space-y-2">
              <span class="font-bold text-rose-400 block text-sm">2. Algorithmic Tilt Cooldowns</span>
              <p class="text-slate-300">Deploy mandatory soft-friction and cooldown prompts after 3 consecutive losses to curb panic spikes, protecting player longevity and meeting tier-1 licensing standards.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-cyan-500/30 space-y-2">
              <span class="font-bold text-cyan-400 block text-sm">3. Infrastructure & Scheduled Marketing</span>
              <p class="text-slate-300">Auto-scale cloud clusters at 16:00 UTC before the 18:00 - 21:00 peak. Fire targeted push notifications at 19:15 for China and 20:15 for Bangladesh/India.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-emerald-500/30 space-y-2">
              <span class="font-bold text-emerald-400 block text-sm">4. B2B Commercial Expansion</span>
              <p class="text-slate-300">Secure long-term exclusive SLAs with m88provnd (99.7% of Vietnam) while acquiring new affiliates in high-margin Indonesian segments (3%-8% hold).</p>
            </div>
          </div>
        </div>
{DOSSIER_SLIDES_HTML}      </section>

{DOSSIER_TABS_HTML}
    </main>

    <!-- FOOTER -->
    <footer class="mt-auto py-6 border-t border-slate-800 text-center text-xs text-slate-500 no-print">
      <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-2">
        <span>ORIENTAL GAMING TITLE BI & RISK CONSOLE &bull; Enterprise Analytics Suite</span>
        <span class="font-mono">Audited Data: August 2026 Operations &bull; Generated October 2026</span>
      </div>
    </footer>

  </div>

  <!-- EMBEDDED MASTER DATASET -->
  <script id="dashboard-raw-data" type="application/json">
{json_str}
  </script>

  <!-- EMBEDDED DOSSIER DATASET (ALL PLAYERS INDEX + OPERATORS) -->
  <script id="dossier-raw-data" type="application/json">
{dossier_json_str}
  </script>

  <!-- DASHBOARD CONTROLLER SCRIPT -->
  <script>
    // Load dataset
    const DATA = JSON.parse(document.getElementById('dashboard-raw-data').textContent);
    console.log("Oriental Gaming Title BI Dashboard Loaded Data:", DATA);

    let isPresentationMode = false;
    let currentSlide = 1;
    const totalSlides = 8;
    let isScatterLog = true;
    let isHeatmapNormalized = true;
    let chartInstances = {{}};

    // Initialize Dashboard
    document.addEventListener('DOMContentLoaded', () => {{
      populateWhaleTable();
      populateChaserTable();
      populateOperatorTable();
      populateWhaleGroupDossier();
      populateChaserGroupDossier();
      initCharts();
      setupKeyboardNavigation();
    }});

    // Tab Navigation
    function switchTab(tabId) {{
      if (isPresentationMode) togglePresentationMode();
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));

      const targetPane = document.getElementById(`tab-${{tabId}}`);
      if (targetPane) targetPane.classList.remove('hidden');

      // Highlight tab button
      const clickedBtn = Array.from(document.querySelectorAll('.nav-tab')).find(b => b.getAttribute('onclick')?.includes(tabId));
      if (clickedBtn) clickedBtn.classList.add('active');

      // Initialize or resize charts for active tab
      setTimeout(() => {{
        if (tabId === 'overview') {{
          if (!chartInstances['overviewTraffic']) initOverviewTrafficChart();
          if (!chartInstances['overviewPillar']) initOverviewPillarChart();
        }} else if (tabId === 'whales') {{
          if (!chartInstances['whaleScatter']) initWhaleScatterChart();
          if (!chartInstances['whaleGeo']) initWhaleGeoChart();
        }} else if (tabId === 'chasers') {{
          if (!chartInstances['chaserTiers']) initChaserTiersChart();
          if (!chartInstances['chaserTilt']) initChaserTiltChart();
          if (!chartInstances['chaserOutcome']) initChaserOutcomePie();
        }} else if (tabId === 'traffic') {{
          if (!chartInstances['trafficCurve']) initTrafficCurveChart();
          if (!chartInstances['trafficHeatmap']) initTrafficHeatmapChart();
          if (!chartInstances['trafficDensity']) initTrafficDensityChart();
        }} else if (tabId === 'operators') {{
          if (!chartInstances['operatorRoi']) initOperatorRoiChart();
          if (!chartInstances['operatorBubble']) initOperatorBubbleChart();
        }}
        resizeAllCharts();
      }}, 50);
    }}

    // Toggle Presentation Mode
    function togglePresentationMode() {{
      isPresentationMode = !isPresentationMode;
      const deck = document.getElementById('presentationDeck');
      const tabs = document.querySelectorAll('.tab-pane');
      const nav = document.getElementById('dashboardNav');
      const btnLabel = document.getElementById('viewModeLabel');

      if (isPresentationMode) {{
        tabs.forEach(t => t.classList.add('hidden'));
        deck.classList.remove('hidden');
        nav.classList.add('hidden');
        btnLabel.textContent = "Dashboard View";
        showSlide(currentSlide);
      }} else {{
        deck.classList.add('hidden');
        nav.classList.remove('hidden');
        btnLabel.textContent = "Presentation Mode";
        switchTab('overview');
      }}
    }}

    // Slide Controller
    function showSlide(idx) {{
      currentSlide = idx;
      document.querySelectorAll('.slide').forEach((s, i) => {{
        if (i + 1 === idx) s.classList.add('active');
        else s.classList.remove('active');
      }});
      document.getElementById('currentSlideNum').textContent = idx;
      setTimeout(renderSlideCharts, 100);
    }}

    function nextSlide() {{
      if (currentSlide < totalSlides) showSlide(currentSlide + 1);
      else showSlide(1);
    }}

    function prevSlide() {{
      if (currentSlide > 1) showSlide(currentSlide - 1);
      else showSlide(totalSlides);
    }}

    function setupKeyboardNavigation() {{
      window.addEventListener('keydown', (e) => {{
        if (!isPresentationMode) return;
        if (e.key === 'ArrowRight' || e.key === 'Space') nextSlide();
        else if (e.key === 'ArrowLeft') prevSlide();
        else if (e.key === 'Escape') togglePresentationMode();
      }});
    }}

    // Theme Switcher
    function toggleTheme() {{
      const html = document.documentElement;
      const icon = document.getElementById('themeIcon');
      if (html.classList.contains('dark')) {{
        html.classList.remove('dark');
        html.classList.add('light');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
      }} else {{
        html.classList.remove('light');
        html.classList.add('dark');
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
      }}
      setTimeout(reinitAllCharts, 150);
    }}

    // Helpers
    function formatCurrency(val) {{
      if (val >= 1e9) return (val / 1e9).toFixed(2) + 'B';
      if (val >= 1e6) return (val / 1e6).toFixed(2) + 'M';
      if (val >= 1e3) return (val / 1e3).toFixed(1) + 'K';
      return Number(val).toLocaleString();
    }}

    // Populate Whales Table
    function populateWhaleTable() {{
      const tbody = document.getElementById('whalesTableBody');
      tbody.innerHTML = '';
      DATA.whales.top_20.forEach((w, idx) => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/40 transition";
        
        let archetype = "Burst Whale";
        let badgeClass = "bg-amber-500/10 text-amber-400 border border-amber-500/20";
        if (w.avg_session_hours < 0.05) {{
          archetype = "Lightning / Bot";
          badgeClass = "bg-rose-500/10 text-rose-400 border border-rose-500/20";
        }} else if (w.avg_session_hours > 0.4) {{
          archetype = "Sustained Grinder";
          badgeClass = "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20";
        }}

        tr.innerHTML = `
          <td class="py-3 px-3 text-slate-400 font-bold">#${{idx + 1}}</td>
          <td class="py-3 px-3 text-white font-semibold flex items-center gap-2">
            <i class="fa-solid fa-crown text-amber-400 text-[10px]"></i>
            <code>${{w.player_id}}</code>
          </td>
          <td class="py-3 px-3 text-slate-300 font-sans">
            <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] bg-slate-800 border border-slate-700">
              ${{w.country === 'Indonesia' ? '🇮🇩 IDR' : '🇻🇳 VND'}}
            </span>
          </td>
          <td class="py-3 px-3 text-right text-amber-400 font-bold">${{w.total_debit.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-slate-300">${{w.total_bets.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-slate-300">${{w.avg_bet.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-cyan-300 font-bold">${{w.avg_session_hours}}h</td>
          <td class="py-3 px-3 text-center">
            <span class="text-[10px] px-2 py-0.5 rounded-full font-sans font-semibold ${{badgeClass}}">
              ${{archetype}}
            </span>
          </td>
          <td class="py-3 px-3 text-center">
            <button onclick="openPlayerDossierById('${{w.player_id}}', 'whales')" class="px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/25 text-amber-400 text-[10px] font-bold border border-amber-500/30 transition flex items-center gap-1 mx-auto" title="Open Individual Player Dossier">
              <i class="fa-solid fa-user-secret"></i> Open
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // Filter Whales Table
    function filterWhaleTable() {{
      const query = document.getElementById('whaleSearchInput').value.toLowerCase();
      document.querySelectorAll('#whalesTableBody tr').forEach(row => {{
        const txt = row.textContent.toLowerCase();
        row.style.display = txt.includes(query) ? '' : 'none';
      }});
    }}

    // Populate Chasers Table
    function populateChaserTable() {{
      const tbody = document.getElementById('chasersTableBody');
      tbody.innerHTML = '';
      DATA.chasers.top_extreme.forEach(c => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/40 transition";
        const isNetLoss = c.total_winlose < 0;
        tr.innerHTML = `
          <td class="py-3 px-3 text-white font-semibold flex items-center gap-1.5">
            <i class="fa-solid fa-triangle-exclamation text-rose-400 text-[10px]"></i>
            <code>${{c.player_id}}</code>
          </td>
          <td class="py-3 px-3 text-right text-rose-400 font-bold">${{c.spike_multiplier.toLocaleString()}}x</td>
          <td class="py-3 px-3 text-center text-amber-300 font-bold">${{c.max_consecutive_losses}}</td>
          <td class="py-3 px-3 text-right text-slate-300">${{c.avg_loss_debit.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-rose-300 font-bold">${{c.spike_debit.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-slate-400">${{c.total_bets.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-slate-300">${{c.total_debit.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right ${{isNetLoss ? 'text-rose-400' : 'text-emerald-400'}} font-bold">
            ${{c.total_winlose.toLocaleString()}}
          </td>
          <td class="py-3 px-3 text-center font-sans">
            <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold ${{isNetLoss ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}}">
              ${{isNetLoss ? 'Net Loser' : 'Net Winner'}}
            </span>
          </td>
          <td class="py-3 px-3 text-center">
            <button onclick="openPlayerDossierById('${{c.player_id}}', 'chasers')" class="px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/25 text-amber-400 text-[10px] font-bold border border-amber-500/30 transition flex items-center gap-1 mx-auto" title="Open Individual Player Dossier">
              <i class="fa-solid fa-user-secret"></i> Open
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // =========================================================================
    // GROUP DOSSIER POPULATION
    // =========================================================================

    // Populate Whale Group Dossier
    function populateWhaleGroupDossier() {{
      const whales = DATA.whales.top_20;
      const countryDist = DATA.whales.country_distribution;

      // KPI Values
      document.getElementById('whaleGroupTotalDebit').textContent = formatCurrency(DATA.whales.total_debit);
      document.getElementById('whaleGroupTotalBets').textContent = DATA.whales.total_bets.toLocaleString();
      
      // Calculate average session
      const avgSession = whales.reduce((sum, w) => sum + w.avg_session_hours, 0) / whales.length;
      document.getElementById('whaleGroupAvgSession').textContent = avgSession.toFixed(2) + 'h';
      
      document.getElementById('whaleGroupCountries').textContent = countryDist.length;
      
      // Concentration: whale debit / total casino debit
      const totalCasinoDebit = DATA.metadata.total_debit_all_operators;
      const whaleConcentration = (DATA.whales.total_debit / totalCasinoDebit * 100).toFixed(1);
      document.getElementById('whaleGroupConcentration').textContent = whaleConcentration + '%';

      // Geographic Breakdown
      const geoContainer = document.getElementById('whaleGroupGeoBreakdown');
      geoContainer.innerHTML = '';
      countryDist.forEach(c => {{
        const pct = (c.debit / DATA.whales.total_debit * 100).toFixed(1);
        const FLAG_MAP = {'Indonesia':'🇮🇩','Vietnam':'🇻🇳','China':'🇨🇳','Bangladesh':'🇧🇩','Thailand':'🇹🇭','Malaysia':'🇲🇾','India':'🇮🇳','Myanmar':'🇲🇲','Philippines':'🇵🇭','Cambodia':'🇰🇭','Laos':'🇱🇦','Singapore':'🇸🇬','South Korea':'🇰🇷','Japan':'🇯🇵','USA':'🇺🇸','Hong Kong':'🇭🇰','Taiwan':'🇹🇼','Nepal':'🇳🇵','Turkey':'🇹🇷','Crypto':'₿','Unknown':'🌐'};
        const flag = FLAG_MAP[c.country] || '🌐';
        const div = document.createElement('div');
        div.className = 'p-2 rounded-lg bg-slate-800/50 border border-slate-700/50 flex items-center justify-between';
        div.innerHTML = `
          <div class="flex items-center gap-2 text-xs">
            <span class="text-base">${{flag}}</span>
            <span class="font-semibold text-white">${{c.country}}</span>
            <span class="text-slate-400">({{c.count}} whales)</span>
          </div>
          <div class="text-right">
            <div class="font-bold text-slate-200 font-mono">${{formatCurrency(c.debit)}}</div>
            <div class="text-[10px] text-amber-400 font-semibold">${{pct}}%</div>
          </div>
        `;
        geoContainer.appendChild(div);
      }});

      // Behavioral Archetypes
      const archetypeContainer = document.getElementById('whaleGroupArchetypes');
      let lightning = 0, burst = 0, grinder = 0;
      whales.forEach(w => {{
        if (w.avg_session_hours < 0.05) lightning++;
        else if (w.avg_session_hours > 0.4) grinder++;
        else burst++;
      }});
      const archetypes = [
        {{ label: 'Lightning / Bot', count: lightning, color: 'rose', icon: 'fa-bolt' }},
        {{ label: 'Burst Whale', count: burst, color: 'amber', icon: 'fa-gem' }},
        {{ label: 'Sustained Grinder', count: grinder, color: 'cyan', icon: 'fa-hourglass-half' }}
      ];
      archetypeContainer.innerHTML = '';
      archetypes.forEach(a => {{
        if (a.count > 0) {{
          const div = document.createElement('div');
          div.className = 'p-2 rounded-lg bg-slate-800/50 border border-slate-700/50 flex items-center justify-between';
          div.innerHTML = `
            <div class="flex items-center gap-2 text-xs">
              <i class="fa-solid ${{a.icon}} text-${{a.color}}-400"></i>
              <span class="font-semibold text-white">${{a.label}}</span>
            </div>
            <div class="text-right">
              <div class="font-bold text-${{a.color}}-400 font-mono">${{a.count}}</div>
              <div class="text-[10px] text-slate-400">${{((a.count/whales.length)*100).toFixed(0)}}% of group</div>
            </div>
          `;
          archetypeContainer.appendChild(div);
        }}
      }});

      // Key Insights
      const insightsContainer = document.getElementById('whaleGroupInsights');
      const topWhale = whales[0];
      const chinaShare = countryDist.find(c => c.country === 'China');
      const indonesiaShare = countryDist.find(c => c.country === 'Indonesia');
      const vietnamShare = countryDist.find(c => c.country === 'Vietnam');
      
const topCountry = countryDist[0];
            const topPct = ((topCountry.debit / DATA.whales.total_debit) * 100).toFixed(1);
            const top2 = countryDist.slice(0, 2);
            const top2Pct = ((top2.reduce((s, c) => s + c.debit, 0) / DATA.whales.total_debit) * 100).toFixed(1);
            const insights = [
              `<strong>Dominant Profile:</strong> ${{lightning}}/${{whales.length}} whales (${{((lightning/whales.length)*100).toFixed(0)}}%) are "Lightning" archetypes with sub-3-minute avg sessions — likely automated/high-frequency execution.`,
              `<strong>Geographic Concentration:</strong> ${{topCountry.country}} dominates with ${{topCountry.count}}/${{whales.length}} whales (${{topPct}}% of whale debit). The top ${{top2.length}} countries control ${{top2Pct}}% of group turnover.`,
              `<strong>Top Individual:</strong> <code>${{topWhale.player_id}}</code> (${{topWhale.country}}) — ${{formatCurrency(topWhale.total_debit)}} across ${{topWhale.total_bets}} bets (avg session: ${{topWhale.avg_session_hours}}h).`,
              `<strong>Volume Velocity:</strong> Group averages ${{(DATA.whales.total_debit / DATA.whales.total_bets).toFixed(0)}} PHP per bet. Whales execute ${{(DATA.whales.total_bets / whales.length).toFixed(0)}} bets each on average.`,
              `<strong>Session Brevity:</strong> ${{((lightning/whales.length)*100).toFixed(0)}}% of whales complete sessions in under 3 minutes, indicating burst-betting patterns rather than recreational play.`
            ];
      insightsContainer.innerHTML = insights.map(i => `<li>${{i}}</li>`).join('');
    }}

    // Populate Chaser Group Dossier
    function populateChaserGroupDossier() {{
      const chasers = DATA.chasers;
      const topExtreme = DATA.chasers.top_extreme;
      const l3Entry = chasers.loss_streak_distribution.find(d => d.streak === 3);
      const l3Pct = l3Entry ? l3Entry.pct : 0;
      const l3Count = l3Entry ? l3Entry.players : 0;

      // KPI Values
      document.getElementById('chaserGroupTotalDebit').textContent = formatCurrency(chasers.total_debit);
      document.getElementById('chaserGroupTotalCount').textContent = chasers.total_count.toLocaleString();
      document.getElementById('chaserGroupNetLosers').textContent = chasers.net_loser_pct.toFixed(1) + '%';
      document.getElementById('chaserGroupTotalHarm').textContent = formatCurrency(chasers.total_winlose);
      document.getElementById('chaserGroupMaxSpike').textContent = topExtreme.length > 0 ? topExtreme[0].spike_multiplier.toFixed(0) + 'x' : 'N/A';

// Static descriptive labels that hardcode the stale 11,978 count
      const navFlagged = document.getElementById('navChaserFlagged');
      if (navFlagged) navFlagged.textContent = chasers.total_count.toLocaleString() + ' Flagged';
      const chaserGroupProfiles = document.getElementById('chaserGroupProfiles');
      if (chaserGroupProfiles) chaserGroupProfiles.textContent = chasers.total_count.toLocaleString() + ' Profiles';
      const execTilt = document.getElementById('execTiltText');
      if (execTilt) {{
        const spikeTxt = topExtreme.length > 0 ? topExtreme[0].spike_multiplier.toFixed(0) + 'x' : 'N/A';
        execTilt.innerHTML =
          `<strong>${{chasers.total_count.toLocaleString()}}</strong> chasers detected. <strong>${{chasers.net_loser_pct.toFixed(1)}}% end as net losers</strong>. Chasing begins decisively at <strong>3 consecutive losses</strong> (${{l3Pct.toFixed(1)}}% trigger rate). Spikes reach up to <strong>${{spikeTxt}}</strong> loss-bet debit.`;
      }}
      const area2Flagged = document.getElementById('area2Flagged');
      if (area2Flagged) area2Flagged.textContent = chasers.total_count.toLocaleString();
      const chaserGroupSubtitle = document.getElementById('chaserGroupSubtitle');
      if (chaserGroupSubtitle) chaserGroupSubtitle.textContent = chasers.total_count.toLocaleString();
      const kpiExtremeSpike = document.getElementById('kpiExtremeSpike');
      if (kpiExtremeSpike) kpiExtremeSpike.textContent = (topExtreme.length > 0 ? topExtreme[0].spike_multiplier.toFixed(1) : 'N/A') + 'x Spike';
      const kpiNetLoserPct = document.getElementById('kpiNetLoserPct');
      if (kpiNetLoserPct) kpiNetLoserPct.textContent = chasers.net_loser_pct.toFixed(2) + '% Losers';
      const kpiNetLoserCount = document.getElementById('kpiNetLoserCount');
      if (kpiNetLoserCount) kpiNetLoserCount.textContent = chasers.net_losers.toLocaleString() + ' players suffered net loss';
      const kpiL3Pct = document.getElementById('kpiL3Pct');
      if (kpiL3Pct) kpiL3Pct.textContent = l3Pct.toFixed(1) + '% of chasers tilt at streak #3';
      const kpiChaserHarm = document.getElementById('kpiChaserHarm');
      if (kpiChaserHarm) kpiChaserHarm.textContent = formatCurrency(chasers.total_winlose);
      const pillarL3Pct = document.getElementById('pillarL3Pct');
      if (pillarL3Pct) pillarL3Pct.textContent = l3Pct.toFixed(1) + '%';

      // Risk Tier Distribution
      const tierContainer = document.getElementById('chaserGroupRiskTiers');
      tierContainer.innerHTML = '';
      const tierOrder = ['Extreme (>=1000x)', 'Critical (100x-999x)', 'High (20x-99x)', 'Moderate (5x-19x)', 'Low (<5x)'];
      const tierColors = {{ 'Extreme (>=1000x)': 'rose', 'Critical (100x-999x)': 'amber', 'High (20x-99x)': 'orange', 'Moderate (5x-19x)': 'yellow', 'Low (<5x)': 'green' }};
      chasers.risk_tiers.forEach(tier => {{
        const tierLabel = tier.tier;
        const pct = (tier.count / chasers.total_count * 100).toFixed(1);
        const div = document.createElement('div');
        div.className = 'p-2 rounded-lg bg-slate-800/50 border border-slate-700/50 flex items-center justify-between';
        div.innerHTML = `
          <div class="flex items-center gap-2 text-xs">
            <span class="w-2 h-2 rounded-full bg-${{tierColors[tierLabel]}}-500"></span>
            <span class="font-semibold text-white">${{tierLabel}}</span>
          </div>
          <div class="text-right">
            <div class="font-bold text-${{tierColors[tierLabel]}}-400 font-mono">${{tier.count.toLocaleString()}}</div>
            <div class="text-[10px] text-slate-400">${{pct}}% of chasers</div>
          </div>
        `;
        tierContainer.appendChild(div);
      }});

      // Tilt Threshold Analysis
      const tiltContainer = document.getElementById('chaserGroupTiltThresholds');
      tiltContainer.innerHTML = '';
      const keyStreaks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      keyStreaks.forEach(streak => {{
        const data = chasers.loss_streak_distribution.find(d => d.streak === streak);
        if (data && data.players > 0) {{
          const div = document.createElement('div');
          div.className = 'p-2 rounded-lg bg-slate-800/50 border border-slate-700/50 flex items-center justify-between';
          const isPeak = streak === 3;
          div.innerHTML = `
            <div class="flex items-center gap-2 text-xs">
              <span class="font-mono text-${{isPeak ? 'rose' : 'slate'}}-400 font-bold">L${{streak}}</span>
              <span class="font-semibold text-${{isPeak ? 'rose' : 'white'}}-300">${{streak}} Consecutive Losses</span>
              ${{isPeak ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">PEAK</span>' : ''}}
            </div>
            <div class="text-right">
              <div class="font-bold text-${{isPeak ? 'rose' : 'slate'}}-300 font-mono">${{data.players.toLocaleString()}}</div>
              <div class="text-[10px] text-slate-400">${{data.pct.toFixed(1)}}% of chasers</div>
            </div>
          `;
          tiltContainer.appendChild(div);
        }}
      }});

      // Key Risk Insights
      const insightsContainer = document.getElementById('chaserGroupInsights');
      const extremeCount = chasers.risk_tiers.find(t => t.tier === 'Extreme (>=1000x)')?.count || 0;
      const criticalCount = chasers.risk_tiers.find(t => t.tier === 'Critical (100x-999x)')?.count || 0;
      
      const insights = [
        `<strong>Loss-Streak Tipping Point:</strong> <span class="text-rose-400 font-bold">${{l3Count}} chasers (${{l3Pct.toFixed(1)}}%)</span> initiate panic spikes at exactly <strong>3 consecutive losses</strong> — the decisive psychological tilt threshold.`,
        `<strong>Chasing Is Financially Destructive:</strong> <span class="text-rose-400 font-bold">${{chasers.net_loser_pct.toFixed(1)}}%</span> of all chasers end in net drawdown (${{formatCurrency(Math.abs(chasers.total_winlose))}} cumulative loss). Bet escalation deepens losses rather than recovering them.`,
        `<strong>Extreme Risk Cohort:</strong> ${{extremeCount}} players in "Extreme" tier (≥1,000x spike) and ${{criticalCount}} in "Critical" tier (100-999x). Top spike: <code>${{topExtreme[0]?.player_id || 'N/A'}}</code> at ${{topExtreme[0]?.spike_multiplier?.toFixed(0) || 'N/A'}}x.`,
        `<strong>Streak Escalation:</strong> Streaks 3-5 capture ${{((chasers.loss_streak_distribution.filter(d => d.streak >= 3 && d.streak <= 5).reduce((sum, d) => sum + d.players, 0)) / chasers.total_count * 100).toFixed(1)}}% of all tilt events. Interventions at L3 would address the majority.`,
        `<strong>Net Winner Anomaly:</strong> Only ${{chasers.net_winner_pct.toFixed(1)}}% of chasers (${{chasers.net_winners}} players) achieve net positive P&L — likely luck-driven outliers, not sustainable strategy.`
      ];
      insightsContainer.innerHTML = insights.map(i => `<li>${{i}}</li>`).join('');
    }}

    // Populate Operators Table
    function populateOperatorTable() {{
      const tbody = document.getElementById('operatorsTableBody');
      tbody.innerHTML = '';
      DATA.operators.top_50.forEach((op, idx) => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/40 transition";
        const isPositiveGGR = op.ggr > 0;
        tr.innerHTML = `
          <td class="py-3 px-3 text-white font-semibold flex items-center gap-1.5">
            <span class="text-slate-500 text-[10px] font-mono">#${{idx+1}}</span>
            <code>${{op.operator}}</code>
          </td>
          <td class="py-3 px-3 text-slate-300 font-sans">${{op.countries}}</td>
          <td class="py-3 px-3 text-right text-emerald-400 font-bold">${{op.total_debit.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right ${{isPositiveGGR ? 'text-emerald-400' : 'text-rose-400'}} font-bold">
            ${{op.ggr.toLocaleString()}}
          </td>
          <td class="py-3 px-3 text-right font-bold ${{op.operator_hold_margin >= 3 ? 'text-emerald-300' : 'text-slate-300'}}">
            ${{op.operator_hold_margin}}%
          </td>
          <td class="py-3 px-3 text-right text-slate-400 font-mono">${{op.operator_roi}}%</td>
          <td class="py-3 px-3 text-right text-slate-300">${{op.total_bets.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-cyan-300 font-bold">${{op.unique_players.toLocaleString()}}</td>
          <td class="py-3 px-3 text-right text-slate-400">${{op.avg_bet.toLocaleString()}}</td>
          <td class="py-3 px-3 text-center">
            <button onclick="openOperatorDossierById('${{op.operator}}')" class="px-2.5 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/25 text-cyan-400 text-[10px] font-bold border border-cyan-500/30 transition flex items-center gap-1 mx-auto" title="Open Individual Operator Dossier">
              <i class="fa-solid fa-building-columns"></i> Open
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // Filter Operator Table
    function filterOperatorTable() {{
      const query = document.getElementById('operatorSearchInput').value.toLowerCase();
      document.querySelectorAll('#operatorsTableBody tr').forEach(row => {{
        const txt = row.textContent.toLowerCase();
        row.style.display = txt.includes(query) ? '' : 'none';
      }});
    }}

    // CSV Exporter
    function exportTableToCSV(tableId, filename) {{
      let csv = [];
      const rows = document.querySelectorAll(`#${{tableId}} tr`);
      for (let i = 0; i < rows.length; i++) {{
        let row = [], cols = rows[i].querySelectorAll('td, th');
        for (let j = 0; j < cols.length; j++) {{
          let data = cols[j].innerText.replace(/(\\r\\n|\\n|\\r)/gm, '').replace(/(\\s\\s+)/gm, ' ');
          data = data.replace(/"/g, '""');
          row.push('"' + data + '"');
        }}
        csv.push(row.join(','));
      }}
      const csvFile = new Blob([csv.join('\\n')], {{ type: 'text/csv' }});
      const downloadLink = document.createElement('a');
      downloadLink.download = filename;
      downloadLink.href = window.URL.createObjectURL(csvFile);
      downloadLink.style.display = 'none';
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    }}

    // =========================================================================
    // ECHARTS INITIALIZATION
    // =========================================================================

    function isDark() {{
      return document.documentElement.classList.contains('dark');
    }}

    function getChartTheme() {{
      const dark = isDark();
      return {{
        bg: 'transparent',
        textColor: dark ? '#94a3b8' : '#475569',
        titleColor: dark ? '#f8fafc' : '#0f172a',
        gridBorder: dark ? '#1e293b' : '#e2e8f0',
        tooltipBg: dark ? '#0f172a' : '#ffffff',
        tooltipBorder: dark ? '#334155' : '#cbd5e1',
        tooltipText: dark ? '#ffffff' : '#0f172a'
      }};
    }}

    function initCharts() {{
      initOverviewTrafficChart();
      initOverviewPillarChart();
      initWhaleScatterChart();
      initWhaleGeoChart();
      initChaserTiersChart();
      initChaserTiltChart();
      initChaserOutcomePie();
      initTrafficCurveChart();
      initTrafficHeatmapChart();
      initTrafficDensityChart();
      initOperatorRoiChart();
      initOperatorBubbleChart();
    }}

    function reinitAllCharts() {{
      Object.values(chartInstances).forEach(c => c && c.dispose());
      chartInstances = {{}};
      initCharts();
      if (isPresentationMode) renderSlideCharts();
    }}

    function resizeAllCharts() {{
      Object.values(chartInstances).forEach(c => c && c.resize());
    }}
    window.addEventListener('resize', resizeAllCharts);

    // 1. Overview Traffic
    function initOverviewTrafficChart() {{
      const dom = document.getElementById('overviewTrafficChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['overviewTraffic'] = chart;

      const hours = DATA.traffic.hourly_curve.map(d => d.hour);
      const bets = DATA.traffic.hourly_curve.map(d => d.bets);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'axis',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => `<strong>${{params[0].name}}</strong>: ${{params[0].value.toLocaleString()}} Bets`
        }},
        grid: {{ top: 20, right: 20, bottom: 30, left: 60 }},
        xAxis: {{
          type: 'category',
          data: hours,
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10 }}
        }},
        yAxis: {{
          type: 'value',
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => (v/1000).toFixed(0) + 'K' }}
        }},
        series: [{{
          data: bets,
          type: 'line',
          smooth: true,
          lineStyle: {{ color: '#6366f1', width: 3 }},
          areaStyle: {{
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {{ offset: 0, color: 'rgba(99, 102, 241, 0.45)' }},
              {{ offset: 1, color: 'rgba(99, 102, 241, 0.01)' }}
            ])
          }},
          markPoint: {{
            data: [
              {{ type: 'max', name: 'Peak', itemStyle: {{ color: '#f43f5e' }} }}
            ]
          }}
        }}]
      }});
    }}

    // 2. Overview Pillar Chart
    function initOverviewPillarChart() {{
      const dom = document.getElementById('overviewPillarChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['overviewPillar'] = chart;

      const nonWhaleDebit = DATA.metadata.total_debit_all_operators - DATA.whales.total_debit;
      const whalePct = ((DATA.whales.total_debit / DATA.metadata.total_debit_all_operators) * 100).toFixed(1);
      const otherPct = (100 - parseFloat(whalePct)).toFixed(1);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'item',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => `<strong>${{params.name}}</strong>: ${{formatCurrency(params.value)}} (${{params.percent}}%)`
        }},
        legend: {{
          bottom: 0,
          textStyle: {{ color: t.textColor, fontSize: 11 }}
        }},
        series: [{{
          name: 'Revenue Concentration',
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          itemStyle: {{ borderRadius: 8, borderColor: isDark() ? '#111726' : '#ffffff', borderWidth: 2 }},
          label: {{ show: false }},
          emphasis: {{ label: {{ show: true, fontSize: 12, fontWeight: 'bold', color: t.titleColor }} }},
          data: [
            {{ value: DATA.whales.total_debit, name: 'Top 20 Whales (' + whalePct + '%)', itemStyle: {{ color: '#f59e0b' }} }},
            {{ value: nonWhaleDebit, name: 'Other Players (' + otherPct + '%)', itemStyle: {{ color: '#3b82f6' }} }}
          ]
        }}]
      }});
    }}

    // 3. Whale Scatter Chart
    function initWhaleScatterChart() {{
      const dom = document.getElementById('whaleScatterChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['whaleScatter'] = chart;

      const scatterData = DATA.whales.top_20.map(w => [
        w.avg_session_hours,
        w.total_debit,
        w.total_bets,
        w.player_id,
        w.country,
        w.avg_bet
      ]);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'item',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => {{
            const d = params.value;
            return `
              <div class="font-sans">
                <div class="font-bold text-indigo-400 mb-1">${{d[3]}} (${{d[4]}})</div>
                <div>Avg Session: <strong>${{d[0]}} Hours</strong></div>
                <div>Total Debit: <strong>${{Number(d[1]).toLocaleString()}}</strong></div>
                <div>Total Bets: <strong>${{Number(d[2]).toLocaleString()}}</strong></div>
                <div>Avg Bet Size: <strong>${{Number(d[5]).toLocaleString()}}</strong></div>
              </div>
            `;
          }}
        }},
        grid: {{ top: 30, right: 30, bottom: 50, left: 80 }},
        xAxis: {{
          name: 'Avg Session (Hours)',
          nameLocation: 'middle',
          nameGap: 30,
          nameTextStyle: {{ color: t.textColor, fontSize: 11 }},
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10 }},
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }}
        }},
        yAxis: {{
          name: isScatterLog ? 'Total Debit (Log Scale)' : 'Total Debit',
          type: isScatterLog ? 'log' : 'value',
          nameTextStyle: {{ color: t.textColor, fontSize: 11 }},
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => formatCurrency(v) }},
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }}
        }},
        series: [{{
          type: 'scatter',
          data: scatterData,
          symbolSize: data => Math.min(60, Math.max(16, Math.sqrt(data[2]) * 0.25)),
          itemStyle: {{
            color: p => p.value[4] === 'Indonesia' ? '#6366f1' : '#10b981',
            shadowBlur: 10,
            shadowColor: 'rgba(99, 102, 241, 0.4)'
          }}
        }}]
      }});
    }}

    function toggleScatterScale() {{
      isScatterLog = !isScatterLog;
      document.getElementById('scatterScaleBtn').textContent = isScatterLog ? 'Logarithmic' : 'Linear';
      initWhaleScatterChart();
    }}

    // 4. Whale Geo Donut Chart
    function initWhaleGeoChart() {{
      const dom = document.getElementById('whaleGeoChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['whaleGeo'] = chart;

      const pieData = DATA.whales.country_distribution.map(c => ({{
        name: c.country,
        value: c.debit
      }}));

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'item',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => `<strong>${{params.name}}</strong>: ${{formatCurrency(params.value)}} (${{params.percent}}%)`
        }},
        legend: {{ bottom: 0, textStyle: {{ color: t.textColor, fontSize: 11 }} }},
        series: [{{
          type: 'pie',
          radius: ['45%', '75%'],
          center: ['50%', '42%'],
          avoidLabelOverlap: false,
          itemStyle: {{ borderRadius: 8, borderColor: isDark() ? '#111726' : '#ffffff', borderWidth: 2 }},
          label: {{ show: false }},
          emphasis: {{ label: {{ show: true, fontSize: 12, fontWeight: 'bold' }} }},
          data: DATA.whales.country_distribution.map((c, i) => ({{
            value: c.debit,
            name: c.country,
            itemStyle: {{ color: ['#6366f1','#10b981','#f59e0b','#06b6d4','#ef4444','#8b5cf6','#ec4899'][i % 7] }}
          }}))
        }}]
      }});
    }}

    // 5. Chaser Tiers Chart
    function initChaserTiersChart() {{
      const dom = document.getElementById('chaserTiersChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['chaserTiers'] = chart;

      const tiers = DATA.chasers.risk_tiers;
      const labels = tiers.map(t => t.tier);
      const counts = tiers.map(t => t.count);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'axis',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }}
        }},
        grid: {{ top: 20, right: 30, bottom: 40, left: 140 }},
        xAxis: {{
          type: 'value',
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10 }}
        }},
        yAxis: {{
          type: 'category',
          data: labels,
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10 }}
        }},
        series: [{{
          type: 'bar',
          data: counts,
          itemStyle: {{
            color: params => {{
              const colors = ['#e11d48', '#f43f5e', '#f59e0b', '#3b82f6', '#64748b'];
              return colors[params.dataIndex] || '#6366f1';
            }},
            borderRadius: [0, 6, 6, 0]
          }},
          label: {{
            show: true,
            position: 'right',
            color: t.textColor,
            fontSize: 10,
            formatter: p => p.value.toLocaleString() + ' players'
          }}
        }}]
      }});
    }}

    // 6. Chaser Tilt Chart
    function initChaserTiltChart() {{
      const dom = document.getElementById('chaserTiltChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['chaserTilt'] = chart;

      // Only show streaks that actually trigger tilt (>= 3 consecutive losses).
      // Streaks 0-2 are players who lost rounds but never chained 3+ together,
      // so they are excluded from this chart.
      const dataSlice = DATA.chasers.loss_streak_distribution
        .filter(d => d.streak >= 3)
        .slice(0, 12);
      const streaks = dataSlice.map(d => `Streak ${{d.streak}}`);
      const players = dataSlice.map(d => d.players);

      // L3 = 3 consecutive losses is the tilt trigger threshold. After filtering
      // out streaks 0-2, L3 is now the first bar (index 0).
      const l3Idx = 0;
      const l3 = dataSlice[l3Idx];
      const l3Pct = l3 ? (l3.players / DATA.chasers.total_count * 100).toFixed(1) : 0;

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'axis',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => `<strong>${{params[0].name}}</strong>: ${{params[0].value.toLocaleString()}} players`
        }},
        grid: {{ top: 30, right: 20, bottom: 30, left: 50 }},
        xAxis: {{
          type: 'category',
          data: streaks,
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }},
          axisLabel: {{ color: t.textColor, fontSize: 9, rotate: 30 }}
        }},
        yAxis: {{
          type: 'value',
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10 }}
        }},
        series: [{{
          data: players,
          type: 'bar',
          itemStyle: {{ color: '#f43f5e', borderRadius: [6, 6, 0, 0] }},
          markPoint: {{
            data: [{{ name: 'Tilt Threshold', coord: [l3Idx, players[l3Idx]], value: `${{l3Pct}}% of chasers`, label: {{ show: true, color: '#fff', fontSize: 12, fontWeight: 'bold', backgroundColor: 'rgba(15, 23, 42, 0.92)', padding: [4, 8], borderRadius: 6, borderColor: '#f59e0b', borderWidth: 1.5 }} }}],
            itemStyle: {{ color: '#f59e0b', width: 2, height: 34 }}
          }}
        }}]
      }});
    }}

    // 7. Chaser Outcome Pie
    function initChaserOutcomePie() {{
      const dom = document.getElementById('chaserOutcomePie');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['chaserOutcome'] = chart;

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'item',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => `<strong>${{params.name}}</strong>: ${{params.value.toLocaleString()}} (${{params.percent}}%)`
        }},
        legend: {{ bottom: 0, textStyle: {{ color: t.textColor, fontSize: 10 }} }},
        series: [{{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '42%'],
          itemStyle: {{ borderRadius: 6, borderColor: isDark() ? '#111726' : '#ffffff', borderWidth: 2 }},
          label: {{ show: false }},
          emphasis: {{ label: {{ show: true, fontSize: 11, fontWeight: 'bold' }} }},
          data: [
            {{ value: DATA.chasers.net_losers, name: 'Net Losers (67.7%)', itemStyle: {{ color: '#f43f5e' }} }},
            {{ value: DATA.chasers.net_winners, name: 'Net Winners (32.2%)', itemStyle: {{ color: '#10b981' }} }}
          ]
        }}]
      }});
    }}

    // 8. Traffic Curve Chart
    function initTrafficCurveChart() {{
      const dom = document.getElementById('trafficCurveChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['trafficCurve'] = chart;

      const hours = DATA.traffic.hourly_curve.map(d => d.hour);
      const bets = DATA.traffic.hourly_curve.map(d => d.bets);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'axis',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }}
        }},
        grid: {{ top: 40, right: 30, bottom: 40, left: 70 }},
        xAxis: {{
          type: 'category',
          data: hours,
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10 }}
        }},
        yAxis: {{
          type: 'value',
          name: 'Bets / Hour',
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => (v/1000).toFixed(0) + 'K' }}
        }},
        series: [{{
          data: bets,
          type: 'line',
          smooth: true,
          lineStyle: {{ color: '#06b6d4', width: 3 }},
          areaStyle: {{
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {{ offset: 0, color: 'rgba(6, 182, 212, 0.5)' }},
              {{ offset: 1, color: 'rgba(6, 182, 212, 0.02)' }}
            ])
          }},
          markArea: {{
            itemStyle: {{ color: 'rgba(244, 63, 94, 0.08)' }},
            data: [
              [{{ xAxis: '17:00' }}, {{ xAxis: '21:00' }}]
            ]
          }},
          markLine: {{
            data: [
              {{ yAxis: 1000000, name: '1M Peak Threshold', lineStyle: {{ color: '#f43f5e', type: 'dashed' }} }}
            ]
          }}
        }}]
      }});
    }}

    // 9. Traffic Heatmap
    function initTrafficHeatmapChart() {{
      const dom = document.getElementById('trafficHeatmapChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['trafficHeatmap'] = chart;

      const countries = DATA.traffic.heatmap.countries;
      const hours = DATA.traffic.heatmap.hours;
      const cells = DATA.traffic.heatmap.cells;

      // Color-scale value. Absolute bet counts are heavily skewed (China = 12.8M of
      // 18.2M total; 90% of cells < 87K, max = 772K), so a linear scale buries
      // nearly every cell in the darkest band. Log10(bets+1) spreads the full
      // 7-color gradient meaningfully across the skew.
      const log10 = v => Math.log10(v + 1);
      let colorVals, heatmapMax;
      if (isHeatmapNormalized) {{
        colorVals = cells.map(c => c.intensity);
        heatmapMax = 1;
      }} else {{
        const bets = cells.map(c => c.bets);
        colorVals = bets.map(log10);
        heatmapMax = log10(Math.max(...bets));
      }}

      const heatmapVals = cells.map((c, i) => [
        c.hour_idx,
        c.country_idx,
        colorVals[i],
        c.bets
      ]);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          position: 'top',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 11 }},
          formatter: params => {{
            const h = hours[params.value[0]];
            const c = countries[params.value[1]];
            const bets = params.value[3].toLocaleString();
            const intensity = (params.value[2] / heatmapMax * 100).toFixed(1);
            return `<strong>${{c}}</strong> @ ${{h}}<br>Bets: <strong>${{bets}}</strong><br>Relative Intensity: <strong>${{intensity}}%</strong>`;
          }}
        }},
        grid: {{ top: 20, right: 30, bottom: 60, left: 110 }},
        xAxis: {{
          type: 'category',
          data: hours,
          splitArea: {{ show: true }},
          axisLabel: {{ color: t.textColor, fontSize: 9, rotate: 45 }},
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }}
        }},
        yAxis: {{
          type: 'category',
          data: countries,
          splitArea: {{ show: true }},
          axisLabel: {{ color: t.textColor, fontSize: 10 }},
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }}
        }},
        visualMap: {{
          min: 0,
          max: heatmapMax,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: 10,
          inRange: {{
            color: ['#0f172a', '#1e1b4b', '#4338ca', '#6366f1', '#ec4899', '#f43f5e', '#fbbf24']
          }},
          textStyle: {{ color: t.textColor, fontSize: 10 }}
        }},
        series: [{{
          name: 'Bet Volume',
          type: 'heatmap',
          data: heatmapVals,
          label: {{ show: false }},
          emphasis: {{
            itemStyle: {{ shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }}
          }}
        }}]
      }});
    }}

    function toggleHeatmapNormalize() {{
      isHeatmapNormalized = !isHeatmapNormalized;
      document.getElementById('heatmapModeLabel').textContent = isHeatmapNormalized ? 'Country Relative (Normalized)' : 'Absolute Bet Counts (Log Scale)';
      initTrafficHeatmapChart();
    }}

    // 10. Traffic Density Chart
    function initTrafficDensityChart() {{
      const dom = document.getElementById('trafficDensityChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['trafficDensity'] = chart;

      const densityData = DATA.traffic.country_density;
      const countries = densityData.map(d => d.country);
      const pcts = densityData.map(d => d.peak_percentage);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'axis',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => {{
            const item = densityData[params[0].dataIndex];
            return `<strong>${{item.country}}</strong><br>Peak Hour: <strong>${{item.peak_hour}}</strong><br>Peak Concentration: <strong>${{item.peak_percentage}}%</strong><br>Total Bets: ${{item.total_bets.toLocaleString()}}`;
          }}
        }},
        grid: {{ top: 20, right: 30, bottom: 40, left: 110 }},
        xAxis: {{
          type: 'value',
          name: '% in Single Peak Hour',
          nameTextStyle: {{ color: t.textColor, fontSize: 10 }},
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => v + '%' }}
        }},
        yAxis: {{
          type: 'category',
          data: countries,
          inverse: true,
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }},
          axisLabel: {{ color: t.textColor, fontSize: 9 }}
        }},
        series: [{{
          type: 'bar',
          data: pcts,
          itemStyle: {{
            color: p => p.value > 15 ? '#f43f5e' : (p.value > 8 ? '#f59e0b' : '#3b82f6'),
            borderRadius: [0, 6, 6, 0]
          }},
          label: {{
            show: true,
            position: 'right',
            color: t.textColor,
            fontSize: 9,
            formatter: p => p.value + '%'
          }}
        }}]
      }});
    }}

    // 11. Operator ROI / Margin Chart
    function initOperatorRoiChart() {{
      const dom = document.getElementById('operatorRoiChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['operatorRoi'] = chart;

      const ops = DATA.operators.roi_comparison.slice(0, 15);
      const names = ops.map(o => o.operator);
      const margins = ops.map(o => o.operator_hold_margin);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'axis',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => {{
            const op = ops[params[0].dataIndex];
            return `<strong>${{op.operator}}</strong> (${{op.countries}})<br>Net Hold Margin: <strong>${{op.operator_hold_margin}}%</strong><br>Raw RTP: <strong>${{op.operator_roi}}%</strong><br>Debit: ${{formatCurrency(op.total_debit)}}`;
          }}
        }},
        grid: {{ top: 20, right: 30, bottom: 40, left: 140 }},
        xAxis: {{
          type: 'value',
          name: 'House Hold Margin %',
          nameTextStyle: {{ color: t.textColor, fontSize: 10 }},
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => v + '%' }}
        }},
        yAxis: {{
          type: 'category',
          data: names,
          inverse: true,
          axisLine: {{ lineStyle: {{ color: t.gridBorder }} }},
          axisLabel: {{ color: t.textColor, fontSize: 9 }}
        }},
        series: [{{
          type: 'bar',
          data: margins,
          itemStyle: {{ color: '#10b981', borderRadius: [0, 6, 6, 0] }},
          label: {{
            show: true,
            position: 'right',
            color: t.textColor,
            fontSize: 9,
            formatter: p => p.value + '%'
          }}
        }}]
      }});
    }}

    // 12. Operator Bubble Chart (Volume vs Value)
    function initOperatorBubbleChart() {{
      const dom = document.getElementById('operatorBubbleChart');
      if (!dom) return;
      const t = getChartTheme();
      const chart = echarts.init(dom);
      chartInstances['operatorBubble'] = chart;

      const bubbleData = DATA.operators.top_50.map(o => [
        o.total_bets,
        o.total_debit,
        o.unique_players,
        o.operator,
        o.countries,
        o.operator_hold_margin
      ]);

      chart.setOption({{
        backgroundColor: t.bg,
        tooltip: {{
          trigger: 'item',
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          textStyle: {{ color: t.tooltipText, fontSize: 12 }},
          formatter: params => {{
            const d = params.value;
            return `
              <div class="font-sans">
                <div class="font-bold text-emerald-400 mb-1">${{d[3]}} (${{d[4]}})</div>
                <div>Total Bets: <strong>${{Number(d[0]).toLocaleString()}}</strong></div>
                <div>Total Debit: <strong>${{formatCurrency(d[1])}}</strong></div>
                <div>Unique Players: <strong>${{Number(d[2]).toLocaleString()}}</strong></div>
                <div>Hold Margin: <strong>${{d[5]}}%</strong></div>
              </div>
            `;
          }}
        }},
        grid: {{ top: 30, right: 30, bottom: 50, left: 70 }},
        xAxis: {{
          name: 'Total Bets',
          nameLocation: 'middle',
          nameGap: 30,
          nameTextStyle: {{ color: t.textColor, fontSize: 10 }},
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 9, formatter: v => (v/1000).toFixed(0) + 'K' }}
        }},
        yAxis: {{
          name: 'Total Turnover (Log Scale)',
          type: 'log',
          nameTextStyle: {{ color: t.textColor, fontSize: 10 }},
          splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }},
          axisLabel: {{ color: t.textColor, fontSize: 9, formatter: v => formatCurrency(v) }}
        }},
        series: [{{
          type: 'scatter',
          data: bubbleData,
          symbolSize: data => Math.min(65, Math.max(12, Math.sqrt(data[2]) * 1.2)),
          itemStyle: {{
            color: p => p.value[4].includes('Vietnam') ? '#10b981' : (p.value[4].includes('Indonesia') ? '#6366f1' : '#06b6d4'),
            shadowBlur: 10,
            shadowColor: 'rgba(16, 185, 129, 0.4)'
          }}
        }}]
      }});
    }}

    // =========================================================================
    // SLIDE DECK CHARTS
    // =========================================================================
    function renderSlideCharts() {{
      const t = getChartTheme();
      const chasers = DATA.chasers;

      // Slide 3 static text reflects live chaser totals
      const slideFlagged = document.getElementById('slideFlaggedChasers');
      if (slideFlagged) slideFlagged.textContent = `${{chasers.total_count.toLocaleString()}} (${{chasers.net_loser_pct.toFixed(1)}}% Net Loss)`;
      const slideChaserCountEl = document.getElementById('slideChaserCount');
      if (slideChaserCountEl) slideChaserCountEl.textContent = chasers.total_count.toLocaleString();
      const l3Slide = chasers.loss_streak_distribution.find(d => d.streak === 3);
      const slideL3PctEl = document.getElementById('slideL3Pct');
      if (slideL3PctEl) slideL3PctEl.textContent = l3Slide ? l3Slide.pct.toFixed(1) : '—';
      const slideNetLoserPctEl = document.getElementById('slideNetLoserPct');
      if (slideNetLoserPctEl) slideNetLoserPctEl.textContent = chasers.net_loser_pct.toFixed(1);

      // Slide 2: Whale Geo
      const s2 = document.getElementById('slideWhaleGeoChart');
      if (s2 && currentSlide === 2) {{
        const c2 = echarts.init(s2);
        chartInstances['slideWhaleGeo'] = c2;
        c2.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'item' }},
          legend: {{ bottom: 0, textStyle: {{ color: t.textColor }} }},
          series: [{{
            type: 'pie',
            radius: ['45%', '70%'],
            itemStyle: {{ borderRadius: 8, borderColor: isDark() ? '#111726' : '#fff', borderWidth: 2 }},
            data: DATA.whales.country_distribution.map((c, i) => ({{
            value: c.debit,
            name: c.country + ' (' + ((c.debit / DATA.whales.total_debit) * 100).toFixed(1) + '%)',
            itemStyle: {{ color: ['#6366f1','#10b981','#f59e0b','#06b6d4','#ef4444','#8b5cf6','#ec4899'][i % 7] }}
          }}))
          }}]
        }});
      }}

      // Slide 3: Chaser Tilt
      const s3 = document.getElementById('slideChaserTiltChart');
      if (s3 && currentSlide === 3) {{
        const c3 = echarts.init(s3);
        chartInstances['slideChaserTilt'] = c3;
        const slice = DATA.chasers.loss_streak_distribution
        .filter(d => d.streak >= 3)
        .slice(0, 8);
        c3.setOption({{
          backgroundColor: t.bg,
          grid: {{ top: 20, right: 20, bottom: 30, left: 40 }},
          xAxis: {{ type: 'category', data: slice.map(d => `L${{d.streak}}`), axisLabel: {{ color: t.textColor }} }},
          yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ color: t.gridBorder }} }}, axisLabel: {{ color: t.textColor }} }},
          series: [{{
            type: 'bar',
            data: slice.map(d => d.players),
            itemStyle: {{ color: '#f43f5e', borderRadius: [6, 6, 0, 0] }}
          }}]
        }});
      }}

      // Slide 4: Traffic
      const s4 = document.getElementById('slideTrafficChart');
      if (s4 && currentSlide === 4) {{
        const c4 = echarts.init(s4);
        chartInstances['slideTraffic'] = c4;
        c4.setOption({{
          backgroundColor: t.bg,
          grid: {{ top: 20, right: 20, bottom: 30, left: 50 }},
          xAxis: {{ type: 'category', data: DATA.traffic.hourly_curve.map(d => d.hour), axisLabel: {{ color: t.textColor }} }},
          yAxis: {{ type: 'value', axisLabel: {{ color: t.textColor, formatter: v => (v/1000).toFixed(0) + 'K' }} }},
          series: [{{
            data: DATA.traffic.hourly_curve.map(d => d.bets),
            type: 'line',
            smooth: true,
            lineStyle: {{ color: '#06b6d4', width: 3 }},
            areaStyle: {{ color: 'rgba(6, 182, 212, 0.3)' }}
          }}]
        }});
      }}

      // Slide 5: Operator Bubble
      const s5 = document.getElementById('slideOperatorBubbleChart');
      if (s5 && currentSlide === 5) {{
        const c5 = echarts.init(s5);
        chartInstances['slideOperatorBubble'] = c5;
        c5.setOption({{
          backgroundColor: t.bg,
          grid: {{ top: 20, right: 20, bottom: 40, left: 60 }},
          xAxis: {{ type: 'value', axisLabel: {{ color: t.textColor, formatter: v => (v/1000).toFixed(0) + 'K' }} }},
          yAxis: {{ type: 'log', axisLabel: {{ color: t.textColor, formatter: v => formatCurrency(v) }} }},
          series: [{{
            type: 'scatter',
            data: DATA.operators.top_50.slice(0, 20).map(o => [o.total_bets, o.total_debit, o.unique_players]),
            symbolSize: d => Math.min(45, Math.max(12, Math.sqrt(d[2]) * 1.1)),
            itemStyle: {{ color: '#10b981' }}
          }}]
        }});
      }}
    }}
{DOSSIER_JS}
  </script>
</body>
</html>'''

out_path_1 = Path(WORKSPACE / "output" / "dashboards" / "bi_dashboard.html")
out_path_2 = Path(WORKSPACE / "output" / "dashboards" / "bi_dashboard.html")

with open(out_path_1, "w", encoding="utf-8") as f:
    f.write(html_template)
with open(out_path_2, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Generated {out_path_1} ({len(html_template):,} chars)")
print(f"Generated {out_path_2} ({len(html_template):,} chars)")
