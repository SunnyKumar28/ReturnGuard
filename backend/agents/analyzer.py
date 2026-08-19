"""
LLM analyzer agent. Invoked ONLY for orders the rule engine left in the ambiguous
band. Reasons over all fetched signals and proposes exactly one action from the
allow-listed set. Never allowed to act directly — the guardrail layer has final say.

If no ANTHROPIC_API_KEY is configured, falls back to a deterministic heuristic so the
whole pipeline still runs end-to-end for an offline demo.
"""
import json

from backend.config import settings
from backend.models.schemas import AnalyzerVerdict, FetcherResult, OrderRequest, RuleVerdict

ALLOWED_ACTIONS = ["allow", "whatsapp_confirm", "prepaid_incentive", "manual_review"]

SYSTEM_PROMPT = f"""You are a risk-intervention analyst for a fashion e-commerce COD order.
You are only ever called for orders in an ambiguous risk band — the easy cases have
already been resolved by deterministic rules before you were invoked.

You must choose exactly one action from this fixed set: {ALLOWED_ACTIONS}.
- "allow": let the order proceed untouched.
- "whatsapp_confirm": send a delivery confirmation message before shipping (low friction).
- "prepaid_incentive": offer a discount to convert the order from COD to prepaid.
- "manual_review": escalate to a human analyst.

If you propose "prepaid_incentive", also propose a discount_pct (a number, not a string).
You do not have authority to apply any action yourself — a downstream guardrail will
validate and clamp whatever you propose. Respond with ONLY a JSON object of the form:
{{"action": "...", "discount_pct": 0, "rationale": "..."}}
"""


def _build_user_prompt(order: OrderRequest, rule_verdict: RuleVerdict, fetcher_results: list[FetcherResult]) -> str:
    context = {
        "order_id": order.order_id,
        "order_value": order.order_value,
        "items": [item.model_dump() for item in order.items],
        "rule_engine_risk_score": rule_verdict.risk_score,
        "rule_engine_matched_rules": rule_verdict.matched_rules,
        "fetched_signals": {r.name: r.data for r in fetcher_results},
    }
    return f"Order context:\n{json.dumps(context, indent=2)}\n\nChoose one action and respond with JSON only."


def _heuristic_fallback(rule_verdict: RuleVerdict, fetcher_results: list[FetcherResult]) -> AnalyzerVerdict:
    """Deterministic stand-in used when no LLM key is configured."""
    by_name = {r.name: r.data for r in fetcher_results}
    campaign = by_name.get("campaign_spike", {})
    size_pattern = by_name.get("size_order_pattern", {})

    if campaign.get("is_spiking"):
        return AnalyzerVerdict(
            proposed_action="whatsapp_confirm",
            proposed_discount_pct=0.0,
            rationale="Order is attributed to a currently spiking campaign; a lightweight "
                        "delivery confirmation filters out impulse orders without adding friction "
                        "for genuine buyers.",
            used_llm=False,
        )
    if size_pattern.get("is_multi_size_order"):
        return AnalyzerVerdict(
            proposed_action="prepaid_incentive",
            proposed_discount_pct=10.0,
            rationale="Multi-size order for the same SKU strongly suggests a keep-one-return-rest "
                        "pattern; a modest prepaid discount converts likely-COD-refusal risk into a "
                        "committed sale.",
            used_llm=False,
        )
    if rule_verdict.risk_score >= (settings.ambiguous_band_low + settings.ambiguous_band_high) // 2:
        return AnalyzerVerdict(
            proposed_action="whatsapp_confirm",
            proposed_discount_pct=0.0,
            rationale="Risk score sits in the upper half of the ambiguous band; a delivery "
                        "confirmation is a low-friction way to reduce RTO likelihood before escalating.",
            used_llm=False,
        )
    return AnalyzerVerdict(
        proposed_action="allow",
        proposed_discount_pct=0.0,
        rationale="No fashion-specific or campaign risk signal fired strongly enough to warrant "
                    "intervention; allow the order to proceed.",
        used_llm=False,
    )


def analyze(order: OrderRequest, rule_verdict: RuleVerdict, fetcher_results: list[FetcherResult]) -> AnalyzerVerdict:
    if not settings.anthropic_api_key:
        return _heuristic_fallback(rule_verdict, fetcher_results)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(order, rule_verdict, fetcher_results)}],
        )
        raw_text = response.content[0].text
        parsed = json.loads(raw_text)
        action = parsed.get("action")
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"LLM proposed an action outside the allow-list: {action}")
        return AnalyzerVerdict(
            proposed_action=action,
            proposed_discount_pct=float(parsed.get("discount_pct", 0) or 0),
            rationale=parsed.get("rationale", ""),
            used_llm=True,
        )
    except Exception as exc:  # noqa: BLE001 - any LLM/parse failure falls back safely
        fallback = _heuristic_fallback(rule_verdict, fetcher_results)
        fallback.rationale = f"[LLM call failed, used heuristic fallback: {exc}] {fallback.rationale}"
        return fallback
