"""
Planner agent: decides which fetchers are relevant for a given order, so we don't
pay the cost of fetching fashion-specific signals (size pattern, campaign spike,
category prior) for a non-fashion order.
"""
from backend.models.schemas import OrderRequest

FASHION_CATEGORY_PREFIX = "fashion_"

ALL_FETCHERS = [
    "order_history",
    "size_order_pattern",
    "campaign_spike",
    "pincode_risk",
    "category_return_prior",
]


def plan_fetchers(order: OrderRequest) -> list[str]:
    is_fashion = any(item.category.startswith(FASHION_CATEGORY_PREFIX) for item in order.items)

    selected = ["order_history", "pincode_risk"]  # always relevant, category-agnostic

    if is_fashion:
        selected.append("size_order_pattern")
        selected.append("category_return_prior")
        if order.campaign_ref:
            selected.append("campaign_spike")

    return selected
