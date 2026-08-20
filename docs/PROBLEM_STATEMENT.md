# Problem Statement — ReturnGuard AI

## The problem

Cash-on-delivery (COD) e-commerce in India suffers **Return-to-Origin (RTO) rates of
25–40%**: orders that are shipped but refused at the door, undeliverable, or simply
never intended to be kept. Every RTO order costs the merchant forward shipping,
reverse shipping, repackaging, and lost inventory turnover — even though the merchant
was never paid.

Payment/commerce platforms (e.g. Razorpay) already ship a **generic** RTO risk model:
pincode risk history, customer return history, order value vs. customer lifetime
value. It is deliberately category-agnostic, because it has to work for every
merchant on the platform — electronics, grocery, fashion, everything.

That genericness is exactly the gap. **Fashion/apparel D2C sellers** have return
drivers a generic model cannot see:

- **Multi-size ordering** — a customer orders S, M, and L of the same shirt, intending
  to keep one and return two. This is normal shopping behaviour, not fraud, but it
  guarantees a high per-order return rate that a generic model would misclassify.
- **Influencer/campaign spikes** — a single Instagram/YouTube post can drive 500+
  orders in an hour, a meaningful fraction of which are impulse buys that cancel or
  refuse delivery. A generic model has no notion of "an order campaign just fired."
- **Category/fabric return priors** — going-out wear and fit-sensitive categories
  return at structurally higher rates than basics, independent of customer or pincode.

## Proposed solution

**ReturnGuard AI** is a multi-agent plug-in that sits *in front of* checkout/shipping
decisioning (i.e., it composes with a platform's existing generic RTO agent rather
than replacing it) and adds fashion-specific evidence to the decision:

1. **Planner** — inspects the incoming order and decides which fetchers are relevant
   (e.g. skip campaign-spike fetch for a non-marketed SKU).
2. **Fetchers** (run in parallel) — `OrderHistoryFetcher`, `SizeOrderPatternFetcher`,
   `CampaignSpikeFetcher`, `PincodeRiskFetcher`, `CategoryReturnPriorFetcher`.
3. **Deterministic rule layer** — cheap, auditable hard rules run first (e.g. "3+
   sizes of the same SKU in one order" or "pincode on hard blacklist") and can
   short-circuit straight to a decision without ever invoking an LLM.
4. **LLM Analyzer** — only for the ambiguous middle band the rules can't confidently
   resolve, reasons over all fetched signals together and proposes one intervention.
5. **Guardrail layer** — the LLM never acts directly. It can only pick from a
   pre-approved action set (`allow`, `whatsapp_confirm`, `prepaid_incentive`,
   `manual_review`), and any discount it proposes is clamped to a hard ceiling. Every
   decision, including the full agent trace, is written to an audit log.

## Why this framing

- **Extends rather than competes** with an existing platform's product — it is a
  plug-in on top of a generic RTO agent, not a re-pitch of it.
- **Technically defensible**: category-specific feature engineering, not "call an LLM
  and hope." Rules are inspectable; LLM involvement is bounded to ambiguous cases.
- **Quantifiable impact**: RTO rate reduction on the fashion order segment, and
  time/cost saved vs. manual review, both measurable against a held-out order set.
- **Concrete guardrail story**: never auto-blocks or auto-discounts beyond a hard
  ceiling without the action passing through the guardrail layer, and every action is
  logged with the reasoning that produced it.

## What this project deliberately does NOT do

- Does not auto-cancel orders or auto-charge customers.
- Does not hardcode evidence/logic for a single card network or courier — the fetcher
  interface is provider-agnostic (mock providers are swapped for real ones later).
- Does not rely on a single LLM call for the whole decision — the LLM is invoked only
  for the ambiguous band, after deterministic rules have had first refusal.
