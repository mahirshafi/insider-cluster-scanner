from datetime import date, timedelta

from backend.app.models import InsiderTransaction
from backend.app.services.cluster import detect_clusters


def tx(name: str, day_offset: int, value: float, title: str = "Director") -> InsiderTransaction:
    day = date(2026, 5, 1) + timedelta(days=day_offset)
    return InsiderTransaction(
        ticker="TEST",
        company_name="Test Corp",
        insider_name=name,
        insider_title=title,
        transaction_date=day,
        filing_date=day,
        trade_type="P",
        shares=value / 10,
        price=10,
        value=value,
    )


def test_detects_three_distinct_insider_cluster_within_window():
    clusters = detect_clusters([
        tx("Alice", 0, 150_000, "CEO"),
        tx("Bob", 1, 200_000, "Director"),
        tx("Carol", 2, 175_000, "CFO"),
    ])

    assert "TEST" in clusters
    assert {item.insider_name for item in clusters["TEST"]} == {"Alice", "Bob", "Carol"}


def test_rejects_same_person_and_small_purchase():
    clusters = detect_clusters([
        tx("Alice", 0, 150_000, "CEO"),
        tx("Alice", 1, 200_000, "CEO"),
        tx("Carol", 2, 99_999, "Director"),
        tx("Dave", 40, 250_000, "Director"),
    ])

    assert clusters == {}
