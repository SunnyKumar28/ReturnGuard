const API_BASE = "/api";

const statusEl = document.getElementById("status");
const statTotal = document.getElementById("statTotal");
const statLlmRate = document.getElementById("statLlmRate");
const actionBreakdown = document.getElementById("actionBreakdown");
const tracesList = document.getElementById("tracesList");

function setStatus(msg) {
  statusEl.textContent = msg;
  if (msg) setTimeout(() => (statusEl.textContent = ""), 3000);
}

async function seedDemo() {
  setStatus("Running pipeline over sample orders...");
  const res = await fetch(`${API_BASE}/orders/seed-demo`, { method: "POST" });
  if (!res.ok) {
    setStatus("Failed to seed demo orders.");
    return;
  }
  setStatus("Seeded 5 demo orders.");
  await refreshAll();
}

async function refreshStats() {
  const res = await fetch(`${API_BASE}/dashboard/stats`);
  const data = await res.json();
  statTotal.textContent = data.total_orders_evaluated;
  statLlmRate.textContent = `${Math.round(data.llm_invocation_rate * 100)}%`;
  actionBreakdown.innerHTML = "";
  Object.entries(data.action_breakdown || {}).forEach(([action, count]) => {
    const span = document.createElement("span");
    span.className = `badge ${action}`;
    span.style.marginRight = "6px";
    span.textContent = `${action}: ${count}`;
    actionBreakdown.appendChild(span);
  });
}

async function refreshTraces() {
  const res = await fetch(`${API_BASE}/dashboard/recent-traces?limit=20`);
  const traces = await res.json();
  tracesList.innerHTML = "";
  if (!traces.length) {
    tracesList.innerHTML = '<p style="color:#8b90a0">No orders evaluated yet — click "Seed demo orders".</p>';
    return;
  }
  traces.forEach((t) => tracesList.appendChild(renderTraceCard(t)));
}

function renderTraceCard(trace) {
  const card = document.createElement("div");
  card.className = "trace-card";

  const action = trace.guardrail_result.final_action;
  const discount = trace.guardrail_result.final_discount_pct;
  const score = trace.rule_verdict.risk_score;

  card.innerHTML = `
    <div class="trace-head">
      <span class="trace-order-id">${trace.order_id}</span>
      <span class="badge ${action}">${action}</span>
    </div>
    <div class="trace-meta">
      risk score: <strong>${score}</strong>
      &nbsp;|&nbsp; discount: <strong>${discount}%</strong>
      &nbsp;|&nbsp; LLM invoked: <strong>${trace.llm_invoked ? "yes" : "no"}</strong>
      &nbsp;|&nbsp; fetchers: ${trace.planner_selected_fetchers.join(", ")}
    </div>
    <details>
      <summary>Full agent trace</summary>
      <pre>${JSON.stringify(trace, null, 2)}</pre>
    </details>
  `;
  return card;
}

async function refreshAll() {
  await Promise.all([refreshStats(), refreshTraces()]);
}

document.getElementById("seedBtn").addEventListener("click", seedDemo);
document.getElementById("refreshBtn").addEventListener("click", () => {
  setStatus("Refreshing...");
  refreshAll();
});

refreshAll();
