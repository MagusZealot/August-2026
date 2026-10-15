#!/usr/bin/env python3
"""Generate the game-isolated Dealer & Table Pace Intelligence console."""
from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
if not (WORKSPACE / "workspace_map.txt").exists():
    for _parent in WORKSPACE.parents:
        if (_parent / "workspace_map.txt").exists():
            WORKSPACE = _parent
            break

WORKSPACE = Path(WORKSPACE)
DATA_FILE = WORKSPACE / "output" / "round_dealer_table_time_data.json"
OUT_FILE = WORKSPACE / "output" / "dashboards" / "round_dealer_table_time_dashboard.html"


def _telemetry_rows(data):
    """Normalize the combined pipeline's entity entries into the console schema."""
    entity_entries = data.get("entity_entries")
    if not isinstance(entity_entries, dict):
        raise ValueError("Combined pace payload is missing its entity_entries object")

    rows = []
    for entity_id, entries in entity_entries.items():
        if not isinstance(entries, list):
            raise ValueError(f"Invalid telemetry entries for entity {entity_id!r}")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"Invalid telemetry record for entity {entity_id!r}")

            source = entry.get("source")
            if source not in ("dealer", "table"):
                raise ValueError(f"Unknown telemetry source {source!r} for entity {entity_id!r}")

            rows.append({
                "BILLING_DATE": entry.get("date"),
                "GAME_TYPE": entry.get("game_type"),
                "DEALER": entity_id if source == "dealer" else None,
                "TABLE_NO": entity_id if source == "table" else None,
                "AVG_TIMEDIFF": entry.get("actual_duration"),
                "STD_TIMEDIFF": entry.get("std_actual_duration"),
            })
    return rows


def render_dashboard(data):
    rows = _telemetry_rows(data)
    meta = data.get("meta") or {}
    console_data = {
        "meta": {
            "generated_at": meta.get("generated_at"),
            "latest_file_date": meta.get("latest_file_date"),
        },
        "rows": rows,
    }
    payload = json.dumps(console_data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    template = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dealer &amp; Table Pace Intelligence</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    :root { color-scheme: dark; font-family: Inter, "Segoe UI", sans-serif; background: #090e1a; color: #e2e8f0; }
    * { box-sizing: border-box; }
    body { margin: 0; min-width: 320px; background: radial-gradient(ellipse at top, #14213a 0, #090e1a 55%); }
    header { position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px; padding: 14px max(20px, calc((100vw - 1480px) / 2)); background: #0b1220ed; border-bottom: 1px solid #253247; backdrop-filter: blur(12px); }
    h1 { margin: 0; font-size: clamp(18px, 2.4vw, 26px); letter-spacing: .02em; }
    header p { margin: 5px 0 0; color: #93a4bc; font-size: 12px; }
    .filters { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; }
    select { min-width: 190px; padding: 9px 12px; border: 1px solid #344258; border-radius: 8px; background: #111b2d; color: #e2e8f0; font-family: inherit; font-size: 12px; }
    .game-tags button {
      padding: 6px 12px;
      border: 1px solid #344258;
      border-radius: 20px;
      background: #111b2d;
      color: #94a3b8;
      font-family: inherit;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .game-tags button.active {
      background: #1e3a5f;
      border-color: #34d399;
      color: #34d399;
    }
    .game-tags button:hover:not(.active) {
      border-color: #4a5a7a;
      background: #1a2740;
    }
    main { max-width: 1480px; margin: auto; padding: 22px; }
    .section { margin-bottom: 16px; }
    .hero { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 18px; }
    .hero h2 { margin: 0; font-size: 18px; }
    .hero p, .muted { color: #94a3b8; font-size: 12px; }
    .hero p { max-width: 900px; margin-bottom: 0; line-height: 1.55; }
    .kpis { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 10px; margin-bottom: 16px; }
    .card { border: 1px solid #24334a; border-radius: 14px; background: linear-gradient(145deg, #121d30e8, #0c1423f2); box-shadow: 0 10px 30px #0002; }
    .kpi { padding: 16px; }
    .kpi label { display: block; margin-bottom: 8px; color: #91a2ba; font-size: 10px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
    .kpi strong { font: 700 20px ui-monospace, Consolas, monospace; color: #f8fafc; }
    .kpi .sub { display: block; margin-top: 6px; color: #64748b; font-size: 10px; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .chart-card { min-width: 0; padding: 15px; }
    .chart-card h3 { margin: 0 0 8px; font-size: 14px; }
    .chart-card .muted { margin: 0 0 12px; }
    .chart { width: 100%; height: 360px; }
    .wide { grid-column: 1 / -1; }
    .full-width { width: 100vw; max-width: none; margin-left: calc(50% - 50vw); margin-right: calc(50% - 50vw); }
    .watchlist { padding: 16px; border-color: #7f1d1d; }
    .watchlist h3 { margin: 0 0 4px; color: #fda4af; font-size: 15px; }
    .watchlist .muted { margin: 0 0 12px; }
    .watchlist .pagination { display: flex; justify-content: space-between; align-items: center; margin: 12px 0 0; }
    .watchlist .pagination button { cursor: pointer; color: #94a3b8; }
    .watchlist .pagination button:disabled { opacity: 0.45; }
    .watchlist table th { color: #fda4af; }
    .watchlist table td { color: #fecdd3; }
    .watchlist .action { color: #fbbf24; font-weight: 700; }
    .table-wrap { overflow: auto; max-height: 680px; border: 1px solid #253247; border-radius: 10px; }
    table { width: 100%; border-collapse: collapse; white-space: nowrap; font-size: 12px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #253247; text-align: right; }
    th { position: sticky; top: 0; z-index: 1; background: #111b2d; color: #90a3bd; font-size: 10px; text-transform: uppercase; letter-spacing: .06em; }
    td:first-child, th:first-child { text-align: left; }
    tbody tr:hover { background: #17243a; }
    .table-empty { padding: 18px 12px; color: #94a3b8; font-size: 12px; font-style: italic; text-align: left; }
    .dealer-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
    @media (max-width: 1200px) { .dealer-grid { grid-template-columns: repeat(3, 1fr); } }
    @media (max-width: 900px) { .dealer-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 560px) { .dealer-grid { grid-template-columns: 1fr; } }
    .dossier-section { padding: 16px; }
    .dossier-section .card { padding: 16px; }
    .dossier-section h3 { margin: 0 0 8px; font-size: 14px; }
    .dossier-section .muted { margin: 0 0 12px; }
    .dossier-section .game-switcher { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .dossier-section .game-switcher button { padding: 4px 10px; border: 1px solid #344258; border-radius: 16px; background: #111b2d; color: #94a3b8; font-size: 11px; cursor: pointer; transition: all 0.15s; }
    .dossier-section .game-switcher button.active { background: #1e3a5f; border-color: #34d399; color: #34d399; }
    footer { padding: 22px 0 8px; color: #77869c; font-size: 11px; }
    @media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, 1fr); } .grid { grid-template-columns: 1fr; } .wide { grid-column: auto; } .full-width { width: auto; margin-left: 0; margin-right: 0; } }
    @media (max-width: 560px) { main { padding: 14px; } .kpis { grid-template-columns: 1fr; } .chart { height: 300px; } header { padding-inline: 14px; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1><i class="fa-solid fa-gauge-high" style="color:#34d399"></i> Dealer &amp; Table Pace Intelligence</h1>
      <p id="feedStatus">Loading pace telemetry...</p>
    </div>
<div class="filters">
      <div class="muted" style="font-size: 11px; margin-bottom: 6px;">Game type (all views are isolated to this game)</div>
      <div id="gameTags" class="game-tags" style="display: flex; flex-wrap: wrap; gap: 6px;"></div>
    </div>
</header>
<main>
    <section class="hero section">
      <div>
        <h2>Operational Efficiency & Pace Console</h2>
        <p>Dealer speeds are compared only with the selected game's baseline. The source feed reports dealers and tables as separate observations, not dealer-table pairings; the matrix and rankings preserve that distinction rather than inventing matches.</p>
      </div>
    </section>
    <section id="kpis" class="kpis section" aria-label="Selected game key performance indicators"></section>
    <section class="card watchlist section" aria-labelledby="watchlistTitle">
      <h3 id="watchlistTitle"><i class="fa-solid fa-triangle-exclamation"></i> Watchlist: Slow Dealers</h3>
      <p class="muted">Dealers slower than the selected game's baseline by at least 1.50 seconds or in its slowest 10%.</p>
      <div class="pagination">
        <span id="watchlistPageInfo">Loading watchlist…</span>
        <button id="watchlistPrevPage" type="button">&larr; Prev</button>
        <button id="watchlistNextPage" type="button">Next &rarr;</button>
      </div>
      <div class="chart-card">
        <div id="watchlistChart" class="chart"></div>
      </div>
    </section>
    <section class="card watchlist section" aria-labelledby="tableWatchlistTitle">
      <h3 id="tableWatchlistTitle"><i class="fa-solid fa-table"></i> Watchlist: Slow Tables</h3>
      <p class="muted">Tables slower than the selected game's baseline by at least 1.50 seconds or in its slowest 10%.</p>
      <div class="pagination">
        <span id="tableWatchlistPageInfo">Loading watchlist…</span>
        <button id="tableWatchlistPrevPage" type="button">&larr; Prev</button>
        <button id="tableWatchlistNextPage" type="button">Next &rarr;</button>
      </div>
      <div class="chart-card">
        <div id="tableWatchlistChart" class="chart"></div>
      </div>
    </section>
    <section class="grid section">
      <article class="card chart-card">
        <h3>Combined Efficiency Matrix</h3>
        <div class="muted">Average time (speed) vs standard deviation (consistency), selected game only</div>
        <div id="efficiencyMatrix" class="chart"></div>
      </article>
      <article class="card chart-card">
        <h3>Dealer Speed Over Time</h3>
        <div class="muted">Selected game's daily dealer baseline and up to five fastest and five slowest dealer trends</div>
        <div id="dealerTrend" class="chart"></div>
      </article>
      <article class="card chart-card wide">
        <h3>Top / Bottom 10 Dealer & Table Profiles</h3>
        <div class="muted">Fastest and slowest entity profiles by average time, ranked within the selected game only</div>
        <div id="paceExtremes" class="chart"></div>
      </article>
      <article class="card chart-card wide full-width">
        <h3>Individualized Dealer Dossier</h3>
        <div class="muted">Select a dealer to view their KPIs and performance trend</div>
        <div class="filters" style="margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 11px; color: #94a3b8;">Baseline:</label>
            <select id="filterBaseline" style="padding: 6px 10px; border: 1px solid #344258; border-radius: 6px; background: #111b2d; color: #e2e8f0; font-size: 11px;">
              <option value="">All</option>
              <option value="above">Above (Slower)</option>
              <option value="below">Below (Faster)</option>
            </select>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 11px; color: #94a3b8;">Min Days:</label>
            <select id="filterMinDays" style="padding: 6px 10px; border: 1px solid #344258; border-radius: 6px; background: #111b2d; color: #e2e8f0; font-size: 11px;">
              <option value="">Any</option>
              <option value="14">14+ Days</option>
              <option value="30">30+ Days</option>
              <option value="60">60+ Days</option>
            </select>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 11px; color: #94a3b8;">Week-over-Week (WoW):</label>
            <select id="filterWow" style="padding: 6px 10px; border: 1px solid #344258; border-radius: 6px; background: #111b2d; color: #e2e8f0; font-size: 11px;">
              <option value="">All</option>
              <option value="faster">Faster (Improved)</option>
              <option value="slower">Slower (Declined)</option>
              <option value="no-data">No Week-over-Week Data</option>
            </select>
          </div>
          <button id="clearFilters" type="button" style="padding: 6px 12px; border: 1px solid #344258; border-radius: 6px; background: #111b2d; color: #94a3b8; font-size: 11px; cursor: pointer;">Clear Filters</button>
        </div>
        <div id="dealerCardGrid" class="dealer-grid" style="padding: 16px;"></div>
        <div id="loadMoreBtn" style="margin: 16px auto; cursor: pointer; color: #94a3b8; text-align: center; display: none;">Load More Dealers &rarr;</div>
      </article>
    </section>
    <section id="dealerDossierSection" class="full-width dossier-section" style="display: none;">
        <div class="card" style="max-width: none; margin: 0;">
          <div style="padding: 16px;">
            <div style="font-size: 12px; color: #91a2ba; text-transform: uppercase; letter-spacing: .09em; margin-bottom: 12px;">Dealer Dossier</div>
            <div id="dealerDossierKpis" style="min-height: 120px;"></div>
            <div style="margin-top: 16px;">
              <strong>Other games for this dealer:</strong>
              <div id="dealerGameSwitcher" class="game-switcher"></div>
            </div>
            <div style="margin-top: 24px;">
              <strong>Trend Chart:</strong> Dealer performance over time
            </div>
            <div id="dealerDossierTrend" class="chart" style="height: 300px; margin-top: 12px;"></div>
          </div>
        </div>
      </section>
    </section>
    <footer>Source: combined daily dealer and table pace snapshots. Change the game selector to isolate all KPIs, charts, and tables to another game.</footer>
  </main>
  <script id="pace-console-data" type="application/json">__PAYLOAD__</script>
  <script>
    const DATA = JSON.parse(document.getElementById('pace-console-data').textContent);
    const ROWS = Array.isArray(DATA.rows) ? DATA.rows : [];
    const gameTagsContainer = document.getElementById('gameTags');
    let selectedGame = null;
    let currentPage = 1;
    let currentTablePage = 1;
    const getChartTheme = () => ({
      textColor: '#94a3b8',
      gridBorder: '#253247',
      tooltipBg: '#0f172a',
      tooltipBorder: '#334155',
      tooltipText: '#f8fafc'
    });
    const theme = getChartTheme();
    const palette = ['#38bdf8', '#34d399', '#fbbf24', '#c084fc', '#fb7185', '#2dd4bf', '#a3e635', '#f97316', '#818cf8', '#f472b6'];
    const axisStyle = {
      axisLabel: { color: theme.textColor },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: theme.gridBorder, type: 'dashed' } }
    };
    const tooltipStyle = {
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText, fontSize: 12 },
      confine: true
    };
    const charts = {
      efficiencyMatrix: echarts.init(document.getElementById('efficiencyMatrix')),
      dealerTrend: echarts.init(document.getElementById('dealerTrend')),
      paceExtremes: echarts.init(document.getElementById('paceExtremes')),
      watchlist: echarts.init(document.getElementById('watchlistChart')),
      tableWatchlist: echarts.init(document.getElementById('tableWatchlistChart'))
    };
    const allCharts = Object.values(charts);
    const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[character]));
    const num = value => value == null || value === '' || !Number.isFinite(Number(value)) ? null : Number(value);
    const mean = values => {
      const valid = values.map(num).filter(value => value != null);
      return valid.length ? valid.reduce((sum, value) => sum + value, 0) / valid.length : null;
    };
    const fmt2 = value => num(value) == null ? 'N/A' : num(value).toFixed(2);
    const safeCell = value => value ? escapeHtml(value) : 'N/A';
    const selectedRows = () => selectedGame ? ROWS.filter(row => row.GAME_TYPE === selectedGame) : ROWS;
    const currentGameColor = gameType => {
      if (!gameType) return palette[0];
      return palette[Math.max(0, [...new Set(ROWS.map(row => row.GAME_TYPE).filter(Boolean))].sort().indexOf(gameType)) % palette.length];
    };

    function summarizeProfiles(rows) {
      const profiles = new Map();
      rows.forEach(row => {
        const dealer = row.DEALER ? String(row.DEALER) : '';
        const tableNo = row.TABLE_NO ? String(row.TABLE_NO) : '';
        if (!dealer && !tableNo) return;
        const key = `${dealer}\u0000${tableNo}`;
        if (!profiles.has(key)) {
          profiles.set(key, { dealer, tableNo, avgValues: [], stdValues: [] });
        }
        const profile = profiles.get(key);
        if (num(row.AVG_TIMEDIFF) != null) profile.avgValues.push(num(row.AVG_TIMEDIFF));
        if (num(row.STD_TIMEDIFF) != null) profile.stdValues.push(num(row.STD_TIMEDIFF));
      });
      return [...profiles.values()].map(profile => ({
        ...profile,
        avg: mean(profile.avgValues),
        std: mean(profile.stdValues),
        label: profile.dealer && profile.tableNo
          ? `${profile.dealer} · ${profile.tableNo}`
          : profile.dealer ? `Dealer · ${profile.dealer}` : `Table · ${profile.tableNo}`
      }));
    }

    function renderKpis(rows) {
      const dealers = rows.filter(row => row.DEALER);
      const globalAvg = mean(rows.map(row => row.AVG_TIMEDIFF));
      const gameBaseline = mean(dealers.map(row => row.AVG_TIMEDIFF));
      const stdBaseline = mean(rows.map(row => row.STD_TIMEDIFF));
      const dealerCount = new Set(rows.map(row => row.DEALER).filter(Boolean)).size;
      const tableCount = new Set(rows.map(row => row.TABLE_NO).filter(Boolean)).size;
      const game = selectedGame || 'All Games';
      const tiles = [
        ['Global Average Pace', `${fmt2(globalAvg)} s`, selectedGame ? `${selectedGame} only` : 'All games'],
        ['Selected Game Baseline', `${fmt2(gameBaseline)} s`, selectedGame ? 'Average dealer time for this game' : 'Average dealer time across all games'],
        ['Average Std Dev', `${fmt2(stdBaseline)} s`, selectedGame ? 'Consistency baseline for this game' : 'Consistency baseline across all games'],
        ['Active Fleet', `${dealerCount} / ${tableCount}`, `${dealerCount} dealers · ${tableCount} tables ${selectedGame ? `in ${selectedGame}` : 'across all games'}`]
      ];
      document.getElementById('kpis').innerHTML = tiles.map(([label, value, sub]) =>
        `<div class="card kpi"><label>${escapeHtml(label)}</label><strong>${value}</strong><span class="sub">${escapeHtml(sub)}</span></div>`
      ).join('');

      const generatedAt = DATA.meta && DATA.meta.generated_at;
      document.getElementById('feedStatus').textContent = generatedAt
        ? `Updated ${generatedAt} · ${game}`
        : `Pace telemetry loaded · ${game}`;
    }

    function renderWatchlist(rows) {
      const gameType = selectedGame;
      
      // In "Show All" mode, watchlist doesn't make sense - show message
      if (!gameType) {
        charts.watchlist.clear();
        charts.watchlist.setOption({
          graphic: [{ type: 'text', left: 'center', top: 'middle', style: { text: 'Select a game to view the slow dealer watchlist.', fill: theme.textColor, fontSize: 12 } }]
        });
        document.getElementById('watchlistPageInfo').textContent = '';
        return;
      }
      
      const dealerRows = rows.filter(row => row.DEALER && num(row.AVG_TIMEDIFF) != null);
      const baseline = mean(dealerRows.map(row => row.AVG_TIMEDIFF));
      const grouped = new Map();
      dealerRows.forEach(row => {
        const dealer = String(row.DEALER);
        if (!grouped.has(dealer)) grouped.set(dealer, []);
        grouped.get(dealer).push(num(row.AVG_TIMEDIFF));
      });
      const dealerAvgs = [...grouped.entries()]
        .map(([dealer, values]) => ({ dealer, avg: mean(values) }))
        .filter(item => item.avg != null)
        .sort((a, b) => a.avg - b.avg);
      const slowDecileIndex = dealerAvgs.length
        ? Math.max(0, Math.ceil(dealerAvgs.length * 0.9) - 1)
        : -1;
      const slowDecileFloor = slowDecileIndex >= 0 ? dealerAvgs[slowDecileIndex].avg : null;
      const flagged = dealerAvgs.filter(item => {
        const delta = item.avg - baseline;
        return delta > 0 && (delta >= 1.5 || item.avg >= slowDecileFloor);
      }).sort((a, b) => b.avg - a.avg);
      
      // Pagination: show up to 20 dealers per page
      const itemsPerPage = 20;
      const page = Math.max(1, Math.min(currentPage, Math.ceil(flagged.length / itemsPerPage) || 1));
      const startIdx = (page - 1) * itemsPerPage;
      const endIdx = startIdx + itemsPerPage;
      const pageFlagged = flagged.slice(startIdx, endIdx);
      const totalPages = Math.ceil(flagged.length / itemsPerPage) || 1;
      
      if (!flagged.length) {
        charts.watchlist.clear();
        charts.watchlist.setOption({
          graphic: [{ type: 'text', left: 'center', top: 'middle', style: { text: 'No dealers meet the selected-game slow-pace thresholds.', fill: theme.textColor, fontSize: 12 } }]
        });
        document.getElementById('watchlistPageInfo').textContent = '0 dealers';
        return;
      }
      const points = pageFlagged.map(item => ({
        value: item.avg,
        label: item.dealer,
        delta: item.avg - baseline
      }));
      
      charts.watchlist.setOption({
        tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' },
          formatter: params => {
            const point = points[params[0].dataIndex];
            return `<strong>${escapeHtml(point.label)}</strong><br>Dealer average: ${fmt2(point.value)} s<br>${escapeHtml(gameType)} baseline: ${fmt2(baseline)} s<br>Slower than baseline: +${fmt2(point.delta)} s`;
          }
        },
        xAxis: { type: 'value', name: 'AVG_TIMEDIFF (s)', nameTextStyle: { color: theme.textColor, fontSize: 11 }, ...axisStyle },
        yAxis: { type: 'category', data: points.map(p => p.label), inverse: true, axisLabel: { ...axisStyle.axisLabel, fontSize: 10 } },
        series: [{
          name: 'Slow Dealers',
          type: 'bar',
          barWidth: '60%',
          itemStyle: {
            color: params => {
              const delta = points[params.dataIndex].delta;
              return delta >= 1.5 ? '#fb7185' : '#fbbf24';
            }
          },
          data: points.map(p => p.value),
          label: { show: true, position: 'right', color: theme.textColor, formatter: params => `${fmt2(params.value)} s`, fontSize: 10 },
          markLine: {
            symbol: ['none', 'none'],
            lineStyle: { color: '#38bdf8', type: 'dashed', width: 2 },
            label: { 
              formatter: `Baseline ${fmt2(baseline)} s`, 
              color: '#f8fafc', 
              backgroundColor: '#38bdf8',
              padding: [4, 8],
              borderRadius: 4,
              position: 'insideEndTop',
              fontWeight: 600,
              fontSize: 11
            },
            data: [{ xAxis: baseline }]
          }
        }]
      }, true);
      
      // Click handler for watchlist bars
      charts.watchlist.off('click');
      charts.watchlist.on('click', params => {
        if (params.dataIndex != null && points[params.dataIndex]) {
            openDealerDossier(String(points[params.dataIndex].label));
        }
      });
      
      // Update pagination display
      document.getElementById('watchlistPageInfo').textContent = `Showing ${startIdx + 1}-${Math.min(endIdx, flagged.length)} of ${flagged.length}`;
      document.getElementById('watchlistPrevPage').disabled = page <= 1;
      document.getElementById('watchlistNextPage').disabled = page >= totalPages;
      document.getElementById('watchlistPrevPage').onclick = () => {
        currentPage = Math.max(1, currentPage - 1);
        renderWatchlist(rows);
      };
      document.getElementById('watchlistNextPage').onclick = () => {
        currentPage = Math.min(totalPages, currentPage + 1);
        renderWatchlist(rows);
      };
    }

    function renderTableWatchlist(rows) {
      const gameType = selectedGame;
      
      // In "Show All" mode, watchlist doesn't make sense - show message
      if (!gameType) {
        charts.tableWatchlist.clear();
        charts.tableWatchlist.setOption({
          graphic: [{ type: 'text', left: 'center', top: 'middle', style: { text: 'Select a game to view the slow table watchlist.', fill: theme.textColor, fontSize: 12 } }]
        });
        document.getElementById('tableWatchlistPageInfo').textContent = '';
        return;
      }
      
      const tableRows = rows.filter(row => row.TABLE_NO && num(row.AVG_TIMEDIFF) != null);
      const baseline = mean(tableRows.map(row => row.AVG_TIMEDIFF));
      const grouped = new Map();
      tableRows.forEach(row => {
        const table = String(row.TABLE_NO);
        if (!grouped.has(table)) grouped.set(table, []);
        grouped.get(table).push(num(row.AVG_TIMEDIFF));
      });
      const tableAvgs = [...grouped.entries()]
        .map(([table, values]) => ({ table, avg: mean(values) }))
        .filter(item => item.avg != null)
        .sort((a, b) => a.avg - b.avg);
      const slowDecileIndex = tableAvgs.length
        ? Math.max(0, Math.ceil(tableAvgs.length * 0.9) - 1)
        : -1;
      const slowDecileFloor = slowDecileIndex >= 0 ? tableAvgs[slowDecileIndex].avg : null;
      const flagged = tableAvgs.filter(item => {
        const delta = item.avg - baseline;
        return delta > 0 && (delta >= 1.5 || item.avg >= slowDecileFloor);
      }).sort((a, b) => b.avg - a.avg);
      
      // Pagination: show up to 20 tables per page
      const itemsPerPage = 20;
      const page = Math.max(1, Math.min(currentTablePage, Math.ceil(flagged.length / itemsPerPage) || 1));
      const startIdx = (page - 1) * itemsPerPage;
      const endIdx = startIdx + itemsPerPage;
      const pageFlagged = flagged.slice(startIdx, endIdx);
      const totalPages = Math.ceil(flagged.length / itemsPerPage) || 1;
      
      if (!flagged.length) {
        charts.tableWatchlist.clear();
        charts.tableWatchlist.setOption({
          graphic: [{ type: 'text', left: 'center', top: 'middle', style: { text: 'No tables meet the selected-game slow-pace thresholds.', fill: theme.textColor, fontSize: 12 } }]
        });
        document.getElementById('tableWatchlistPageInfo').textContent = '0 tables';
        return;
      }
      const points = pageFlagged.map(item => ({
        value: item.avg,
        label: item.table,
        delta: item.avg - baseline
      }));
      
      charts.tableWatchlist.setOption({
        tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' },
          formatter: params => {
            const point = points[params[0].dataIndex];
            return `<strong>Table ${escapeHtml(point.label)}</strong><br>Table average: ${fmt2(point.value)} s<br>${escapeHtml(gameType)} baseline: ${fmt2(baseline)} s<br>Slower than baseline: +${fmt2(point.delta)} s`;
          }
        },
        xAxis: { type: 'value', name: 'AVG_TIMEDIFF (s)', nameTextStyle: { color: theme.textColor, fontSize: 11 }, ...axisStyle },
        yAxis: { type: 'category', data: points.map(p => 'Table ' + p.label), inverse: true, axisLabel: { ...axisStyle.axisLabel, fontSize: 10 } },
        series: [{
          name: 'Slow Tables',
          type: 'bar',
          barWidth: '60%',
          itemStyle: {
            color: params => {
              const delta = points[params.dataIndex].delta;
              return delta >= 1.5 ? '#fb7185' : '#fbbf24';
            }
          },
          data: points.map(p => p.value),
          label: { show: true, position: 'right', color: theme.textColor, formatter: params => `${fmt2(params.value)} s`, fontSize: 10 },
          markLine: {
            symbol: ['none', 'none'],
            lineStyle: { color: '#38bdf8', type: 'dashed', width: 2 },
            label: { 
              formatter: `Baseline ${fmt2(baseline)} s`, 
              color: '#f8fafc', 
              backgroundColor: '#38bdf8',
              padding: [4, 8],
              borderRadius: 4,
              position: 'insideEndTop',
              fontWeight: 600,
              fontSize: 11
            },
            data: [{ xAxis: baseline }]
          }
        }]
      }, true);
      
      // Update pagination display
      document.getElementById('tableWatchlistPageInfo').textContent = `Showing ${startIdx + 1}-${Math.min(endIdx, flagged.length)} of ${flagged.length}`;
      document.getElementById('tableWatchlistPrevPage').disabled = page <= 1;
      document.getElementById('tableWatchlistNextPage').disabled = page >= totalPages;
      document.getElementById('tableWatchlistPrevPage').onclick = () => {
        currentTablePage = Math.max(1, currentTablePage - 1);
        renderTableWatchlist(rows);
      };
      document.getElementById('tableWatchlistNextPage').onclick = () => {
        currentTablePage = Math.min(totalPages, currentTablePage + 1);
        renderTableWatchlist(rows);
      };
    }

    function renderEfficiencyMatrix(rows) {
      const gameType = selectedGame;
      const color = currentGameColor(gameType);
      const points = summarizeProfiles(rows).filter(profile => profile.avg != null && profile.std != null);
      charts.efficiencyMatrix.setOption({
        color: [color],
        tooltip: {
          ...tooltipStyle,
          trigger: 'item',
          formatter: param => {
            const profile = param.data.profile;
            return `<strong>${escapeHtml(profile.label)}</strong><br>Dealer: ${safeCell(profile.dealer)}<br>Table No: ${safeCell(profile.tableNo)}<br>Game Type: ${escapeHtml(gameType)}<br>Avg Time: ${fmt2(profile.avg)} s<br>Std Dev: ${fmt2(profile.std)} s`;
          }
        },
        legend: { top: 0, data: [gameType], textStyle: { color: theme.textColor, fontSize: 11 } },
        grid: { left: 62, right: 22, top: 42, bottom: 54 },
        xAxis: { type: 'value', name: 'AVG_TIMEDIFF · Speed (s)', nameLocation: 'middle', nameGap: 30, nameTextStyle: { color: theme.textColor, fontSize: 11 }, ...axisStyle },
        yAxis: { type: 'value', name: 'STD_TIMEDIFF · Consistency (s)', nameTextStyle: { color: theme.textColor, fontSize: 11 }, ...axisStyle },
        series: [{
          name: gameType,
          type: 'scatter',
          symbolSize: 11,
          itemStyle: { color, opacity: 0.85, borderColor: '#0f172a', borderWidth: 1 },
          data: points.map(profile => ({
            value: [profile.avg, profile.std],
            symbol: profile.dealer && profile.tableNo ? 'circle' : profile.tableNo ? 'diamond' : 'circle',
            profile
          }))
        }]
      }, true);
      
      charts.efficiencyMatrix.off('click');
      charts.efficiencyMatrix.on('click', params => {
        if (params.data && params.data.profile) {
          const dealer = params.data.profile.dealer;
          const tableNo = params.data.profile.tableNo;
          if (dealer) {
            openDealerDossier(dealer);
          } else if (tableNo) {
            console.log('Clicked on table:', tableNo);
          }
        }
      });
    }

    function renderDealerTrend(rows) {
      const dealerRows = rows.filter(row => row.DEALER && row.BILLING_DATE && num(row.AVG_TIMEDIFF) != null);
      const gameType = selectedGame;
      const dates = [...new Set(dealerRows.map(row => String(row.BILLING_DATE)))].sort();
      const dailyValues = new Map();
      const dealerDaily = new Map();
      const dealerTotals = new Map();
      dealerRows.forEach(row => {
        const date = String(row.BILLING_DATE);
        const dealer = String(row.DEALER);
        if (!dailyValues.has(date)) dailyValues.set(date, []);
        dailyValues.get(date).push(num(row.AVG_TIMEDIFF));
        if (!dealerDaily.has(dealer)) dealerDaily.set(dealer, new Map());
        const valuesByDate = dealerDaily.get(dealer);
        if (!valuesByDate.has(date)) valuesByDate.set(date, []);
        valuesByDate.get(date).push(num(row.AVG_TIMEDIFF));
        if (!dealerTotals.has(dealer)) dealerTotals.set(dealer, []);
        dealerTotals.get(dealer).push(num(row.AVG_TIMEDIFF));
      });
      const rankedDealers = [...dealerTotals.entries()]
        .map(([dealer, values]) => ({ dealer, avg: mean(values) }))
        .filter(item => item.avg != null)
        .sort((a, b) => a.avg - b.avg);
      const chosen = new Map();
      rankedDealers.slice(0, 5).forEach(item => chosen.set(item.dealer, item));
      rankedDealers.slice(-5).forEach(item => chosen.set(item.dealer, item));
      const baselineColor = currentGameColor(gameType);
      const series = [{
        name: `${gameType} baseline`,
        type: 'line',
        data: dates.map(date => mean(dailyValues.get(date))),
        showSymbol: false,
        connectNulls: false,
        lineStyle: { color: '#f8fafc', width: 4 },
        itemStyle: { color: '#f8fafc' },
        emphasis: { focus: 'series' }
      }];
      [...chosen.values()].forEach((item, index) => {
        const daily = dealerDaily.get(item.dealer);
        series.push({
          name: item.dealer,
          type: 'line',
          data: dates.map(date => mean(daily.get(date) || [])),
          showSymbol: false,
          connectNulls: false,
          lineStyle: { color: palette[index % palette.length], width: 2 },
          itemStyle: { color: palette[index % palette.length] },
          emphasis: { focus: 'series' }
        });
      });
      charts.dealerTrend.setOption({
        color: [baselineColor, ...palette],
        tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'line' },
          formatter: params => [`<strong>${escapeHtml(params[0] ? params[0].axisValue : '')}</strong>`,
            ...params.filter(item => item.value != null).map(item => `${escapeHtml(item.seriesName)}: ${fmt2(item.value)} s`)].join('<br>') },
        legend: {
          type: 'scroll',
          top: 0,
          textStyle: { color: theme.textColor, fontSize: 10 },
          selected: Object.fromEntries(series.map(item => [item.name, item.name === `${gameType} baseline`]))
        },
        grid: { left: 60, right: 22, top: 54, bottom: 56 },
        xAxis: { type: 'category', boundaryGap: false, data: dates, ...axisStyle, axisLabel: { ...axisStyle.axisLabel, rotate: dates.length > 16 ? 35 : 0 } },
        yAxis: { type: 'value', name: 'AVG_TIMEDIFF (s)', nameTextStyle: { color: theme.textColor, fontSize: 11 }, ...axisStyle },
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 10 }],
        markLine: { data: [{ type: 'average' }] },
        series
      }, true);

      charts.dealerTrend.off('click');
      charts.dealerTrend.on('click', params => {
        if (params.seriesName && params.seriesName !== `${gameType} baseline`) {
          openDealerDossier(params.seriesName);
        }
      });
    }

    function renderPaceExtremes(rows) {
      const profiles = summarizeProfiles(rows).filter(profile => profile.avg != null)
        .map(profile => ({ ...profile, identity: `${profile.dealer}\u0000${profile.tableNo}` }))
        .sort((a, b) => a.avg - b.avg);
      const selected = new Map();
      profiles.slice(0, 10).forEach(profile => selected.set(profile.identity, { ...profile, kind: 'fastest' }));
      profiles.slice(-10).forEach(profile => {
        const previous = selected.get(profile.identity);
        selected.set(profile.identity, { ...profile, kind: previous ? 'both' : 'slowest' });
      });
      const entries = [...selected.values()];
      const labels = entries.map(profile => profile.label);
      charts.paceExtremes.setOption({
        tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' },
          formatter: params => {
            const profile = entries[params[0].dataIndex];
            return `<strong>${escapeHtml(profile.label)}</strong><br>Dealer: ${safeCell(profile.dealer)}<br>Table No: ${safeCell(profile.tableNo)}<br>Game Type: ${escapeHtml(selectedGame)}<br>Avg Time: ${fmt2(profile.avg)} s<br>Std Dev: ${fmt2(profile.std)} s`;
          }
        },
        grid: { left: 16, right: 62, top: 20, bottom: 12, containLabel: true },
        xAxis: { type: 'value', name: 'AVG_TIMEDIFF (s)', nameTextStyle: { color: theme.textColor, fontSize: 11 }, ...axisStyle },
        yAxis: { type: 'category', inverse: true, data: labels, ...axisStyle, axisLabel: { ...axisStyle.axisLabel, fontSize: 10 } },
        series: [{
          name: 'Average time',
          type: 'bar',
          barMaxWidth: 18,
          data: entries.map(profile => ({
            value: Number(profile.avg.toFixed(2)),
            itemStyle: {
              color: profile.kind === 'fastest' ? '#34d399' : profile.kind === 'slowest' ? '#fb7185' : '#fbbf24',
              borderRadius: [0, 4, 4, 0]
            }
          })),
          label: { show: true, position: 'right', color: theme.textColor, fontSize: 10, formatter: param => Number(param.value).toFixed(2) },
          markLine: {
            symbol: ['none', 'none'],
            lineStyle: { color: '#38bdf8', type: 'dashed', width: 2 },
            label: { 
              formatter: `Baseline ${fmt2(mean(entries.map(e => e.avg)))} s`, 
              color: '#f8fafc', 
              backgroundColor: '#38bdf8',
              padding: [4, 8],
              borderRadius: 4,
              position: 'insideEndTop',
              fontWeight: 600,
              fontSize: 11
            },
            data: [{ xAxis: mean(entries.map(e => e.avg)) }]
          }
        }]
      }, true);
      
      charts.paceExtremes.off('click');
      charts.paceExtremes.on('click', params => {
        if (params.dataIndex != null && entries[params.dataIndex]) {
          const profile = entries[params.dataIndex];
          if (profile.dealer) {
            openDealerDossier(profile.dealer);
          }
        }
      });
    }

    function renderForensics(rows) {
      const host = document.getElementById('forensicsTable');
      if (!host) return;
      if (!rows.length) {
        host.innerHTML = '<div class="table-empty">No telemetry records are available for this game.</div>';
        return;
      }
      const sortedRows = [...rows].sort((a, b) => String(b.BILLING_DATE || '').localeCompare(String(a.BILLING_DATE || '')));
      const body = sortedRows.map(row => `<tr>
        <td>${row.BILLING_DATE ? escapeHtml(row.BILLING_DATE) : 'N/A'}</td>
        <td>${row.GAME_TYPE ? escapeHtml(row.GAME_TYPE) : 'N/A'}</td>
        <td>${row.DEALER ? escapeHtml(row.DEALER) : 'N/A'}</td>
        <td>${row.TABLE_NO ? escapeHtml(row.TABLE_NO) : 'N/A'}</td>
        <td>${num(row.AVG_TIMEDIFF) != null ? Number(row.AVG_TIMEDIFF).toFixed(2) : 'N/A'}</td>
        <td>${num(row.STD_TIMEDIFF) != null ? Number(row.STD_TIMEDIFF).toFixed(2) : 'N/A'}</td>
      </tr>`).join('');
      host.innerHTML = `<table>
        <thead><tr><th>Billing Date</th><th>Game Type</th><th>Dealer</th><th>Table No</th><th>Avg Time (s)</th><th>Std Dev (s)</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
      <div class="table-empty">${rows.length.toLocaleString()} selected-game telemetry records.</div>`;
    }

    function renderDealerCardGrid(rows) {
      const host = document.getElementById('dealerCardGrid');
      const gameType = selectedGame;
      
      // Get filter values
      const filterBaseline = document.getElementById('filterBaseline').value;
      const filterMinDays = document.getElementById('filterMinDays').value;
      const filterWow = document.getElementById('filterWow').value;
      
      if (!gameType) {
        host.innerHTML = '<div class="table-empty" style="grid-column: 1/-1; text-align: center; padding: 20px;">Select a game to view dealer cards.</div>';
        return;
      }
      
      // Group by dealer
      const dealerMap = new Map();
      rows.filter(r => r.DEALER && num(r.AVG_TIMEDIFF) != null).forEach(row => {
        const dealer = String(row.DEALER);
        if (!dealerMap.has(dealer)) dealerMap.set(dealer, []);
        dealerMap.get(dealer).push(row);
      });
      
      // Calculate WoW for each dealer in this game
      const allDatesGame = [...new Set(rows.filter(r => r.DEALER).map(r => r.BILLING_DATE).filter(Boolean))].sort();
      const latestDateGame = allDatesGame[allDatesGame.length - 1];
      const latestDateObj = new Date(latestDateGame);
      const weekAgoDateObj = new Date(latestDateObj);
      weekAgoDateObj.setDate(weekAgoDateObj.getDate() - 7);
      const twoWeeksAgoDateObj = new Date(latestDateObj);
      twoWeeksAgoDateObj.setDate(twoWeeksAgoDateObj.getDate() - 14);
      const weekAgoStr = weekAgoDateObj.toISOString().split('T')[0];
      const twoWeeksAgoStr = twoWeeksAgoDateObj.toISOString().split('T')[0];
      
      const dealerStats = [...dealerMap.entries()].map(([dealer, dealerRows]) => {
        const avgTime = mean(dealerRows.map(r => r.AVG_TIMEDIFF));
        const stdTime = mean(dealerRows.map(r => r.STD_TIMEDIFF));
        const tables = [...new Set(dealerRows.map(r => r.TABLE_NO).filter(Boolean))];
        const days = [...new Set(dealerRows.map(r => r.BILLING_DATE).filter(Boolean))].length;
        const totalRecords = dealerRows.length;
        
        // WoW calculation
        let wow = null;
        if (days >= 14) {
          const recentRows = dealerRows.filter(r => r.BILLING_DATE > weekAgoStr && r.BILLING_DATE <= latestDateGame);
          const prevWeekRows = dealerRows.filter(r => r.BILLING_DATE > twoWeeksAgoStr && r.BILLING_DATE <= weekAgoStr);
          const recentAvg = mean(recentRows.map(r => r.AVG_TIMEDIFF));
          const prevWeekAvg = mean(prevWeekRows.map(r => r.AVG_TIMEDIFF));
          if (recentAvg != null && prevWeekAvg != null && recentRows.length > 0 && prevWeekRows.length > 0) {
            const diff = recentAvg - prevWeekAvg;
            const pct = ((diff / prevWeekAvg) * 100);
            wow = { diff, pct, recentAvg, prevWeekAvg, isWorse: diff > 0 };
          }
        }
        
        return { dealer, avgTime, stdTime, tables: tables.length, days, totalRecords, wow };
      }).sort((a, b) => (b.avgTime || 0) - (a.avgTime || 0)); // Slowest first
      
      // Apply filters
      let filteredStats = dealerStats;
      
      // Baseline filter
      if (filterBaseline) {
        const baseline = mean(dealerStats.map(d => d.avgTime).filter(v => v != null));
        if (filterBaseline === 'above') {
          filteredStats = filteredStats.filter(d => (d.avgTime || 0) > (baseline || 0));
        } else if (filterBaseline === 'below') {
          filteredStats = filteredStats.filter(d => (d.avgTime || 0) < (baseline || 0));
        }
      }
      
      // Min days filter
      if (filterMinDays) {
        const minDays = parseInt(filterMinDays);
        filteredStats = filteredStats.filter(d => d.days >= minDays);
      }
      
      // WoW filter
      if (filterWow) {
        if (filterWow === 'faster') {
          filteredStats = filteredStats.filter(d => d.wow && !d.wow.isWorse);
        } else if (filterWow === 'slower') {
          filteredStats = filteredStats.filter(d => d.wow && d.wow.isWorse);
        } else if (filterWow === 'no-data') {
          filteredStats = filteredStats.filter(d => !d.wow);
        }
      }
      
      if (!filteredStats.length) {
        host.innerHTML = '<div class="table-empty" style="grid-column: 1/-1; text-align: center; padding: 20px;">No dealers match the current filters.</div>';
        return;
      }
      
      const baseline = mean(dealerStats.map(d => d.avgTime).filter(v => v != null));
      
      host.innerHTML = filteredStats.map(d => {
        const isAbove = (d.avgTime || 0) > (baseline || 0);
        const wowHtml = d.wow 
          ? `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #253247; font-size: 10px; color: ${d.wow.isWorse ? '#fb7185' : '#34d399'};">
               Week-over-Week (WoW): ${d.wow.isWorse ? 'Slower' : 'Faster'} by ${Math.abs(d.wow.pct).toFixed(1)}% (${fmt2(d.wow.recentAvg)}s vs ${fmt2(d.wow.prevWeekAvg)}s)
             </div>`
          : '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #253247; font-size: 10px; color: #64748b;">Week-over-Week (WoW): Insufficient data</div>';
        
        return `
        <div class="card" style="padding: 12px; cursor: pointer; transition: background 0.15s;" 
             onmouseover="this.style.background='#17243a'" 
             onmouseout="this.style.background=''"
             onclick="openDealerDossier('${escapeHtml(d.dealer)}')">
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
            <strong style="font-size: 13px;">${escapeHtml(d.dealer)}</strong>
            <span style="font-size: 10px; color: ${isAbove ? '#fb7185' : '#34d399'};">
              ${isAbove ? '+' : ''}${fmt2((d.avgTime || 0) - (baseline || 0))}s vs baseline
            </span>
          </div>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11px;">
            <div><label style="color: #64748b;">Avg Pace</label><br><strong>${fmt2(d.avgTime)} s</strong></div>
            <div><label style="color: #64748b;">Consistency</label><br><strong>${fmt2(d.stdTime)} s</strong></div>
            <div><label style="color: #64748b;">Days Active</label><br><strong>${d.days}</strong></div>
            <div><label style="color: #64748b;">Tables</label><br><strong>${d.tables}</strong></div>
            <div><label style="color: #64748b;">Records</label><br><strong>${d.totalRecords}</strong></div>
          </div>
          ${wowHtml}
        </div>
        `;
      }).join('');
    }

    let currentDealer = null;
    let dealerDossierChart = null;

    function openDealerDossier(dealer) {
      currentDealer = dealer;
      document.getElementById('dealerDossierSection').style.display = 'block';
      
      // Build dealer game switcher
      const dealerId = String(dealer);
      const dealerGames = [...new Set(ROWS.filter(row => row.DEALER != null && String(row.DEALER) === dealerId).map(row => row.GAME_TYPE).filter(Boolean))].sort();
      
      // If current selectedGame doesn't have data for this dealer, switch to first available game
      if (selectedGame && !dealerGames.includes(selectedGame)) {
        selectedGame = dealerGames[0] || null;
        gameTagsContainer.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        if (selectedGame) {
          gameTagsContainer.querySelectorAll('button').forEach(b => { if (b.textContent === selectedGame) b.classList.add('active'); });
        }
      }
      
      const switcher = document.getElementById('dealerGameSwitcher');
      switcher.innerHTML = '';
      dealerGames.forEach(game => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = game;
        btn.style.cssText = 'padding: 4px 10px; border: 1px solid #344258; border-radius: 16px; background: #111b2d; color: #94a3b8; font-size: 11px; cursor: pointer; transition: all 0.15s;';
        if (game === selectedGame) {
          btn.style.background = '#1e3a5f';
          btn.style.borderColor = '#34d399';
          btn.style.color = '#34d399';
        }
        btn.addEventListener('click', () => {
          selectedGame = game;
          gameTagsContainer.querySelectorAll('button').forEach(b => b.classList.remove('active'));
          gameTagsContainer.querySelectorAll('button').forEach(b => { if (b.textContent === game) b.classList.add('active'); });
          switcher.querySelectorAll('button').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          render();
          openDealerDossier(dealer);
        });
        switcher.appendChild(btn);
      });
      
      // Add "Show All" button
      const showAllBtn = document.createElement('button');
      showAllBtn.type = 'button';
      showAllBtn.textContent = 'Show All';
      showAllBtn.className = 'game-switcher-btn';
      showAllBtn.addEventListener('click', () => {
        selectedGame = null;
        gameTagsContainer.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        switcher.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        showAllBtn.classList.add('active');
        render();
        openDealerDossier(dealer);
      });
      switcher.appendChild(showAllBtn);
      
      // Render dealer KPIs
      const dealerRows = ROWS.filter(row => row.DEALER != null && String(row.DEALER) === dealerId && (selectedGame == null || row.GAME_TYPE === selectedGame));
      const dealerTables = [...new Set(dealerRows.map(row => row.TABLE_NO).filter(Boolean))];
      const dealerGameTypes = [...new Set(dealerRows.map(row => row.GAME_TYPE).filter(Boolean))];
      const avgTime = mean(dealerRows.map(row => row.AVG_TIMEDIFF));
      const stdTime = mean(dealerRows.map(row => row.STD_TIMEDIFF));
      const totalDays = [...new Set(dealerRows.map(row => row.BILLING_DATE).filter(Boolean))].length;
      
      // Week-over-week comparison
      const allDates = [...new Set(dealerRows.map(row => row.BILLING_DATE).filter(Boolean))].sort();
      let wowHtml = '';
      if (allDates.length >= 7) {
        const latestDate = allDates[allDates.length - 1];
        const latestDateObj = new Date(latestDate);
        const weekAgoDateObj = new Date(latestDateObj);
        weekAgoDateObj.setDate(weekAgoDateObj.getDate() - 7);
        const twoWeeksAgoDateObj = new Date(latestDateObj);
        twoWeeksAgoDateObj.setDate(twoWeeksAgoDateObj.getDate() - 14);
        
        const weekAgoStr = weekAgoDateObj.toISOString().split('T')[0];
        const twoWeeksAgoStr = twoWeeksAgoDateObj.toISOString().split('T')[0];
        
        const recentRows = dealerRows.filter(r => r.BILLING_DATE > weekAgoStr && r.BILLING_DATE <= latestDate);
        const prevWeekRows = dealerRows.filter(r => r.BILLING_DATE > twoWeeksAgoStr && r.BILLING_DATE <= weekAgoStr);
        
        const recentAvg = mean(recentRows.map(r => r.AVG_TIMEDIFF));
        const prevWeekAvg = mean(prevWeekRows.map(r => r.AVG_TIMEDIFF));
        
        if (recentAvg != null && prevWeekAvg != null && recentRows.length > 0 && prevWeekRows.length > 0) {
          const diff = recentAvg - prevWeekAvg;
          const pct = ((diff / prevWeekAvg) * 100).toFixed(1);
          const isWorse = diff > 0; // Higher time = slower = worse
          const color = isWorse ? '#fb7185' : '#34d399';
          const label = isWorse ? 'Slower' : 'Faster';
          wowHtml = `
            <div class="card kpi" style="padding: 12px; border-left: 3px solid ${color};">
              <label>Week-over-Week (WoW)</label>
              <strong style="color: ${color};">${label} by ${Math.abs(pct)}%</strong>
              <span class="sub">${fmt2(recentAvg)}s vs ${fmt2(prevWeekAvg)}s (${recentRows.length} vs ${prevWeekRows.length} records)</span>
            </div>
          `;
        }
      }
      
      document.getElementById('dealerDossierKpis').innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
          <div class="card kpi" style="padding: 12px;">
            <label>Avg Pace</label>
            <strong>${fmt2(avgTime)} s</strong>
            <span class="sub">${dealerGameTypes.length} game(s)</span>
          </div>
          <div class="card kpi" style="padding: 12px;">
            <label>Consistency (Std Dev)</label>
            <strong>${fmt2(stdTime)} s</strong>
            <span class="sub">${totalDays} active day(s)</span>
          </div>
          <div class="card kpi" style="padding: 12px;">
            <label>Tables Worked</label>
            <strong>${dealerTables.length}</strong>
            <span class="sub">${dealerRows.length} records</span>
          </div>
        </div>
        ${wowHtml ? `<div style="display: grid; grid-template-columns: 1fr; gap: 12px; margin-bottom: 12px;">${wowHtml}</div>` : ''}
        <div style="color: #94a3b8; font-size: 12px; margin-bottom: 8px;">
          Dealer: <strong>${escapeHtml(dealer)}</strong> ${selectedGame ? `· Game: <strong>${escapeHtml(selectedGame)}</strong>` : '· All Games'}
        </div>
      `;
      
      // Render dealer trend chart
      const dealerTrendContainer = document.getElementById('dealerDossierTrend');
      if (!dealerDossierChart) dealerDossierChart = echarts.init(dealerTrendContainer);
      
      const dates = [...new Set(dealerRows.map(row => String(row.BILLING_DATE)))].sort();
      const dailyValues = new Map();
      dealerRows.forEach(row => {
        const date = String(row.BILLING_DATE);
        if (!dailyValues.has(date)) dailyValues.set(date, []);
        dailyValues.get(date).push(num(row.AVG_TIMEDIFF));
      });
      
      // Calculate baseline for this dealer (or game if Show All)
      const dealerBaseline = selectedGame 
        ? mean(ROWS.filter(r => r.GAME_TYPE === selectedGame && r.DEALER && num(r.AVG_TIMEDIFF) != null).map(r => r.AVG_TIMEDIFF))
        : mean(dealerRows.map(row => row.AVG_TIMEDIFF));
      
      dealerDossierChart.setOption({
        color: [currentGameColor(selectedGame || dealerGameTypes[0] || '')],
        tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'line' },
          formatter: params => [`<strong>${escapeHtml(params[0] ? params[0].axisValue : '')}</strong>`,
            ...params.filter(item => item.value != null).map(item => `${escapeHtml(item.seriesName)}: ${fmt2(item.value)} s`)].join('<br>') },
        grid: { left: 50, right: 20, top: 30, bottom: 50 },
        xAxis: { type: 'category', boundaryGap: false, data: dates, ...axisStyle, axisLabel: { ...axisStyle.axisLabel, rotate: dates.length > 16 ? 35 : 0, fontSize: 10 } },
        yAxis: { type: 'value', name: 'AVG_TIMEDIFF (s)', nameTextStyle: { color: theme.textColor, fontSize: 11 }, ...axisStyle },
        series: [{
          name: 'Avg Time',
          type: 'line',
          data: dates.map(date => mean(dailyValues.get(date))),
          showSymbol: true,
          symbolSize: 6,
          connectNulls: false,
          lineStyle: { width: 2 },
          emphasis: { focus: 'series' },
          markLine: {
            symbol: ['none', 'none'],
            lineStyle: { color: '#38bdf8', type: 'dashed', width: 2 },
            label: { 
              formatter: `Baseline ${fmt2(dealerBaseline)} s`, 
              color: '#f8fafc', 
              backgroundColor: '#38bdf8',
              padding: [4, 8],
              borderRadius: 4,
              position: 'insideEndTop',
              fontWeight: 600,
              fontSize: 11
            },
            data: [{ yAxis: dealerBaseline }]
          }
        }]
      }, true);
      
      // Scroll to dossier
      dealerDossierChart.resize();
      document.getElementById('dealerDossierSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function render() {
      const rows = selectedRows();
      renderKpis(rows);
      renderWatchlist(rows);
      renderTableWatchlist(rows);
      renderEfficiencyMatrix(rows);
      renderDealerTrend(rows);
      renderPaceExtremes(rows);
      renderDealerCardGrid(rows);
      renderForensics(rows);
    }

    const gameTypes = [...new Set(ROWS.map(row => row.GAME_TYPE).filter(game => typeof game === 'string' && game))].sort();
    gameTypes.forEach(game => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = game;
      btn.addEventListener('click', () => {
        selectedGame = game;
        gameTagsContainer.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        render();
      });
      gameTagsContainer.appendChild(btn);
    });
    if (gameTypes.length) {
      selectedGame = gameTypes[0];
      gameTagsContainer.querySelector('button').classList.add('active');
    }
    render();
    
    // Dealer card grid filters
    document.getElementById('filterBaseline').addEventListener('change', render);
    document.getElementById('filterMinDays').addEventListener('change', render);
    document.getElementById('filterWow').addEventListener('change', render);
    document.getElementById('clearFilters').addEventListener('click', () => {
      document.getElementById('filterBaseline').value = '';
      document.getElementById('filterMinDays').value = '';
      document.getElementById('filterWow').value = '';
      render();
    });

    let resizePending = false;
    function resizeCharts() {
      if (resizePending) return;
      resizePending = true;
      requestAnimationFrame(() => {
        allCharts.forEach(chart => chart.resize());
        if (dealerDossierChart) dealerDossierChart.resize();
        resizePending = false;
      });
    }
    window.addEventListener('resize', resizeCharts);
    if ('ResizeObserver' in window) {
      const layoutObserver = new ResizeObserver(resizeCharts);
      layoutObserver.observe(document.querySelector('main'));
    }
  </script>
</body>
</html>
"""
    return template.replace("__PAYLOAD__", payload)


def build_dashboard():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Combined pace data payload not found: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as source:
        data = json.load(source)

    html = render_dashboard(data)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as output:
        output.write(html)
    print(f"Generated {OUT_FILE} ({len(html):,} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_dashboard())
