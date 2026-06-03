# Coverage Agent — Prompt Reference

**Agent**: `coverage_agent`  
**Type**: Leaf (MANDATORY)  
**User Story**: US-1003 — Coverage Verification  
**Workbench Tab**: Policy  
**request_type**: `coverage_verification`

---

## Purpose

Verifies insurance coverage for a claim when the adjuster opens the Policy tab.
Confirms applicable coverages, limits, deductible, exclusions, and no-fault/PIP
rules for the claimant's state. Recommends denial if the policy is inactive or
the claim type is not covered.

---

## When Triggered

- When adjuster opens the Policy tab on the claim workbench
- Invoked via "Run AI Coverage Check" button on the Policy tab
- Payload assembled from: policy stub response + claim record + claimant state

---

## Input Payload

```json
{
  "policy_number": "POL-TEST-001",
  "claim_type": "collision",
  "incident_date": "2026-04-10",
  "vehicle_vin": "1HGCM82633A004352",
  "claimant_state": "TX",
  "coverage_types": ["collision", "comprehensive", "liability"],
  "deductible": 500.0,
  "limits": {
    "collision": 250000,
    "liability": 300000,
    "pip": 0
  },
  "exclusions": [],
  "policy_status": "ACTIVE",
  "pip_limit": null
}
```

---

## Output Schema

```json
{
  "coverage_confirmed": true,
  "denial_recommended": false,
  "policy_status": "ACTIVE",
  "coverage_types_applicable": ["collision"],
  "deductible": 500.0,
  "policy_limit": 250000.0,
  "exclusions_triggered": [],
  "no_fault_applies": false,
  "pip_limit": null,
  "pip_baseline_note": "",
  "coverage_gaps": [],
  "coverage_notes": "Collision coverage confirmed. No exclusions triggered.",
  "denial_reason": null
}
```

---

## Coverage Determination Rules

| Condition | coverage_confirmed | denial_recommended | denial_reason |
|-----------|-------------------|--------------------|---------------|
| `policy_status != "ACTIVE"` | `false` | `true` | `"Policy status: {status}"` |
| `claim_type not in coverage_types` (and coverage_types non-empty) | `false` | `true` | `"Claim type not covered"` |
| Both checks pass | `true` | `false` | `null` |

---

## No-Fault State PIP Rules

| State | pip_baseline_note content requirements |
|-------|---------------------------------------|
| FL | "14-day rule" + "$10,000 PIP baseline minimum" + "Emergency: 80%; non-emergency: 60%" |
| MI | "unlimited medical" + "Catastrophic Claims Association (MCCA)" |
| NY | "Basic Economic Loss" + "$50,000" |
| PA | "limited vs full tort" + pain & suffering recovery impact |
| HI, KS, MN, ND, OR, UT, WA, WI | Note PIP applies; verify policy PIP limits |
| Non-no-fault states | `no_fault_applies = false`, `pip_limit = null`, `pip_baseline_note = ""` |

---

## Example Output — Coverage Confirmed (TX)

```json
{
  "coverage_confirmed": true,
  "denial_recommended": false,
  "policy_status": "ACTIVE",
  "coverage_types_applicable": ["collision"],
  "deductible": 500.0,
  "policy_limit": 250000.0,
  "exclusions_triggered": [],
  "no_fault_applies": false,
  "pip_limit": null,
  "pip_baseline_note": "",
  "coverage_gaps": [],
  "coverage_notes": "Collision coverage active. Policy ACTIVE. No exclusions triggered. Deductible $500.",
  "denial_reason": null
}
```

---

## Example Output — Coverage Denied (EXPIRED policy)

```json
{
  "coverage_confirmed": false,
  "denial_recommended": true,
  "policy_status": "EXPIRED",
  "coverage_types_applicable": [],
  "deductible": 0.0,
  "policy_limit": 0.0,
  "exclusions_triggered": ["Policy expired — no coverage in force on incident date"],
  "no_fault_applies": false,
  "pip_limit": null,
  "pip_baseline_note": "",
  "coverage_gaps": ["Policy expired before incident date"],
  "coverage_notes": "Coverage not confirmed. Policy EXPIRED. Denial recommended.",
  "denial_reason": "Policy status: EXPIRED"
}
```

---

## Example Output — No-Fault State (FL, PIP claim)

```json
{
  "coverage_confirmed": true,
  "denial_recommended": false,
  "policy_status": "ACTIVE",
  "coverage_types_applicable": ["pip"],
  "deductible": 0.0,
  "policy_limit": 10000.0,
  "exclusions_triggered": [],
  "no_fault_applies": true,
  "pip_limit": 10000.0,
  "pip_baseline_note": "FL is a no-fault state. 14-day rule applies — claimant must seek treatment within 14 days of accident. $10,000 PIP baseline minimum. Emergency medical: 80% covered; non-emergency: 60%.",
  "coverage_gaps": [],
  "coverage_notes": "PIP coverage confirmed for FL no-fault claim. 14-day rule applies.",
  "denial_reason": null
}
```
