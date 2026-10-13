    // ========================================================================
    // DOSSIER MODULE — ALL PLAYERS (full database) + OPERATORS
    // ========================================================================
    // The embedded #dossier-raw-data payload carries the compact index of
    // EVERY player in the audit (meta + players[]) plus the fully detailed
    // operator dossiers. Each player's FULL round-by-round balance trajectory
    // is lazy-loaded on demand from dossier_chunks/chunk_NNNN.js companion
    // files sitting next to this HTML, so any of the ~50k players can be
    // opened with their complete balance history without inflating the page.
    let DOSSIER = null;
    let CHUNK_SIZE = 1000;
    document.addEventListener('DOMContentLoaded', function () {
      try {
        const el = document.getElementById('dossier-raw-data');
        if (el) {
          DOSSIER = JSON.parse(el.textContent);
          if (DOSSIER && DOSSIER.meta) CHUNK_SIZE = DOSSIER.meta.chunk_size || 1000;
        }
      } catch (e) { console.warn('Dossier data unavailable', e); DOSSIER = null; }
    });

    const FLAG_MAP = {"Indonesia":"🇮🇩","Vietnam":"🇻🇳","China":"🇨🇳","Bangladesh":"🇧🇩","Thailand":"🇹🇭","Malaysia":"🇲🇾","India":"🇮🇳","Myanmar":"🇲🇲","Philippines":"🇵🇭","Cambodia":"🇰🇭","Laos":"🇱🇦","Singapore":"🇸🇬","South Korea":"🇰🇷","Japan":"🇯🇵","USA":"🇺🇸","Hong Kong":"🇭🇰","Taiwan":"🇹🇼","Nepal":"🇳🇵","Turkey":"🇹🇷","Crypto":"🪙","Unknown":"🌐"};
const ARCHETYPE_COLORS = {
  'Extreme Chaser': '#f43f5e', 'Critical Chaser': '#f97316', 'High Chaser': '#f59e0b',
  'Moderate Chaser': '#eab308', 'Low Chaser': '#84cc16',
  'Lightning Burst Whale': '#f59e0b', 'Sustained Grinder Whale': '#d97706', 'VIP Whale': '#fbbf24',
  'VIP High Roller': '#a78bfa', 'High Roller': '#8b5cf6', 'Mid Roller': '#6366f1',
  'Active Player': '#0ea5e9', 'Casual Player': '#64748b'
};
const ARCHETYPE_DESC = {
  'Extreme Chaser': 'Spike ≥1000x — bet escalation after consecutive losses is extreme. Highest-risk gambler.',
  'Critical Chaser': 'Spike 100–999x — severe escalation, strong problem-gambling signal.',
  'High Chaser': 'Spike 50–99x — rapid bet inflation after losses.',
  'Moderate Chaser': 'Spike 10–49x — noticeable chase behaviour.',
  'Low Chaser': 'Spike 3–9x — mild chase tendency.',
  'Lightning Burst Whale': 'Whale who wagers in short, intense bursts — high volume in brief sessions.',
  'Sustained Grinder Whale': 'Whale with long, steady sessions — consistent high-volume grinding.',
  'VIP Whale': 'Top-tier whale by total debit — among the largest depositors in the database.',
  'VIP High Roller': 'VIP whale with very high average bet size on premium games.',
  'High Roller': 'High average bet size, elevated spend per wager.',
  'Mid Roller': 'Moderate bet sizes and steady activity.',
  'Active Player': 'Frequent wagers but modest bet sizes — regular participant.',
  'Casual Player': 'Low frequency / low bet size — infrequent, small-stakes play.'
};
    const GAME_COLORS = {'baccarat':'#10b981','dragon_tiger':'#f59e0b','roulette':'#8b5cf6','sicbo':'#06b6d4','niuniu':'#ec4899','Unknown':'#64748b'};

    function archetypeColor(arch) {
      if (!arch) return '#6366f1';
      for (const k of Object.keys(ARCHETYPE_COLORS)) { if (arch.includes(k)) return ARCHETYPE_COLORS[k]; }
      return '#6366f1';
    }
function archetypeBg(arch) {
  const c = archetypeColor(arch);
  return `background:${c}22; border:1px solid ${c}55; color:${c}`;
}
function renderArchetypeLegend() {
  const host = document.getElementById('archetypeLegend');
  if (!host) return;
  const order = [
    'Extreme Chaser', 'Critical Chaser', 'High Chaser', 'Moderate Chaser', 'Low Chaser',
    'Lightning Burst Whale', 'Sustained Grinder Whale', 'VIP Whale', 'VIP High Roller',
    'High Roller', 'Mid Roller', 'Active Player', 'Casual Player'
  ];
  host.innerHTML = order.map(a => {
    const c = ARCHETYPE_COLORS[a] || '#6366f1';
    const active = _selectedArchetypes.has(a);
    return `<div class="rounded-lg p-2 border cursor-pointer transition-all hover:scale-105" ${active ? `style="background:${c}44; border-color:${c}; box-shadow:0 0 0 2px ${c} inset;"` : `style="background:${c}15; border-color:${c}44;"`} onclick="toggleArchetypeFilter('${a}')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleArchetypeFilter('${a}');}" tabindex="0" role="button" aria-pressed="${active}" title="Filter by ${a}">
      <div class="text-[11px] font-bold" style="color:${c}">${a}</div>
      <div class="text-[9px] text-slate-400 mt-0.5 leading-snug">${ARCHETYPE_DESC[a] || ''}</div>
    </div>`;
  }).join('');
  const countEl = document.getElementById('archetypeFilterCount');
  if (countEl) countEl.textContent = _selectedArchetypes.size ? `· ${_selectedArchetypes.size} selected` : '';
  const clearBtn = document.getElementById('clearArchetypeFiltersBtn');
  if (clearBtn) clearBtn.classList.toggle('hidden', _selectedArchetypes.size === 0);
}
    function fmtN(v, dec) {
      if (v == null || isNaN(v)) return 'N/A';
      dec = dec == null ? 2 : dec;
      const abs = Math.abs(v);
      if (abs >= 1e9) return (v/1e9).toFixed(dec)+'B';
      if (abs >= 1e6) return (v/1e6).toFixed(dec)+'M';
      if (abs >= 1e3) return (v/1e3).toFixed(dec)+'K';
      return (typeof v === 'number' ? v.toFixed(dec) : v);
    }
    function kpiCard(label, value, color, icon, description) {
      const descHtml = description ? `<div class="text-[9px] text-slate-500 mt-1.5 leading-tight">${description}</div>` : '';
      return `<div class="glass-card rounded-xl p-3 text-center">
        <div class="text-[10px] text-slate-400 uppercase font-semibold">${icon ? '<i class="'+icon+' mr-1"></i>' : ''}${label}</div>
        <div class="text-base font-extrabold font-mono mt-1 ${color || 'text-white'}">${value}</div>
        ${descHtml}
      </div>`;
    }
    function dossierTheme() {
      if (typeof getChartTheme === 'function') return getChartTheme();
      return { bg:'transparent', textColor:'#94a3b8', titleColor:'#f8fafc', gridBorder:'#1e293b', tooltipBg:'#0f172a', tooltipBorder:'#334155', tooltipText:'#ffffff' };
    }
    function flagOf(country) { return FLAG_MAP[country] || '🌐'; }

    // ── CHUNK LOADER (lazy-load full trajectories) ─────────────────
    const _chunkCallbacks = {};
    function loadDossierChunk(chunkId, callback) {
      const gname = 'DOSSIER_CHUNK_' + String(chunkId).padStart(4, '0');
      if (window[gname]) { callback(window[gname]); return; }
      if (_chunkCallbacks[chunkId]) { _chunkCallbacks[chunkId].push(callback); return; }
      _chunkCallbacks[chunkId] = [callback];
      const s = document.createElement('script');
      s.src = 'dossier_chunks/chunk_' + String(chunkId).padStart(4, '0') + '.js';
      s.onload = function () {
        const cbs = _chunkCallbacks[chunkId] || [];
        delete _chunkCallbacks[chunkId];
        cbs.forEach(cb => cb(window[gname] || null));
      };
      s.onerror = function () {
        const cbs = _chunkCallbacks[chunkId] || [];
        delete _chunkCallbacks[chunkId];
        cbs.forEach(cb => cb(null));
      };
      document.head.appendChild(s);
    }

// ── PLAYER DOSSIERS (ALL PLAYERS, PAGINATED) ─────────────────
    let filteredPlayers = DOSSIER ? [...DOSSIER.players] : [];
    let playerPage = 1;
    let playerPageSize = 60;
    let _selectedArchetypes = new Set();  // empty = show all

    function toggleArchetypeFilter(arch) {
      if (_selectedArchetypes.has(arch)) _selectedArchetypes.delete(arch);
      else _selectedArchetypes.add(arch);
      renderArchetypeLegend();
      filterPlayerDossiers();
    }
    function clearArchetypeFilters() {
      _selectedArchetypes.clear();
      renderArchetypeLegend();
      filterPlayerDossiers();
    }

    function initPlayerDossiers() {
      if (!DOSSIER) return;
      renderArchetypeLegend();
  const countries = [...new Set(DOSSIER.players.map(p => p.country).filter(Boolean))].sort();
      const sel = document.getElementById('playerCountryFilter');
      if (sel) countries.forEach(c => { const o = document.createElement('option'); o.value = c; o.text = c; sel.appendChild(o); });
      const cnt = document.getElementById('playerDossierCount');
      if (cnt) cnt.textContent = DOSSIER.players.length.toLocaleString();
      const tot = document.getElementById('playerDossierTotal');
      if (tot) tot.textContent = DOSSIER.players.length.toLocaleString();
      filterPlayerDossiers();
    }

    function filterPlayerDossiers() {
      if (!DOSSIER) return;
      const q = (document.getElementById('playerSearch')?.value || '').toLowerCase();
      const tier = document.getElementById('playerTierFilter')?.value || '';
      const country = document.getElementById('playerCountryFilter')?.value || '';
      const sort = document.getElementById('playerSortFilter')?.value || 'debit';
      filteredPlayers = DOSSIER.players.filter(p => {
        const matchQ = !q || (p.pid||'').toLowerCase().includes(q) || (p.country||'').toLowerCase().includes(q) || (p.arch||'').toLowerCase().includes(q) || (p.op||'').toLowerCase().includes(q);
        let matchTier = true;
        if (tier === 'whale') matchTier = !!p.whale;
        else if (tier === 'chaser') matchTier = !!p.chaser;
        else if (tier) matchTier = (p.arch||'') === tier;
        // Legend archetype toggle: match exact archetype string
        const matchArch = _selectedArchetypes.size === 0 || _selectedArchetypes.has(p.arch);
        const matchCountry = !country || p.country === country;
        return matchQ && matchTier && matchArch && matchCountry;
      });
      const sorters = {
        debit: (a,b) => (b.debit||0) - (a.debit||0),
        bets: (a,b) => (b.bets||0) - (a.bets||0),
        pnl: (a,b) => (b.winlose||0) - (a.winlose||0),
        spike: (a,b) => (b.spike||0) - (a.spike||0),
        avg_bet: (a,b) => (b.avg_bet||0) - (a.avg_bet||0)
      };
      filteredPlayers.sort(sorters[sort] || sorters.debit);
      playerPage = 1;
      renderPlayerCards();
    }

    function changePageSize() {
      playerPageSize = parseInt(document.getElementById('playerPageSize')?.value || '60', 10);
      playerPage = 1;
      renderPlayerCards();
    }
    function prevPlayerPage() { if (playerPage > 1) { playerPage--; renderPlayerCards(); } }
    function nextPlayerPage() {
      const totalPages = Math.max(1, Math.ceil(filteredPlayers.length / playerPageSize));
      if (playerPage < totalPages) { playerPage++; renderPlayerCards(); }
    }

    function renderPlayerCards() {
      const grid = document.getElementById('playerCardsGrid');
      if (!grid || !DOSSIER) return;
      const fc = document.getElementById('playerFilterCount');
      if (fc) fc.textContent = `${filteredPlayers.length.toLocaleString()} of ${DOSSIER.players.length.toLocaleString()} players`;

      const totalPages = Math.max(1, Math.ceil(filteredPlayers.length / playerPageSize));
      if (playerPage > totalPages) playerPage = totalPages;
      const start = (playerPage - 1) * playerPageSize;
      const pageItems = filteredPlayers.slice(start, start + playerPageSize);

      const pi = document.getElementById('playerPageInfo');
      if (pi) pi.textContent = `Page ${playerPage.toLocaleString()} / ${totalPages.toLocaleString()} · showing #${(start+1).toLocaleString()}–#${(start+pageItems.length).toLocaleString()}`;
      const pb = document.getElementById('playerPrevBtn');
      if (pb) pb.disabled = playerPage <= 1;
      const nb = document.getElementById('playerNextBtn');
      if (nb) nb.disabled = playerPage >= totalPages;

      const html = pageItems.map(p => {
        const flag = flagOf(p.country);
        const winloseColor = (p.winlose||0) < 0 ? 'text-emerald-400' : 'text-rose-400';
        const winloseLabel = (p.winlose||0) < 0 ? `Casino +${fmtN(Math.abs(p.winlose))}` : `Player +${fmtN(p.winlose)}`;
        const tags = [];
        if (p.whale) tags.push('<span class="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 text-[9px] font-bold">🐋 WHALE</span>');
        if (p.chaser) tags.push('<span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[9px] font-bold">🎯 CHASER</span>');
        const c = archetypeColor(p.arch);
        return `<div onclick="openPlayerDossier(${p.id})"
          class="glass-card rounded-2xl p-4 cursor-pointer hover:scale-[1.02] transition-all duration-200 border"
          style="border-color:${c}44">
          <div class="flex items-start justify-between mb-2">
            <div>
              <div class="font-mono text-sm font-bold text-white truncate max-w-[150px]" title="${p.pid}">${p.pid}</div>
              <div class="text-[10px] text-slate-400 mt-0.5">${flag} ${p.country||'Unknown'}</div>
            </div>
            <div class="flex flex-wrap gap-1 justify-end">${tags.join('')}</div>
          </div>
          <div class="text-[10px] px-2 py-0.5 rounded-full inline-block mb-2 font-semibold" style="${archetypeBg(p.arch)}">${p.arch||'Player'}</div>
          <div class="grid grid-cols-2 gap-2 text-xs mt-2">
            <div><span class="text-slate-400 text-[10px]">Total Debit</span><br><strong class="text-cyan-400 font-mono">${fmtN(p.debit)}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Net P&amp;L</span><br><strong class="${winloseColor} font-mono">${winloseLabel}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Total Bets</span><br><strong class="text-white font-mono">${(p.bets||0).toLocaleString()}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Avg Bet</span><br><strong class="text-amber-400 font-mono">${fmtN(p.avg_bet)}</strong></div>
          </div>
        </div>`;
      }).join('');

      // Smooth fade transition so filter/search/pagination changes feel fluid
      // instead of an abrupt innerHTML swap.
      grid.style.transition = 'opacity .16s ease';
      grid.style.opacity = '0';
      window.clearTimeout(grid._fadeTimer);
      grid._fadeTimer = window.setTimeout(() => {
        grid.innerHTML = html;
        grid.style.opacity = '1';
      }, 150);
    }

    let playerChartInstances = {};
    function disposePlayerCharts() {
      Object.values(playerChartInstances).forEach(c => { try { c.dispose(); } catch(e){} });
      playerChartInstances = {};
    }

    function openPlayerDossier(id) {
      if (!DOSSIER) return;
      const p = DOSSIER.players[id];
      if (!p) return;
      window._currentPlayerIdx = id;
      const panel = document.getElementById('playerDossierPanel');
      panel.classList.remove('hidden');
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
      disposePlayerCharts();
      _dossierCalendarDate = null;
      _dossierDayTimestamps = null;
      document.getElementById('dossierCalendarGrid').innerHTML = '';
      document.getElementById('dossierCalendarMonth').textContent = '';
      document.getElementById('dossierDayDetail').classList.add('hidden');

      const c = archetypeColor(p.arch);
      const badge = document.getElementById('dossierPlayerBadge');
      badge.innerHTML = `<i class="fa-solid fa-user-secret mr-1"></i>${p.arch||'Player'}`;
      badge.style = archetypeBg(p.arch);
      document.getElementById('dossierPlayerTitle').textContent = '#' + (p.id+1).toLocaleString() + ' · ' + p.pid;
      document.getElementById('dossierPlayerSub').textContent = `${flagOf(p.country)} ${p.country||'Unknown'} · Primary Operator: ${p.op||'N/A'} · ${(p.bets||0).toLocaleString()} wagers · Avg Bet: ${fmtN(p.avg_bet)}`;

      document.getElementById('dossierPlayerKPIs').innerHTML = [
        kpiCard('Total Debit', fmtN(p.debit), 'text-cyan-400', 'fa-solid fa-coins', 'Total wagered amount in PHP'),
        kpiCard('Net P&L', (p.winlose<0?'Casino +':'Player +')+fmtN(Math.abs(p.winlose)), p.winlose<0?'text-emerald-400':'text-rose-400', 'fa-solid fa-scale-balanced', 'Net profit/loss (positive = player won)'),
        kpiCard('Total Bets', (p.bets||0).toLocaleString(), 'text-white', 'fa-solid fa-dice', 'Total number of wagers placed'),
        kpiCard('Avg Bet', fmtN(p.avg_bet), 'text-amber-400', 'fa-solid fa-arrow-up-right-dots', 'Average bet size per wager'),
        kpiCard('Spike Multiplier', (p.spike||1)+'x', 'text-orange-400', 'fa-solid fa-bolt', 'Max bet escalation after consecutive losses'),
        kpiCard('Tier', p.whale ? '🐋 Whale' : (p.chaser ? '🎯 Chaser' : 'Player'), 'text-indigo-400', 'fa-solid fa-shield-halved', 'Player classification by behavior profile'),
        kpiCard('Rank', '#' + (p.id+1).toLocaleString(), 'text-slate-300', 'fa-solid fa-ranking-star', 'Position in leaderboard by total debit')
      ].join('');

      // Show loading, then lazy-load the full trajectory chunk
      const loading = document.getElementById('dossierLoading');
      if (loading) loading.classList.remove('hidden');
      ['dossierBalanceChart','dossierPnlChart','dossierHoursChart','dossierGamesChart','dossierDeviceChart'].forEach(d => {
        const el = document.getElementById(d);
        if (el) el.innerHTML = '';
      });
      const rrDom = document.getElementById('dossierRecentRoundsTable');
      if (rrDom) rrDom.innerHTML = '<p class="text-xs text-slate-500 italic">Loading...</p>';
      const tp = document.getElementById('dossierTrajPoints');
      if (tp) tp.textContent = '';

      const chunkId = Math.floor(id / CHUNK_SIZE);
      loadDossierChunk(chunkId, function (chunk) {
        if (loading) loading.classList.add('hidden');
        if (!chunk) {
          const rrDom2 = document.getElementById('dossierRecentRoundsTable');
          if (rrDom2) rrDom2.innerHTML = '<p class="text-xs text-rose-400 italic">Trajectory chunk could not be loaded. Make sure the dossier_chunks/ directory sits next to this HTML file (or serve this folder over HTTP, e.g. `python -m http.server`).</p>';
          return;
        }
        const detail = chunk[p.pid];
        if (!detail) return;
        renderDossierDetail(p, detail);
      });
    }

    function renderDossierDetail(p, d) {
      const t = dossierTheme();
      const bal = d.balance_series || [];
      const n = bal.length;

      const tp = document.getElementById('dossierTrajPoints');
      if (tp) tp.textContent = n.toLocaleString() + ' rounds · FULL TRAJECTORY';

      // Balance trajectory (FULL)
      const balDom = document.getElementById('dossierBalanceChart');
      let bc = null;
      if (balDom && n) {
        bc = echarts.init(balDom);
        playerChartInstances['balance'] = bc;
        bc.setOption({
          backgroundColor: t.bg,
          grid: { top:20, right:20, bottom:30, left:70 },
          tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10},
            formatter: ps => `Round ${ps[0].dataIndex+1} of ${n.toLocaleString()}<br>Balance: <strong>${fmtN(ps[0].value)}</strong>` },
          xAxis: { type:'category', axisLabel:{color:t.textColor,fontSize:8}, boundaryGap:false },
          yAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:8,formatter:v=>fmtN(v)}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
          dataZoom: [{ type:'inside' }, { type:'slider', height:14, bottom:4, borderColor:t.gridBorder, textStyle:{color:t.textColor,fontSize:8} }],
          series: [{ type:'line', data: bal, smooth:false, showSymbol:false, sampling:'lttb',
            lineStyle:{color:'#06b6d4',width:1.5},
            areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(6,182,212,0.22)'},{offset:1,color:'rgba(6,182,212,0)'}]}} }]
        });
      }

      // Cumulative P&L (derived from balance: net change from first observation)
      const pnlDom = document.getElementById('dossierPnlChart');
      let pc = null;
      if (pnlDom && n) {
        const base = bal[0];
        const pnl = bal.map(b => b - base);
        pc = echarts.init(pnlDom);
        playerChartInstances['pnl'] = pc;
        pc.setOption({
          backgroundColor: t.bg,
          grid: { top:20, right:20, bottom:30, left:70 },
          tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10},
            formatter: ps => `Round ${ps[0].dataIndex+1} of ${n.toLocaleString()}<br>Cumulative P&amp;L: <strong>${fmtN(ps[0].value)}</strong>` },
          xAxis: { type:'category', axisLabel:{color:t.textColor,fontSize:8}, boundaryGap:false },
          yAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:8,formatter:v=>fmtN(v)}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
          dataZoom: [{ type:'inside' }, { type:'slider', height:14, bottom:4, borderColor:t.gridBorder, textStyle:{color:t.textColor,fontSize:8} }],
          series: [{ type:'line', data: pnl, smooth:false, showSymbol:false, sampling:'lttb',
            lineStyle:{color:'#f43f5e',width:1.5},
            markLine:{ silent:true, symbol:'none', lineStyle:{color:t.textColor,type:'dashed'}, data:[{yAxis:0}], label:{show:false} },
            areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(244,63,94,0.18)'},{offset:1,color:'rgba(244,63,94,0)'}]}} }]
        });
      }

      // Link the Balance Trajectory and Cumulative P&L charts so their
      // horizontal (round) zoom/pan stays perfectly in sync — both curves
      // share the same X axis (round index), so scrolling one must scroll
      // the other. ECharts `connect` syncs dataZoom actions bidirectionally.
      if (bc && pc) {
        echarts.connect([bc, pc]);
      }

      // Hourly activity
      const hrsDom = document.getElementById('dossierHoursChart');
      if (hrsDom && d.hours && d.hours.length) {
        const hc = echarts.init(hrsDom);
        playerChartInstances['hours'] = hc;
        const peak = Math.max(...d.hours);
        hc.setOption({
          backgroundColor: t.bg,
          grid: { top:10, right:20, bottom:30, left:45 },
          tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10}, formatter: ps => `${ps[0].name}<br>Bets: <strong>${ps[0].value.toLocaleString()}</strong>` },
          xAxis: { type:'category', data: Array.from({length:24},(_,i)=>`${i}:00`), axisLabel:{color:t.textColor,fontSize:8} },
          yAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:8}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
          series: [{ type:'bar', data: d.hours.map(v=>({ value:v, itemStyle:{ color: v===peak ? '#f43f5e' : '#f59e0b', borderRadius:[3,3,0,0] } })) }]
        });
      }

      // Game mix pie
      const gmDom = document.getElementById('dossierGamesChart');
      if (gmDom && d.games && d.games.length) {
        const gc = echarts.init(gmDom);
        playerChartInstances['games'] = gc;
        gc.setOption({
          backgroundColor: t.bg,
          tooltip: { trigger:'item', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10},
            formatter: pr => `<strong>${pr.name}</strong><br>Bets: ${pr.value.toLocaleString()} (${pr.percent}%)<br>Volume: ${fmtN(pr.data.debit)}<br>Win Rate: ${pr.data.win_rate_pct}%` },
          series: [{ type:'pie', radius:['40%','70%'],
            data:d.games.map(g=>({ name:g.game, value:g.bets, debit:g.debit, win_rate_pct:g.win_rate_pct, itemStyle:{color:GAME_COLORS[g.game]||'#64748b'} })),
            label:{color:t.textColor,fontSize:9}, emphasis:{itemStyle:{shadowBlur:8}} }]
        });
      }

      // Device split
      const devDom = document.getElementById('dossierDeviceChart');
      if (devDom && d.devices) {
        const dc = echarts.init(devDom);
        playerChartInstances['device'] = dc;
        const devData = Object.keys(d.devices).map(k => ({ name:k, value:d.devices[k] }));
        dc.setOption({
          backgroundColor: t.bg,
          tooltip: { trigger:'item', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10} },
          series: [{ type:'pie', radius:['35%','60%'], data: devData.map(x => ({ name:x.name, value:x.value, itemStyle:{ color: x.name==='Mobile' ? '#6366f1' : (x.name==='Desktop' ? '#06b6d4' : '#94a3b8') } })), label:{color:t.textColor,fontSize:9} }]
        });
      }

      // Recent rounds table
      const rr = d.recent_rounds || [];
      const rrDom = document.getElementById('dossierRecentRoundsTable');
      if (rrDom) {
        if (!rr.length) {
          rrDom.innerHTML = '<p class="text-xs text-slate-500 italic">No recent rounds captured for this player in the audit window.</p>';
        } else {
          rrDom.innerHTML = `<table class="w-full text-xs text-slate-300 border-collapse">
            <thead><tr class="border-b border-slate-700 text-slate-500 text-[10px] uppercase">
              <th class="py-1 px-2 text-left">Time</th><th class="py-1 px-2 text-left">Game</th>
              <th class="py-1 px-2 text-right">Debit</th><th class="py-1 px-2 text-right">Credit</th>
              <th class="py-1 px-2 text-center">Outcome</th><th class="py-1 px-2 text-right">Balance</th>
            </tr></thead>
            <tbody>${rr.slice(0,20).map(r=>`<tr class="border-b border-slate-800/50 hover:bg-slate-800/30">
              <td class="py-1 px-2 text-slate-500 text-[10px] font-mono">${(r.time||'').substring(5,16)}</td>
              <td class="py-1 px-2 text-slate-300">${r.game||''}</td>
              <td class="py-1 px-2 text-right text-amber-400 font-mono">${fmtN(r.debit||0)}</td>
              <td class="py-1 px-2 text-right text-emerald-400 font-mono">${fmtN(r.credit||0)}</td>
              <td class="py-1 px-2 text-center"><span class="px-1.5 py-0.5 rounded text-[9px] font-bold ${(r.winlose||0)>0?'bg-emerald-500/20 text-emerald-400':((r.winlose||0)<0?'bg-rose-500/20 text-rose-400':'bg-slate-500/20 text-slate-400')}">${(r.winlose||0)>0?'WIN':((r.winlose||0)<0?'LOSS':'TIE')}</span></td>
              <td class="py-1 px-2 text-right text-slate-400 font-mono">${fmtN(r.balance||0)}</td>
            </tr>`).join('')}</tbody>
</table>`;
        }
      }
    // Initialize monthly activity calendar
    initDossierCalendar(d);
  }

  // ── MONTHLY ACTIVITY CALENDAR ────────────────────────────────────
  let _dossierCalendarDate = null;
  let _dossierDayTimestamps = null;

  function buildDayTimestampMap(timestamps) {
    const map = new Map();
    for (const ts of timestamps) {
      if (!ts) continue;
      const d = new Date(ts * 1000);
      const dayKey = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
      if (!map.has(dayKey)) map.set(dayKey, new Array(24).fill(0));
      map.get(dayKey)[d.getHours()]++;
    }
    return map;
  }

  function initDossierCalendar(detail) {
    const timestamps = detail.timestamps || [];
    _dossierDayTimestamps = buildDayTimestampMap(timestamps);
    if (!_dossierDayTimestamps.size) return;

    const days = Array.from(_dossierDayTimestamps.keys()).sort((a, b) => a - b);
    const firstDay = days[0];
    const firstYear = Math.floor(firstDay / 10000);
    const firstMonth = Math.floor((firstDay % 10000) / 100) - 1;
    _dossierCalendarDate = { year: firstYear, month: firstMonth };
    renderDossierCalendar();
  }

  function renderDossierCalendar() {
    const grid = document.getElementById('dossierCalendarGrid');
    const monthLabel = document.getElementById('dossierCalendarMonth');
    if (!grid || !monthLabel || !_dossierCalendarDate) return;

    const { year, month } = _dossierCalendarDate;
    const date = new Date(year, month, 1);
    monthLabel.textContent = date.toLocaleString('en-US', { month: 'long', year: 'numeric' });

    const firstDayOfWeek = date.getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const prevMonthDays = new Date(year, month, 0).getDate();

    const activeColor = '#f59e0b';
    const todayColor = '#06b6d4';

    let html = '';
    const dayNames = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
    for (const dn of dayNames) {
      html += `<div class="text-center text-[10px] text-slate-500 font-semibold py-1">${dn}</div>`;
    }
    for (let i = 0; i < firstDayOfWeek; i++) {
      const day = prevMonthDays - firstDayOfWeek + i + 1;
      html += `<div class="text-center text-[11px] text-slate-600 py-1.5">${day}</div>`;
    }
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
      const dayKey = year * 10000 + (month + 1) * 100 + day;
      const isActive = _dossierDayTimestamps.has(dayKey);
      const isToday = (year === today.getFullYear() && month === today.getMonth() && day === today.getDate());
      const dayTotal = isActive ? _dossierDayTimestamps.get(dayKey).reduce((a, b) => a + b, 0) : 0;
      const bg = isActive ? `background:${activeColor}33;` : '';
      const border = isToday && !isActive ? `border:1px solid ${todayColor};` : (isToday && isActive ? `border:2px solid ${todayColor};` : '');
      const textColor = isActive ? (isToday ? todayColor : activeColor) : 'text-slate-400';
      const cursor = isActive ? 'cursor-pointer' : '';
      const onclick = isActive ? `onclick="openDayDetail(${dayKey})"` : '';
      html += `<div class="relative aspect-square rounded-lg p-1.5 ${cursor} transition-all hover:scale-105" style="${bg}${border}" ${onclick}>
        <span class="block text-[11px] font-mono ${textColor}">${day}</span>
        ${isActive ? `<span class="absolute bottom-0.5 left-0.5 right-0.5 h-1 rounded bg-gradient-to-r from-${activeColor} to-${activeColor}80 opacity-70" style="height:${Math.min(dayTotal / 50, 1) * 100}%"></span>` : ''}
      </div>`;
    }
    const totalCells = firstDayOfWeek + daysInMonth;
    const remaining = (7 - (totalCells % 7)) % 7;
    for (let i = 1; i <= remaining; i++) {
      html += `<div class="text-center text-[11px] text-slate-600 py-1.5">${i}</div>`;
    }
    grid.innerHTML = html;
  }

  function dossierCalendarPrevMonth() {
    if (!_dossierCalendarDate) return;
    _dossierCalendarDate.month--;
    if (_dossierCalendarDate.month < 0) {
      _dossierCalendarDate.month = 11;
      _dossierCalendarDate.year--;
    }
    renderDossierCalendar();
  }

  function dossierCalendarNextMonth() {
    if (!_dossierCalendarDate) return;
    _dossierCalendarDate.month++;
    if (_dossierCalendarDate.month > 11) {
      _dossierCalendarDate.month = 0;
      _dossierCalendarDate.year++;
    }
    renderDossierCalendar();
  }

  function openDayDetail(dayKey) {
    const hours = _dossierDayTimestamps.get(dayKey);
    if (!hours) return;
    const year = Math.floor(dayKey / 10000);
    const month = Math.floor((dayKey % 10000) / 100);
    const day = dayKey % 100;
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const dayName = new Date(year, month - 1, day).toLocaleString('en-US', { weekday: 'long' });

    const title = document.getElementById('dossierDayDetailTitle');
    const content = document.getElementById('dossierDayDetailContent');
    const panel = document.getElementById('dossierDayDetail');

    title.textContent = `${dayName}, ${dateStr} — Hourly Activity`;
    let html = '<div class="grid grid-cols-4 gap-1">';
    const peak = Math.max(...hours);
    for (let h = 0; h < 24; h++) {
      const v = hours[h];
      const isPeak = v === peak && v > 0;
      const bg = v > 0 ? `background:${isPeak ? '#f43f5e' : '#f59e0b'}33;` : '';
      const color = v > 0 ? (isPeak ? '#f43f5e' : '#f59e0b') : 'text-slate-600';
      html += `<div class="text-center p-1.5 rounded ${bg}">
        <div class="text-[10px] font-mono ${color}">${String(h).padStart(2, '0')}:00</div>
        <div class="text-[9px] ${color}">${v > 0 ? v.toLocaleString() : '—'}</div>
      </div>`;
    }
    html += '</div>';
    content.innerHTML = html;
    panel.classList.remove('hidden');
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function closeDayDetail() {
    document.getElementById('dossierDayDetail').classList.add('hidden');
  }

function closePlayerDossier() {
    document.getElementById('playerDossierPanel').classList.add('hidden');
    disposePlayerCharts();
    _dossierCalendarDate = null;
    _dossierDayTimestamps = null;
    document.getElementById('dossierDayDetail').classList.add('hidden');
    window._currentPlayerIdx = null;
  }

    function openPlayerDossierById(pid, contextTab) {
      if (!DOSSIER) return;
      const entry = DOSSIER.players.find(p => p.pid === pid);
      if (!entry) return;
      switchTab('players');
      setTimeout(() => openPlayerDossier(entry.id), 90);
    }

    // ── OPERATOR DOSSIERS ────────────────────────────────────────
    let filteredOperators = DOSSIER ? [...(DOSSIER.operators||[])] : [];

    function initOperatorDossiers() {
      if (!DOSSIER) return;
      const countries = [...new Set((DOSSIER.operators||[]).map(o => o.countries).filter(Boolean))].sort();
      const sel = document.getElementById('operatorCountryFilter');
      if (sel) countries.forEach(c => { const opt = document.createElement('option'); opt.value = c; opt.text = c; sel.appendChild(opt); });
      const cnt = document.getElementById('operatorDossierCount');
      if (cnt) cnt.textContent = (DOSSIER.operators||[]).length;
      renderOperatorCards();
    }

    function filterOperatorDossiers() {
      if (!DOSSIER) return;
      const q = (document.getElementById('operatorSearch')?.value || '').toLowerCase();
      const country = document.getElementById('operatorCountryFilter')?.value || '';
      filteredOperators = (DOSSIER.operators||[]).filter(o => {
        const matchQ = !q || (o.operator||'').toLowerCase().includes(q) || (o.countries||'').toLowerCase().includes(q);
        const matchCountry = !country || o.countries === country;
        return matchQ && matchCountry;
      });
      renderOperatorCards();
    }

    function renderOperatorCards() {
      const grid = document.getElementById('operatorCardsGrid');
      if (!grid || !DOSSIER) return;
      const fc = document.getElementById('operatorFilterCount');
      if (fc) fc.textContent = `${filteredOperators.length} of ${(DOSSIER.operators||[]).length} operators`;
      grid.innerHTML = filteredOperators.map(o => {
        const flag = flagOf(o.countries);
        const holdColor = o.hold_margin_pct > 3 ? '#10b981' : (o.hold_margin_pct > 1 ? '#f59e0b' : '#f43f5e');
        const holdBg = o.hold_margin_pct > 3 ? 'bg-emerald-500/20 text-emerald-400' : (o.hold_margin_pct > 1 ? 'bg-amber-500/20 text-amber-400' : 'bg-rose-500/20 text-rose-400');
        return `<div onclick="openOperatorDossier(${(DOSSIER.operators||[]).indexOf(o)})"
          class="glass-card rounded-2xl p-4 cursor-pointer hover:scale-[1.02] transition-all duration-200 border border-cyan-500/20">
          <div class="flex items-start justify-between mb-2">
            <div class="font-mono text-sm font-bold text-white truncate max-w-[190px]" title="${o.operator}">${o.operator}</div>
            <span class="px-2 py-0.5 rounded-full text-[9px] font-bold ${holdBg}">${(o.hold_margin_pct||0).toFixed(2)}% Hold</span>
          </div>
          <div class="text-[10px] text-slate-400 mb-2">${flag} ${o.countries||'Unknown'}</div>
          <div class="grid grid-cols-3 gap-2 text-xs">
            <div><span class="text-slate-400 text-[10px]">GGR</span><br><strong class="text-emerald-400 font-mono">${fmtN(o.ggr)}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Players</span><br><strong class="text-white font-mono">${(o.unique_players||0).toLocaleString()}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Bets/Player</span><br><strong class="text-cyan-400 font-mono">${(o.bets_per_player||0).toFixed(0)}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Total Volume</span><br><strong class="text-amber-400 font-mono">${fmtN(o.total_debit)}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Total Bets</span><br><strong class="text-slate-300 font-mono">${(o.total_bets||0).toLocaleString()}</strong></div>
            <div><span class="text-slate-400 text-[10px]">Avg Bet</span><br><strong class="text-indigo-400 font-mono">${fmtN(o.avg_bet)}</strong></div>
          </div>
        </div>`;
      }).join('');
    }

    let operatorChartInstances = {};
    function disposeOperatorCharts() {
      Object.values(operatorChartInstances).forEach(c => { try { c.dispose(); } catch(e){} });
      operatorChartInstances = {};
    }

    function openOperatorDossier(idx) {
      if (!DOSSIER) return;
      const o = (DOSSIER.operators||[])[idx];
      if (!o) return;
      window._currentOperatorIdx = idx;
      const panel = document.getElementById('operatorDossierPanel');
      panel.classList.remove('hidden');
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
      disposeOperatorCharts();

      const badge = document.getElementById('dossierOperatorBadge');
      badge.innerHTML = `<i class="fa-solid fa-building-columns mr-1"></i>${flagOf(o.countries)} ${o.countries||'Unknown'}`;
      badge.style = 'background:#06b6d422;border:1px solid #06b6d455;color:#06b6d4';
      document.getElementById('dossierOperatorTitle').textContent = o.operator;
      document.getElementById('dossierOperatorSub').textContent = `Hold Margin: ${(o.hold_margin_pct||0).toFixed(2)}% · Raw RTP: ${(o.operator_roi||0).toFixed(2)}% · ${(o.unique_players||0).toLocaleString()} unique players · ${(o.bets_per_player||0).toFixed(0)} bets/player`;

      document.getElementById('dossierOperatorKPIs').innerHTML = [
        kpiCard('Total Volume', fmtN(o.total_debit), 'text-cyan-400', 'fa-solid fa-coins'),
        kpiCard('Net GGR', fmtN(o.ggr), 'text-emerald-400', 'fa-solid fa-sack-dollar'),
        kpiCard('Hold %', (o.hold_margin_pct||0).toFixed(2)+'%', o.hold_margin_pct>3?'text-emerald-400':o.hold_margin_pct>1?'text-amber-400':'text-rose-400', 'fa-solid fa-percent'),
        kpiCard('Unique Players', (o.unique_players||0).toLocaleString(), 'text-white', 'fa-solid fa-users'),
        kpiCard('Bets/Player', (o.bets_per_player||0).toFixed(0), 'text-indigo-400', 'fa-solid fa-chart-bar'),
        kpiCard('Avg Bet', fmtN(o.avg_bet), 'text-amber-400', 'fa-solid fa-arrow-up-right-dots')
      ].join('');

      const t = dossierTheme();

      // Games breakdown bar
      const opGmDom = document.getElementById('dossierOpGamesChart');
      if (opGmDom && o.games && o.games.length) {
        const gc = echarts.init(opGmDom);
        operatorChartInstances['games'] = gc;
        const games = o.games.filter(g => g.game !== 'Unknown');
        gc.setOption({
          backgroundColor: t.bg,
          tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10},
            formatter: ps => { const d = ps[0].data; return `<strong>${ps[0].name}</strong><br>Bets: ${(d.bets||0).toLocaleString()}<br>Volume: ${fmtN(d.debit||0)}<br>Hold Margin: ${(d.hold_margin_pct||0).toFixed(2)}%`; } },
          grid: { top:20, right:20, bottom:50, left:60 },
          xAxis: { type:'category', data:games.map(g=>g.game), axisLabel:{color:t.textColor,fontSize:9,rotate:20} },
          yAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:8,formatter:v=>fmtN(v)}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
          series: [{ type:'bar', data:games.map(g=>({value:g.bets, bets:g.bets, debit:g.debit, hold_margin_pct:g.hold_margin_pct, itemStyle:{color:GAME_COLORS[g.game]||'#64748b', borderRadius:[4,4,0,0]}})) }]
        });
      }

      // Hourly load
      const opHrsDom = document.getElementById('dossierOpHoursChart');
      if (opHrsDom && o.hours && o.hours.length) {
        const hc = echarts.init(opHrsDom);
        operatorChartInstances['hours'] = hc;
        const peak = Math.max(...o.hours);
        hc.setOption({
          backgroundColor: t.bg,
          grid: { top:10, right:20, bottom:30, left:55 },
          tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10}, formatter: ps => `${ps[0].name}<br>Bets: <strong>${ps[0].value.toLocaleString()}</strong>` },
          xAxis: { type:'category', data:Array.from({length:24},(_,i)=>`${i}:00`), axisLabel:{color:t.textColor,fontSize:8} },
          yAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:8}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
          series: [{ type:'bar', data:o.hours.map(v=>({ value:v, itemStyle:{ color: v===peak ? '#f43f5e' : '#06b6d4', borderRadius:[3,3,0,0] } })) }]
        });
      }

      // Device mix
      const opDevDom = document.getElementById('dossierOpDeviceChart');
      if (opDevDom && o.devices) {
        const dc = echarts.init(opDevDom);
        operatorChartInstances['device'] = dc;
        dc.setOption({
          backgroundColor: t.bg,
          tooltip: { trigger:'item', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:10} },
          series: [{ type:'pie', radius:['35%','60%'], data:[
            {name:'Mobile',value:o.devices['Mobile']||0,itemStyle:{color:'#6366f1'}},
            {name:'Desktop',value:o.devices['Desktop']||0,itemStyle:{color:'#06b6d4'}}
          ], label:{color:t.textColor,fontSize:9} }]
        });
      }

      // Top players table
      const tp = o.top_players || [];
      const tpDom = document.getElementById('dossierOpPlayersTable');
      if (tpDom) {
        if (!tp.length) {
          tpDom.innerHTML = '<p class="text-xs text-slate-500 italic">No player-level data captured for this operator in the audit window.</p>';
        } else {
          tpDom.innerHTML = `<table class="w-full text-xs text-slate-300 border-collapse">
            <thead><tr class="border-b border-slate-700 text-slate-500 text-[10px] uppercase">
              <th class="py-1 px-2 text-left">#</th>
              <th class="py-1 px-2 text-left">Player ID</th>
              <th class="py-1 px-2 text-right">Bets</th>
              <th class="py-1 px-2 text-right">Volume</th>
              <th class="py-1 px-2 text-right">Net W/L</th>
              <th class="py-1 px-2 text-right">Share</th>
              <th class="py-1 px-2 text-center">Dossier</th>
            </tr></thead>
            <tbody>${tp.map((pl,i)=>`<tr class="border-b border-slate-800/50 hover:bg-slate-800/30">
              <td class="py-1 px-2 text-slate-500">${i+1}</td>
              <td class="py-1 px-2 font-mono text-[10px] text-slate-300">${pl.player_id}</td>
              <td class="py-1 px-2 text-right text-slate-400">${(pl.bets||0).toLocaleString()}</td>
              <td class="py-1 px-2 text-right text-amber-400 font-mono">${fmtN(pl.debit||0)}</td>
              <td class="py-1 px-2 text-right font-mono ${(pl.winlose||0)<0?'text-emerald-400':'text-rose-400'}">${(pl.winlose||0)<0?'+'+fmtN(Math.abs(pl.winlose)):'−'+fmtN(Math.abs(pl.winlose))}</td>
              <td class="py-1 px-2 text-right text-cyan-400">${(pl.share_pct||0).toFixed(2)}%</td>
              <td class="py-1 px-2 text-center"><button onclick="event.stopPropagation(); openPlayerDossierById('${pl.player_id}', 'opdossiers')" class="px-1.5 py-0.5 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-[9px] font-semibold border border-amber-500/30"><i class="fa-solid fa-user-secret mr-0.5"></i>Open</button></td>
            </tr>`).join('')}</tbody>
          </table>`;
        }
      }
    }

    function closeOperatorDossier() {
      document.getElementById('operatorDossierPanel').classList.add('hidden');
      disposeOperatorCharts();
      window._currentOperatorIdx = null;
    }

    function openOperatorDossierById(name) {
      if (!DOSSIER) return;
      const idx = (DOSSIER.operators||[]).findIndex(o => o.operator === name);
      if (idx < 0) return;
      switchTab('opdossiers');
      setTimeout(() => openOperatorDossier(idx), 90);
    }

    // ── CSV EXPORT ───────────────────────────────────────────────
    function exportDossierCSV(type) {
      if (!DOSSIER) return;
      let rows = [];
      if (type === 'players') {
        rows.push(['rank','player_id','archetype','country','primary_operator','total_debit','total_winlose','total_bets','avg_bet','spike_multiplier','is_whale','is_chaser']);
        DOSSIER.players.forEach(p => rows.push([p.id, p.pid, p.arch, p.country, p.op, p.debit, p.winlose, p.bets, p.avg_bet, p.spike, p.whale, p.chaser]));
      } else {
        rows.push(['operator','countries','total_debit','total_winlose','net_ggr','hold_margin_pct','operator_roi_pct','total_bets','unique_players','bets_per_player','avg_bet']);
        (DOSSIER.operators||[]).forEach(o => rows.push([o.operator, o.countries, o.total_debit, o.total_winlose, o.ggr, o.hold_margin_pct, o.operator_roi, o.total_bets, o.unique_players, o.bets_per_player, o.avg_bet]));
      }
      const csv = rows.map(r => r.map(v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"').join(',')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const a = document.createElement('a');
      a.download = type === 'players' ? 'all_player_dossiers.csv' : 'operator_dossiers.csv';
      a.href = URL.createObjectURL(blob);
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    // ── PRESENTATION SLIDE CHARTS (Slides 7 & 8) ─────────────────
    let dossierSlideCharts = {};
    function disposeDossierSlideCharts() {
      Object.values(dossierSlideCharts).forEach(c => { try { c.dispose(); } catch(e){} });
      dossierSlideCharts = {};
    }

    function renderDossierSlideCharts(idx) {
      if (!DOSSIER || (idx !== 7 && idx !== 8)) { if (idx !== 7 && idx !== 8) disposeDossierSlideCharts(); return; }
      disposeDossierSlideCharts();
      const t = dossierTheme();

      if (idx === 7) {
        // Archetype distribution
        const archDom = document.getElementById('slidePlayerArchChart');
        if (archDom) {
          const groups = {};
          DOSSIER.players.forEach(p => {
            const a = p.arch || 'Player';
            let g = 'Other';
            if (a.includes('Extreme')) g = 'Extreme Chaser';
            else if (a.includes('Critical')) g = 'Critical Chaser';
            else if (a.includes('Lightning')) g = 'Lightning Whale';
            else if (a.includes('Grinder')) g = 'Grinder Whale';
            else if (a.includes('Whale')) g = 'VIP Whale';
            else if (a.includes('VIP High Roller')) g = 'VIP High Roller';
            else if (a.includes('High Roller')) g = 'High Roller';
            else if (a.includes('Mid Roller')) g = 'Mid Roller';
            else if (a.includes('Active')) g = 'Active Player';
            else if (a.includes('Casual')) g = 'Casual Player';
            else if (a.includes('Chaser')) g = 'Other Chaser';
            groups[g] = (groups[g] || 0) + 1;
          });
          const names = Object.keys(groups);
          const c1 = echarts.init(archDom);
          dossierSlideCharts['arch'] = c1;
          c1.setOption({
            backgroundColor: t.bg,
            grid: { top:15, right:20, bottom:30, left:110 },
            tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:11} },
            xAxis: { type:'value', axisLabel:{color:t.textColor}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
            yAxis: { type:'category', data:names, inverse:true, axisLabel:{color:t.textColor,fontSize:10} },
            series: [{ type:'bar', data:names.map(n=>({ value:groups[n], itemStyle:{ color: archetypeColor(n.includes('Whale') ? 'VIP Whale' : n.includes('Extreme') ? 'Extreme Chaser' : n.includes('Critical') ? 'Critical Chaser' : n), borderRadius:[0,5,5,0] } })),
              label:{ show:true, position:'right', color:t.textColor, fontSize:10 } }]
          });
        }
        // Top 8 players by debit
        const tpDom = document.getElementById('slideTopPlayersChart');
        if (tpDom) {
          const top = [...DOSSIER.players].sort((a,b) => (b.debit||0)-(a.debit||0)).slice(0,8);
          const c2 = echarts.init(tpDom);
          dossierSlideCharts['topPlayers'] = c2;
          c2.setOption({
            backgroundColor: t.bg,
            grid: { top:10, right:60, bottom:20, left:110 },
            tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:11}, formatter: ps => `<strong>${ps[0].name}</strong><br>Debit: ${fmtN(ps[0].value)}` },
            xAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:9,formatter:v=>fmtN(v)}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
            yAxis: { type:'category', data:top.map(p=>p.pid), inverse:true, axisLabel:{color:t.textColor,fontSize:9} },
            series: [{ type:'bar', data:top.map(p=>({ value:p.debit, itemStyle:{ color: p.chaser ? '#f43f5e' : '#f59e0b', borderRadius:[0,5,5,0] } })),
              label:{ show:true, position:'right', color:t.textColor, fontSize:9, formatter: pr => fmtN(pr.value) } }]
          });
        }
      }

      if (idx === 8) {
        // Top 8 operators by GGR
        const ggrDom = document.getElementById('slideOpGgrChart');
        if (ggrDom) {
          const top = [...(DOSSIER.operators||[])].sort((a,b) => (b.ggr||0)-(a.ggr||0)).slice(0,8);
          const c1 = echarts.init(ggrDom);
          dossierSlideCharts['opGgr'] = c1;
          c1.setOption({
            backgroundColor: t.bg,
            grid: { top:10, right:60, bottom:20, left:110 },
            tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:11}, formatter: ps => `<strong>${ps[0].name}</strong><br>Net GGR: ${fmtN(ps[0].value)}` },
            xAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:9,formatter:v=>fmtN(v)}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
            yAxis: { type:'category', data:top.map(o=>o.operator), inverse:true, axisLabel:{color:t.textColor,fontSize:9} },
            series: [{ type:'bar', data:top.map(o=>({ value:o.ggr, itemStyle:{ color:'#10b981', borderRadius:[0,5,5,0] } })),
              label:{ show:true, position:'right', color:t.textColor, fontSize:9, formatter: pr => fmtN(pr.value) } }]
          });
        }
        // Hold margin for top 8 by volume
        const holdDom = document.getElementById('slideOpHoldChart');
        if (holdDom) {
          const top = [...(DOSSIER.operators||[])].sort((a,b) => (b.total_debit||0)-(a.total_debit||0)).slice(0,8);
          const c2 = echarts.init(holdDom);
          dossierSlideCharts['opHold'] = c2;
          c2.setOption({
            backgroundColor: t.bg,
            grid: { top:10, right:50, bottom:30, left:110 },
            tooltip: { trigger:'axis', backgroundColor:t.tooltipBg, borderColor:t.tooltipBorder, textStyle:{color:t.tooltipText,fontSize:11}, formatter: ps => `<strong>${ps[0].name}</strong><br>Hold Margin: ${ps[0].value}%<br>Volume: ${fmtN(top[ps[0].dataIndex].total_debit)}` },
            xAxis: { type:'value', axisLabel:{color:t.textColor,fontSize:9,formatter:v=>v+'%'}, splitLine:{lineStyle:{color:t.gridBorder,type:'dashed'}} },
            yAxis: { type:'category', data:top.map(o=>o.operator), inverse:true, axisLabel:{color:t.textColor,fontSize:9} },
            series: [{ type:'bar', data:top.map(o=>({ value:o.hold_margin_pct, itemStyle:{ color: o.hold_margin_pct>3 ? '#10b981' : (o.hold_margin_pct>1 ? '#f59e0b' : '#f43f5e'), borderRadius:[0,5,5,0] } })),
              label:{ show:true, position:'right', color:t.textColor, fontSize:9, formatter: pr => pr.value.toFixed(2)+'%' } }]
          });
        }
      }
    }

    // ── INTEGRATION HOOKS ────────────────────────────────────────
    (function patchDashboardHooks() {
      // 1. switchTab: lazy-init dossier browsers on first visit
      const origSwitchTab = window.switchTab;
      window.switchTab = function(tabId) {
        origSwitchTab(tabId);
        if (tabId === 'players' && !window._playersInited) { window._playersInited = true; initPlayerDossiers(); }
        if (tabId === 'opdossiers' && !window._operatorsInited) { window._operatorsInited = true; initOperatorDossiers(); }
      };

      // 2. Whale scatter click → open player dossier (works for ALL players)
      const origScatter = window.initWhaleScatterChart;
      window.initWhaleScatterChart = function() {
        origScatter();
        const c = chartInstances['whaleScatter'];
        if (c && !c._dossierLinked) {
          c._dossierLinked = true;
          c.on('click', function(params) {
            if (params.value && params.value[3]) openPlayerDossierById(String(params.value[3]), 'whales');
          });
        }
      };

      // 3. Operator bubble click → open operator dossier
      const origBubble = window.initOperatorBubbleChart;
      window.initOperatorBubbleChart = function() {
        origBubble();
        const c = chartInstances['operatorBubble'];
        if (c && !c._dossierLinked) {
          c._dossierLinked = true;
          c.on('click', function(params) {
            if (params.value && params.value[3]) openOperatorDossierById(String(params.value[3]));
          });
        }
      };

      // 4. Slide deck: render dossier slide charts on navigation
      const origRenderSlides = window.renderSlideCharts;
      window.renderSlideCharts = function() {
        origRenderSlides();
        renderDossierSlideCharts(currentSlide);
      };

      // 5. Theme toggle / reinit: dispose dossier charts and re-render open panels
      const origReinit = window.reinitAllCharts;
      window.reinitAllCharts = function() {
        origReinit();
        disposePlayerCharts();
        disposeOperatorCharts();
        if (window._currentPlayerIdx != null && !document.getElementById('playerDossierPanel').classList.contains('hidden')) {
          openPlayerDossier(window._currentPlayerIdx);
        }
        if (window._currentOperatorIdx != null && !document.getElementById('operatorDossierPanel').classList.contains('hidden')) {
          openOperatorDossier(window._currentOperatorIdx);
        }
      };
    })();
