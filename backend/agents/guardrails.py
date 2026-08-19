"""
Guardrail layer — the ONLY place a final action is decided. Neither the rule engine
nor the LLM analyzer can act directly; this layer validates the action is in the
allow-listed set and clamps any proposed discount to a hard ceiling.
"""
from backend.config import settings
from backend.models.schemas import ActionType, GuardrailResult

ALLOWED_ACTIONS: set[ActionType] = {"allow", "whatsapp_confirm", "prepaid_incentive", "manual_review"}


def apply_guardrails(proposed_action: ActionType, proposed_discount_pct: float) -> GuardrailResult:
    clamped = False
    notes_parts: list[str] = []

    action = proposed_action
    if action not in ALLOWED_ACTIONS:
        notes_parts.append(f"Proposed action '{proposed_action}' not in allow-list; downgraded to manual_review.")
        action = "manual_review"
        clamped = True

    discount = proposed_discount_pct if action == "prepaid_incentive" else 0.0
    if discount > settings.max_discount_pct:
        notes_parts.append(
            f"Proposed discount {discount}% exceeded ceiling of {settings.max_discount_pct}%; clamped."
        )
        discount = settings.max_discount_pct
        clamped = True
    if discount < 0:
        discount = 0.0
        clamped = True

    if not notes_parts:
        notes_parts.append("Action and discount within policy; no clamping needed.")

    return GuardrailResult(
        final_action=action,
        final_discount_pct=discount,
        clamped=clamped,
        notes=" ".join(notes_parts),
    )
