from __future__ import annotations

import statistics

import requests
import yfinance as yf

from backend.app.config import get_settings
from backend.app.models import PeerMultiple, ValuationSnapshot
from backend.app.services.cache import TTLCache
from backend.app.services.logging import log_api_call

PEER_MAP: dict[str, list[str]] = {
    "AAPL": ["MSFT", "GOOGL", "META", "HPQ"],
    "MSFT": ["AAPL", "GOOGL", "ORCL", "ADBE"],
    "NVDA": ["AMD", "AVGO", "QCOM", "INTC"],
    "TSLA": ["F", "GM", "RIVN", "TM"],
    "JPM": ["BAC", "WFC", "C", "GS"],
    "HLNE": ["APO", "ARES", "BX", "KKR"],
    "AAT": ["KIM", "REG", "FRT", "BRX"],
}

_cache: TTLCache[ValuationSnapshot] | None = None


def _cache_instance() -> TTLCache[ValuationSnapshot]:
    global _cache
    if _cache is None:
        _cache = TTLCache(get_settings().cache_ttl_seconds)
    return _cache


def fetch_valuation(ticker: str) -> ValuationSnapshot:
    ticker = ticker.upper()
    cached = _cache_instance().get(ticker)
    if cached is not None:
        return cached

    snapshot = _fetch_yfinance_snapshot(ticker)
    _merge_fmp_quote(ticker, snapshot)
    snapshot.peers = [_fetch_peer_multiple(peer) for peer in PEER_MAP.get(ticker, [])]
    _cache_instance().set(ticker, snapshot)
    return snapshot


def peer_averages(peers: list[PeerMultiple]) -> dict[str, float | None]:
    return {
        "pe_forward": _mean([peer.pe_forward for peer in peers]),
        "pb": _mean([peer.pb for peer in peers]),
        "ps": _mean([peer.ps for peer in peers]),
    }


def _fetch_yfinance_snapshot(ticker: str) -> ValuationSnapshot:
    log_api_call("Yahoo Finance", f"ticker:{ticker}")
    info = yf.Ticker(ticker).get_info()
    return ValuationSnapshot(
        current_price=_number(info.get("currentPrice") or info.get("regularMarketPrice")),
        avg_target=_number(info.get("targetMeanPrice")),
        high_target=_number(info.get("targetHighPrice")),
        low_target=_number(info.get("targetLowPrice")),
        pe_forward=_number(info.get("forwardPE")),
        pb=_number(info.get("priceToBook")),
        ps=_number(info.get("priceToSalesTrailing12Months")),
        market_cap=int(info["marketCap"]) if info.get("marketCap") else None,
    )


def _fetch_peer_multiple(ticker: str) -> PeerMultiple:
    try:
        info = yf.Ticker(ticker).get_info()
    except Exception:
        return PeerMultiple(ticker=ticker)
    return PeerMultiple(
        ticker=ticker,
        pe_forward=_number(info.get("forwardPE")),
        pb=_number(info.get("priceToBook")),
        ps=_number(info.get("priceToSalesTrailing12Months")),
    )


def _merge_fmp_quote(ticker: str, snapshot: ValuationSnapshot) -> None:
    api_key = get_settings().fmp_api_key
    if not api_key:
        return
    url = f"https://financialmodelingprep.com/api/v3/price-target-consensus?symbol={ticker}&apikey={api_key}"
    try:
        log_api_call("FMP", url.split("apikey=")[0] + "apikey=***")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return
    if isinstance(data, list) and data:
        row = data[0]
        snapshot.avg_target = snapshot.avg_target or _number(row.get("targetConsensus"))
        snapshot.high_target = snapshot.high_target or _number(row.get("targetHigh"))
        snapshot.low_target = snapshot.low_target or _number(row.get("targetLow"))


def _number(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed or parsed <= 0:
        return None
    return parsed


def _mean(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None and value > 0]
    if not filtered:
        return None
    return statistics.fmean(filtered)
