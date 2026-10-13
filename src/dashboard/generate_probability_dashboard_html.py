#!/usr/bin/env python3
"""Generate the standalone game probability and house-edge dashboard."""

import json
from pathlib import Path

WORKSPACE = Path(r"C:\Users\IT-40126\Documents\August 2026-20261008T011759Z-1-001\August 2026")
DATA_FILE = WORKSPACE / "output" / "game_probability_he_data.json"
OUT_FILE = WORKSPACE / "output" / "game_probability_dashboard.html"


def build_dashboard():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Probability data payload not found: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as source:
        data = json.load(source)

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    template = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Game Probability &amp; House Edge Dashboard</title>
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
    .alert { margin: 14px 0; padding: 12px 15px; border: 1px solid #854d0e; border-radius: 10px; background: #713f121f; color: #fcd34d; font-size: 12px; }
    .alert.good { border-color: #166534; background: #14532d22; color: #86efac; }
    .trend-tabs { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px 15px 0; border-bottom: 1px solid #253247; margin: -15px -15px 0; }
    .trend-tab-btn { padding: 8px 14px; border: 1px solid #344258; border-radius: 9px 9px 0 0; background: #111b2d; color: #b9c7da; font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s ease; display: inline-flex; align-items: center; gap: 7px; }
    .trend-tab-btn:hover { border-color: #34d399; color: #6ee7b7; }
    .trend-tab-btn.active { background: #059669; border-color: #34d399; color: #ffffff; box-shadow: 0 4px 14px 0 #05966959; }
    .trend-pane { display: none; padding-top: 12px; }
    .trend-pane.active { display: block; animation: fadeIn .3s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
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
      <h1><i class="fa-solid fa-dice" style="color:#34d399"></i> Game Probability &amp; House Edge</h1>
      <p id="feedStatus">Loading latest probability feed…</p>
    </div>
    <nav aria-label="Dashboards">
      <a href="bi_dashboard.html"><i class="fa-solid fa-chart-line"></i> BI Console</a>
      <a href="player_behavior_dashboard.html"><i class="fa-solid fa-gamepad"></i> Player Behavior</a>
    </nav>
  </header>
  <main>
    <section class="hero">
      <div>
        <h2>Game performance, model expectation &amp; threshold monitoring</h2>
        <p>Percent values follow the source feed. Probability breaches are actual probability above threshold.</p>
      </div>
      <div class="filters">
        <label class="muted" for="gameFilter">Trend game<br><select id="gameFilter"></select></label>
        <label class="muted" for="periodFilter">Trend window<br><select id="periodFilter"><option value="90">Latest 90 days</option><option value="365">Latest 365 days</option><option value="all">All available dates</option></select></label>
        <label class="muted" for="startDate">Start date<br><input type="date" id="startDate"></label>
        <label class="muted" for="endDate">End date<br><input type="date" id="endDate"></label>
        <button type="button" class="date-range-reset" id="resetDateRange" title="Clear the date range and fall back to the trend window"><i class="fa-solid fa-rotate-left"></i> Reset range</button>
      </div>
    </section>
    <div id="coverageAlert"></div>
    <section id="kpis" class="kpis"></section>
    <section class="grid">
      <article class="card chart-card"><h3>Average actual vs expected HE by game</h3><div class="muted" id="heCompareNote">Daily bet-place records pooled across the selected history</div><div id="heCompare" class="chart"></div></article>
      <article class="card chart-card"><h3>Probability vs expected probability and threshold</h3><div class="muted" id="probCompareNote">Compare the observed probability with the model and configured limit</div><div id="probCompare" class="chart"></div></article>
      <article class="card chart-card wide" id="trendPanel">
        <div class="trend-tabs" role="tablist" aria-label="Trend views">
          <button type="button" class="trend-tab-btn active" role="tab" aria-selected="true" aria-controls="pane-heTrend" onclick="switchTrendTab('he')"><i class="fa-solid fa-chart-line"></i> HE trend for selected game</button>
          <button type="button" class="trend-tab-btn" role="tab" aria-selected="false" aria-controls="pane-probTrend" onclick="switchTrendTab('prob')"><i class="fa-solid fa-percent"></i> Probability and threshold trend</button>
        </div>
        <div class="trend-pane active" id="pane-heTrend" role="tabpanel">
          <h3>HE trend for selected game</h3>
          <div class="muted">Daily actual and expected house edge · honours the start/end date range</div>
          <div id="heTrend" class="chart"></div>
        </div>
        <div class="trend-pane" id="pane-probTrend" role="tabpanel">
          <h3>Probability and threshold trend</h3>
          <div class="muted">Daily averages for the selected game · honours the start/end date range</div>
          <div id="probTrend" class="chart"></div>
        </div>
      </article>
      <article class="card chart-card wide"><h3>Latest bet-place relationship: actual probability vs actual HE</h3><div class="muted">Each point is a bet place on the latest billing date; triangles indicate probability above threshold</div><div id="relationship" class="chart"></div></article>
      <article class="card chart-card wide"><h3>Game type summary</h3><div class="table-wrap"><table><thead><tr><th>Game</th><th>Days</th><th>HE rows</th><th>Actual HE</th><th>Expected HE</th><th>HE delta</th><th>Actual prob.</th><th>Expected prob.</th><th>Threshold</th><th>Breach rows %</th></tr></thead><tbody id="summaryRows"></tbody></table></div></article>
    </section>
    <footer>Source: daily published CSV snapshots. Missing dates are retained as gaps; no metric is interpolated. Refresh this dashboard by running the dashboard pipeline.</footer>
  </main>
  <script id="probability-data" type="application/json">__PAYLOAD__</script>
  <script>
    const DATA = JSON.parse(document.getElementById('probability-data').textContent);
    const colors = ['#38bdf8','#34d399','#fbbf24','#c084fc','#fb7185','#2dd4bf','#a3e635','#f97316'];
    const chartIds = ['heCompare','probCompare','heTrend','probTrend','relationship'];
    const charts = Object.fromEntries(chartIds.map(id => [id, echarts.init(document.getElementById(id))]));
    const gameFilter = document.getElementById('gameFilter');
    const number = value => value == null ? '—' : `${Number(value).toFixed(2)}%`;
    const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[character]));
    const pair = (object, key) => object && object[key] || [];
    const axisStyle = { axisLabel: { color: '#94a3b8' }, axisLine: { lineStyle: { color: '#334155' } }, splitLine: { lineStyle: { color: '#253247', type: 'dashed' } } };
    const tooltipStyle = { backgroundColor: '#0f172a', borderColor: '#334155', textStyle: { color: '#f8fafc' } };
    const types = DATA.game_types || [];
    for (const game of types) gameFilter.add(new Option(game.game_type, game.game_type));
    gameFilter.add(new Option('All games', '__all__'), 0);
    gameFilter.value = '__all__';

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
        <td>${escapeHtml(game.game_type)}</td><td>${game.days}</td><td>${game.he_rows}</td>
        <td>${number(game.mean_actual_he)}</td><td>${number(game.mean_expected_he)}</td><td>${number(game.mean_he_delta)}</td>
        <td>${number(game.mean_actual_probability)}</td><td>${number(game.mean_expected_probability)}</td><td>${number(game.mean_threshold)}</td><td>${Number(game.breach_pct).toFixed(2)}%</td>
      </tr>`).join('');
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
      document.getElementById('heCompareNote').textContent = `Daily bet-place records pooled across the selected history${suffix}`;
      document.getElementById('probCompareNote').textContent = `Compare the observed probability with the model and configured limit${suffix}`;
    }

    function renderGameComparisons() {
      const names = types.map(game => game.game_type);
      charts.heCompare.setOption({
        color: ['#38bdf8','#fbbf24'], tooltip: { ...tooltipStyle, trigger: 'axis' }, legend: { textStyle: { color: '#cbd5e1' } },
        grid: { left: 55, right: 18, top: 38, bottom: 72 },
        xAxis: { type: 'category', data: names, axisLabel: { ...axisStyle.axisLabel, rotate: 25 } }, yAxis: { type: 'value', name: 'HE (%)', ...axisStyle },
        series: [
          { name: 'Actual HE', type: 'bar', data: comparisonValues('series_he', 'mean_actual_he'), itemStyle: { borderRadius: [4,4,0,0] } },
          { name: 'Expected HE', type: 'bar', data: comparisonValues('series_expected_he', 'mean_expected_he'), itemStyle: { borderRadius: [4,4,0,0] } }
        ]
      });
      charts.probCompare.setOption({
        color: ['#38bdf8','#a78bfa','#fb7185'], tooltip: { ...tooltipStyle, trigger: 'axis' }, legend: { textStyle: { color: '#cbd5e1' } },
        grid: { left: 55, right: 18, top: 38, bottom: 72 },
        xAxis: { type: 'category', data: names, axisLabel: { ...axisStyle.axisLabel, rotate: 25 } }, yAxis: { type: 'value', name: 'Probability (%)', ...axisStyle },
        series: [
          { name: 'Actual probability', type: 'bar', data: comparisonValues('series_actual_probability', 'mean_actual_probability'), itemStyle: { borderRadius: [4,4,0,0] } },
          { name: 'Expected probability', type: 'bar', data: comparisonValues('series_expected_probability', 'mean_expected_probability'), itemStyle: { borderRadius: [4,4,0,0] } },
          { name: 'Threshold', type: 'bar', data: comparisonValues('series_threshold', 'mean_threshold'), itemStyle: { borderRadius: [4,4,0,0] } }
        ]
      });
      updateComparisonNotes();
    }

    function selectedTrendValues(seriesByGame, selected, days) {
      const chosen = selected === '__all__' ? types.map(game => game.game_type) : [selected];
      const cutoff = days === 'all' ? null : new Date();
      if (cutoff) cutoff.setDate(cutoff.getDate() - Number(days));
      const range = getDateRange();
      return chosen.map((game, index) => ({
        name: game,
        type: 'line',
        connectNulls: false,
        showSymbol: false,
        smooth: true,
        data: pair(seriesByGame, game).filter(([day]) => {
          if (cutoff && new Date(`${day}T00:00:00`) < cutoff) return false;
          return inDateRange(day);
        }).map(([day, value]) => [day, value]),
        itemStyle: { color: colors[index % colors.length] },
        lineStyle: { width: 2 }
      }));
    }

    function renderTrends() {
      const selected = gameFilter.value;
      const days = document.getElementById('periodFilter').value;
      const common = {
        tooltip: { ...tooltipStyle, trigger: 'axis' }, legend: { type: 'scroll', textStyle: { color: '#cbd5e1' } },
        grid: { left: 58, right: 20, top: 45, bottom: 38 },
        xAxis: { type: 'time', ...axisStyle }, yAxis: { type: 'value', ...axisStyle }
      };
      charts.heTrend.setOption({
        ...common, yAxis: { ...common.yAxis, name: 'HE (%)' },
        series: [
          ...selectedTrendValues(DATA.series_he, selected, days).map(series => ({ ...series, name: `${series.name} actual HE` })),
          ...selectedTrendValues(DATA.series_expected_he, selected, days).map(series => ({ ...series, name: `${series.name} expected HE`, lineStyle: { ...series.lineStyle, type: 'dashed' } }))
        ]
      }, true);
      charts.probTrend.setOption({
        ...common, yAxis: { ...common.yAxis, name: 'Probability (%)' },
        series: [
          ...selectedTrendValues(DATA.series_actual_probability, selected, days).map(series => ({ ...series, name: `${series.name} actual probability` })),
          ...selectedTrendValues(DATA.series_expected_probability, selected, days).map(series => ({ ...series, name: `${series.name} expected probability`, lineStyle: { ...series.lineStyle, type: 'dashed' } })),
          ...selectedTrendValues(DATA.series_threshold, selected, days).map(series => ({ ...series, name: `${series.name} threshold`, lineStyle: { ...series.lineStyle, type: 'dotted' } }))
        ]
      }, true);
    }

    function switchTrendTab(which) {
      document.querySelectorAll('.trend-pane').forEach(pane => pane.classList.remove('active'));
      document.querySelectorAll('.trend-tab-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      });
      const pane = document.getElementById(`pane-${which === 'he' ? 'heTrend' : 'probTrend'}`);
      if (pane) pane.classList.add('active');
      const btn = document.querySelector(`.trend-tab-btn[onclick="switchTrendTab('${which}')"]`);
      if (btn) { btn.classList.add('active'); btn.setAttribute('aria-selected', 'true'); }
      setTimeout(() => charts[which === 'he' ? 'heTrend' : 'probTrend'].resize(), 50);
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

    function initDateRangeBounds() {
      const dates = [...Object.values(DATA.series_he || {}), ...Object.values(DATA.series_expected_he || {}),
                     ...Object.values(DATA.series_actual_probability || {}), ...Object.values(DATA.series_expected_probability || {}),
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

    function renderRelationship() {
      const latest = DATA.latest_day;
      const selected = gameFilter.value;
      const rows = (latest.rows || []).filter(row => selected === '__all__' || row.game_type === selected);
      const groups = [...new Set(rows.filter(row => row.actual_probability != null && row.actual_he != null).map(row => row.game_type))];
      charts.relationship.setOption({
        color: colors, tooltip: {
          ...tooltipStyle, formatter: point => {
            const row = point.data.row;
            return `<strong>${escapeHtml(row.game_type)}</strong><br>${escapeHtml(row.bet_place)}<br>Actual probability: ${number(row.actual_probability)}<br>Threshold: ${number(row.threshold)}<br>Actual HE: ${number(row.actual_he)}<br>Expected HE: ${number(row.expected_he)}<br>${row.prob_breach ? 'Above threshold' : 'At/below threshold'}`;
          }
        },
        legend: { data: groups, textStyle: { color: '#cbd5e1' } },
        grid: { left: 65, right: 24, top: 42, bottom: 48 },
        xAxis: { type: 'value', name: 'Actual probability (%)', ...axisStyle },
        yAxis: { type: 'value', name: 'Actual HE (%)', ...axisStyle },
        series: groups.map(game => ({
          name: game, type: 'scatter', symbolSize: 11,
          data: rows.filter(row => row.game_type === game && row.actual_probability != null && row.actual_he != null).map(row => ({
            value: [row.actual_probability, row.actual_he],
            symbol: row.prob_breach ? 'triangle' : 'circle',
            row
          }))
        }))
      }, true);
      document.querySelector('#relationship').previousElementSibling.textContent =
        `Each point is a bet place on ${latest.billing_date}; triangles indicate probability above threshold`;
    }

    function render() {
      renderGameComparisons();
      renderTrends();
      renderRelationship();
    }

    renderKpis();
    initDateRangeBounds();
    render();
    gameFilter.addEventListener('change', render);
    document.getElementById('periodFilter').addEventListener('change', renderTrends);
    document.getElementById('startDate').addEventListener('change', render);
    document.getElementById('endDate').addEventListener('change', render);
    document.getElementById('resetDateRange').addEventListener('click', resetDateRange);
    window.addEventListener('resize', () => Object.values(charts).forEach(chart => chart.resize()));
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
