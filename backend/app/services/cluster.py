from __future__ import annotations

from datetime import timedelta

from backend.app.models import InsiderTransaction

SENIOR_TITLE_KEYWORDS = ("CEO", "CFO", "COB", "CHAIR", "PRESIDENT", "DIRECTOR")


def detect_clusters(
    transactions: list[InsiderTransaction],
    window_days: int = 30,
    min_value: float = 100_000,
    min_insiders: int = 3,
) -> dict[str, list[InsiderTransaction]]:
    eligible = [tx for tx in transactions if tx.trade_type == "P" and tx.value >= min_value]
    clusters: dict[str, list[InsiderTransaction]] = {}
    for ticker in sorted({tx.ticker for tx in eligible}):
        group = sorted((tx for tx in eligible if tx.ticker == ticker), key=lambda tx: tx.transaction_date)
        best: list[InsiderTransaction] = []
        for start in group:
            end_date = start.transaction_date + timedelta(days=window_days)
            candidate = [tx for tx in group if start.transaction_date <= tx.transaction_date <= end_date]
            if len({tx.insider_name for tx in candidate}) < min_insiders:
                continue
            if not _has_senior_title([tx.insider_title for tx in candidate]):
                continue
            if sum(tx.value for tx in candidate) > sum(tx.value for tx in best):
                best = candidate
        if best:
            clusters[ticker] = best
    return clusters


def _has_senior_title(titles: list[str]) -> bool:
    combined = " ".join(titles).upper()
    return any(keyword in combined for keyword in SENIOR_TITLE_KEYWORDS)

