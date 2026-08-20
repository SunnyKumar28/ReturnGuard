from backend.agents.guardrails import apply_guardrails
from backend.config import settings


def test_discount_clamped_to_ceiling():
    result = apply_guardrails("prepaid_incentive", 40.0)
    assert result.final_discount_pct == settings.max_discount_pct
    assert result.clamped is True


def test_within_policy_not_clamped():
    result = apply_guardrails("allow", 0.0)
    assert result.clamped is False
    assert result.final_action == "allow"
    assert result.final_discount_pct == 0.0


def test_unknown_action_downgraded_to_manual_review():
    result = apply_guardrails("auto_cancel_order", 0.0)  # not in allow-list
    assert result.final_action == "manual_review"
    assert result.clamped is True


def test_negative_discount_clamped_to_zero():
    result = apply_guardrails("prepaid_incentive", -5.0)
    assert result.final_discount_pct == 0.0
    assert result.clamped is True


def test_discount_only_applies_to_prepaid_incentive_action():
    result = apply_guardrails("whatsapp_confirm", 20.0)
    assert result.final_discount_pct == 0.0
