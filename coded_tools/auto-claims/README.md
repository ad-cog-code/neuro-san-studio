# Auto Claims AI Agent Network — Neuro SAN Integration Guide

**Project**: Auto Claims Management System  
**Port**: 6001 (Flask app) | 30011 (Neuro SAN gRPC, configurable)  
**Registry**: `registries/auto-claims/auto-claims.hocon`  
**Client**: `services/neuro_san_client.py` (in Flask project)  
**Pattern**: Async 202 dispatch (AppMagic Learning #21) + VALID_AGENTS frozenset (Learning #25)  
**Version**: 1.2 | **Date**: 2026-05-06

---

## Overview

The Auto Claims agent network implements **7 specialist AI agents** coordinated by a single
top-level orchestrator (`claims_orchestrator`). All agents are defined in a single HOCON file
per AppMagic Learning #25.

The Flask application communicates with the agent network via:
1. `POST /adjuster/api/agent/invoke` → returns `{"job_id": "...", "status": "pending"}` (202)
2. `GET /adjuster/api/agent/status/<job_id>` → returns current job state
3. `services/neuro_san_client.py` dispatches to `claims_orchestrator` via `StreamingClient`
4. The orchestrator routes to the correct leaf agent via the `request_type` field
5. Background thread writes result to `agent_jobs` DB table
6. Frontend JS (`static/js/agent-poll.js`) polls every 5 seconds

---

## Agent Inventory

| Agent | Type | User Story | Workbench Tab | request_type |
|-------|------|-----------|---------------|--------------|
| `claims_orchestrator` | top | — | — | (router) |
| `fnol_triage_agent` | leaf | US-1001 | Overview | `fnol_triage` |
| `coverage_agent` | leaf | US-1003 | Policy | `coverage_verification` |
| `settlement_calculator_agent` | leaf | US-1007 | Settlement | `settlement_calculation` |
| `liability_agent` | leaf | US-1004 | Investigation | `liability_assessment` |
| `total_loss_agent` | leaf | US-1005 | Estimation | `total_loss_evaluation` |
| `fraud_detection_agent` | leaf | US-1013 | Investigation | `fraud_detection` |
| `subrogation_agent` | leaf | Sprint 2 | Settlement | `subrogation_evaluation` |

---

## Starting the Neuro SAN Server

```bash
# From the neuro-san-studio directory:
python -m neuro_san.run_server \
  --registry registries/auto-claims/auto-claims.hocon

# Or using the CLI tool:
neuro-san-service --manifest registries/auto-claims/auto-claims.hocon

# Default gRPC port: 30011
```

Configure the Flask app connection via environment variables in `.env`:
```
NEURO_SAN_HOST=localhost
NEURO_SAN_PORT=30011
```

---

## VALID_AGENTS Frozenset

The Flask service enforces agent name validation before any network call:

```python
# services/neuro_san_client.py
VALID_AGENTS = frozenset({
    "fnol_triage_agent",           # MANDATORY — US-1001 FNOL triage
    "coverage_agent",              # MANDATORY — US-1003 coverage verification
    "settlement_calculator_agent", # MANDATORY — US-1007 settlement calculation
    "liability_agent",             # OPTIONAL  — US-1004 enhancement
    "total_loss_agent",            # OPTIONAL  — US-1005 enhancement
    "fraud_detection_agent",       # OPTIONAL  — US-1013 enhancement
    "subrogation_agent",           # OPTIONAL  — Sprint 2
})
```

Any call with an agent name NOT in this frozenset raises `ValueError` → HTTP 400.

---

## Orchestrator Routing

The `claims_orchestrator` receives all requests from the Flask app. It reads the
`request_type` field and routes to the correct leaf agent:

| request_type | Routes to |
|-------------|-----------|
| `fnol_triage` | `fnol_triage_agent` |
| `coverage_verification` | `coverage_agent` |
| `settlement_calculation` | `settlement_calculator_agent` |
| `liability_assessment` | `liability_agent` |
| `total_loss_evaluation` | `total_loss_agent` |
| `fraud_detection` | `fraud_detection_agent` |
| `subrogation_evaluation` | `subrogation_agent` |

---

## Async Dispatch Pattern (Learning #21)

```
HTTP Request (Flask)                     Background Thread
─────────────────                        ─────────────────
POST /adjuster/api/agent/invoke
  ↓
validate agent (VALID_AGENTS)
write 'pending' to agent_jobs DB ──────→ daemon thread: _run_agent_async()
return 202 + job_id                        _invoke_live_neuro_san()
                                             → StreamingClient
Client polls (every 5s)                      → claims_orchestrator
GET /api/agent/status/<job_id>               → leaf agent
  ← {status: 'done', result: {...}}       write 'done' + result to DB
```

**Critical rule (Learning #21)**: DB state is written to `agent_jobs` table BEFORE
the background thread is started. This ensures the job record always exists when the
client polls, even if the poll happens before the thread begins running.

---

## Stub Fallback

When the Neuro SAN server is unavailable (e.g. in development/test):
- `ImportError` (neuro_san not installed) → automatic stub fallback
- Any connection/runtime exception → automatic stub fallback
- Stub responses include `"_stub": true` for UI display

The stubs are deterministic and test-compatible. All 35 unit tests in
`tests/test_neuro_san_client.py` run without a live Neuro SAN server.

---

## DB Schema — agent_jobs Table

```sql
CREATE TABLE agent_jobs (
    job_id       TEXT PRIMARY KEY,
    claim_id     INTEGER,
    agent_name   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK(status IN ('pending','running','done','error')),
    input_data   TEXT NOT NULL DEFAULT '{}',
    result_data  TEXT DEFAULT NULL,
    error_detail TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## Agent Prompt Files

Detailed prompt specifications for each agent are in this directory:

| File | Agent |
|------|-------|
| `prompts/fnol-triage-agent.md` | `fnol_triage_agent` |
| `prompts/coverage-agent.md` | `coverage_agent` |
| `prompts/settlement-calculator-agent.md` | `settlement_calculator_agent` |
| `prompts/optional-agents.md` | `liability_agent`, `total_loss_agent`, `fraud_detection_agent`, `subrogation_agent` |

---

## Testing

```bash
# Run all Neuro SAN client tests (no live server needed):
pytest tests/test_neuro_san_client.py -v

# Expected: 35 tests, all passing
# Test categories:
#   - VALID_AGENTS frozenset (5 tests)
#   - Async dispatch / 202 pattern (5 tests)
#   - Stub: fnol_triage_agent (4 tests)
#   - Stub: coverage_agent (3 tests)
#   - Stub: settlement_calculator_agent (5 tests)
#   - Stub: optional agents (8 tests)
#   - HTTP endpoint tests (5 tests)
```

---

## Production Checklist

- [ ] Neuro SAN server running at `NEURO_SAN_HOST:NEURO_SAN_PORT`
- [ ] `registries/auto-claims/auto-claims.hocon` loaded by Neuro SAN server
- [ ] `neuro-san >= 0.2` installed in Flask app environment
- [ ] `NEURO_SAN_HOST` and `NEURO_SAN_PORT` set in Flask `.env`
- [ ] All 35 unit tests passing
- [ ] Live agent call verified: POST `/adjuster/api/agent/invoke`
      → result includes `"_stub": false`
- [ ] Stub fallback verified: stop neuro-san server → POST invoke
      → result includes `"_stub": true`

---

*Auto Claims Agent Network | Neuro SAN Integration | 2026-05-06*
