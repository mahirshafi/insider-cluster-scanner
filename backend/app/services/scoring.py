from __future__ import annotations

import statistics

from backend.app.models import PeerMultiple, ValuationSnapshot


def divergence_score(snapshot: ValuationSnapshot, total_cluster_value: float) -> tuple[int, str, list[str], dict[str, float | None]]:
    score = 0
    rationale: list[str] = []
    averages = peer_averages(snapshot.peers)

    if snapshot.current_price and snapshot.avg_target:
        upside = (snapshot.avg_target - snapshot.current_price) / snapshot.current_price
        if upside >= 0.20:
            score += 40
            rationale.append(f"Average analyst target implies {upside:.0%} upside")
        else:
            rationale.append(f"Average analyst target implies {upside:.0%} upside")
    else:
        rationale.append("Average analyst target unavailable")

    if snapshot.current_price and snapshot.low_target and snapshot.current_price < snapshot.low_target:
        score += 20
        rationale.append("Current price is below the lowest analyst target")

    peer_pe = averages["pe_forward"]
    if snapshot.pe_forward and peer_pe and snapshot.pe_forward < peer_pe:
        score += 20
        rationale.append(f"Forward P/E {snapshot.pe_forward:.1f} is below peer average {peer_pe:.1f}")
    elif snapshot.pe_forward and peer_pe:
        rationale.append(f"Forward P/E {snapshot.pe_forward:.1f} is not below peer average {peer_pe:.1f}")
    else:
        rationale.append("Forward P/E comparison unavailable")

    peer_pb = averages["pb"]
    if snapshot.pb and peer_pb and snapshot.pb < peer_pb:
        score += 10
        rationale.append(f"P/B {snapshot.pb:.1f} is below peer average {peer_pb:.1f}")
    elif snapshot.pb and peer_pb:
        rationale.append(f"P/B {snapshot.pb:.1f} is not below peer average {peer_pb:.1f}")
    else:
        rationale.append("P/B comparison unavailable")

    if total_cluster_value > 5_000_000:
        score += 10
        rationale.append("Insider cluster value exceeds $5M")

    return score, _signal(score), rationale, averages


def peer_averages(peers: list[PeerMultiple]) -> dict[str, float | None]:
    return {
        "pe_forward": _mean([peer.pe_forward for peer in peers]),
        "pb": _mean([peer.pb for peer in peers]),
        "ps": _mean([peer.ps for peer in peers]),
    }


def _mean(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None and value > 0]
    if not filtered:
        return None
    return statistics.fmean(filtered)


def _signal(score: int) -> str:
    if score >= 70:
        return "Strong Buy"
    if score >= 50:
        return "Watch"
    return "Avoid"
