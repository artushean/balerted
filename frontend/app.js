const API = window.API_BASE || '';

async function getJSON(path, options={}) {
  const res = await fetch(`${API}${path}`, {headers:{'Content-Type':'application/json'}, ...options});
  return res.json();
}

function cls(v){ return v >= 0 ? 'pos' : 'neg'; }
function scoreBadge(score){ if(score>=4) return '<span class="badge high">High</span>'; if(score>=3) return '<span class="badge medium">Medium</span>'; return score; }

async function renderWatchlist(){
  const watch = await getJSON('/api/watchlist');
  const ul = document.getElementById('watchlist');
  ul.innerHTML='';
  watch.forEach(w=>{
    const li=document.createElement('li');
    li.className='watch-item';
    li.innerHTML=`<span><strong>${w.symbol}</strong> ${w.note||''}</span><button class="small" data-s="${w.symbol}">Remove</button>`;
    ul.appendChild(li);
  });
  ul.querySelectorAll('button').forEach(btn=>btn.onclick=async()=>{await getJSON('/api/watchlist/remove',{method:'POST',body:JSON.stringify({symbol:btn.dataset.s})}); await refresh();});
}

async function renderTable(){
  const data = await getJSON('/api/latest');
  const tbody = document.getElementById('rows');
  tbody.innerHTML='';
  data.forEach(r=>{
    const tr=document.createElement('tr');
    if(r.watchlist) tr.className='watch-row';
    tr.innerHTML=`<td>${r.symbol}${r.watchlist?' ⭐':''}</td><td>${r.price}</td><td class="${cls(r.daily_pct)}">${r.daily_pct}%</td><td class="${cls(r['15m_pct'])}">${r['15m_pct']}%</td><td>${r.volume_mult}</td><td>${r.rsi}</td><td>${r.atr_ratio}</td><td>${scoreBadge(r.score)}</td>`;
    tbody.appendChild(tr);
  });
}

async function refresh(){ await renderWatchlist(); await renderTable(); }

document.getElementById('addBtn').onclick = async()=>{
  const symbol=document.getElementById('ticker').value.trim();
  const note=document.getElementById('note').value.trim();
  if(!symbol) return;
  await getJSON('/api/watchlist/add',{method:'POST',body:JSON.stringify({symbol,note})});
  document.getElementById('ticker').value=''; document.getElementById('note').value='';
  await refresh();
};

refresh();
setInterval(renderTable, 60000);
