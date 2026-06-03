# Auto Claims — Neuro SAN Agent Network
## neuro-san-studio/auto-claims/

**Project**: Auto Claims Management System
**Port**: 6001
**HOCON**: `neuro-san-studio/registries/auto-claims/auto-claims.hocon`

---

## Quick Start

```bash
# From neuro-san-studio root:
python -m neuro_san.run_server --registry registries/auto-claims/auto-claims.hocon

# Flask app (separate terminal):
cd C:\my-projects\auto-claims
python app.py
```

When the Neuro SAN server is NOT running, the Flask app automatically uses
stub responses from `services/neuro_san_client.py::_get_stub_response()`.
No configuration is needed to enable the stub fallback.

---

## Agent Network

| Agent | Role | Story | Status |
|-------|------|-------|--------|
| `claims_orchestrator` | top (router) | — | MANDATORY |
| `fnol_triage_agent` | leaf | US-1001 | MANDATORY |
| `coverage_agent` | leaf | US-1003 | MANDATORY |
| `settlement_calculator_agent` | leaf | US-1007 | MANDATORY |
| `liability_agent` | leaf | US-1004 | OPTIONAL |
| `total_loss_agent` | leaf | US-1005 | OPTIONAL |
| `fraud_detection_agent` | leaf | US-1013 | OPTIONAL |
| `subrogation_agent` | leaf | Sprint 2 | OPTIONAL |

---

## HTTP Pattern (ADR-003 / AppMagic Learning #21)

```
POST /adjuster/api/agent/invoke
Body: {"agent": "coverage_agent", "payload": {...}, "claim_id": 1001}
→ 202 Accepted: {"job_id": "uuid-here", "status": "pending"}

Poll: GET /adjuster/api/agent/status/{job_id}
→ {"status": "pending"|"running"|"done"|"error", "result": {...}}
```

JavaScript client: `static/js/agent-poll.js` → `AgentPoll.invoke()`

---

## VALID_AGENTS Frozenset (services/neuro_san_client.py)

```python
VALID_AGENTS = frozenset({
    'fnol_triage_agent',
    'coverage_agent',
    'settlement_calculator_agent',
    'liability_agent',
    'total_loss_agent',
    'fraud_detection_agent',
    'subrogation_agent',
})
```

Any name not in this frozenset returns HTTP 400 before any Neuro SAN call.

---

## Prompt Files

| File | Agent |
|------|-------|
| `fnol-triage-agent.md` | `fnol_triage_agent` |
| `coverage-agent.md` | `coverage_agent` |
| `settlement-calculator-agent.md` | `settlement_calculator_agent` |
| `optional-agents.md` | liability, total_loss, fraud_detection, subrogation |

---

## Environment Variables (.env)

```
NEURO_SAN_HOST=localhost     # Neuro SAN server host
NEURO_SAN_PORT=30011         # Neuro SAN server port (gRPC)
```

---

*Auto Claims Management System | Iteration 1 MVP | 2026-05-05*
