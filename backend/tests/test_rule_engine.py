from backend.agents.rule_engine import evaluate_rules
from backend.models.schemas import FetcherResult


def _fr(name: str, data: dict) -> FetcherResult:
    return FetcherResult(name=name, data=data)


def test_blacklisted_pincode_short_circuits_to_manual_review():
    results = [
        _fr("pincode_risk", {"pincode": "800001", "historical_rto_rate": 0.61, "is_blacklisted": True}),
        _fr("order_history", {"total_orders": 5, "returned_orders": 1, "return_rate": 0.2}),
    ]
    verdict = evaluate_rules(results)
    assert verdict.confident_action == "manual_review"
    assert "pincode_blacklisted" in verdict.matched_rules
    assert verdict.risk_score == 95


def test_multi_size_order_pushes_into_ambiguous_or_review_band():
    results = [
        _fr("pincode_risk", {"pincode": "560001", "historical_rto_rate": 0.12, "is_blacklisted": False}),
        _fr("size_order_pattern", {"distinct_sizes_ordered": 3, "multi_size_skus": {"DRS-RED": 3},
                                     "is_multi_size_order": True}),
        _fr("order_history", {"total_orders": 1, "returned_orders": 0, "return_rate": 0.0}),
    ]
    verdict = evaluate_rules(results)
    assert "multi_size_order" in verdict.matched_rules
    assert verdict.risk_score >= 40


def test_low_risk_order_allows_without_llm():
    results = [
        _fr("pincode_risk", {"pincode": "560001", "historical_rto_rate": 0.12, "is_blacklisted": False}),
        _fr("order_history", {"total_orders": 20, "returned_orders": 2, "return_rate": 0.1}),
    ]
    verdict = evaluate_rules(results)
    assert verdict.confident_action == "allow"
    assert verdict.risk_score < 40


def test_serial_returner_flagged():
    results = [
        _fr("pincode_risk", {"pincode": "560001", "historical_rto_rate": 0.12, "is_blacklisted": False}),
        _fr("order_history", {"total_orders": 5, "returned_orders": 4, "return_rate": 0.8}),
    ]
    verdict = evaluate_rules(results)
    assert "serial_returner" in verdict.matched_rules
    assert verdict.risk_score >= 60
