from backend.agents.analyzer import analyze
from backend.agents.fetchers import run_fetchers
from backend.agents.guardrails import apply_guardrails
from backend.agents.planner import plan_fetchers
from backend.agents.rule_engine import evaluate_rules
from backend.models.schemas import AnalyzerVerdict, DecisionTrace, EvaluateResponse, OrderRequest
from backend.storage.audit_log import append_audit_record


def evaluate_order(order: OrderRequest) -> EvaluateResponse:
    selected_fetchers = plan_fetchers(order)
    fetcher_results = run_fetchers(order, selected_fetchers)

    rule_verdict = evaluate_rules(fetcher_results)

    analyzer_verdict: AnalyzerVerdict | None = None
    llm_invoked = False

    if rule_verdict.confident_action is not None:
        proposed_action = rule_verdict.confident_action
        proposed_discount = 0.0
    else:
        analyzer_verdict = analyze(order, rule_verdict, fetcher_results)
        proposed_action = analyzer_verdict.proposed_action
        proposed_discount = analyzer_verdict.proposed_discount_pct
        llm_invoked = analyzer_verdict.used_llm

    guardrail_result = apply_guardrails(proposed_action, proposed_discount)

    trace = DecisionTrace(
        order_id=order.order_id,
        planner_selected_fetchers=selected_fetchers,
        fetcher_results=fetcher_results,
        rule_verdict=rule_verdict,
        analyzer_verdict=analyzer_verdict,
        guardrail_result=guardrail_result,
        llm_invoked=llm_invoked,
    )

    append_audit_record(trace)

    return EvaluateResponse(
        order_id=order.order_id,
        final_action=guardrail_result.final_action,
        final_discount_pct=guardrail_result.final_discount_pct,
        risk_score=rule_verdict.risk_score,
        llm_invoked=llm_invoked,
        trace=trace,
    )
