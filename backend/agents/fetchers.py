"""
Fetcher agents. Each fetcher has the same interface — (order) -> FetcherResult — so a
mock provider can be swapped for a real integration (shipping API, OMS, campaign
platform) without touching the planner or pipeline.
"""
from collections import Counter

from backend.data.mock_providers import (
    ACTIVE_CAMPAIGNS,
    CATEGORY_RETURN_PRIOR,
    CUSTOMER_RETURN_HISTORY,
    DEFAULT_CATEGORY_PRIOR,
    DEFAULT_CUSTOMER_HISTORY,
    DEFAULT_PINCODE_RTO,
    FABRIC_RETURN_MODIFIER,
    PINCODE_RTO_HISTORY,
)
from backend.models.schemas import FetcherResult, OrderRequest


def fetch_order_history(order: OrderRequest) -> FetcherResult:
    history = CUSTOMER_RETURN_HISTORY.get(order.customer_id, DEFAULT_CUSTOMER_HISTORY)
    total = history["total_orders"]
    returned = history["returned_orders"]
    return_rate = returned / total if total else None
    return FetcherResult(
        name="order_history",
        data={"total_orders": total, "returned_orders": returned, "return_rate": return_rate},
        notes="New customer, no history" if total == 0 else "",
    )


def fetch_size_order_pattern(order: OrderRequest) -> FetcherResult:
    sku_bases = Counter(item.sku.rsplit("-", 1)[0] for item in order.items)
    multi_size_skus = {base: count for base, count in sku_bases.items() if count >= 2}
    return FetcherResult(
        name="size_order_pattern",
        data={
            "distinct_sizes_ordered": len(order.items),
            "multi_size_skus": multi_size_skus,
            "is_multi_size_order": bool(multi_size_skus),
        },
    )


def fetch_campaign_spike(order: OrderRequest) -> FetcherResult:
    if not order.campaign_ref:
        return FetcherResult(name="campaign_spike", data={"campaign_ref": None, "is_spiking": False})
    campaign = ACTIVE_CAMPAIGNS.get(order.campaign_ref, {"is_spiking": False, "orders_last_hour": 0,
                                                          "avg_orders_last_hour": 0})
    return FetcherResult(
        name="campaign_spike",
        data={"campaign_ref": order.campaign_ref, **campaign},
        notes="Order attributed to an actively spiking campaign" if campaign.get("is_spiking") else "",
    )


def fetch_pincode_risk(order: OrderRequest) -> FetcherResult:
    rto_rate = PINCODE_RTO_HISTORY.get(order.pincode, DEFAULT_PINCODE_RTO)
    return FetcherResult(
        name="pincode_risk",
        data={"pincode": order.pincode, "historical_rto_rate": rto_rate, "is_blacklisted": rto_rate >= 0.5},
    )


def fetch_category_return_prior(order: OrderRequest) -> FetcherResult:
    per_item = []
    for item in order.items:
        base_prior = CATEGORY_RETURN_PRIOR.get(item.category, DEFAULT_CATEGORY_PRIOR)
        fabric_mod = FABRIC_RETURN_MODIFIER.get(item.fabric or "", 0.0)
        per_item.append({
            "sku": item.sku,
            "category": item.category,
            "fabric": item.fabric,
            "prior_return_rate": round(base_prior + fabric_mod, 3),
        })
    avg_prior = sum(x["prior_return_rate"] for x in per_item) / len(per_item) if per_item else 0.0
    return FetcherResult(
        name="category_return_prior",
        data={"per_item": per_item, "avg_prior_return_rate": round(avg_prior, 3)},
    )


FETCHER_REGISTRY = {
    "order_history": fetch_order_history,
    "size_order_pattern": fetch_size_order_pattern,
    "campaign_spike": fetch_campaign_spike,
    "pincode_risk": fetch_pincode_risk,
    "category_return_prior": fetch_category_return_prior,
}


def run_fetchers(order: OrderRequest, fetcher_names: list[str]) -> list[FetcherResult]:
    return [FETCHER_REGISTRY[name](order) for name in fetcher_names if name in FETCHER_REGISTRY]
