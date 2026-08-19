from fastapi import APIRouter, HTTPException

from backend.agents.pipeline import evaluate_order
from backend.data.mock_orders import SAMPLE_ORDERS
from backend.models.schemas import DecisionTrace, EvaluateResponse, OrderRequest
from backend.storage.audit_log import get_record, read_all_records

router = APIRouter()


@router.post("/orders/evaluate", response_model=EvaluateResponse)
def evaluate(order: OrderRequest) -> EvaluateResponse:
    return evaluate_order(order)


@router.post("/orders/seed-demo", response_model=list[EvaluateResponse])
def seed_demo() -> list[EvaluateResponse]:
    """Runs the pipeline over the bundled sample orders — useful for a quick demo."""
    return [evaluate_order(order) for order in SAMPLE_ORDERS]


@router.get("/orders/{order_id}/trace", response_model=DecisionTrace)
def get_trace(order_id: str) -> DecisionTrace:
    record = get_record(order_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No decision trace found for order_id={order_id}")
    return record


@router.get("/dashboard/stats")
def dashboard_stats() -> dict:
    records = read_all_records()
    total = len(records)
    action_counts: dict[str, int] = {}
    llm_invocations = 0
    for r in records:
        action_counts[r.guardrail_result.final_action] = action_counts.get(r.guardrail_result.final_action, 0) + 1
        if r.llm_invoked:
            llm_invocations += 1
    return {
        "total_orders_evaluated": total,
        "action_breakdown": action_counts,
        "llm_invocation_rate": round(llm_invocations / total, 3) if total else 0.0,
        "recent_orders": [r.order_id for r in records[-10:]],
    }


@router.get("/dashboard/recent-traces", response_model=list[DecisionTrace])
def recent_traces(limit: int = 20) -> list[DecisionTrace]:
    records = read_all_records()
    return records[-limit:][::-1]
