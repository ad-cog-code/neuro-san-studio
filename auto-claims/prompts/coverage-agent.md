# Coverage Agent — Prompt Reference
## Auto Claims Management System | Neuro SAN Agent Network

**Agent Name**: `coverage_agent`
**Role**: leaf
**Trigger**: When adjuster opens Policy tab — User Story US-1003
**Called by**: `services/neuro_san_client.py` via async 202 dispatch
**Authority Level**: Read-only analysis — no DB writes, no side effects

---

## Purpose

Verify insurance coverage for a claim. Determine applicable coverages, limits,
deductibles, triggered exclusions, and state-specific PIP/no-fault rules.
Recommend denial when coverage clearly does not apply.

---

## Input Payload Schema

```json
{
  "policy_number":   "POL-TEST-001",
  "claim_type":      "collision",
  "incident_date":   "2026-04-10",
  "vehicle_vin":     "1HGCM82633A004352",
  "claimant_state":  "TX",
  "coverage_types":  ["collision", "comprehensive", "liability", "pip"],
  "deductible":      500.0,
  "limits":          {"collision": 250000, "liability": 300000, "pip": 10000},
  "exclusions":      [],
  "policy_status":   "ACTIVE"
}
```

---

## Output Schema (return ONLY valid JSON — no prose)

```json
{
  "coverage_confirmed":         true,
  "coverage_types_applicable":  ["collision"],
  "deductible":                 500.0,
  "policy_limit":               250000.0,
  "exclusions_triggered":       [],
  "no_fault_applies":           false,
  "pip_limit":                  null,
  "pip_baseline_note":          "",
  "coverage_gaps":              [],
  "coverage_notes":             "Collision coverage confirmed. Deductible $500 applies.",
  "denial_recommended":         false,
  "denial_reason":              null
}
```

---

## Business Rules

| Condition | Action |
|-----------|--------|
| `policy_status != 'ACTIVE'` | `coverage_confirmed = false`, `denial_recommended = true` |
| `claim_type not in coverage_types` | `coverage_confirmed = false`, `denial_recommended = true` |
| State in no-fault states | `no_fault_applies = true` |
| `state = FL` | Must include "14-day rule" and "$10,000 minimum PIP baseline" |
| `state = MI` | Must include "unlimited medical benefits" and "catastrophic assigned care" |
| `state = NY` | Must include "$50,000 no-fault basic economic loss limit" |
| `claim_type = 'pip'` and `no_fault_applies = false` | `coverage_confirmed = false` |

**No-fault states**: FL, MI, NY, PA, HI, KS, MN, ND, OR, UT, WA, WI

---

## Test Cases

| Input | Expected Output |
|-------|----------------|
| `policy_status = ACTIVE, claim_type in coverage_types` | `coverage_confirmed = true` |
| `policy_status = EXPIRED` | `coverage_confirmed = false, denial_recommended = true` |
| `claim_type = collision, coverage_types = ['liability']` | `coverage_confirmed = false` |
| `claimant_state = FL` | `pip_baseline_note` includes "14-day rule" |
| `claimant_state = MI` | `pip_baseline_note` includes "unlimited medical" |
| `claimant_state = TX` | `no_fault_applies = false` |

---

## Integration Points

- Invoked from: Policy tab → "Run Coverage Verification" button
- Result displayed on: `<pre id="coverage_agent-result" aria-live="polite">`
- Stub fallback: `services/neuro_san_client.py::_get_stub_response('coverage_agent', ...)`

---

*Auto Claims Management System | Iteration 1 MVP | 2026-05-05*
