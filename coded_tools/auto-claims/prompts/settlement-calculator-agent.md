# Settlement Calculator Agent — Prompt Reference

**Agent**: `settlement_calculator_agent`  
**Type**: Leaf (MANDATORY)  
**User Story**: US-1007 — Settlement Proposal  
**Workbench Tab**: Settlement  
**request_type**: `settlement_calculation`

---

## Purpose

Calculates the recommended net settlement amount for an auto claim using the adjuster's
repair estimate, ACV, deductible, liability percentage, and state-specific TLT rules.
Returns authority level required and flags if a 1099 must be issued.

---

## When Triggered

- When adjuster opens the Settlement tab on the claim workbench
- Invoked via "Calculate Settlement" AI button on the Settlement tab
- Payload assembled from: claim record + estimation data + admin_configs TLT values

---

## Input Payload

```json
{
  "claim_id": 1001,
  "claim_type": "collision",
  "repair_estimate": 8500.0,
  "acv": 12000.0,
  "deductible": 500.0,
  "liability_percent": 100,
  "state_code": "TX",
  "tlt_threshold": 100,
  "medical_bills": 0.0,
  "lost_wages": 0.0,
  "pain_suffering_multiplier": 0.0,
  "lienholder_payoff": 0.0,
  "deferred_property_damage": 0.0
}
```

---

## Calculation Steps (MUST be followed exactly)

```
1. is_total_loss = (repair_estimate > acv * tlt_threshold / 100)
2. base_amount   = acv if is_total_loss else repair_estimate
3. pain_and_suffering = medical_bills * pain_suffering_multiplier
                        (only if multiplier > 0, else 0.0)
4. gross = base_amount - deductible + medical_bills + lost_wages
           + pain_and_suffering
5. gross = max(0.0, gross)
6. net   = max(0.0, round(gross * (liability_percent / 100.0), 2))
7. net_to_claimant = max(0.0, round(net - lienholder_payoff, 2))
```

---

## Authority Level Mapping

| Net Settlement | Authority Required |
|---------------|--------------------|
| <= $2,500 | `TRAINEE` |
| <= $5,000 | `ASSOCIATE` |
| <= $10,000 | `ADJUSTER` |
| <= $25,000 | `SENIOR` |
| <= $50,000 | `SUPERVISOR` |
| > $50,000 | `VP` |

---

## State-Specific TLT Notes

| State | Note |
|-------|------|
| TX | "Texas 100% TLT — vehicle must exceed full ACV to be declared total loss." |
| CA | "California 80% TLT per CIC §4751." |
| FL | "Florida 80% TLT per §319.30(3) Florida Statutes." |
| NY | "New York 75% TLT. Salvage title from DMV required within 30 days." |
| KS | "Kansas 75% TLT. Kansas Insurance Dept. standard." |
| MN | "Minnesota 75% TLT. Commissioner of Commerce standard." |
| Other | "Default {tlt_threshold}% TLT applies in {state_code}." |

---

## Output Schema

```json
{
  "recommended_settlement": 8000.0,
  "settlement_breakdown": {
    "base_amount": 8500.0,
    "deductible_applied": -500.0,
    "liability_factor": 1.0,
    "medical_bills": 0.0,
    "lost_wages": 0.0,
    "pain_and_suffering": 0.0,
    "total": 8000.0
  },
  "is_total_loss": false,
  "total_loss_analysis": {
    "repair_estimate": 8500.0,
    "acv": 12000.0,
    "tlt_threshold_pct": 100,
    "tlt_threshold_amount": 12000.0,
    "exceeds_tlt": false
  },
  "net_to_claimant": 8000.0,
  "lienholder_payoff": 0.0,
  "authority_level_required": "ADJUSTER",
  "requires_1099": true,
  "state_specific_notes": "Texas 100% TLT — vehicle must exceed full ACV.",
  "confidence": "HIGH",
  "confidence_notes": "Arithmetic calculation — deterministic result.",
  "notes": "Repairable — net settlement $8,000.00. Requires ADJUSTER authority."
}
```

---

## Example — Total Loss (CA, 80% TLT)

```
Input: repair=$9,000, acv=$10,000, tlt=80, deductible=$500, liability=100%
Step 1: is_total_loss = (9000 > 10000 * 80 / 100) = (9000 > 8000) = TRUE
Step 2: base = 10000 (ACV, total loss)
Step 4: gross = 10000 - 500 = 9500
Step 6: net = 9500 * 1.0 = 9500
```

```json
{
  "recommended_settlement": 9500.0,
  "is_total_loss": true,
  "authority_level_required": "ADJUSTER",
  "requires_1099": true,
  "state_specific_notes": "California 80% TLT per CIC §4751."
}
```

---

## Example — Shared Liability (50%)

```
Input: repair=$8000, acv=$12000, tlt=100, deductible=$500, liability=50%
Step 1: is_total_loss = (8000 > 12000) = FALSE
Step 2: base = 8000
Step 4: gross = 8000 - 500 = 7500
Step 6: net = 7500 * 0.50 = 3750
```

```json
{
  "recommended_settlement": 3750.0,
  "is_total_loss": false,
  "authority_level_required": "ASSOCIATE",
  "requires_1099": true
}
```
