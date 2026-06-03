# Agent Prompt Guide — `kyc_orchestrator`
*Network: kyc-onboarding | Role: Front-Man Orchestrator*
*Author: neuro_ai_developer | Phase: Build | Iteration: 1*

---

## Overview

`kyc_orchestrator` is the **front-man agent** for the KYC Onboarding AI advisory network. It is the only agent that the Flask application (`services/ai_bridge.py`) calls directly via `services/neuro_san_client.py`.

It receives a PII-scrubbed payload, delegates to three specialist sub-agents, and synthesises their findings into a single compliance advisory memo that is stored in the `applications.ai_summary` database column and displayed on the Application Detail page under the **AI Advisory (Non-Binding)** tab.

---

## Calling Context

**Called by:** `services/ai_bridge.py` → `_run_ai_review()` daemon thread  
**Endpoint:** `POST {NEURO_SAN_URL}/api/v1/streaming-agent-chat`  
**Payload key:** `"agent_name": "kyc_orchestrator"`  
**Validated by:** `VALID_AGENTS = frozenset({"kyc_orchestrator"})` in `models/constants.py`  
**Return shape:** `{"response": "<advisory text>"}` extracted by `neuro_san_client._extract_nested_response()`

---

## Input Payload Schema

```json
{
  "ref_number":        "KYC-260511-A001",
  "risk_rating":       "LOW | MEDIUM | HIGH | UNRATED",
  "is_pep":            false,
  "is_sanctioned":     false,
  "screening_results": [
    {"check_type": "OFAC",      "result": "CLEAR",         "details": "{}"},
    {"check_type": "PEP",       "result": "CLEAR",         "details": "{}"},
    {"check_type": "AML_SCORE", "result": "CLEAR",         "details": "{\"score\": 5, \"tier\": \"LOW\"}"}
  ],
  "identity": {
    "nationality": "US",
    "occupation":  "Teacher",
    "id_type":     "DRIVERS_LICENSE"
  }
}
```

**PII Fields Explicitly Excluded (compliance red line #5):**
- `full_name` — NEVER included
- `date_of_birth` — NEVER included
- `ssn_last4` — NEVER included
- `address_line1`, `address_line2`, `city`, `zip_code` — NEVER included
- `id_number` — NEVER included

---

## Sub-Agent Delegation Order

```
kyc_orchestrator
    1. → identity_reviewer(nationality, occupation, id_type)
    2. → screening_analyst(screening_results, is_pep, is_sanctioned)
    3. → risk_advisor(identity_assessment, screening_analysis, risk_rating, is_pep, is_sanctioned)
    4. Synthesise outputs into final advisory memo
```

---

## Expected Output Format

The orchestrator's final response must follow this structure:

```
RISK SUMMARY
[1-2 sentences: overall risk level and primary finding]

KEY RISK FACTORS
• [Factor 1]
• [Factor 2]
• [Factor N]

RECOMMENDED ACTION: [APPROVE / ESCALATE_EDD / REJECT]
[2-3 sentences of rationale]

REGULATORY BASIS
• [Regulation 1 with citation]
• [Regulation 2 with citation]

IMPORTANT: This advisory is non-binding. The Compliance Officer makes the final decision.
```

---

## Mandatory Compliance Constraints

| Constraint | Rule |
|---|---|
| OFAC match | NEVER recommend APPROVE when `is_sanctioned = true` |
| PEP flag | NEVER recommend APPROVE without noting EDD is mandatory |
| No PII reconstruction | Never reference, guess, or imply full name, DOB, SSN, or address |
| Word limit | 200–500 words total advisory |
| Non-binding disclaimer | Always include as final line |
| No status transitions | Advisory text only; no system actions triggered |

---

## Example Advisory Output (Happy Path — LOW risk)

```
RISK SUMMARY
Application KYC-260511-A001 presents a low-risk profile. All automated
screening checks returned clear results, and no PEP or sanctions flags
were identified.

KEY RISK FACTORS
• None identified — all screening checks clear
• Nationality: US (no elevated country risk)
• Occupation: Teacher (low-risk occupation category)
• Document type: Driver's License (standard domestic ID)

RECOMMENDED ACTION: APPROVE
All three automated screening checks (OFAC, PEP, AML Risk Score) returned
CLEAR results. The identity profile presents no elevated risk indicators.
Standard CDD procedures have been satisfied under BSA/AML program requirements.
Ongoing monitoring per FinCEN CDD Rule (31 CFR §1020.210) remains required.

REGULATORY BASIS
• BSA/AML Customer Due Diligence (CDD) Rule — 31 CFR §1020.210
• USA PATRIOT Act §326 (CIP requirements) — satisfied
• OFAC Screening — no SDN match

IMPORTANT: This advisory is non-binding. The Compliance Officer makes the
final decision.
```

---

## Example Advisory Output (EDD Escalation — HIGH risk, PEP)

```
RISK SUMMARY
Application KYC-260511-A003 presents a HIGH risk profile with both a PEP
flag and an OFAC screening hit. Immediate escalation is required.

KEY RISK FACTORS
• OFAC SDN LIST HIT — potential match on sanctions list (absolute regulatory bar to approval)
• PEP FLAG — applicant identified as Politically Exposed Person
• Nationality: RU (Russia — elevated country risk, FATF monitoring)
• AML Risk Score: HIGH tier (compounding factors)

RECOMMENDED ACTION: REJECT
An OFAC SDN list match creates an absolute legal prohibition under IEEPA and
applicable Executive Orders. US financial institutions are prohibited from
establishing or maintaining a customer relationship with SDN-listed persons.
Additionally, the PEP flag would independently require Enhanced Due Diligence.

REGULATORY BASIS
• OFAC Regulations — 31 CFR Chapter V; Executive Order 13382 (WMD)
• BSA/AML EDD requirements for HIGH-risk customers — 31 CFR §1020.210
• FinCEN PEP guidance — FIN-2008-G005
• SAR filing obligation may be triggered — 31 CFR §1020.320

IMPORTANT: This advisory is non-binding. The Compliance Officer makes the
final decision.
```
