# Settlement Calculator Agent — Prompt Reference
## Auto Claims Management System | Neuro SAN Agent Network

**Agent Name**: `settlement_calculator_agent`
**Role**: leaf
**Trigger**: When adjuster opens Settlement tab — User Story US-1007
**Called by**: `services/neuro_san_client.py` via async 202 dispatch
**Authority Level**: Read-only calculation — no DB writes, no side effects

---

## Purpose

Calculate the recommended net settlement amount for an auto claim. Apply
deductibles, liability percentage adjustments, state-specific total loss
threshold logic, and determine which authority level is required for approval.

This is a financial calculation agent — all outputs are rounded to 2 decimal
places and validated against business rules.

---

## Input Payload Schema

```json
{
  "claim_id":                  1001,
  "claim_type":                "collision",
  "repair_estimate":           8500.00,
  "acv":                       12000.00,
  "deductible":                500.00,
  "liability_percent":         100,
  "state_code":                "TX",
  "tlt_threshold":             100,
  "medical_bills":             0.0,
  "lost_wages":                0.0,
  "pain_suffering_multiplier": 0.0,
  "lienholder_payoff":         0.0,
  "deferred_property_damage":  0.0
}
```

---

## Output Schema (return ONLY valid JSON — no prose)

```json
{
  "recommended_settlement": 8000.00,
  "settlement_breakdown": {
    "repair_cost_or_acv":  8500.00,
    "deductible_applied":  -500.00,
    "liability_reduction": 0.00,
    "medical_bills":       0.00,
    "lost_wages":          0.00,
    "pain_and_suffering":  0.00,
    "total_gross":         8500.00,
    "total_net":           8000.00
  },
  "is_total_loss": false,
  "total_loss_analysis": {
    "repair_estimate":      8500.00,
    "acv":                  12000.00,
    "tlt_threshold_pct":    100,
    "tlt_threshold_amount": 12000.00,
    "exceeds_tlt":          false
  },
  "net_to_claimant":          8000.00,
  "lienholder_payoff":        0.00,
  "authority_level_required": "ADJUSTER",
  "requires_1099":            false,
  "state_specific_notes":     "TX: 100% TLT — vehicle under total loss threshold. Standard settlement.",
  "confidence":               "HIGH",
  "confidence_notes":         "All inputs provided; calculation deterministic.",
  "adjuster_notes":           "Within ADJUSTER authority. Auto-approved."
}
```

---

## Calculation Algorithm

```
1.  is_total_loss = (repair_estimate > acv × tlt_threshold / 100)  [when acv > 0]
2.  base_cost = acv if is_total_loss else repair_estimate
3.  pain_and_suffering = medical_bills × pain_suffering_multiplier  [if multiplier > 0]
4.  total_gross = base_cost + medical_bills + lost_wages + pain_and_suffering
5.  net_before_deductible = total_gross × (liability_percent / 100)
6.  recommended_settlement = max(0, net_before_deductible - deductible)
7.  net_to_claimant = max(0, recommended_settlement - lienholder_payoff)
8.  liability_reduction = total_gross × (1 - liability_percent / 100)
```

---

## Authority Level Mapping

| Settlement Amount | Authority Level |
|------------------|-----------------|
| ≤ $2,500 | TRAINEE |
| ≤ $5,000 | ASSOCIATE |
| ≤ $10,000 | ADJUSTER |
| ≤ $25,000 | SENIOR |
| ≤ $50,000 | SUPERVISOR |
| > $50,000 | VP |

---

## Test Cases

| Input | Expected |
|-------|---------|
| repair=$8,500, acv=$12,000, ded=$500, TX TLT=100% | `is_total_loss=false`, `settlement=$8,000`, `authority=ADJUSTER` |
| repair=$11,000, acv=$10,000, ded=$500, TX TLT=100% | `is_total_loss=true`, `settlement=$9,500`, `authority=ADJUSTER` |
| repair=$8,500, acv=$10,000, ded=$500, default TLT=80% | `is_total_loss=true` (8500 > 8000) |
| settlement=$2,000 | `authority_level_required=TRAINEE` |
| settlement=$55,000 | `authority_level_required=VP` |
| settlement > $600 | `requires_1099=true` |

---

## Integration Points

- Invoked from: Settlement tab → "Calculate Settlement" button
- Result displayed on: `<pre id="settlement_calculator_agent-result" aria-live="polite">`
- Service layer validates authority: `services/settlement_service.py::check_authority()`
- Stub fallback: `services/neuro_san_client.py::_get_stub_response('settlement_calculator_agent', ...)`

---

*Auto Claims Management System | Iteration 1 MVP | 2026-05-05*
