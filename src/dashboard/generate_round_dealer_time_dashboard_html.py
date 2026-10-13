#!/usr/bin/env python3
"""Generate the standalone round dealer time dashboard — with dealer history."""
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
  <title>Round Dealer Time & Dealer Progress Dashboard</title>
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
    .kpis { display: grid; grid-template-columns: repeat(6, minmax(110px, 1fr)); gap: 10px; margin-bottom: 16px; }
    .card { border: 1px solid #24334a; border-radius: 14px; background: linear-gradient(145deg, #121d30e8, #0c1423f2); box-shadow: 0 10px 30px #0002; }
    .kpi { padding: 16px; }
    .kpi label { display: block; margin-bottom: 8px; color: #91a2ba; font-size: 10px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
    .kpi strong { font: 700 18px ui-monospace, Consolas, monospace; color: #f8fafc; }
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
    @media (max-width: 900px) { .kpis { grid-template-columns: repeat(4, 1fr); } .grid { grid-template-columns: 1fr; } .wide { grid-column: auto; } }
    @media (max-width: 560px) { main { padding: 14px; } .kpis { grid-template-columns: repeat(2, 1fr); } .chart { height: 300px; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1><i class="fa-solid fa-clock" style="color:#34d399"></i> Round Dealer Time & Dealer Progress</h1>
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
        <h2>Dealer timing performance across games and dates</h2>
        <p>AVG_TIMEDIFF = actual mean round duration (hours). Breach when actual exceeds expected.</p>
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
        <div class="muted" id="combinedNote">Pooled daily means across every dealer-game combination · follows the trend window and date range</div>
      </article>
      <article class="card chart-card"><h3>Overall duration trend — all games</h3><div class="muted">Pooled daily mean actual vs expected round duration</div><div id="combinedDuration" class="chart"></div></article>
      <article class="card chart-card"><h3>Overall breach rate — all games</h3><div class="muted">Pooled daily % of dealer rounds above expected duration</div><div id="combinedBreach" class="chart"></div></article>
      <article class="card chart-card"><h3>Top breach dealers</h3><div class="muted">Dealers with highest breach rates across selected history</div><div id="breachDealers" class="chart"></div></article>
      <div class="game-sections" id="gameSections"></div>
      <article class="card chart-card wide">
        <h3>Latest day: actual vs expected duration by dealer</h3>
        <div class="muted">Each point is a dealer round on the latest billing date; triangles indicate above-expected duration</div>
        <div id="relationship" class="chart"></div>
      </article>
      <article class="card chart-card wide">
        <h3>Dealer progress over time</h3>
        <div class="muted">Select a dealer below to see their timing progression across dates and game types</div>
        <select id="dealerSelect" style="padding: 9px 12px; border: 1px solid #344258; border-radius: 8px; background: #111b2d; color: #e2e8f0; font-family: inherit; font-size: 12px; width: 100%; margin-bottom: 12px;">
          <option value="">-- Select dealer --</option>
        </select>
        <div id="dealerProgress" style="height: 300px; min-width: 600px;"></div>
      </article>
      <article class="card chart-card wide"><h3>Dealer type summary</h3><div class="table-wrap"><table><thead><tr><th>Dealer</th><th>Total Rows</th><th>Date Range</th><th>Games</th><th>Mean Actual</th><th>Mean Expected</th><th>Breach %</th></th></tr></thead><tbody id="dealerSummaries"></tbody></table></div></article>
    </section>
    <footer>Source: daily published CSV snapshots. Missing dates are retained as gaps; no metric is interpolated. Refresh this dashboard by running the dashboard pipeline.</footer>
  </main>
  <script id="round-dealer-time-data" type="application/json">__PAYLOAD__</script>
  <script>
    const DATA = JSON.parse(document.getElementById('round-dealer-time-data').textContent);
    const colors = ['#38bdf8','#34d399','#fbbf24','#c084fc','#fb7185','#2dd4bf','#a3e635','#f97316'];
    const chartIds = ['dealerProgress','combinedDuration','combinedBreach','breachDealers','relationship'];
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
    const allDealers = DATA.dealers || [];

    // Build dealer options
    const dealerSelect = document.getElementById('dealerSelect');
    allDealers.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.dealer_id;
      opt.textContent = `${escapeHtml(d.dealer_id)} — ${d.total_rows} rows, ${d.games_count} games`;
      dealerSelect.appendChild(opt);
    });

    function renderKpis() {
      const m = DATA.meta;
      const tiles = [
        ['Latest snapshot', m.latest_file_date],
        ['Billing date range', `${m.billing_date_min} – ${m.billing_date_max}`],
        ['Game types', m.game_types.length],
        ['Dealers tracked', m.dealers_tracked],
        ['Null duration rows', m.null_duration_rows],
        ['Unique dealer-game entries', m.dealer_entries_count]
      ];
      document.getElementById('kpis').innerHTML = tiles.map(([label, value]) => `<div class="card kpi"><label>${escapeHtml(label)}</label><strong>${escapeHtml(value)}</strong></div>`).join('');
      document.getElementById('feedStatus').textContent = `Updated ${m.generated_at} · ${Number(m.files_available).toLocaleString()} snapshots · ${Number(m.unique_keys).toLocaleString()} unique dealer-game records`;
      const gaps = DATA.missing_dates || [];
      document.getElementById('coverageAlert').innerHTML = gaps.length
        ? `<div class="alert"><strong>${gaps.length} missing snapshot dates</strong> after the first published file. Missing days are excluded from averages and shown as a coverage gap. Recent gaps: ${gaps.slice(-8).map(escapeHtml).join(', ')}</div>`
        : '<div class="alert good">No missing snapshot dates are currently recorded after feed start.</div>';
      document.getElementById('dealerSummaries').innerHTML = DATA.dealers.map(d => `<tr>
        <td>${escapeHtml(d.dealer_id)}</td><td>${d.total_rows}</td>
        <td>${escapeHtml(d.date_range)}</td><td>${d.games_count}</td>
        <td>${number(d.mean_actual_duration)}</td><td>${number(d.mean_expected_duration)}</td>
        <td>${Number(d.breach_pct).toFixed(2)}%</td>
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

    function renderGameComparisons() {
      const names = types.map(game => game.game_type);
      /* dealerCompare removed — replaced by dealerSelect-driven chart */
    }

    function renderCombinedSummary() {
      const rows = (DATA.daily || []).filter(row => inTimeframe(row.date));
      const totalRows = DATA.dealers.reduce((sum, d) => sum + d.total_rows, 0);
      const totalBreaches = DATA.dealers.reduce((sum, d) => sum + d.total_breaches, 0);
      const pooledBreach = totalRows ? (totalBreaches / totalRows * 100) : null;
      const { start, end } = getDateRange();
      const suffix = (start || end) ? ` · ${start || '…'} to ${end || '…'}` : '';
      document.getElementById('combinedNote').textContent =
        `${DATA.dealers.length} dealers · ${totalRows} total records · ${pooledBreach == null ? '—' : `${pooledBreach.toFixed(2)}%`} pooled breach rate · ${rows.length} days in view${suffix}`;
      charts.combinedDuration.setOption({
        ...trendCommon, yAxis: { ...trendCommon.yAxis, name: 'Duration (h)' },
        series: [
          { name: 'Actual duration', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.mean_actual_duration]), lineStyle: { width: 2 }, itemStyle: { color: '#38bdf8' } },
          { name: 'Expected duration', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.mean_expected_duration]), lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#fbbf24' } }
        ]
      }, true);
      charts.combinedBreach.setOption({
        ...trendCommon, yAxis: { ...trendCommon.yAxis, name: 'Breach %' },
        series: [
          { name: 'Breach rate', type: 'line', showSymbol: false, smooth: true, connectNulls: false, data: rows.map(row => [row.date, row.breach_pct]), lineStyle: { width: 2 }, itemStyle: { color: '#f97316' } }
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
            <thead><tr><th>Dealer</th><th>Actual Duration</th><th>Expected Duration</th><th>Breach %</th></tr></thead>
            <tbody id="gameRows-${index}"></tbody>
          </table></div>
        `;
        fragment.appendChild(article);
      });
      container.appendChild(fragment);
    }

    function renderGameSections() {
      types.forEach((game, index) => {
        const name = game.game_type;
        const dealerRows = [];
        /* Show top 5 dealers by mean actual duration for this game */
        const gameDealers = (DATA.game_dealer_map || {})[name] || {};
        const dealerEntries = Object.entries(gameDealers)
          .map(([did, sublist]) => ({
            dealer_id: did,
            mean_actual: mean(sublist.map(r => r["actual_duration"])),
            mean_expected: mean(sublist.map(r => r["expected_duration"])),
            breach_pct: round(
              sum(1 for r in sublist if r["actual_duration"] > r["expected_duration"]) / sublist.length * 100, 2
            ),
            rows: sublist.length
          }))
          .sort((a, b) => b.mean_actual - a.mean_actual)
          .slice(0, 5);

        dealerRows.push(`<tr class="table-total"><td>${escapeHtml(name)} — top dealers</td>`);
        dealerEntries.forEach(d => {
          dealerRows.push(`<tr>
            <td>${escapeHtml(d.dealer_id)}</td><td>${number(d.mean_actual)}</td>
            <td>${number(d.mean_expected)}</td><td>${Number(d.breach_pct).toFixed(2)}%</td>
          </tr>`);
        });
        document.getElementById(`gameRows-${index}`).innerHTML = dealerRows.join('');
      });
    }

    function renderRelationship() {
      const latest = DATA.latest_day;
      const rows = latest.rows || [];
      const groups = [...new Set(rows.filter(row => row.actual_duration != null).map(row => row.game_type))];
      charts.relationship.setOption({
        color: colors, tooltip: {
          ...tooltipStyle, formatter: point => {
            const row = point.data.row;
            return `<strong>${escapeHtml(row.game_type)}</strong><br>${escapeHtml(row.dealer)}<br>Actual duration: ${number(row.actual_duration)}<br>Expected duration: ${number(row.expected_duration)}<br>${row.actual_duration > row.expected_duration ? 'Above expected' : 'At/below expected'}`;
          }
        },
        legend: { data: groups, textStyle: { color: '#cbd5e1' } },
        grid: { left: 65, right: 24, top: 42, bottom: 48 },
        xAxis: { type: 'value', name: 'Duration (h)', ...axisStyle },
        yAxis: { type: 'value', name: 'Duration (h)', ...axisStyle },
        series: groups.map(game => ({
          name: game, type: 'scatter', symbolSize: 11,
          data: rows.filter(row => row.game_type === game && row.actual_duration != null).map(row => ({
            value: [row.actual_duration, row.expected_duration],
            symbol: row.actual_duration > row.expected_duration ? 'triangle' : 'circle',
            row
          }))
        }))
      }, true);
      document.querySelector('#relationship').previousElementSibling.textContent =
        `Each point is a dealer round on ${latest.billing_date}; triangles indicate above-expected duration`;
    }

    function renderDealerProgress(dealerId) {
      const entries = DATA.dealer_entries || {}[dealerId] || [];
      if (!entries || entries.length === 0) {
        document.getElementById('dealerProgress').innerHTML = '<div class="alert">No trajectory data for selected dealer.</div>';
        return;
      }

      // Filter by date range if active
      const { start, end } = getDateRange();
      const filtered = entries.filter(e => {
        if (!inDateRange(e.date)) return false;
        return true;
      });

      if (filtered.length === 0) {
        document.getElementById('dealerProgress').innerHTML = '<div class="alert">No data in selected date range.</div>';
        return;
      }

      // Sort by date
      filtered.sort((a, b) => (a.date || '').localeCompare(b.date || '') || (a.game_type || '').localeCompare(b.game_type || ''));

      // Build series: one line per game type for this dealer
      const gameTypes = [...new Set(filtered.map(e => e.game_type))];
      const series = gameTypes.map(gt => ({
        name: gt,
        type: 'line',
        showSymbol: false,
        smooth: true,
        connectNulls: false,
        data: filtered
          .filter(e => e.game_type === gt)
          .map(e => [e.date, e.actual_duration])
          .filter(d => d[1] != null),
        itemStyle: { color: colors[gameTypes.indexOf(gt) % colors.length] },
        lineStyle: { width: 2 }
      }));

      charts.dealerProgress.setOption({
        ...trendCommon,
        yAxis: { ...trendCommon.yAxis, name: 'Duration (h)' },
        tooltip: { ...tooltipStyle, trigger: 'axis' },
        legend: { textStyle: { color: '#cbd5e1' } },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 14, bottom: 4, borderColor: '#334155', textStyle: { color: '#94a3b8', fontSize: 8 } }
        ],
        series: series
      });
    }

    function initDealerSelect() {
      dealerSelect.addEventListener('change', (e) => {
        const selected = e.target.value;
        renderDealerProgress(selected);
      });
    }

    function initDateRangeBounds() {
      const allDates = [...Object.values(DATA.series_duration || {}), ...Object.values(DATA.series_breach || {})].flat().map(([day]) => day).sort();
      const min = DATA.meta.billing_date_min || (allDates.length > 0 ? allDates[0][0] : '');
      const max = DATA.meta.billing_date_max || (allDates.length > 0 ? allDates[allDates.length - 1][0] : '');
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
      initDealerSelect();
    }

    const allCharts = () => [...Object.values(charts), charts.dealerProgress];

    renderKpis();
    initDateRangeBounds();
    buildGameSections();
    render();
    document.getElementById('periodFilter').addEventListener('change', render);
    document.getElementById('startDate').addEventListener('change', render);
    document.getElementById('endDate').addEventListener('change', render);
    document.getElementById('resetDateRange').addEventListener('click', resetDateRange);
    dealerSelect.addEventListener('change', render);
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