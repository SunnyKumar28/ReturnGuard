"""
Deterministic rule engine. Runs before any LLM call. Cheap, auditable, and can
short-circuit straight to a confident action for the clear-cut majority of orders.
Only orders that land in the ambiguous risk-score band are handed to the LLM analyzer.
"""
from backend.config import settings
from backend.models.schemas import FetcherResult, RuleVerdict

BLACKLIST_PINCODE_SCORE = 95
MULTI_SIZE_BASE_SCORE = 55
SERIAL_RETURNER_THRESHOLD = 0.5
SERIAL_RETURNER_SCORE = 60


def _by_name(results: list[FetcherResult]) -> dict[str, dict]:
    return {r.name: r.data for r in results}


def evaluate_rules(fetcher_results: list[FetcherResult]) -> RuleVerdict:
    data = _by_name(fetcher_results)
    matched: list[str] = []
    score = 10  # baseline low risk

    pincode = data.get("pincode_risk", {})
    if pincode.get("is_blacklisted"):
        matched.append("pincode_blacklisted")
        return RuleVerdict(
            matched_rules=matched,
            risk_score=BLACKLIST_PINCODE_SCORE,
            confident_action="manual_review",
            reason=f"Pincode {pincode.get('pincode')} has a historical RTO rate of "
                    f"{pincode.get('historical_rto_rate')}, above the hard blacklist threshold.",
        )
    score = max(score, int(pincode.get("historical_rto_rate", 0.2) * 100))

    size_pattern = data.get("size_order_pattern", {})
    if size_pattern.get("is_multi_size_order"):
        matched.append("multi_size_order")
        score = max(score, MULTI_SIZE_BASE_SCORE)

    history = data.get("order_history", {})
    return_rate = history.get("return_rate")
    if return_rate is not None and return_rate >= SERIAL_RETURNER_THRESHOLD:
        matched.append("serial_returner")
        score = max(score, SERIAL_RETURNER_SCORE)

    campaign = data.get("campaign_spike", {})
    if campaign.get("is_spiking"):
        matched.append("campaign_spike_active")
        score = max(score, 45)

    category = data.get("category_return_prior", {})
    avg_prior = category.get("avg_prior_return_rate")
    if avg_prior is not None:
        score = max(score, int(avg_prior * 100))

    score = min(score, 100)

    if score < settings.ambiguous_band_low:
        matched.append("low_risk_pass_through")
        return RuleVerdict(
            matched_rules=matched,
            risk_score=score,
            confident_action="allow",
            reason=f"Risk score {score} is below the ambiguous band "
                    f"({settings.ambiguous_band_low}); rules alone are confident this order is low-risk.",
        )

    if score > settings.ambiguous_band_high:
        matched.append("high_risk_no_single_hard_rule")
        return RuleVerdict(
            matched_rules=matched,
            risk_score=score,
            confident_action="manual_review",
            reason=f"Risk score {score} is above the ambiguous band "
                    f"({settings.ambiguous_band_high}), routed straight to manual review.",
        )

    # Ambiguous band: no confident_action -> pipeline will invoke the LLM analyzer.
    return RuleVerdict(
        matched_rules=matched,
        risk_score=score,
        confident_action=None,
        reason=f"Risk score {score} falls inside the ambiguous band "
                f"[{settings.ambiguous_band_low}, {settings.ambiguous_band_high}]; deferring to LLM analyzer.",
    )
