import pytest

from backend.agents.pipeline import evaluate_order
from backend.config import settings
from backend.data.mock_orders import SAMPLE_ORDERS
from backend.storage.audit_log import get_record


@pytest.fixture(autouse=True)
def isolated_audit_log(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "audit_log_path", str(tmp_path / "audit_log.jsonl"))


def test_sample_orders_run_end_to_end_without_llm_key(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    for order in SAMPLE_ORDERS:
        response = evaluate_order(order)
        assert response.final_action in {"allow", "whatsapp_confirm", "prepaid_incentive", "manual_review"}
        assert 0 <= response.final_discount_pct <= settings.max_discount_pct


def test_blacklisted_pincode_order_never_invokes_llm(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    blacklisted_order = next(o for o in SAMPLE_ORDERS if o.order_id == "ORD-1004")
    response = evaluate_order(blacklisted_order)
    assert response.final_action == "manual_review"
    assert response.llm_invoked is False


def test_trace_is_persisted_and_retrievable(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    order = SAMPLE_ORDERS[0]
    evaluate_order(order)
    record = get_record(order.order_id)
    assert record is not None
    assert record.order_id == order.order_id
    assert record.guardrail_result is not None
