"""Run the pipeline over the bundled sample orders directly (no server needed) and
print each decision — useful for a quick terminal demo or for the video walkthrough."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents.pipeline import evaluate_order
from backend.data.mock_orders import SAMPLE_ORDERS


def main() -> None:
    for order in SAMPLE_ORDERS:
        response = evaluate_order(order)
        print(f"\n=== {order.order_id} ===")
        print(f"risk_score={response.risk_score}  final_action={response.final_action}  "
              f"discount={response.final_discount_pct}%  llm_invoked={response.llm_invoked}")
        print(json.dumps(response.trace.rule_verdict.model_dump(), indent=2))


if __name__ == "__main__":
    main()
