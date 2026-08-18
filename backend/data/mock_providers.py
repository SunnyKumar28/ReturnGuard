"""
Mock backing data for the fetcher agents. In production these would be replaced by
real integrations (order management system, shipping provider, ads/campaign
platform, customer data platform) — the fetcher interface in agents/fetchers.py
does not change when that swap happens.
"""

# Historical RTO rate per pincode (0-1). Anything >= 0.5 is a hard blacklist signal.
PINCODE_RTO_HISTORY = {
    "560001": 0.12,
    "110001": 0.18,
    "400001": 0.15,
    "700001": 0.22,
    "382001": 0.55,  # blacklisted
    "800001": 0.61,  # blacklisted
}
DEFAULT_PINCODE_RTO = 0.20

# Category-level baseline return-rate priors, independent of any single order.
CATEGORY_RETURN_PRIOR = {
    "fashion_topwear": 0.32,
    "fashion_bottomwear": 0.35,
    "fashion_footwear": 0.28,
    "fashion_going_out": 0.45,
    "fashion_basics": 0.15,
    "electronics": 0.08,
    "grocery": 0.02,
}
DEFAULT_CATEGORY_PRIOR = 0.20

# Fabric-level modifier on top of category prior.
FABRIC_RETURN_MODIFIER = {
    "silk": 0.10,
    "linen": 0.06,
    "cotton": 0.0,
    "polyester": -0.02,
    "denim": -0.03,
}

# Per-customer historical return behaviour (returns / total orders).
CUSTOMER_RETURN_HISTORY = {
    "cust_001": {"total_orders": 20, "returned_orders": 2},
    "cust_002": {"total_orders": 5, "returned_orders": 4},  # serial returner
    "cust_003": {"total_orders": 1, "returned_orders": 0},  # new customer
}
DEFAULT_CUSTOMER_HISTORY = {"total_orders": 0, "returned_orders": 0}

# Active campaigns and whether they are currently causing an order spike.
ACTIVE_CAMPAIGNS = {
    "insta_reel_launch_42": {"is_spiking": True, "orders_last_hour": 512, "avg_orders_last_hour": 20},
    "email_newsletter_08": {"is_spiking": False, "orders_last_hour": 15, "avg_orders_last_hour": 12},
}
