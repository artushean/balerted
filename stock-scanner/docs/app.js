function badge(text, klass) {
  return `<span class="badge ${klass}">${text}</span>`;
}

function cardMarkup(a) {
  const badges = [];
  if (a.breakout_52w) badges.push(badge('🚀 52W breakout', 'breakout'));
  if (a.breakout_20d) badges.push(badge('📈 20D breakout', 'breakout'));
  if (a.conviction === 'Extreme') badges.push(badge('🔥 Extreme', 'extreme'));
  if (a.relative_strength > 3) badges.push(badge('💪 Strong RS', 'strong'));

  return `
    <article class="card">
      <div class="card-head">
        <h3>${a.symbol}</h3>
        <div class="score">${a.momentum_score}</div>
      </div>
      <p class="muted">${a.conviction} conviction</p>
      <div class="badge-row">${badges.join(' ')}</div>
      <dl class="grid">
        <div><dt>Price</dt><dd>$${a.price}</dd></div>
        <div><dt>Daily</dt><dd>${a.daily_pct}%</dd></div>
        <div><dt>15m</dt><dd>${a['15m_pct']}%</dd></div>
        <div><dt>Rel.Str</dt><dd>${a.relative_strength}%</dd></div>
        <div><dt>Volume</dt><dd>${a.volume_mult}x</dd></div>
        <div><dt>RSI</dt><dd>${a.rsi}</dd></div>
      </dl>
    </article>
  `;
}

async function load() {
  const res = await fetch('./latest_data.json', { cache: 'no-store' });
  const data = await res.json();

  document.getElementById('updated').textContent = `Updated: ${new Date(data.last_updated).toLocaleString()}`;
  document.getElementById('total').textContent = `Signals: ${data.total_alerts}`;
  document.getElementById('universe').textContent = `Universe: ${data.scan_universe || 'N/A'} symbols`;

  const root = document.getElementById('alerts');
  root.innerHTML = (data.alerts || []).map(cardMarkup).join('');
}

load().catch((err) => {
  document.getElementById('alerts').textContent = `Failed to load data: ${err}`;
});
