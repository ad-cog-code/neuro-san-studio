# FNOL Triage Agent — Prompt Reference
## Auto Claims Management System | Neuro SAN Agent Network

**Agent Name**: `fnol_triage_agent`
**Role**: leaf
**Trigger**: On FNOL submission (after policy verification) — User Story US-1001
**Called by**: `services/neuro_san_client.py` via async 202 dispatch
**Authority Level**: Read-only analysis — no DB writes, no side effects

---

## Purpose

Analyze a First Notice of Loss (FNOL) to categorize the claim, assess severity,
recommend adjuster tier, provide initial fraud pre-screening notes, and suggest
next steps. This is the first AI touchpoint in the claims lifecycle.

---

## Input Payload Schema

```json
{
  "claim_type":           "collision",
  "incident_description": "I was driving on Highway 35...",
  "incident_date":        "2026-04-10",
  "vehicle_year":         2022,
  "vehicle_make":         "Toyota",
  "vehicle_model":        "Camry",
  "claimant_name":        "[PII — do not use or repeat]",
  "policy_number":        "POL-TEST-001",
  "fraud_score":          25,
  "state_code":           "TX"
}
```

---

## Output Schema (return ONLY valid JSON — no prose)

```json
{
  "suggested_category":         "STANDARD | COMPLEX | TOTAL_LOSS_LIKELY | SIU_REVIEW",
  "severity":                   "LOW | MEDIUM | HIGH | CATASTROPHIC",
  "recommended_adjuster_tier":  "STANDARD | SENIOR | SPECIALIST",
  "fraud_pre_score_notes":      "1-2 sentence note on fraud risk factors",
  "complexity_indicators":      ["list of complexity reasons, or empty"],
  "next_steps":                 ["3-5 ordered adjuster actions"],
  "priority_flag":              "ROUTINE | URGENT | EXPEDITE",
  "estimated_settlement_range": {"low": 0, "high": 0, "currency": "USD"},
  "coverage_verification_notes": "Coverage concerns for this claim type + state"
}
```

---

## Business Rules

| Condition | Action |
|-----------|--------|
| `fraud_score >= 70` | `suggested_category = SIU_REVIEW` |
| Description contains "total loss", "totaled", "airbag deployed" | `suggested_category = TOTAL_LOSS_LIKELY` |
| State in `[FL,MI,NY,PA,HI,KS,MN,ND,OR,UT,WA,WI]` | Note PIP/no-fault in `coverage_verification_notes` |
| Bodily injury keywords in description | `severity = HIGH` or `CATASTROPHIC` |
| Fatalities mentioned | `severity = CATASTROPHIC` |

**PII Rule**: Never include, quote, or reference `claimant_name` or any PII in the response.

---

## Test Cases

| Input | Expected Output |
|-------|----------------|
| `fraud_score=80` | `suggested_category = SIU_REVIEW` |
| `incident_description = "total loss"` | `suggested_category = TOTAL_LOSS_LIKELY` |
| `state_code = FL` | PIP / 14-day rule mentioned in `coverage_verification_notes` |
| `fraud_score=10, collision, TX` | `suggested_category = STANDARD`, `severity = LOW` |
| Description mentions "hospitalized" | `severity = HIGH` |

---

## Integration Points

- Invoked from: `blueprints/adjuster/routes.py::invoke_agent()` via POST `/adjuster/api/agent/invoke`
- Result displayed on: `templates/adjuster/workbench.html` → `<pre id="fnol_triage_agent-result">`
- Activity logged: `AGENT_INVOKED` and `AGENT_RESULT_RECEIVED` in `activity_log`
- Stub fallback: `services/neuro_san_client.py::_get_stub_response('fnol_triage_agent', ...)`

---

*Auto Claims Management System | Iteration 1 MVP | 2026-05-05*
