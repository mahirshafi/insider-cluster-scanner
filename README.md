# Insider Cluster & Divergence Stock Scanner

A FastAPI web app that scans for insider cluster buying and compares those signals with valuation/analyst divergence.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Open <http://localhost:8000> and click **Scan Now**.

## Configuration

Optional environment variables:

- `SCANNER_API_KEY`: require clients to send `X-API-Key` on `/scan`.
- `FMP_API_KEY`: enables Financial Modeling Prep analyst/fundamental data if available.
- `SEC_USER_AGENT`: SEC-compliant user agent, e.g. `name email@example.com`.
- `SCAN_TICKERS`: comma-separated ticker universe for SEC scans; defaults to a small liquid sample for MVP.

No API keys are committed. If data providers rate-limit or omit data, fields fall back to `N/A` and scoring continues.
