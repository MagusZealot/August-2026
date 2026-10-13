#!/usr/bin/env python3
"""Generate the standalone round dealer time dashboard."""
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

WORKSPACE = Path(WORKSPACE)
DATA_FILE = WORKSPACE / "output" / "round_dealer_time_data.json"
OUT_FILE = WORKSPACE / "output" / "dashboards" / "round_dealer_time_dashboard.html"


def build_dashboard():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Round dealer time data payload not found: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as source:
        data = json.load(source)

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    template = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Round Dealer Time & Shift Performance Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    :root { color-scheme: dark; font-family: Inter, "Segoe UI", sans-serif; background: #090e1a; color: #e2e8f0; }
    * { box-sizing: border-box; }
    body { margin: 0; min-width: 320px; background: radial-gradient(ellipse at top, #14213a 0, #090e1a 55%); }
    header { position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; padding: 16px max(20px, calc((100vw - 1480px) / 2)); background: #0b1220ed; border-bottom: 1px solid #253247; backdrop-filter: blur(12px); }
    h1 { margin: 0; font-size: clamp(18px, 2.4vw, 26px); letter-spacing: .02em; }
    header p { margin: 5px 0 0; color: #93a4bc; font-size: 12px; }
    nav { display: flex; flex-wrap: wrap; gap: 8px; }
    nav a { padding: 9px 12px; border: 1px solid #344258; border-radius: 9px; color: #b9c7da; text-decoration: none; font-size: 12px; background: #111b2d; }
    nav a:hover { border-color: #34d399; color: #6ee7b7; }
    main { max-width: 1480px; margin: auto; padding: 22px; }
    .hero { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
    .hero h2 { margin: 0; font-size: 18px; }
    .hero p, .muted { color: #94a3b8; font-size: 12px; }
    .filters { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; }
    select, input[type="date"] { padding: 9px 12px; border: 1px solid #344258; border-radius: 8px; background: #111b2d; color: #e2e8f0; font-family: inherit; font-size: 12px; }
    .kpis { display: grid; grid-template-columns: repeat(5, minmax(130px, 1fr)); gap: 12px; margin-bottom: 16px; }
    .card { border: 1px solid #24334a; border-radius: 14px; background: linear-gradient(145deg, #121d30e8, #0c1423f2); box-shadow: 0 10px 30px #0002; }
    .kpi { padding: 16px; }
    .kpi label { display: block; margin-bottom: 8px; color: #91a2ba; font-size: 10px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
    .kpi strong { font: 700 21px ui-monospace, Consolas, monospace; color: #f8fafc; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .chart-card { min-width: 0; padding: 15px; }
    .chart-card h3 { margin: 0 0 3px; font-size: 14px; }
    .chart { width: 100%; height: 350px; }
    .wide { grid-column: 1 / -1; }
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; white-space: nowrap; font-size: 12px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #253247; text-align: right; }
    th { color: #90a3bd; font-size: 10px; text-transform: uppercase; letter-spacing: .06em; }
    td:first-child, th:first-child { text-align: left; }
    .table-total td { color: #f8fafc; font-weight: 700; background: #16213a80; }
    .game-sections { display: contents; }
    .grid.nested { margin-top: 12px; }
    .alert { margin: 14px 0; padding: 12px 15px; border: 1px solid #854d0e; border-radius: 10px; background: #713f121f; color: #fcd34d; font-size: 12px; }
    .alert.good { border-color: #166534; background: #14532d22; color: #86efac; }
    .date-range-reset { padding: 9px 12px; border: 1px solid #344258; border-radius: 8px; background: #111b2d; color: #b9c7da; font-size: 12px; cursor: pointer; transition: all .15s ease; }
    .date-range-reset:hover { border-color: #fb7185; color: #fda4af; }
    footer { padding: 22px 0 8px; color: #77869c; font-size: 11px; }
    @media (max-width: 900px) { .kpis { grid-template-columns: repeat(3, 1fr); } .grid { grid-template-columns: 1fr; } .wide { grid-column: auto; } }
    @media (max-width: 560px) { main { padding: 14px; } .kpis { grid-template-columns: repeat(2, 1fr); } .chart { height: 300px; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1><i class="fa-solid fa-clock" style="color:#34d399"></i> Round Dealer Time & Shift Performance</h1>
      <p id="feedStatus">Loading latest dealer time feed…</p>
    </div>
    <nav aria-label="Dashboards">
      <a href="bi_dashboard.html"><i class="fa-solid fa-chart-line"></i> BI Console</a>
      <a href="player_behavior_dashboard.html"><i class="fa-solid fa-gamepad"></i> Player Behavior</a>
    </nav>
  </header>
  <main>
    <section class="hero">
      <div>
        <h2>Every game at a glance: combined trends and per-game detail</h2>
        <p>Percent values follow the source feed. Shift breaches are actual duration above threshold.</p>
      </div>
      <div class="filters">
        <label class="muted" for="periodFilter">Trend window<br><select id="periodFilter"><option value="90">Latest 90 days</option><option value="365">Latest 365 days</option><option value="all">All available dates</option></select></label>
        <label class="muted" for="startDate">Start date<br><input type="date" id="startDate"></label>
        <label class="muted" for="endDate">End date<br><input type="date" id="endDate"></label>
        <button type="button" class="date-range-reset" id="resetDateRange" title="Clear the date range and fall back to the trend window"><i class="fa-solid fa-rotate-left"></i> Reset range</button>
      </div>
    </section>
    <div id="coverageAlert"></div>
    <section id="kpis" class="kpis"></section>
    <section class="grid">
      <article class="card chart-card wide" id="combinedPanel">
        <h3>Combined Summary — all games</h3>
        <div class="muted" id="combinedNote">Pooled daily means across every game type · follows the trend window and date range</div>
      </article>
      <article class="card chart-card"><h3>Overall duration trend — all games</h3><div class="muted">Pooled daily mean actual vs expected round duration</div><div id="combinedDuration" class="chart"></div></article>
      <article class="card chart-card"><h3>Overall win probability and threshold trend — all games</h3><div class="muted">Pooled daily mean actual vs expected wins and threshold</div><div id="combinedWin" class="chart"></div></article>
      <article class="card chart-card"><h3>Average actual vs expected duration by game</h3><div class="muted" id="durationCompareNote">Daily bet-place records pooled across the selected history</div><div id="durationCompare" class="chart"></div></article>
      <article class="card chart-card"><h3>Wins vs expected wins and threshold</h3><div class="muted" id="winCompareNote">Compare the observed wins with the model and configured limit</div><div id="winCompare" class="chart"></div></article>
      <div class="game-sections" id="gameSections"></div>
      <article class="card chart-card wide"><h3>Latest bet-place relationship: actual duration vs actual wins</h3><div class="muted">Each point is a bet place on the latest billing date; triangles indicate duration above threshold</div><div id="relationship" class="chart"></div></article>
      <article class="card chart-card wide"><h3>Game type summary</h3><div class="table-wrap"><table><thead><tr><th>Game</th><th>Days</th><th>HE rows</th><th>Actual Duration</th><th>Expected Duration</th><th>Duration delta</th><th>Actual Wins</th><th>Expected Wins</th><th>Win delta</th><th>Threshold</th><th>Breach rows %</th></tr></thead><tbody id="summaryRows"></tbody></table></div></article>
    </section>
    <footer>Source: daily published CSV snapshots. Missing dates are retained as gaps; no metric is interpolated. Refresh this dashboard by running the dashboard pipeline.</footer>
  </main>
  <script id="round-dealer-time-data" type="application/json">__PAYLOAD__</script>
  <script>
    const DATA = JSON.parse(document.getElementById('round-dealer-time-data').textContent);
    const colors = ['#38bdf8','#34d399','#fbbf24','#c084fc','#fb7185','#2dd4bf','#a3e635','#f97316'];
    const chartIds = ['durationCompare','winCompare','combinedDuration','combinedWin','relationship'];
    const charts = Object.fromEntries(chartIds.map(id => [id, echarts.init(document.getElementById(id))]));
    const gameCharts = [];
    const number = value => value == null ? '—' : `${Number(value).toFixed(2)}h`;
    const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&', '<': '<', '>': '>', '"': '"', "'": '''
    }[character]));
    const pair = (object, key) => object && object[key] || [];
    const axisStyle = { axisLabel: { color: '#94a3b8' }, axisLine: { lineStyle: { color: '#334155' } }, splitLine: { lineStyle: { color: '#253247', type: 'dashed' } } };
    const tooltipStyle = { backgroundColor: '#0f172a', borderColor: '#334155', textStyle: { color: '#f8fafc' } };
    const trendCommon = {
      tooltip: { ...tooltipStyle, trigger: 'axis' }, legend: { textStyle: { color: '#cbd5e1' } },
      grid: { left: 58, right: 20, top: 45, bottom: 38 },
      xAxis: { type: 'time', ...axisStyle }, yAxis: { type: 'value', ...axisStyle },
      dataZoom: [
        { type: 'inside' },
        { type: 'slider', height: 14, bottom: 4, borderColor: '#334155', textStyle: { color: '#94a3b8', fontSize: 8 } }
      ]
    };
    const types = DATA.game_types || [];

    function renderKpis() {
      const m = DATA.meta;
      const tiles = [
        ['Latest snapshot', m.latest_file_date],
        ['Billing date range', `${m.billing_date_min} – ${m.billing_date_max}`],
        ['Game types', m.game_types.length],
        ['Bet places', m.bet_places_tracked],
        ['Missing snapshots', m.files_missing_count]
      ];
      document.getElementById('kpis').innerHTML = tiles.map(([label, value]) => `<div class="card kpi"><label>${escapeHtml(label)}</label><strong>${escapeHtml(value)}</strong></div>`).join('');
      document.getElementById('feedStatus').textContent = `Updated ${m.generated_at} · ${Number(m.files_available).toLocaleString()} snapshots · ${Number(m.unique_keys).toLocaleString()} unique daily bet-place records`;
      const gaps = DATA.missing_dates || [];
      document.getElementById('coverageAlert').innerHTML = gaps.length
        ? `<div class="alert"><strong>${gaps.length} missing snapshot dates</strong> after the first published file. Missing days are excluded from averages and shown as a coverage gap. Recent gaps: ${gaps.slice(-8).map(escapeHtml).join(', ')}</div>`
        : '<div class="alert good">No missing snapshot dates are currently recorded after feed start.</div>';
      document.getElementById('summaryRows').innerHTML = types.map(game => `<tr>
        <td>${escapeHtml(game.game_type)}</td><td>${game.days}</td><td>${game.dur_rows}</td>
        <td>${number(game.mean_actual_duration)}</td><td>${number(game.mean_expected_duration)}</td><td>${number(game.mean_duration_delta)}</td>
        <td>${number(game.mean_actual_wins)}</td><td>${number(game.mean_expected_wins)}</td><td>${number(game.mean_win_delta)}</td><td>${Number(game.breach_pct).toFixed(2)}%</td>
      </tr>`).join('');
    }

    function getDateRange() {
      const start = document.getElementById('startDate').value;
      const end = document.getElementById('endDate').value;
      return { start: start || null, end: end || null };
    }

    function inDateRange(day) {
      const { start, end } = getDateRange();
      if (start && day < start) return false;
      if (end && day > end) return false;
      return true;
    }

    function inTimeframe(day) {
      if (!inDateRange(day)) return false;
      const days = document.getElementById('periodFilter').value;
      if (days !== 'all') {
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - Number(days));
        if (new Date(`${day}T00:00:00`) < cutoff) return false;
      }
      return true;
    }

    function timeframeSeries(seriesByGame, game) {
      return pair(seriesByGame, game).filter(([day]) => inTimeframe(day));
    }

    function timeframeMean(seriesByGame, game) {
      const values = timeframeSeries(seriesByGame, game).map(([, value]) => value).filter(value => value != null);
      return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
    }

    function comparisonValues(seriesKey, meanKey) {
      const { start, end } = getDateRange();
      const precomputed = () => types.map(game => game[meanKey]);
      if (!start && !end) return precomputed();
      return types.map(game => {
        const values = pair(DATA[seriesKey], game.game_type).filter(([day]) => inDateRange(day)).map(([, value]) => value).filter(value => value != null);
        return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
      });
    }

    function updateComparisonNotes() {
      const { start, end } = getDateRange();
      const suffix = (start || end) ? ` · ${start || '…'} to ${end || '…'}` : '';
      document.getElementById('durationCompareNote').textContent = `Daily bet-place records pooled across the selected history${suffix}`;
      document.getElementById('winCompareNote').textContent = `Compare the observed wins with the model and configured limit${suffix}`;
    }

    function renderGameComparisons() {
      const names = types.map(game => game.game_type);
      charts.durationCompare.setOption({
        color: ['#38bdf8','#fbbf24'], tooltip: { ...tooltipStyle, trigger: 'axis' }, legend: { textStyle: { color: '#cbd5e1' } },
        grid: { left: 55, right: 18, top: 38, bottom: 72 },
        xAxis: { type: 'category', data: names, axisLabel: { ...axisStyle.axisLabel, rotate: 25 } }, yAxis: { type: 'value', name: 'Duration (h)', ...axisStyle },
        series: [
          { name: 'Actual duration', type: 'bar', data: comparisonValues('series_duration', 'mean_actual_duration'), itemStyle: { borderRadius: [4,4,0,0] } },
          { name: 'Expected duration', type: 'bar', data: comparisonValues('series_expected_duration', 'mean_expected_duration'), itemStyle: { borderRadius: [4,4,0,0] } }
        ]
      });
      charts.winCompare.setOption({
        color: ['#38bdf8','#a78bfa','#fb7185'], tooltip: { ...tooltipStyle, trigger: 'axis' }, legend: { textStyle: { color: '#cbd5e1' } },
        grid: { left: 55, right: 18, top: 38, bottom: 72 },
        xAxis: { type: 'category', data: names, axisLabel: { ...axisStyle.axisLabel, rotate: 25 } }, yAxis: { type: 'value', name: 'Wins', ...axisStyle },
        series: [
          { name: 'Actual wins', type: 'bar', data: comparisonValues('series_actual_wins', 'mean_actual_wins'), itemStyle: { borderRadius: [4,4,0,0] } },
          { name: 'Expected wins', type: 'bar', data: comparisonValues('series_expected_wins', 'mean_expected_wins'), itemStyle: { borderRadius: [4,4,0,0] } },
          { name: 'Threshold', type: 'bar', data: comparisonValues('series_threshold', 'mean_threshold'), itemStyle: { borderRadius: [4,4,0,0] } }
        ]
      });
      updateComparisonNotes();
    }

    function renderCombinedSummary() {
      const rows = (DATA.daily || []).filter(row => inTimeframe(row.date));
      const totalRows = types.reduce((sum, game) => sum + (game.dur_rows || 0), 0);
      const totalBreaches = types.reduce((sum, game) => sum + (game.breaches || 0), 0);
      const pooledBreach = totalRows ? (totalBreaches / totalRows * 100) : null;
      const { start, end } = getDateRange();
      const suffix = (start || end) ? ` · ${start || '…'} to ${end || '…'}` : '';
      document.getElementById('combinedNote').textContent =
        `${types.length} game types · ${(DATA.bet_places || []).length} bet places · ${Number(totalRows).toLocaleString()} pooled rows · pooled breach rate ${pooledBreach == null ? '—' : `${pooledBreach.toFixed(2)}%`} · ${rows.length} days in view${suffix}`;
      charts.combinedDuration.setOption({
        ...trendCommon, yAxis: { ...trendCommon.yAxis, name: 'Duration (h)' },
        series: [
          { name: 'Actual duration', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.mean_actual_duration]), lineStyle: { width: 2 }, itemStyle: { color: '#38bdf8' } },
          { name: 'Expected duration', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.mean_expected_duration]), lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#fbbf24' } }
        ]
      }, true);
      charts.combinedWin.setOption({
        ...trendCommon, yAxis: { ...trendCommon.yAxis, name: 'Wins' },
        series: [
          { name: 'Actual wins', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.mean_actual_wins]), lineStyle: { width: 2 }, itemStyle: { color: '#38bdf8' } },
          { name: 'Expected wins', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.mean_expected_wins]), lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#a78bfa' } },
          { name: 'Threshold', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.mean_threshold]), lineStyle: { width: 2, type: 'dotted' }, itemStyle: { color: '#fb7185' } }
        ]
      }, true);
    }

    function buildGameSections() {
      const container = document.getElementById('gameSections');
      const fragment = document.createDocumentFragment();
      types.forEach((game, index) => {
        const article = document.createElement('article');
        article.className = 'card chart-card wide';
        article.innerHTML = `
          <h3>${escapeHtml(game.game_type)}</h3>
          <div class="muted" id="gameMeta-${index}"></div>
          <div class="table-wrap"><table>
            <thead><tr><th>Bet place</th><th>Days</th><th>Actual Duration</th><th>Expected Duration</th><th>Duration delta</th><th>Actual Wins</th><th>Expected Wins</th><th>Win delta</th><th>Threshold</th><th>Breach rows %</th></tr></thead>
            <tbody id="gameRows-${index}"></tbody>
          </table></div>
          <div class="grid nested">
            <article class="card chart-card"><h3>Duration trend — ${escapeHtml(game.game_type)}</h3><div class="muted">Daily actual and expected round duration · honours the trend window and date range</div><div id="gameDur-${index}" class="chart"></div></article>
            <article class="card chart-card"><h3>Wins and threshold trend — ${escapeHtml(game.game_type)}</h3><div class="muted">Daily average wins and threshold · honours the trend window and date range</div><div id="gameWin-${index}" class="chart"></div></article>
          </div>`;
        fragment.appendChild(article);
      });
      container.appendChild(fragment);
      types.forEach((game, index) => {
        gameCharts.push({
          dur: echarts.init(document.getElementById(`gameDur-${index}`)),
          win: echarts.init(document.getElementById(`gameWin-${index}`))
        });
      });
    }

    function renderGameSections() {
      types.forEach((game, index) => {
        const name = game.game_type;
        const daysInRange = timeframeSeries(DATA.series_duration, name).length;
        const actualDur = timeframeMean(DATA.series_duration, name);
        const expectedDur = timeframeMean(DATA.series_expected_duration, name);
        const actualWin = timeframeMean(DATA.series_actual_wins, name);
        const expectedWin = timeframeMean(DATA.series_expected_wins, name);
        const threshold = timeframeMean(DATA.series_threshold, name);
        const breach = timeframeMean(DATA.series_breach, name);
        document.getElementById(`gameMeta-${index}`).textContent =
          `${Number(game.rows).toLocaleString()} rows · ${game.days} days on record · ${game.first_date} – ${game.last_date} · ${game.bet_places} bet places · the game row follows the trend window and date range; bet-place rows are full-history pooled means`;
        const rows = [`<tr class="table-total"><td>${escapeHtml(name)} — all bet places</td><td>${daysInRange}</td><td>${number(actualDur)}</td><td>${number(expectedDur)}</td><td>${number(actualDur != null && expectedDur != null ? actualDur - expectedDur : null)}</td><td>${number(actualWin)}</td><td>${number(expectedWin)}</td><td>${number(win_delta != null ? win_delta : null)}</td><td>${number(threshold)}</td><td>${breach == null ? `${Number(game.breach_pct).toFixed(2)}%` : `${breach.toFixed(2)}%`}</td></tr>`];
        for (const place of (DATA.bet_places || []).filter(entry => entry.game_type === name)) {
          rows.push(`<tr>
            <td>${escapeHtml(place.bet_place)}</td><td>${place.days}</td>
            <td>${number(place.mean_actual_duration)}</td><td>${number(place.mean_expected_duration)}</td><td>${number(place.mean_duration_delta)}</td>
            <td>${number(place.mean_actual_wins)}</td><td>${number(place.mean_expected_wins)}</td><td>${number(place.mean_win_delta)}</td><td>${Number(place.breach_pct).toFixed(2)}%</td>
          </tr>`);
        }
        document.getElementById(`gameRows-${index}`).innerHTML = rows.join('');
        const line = (seriesByGame, label, color, dash) => ({
          name: label, type: 'line', showSymbol: false, smooth: true, connectNulls: false,
          data: timeframeSeries(seriesByGame, name).map(([day, value]) => [day, value]),
          itemStyle: { color }, lineStyle: dash ? { width: 2, type: dash } : { width: 2 }
        });
        gameCharts[index].dur.setOption({
          ...trendCommon, yAxis: { ...trendCommon.yAxis, name: 'Duration (h)' },
          series: [ line(DATA.series_duration, 'Actual duration', '#38bdf8'), line(DATA.series_expected_duration, 'Expected duration', '#fbbf24', 'dashed') ]
        }, true);
        gameCharts[index].win.setOption({
          ...trendCommon, yAxis: { ...trendCommon.yAxis, name: 'Wins' },
          series: [
            line(DATA.series_actual_wins, 'Actual wins', '#38bdf8'),
            line(DATA.series_expected_wins, 'Expected wins', '#a78bfa', 'dashed'),
            line(DATA.series_threshold, 'Threshold', '#fb7185', 'dotted')
          ]
        }, true);
      });
    }

    function renderRelationship() {
      const latest = DATA.latest_day;
      const rows = latest.rows || [];
      const groups = [...new Set(rows.filter(row => row.actual_duration != null && row.actual_wins != null).map(row => row.game_type))];
      charts.relationship.setOption({
        color: colors, tooltip: {
          ...tooltipStyle, formatter: point => {
            const row = point.data.row;
            return `<strong>${escapeHtml(row.game_type)}</strong><br>${escapeHtml(row.bet_place)}<br>Actual duration: ${number(row.actual_duration)}<br>Actual wins: ${number(row.actual_wins)}<br>Threshold: ${number(row.threshold)}<br>${row.shift_breach ? 'Above threshold' : 'At/below threshold'}`;
          }
        },
        legend: { data: groups, textStyle: { color: '#cbd5e1' } },
        grid: { left: 65, right: 24, top: 42, bottom: 48 },
        xAxis: { type: 'value', name: 'Actual duration (h)', ...axisStyle },
        yAxis: { type: 'value', name: 'Actual wins', ...axisStyle },
        series: groups.map(game => ({
          name: game, type: 'scatter', symbolSize: 11,
          data: rows.filter(row => row.game_type === game && row.actual_duration != null && row.actual_wins != null).map(row => ({
            value: [row.actual_duration, row.actual_wins],
            symbol: row.shift_breach ? 'triangle' : 'circle',
            row
          }))
        }))
      }, true);
      document.querySelector('#relationship').previousElementSibling.textContent =
        `Each point is a bet place on ${latest.billing_date}; triangles indicate duration above threshold`;
    }

    function render() {
      renderCombinedSummary();
      renderGameComparisons();
      renderGameSections();
      renderRelationship();
    }

    function initDateRangeBounds() {
      const dates = [...Object.values(DATA.series_duration || {}), ...Object.values(DATA.series_expected_duration || {}),
                     ...Object.values(DATA.series_actual_wins || {}), ...Object.values(DATA.series_expected_wins || {}),
                     ...Object.values(DATA.series_threshold || {})].flat().map(([day]) => day).sort();
      const min = DATA.meta.billing_date_min || dates[0] || '';
      const max = DATA.meta.billing_date_max || dates[dates.length - 1] || '';
      const startInput = document.getElementById('startDate');
      const endInput = document.getElementById('endDate');
      for (const input of [startInput, endInput]) {
        input.min = min;
        input.max = max;
      }
      return { min, max };
    }

    function resetDateRange() {
      document.getElementById('startDate').value = '';
      document.getElementById('endDate').value = '';
      render();
    }

    const allCharts = () => [...Object.values(charts), ...gameCharts.flatMap(entry => [entry.dur, entry.win])];

    renderKpis();
    initDateRangeBounds();
    buildGameSections();
    render();
    document.getElementById('periodFilter').addEventListener('change', render);
    document.getElementById('startDate').addEventListener('change', render);
    document.getElementById('endDate').addEventListener('change', render);
    document.getElementById('resetDateRange').addEventListener('click', resetDateRange);
    window.addEventListener('resize', () => allCharts().forEach(chart => chart.resize()));
  </script>
</body>
</html>
"""
    html = template.replace("__PAYLOAD__", payload)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as output:
        output.write(html)
    print(f"Generated {OUT_FILE} ({len(html):,} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_dashboard())