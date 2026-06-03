# Optional Agents — Prompt Reference

**Agents**: `liability_agent`, `total_loss_agent`, `fraud_detection_agent`, `subrogation_agent`  
**Type**: Leaf (OPTIONAL)  
**User Stories**: US-1004, US-1005, US-1013, Sprint 2

---

## 1. Liability Agent

**Agent**: `liability_agent` | **request_type**: `liability_assessment`  
**User Story**: US-1004 (Investigation enhancement)  
**Workbench Tab**: Investigation

### Purpose
Assesses claimant vs third-party liability percentage based on incident facts, police
report, and state comparative/contributory negligence rules.

### Input
```json
{
  "incident_description": "Rear-ended at red light. Other driver failed to stop.",
  "police_report_summary": "Officer cited other driver for following too close.",
  "state_code": "TX",
  "claim_type": "collision",
  "claimant_statement": "I was stopped at a red light when hit from behind.",
  "third_party_statement": "The claimant stopped suddenly."
}
```

### Output Schema
```json
{
  "claimant_liability_pct": 0,
  "third_party_liability_pct": 100,
  "negligence_rule": "COMPARATIVE",
  "state_rule_notes": "TX uses comparative negligence — recovery reduced by claimant fault %.",
  "liability_basis": "Rear-end collision. Other driver cited. Clear third-party fault.",
  "confidence": "HIGH",
  "flags": []
}
```

### Negligence Rules by State

**Contributory negligence** (any claimant fault bars recovery):
- States: AL, DC, MD, NC, VA
- Must note: "CONTRIBUTORY STATE: Claimant fault may bar recovery."

**Comparative negligence** (all other states):
- Recovery reduced proportionally by claimant fault %.

### Confidence Levels
- `HIGH`: Police report confirms fault, no dispute
- `MEDIUM`: Police report available with some dispute, OR facts clear without police report
- `LOW`: No police report + disputed facts

---

## 2. Total Loss Agent

**Agent**: `total_loss_agent` | **request_type**: `total_loss_evaluation`  
**User Story**: US-1005 (Estimation enhancement)  
**Workbench Tab**: Estimation

### Purpose
Recommends whether a vehicle should be declared a total loss. Applies state TLT
threshold, estimates salvage value, calculates net total loss settlement.

### Input
```json
{
  "repair_estimate": 8500.0,
  "acv": 10000.0,
  "state_code": "CA",
  "tlt_threshold": 80,
  "vehicle_year": 2018,
  "vehicle_make": "Honda",
  "vehicle_model": "Civic",
  "mileage": 85000
}
```

### Output Schema
```json
{
  "recommend_total_loss": true,
  "tlt_calculation": "8500 / 10000 = 85.0% vs TLT 80%",
  "tl_percentage": 85.0,
  "tlt_threshold_used": 80,
  "acv_used": 10000.0,
  "repair_estimate_used": 8500.0,
  "market_adjustment_notes": "No market adjustment — standard valuation.",
  "salvage_value_estimate": 2000.0,
  "net_total_loss_settlement": 8000.0,
  "dmv_notification_needed": true,
  "state_notes": "California 80% TLT per CIC §4751. Salvage certificate required.",
  "recommendation_rationale": "Repair cost (85%) exceeds TLT threshold (80%). Total loss recommended.",
  "confidence": "HIGH"
}
```

### TLT Calculation
- `tl_percentage = repair_estimate / acv * 100`
- `recommend_total_loss = tl_percentage >= tlt_threshold`
- `salvage_value_estimate = acv * 0.20` (if total loss)
- `net_total_loss_settlement = acv - salvage_value_estimate`
- `dmv_notification_needed = recommend_total_loss`

### State TLT Notes
| State | TLT % | Note |
|-------|--------|------|
| TX | 100% | Title surrender required |
| CA | 80% | CIC §4751, salvage certificate |
| FL | 80% | §319.30(3), electronic title surrender |
| NY | 75% | DMV salvage title within 30 days |
| KS | 75% | KS Insurance Dept. standard |
| MN | 75% | Commissioner of Commerce standard |

---

## 3. Fraud Detection Agent (Enhanced NLP)

**Agent**: `fraud_detection_agent` | **request_type**: `fraud_detection`  
**User Story**: US-1013 (Fraud scoring enhancement)  
**Workbench Tab**: Investigation (Fraud section)

### Purpose
Enhanced NLP fraud analysis of claim narrative text. Supplements the system's
synchronous 8-indicator `fraud_service.py` score with pattern recognition.

### Input
```json
{
  "incident_description": "My car was damaged while parked. I don't know how it happened.",
  "adjuster_notes": "No witnesses. No police report. Large repair estimate.",
  "claim_type": "collision",
  "fraud_score": 45,
  "prior_claims_count": 2,
  "days_since_policy_inception": 18
}
```

### Output Schema
```json
{
  "fraud_score_confirmed": 45,
  "narrative_fraud_risk": "MEDIUM",
  "suspicious_patterns": [
    "Vague incident description — no specifics on location or time",
    "No witnesses or police report for collision claim",
    "New policy (18 days) with immediate claim"
  ],
  "linguistic_indicators": [
    "Vague description ('I don't know how it happened')",
    "Passive voice throughout narrative"
  ],
  "recommendation": "ENHANCED_INVESTIGATION",
  "confidence": "MEDIUM",
  "rationale": "System score (45) combined with narrative vagueness and new policy flag warrants enhanced investigation. No clear indicators for immediate SIU referral."
}
```

### Suspicious Patterns to Detect
- Vague or generic descriptions ("car just stopped", "brakes failed suddenly")
- Inconsistent timeline (impossible sequence of events)
- Over-specific damage detail but vague accident circumstances
- Missing key contextual details (location, time, weather, road conditions, witnesses)
- Scripted or rehearsed tone
- Witnesses named but not corroborated in police report

### Policy Inception Red Flags
- `days_since_policy_inception < 30`: elevated risk
- `days_since_policy_inception < 7`: HIGH risk — add to suspicious_patterns

### Recommendation Rules
| Condition | recommendation |
|-----------|----------------|
| `fraud_score >= 70` OR `narrative_fraud_risk = "HIGH"` | `SIU_REFERRAL` |
| `fraud_score >= 40` OR `narrative_fraud_risk = "MEDIUM"` | `ENHANCED_INVESTIGATION` |
| `fraud_score < 40` AND `narrative_fraud_risk = "LOW"` | `NO_ACTION` |

---

## 4. Subrogation Agent

**Agent**: `subrogation_agent` | **request_type**: `subrogation_evaluation`  
**User Story**: Sprint 2 (post-settlement)  
**Workbench Tab**: Settlement

### Purpose
Evaluates whether the insurer can recover settled amounts from an at-fault third party.
Considers state-specific subrogation rules and statute of limitations.

### Input
```json
{
  "claim_type": "collision",
  "claimant_liability_pct": 0,
  "third_party_identified": true,
  "third_party_insured": true,
  "settlement_amount": 8000.0,
  "state_code": "TX"
}
```

### Output Schema
```json
{
  "subrogation_viable": true,
  "recommended_action": "PURSUE",
  "recoverable_amount": 8000.0,
  "claimant_liability_pct": 0,
  "third_party_identified": true,
  "third_party_insured": true,
  "viability_rationale": "Third party identified and insured. Claimant not at fault. Full recovery possible.",
  "state_specific_notes": "TX: Subrogation allowed for all claim types. Property damage SOL: 2 years.",
  "statute_of_limitations_note": "TX property damage SOL: 2 years from date of loss.",
  "notes": "Subrogation viable. Recoverable: $8,000.00. Recommend pursuing third-party insurer."
}
```

### Viability Calculation
```
subrogation_viable = (claimant_liability_pct < 100)
                     AND third_party_identified
                     AND (settlement_amount > 0)

recoverable_amount = settlement_amount * (1 - claimant_liability_pct / 100)
                     (if viable, else 0.0)
```

### Recommended Action
| Condition | recommended_action |
|-----------|-------------------|
| NOT viable | `WAIVE` |
| Viable + `third_party_insured = true` | `PURSUE` |
| Viable + `third_party_insured = false` | `INVESTIGATE` |

### State-Specific Notes
| State | Note |
|-------|------|
| CA | Subrogation allowed for UM/UIM claims against uninsured motorists |
| FL | PIP benefits not subject to subrogation in most cases (§627.736) |
| TX | All claim types, property damage SOL: 2 years |
| NY | No-fault limits subrogation — economic losses must exceed $50K |
| MI | Anti-subrogation rule for PIP. Unlimited medical exception applies |
