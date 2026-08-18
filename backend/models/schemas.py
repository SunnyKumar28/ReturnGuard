from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

ActionType = Literal["allow", "whatsapp_confirm", "prepaid_incentive", "manual_review"]


class OrderItem(BaseModel):
    sku: str
    product_name: str
    category: str  # e.g. "fashion_topwear", "fashion_footwear", "electronics"
    size: str | None = None
    fabric: str | None = None
    price: float


class OrderRequest(BaseModel):
    order_id: str
    customer_id: str
    pincode: str
    payment_method: Literal["cod", "prepaid"] = "cod"
    items: list[OrderItem]
    campaign_ref: str | None = Field(
        default=None, description="Ad/influencer campaign id this order was attributed to, if any"
    )
    order_value: float


class FetcherResult(BaseModel):
    name: str
    data: dict
    notes: str = ""


class RuleVerdict(BaseModel):
    matched_rules: list[str]
    risk_score: int  # 0-100
    confident_action: ActionType | None = None
    reason: str


class AnalyzerVerdict(BaseModel):
    proposed_action: ActionType
    proposed_discount_pct: float = 0.0
    rationale: str
    used_llm: bool


class GuardrailResult(BaseModel):
    final_action: ActionType
    final_discount_pct: float
    clamped: bool
    notes: str


class DecisionTrace(BaseModel):
    order_id: str
    planner_selected_fetchers: list[str]
    fetcher_results: list[FetcherResult]
    rule_verdict: RuleVerdict
    analyzer_verdict: AnalyzerVerdict | None
    guardrail_result: GuardrailResult
    llm_invoked: bool


class EvaluateResponse(BaseModel):
    order_id: str
    final_action: ActionType
    final_discount_pct: float
    risk_score: int
    llm_invoked: bool
    trace: DecisionTrace
