const API = window.API_BASE || '';

async function getJSON(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}

function badge(text, cls) {
  return `<span class="badge ${cls}">${text}</span>`;
}

function renderCards(alerts) {
  const tbody = document.getElementById('rows');
  tbody.innerHTML = '';
  alerts.forEach((r) => {
    const tr = document.createElement('tr');
    const badges = [];
    if (r.breakout_52w) badges.push('🚀');
    if (r.breakout_20d) badges.push('📈');
    if (r.conviction === 'Extreme') badges.push('🔥');
    if (r.relative_strength > 3) badges.push('💪');
    tr.innerHTML = `<td>${r.symbol}${r.watchlist ? ' ⭐' : ''} ${badges.join(' ')}</td><td>${r.price}</td><td>${r.daily_pct}%</td><td>${r['15m_pct']}%</td><td>${r.volume_mult}</td><td>${r.relative_strength}</td><td>${r.conviction}</td><td>${r.score}</td>`;
    tbody.appendChild(tr);
  });
}

function setMeta(lastUpdated, totalAlerts) {
  document.getElementById('lastUpdated').textContent = `Last updated: ${lastUpdated || 'N/A'}`;
  document.getElementById('totalAlerts').textContent = `Total alerts: ${totalAlerts ?? 0}`;
}

async function renderFromStatic() {
  const data = await getJSON('./latest_data.json', { cache: 'no-store' });
  setMeta(data.last_updated, data.total_alerts);
  renderCards(data.alerts || []);
}

async function renderFromApi() {
  const data = await getJSON('/api/latest');
  setMeta(new Date().toISOString(), data.length);
  renderCards(data || []);
}

async function refresh() {
  // GitHub Pages/serverless mode first.
  try {
    await renderFromStatic();
    document.getElementById('mode').innerHTML = badge('Serverless JSON mode', 'medium');
    return;
  } catch (_err) {
    // fallback to local API mode
  }

  await renderFromApi();
  document.getElementById('mode').innerHTML = badge('Local API mode', 'high');
}

refresh().catch((err) => {
  document.getElementById('rows').innerHTML = `<tr><td colspan="8">Failed to load data: ${err}</td></tr>`;
});

setInterval(refresh, 60000);
