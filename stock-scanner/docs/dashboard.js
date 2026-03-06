function pctClass(value) {
  return Number(value) >= 0 ? 'pos' : 'neg';
}

function fmtPct(value) {
  const num = Number(value || 0);
  return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
}

function rowCells(values) {
  return `<tr>${values.map((v) => `<td>${v}</td>`).join('')}</tr>`;
}

function fillSimpleTable(elId, items, fallback) {
  const tbody = document.getElementById(elId);
  if (!items.length) {
    tbody.innerHTML = rowCells([fallback]);
    return;
  }
  tbody.innerHTML = items
    .map((item) => rowCells([
      item.symbol,
      `<span class="${pctClass(item.daily_pct)}">${fmtPct(item.daily_pct)}</span>`,
      `<span class="${pctClass(item.relative_strength)}">${fmtPct(item.relative_strength)}</span>`,
      item.momentum_score ?? '--',
    ]))
    .join('');
}

function fill52WeekTable(elId, items, fallback) {
  const tbody = document.getElementById(elId);
  if (!items.length) {
    tbody.innerHTML = rowCells([fallback]);
    return;
  }

  tbody.innerHTML = items
    .map((item) => {
      const awayFromHigh = Number(item.distance_to_52w_high || 0);
      return rowCells([
        item.symbol,
        `<span class="${pctClass(item.daily_pct)}">${fmtPct(item.daily_pct)}</span>`,
        `-${awayFromHigh.toFixed(2)}% from 52W high`,
        item.momentum_score ?? '--',
      ]);
    })
    .join('');
}

async function loadCryptoTop100() {
  const response = await fetch(
    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false',
    { cache: 'no-store' }
  );
  if (!response.ok) return [];
  const coins = await response.json();
  return coins.map((c) => ({
    symbol: c.symbol.toUpperCase(),
    name: c.name,
    price: c.current_price,
    daily_pct: c.price_change_percentage_24h ?? 0,
    relative_strength: c.price_change_percentage_24h ?? 0,
    momentum_score: Math.min(100, Math.max(0, Math.round((c.price_change_percentage_24h ?? 0) * 4 + 50))),
  }));
}

function renderCryptoTable(coins) {
  const tbody = document.getElementById('cryptoBody');
  if (!coins.length) {
    tbody.innerHTML = rowCells(['Crypto feed unavailable']);
    return;
  }

  const top10 = [...coins]
    .sort((a, b) => Math.abs(b.daily_pct) - Math.abs(a.daily_pct))
    .slice(0, 10);

  tbody.innerHTML = top10
    .map((coin) => rowCells([
      coin.name,
      coin.symbol,
      `$${Number(coin.price).toLocaleString()}`,
      `<span class="${pctClass(coin.daily_pct)}">${fmtPct(coin.daily_pct)}</span>`,
    ]))
    .join('');
}

async function loadData() {
  const errorMessage = document.getElementById('errorMessage');

  try {
    errorMessage.hidden = true;
    const [scannerRes, crypto] = await Promise.all([
      fetch('/data/latest_data.json', { cache: 'no-store' }).then((res) => {
        if (!res.ok) throw new Error('scanner');
        return res.json();
      }),
      loadCryptoTop100().catch(() => []),
    ]);

    document.getElementById('total').textContent = `Signals: ${scannerRes.total_alerts ?? 0}`;
    document.getElementById('universe').textContent = `Universe: ${scannerRes.scan_universe ?? 'N/A'}`;
    document.getElementById('updated').textContent = `Last Updated: ${new Date(scannerRes.last_updated).toLocaleString()}`;

    const stockAlerts = scannerRes.alerts || [];
    const momentumTitle = document.getElementById('momentumTitle');
    momentumTitle.textContent = stockAlerts.length ? 'Top Momentum Signals' : 'Top Momentum Stocks Today';
    fillSimpleTable('momentumBody', stockAlerts, 'No stock momentum signals in latest scan');

    const combined = [
      ...stockAlerts,
      ...crypto.map((c) => ({
        symbol: c.symbol,
        daily_pct: c.daily_pct,
        relative_strength: c.relative_strength,
        momentum_score: c.momentum_score,
      })),
    ];

    fillSimpleTable('moversBody', [...combined].sort((a, b) => Math.abs(b.daily_pct) - Math.abs(a.daily_pct)).slice(0, 10), 'No movers');

    const sortedBy52wDistance = [...stockAlerts].sort(
      (a, b) => Number(a.distance_to_52w_high || 0) - Number(b.distance_to_52w_high || 0)
    );
    fill52WeekTable('gainers52Body', sortedBy52wDistance.slice(0, 10), 'No 52-week gainers');
    fill52WeekTable('losers52Body', sortedBy52wDistance.reverse().slice(0, 10), 'No 52-week losers');

    renderCryptoTable(crypto);
  } catch (error) {
    document.getElementById('momentumBody').innerHTML = '';
    document.getElementById('moversBody').innerHTML = '';
    document.getElementById('gainers52Body').innerHTML = '';
    document.getElementById('losers52Body').innerHTML = '';
    document.getElementById('cryptoBody').innerHTML = '';
    errorMessage.hidden = false;
  }
}

loadData();
setInterval(() => window.location.reload(), 60000);
