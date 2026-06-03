# FNOL Triage Agent — Prompt Reference

**Agent**: `fnol_triage_agent`  
**Type**: Leaf (MANDATORY)  
**User Story**: US-1001 — FNOL Submission  
**Workbench Tab**: Overview  
**request_type**: `fnol_triage`

---

## Purpose

Analyzes a new First Notice of Loss (FNOL) submission immediately after policy
verification and fraud score calculation. Returns a structured triage assessment
that tells the adjuster how to classify, prioritize, and handle the new claim.

---

## When Triggered

- After successful FNOL submission (`POST /fnol/submit`)
- After policy stub verification (`stubs/policy_stub.verify_policy()`)
- After fraud score calculation (`services/fraud_service.calculate_fraud_score()`)
- Invoked asynchronously: Flask returns 202, adjuster sees result in Overview tab

---

## Input Payload

```json
{
  "claim_type": "collision",
  "incident_description": "I was rear-ended at a red light on Highway 1. The other driver ran the light.",
  "incident_date": "2026-04-10",
  "vehicle_year": 2022,
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "policy_number": "POL-TEST-001",
  "fraud_score": 25,
  "state_code": "TX"
}
```

**Note**: `policy_number` is included for internal context only. The agent must
NOT echo policy number or claimant PII in its output.

---

## Output Schema

```json
{
  "suggested_category": "STANDARD | COMPLEX | TOTAL_LOSS_LIKELY | SIU_REVIEW",
  "severity": "LOW | MEDIUM | HIGH | CATASTROPHIC",
  "recommended_adjuster_tier": "STANDARD | SENIOR | SPECIALIST",
  "fraud_pre_score_notes": "Brief note on fraud risk factors from narrative",
  "complexity_indicators": ["reason if complex"],
  "next_steps": ["Step 1", "Step 2", "Step 3"],
  "priority_flag": true,
  "estimated_settlement_range": {"low": 0, "high": 0, "currency": "USD"},
  "coverage_verification_notes": "State/claim-type-specific coverage note"
}
```

---

## Triage Decision Rules

| Condition | suggested_category | severity | tier |
|-----------|-------------------|----------|------|
| `fraud_score >= 70` | `SIU_REVIEW` | `HIGH` | `SPECIALIST` |
| Description: "total loss", "airbag deployed", "vehicle destroyed", "totaled" | `TOTAL_LOSS_LIKELY` | `HIGH` | (inherit) |
| Description: bodily injury / hospitalization / fatality | (inherit) | `HIGH` or `CATASTROPHIC` | (inherit) |
| `claim_type` in `um`, `uim`, `medpay` | `COMPLEX` | `MEDIUM` | `SENIOR` |
| `fraud_score >= 40` | `COMPLEX` | `MEDIUM` | `SENIOR` |
| Default | `STANDARD` | `LOW` | `STANDARD` |

---

## No-Fault State Rules for coverage_verification_notes

| State | Required content |
|-------|-----------------|
| FL | "14-day rule" AND "$10,000 PIP baseline minimum" |
| MI | "unlimited medical PIP" AND "MCCA" |
| NY | "$50,000 Basic Economic Loss" |
| PA | "limited vs full tort election" |
| HI, KS, MN, ND, OR, UT, WA, WI | Note PIP applies; verify policy limits |
| All other states | Standard liability rules; note contributory states (AL, DC, MD, NC, VA) |

---

## Example Output (Standard Claim, TX)

```json
{
  "suggested_category": "STANDARD",
  "severity": "LOW",
  "recommended_adjuster_tier": "STANDARD",
  "fraud_pre_score_notes": "Fraud score 25/100 — within normal range. No specific narrative concerns.",
  "complexity_indicators": [],
  "next_steps": [
    "Verify collision coverage and deductible",
    "Schedule vehicle inspection",
    "Request police report"
  ],
  "priority_flag": false,
  "estimated_settlement_range": {"low": 3000, "high": 15000, "currency": "USD"},
  "coverage_verification_notes": "Standard liability state. Verify collision/comprehensive coverage and deductible amount."
}
```

---

## Example Output (SIU Review, FL)

```json
{
  "suggested_category": "SIU_REVIEW",
  "severity": "HIGH",
  "recommended_adjuster_tier": "SPECIALIST",
  "fraud_pre_score_notes": "Fraud score 75/100 — exceeds SIU auto-flag threshold of 70. Assign to SIU for review.",
  "complexity_indicators": [
    "High fraud score (75/100)",
    "PIP claim in no-fault state — Florida 14-day rule applies"
  ],
  "next_steps": [
    "Do not proceed with standard processing",
    "Refer to SIU immediately",
    "Document all communications",
    "Verify Florida 14-day treatment rule compliance"
  ],
  "priority_flag": true,
  "estimated_settlement_range": {"low": 0, "high": 0, "currency": "USD"},
  "coverage_verification_notes": "FL is a no-fault state. 14-day rule applies — claimant must seek treatment within 14 days. $10,000 PIP baseline minimum. Emergency medical: 80% covered; non-emergency: 60%."
}
```
