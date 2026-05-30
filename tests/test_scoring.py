from backend.app.models import PeerMultiple, ValuationSnapshot
from backend.app.services.scoring import divergence_score


def test_strong_buy_score_formula():
    snapshot = ValuationSnapshot(
        current_price=80,
        avg_target=120,
        low_target=90,
        pe_forward=10,
        pb=1.2,
        peers=[
            PeerMultiple(ticker="AAA", pe_forward=15, pb=2.0),
            PeerMultiple(ticker="BBB", pe_forward=13, pb=1.8),
        ],
    )

    score, signal, rationale, averages = divergence_score(snapshot, 6_000_000)

    assert score == 100
    assert signal == "Strong Buy"
    assert averages["pe_forward"] == 14
    assert any("upside" in reason for reason in rationale)


def test_avoid_when_data_does_not_support_divergence():
    snapshot = ValuationSnapshot(
        current_price=100,
        avg_target=105,
        low_target=80,
        pe_forward=20,
        pb=3,
        peers=[PeerMultiple(ticker="AAA", pe_forward=15, pb=2)],
    )

    score, signal, _, _ = divergence_score(snapshot, 1_000_000)

    assert score == 0
    assert signal == "Avoid"
