"""Sample orders used for seeding the demo/dashboard."""
from backend.models.schemas import OrderItem, OrderRequest

SAMPLE_ORDERS: list[OrderRequest] = [
    # Clearly fine: single item, basics, low-risk pincode, loyal customer.
    OrderRequest(
        order_id="ORD-1001",
        customer_id="cust_001",
        pincode="560001",
        items=[
            OrderItem(sku="TS-BLK-M", product_name="Black Crew Tee", category="fashion_basics",
                      size="M", fabric="cotton", price=499),
        ],
        order_value=499,
    ),
    # Multi-size ordering: classic "try 3 keep 1" fashion pattern.
    OrderRequest(
        order_id="ORD-1002",
        customer_id="cust_003",
        pincode="110001",
        items=[
            OrderItem(sku="DRS-RED-S", product_name="Red Wrap Dress", category="fashion_going_out",
                      size="S", fabric="silk", price=1899),
            OrderItem(sku="DRS-RED-M", product_name="Red Wrap Dress", category="fashion_going_out",
                      size="M", fabric="silk", price=1899),
            OrderItem(sku="DRS-RED-L", product_name="Red Wrap Dress", category="fashion_going_out",
                      size="L", fabric="silk", price=1899),
        ],
        order_value=5697,
    ),
    # Campaign spike + serial-returner customer: ambiguous, should hit the LLM analyzer.
    OrderRequest(
        order_id="ORD-1003",
        customer_id="cust_002",
        pincode="700001",
        items=[
            OrderItem(sku="JKT-BLU-L", product_name="Denim Jacket", category="fashion_topwear",
                      size="L", fabric="denim", price=2299),
        ],
        campaign_ref="insta_reel_launch_42",
        order_value=2299,
    ),
    # Hard blacklist pincode: should short-circuit at the rule engine.
    OrderRequest(
        order_id="ORD-1004",
        customer_id="cust_001",
        pincode="800001",
        items=[
            OrderItem(sku="SHO-WHT-9", product_name="White Sneakers", category="fashion_footwear",
                      size="9", fabric="polyester", price=1599),
        ],
        order_value=1599,
    ),
    # Non-fashion, low-risk category: planner should skip fashion-specific fetchers.
    OrderRequest(
        order_id="ORD-1005",
        customer_id="cust_003",
        pincode="400001",
        items=[
            OrderItem(sku="EAR-BLK-01", product_name="Wireless Earbuds", category="electronics",
                      price=1999),
        ],
        order_value=1999,
    ),
]
