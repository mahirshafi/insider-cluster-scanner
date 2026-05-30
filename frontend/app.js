const button = document.querySelector('#scanButton');
const statusEl = document.querySelector('#status');
const body = document.querySelector('#resultsBody');

button.addEventListener('click', async () => {
  const tickers = document.querySelector('#tickers').value
    .split(',')
    .map((ticker) => ticker.trim().toUpperCase())
    .filter(Boolean);
  const payload = {
    min_market_cap: Number(document.querySelector('#minMarketCap').value),
    max_filing_delay_days: Number(document.querySelector('#maxFilingDelay').value),
    exclude_penny_stocks: document.querySelector('#excludePenny').checked,
    lookback_days: 60,
    cluster_window_days: 30,
  };
  if (tickers.length) payload.tickers = tickers;

  setLoading(true);
  try {
    const response = await fetch('/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(await response.text());
    const results = await response.json();
    renderResults(results);
    statusEl.textContent = `Scan completed: ${new Date().toISOString().slice(0, 10)} (${results.length} clustered stock${results.length === 1 ? '' : 's'})`;
  } catch (error) {
    statusEl.textContent = `Scan failed: ${error.message}`;
    statusEl.classList.add('error');
  } finally {
    setLoading(false);
  }
});

function setLoading(isLoading) {
  button.disabled = isLoading;
  button.textContent = isLoading ? 'Scanning…' : 'Scan Now';
  statusEl.classList.remove('error');
  statusEl.textContent = isLoading ? 'Fetching filings, detecting clusters, and scoring divergence…' : statusEl.textContent;
}

function renderResults(results) {
  if (!results.length) {
    body.innerHTML = '<tr><td colspan="8" class="empty">No qualifying clusters found for the selected filters.</td></tr>';
    return;
  }
  body.innerHTML = results.map((result) => `
    <tr>
      <td><strong>${escapeHtml(result.ticker)}</strong><br>${escapeHtml(result.company_name || '')}</td>
      <td>${result.cluster_size}</td>
      <td>${formatMoney(result.total_cluster_value)}</td>
      <td><strong>${result.score}</strong></td>
      <td><span class="signal ${signalClass(result.signal)}">${escapeHtml(result.signal)}</span></td>
      <td>${formatMoney(result.valuation.avg_target)}</td>
      <td>${formatMoney(result.valuation.current_price)}</td>
      <td>
        ${escapeHtml(result.rationale.join('; '))}
        <details>
          <summary>Insiders & peers</summary>
          <ul class="mini">${result.insiders.map(formatInsider).join('')}</ul>
          <ul class="mini">${result.peer_multiples.map(formatPeer).join('')}</ul>
        </details>
      </td>
    </tr>`).join('');
}

function formatInsider(insider) {
  return `<li>${escapeHtml(insider.insider_name)} (${escapeHtml(insider.insider_title || 'title N/A')}): ${formatMoney(insider.value)} on ${escapeHtml(insider.transaction_date)}</li>`;
}

function formatPeer(peer) {
  return `<li>${escapeHtml(peer.ticker)} — P/E ${formatNumber(peer.pe_forward)}, P/B ${formatNumber(peer.pb)}, P/S ${formatNumber(peer.ps)}</li>`;
}

function signalClass(signal) {
  return signal.toLowerCase().replace(/\s+/g, '-');
}

function formatMoney(value) {
  if (value === null || value === undefined) return 'N/A';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: value > 1000 ? 0 : 2 }).format(value);
}

function formatNumber(value) {
  return value === null || value === undefined ? 'N/A' : Number(value).toFixed(1);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}
