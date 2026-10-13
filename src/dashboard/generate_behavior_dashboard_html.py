import json
from pathlib import Path

REPORT_DIR = Path(r"C:\Users\IT-40126\Documents\August 2026-20261008T011759Z-1-001\August 2026\output")
FOLDER = REPORT_DIR.parent
DATA_FILE = REPORT_DIR / "player_behavior_data.json"

def build_dashboard():
    if not DATA_FILE.exists():
        print(f"Data file {DATA_FILE} not found yet!")
        return False
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    json_str = json.dumps(master_data)

    html_template = f'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Player Behavioral Intelligence Console | Oriental Gaming Title</title>
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
      min-height: 380px;
      width: 100%;
    }}
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
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/30">
            <i class="fa-solid fa-gamepad text-lg"></i>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                PLAYER BEHAVIORAL INTELLIGENCE <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-semibold tracking-wider">TELEMETRY</span>
              </h1>
              <span class="text-xs text-emerald-400 flex items-center gap-1 font-mono">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> LIVE AUDIT
              </span>
            </div>
            <p class="text-xs text-slate-400">Granular Behavioral Forensics: Credit & Win Timing, Betting Velocity, Game Ecosystem & Balance Correlations</p>
          </div>
        </div>

        <!-- Global Header Stats Pill -->
        <div class="hidden xl:flex items-center gap-6 px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Analyzed Wagers</span>
            <span class="font-bold text-cyan-400 font-mono">3,000,000+</span>
          </div>
          <div class="w-px h-6 bg-slate-800"></div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Mobile Share</span>
            <span class="font-bold text-indigo-400 font-mono">84.4%</span>
          </div>
          <div class="w-px h-6 bg-slate-800"></div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Fast Wager Rate</span>
            <span class="font-bold text-amber-400 font-mono">69.6% (&lt;30s)</span>
          </div>
          <div class="w-px h-6 bg-slate-800"></div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Top Game</span>
            <span class="font-bold text-emerald-400 font-mono">Baccarat (42.3%)</span>
          </div>
        </div>

        <!-- Mode & Utility Switchers -->
        <div class="flex items-center gap-2">
          <a href="bi_dashboard.html" class="px-3.5 py-2 rounded-lg bg-indigo-950/60 hover:bg-indigo-900 text-indigo-300 text-xs font-semibold flex items-center gap-2 border border-indigo-700/50 transition" title="Back to Main BI Dashboard">
            <i class="fa-solid fa-arrow-left"></i>
            <span>Executive Console</span>
          </a>
          <a href="game_probability_dashboard.html" class="px-3.5 py-2 rounded-lg bg-emerald-950/60 hover:bg-emerald-900 text-emerald-300 text-xs font-semibold flex items-center gap-2 border border-emerald-700/50 transition" title="Open Game Probability & House-Edge Dashboard">
            <i class="fa-solid fa-dice text-emerald-400"></i>
            <span>Probability &amp; HE</span>
          </a>
          <button id="viewToggleBtn" onclick="togglePresentationMode()" class="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition">
            <i class="fa-solid fa-person-chalkboard text-cyan-400"></i>
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

      <!-- NAVIGATION TABS -->
      <div id="dashboardNav" class="max-w-7xl mx-auto mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between overflow-x-auto gap-2">
        <div class="flex items-center gap-2">
          <button onclick="switchTab('timing')" class="nav-tab active px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-clock text-cyan-400"></i> 1. Credit & Win Timing
          </button>
          <button onclick="switchTab('games')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-dice text-emerald-400"></i> 2. Game Selection
          </button>
          <button onclick="switchTab('behavior')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-arrow-trend-up text-amber-400"></i> 3. Betting Behavior
          </button>
          <button onclick="switchTab('frequency')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-bolt text-rose-400"></i> 4. Betting Frequency
          </button>
          <button onclick="switchTab('correlation')" class="nav-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition flex items-center gap-2">
            <i class="fa-solid fa-scale-balanced text-purple-400"></i> 5. Balance & Bet Correlation
          </button>
        </div>
        <div class="text-[11px] text-slate-400 font-mono hidden md:block">
          Telemetry Audit: 27 Raw Exports (August 2026)
        </div>
      </div>
    </header>

    <!-- MAIN BODY CONTENT -->
    <main class="flex-1 max-w-7xl mx-auto w-full p-6">

      <!-- ========================================================================= -->
      <!-- TAB 1: CREDIT & WIN TIMING -->
      <!-- ========================================================================= -->
      <section id="tab-timing" class="tab-pane space-y-6">
        <!-- Hero Strip -->
        <div class="glass-card rounded-2xl p-5 bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-900 border border-cyan-500/20">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold">
                <i class="fa-solid fa-clock"></i> Payout Latency & Hourly Win Dynamics
              </div>
              <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">When Do Players Credit & Win?</h2>
              <p class="text-xs text-slate-300">24-hour payout distribution, player win-rates, round turnaround times, and hourly RTP fluctuations</p>
            </div>
            <div class="text-right font-mono text-xs text-slate-400">
              Avg Round Turnaround: <strong class="text-emerald-400 text-sm">~8.2 Seconds</strong> (Debit to Credit)
            </div>
          </div>
        </div>

        <!-- Timing KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Average Win Rate</span>
            <div class="text-2xl font-extrabold text-emerald-400 font-mono mt-1">36.2%</div>
            <span class="text-[11px] text-slate-400">36.2% Wins, 54.1% Losses, 9.7% Pushes/Ties</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Peak Credit (Payout) Hour</span>
            <div class="text-2xl font-extrabold text-cyan-400 font-mono mt-1">20:00 UTC</div>
            <span class="text-[11px] text-slate-400">>3.40 Billion returned to players in 1h</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Highest RTP Time Window</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1">06:00 UTC (103.5%)</div>
            <span class="text-[11px] text-slate-400">Temporary variance swing favoring players</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Lowest RTP Time Window</span>
            <div class="text-2xl font-extrabold text-indigo-400 font-mono mt-1">00:00 UTC (94.3%)</div>
            <span class="text-[11px] text-slate-400">Highest casino hold margin window (5.7%)</span>
          </div>
        </div>

        <!-- Charts: 24h Win/Loss Volume & Hourly Payout vs Turnover -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-chart-line text-cyan-400"></i> 24-Hour Outcome Volume: Wins, Losses & Pushes
                </h3>
                <p class="text-xs text-slate-400">Round outcome breakdown across each hour of the operational day</p>
              </div>
            </div>
            <div id="timingOutcomeChart" class="chart-box"></div>
          </div>

          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-scale-unbalanced text-emerald-400"></i> Debit Turnover vs. Credit Payouts & RTP %
                </h3>
                <p class="text-xs text-slate-400">Total money wagered vs money credited back to player balances by hour</p>
              </div>
            </div>
            <div id="timingRtpChart" class="chart-box"></div>
          </div>
        </div>

        <!-- 24-Hour Credit & Win Matrix Table -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-table-list text-cyan-400"></i> Hourly Credit & Payout Audit Table
              </h3>
              <p class="text-xs text-slate-400">Comprehensive breakdown of wagering debit, credit returned, net GGR, and player win rate</p>
            </div>
            <button onclick="exportTableToCSV('timingTable', 'hourly_credit_win_audit.csv')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700">
              <i class="fa-solid fa-download text-cyan-400 mr-1"></i> Export CSV
            </button>
          </div>
          <div class="overflow-x-auto">
            <table id="timingTable" class="w-full text-left text-xs">
              <thead class="bg-slate-900/80 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                <tr>
                  <th class="py-3 px-3">Hour (UTC)</th>
                  <th class="py-3 px-3 text-right">Total Rounds</th>
                  <th class="py-3 px-3 text-right">Winning Rounds</th>
                  <th class="py-3 px-3 text-right">Win Rate %</th>
                  <th class="py-3 px-3 text-right">Total Debit</th>
                  <th class="py-3 px-3 text-right">Total Credit (Payout)</th>
                  <th class="py-3 px-3 text-right">Casino Net GGR</th>
                  <th class="py-3 px-3 text-right">Player RTP %</th>
                </tr>
              </thead>
              <tbody id="timingTableBody" class="divide-y divide-slate-800/60 font-mono">
                <!-- Dynamically Populated -->
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 2: WHICH GAMES THEY PLAY -->
      <!-- ========================================================================= -->
      <section id="tab-games" class="tab-pane hidden space-y-6">
        <div class="glass-card rounded-2xl p-5 bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/20">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
            <i class="fa-solid fa-dice"></i> Game Ecosystem & Preference Matrix
          </div>
          <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">Which Games Do Players Play?</h2>
          <p class="text-xs text-slate-300">Complete performance ranking across Baccarat, Dragon Tiger, Roulette, NiuNiu, and Mini-Games</p>
        </div>

        <!-- Game KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">The Core Duopoly</span>
            <div class="text-2xl font-extrabold text-emerald-400 font-mono mt-1">83.7% Share</div>
            <span class="text-[11px] text-slate-400">Baccarat (42.3%) + Dragon Tiger (41.4%)</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Highest Average Wager</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1">Baccarat ($37,182)</div>
            <span class="text-[11px] text-slate-400">Followed closely by Dragon Tiger ($35,242)</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Highest Player Win Rate</span>
            <div class="text-2xl font-extrabold text-cyan-400 font-mono mt-1">NiuNiu (49.2%)</div>
            <span class="text-[11px] text-slate-400">Bull Bull yields highest hit rate for players</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Highest Casino Hold Margin</span>
            <div class="text-2xl font-extrabold text-rose-400 font-mono mt-1">Roulette (5.33%)</div>
            <span class="text-[11px] text-slate-400">Multi-number bet spreads yield top operator hold</span>
          </div>
        </div>

        <!-- Charts: Game Volume vs Turnover & Outcome Composition -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-chart-column text-emerald-400"></i> Game Popularity: Bet Count vs. Turnover Debit
                </h3>
                <p class="text-xs text-slate-400">Comparison of wagering volume vs total financial value per game</p>
              </div>
            </div>
            <div id="gameTurnoverChart" class="chart-box"></div>
          </div>

          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-chart-pie text-cyan-400"></i> Outcome Composition by Game (% Win, Loss, Tie)
                </h3>
                <p class="text-xs text-slate-400">Distribution of player round results across game mechanics</p>
              </div>
            </div>
            <div id="gameOutcomeChart" class="chart-box"></div>
          </div>
        </div>

        <!-- Games Master Table -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-list-check text-emerald-400"></i> Complete Game Performance Master Registry
              </h3>
              <p class="text-xs text-slate-400">Full financial audit, hit rates, RTP, and average balance per game type</p>
            </div>
            <button onclick="exportTableToCSV('gamesTable', 'game_ecosystem_master.csv')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700">
              <i class="fa-solid fa-download text-emerald-400 mr-1"></i> Export CSV
            </button>
          </div>
          <div class="overflow-x-auto">
            <table id="gamesTable" class="w-full text-left text-xs">
              <thead class="bg-slate-900/80 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                <tr>
                  <th class="py-3 px-3">Game Name</th>
                  <th class="py-3 px-3 text-right">Total Bets</th>
                  <th class="py-3 px-3 text-right">Total Debit</th>
                  <th class="py-3 px-3 text-right">Net GGR</th>
                  <th class="py-3 px-3 text-right">Hold Margin %</th>
                  <th class="py-3 px-3 text-right">RTP %</th>
                  <th class="py-3 px-3 text-right">Win Rate %</th>
                  <th class="py-3 px-3 text-right">Avg Bet Size</th>
                  <th class="py-3 px-3 text-right">Avg Player Balance</th>
                  <th class="py-3 px-3 text-right">Bet-to-Balance %</th>
                </tr>
              </thead>
              <tbody id="gamesTableBody" class="divide-y divide-slate-800/60 font-mono">
                <!-- Dynamically Populated -->
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 3: BETTING BEHAVIOR & PROGRESSION -->
      <!-- ========================================================================= -->
      <section id="tab-behavior" class="tab-pane hidden space-y-6">
        <div class="glass-card rounded-2xl p-5 bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border border-amber-500/20">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
            <i class="fa-solid fa-brain"></i> Player Psychology & Wagering Patterns
          </div>
          <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">Betting Behavior & Progression Dynamics</h2>
          <p class="text-xs text-slate-300">How do players size their wagers? How do they react to wins vs losses? How do mobile vs desktop players differ?</p>
        </div>

        <!-- Behavior KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Post-Loss Bet Escalation</span>
            <div class="text-2xl font-extrabold text-rose-400 font-mono mt-1">37.8% Martingale</div>
            <span class="text-[11px] text-slate-400">Players increase bet immediately after losing</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Post-Win Press Rate</span>
            <div class="text-2xl font-extrabold text-emerald-400 font-mono mt-1">29.1% Pressing</div>
            <span class="text-[11px] text-slate-400">Players increase bet following a winning round</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Mobile Wager Domination</span>
            <div class="text-2xl font-extrabold text-cyan-400 font-mono mt-1">84.4% Mobile</div>
            <span class="text-[11px] text-slate-400">Mobile wagers dominate total volume</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Desktop Bet Premium</span>
            <div class="text-2xl font-extrabold text-indigo-400 font-mono mt-1">2.8x Larger Stakes</div>
            <span class="text-[11px] text-slate-400">Desktop players wager significantly higher avg bet</span>
          </div>
        </div>

        <!-- Charts: Bet Sizing Distribution & Post-Outcome Progression -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-layer-group text-amber-400"></i> Bet Sizing Bracket Distribution
                </h3>
                <p class="text-xs text-slate-400">Breakdown from Micro-bets (&lt;100) to Whale bets (&gt;1,000,000)</p>
              </div>
            </div>
            <div id="betBracketsChart" class="chart-box"></div>
          </div>

          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-code-branch text-rose-400"></i> Reaction to Outcome: Win vs. Loss Progression
                </h3>
                <p class="text-xs text-slate-400">Behavioral divergence: Do players Increase, Decrease, or Keep Bets Same?</p>
              </div>
            </div>
            <div id="betProgressionChart" class="chart-box"></div>
          </div>
        </div>

        <!-- Device Comparison Card -->
        <div class="glass-card rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-mobile-screen text-cyan-400"></i> Device Telemetry: Mobile vs. Desktop Profiles
              </h3>
              <p class="text-xs text-slate-400">Behavioral segmentation between smartphone players and desktop workstation users</p>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <span class="text-xs font-bold text-cyan-400 flex items-center gap-1.5"><i class="fa-solid fa-mobile"></i> Mobile (84.4%)</span>
              <div class="text-sm font-bold text-white font-mono">1,479,935 Bets</div>
              <p class="text-xs text-slate-300">Fast, frequent, lower-stake sessions. Mobile players exhibit rapid re-bets (&lt;10s) and higher responsiveness to flash push notifications.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <span class="text-xs font-bold text-indigo-400 flex items-center gap-1.5"><i class="fa-solid fa-desktop"></i> Desktop (14.5%)</span>
              <div class="text-sm font-bold text-white font-mono">261,905 Bets</div>
              <p class="text-xs text-slate-300">High-conviction, deliberate play with 2.8x higher average wager size. Desktop players multi-table and analyze roadmaps/history scorecards.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <span class="text-xs font-bold text-amber-400 flex items-center gap-1.5"><i class="fa-solid fa-gauge"></i> Behavioral Implication</span>
              <div class="text-sm font-bold text-white font-mono">UX Divergence</div>
              <p class="text-xs text-slate-300">Mobile interface must be optimized for single-thumb one-tap re-bets, while Desktop interface requires multi-window baccarat and detailed trend analysis.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 4: BETTING FREQUENCY & VELOCITY -->
      <!-- ========================================================================= -->
      <section id="tab-frequency" class="tab-pane hidden space-y-6">
        <div class="glass-card rounded-2xl p-5 bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border border-rose-500/20">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
            <i class="fa-solid fa-bolt"></i> Wager Velocity & Cadence Forensics
          </div>
          <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">How Frequently Do Players Bet?</h2>
          <p class="text-xs text-slate-300">Inter-bet arrival time analysis measuring the delta seconds between consecutive wagers placed by the same player</p>
        </div>

        <!-- Frequency KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Modal Cadence (15s–30s)</span>
            <div class="text-2xl font-extrabold text-rose-400 font-mono mt-1">31.4% of Bets</div>
            <span class="text-[11px] text-slate-400">Directly syncs with live dealer round deal cycle</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Hyper-Speed Wagers (&lt;5s)</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1">27.7% of Bets</div>
            <span class="text-[11px] text-slate-400">Multi-spot side-bets or rapid re-betting bursts</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Fast Execution (&lt;30s)</span>
            <div class="text-2xl font-extrabold text-cyan-400 font-mono mt-1">69.6% Total</div>
            <span class="text-[11px] text-slate-400">Over two-thirds of all bets placed in &lt;30 seconds</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Deliberate / Inactive (&gt;60s)</span>
            <div class="text-2xl font-extrabold text-slate-300 font-mono mt-1">8.7% Total</div>
            <span class="text-[11px] text-slate-400">Players skipping rounds or stepping away</span>
          </div>
        </div>

        <!-- Charts: Inter-Bet Frequency Chart & Velocity Breakdown -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-stopwatch text-rose-400"></i> Inter-Bet Arrival Times (Delta Seconds Between Bets)
                </h3>
                <p class="text-xs text-slate-400">Distribution of elapsed time before placing the next wager in a session</p>
              </div>
            </div>
            <div id="frequencyIntervalChart" class="chart-box"></div>
          </div>

          <div class="glass-card rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <h3 class="text-base font-bold text-white flex items-center gap-2 mb-2">
                <i class="fa-solid fa-wave-square text-cyan-400"></i> Behavioral Insights on Wager Velocity
              </h3>
              <p class="text-xs text-slate-400 mb-4">Why does wager cadence follow this exact mathematical distribution?</p>
              
              <div class="space-y-3 text-xs text-slate-300">
                <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div class="font-bold text-rose-400 mb-1">1. The Dealer Rhythm (15s–30s: 31.4%):</div>
                  Live baccarat and dragon tiger tables have a fixed dealing rhythm (~20 seconds between card reveals). Players who place 1 bet per round naturally cluster in this interval.
                </div>
                <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div class="font-bold text-amber-400 mb-1">2. The Multi-Spot Burst (&lt;5s: 27.7%):</div>
                  Players covering multiple outcomes (e.g. Banker + Player Pair + Tie in Baccarat, or multiple numbers in Roulette) trigger multiple debit calls within 1–3 seconds during the open betting window.
                </div>
                <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div class="font-bold text-cyan-400 mb-1">3. The Trend-Observer (30s–60s: 21.6%):</div>
                  Players who wait 1 to 2 rounds before betting to verify if a "dragon" (run) or "ping-pong" (alternating) streak is continuing on the shoe roadmap.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- TAB 5: BALANCE & BET CORRELATION -->
      <!-- ========================================================================= -->
      <section id="tab-correlation" class="tab-pane hidden space-y-6">
        <div class="glass-card rounded-2xl p-5 bg-gradient-to-r from-purple-950/40 via-slate-900 to-slate-900 border border-purple-500/20">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-semibold">
            <i class="fa-solid fa-scale-balanced"></i> Bankroll Elasticity & Risk Exposure
          </div>
          <h2 class="text-2xl font-extrabold text-white tracking-tight mt-1">Correlation: Balance, Bets & Game Selection</h2>
          <p class="text-xs text-slate-300">What fraction of balance do players risk? How does balance dictate game choice? (The Kelly Risk Index)</p>
        </div>

        <!-- Correlation KPI Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Highest Risk-Appetite Game</span>
            <div class="text-2xl font-extrabold text-purple-400 font-mono mt-1">NiuNiu (29.4% Ratio)</div>
            <span class="text-[11px] text-slate-400">Players wager nearly 1/3 of total balance per round!</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Dragon Tiger Risk Ratio</span>
            <div class="text-2xl font-extrabold text-amber-400 font-mono mt-1">14.2% of Balance</div>
            <span class="text-[11px] text-slate-400">High volatility single-card rapid wagers</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Baccarat Conservative Ratio</span>
            <div class="text-2xl font-extrabold text-emerald-400 font-mono mt-1">11.3% of Balance</div>
            <span class="text-[11px] text-slate-400">Disciplined bankroll management by VIPs</span>
          </div>
          <div class="glass-card rounded-2xl p-4">
            <span class="text-xs text-slate-400 uppercase font-semibold">Ultra-Balance Transition (>10M)</span>
            <div class="text-2xl font-extrabold text-rose-400 font-mono mt-1">Roulette (76.0%)</div>
            <span class="text-[11px] text-slate-400">Whales with >10M balance flood into Roulette</span>
          </div>
        </div>

        <!-- Charts: Balance vs Bet Scatter & Balance Tier to Game Preference -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-arrows-to-circle text-purple-400"></i> Balance vs. Bet Size Correlation (Log-Log Scatter)
                </h3>
                <p class="text-xs text-slate-400">X: Player Balance | Y: Wager Size. Colored by Game Type.</p>
              </div>
            </div>
            <div id="balanceScatterChart" class="chart-box"></div>
          </div>

          <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                  <i class="fa-solid fa-cubes-stacked text-cyan-400"></i> Balance Tier to Game Preference Matrix
                </h3>
                <p class="text-xs text-slate-400">How game selection dramatically shifts across player wealth brackets</p>
              </div>
            </div>
            <div id="balanceTierGameChart" class="chart-box"></div>
          </div>
        </div>

        <!-- Deep Analytical Takeaways Card -->
        <div class="glass-card rounded-2xl p-6">
          <h3 class="text-base font-bold text-white mb-3 flex items-center gap-2">
            <i class="fa-solid fa-lightbulb text-amber-400"></i> Strategic Synthesis: The Balance-to-Game Behavioral Law
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
              <span class="font-bold text-emerald-400 block">1. The Under-100K Bracket: Baccarat & Dragon Tiger Core</span>
              <p>Players with balances from &lt;1K up to 100K are split almost equally between Baccarat (~45%) and Dragon Tiger (~45%). They bet 10%–14% of their balance per round, treating the games as 50/50 momentum vehicles.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
              <span class="font-bold text-amber-400 block">2. The 100K–1M Bracket: The Dragon Tiger Escalation</span>
              <p>As balances reach 100K–1M, Dragon Tiger surges to **57.0% preference**. Players seek maximum speed (single card, no draws) with large stakes ($86k average bet), seeking rapid doubling.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
              <span class="font-bold text-rose-400 block">3. The >10M Whale Bracket: The Roulette Shift</span>
              <p>When balances exceed **10 Million**, **76.0% of all bets shift to Roulette**! Why? Ultra-whales exploit high-limit Roulette to spread massive multi-spot bets across neighbors, dozens, and straight-ups, hedging variance while placing multi-million chip wagers.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- ========================================================================= -->
      <!-- PRESENTATION DECK MODE (FULLSCREEN SLIDES) -->
      <!-- ========================================================================= -->
      <section id="presentationDeck" class="hidden space-y-6">
        <div class="flex items-center justify-between bg-slate-900/90 border border-slate-800 p-4 rounded-2xl">
          <div class="flex items-center gap-3">
            <button onclick="togglePresentationMode()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition">
              <i class="fa-solid fa-xmark mr-1"></i> Exit Presentation
            </button>
            <span class="text-xs text-slate-400 font-mono">Slide <span id="currentSlideNum" class="text-white font-bold">1</span> of 5</span>
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

        <!-- SLIDE 1: Payout & Win Timing -->
        <div id="slide-1" class="slide active glass-card rounded-2xl p-8 space-y-6 min-h-[560px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold border border-cyan-500/30">
            SLIDE 1 // CREDIT & WIN TIMING
          </div>
          <h2 class="text-3xl font-black text-white">When Do Players Credit & Win?</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p><strong>Round Turnaround:</strong> Payout latency averages <strong>8.2 seconds</strong> from debit placement to credit settlement.</p>
              <p><strong>Peak Payout Period:</strong> Credit returns peak at <strong>20:00 UTC</strong> (>3.4B credited back to players), driven by Asian prime-time traffic.</p>
              <p><strong>RTP Stability:</strong> Across the 24-hour cycle, player win rates remain consistent at <strong>33%–37%</strong>, with casino house hold safely hovering between 1.5% and 5.7%.</p>
            </div>
            <div id="slideTimingChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 2: Which Games They Play -->
        <div id="slide-2" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[560px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold border border-emerald-500/30">
            SLIDE 2 // GAME SELECTION & REVENUE
          </div>
          <h2 class="text-3xl font-black text-white">Game Ecosystem: The Baccarat & Dragon Tiger Empire</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p><strong>83.7% Market Dominance:</strong> Baccarat (42.3%) and Dragon Tiger (41.4%) account for the overwhelming majority of all wagers and debit turnover.</p>
              <p><strong>Stakes & Yield:</strong> Baccarat leads average stake size at <strong>$37,182</strong>, followed by Dragon Tiger at <strong>$35,242</strong>.</p>
              <p><strong>High-Hold Specialists:</strong> Roulette captures the highest operator hold margin at <strong>5.33%</strong>, while NiuNiu (Bull Bull) provides the highest hit rate for players (49.2%).</p>
            </div>
            <div id="slideGameChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 3: Betting Progression -->
        <div id="slide-3" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[560px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold border border-amber-500/30">
            SLIDE 3 // BETTING BEHAVIOR & REACTION
          </div>
          <h2 class="text-3xl font-black text-white">Martingale Psychology & Mobile Domination</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p><strong>Post-Loss Escalation:</strong> <strong>37.8% of players increase their bet immediately following a loss</strong>, demonstrating strong Martingale and chasing instincts.</p>
              <p><strong>Mobile Primacy:</strong> <strong>84.4% of all wagers</strong> originate on mobile devices, characterized by high speed and lower stakes.</p>
              <p><strong>Desktop Premium:</strong> Desktop players represent 14.5% of volume but bet <strong>2.8x higher average stakes</strong>.</p>
            </div>
            <div id="slideBehaviorChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 4: Wager Velocity -->
        <div id="slide-4" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[560px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/30">
            SLIDE 4 // BETTING FREQUENCY
          </div>
          <h2 class="text-3xl font-black text-white">Wager Cadence: 69.6% Wagered Under 30 Seconds</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p><strong>Cadence Clustering:</strong> <strong>31.4% of bets</strong> occur at 15–30 seconds, perfectly matching the live dealer round dealing loop.</p>
              <p><strong>Hyper-Speed Bursts:</strong> <strong>27.7% of bets</strong> occur in &lt;5 seconds as players drop multiple side bets or smash the quick-rebet button.</p>
              <p><strong>Paced Observers:</strong> 21.6% wait 30–60 seconds, observing shoe roadmaps before placing their next wager.</p>
            </div>
            <div id="slideFrequencyChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>

        <!-- SLIDE 5: Balance vs Bet Correlation -->
        <div id="slide-5" class="slide glass-card rounded-2xl p-8 space-y-6 min-h-[560px]">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-bold border border-purple-500/30">
            SLIDE 5 // BALANCE & BET CORRELATION
          </div>
          <h2 class="text-3xl font-black text-white">The Bankroll Rule: How Balance Dictates the Game</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="space-y-4 text-sm text-slate-300">
              <p><strong>Risk Ratios:</strong> Players wager 11%–14% of their balance on Baccarat and Dragon Tiger, but surge to <strong>29.4% of balance on NiuNiu</strong>.</p>
              <p><strong>The Mega-Whale Pivot:</strong> While normal balances stick to Baccarat/Dragon Tiger, balances exceeding <strong>10 Million shift 76.0% to Roulette</strong> to spread high-limit multi-spot coverage.</p>
              <p><strong>Kelly Compliance:</strong> Sub-1K players bet higher fractions of balance than whales, accelerating churn for casual players.</p>
            </div>
            <div id="slideCorrelationChart" class="chart-box" style="height: 320px;"></div>
          </div>
        </div>
      </section>

    </main>

    <!-- FOOTER -->
    <footer class="mt-auto py-6 border-t border-slate-800 text-center text-xs text-slate-500 no-print">
      <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-2">
        <span>ORIENTAL GAMING TITLE // PLAYER BEHAVIORAL INTELLIGENCE CONSOLE</span>
        <span class="font-mono">Deep-Dive Transaction Telemetry &bull; August 2026 Audit</span>
      </div>
    </footer>

  </div>

  <!-- EMBEDDED DATASET -->
  <script id="behavior-raw-data" type="application/json">
{json_str}
  </script>

  <!-- CONTROLLER SCRIPT -->
  <script>
    const DATA = JSON.parse(document.getElementById('behavior-raw-data').textContent);
    console.log("Player Behavior Data Loaded:", DATA);

    let isPresentationMode = false;
    let currentSlide = 1;
    const totalSlides = 5;
    let chartInstances = {{}};

    document.addEventListener('DOMContentLoaded', () => {{
      populateTimingTable();
      populateGamesTable();
      initTimingCharts();
      setupKeyboardNavigation();
    }});

    function switchTab(tabId) {{
      if (isPresentationMode) togglePresentationMode();
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));

      const targetPane = document.getElementById(`tab-${{tabId}}`);
      if (targetPane) targetPane.classList.remove('hidden');

      const clickedBtn = Array.from(document.querySelectorAll('.nav-tab')).find(b => b.getAttribute('onclick')?.includes(tabId));
      if (clickedBtn) clickedBtn.classList.add('active');

      setTimeout(() => {{
        if (tabId === 'timing') initTimingCharts();
        else if (tabId === 'games') initGamesCharts();
        else if (tabId === 'behavior') initBehaviorCharts();
        else if (tabId === 'frequency') initFrequencyCharts();
        else if (tabId === 'correlation') initCorrelationCharts();
        resizeAllCharts();
      }}, 50);
    }}

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
        switchTab('timing');
      }}
    }}

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

    function formatCurrency(val) {{
      if (val >= 1e9) return (val / 1e9).toFixed(2) + 'B';
      if (val >= 1e6) return (val / 1e6).toFixed(2) + 'M';
      if (val >= 1e3) return (val / 1e3).toFixed(1) + 'K';
      return Number(val).toLocaleString();
    }}

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

    function resizeAllCharts() {{
      Object.values(chartInstances).forEach(c => c && c.resize());
    }}
    window.addEventListener('resize', resizeAllCharts);

    function reinitAllCharts() {{
      Object.values(chartInstances).forEach(c => c && c.dispose());
      chartInstances = {{}};
      initTimingCharts();
      initGamesCharts();
      initBehaviorCharts();
      initFrequencyCharts();
      initCorrelationCharts();
      if (isPresentationMode) renderSlideCharts();
    }}

    // Populate Timing Table
    function populateTimingTable() {{
      const tbody = document.getElementById('timingTableBody');
      tbody.innerHTML = '';
      DATA.hourly_credit_and_wins.forEach(h => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/40 transition";
        tr.innerHTML = `
          <td class="py-2.5 px-3 text-cyan-400 font-bold">${{h.hour}}</td>
          <td class="py-2.5 px-3 text-right text-slate-300">${{h.total_bets.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-emerald-400 font-bold">${{h.wins.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-slate-300">${{h.win_rate_pct}}%</td>
          <td class="py-2.5 px-3 text-right text-slate-300">${{h.total_debit.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-cyan-300 font-bold">${{h.total_credit.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right ${{h.net_ggr >= 0 ? 'text-emerald-400' : 'text-rose-400'}} font-bold">${{h.net_ggr.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-slate-400">${{h.rtp_pct}}%</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // Populate Games Table
    function populateGamesTable() {{
      const tbody = document.getElementById('gamesTableBody');
      tbody.innerHTML = '';
      DATA.games.forEach(g => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-800/40 transition";
        tr.innerHTML = `
          <td class="py-2.5 px-3 text-white font-semibold flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <code>${{g.game}}</code>
          </td>
          <td class="py-2.5 px-3 text-right text-slate-300">${{g.total_bets.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-emerald-400 font-bold">${{g.total_debit.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-slate-300">${{g.ggr.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right font-bold text-emerald-300">${{g.hold_margin_pct}}%</td>
          <td class="py-2.5 px-3 text-right text-slate-400">${{g.rtp_pct}}%</td>
          <td class="py-2.5 px-3 text-right text-cyan-300 font-bold">${{g.win_rate_pct}}%</td>
          <td class="py-2.5 px-3 text-right text-amber-300">${{g.avg_bet.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-slate-400">${{g.avg_player_balance.toLocaleString()}}</td>
          <td class="py-2.5 px-3 text-right text-purple-300 font-bold">${{g.avg_bet_to_balance_pct}}%</td>
        `;
        tbody.appendChild(tr);
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
    // ECHARTS BUILDERS
    // =========================================================================

    // 1. Timing Charts
    function initTimingCharts() {{
      const dom1 = document.getElementById('timingOutcomeChart');
      if (dom1 && !chartInstances['timingOutcome']) {{
        const t = getChartTheme();
        const c1 = echarts.init(dom1);
        chartInstances['timingOutcome'] = c1;

        const hours = DATA.hourly_credit_and_wins.map(d => d.hour);
        const wins = DATA.hourly_credit_and_wins.map(d => d.wins);
        const losses = DATA.hourly_credit_and_wins.map(d => d.losses);
        const ties = DATA.hourly_credit_and_wins.map(d => d.ties);

        c1.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          legend: {{ data: ['Wins', 'Losses', 'Pushes'], textStyle: {{ color: t.textColor }} }},
          grid: {{ top: 35, right: 20, bottom: 30, left: 50 }},
          xAxis: {{ type: 'category', data: hours, axisLabel: {{ color: t.textColor, fontSize: 10 }}, axisLine: {{ lineStyle: {{ color: t.gridBorder }} }} }},
          yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }}, axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => (v/1000).toFixed(0) + 'K' }} }},
series: [
            {{ name: 'Wins', type: 'line', data: wins, lineStyle: {{ color: '#10b981', width: 2 }}, itemStyle: {{ color: '#10b981' }}, areaStyle: {{ color: 'rgba(16,185,129,0.15)' }} }},
            {{ name: 'Losses', type: 'line', data: losses, lineStyle: {{ color: '#f43f5e', width: 2 }}, itemStyle: {{ color: '#f43f5e' }}, areaStyle: {{ color: 'rgba(244,63,94,0.15)' }} }},
            {{ name: 'Pushes', type: 'line', data: ties, lineStyle: {{ color: '#6366f1', width: 2 }}, itemStyle: {{ color: '#6366f1' }}, areaStyle: {{ color: 'rgba(99,102,241,0.15)' }} }}
          ]
        }});
      }}

      const dom2 = document.getElementById('timingRtpChart');
      if (dom2 && !chartInstances['timingRtp']) {{
        const t = getChartTheme();
        const c2 = echarts.init(dom2);
        chartInstances['timingRtp'] = c2;

        const hours = DATA.hourly_credit_and_wins.map(d => d.hour);
        const debit = DATA.hourly_credit_and_wins.map(d => d.total_debit);
        const credit = DATA.hourly_credit_and_wins.map(d => d.total_credit);
        const rtp = DATA.hourly_credit_and_wins.map(d => d.rtp_pct);

        c2.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          legend: {{ data: ['Debit Turnover', 'Credit Payouts', 'RTP %'], textStyle: {{ color: t.textColor }} }},
          grid: {{ top: 35, right: 50, bottom: 30, left: 60 }},
          xAxis: {{ type: 'category', data: hours, axisLabel: {{ color: t.textColor, fontSize: 10 }}, axisLine: {{ lineStyle: {{ color: t.gridBorder }} }} }},
          yAxis: [
            {{ type: 'value', name: 'Turnover', splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }}, axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => formatCurrency(v) }} }},
            {{ type: 'value', name: 'RTP %', min: 90, max: 110, axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => v + '%' }} }}
          ],
          series: [
            {{ name: 'Debit Turnover', type: 'bar', data: debit, itemStyle: {{ color: '#3b82f6', borderRadius: [4, 4, 0, 0] }} }},
            {{ name: 'Credit Payouts', type: 'bar', data: credit, itemStyle: {{ color: '#10b981', borderRadius: [4, 4, 0, 0] }} }},
            {{ name: 'RTP %', type: 'line', yAxisIndex: 1, data: rtp, lineStyle: {{ color: '#f59e0b', width: 2 }}, itemStyle: {{ color: '#f59e0b' }} }}
          ]
        }});
      }}
    }}

    // 2. Games Charts
    function initGamesCharts() {{
      const dom1 = document.getElementById('gameTurnoverChart');
      if (dom1 && !chartInstances['gameTurnover']) {{
        const t = getChartTheme();
        const c1 = echarts.init(dom1);
        chartInstances['gameTurnover'] = c1;

        const games = DATA.games.map(d => d.game);
        const bets = DATA.games.map(d => d.total_bets);
        const debits = DATA.games.map(d => d.total_debit);

        c1.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          grid: {{ top: 30, right: 30, bottom: 40, left: 60 }},
          xAxis: {{ type: 'category', data: games, axisLabel: {{ color: t.textColor, fontSize: 10, rotate: 20 }}, axisLine: {{ lineStyle: {{ color: t.gridBorder }} }} }},
          yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }}, axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => (v/1000).toFixed(0) + 'K' }} }},
          series: [
            {{ name: 'Total Bets', type: 'bar', data: bets, itemStyle: {{ color: '#10b981', borderRadius: [4, 4, 0, 0] }} }}
          ]
        }});
      }}

      const dom2 = document.getElementById('gameOutcomeChart');
      if (dom2 && !chartInstances['gameOutcome']) {{
        const t = getChartTheme();
        const c2 = echarts.init(dom2);
        chartInstances['gameOutcome'] = c2;

        const games = DATA.games.map(d => d.game);
        const winPcts = DATA.games.map(d => d.win_rate_pct);
        const lossPcts = DATA.games.map(d => d.loss_rate_pct);
        const tiePcts = DATA.games.map(d => d.tie_rate_pct);

        c2.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          legend: {{ data: ['Win %', 'Loss %', 'Tie/Push %'], textStyle: {{ color: t.textColor }} }},
          grid: {{ top: 35, right: 30, bottom: 40, left: 50 }},
          xAxis: {{ type: 'category', data: games, axisLabel: {{ color: t.textColor, fontSize: 10, rotate: 20 }}, axisLine: {{ lineStyle: {{ color: t.gridBorder }} }} }},
          yAxis: {{ type: 'value', max: 100, axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => v + '%' }} }},
          series: [
            {{ name: 'Win %', type: 'bar', stack: 'total', data: winPcts, itemStyle: {{ color: '#10b981' }} }},
            {{ name: 'Loss %', type: 'bar', stack: 'total', data: lossPcts, itemStyle: {{ color: '#f43f5e' }} }},
            {{ name: 'Tie/Push %', type: 'bar', stack: 'total', data: tiePcts, itemStyle: {{ color: '#6366f1' }} }}
          ]
        }});
      }}
    }}

    // 3. Behavior Charts
    function initBehaviorCharts() {{
      const dom1 = document.getElementById('betBracketsChart');
      if (dom1 && !chartInstances['betBrackets']) {{
        const t = getChartTheme();
        const c1 = echarts.init(dom1);
        chartInstances['betBrackets'] = c1;

        const labels = DATA.bet_brackets.map(b => b.bracket);
        const counts = DATA.bet_brackets.map(b => b.count);

        c1.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          grid: {{ top: 20, right: 30, bottom: 40, left: 110 }},
          xAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }}, axisLabel: {{ color: t.textColor, fontSize: 10 }} }},
          yAxis: {{ type: 'category', data: labels, axisLine: {{ lineStyle: {{ color: t.gridBorder }} }}, axisLabel: {{ color: t.textColor, fontSize: 9 }} }},
          series: [{{
            type: 'bar',
            data: counts,
            itemStyle: {{ color: '#f59e0b', borderRadius: [0, 6, 6, 0] }},
            label: {{ show: true, position: 'right', color: t.textColor, fontSize: 9, formatter: p => p.value.toLocaleString() }}
          }}]
        }});
      }}

      const dom2 = document.getElementById('betProgressionChart');
      if (dom2 && !chartInstances['betProgression']) {{
        const t = getChartTheme();
        const c2 = echarts.init(dom2);
        chartInstances['betProgression'] = c2;

        const bp = DATA.bet_progression;
        const lossTot = bp.after_loss.increased + bp.after_loss.decreased + bp.after_loss.same;
        const winTot = bp.after_win.increased + bp.after_win.decreased + bp.after_win.same;

        c2.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          legend: {{ data: ['Increased Bet (Aggressive)', 'Same Bet (Neutral)', 'Decreased Bet (Conservative)'], textStyle: {{ color: t.textColor }} }},
          grid: {{ top: 35, right: 20, bottom: 30, left: 60 }},
          xAxis: {{ type: 'category', data: ['After Loss (Martingale Risk)', 'After Win (Pressing Risk)'], axisLabel: {{ color: t.textColor, fontSize: 10 }} }},
          yAxis: {{ type: 'value', max: 100, axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => v + '%' }} }},
          series: [
            {{ name: 'Increased Bet (Aggressive)', type: 'bar', data: [((bp.after_loss.increased/lossTot)*100).toFixed(1), ((bp.after_win.increased/winTot)*100).toFixed(1)], itemStyle: {{ color: '#f43f5e' }} }},
            {{ name: 'Same Bet (Neutral)', type: 'bar', data: [((bp.after_loss.same/lossTot)*100).toFixed(1), ((bp.after_win.same/winTot)*100).toFixed(1)], itemStyle: {{ color: '#6366f1' }} }},
            {{ name: 'Decreased Bet (Conservative)', type: 'bar', data: [((bp.after_loss.decreased/lossTot)*100).toFixed(1), ((bp.after_win.decreased/winTot)*100).toFixed(1)], itemStyle: {{ color: '#10b981' }} }}
          ]
        }});
      }}
    }}

    // 4. Frequency Charts
    function initFrequencyCharts() {{
      const dom = document.getElementById('frequencyIntervalChart');
      if (dom && !chartInstances['frequencyInterval']) {{
        const t = getChartTheme();
        const c = echarts.init(dom);
        chartInstances['frequencyInterval'] = c;

        const intervals = DATA.bet_frequency_intervals.map(d => d.interval);
        const pcts = DATA.bet_frequency_intervals.map(d => d.pct);

        c.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          grid: {{ top: 20, right: 30, bottom: 40, left: 140 }},
          xAxis: {{ type: 'value', axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => v + '%' }} }},
          yAxis: {{ type: 'category', data: intervals, axisLabel: {{ color: t.textColor, fontSize: 10 }} }},
          series: [{{
            type: 'bar',
            data: pcts,
            itemStyle: {{ color: '#f43f5e', borderRadius: [0, 6, 6, 0] }},
            label: {{ show: true, position: 'right', color: t.textColor, fontSize: 10, formatter: p => p.value + '%' }}
          }}]
        }});
      }}
    }}

    // 5. Correlation Charts
    function initCorrelationCharts() {{
      const dom1 = document.getElementById('balanceScatterChart');
      if (dom1 && !chartInstances['balanceScatter']) {{
        const t = getChartTheme();
        const c1 = echarts.init(dom1);
        chartInstances['balanceScatter'] = c1;

        const pts = DATA.balance_vs_bet_scatter.map(p => [
          p.balance,
          p.bet,
          p.ratio_pct,
          p.game,
          p.outcome
        ]);

        c1.setOption({{
          backgroundColor: t.bg,
          tooltip: {{
            trigger: 'item',
            backgroundColor: t.tooltipBg,
            borderColor: t.tooltipBorder,
            textStyle: {{ color: t.tooltipText, fontSize: 11 }},
            formatter: p => `
              <div><strong>Game:</strong> ${{p.value[3]}}</div>
              <div><strong>Balance:</strong> ${{formatCurrency(p.value[0])}}</div>
              <div><strong>Bet Size:</strong> ${{formatCurrency(p.value[1])}}</div>
              <div><strong>Bet-to-Balance:</strong> ${{p.value[2]}}%</div>
              <div><strong>Outcome:</strong> ${{p.value[4]}}</div>
            `
          }},
          grid: {{ top: 30, right: 30, bottom: 40, left: 60 }},
          xAxis: {{ type: 'log', name: 'Balance', splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }}, axisLabel: {{ color: t.textColor, fontSize: 9, formatter: v => formatCurrency(v) }} }},
          yAxis: {{ type: 'log', name: 'Bet', splitLine: {{ lineStyle: {{ color: t.gridBorder, type: 'dashed' }} }}, axisLabel: {{ color: t.textColor, fontSize: 9, formatter: v => formatCurrency(v) }} }},
          series: [{{
            type: 'scatter',
            data: pts,
            symbolSize: 8,
            itemStyle: {{
              color: p => p.value[3] === 'baccarat' ? '#10b981' : (p.value[3] === 'dragon_tiger' ? '#f59e0b' : (p.value[3] === 'roulette' ? '#8b5cf6' : '#ec4899')),
              opacity: 0.75
            }}
          }}]
        }});
      }}

      const dom2 = document.getElementById('balanceTierGameChart');
      if (dom2 && !chartInstances['balanceTierGame']) {{
        const t = getChartTheme();
        const c2 = echarts.init(dom2);
        chartInstances['balanceTierGame'] = c2;

        const tiers = DATA.balance_tiers.map(b => b.tier);
        const baccaratPcts = DATA.balance_tiers.map(b => b.games['baccarat'] ? b.games['baccarat'].pct : 0);
        const dtPcts = DATA.balance_tiers.map(b => b.games['dragon_tiger'] ? b.games['dragon_tiger'].pct : 0);
        const roulettePcts = DATA.balance_tiers.map(b => b.games['roulette'] ? b.games['roulette'].pct : 0);

        c2.setOption({{
          backgroundColor: t.bg,
          tooltip: {{ trigger: 'axis', backgroundColor: t.tooltipBg, borderColor: t.tooltipBorder, textStyle: {{ color: t.tooltipText, fontSize: 11 }} }},
          legend: {{ data: ['Baccarat', 'Dragon Tiger', 'Roulette'], textStyle: {{ color: t.textColor }} }},
          grid: {{ top: 35, right: 30, bottom: 40, left: 50 }},
          xAxis: {{ type: 'category', data: tiers, axisLabel: {{ color: t.textColor, fontSize: 10 }} }},
          yAxis: {{ type: 'value', max: 100, axisLabel: {{ color: t.textColor, fontSize: 10, formatter: v => v + '%' }} }},
          series: [
            {{ name: 'Baccarat', type: 'bar', data: baccaratPcts, itemStyle: {{ color: '#10b981' }} }},
            {{ name: 'Dragon Tiger', type: 'bar', data: dtPcts, itemStyle: {{ color: '#f59e0b' }} }},
            {{ name: 'Roulette', type: 'bar', data: roulettePcts, itemStyle: {{ color: '#8b5cf6' }} }}
          ]
        }});
      }}
    }}

    // Slide Deck Render
    function renderSlideCharts() {{
      const t = getChartTheme();
      if (currentSlide === 1) {{
        const s1 = document.getElementById('slideTimingChart');
        if (s1) {{
          const c = echarts.init(s1);
          chartInstances['slideTiming'] = c;
          c.setOption({{
            backgroundColor: t.bg,
            grid: {{ top: 20, right: 20, bottom: 30, left: 40 }},
            xAxis: {{ type: 'category', data: DATA.hourly_credit_and_wins.map(d => d.hour), axisLabel: {{ color: t.textColor, fontSize: 8 }} }},
            yAxis: {{ type: 'value', axisLabel: {{ color: t.textColor, fontSize: 8 }} }},
            series: [{{ type: 'line', data: DATA.hourly_credit_and_wins.map(d => d.wins), lineStyle: {{ color: '#10b981' }} }}]
          }});
        }}
      }} else if (currentSlide === 2) {{
        const s2 = document.getElementById('slideGameChart');
        if (s2) {{
          const c = echarts.init(s2);
          chartInstances['slideGame'] = c;
          c.setOption({{
            backgroundColor: t.bg,
            grid: {{ top: 20, right: 20, bottom: 40, left: 50 }},
            xAxis: {{ type: 'category', data: DATA.games.map(d => d.game), axisLabel: {{ color: t.textColor, fontSize: 9, rotate: 20 }} }},
            yAxis: {{ type: 'value', axisLabel: {{ color: t.textColor, fontSize: 8 }} }},
            series: [{{ type: 'bar', data: DATA.games.map(d => d.total_bets), itemStyle: {{ color: '#10b981' }} }}]
          }});
        }}
      }}
    }}
  </script>
</body>
</html>'''

    out_file_1 = REPORT_DIR / "player_behavior_dashboard.html"
    out_file_2 = REPORT_DIR / "player_behavior_dashboard.html"
    with open(out_file_1, "w", encoding="utf-8") as f:
        f.write(html_template)
    with open(out_file_2, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Generated {out_file_1} ({len(html_template):,} chars)")
    return True

if __name__ == "__main__":
    build_dashboard()
