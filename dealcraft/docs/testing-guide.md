# DealCraft — Testing Guide
> File: docs/testing-guide.md
> Version: v0.1.0
> Last Updated: 2026-03-26

---

## 1. Pre-requisites Before Testing

Ensure the following are complete before running any test:

- [ ] Claude API key received and added to `.env` file
- [ ] `llm_config.hocon` updated to use `anthropic` / `claude-sonnet-4-6`
- [ ] All `.hocon` agent files are saved in `agents/` folder
- [ ] All prompt `.md` files are saved in `prompts/` folder
- [ ] `dealcraft-network.hocon` is saved in `networks/` folder
- [ ] Neuro-SAN Studio server is running (`python -m run`)
- [ ] Browser is open at `http://localhost:4173/`

---

## 2. Test Scenarios

---

### Test 1 — Client Name Only (Smoke Test)
**Purpose:** Verify the basic pipeline works end to end
**Input:**
```
Research NorthBridge Bank PLC and prepare a BD package.
```
**Expected Flow:**
1. `orchestrator-agent` receives input
2. Calls `client-research-agent` → Client Intelligence Brief
3. Calls `competitive-intel-agent` → Competitive Positioning Sheet
4. Calls `proposal-writer-agent` → Proposal Draft
5. Calls `report-assembler-agent` → Final BD Package

**Expected Output:** Complete BD Package with 4 documents
**Skip:** `rfp-analyzer-agent` (no RFP provided)

---

### Test 2 — RFP Document Input
**Purpose:** Verify RFP analysis is triggered correctly
**Input:**
```
Analyze the following RFP and prepare a complete BD package:
[paste full content of samples/sample-rfp.txt here]
```
**Expected Flow:**
1. `orchestrator-agent` extracts client name from RFP
2. Calls `client-research-agent` → Client Intelligence Brief
3. Calls `rfp-analyzer-agent` → RFP Analysis Summary
4. Calls `competitive-intel-agent` → Competitive Positioning Sheet
5. Calls `proposal-writer-agent` → Proposal Draft
6. Calls `report-assembler-agent` → Final BD Package

**Expected Output:** Complete BD Package with all 5 documents

---

### Test 3 — Client Name + RFP (Full Pipeline)
**Purpose:** Test complete pipeline with both inputs
**Input:**
```
Client: NorthBridge Bank PLC

RFP Document:
[paste full content of samples/sample-rfp.txt here]

Prepare a complete DealCraft BD Package.
```
**Expected Flow:** All 6 agents called in sequence
**Expected Output:** Most comprehensive BD Package

---

## 3. What to Check in Each Output

| Document | What to Verify |
|----------|---------------|
| Client Intelligence Brief | Company facts are accurate, Key Takeaways are relevant |
| RFP Analysis Summary | All 9 sections covered, Win Themes are specific |
| Competitive Positioning Sheet | 3–5 competitors identified, differentiators are concrete |
| Proposal Draft | All 8 sections present, no generic filler, placeholders clearly marked |
| BD Package | All documents assembled, Checklist is actionable, Package Summary is sharp |

---

## 4. Known Limitations (v0.1.0)

- Agent does not browse the internet — all client research is based on LLM training data
- No document upload support yet — RFP must be pasted as text
- Output is text-based — no PDF/DOCX export in this version
- Competitive intel is based on general market knowledge, not real-time data

---

## 5. How to Log Issues

When you find a problem during testing, document it as follows:

```
Issue #: [Number]
Test Scenario: [Test 1 / 2 / 3]
Agent: [Which agent produced the issue]
Input Used: [Brief description]
Expected Output: [What should have happened]
Actual Output: [What actually happened]
Severity: High / Medium / Low
Notes: [Any additional context]
```

Save issues in: `tests/test-scenarios.md`

---

## 6. Success Criteria for v0.1.0

DealCraft v0.1.0 is considered demo-ready when:

- [ ] All 3 test scenarios complete without errors
- [ ] Full BD Package is produced in under 5 minutes
- [ ] Output quality is good enough for a management demo
- [ ] All 5 documents are present in the final package
- [ ] No hallucinated facts in Client Intelligence Brief