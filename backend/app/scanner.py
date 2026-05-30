from __future__ import annotations

from datetime import date, timedelta

from backend.app.config import get_settings
from backend.app.models import ScanFilters, ScanResult
from backend.app.services.cluster import detect_clusters
from backend.app.services.scoring import divergence_score
from backend.app.services.sec_fetcher import fetch_form4_transactions
from backend.app.services.valuation import fetch_valuation


def run_scan(filters: ScanFilters) -> list[ScanResult]:
    settings = get_settings()
    tickers = filters.tickers or settings.scan_tickers
    transactions = fetch_form4_transactions(tickers=tickers, lookback_days=filters.lookback_days)
    max_filing_age = date.today() - timedelta(days=filters.max_filing_delay_days)
    transactions = [
        tx
        for tx in transactions
        if tx.filing_date is None or tx.filing_date >= max_filing_age
    ]
    clusters = detect_clusters(transactions, window_days=filters.cluster_window_days)

    results: list[ScanResult] = []
    for ticker, insiders in clusters.items():
        total_value = sum(tx.value for tx in insiders)
        snapshot = fetch_valuation(ticker)
        if filters.exclude_penny_stocks and snapshot.current_price is not None and snapshot.current_price < 1:
            continue
        if snapshot.market_cap is not None and snapshot.market_cap < filters.min_market_cap:
            continue
        score, signal, rationale, averages = divergence_score(snapshot, total_value)
        results.append(
            ScanResult(
                ticker=ticker,
                company_name=insiders[0].company_name,
                cluster_size=len({tx.insider_name for tx in insiders}),
                total_cluster_value=total_value,
                score=score,
                signal=signal,
                valuation=snapshot,
                rationale=rationale,
                insiders=sorted(insiders, key=lambda tx: tx.transaction_date, reverse=True),
                peer_averages=averages,
                peer_multiples=snapshot.peers,
            )
        )
    return sorted(results, key=lambda item: (item.score, item.total_cluster_value), reverse=True)
