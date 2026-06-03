# Optional Agents — Prompt Reference
## Auto Claims Management System | Neuro SAN Agent Network

This document covers the 4 optional agents: `liability_agent`, `total_loss_agent`,
`fraud_detection_agent`, and `subrogation_agent`.

---

## liability_agent

**Trigger**: Investigation completion for liability/BI claims (US-1004 enhancement)
**Role**: leaf | **Scope**: Optional — MVP enhancement

### Input
```json
{
  "incident_description":    "Rear-end collision on I-35...",
  "police_report_summary":   "Officer noted Vehicle A failed to stop..." | null,
  "state_code":              "TX",
  "claim_type":              "liability",
  "claimant_statement":      "The other driver ran a red light..." | null,
  "third_party_statement":   "I had the green light..." | null
}
```

### Output
```json
{
  "claimant_liability_pct":    20,
  "third_party_liability_pct": 80,
  "negligence_rule":           "COMPARATIVE",
  "state_rule_notes":          "TX comparative negligence — proportional reduction applies",
  "liability_basis":           "Police report indicates third party ran red light (80% at fault)...",
  "confidence":                "HIGH",
  "flags":                     []
}
```

### Key Rules
- Contributory states (AL, MD, NC, VA, DC): any claimant fault may bar recovery
- Sum of percentages must equal 100
- Low confidence when police report unavailable

---

## total_loss_agent

**Trigger**: Adjuster enters repair estimate (US-1005)
**Role**: leaf | **Scope**: Optional — MVP enhancement

### Input
```json
{
  "repair_estimate": 9500.00,
  "acv":             10000.00,
  "state_code":      "TX",
  "tlt_threshold":   100,
  "vehicle_year":    2019,
  "vehicle_make":    "Honda",
  "vehicle_model":   "Civic",
  "mileage":         85000
}
```

### Output
```json
{
  "recommend_total_loss":       false,
  "tlt_calculation":            "9500 / 10000 = 95% vs TLT 100%",
  "market_adjustment_notes":    "No significant market factors — standard vehicle",
  "salvage_value_estimate":     1500.00,
  "net_total_loss_settlement":  8500.00,
  "recommendation_rationale":   "Repair cost is 95% of ACV but TX TLT is 100%...",
  "confidence":                 "HIGH"
}
```

### Key Rules
- `recommend_total_loss = (repair_estimate > acv × tlt_threshold / 100)`
- Salvage ≈ 15% of ACV (use as default)
- Consider: rare parts, high-mileage vehicles, age

---

## fraud_detection_agent

**Trigger**: Adjuster-initiated enhanced fraud review (US-1013 enhancement)
**Role**: leaf | **Scope**: Optional — supplements synchronous 8-indicator score

### Input
```json
{
  "incident_description":        "My car was hit while parked...",
  "adjuster_notes":              "Claimant was vague about exact time...",
  "claim_type":                  "collision",
  "fraud_score":                 55,
  "prior_claims_count":          2,
  "days_since_policy_inception": 45
}
```

### Output
```json
{
  "narrative_fraud_risk":   "MEDIUM",
  "suspicious_patterns":    ["Vague incident timeline", "Prior claims history"],
  "linguistic_indicators":  ["Inconsistent detail level — high on damages, low on incident"],
  "recommendation":         "ENHANCED_INVESTIGATION",
  "confidence":             "MEDIUM",
  "rationale":              "Fraud score 55/100 combined with vague timeline..."
}
```

### Key Rules
- HIGH: fraud_score >= 70 OR multiple linguistic indicators
- SIU_REFERRAL: requires adjuster confirmation (never automatic)
- days_since_policy_inception <= 30: note FI-008 in linguistic_indicators

---

## subrogation_agent

**Trigger**: Claim closure for applicable claim types (Sprint 2 scope)
**Role**: leaf | **Scope**: Optional — Sprint 2

### Input
```json
{
  "claim_type":              "collision",
  "claimant_liability_pct":  0,
  "third_party_identified":  true,
  "third_party_insured":     true,
  "settlement_amount":       8000.00,
  "state_code":              "TX"
}
```

### Output
```json
{
  "subrogation_viable":           true,
  "subrogation_potential_amount": 8000.00,
  "viability_rationale":          "Third party identified and insured; claimant not at fault...",
  "recommended_action":           "PURSUE",
  "state_specific_notes":         "TX: 2-year statute of limitations for subrogation claims"
}
```

### Key Rules
- Viable when: `third_party_identified = true AND claimant_liability_pct < 100`
- `subrogation_potential_amount = settlement × (1 - claimant_liability_pct / 100)`
- PURSUE when third party is insured; EVALUATE_FURTHER when uninsured

---

## Integration Points (all optional agents)

All optional agents use the same infrastructure:
- Invoked via: `POST /adjuster/api/agent/invoke` → `{ "agent": "agent_name", ... }`
- Polled via: `GET /adjuster/api/agent/status/<job_id>`
- Result displayed: `<pre id="agent_name-result" aria-live="polite">`
- Stub fallback: `services/neuro_san_client.py::_get_stub_response(agent_name, ...)`
- Activity logged: `AGENT_INVOKED`, `AGENT_RESULT_RECEIVED` in `activity_log`

---

*Auto Claims Management System | Iteration 1 MVP | 2026-05-05*
