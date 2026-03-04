async function load() {
  const res = await fetch('./latest_data.json', { cache: 'no-store' });
  const data = await res.json();

  document.getElementById('updated').textContent = `Last updated: ${data.last_updated}`;
  document.getElementById('total').textContent = `Total alerts: ${data.total_alerts}`;

  const root = document.getElementById('alerts');
  root.innerHTML = '';

  data.alerts.forEach((a) => {
    const card = document.createElement('article');
    card.className = 'card';

    const badges = [];
    if (a.breakout_52w) badges.push('<span class="badge breakout">🚀 52W breakout</span>');
    if (a.breakout_20d) badges.push('<span class="badge breakout">📈 20D breakout</span>');
    if (a.conviction === 'Extreme') badges.push('<span class="badge extreme">🔥 Extreme</span>');
    if (a.relative_strength > 3) badges.push('<span class="badge strong">Strong vs market</span>');

    card.innerHTML = `
      <h3>${a.symbol} (${a.conviction})</h3>
      <p>${badges.join(' ')}</p>
      <p>Price: $${a.price}</p>
      <p>Daily: ${a.daily_pct}% | 15m: ${a['15m_pct']}%</p>
      <p>RS: ${a.relative_strength}% | Vol: ${a.volume_mult}x</p>
      <p>Score: ${a.score}</p>
    `;
    root.appendChild(card);
  });
}

load().catch((err) => {
  document.getElementById('alerts').textContent = `Failed to load data: ${err}`;
});
