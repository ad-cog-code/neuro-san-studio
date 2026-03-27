# DealCraft — Agent Guide
> File: docs/agent-guide.md
> Version: v0.1.0
> Last Updated: 2026-03-26

---

## 1. Introduction

This guide is the definitive reference for every agent in DealCraft. It covers what each agent does, how to configure it, how to tune its behaviour, and how to troubleshoot it.

Use this guide when:
- Onboarding a new team member to DealCraft
- Modifying an agent's behaviour
- Debugging an agent's output
- Planning new agents for future versions

---

## 2. Agent Quick Reference

| Agent | File | Type | Calls | Called By |
|-------|------|------|-------|-----------|
| `orchestrator-agent` | `agents/orchestrator-agent.hocon` | Hub | All agents | User |
| `client-research-agent` | `agents/client-research-agent.hocon` | Leaf | None | Orchestrator |
| `rfp-analyzer-agent` | `agents/rfp-analyzer-agent.hocon` | Leaf | None | Orchestrator |
| `competitive-intel-agent` | `agents/competitive-intel-agent.hocon` | Leaf | None | Orchestrator |
| `proposal-writer-agent` | `agents/proposal-writer-agent.hocon` | Leaf | None | Orchestrator |
| `report-assembler-agent` | `agents/report-assembler-agent.hocon` | Assembler | None | Orchestrator |

---

## 3. Agent Profiles

---

### 3.1 Orchestrator Agent

| Property | Value |
|----------|-------|
| **File** | `agents/orchestrator-agent.hocon` |
| **Prompt** | `prompts/orchestrator-prompt.md` |
| **Type** | Hub Agent |
| **Version** | v0.1.0 |

**What it does:**
The entry point of DealCraft. Receives the user's input, determines what inputs are available (client name, RFP, or both), and delegates tasks to the right specialist agents in the correct sequence. It never performs research or writing itself.

**Input it expects:**
```
Client name: [name]
RFP Document: [text] (optional)
```

**Output it produces:**
A status summary confirming which agents ran and directing the user to the final BD Package.

**Sequence it follows:**
1. `client-research-agent` — always first
2. `rfp-analyzer-agent` — only if RFP is provided
3. `competitive-intel-agent` — after client research
4. `proposal-writer-agent` — after all research agents
5. `report-assembler-agent` — always last

**How to tune it:**
- To change the workflow sequence → edit `prompts/orchestrator-prompt.md`
- To add a new agent to the pipeline → add it to `tools` in `agents/orchestrator-agent.hocon` and update the prompt

**Common issues:**
| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Skips an agent | Input not clearly provided | Make input more explicit |
| Wrong sequence | Prompt instruction unclear | Strengthen sequence rules in prompt |
| Doesn't call assembler | Earlier agent failed | Check logs for upstream agent error |

---

### 3.2 Client Research Agent

| Property | Value |
|----------|-------|
| **File** | `agents/client-research-agent.hocon` |
| **Prompt** | `prompts/client-research-prompt.md` |
| **Type** | Leaf Agent |
| **Version** | v0.1.0 |

**What it does:**
Researches the given client company using the LLM's knowledge base and produces a structured Client Intelligence Brief covering 6 areas: company overview, strategic priorities, pain points, recent news, technology landscape, and Cognizant relationship.

**Input it expects:**
```
Client/company name
Optionally: industry, geography, deal context
```

**Output it produces:**
A structured **Client Intelligence Brief** with 6 sections and 3–5 Key Takeaways for the BD team.

**How to tune it:**
- To add more research areas → add sections to `prompts/client-research-prompt.md`
- To change output format → edit the Output Format section in the prompt
- To improve accuracy for a specific industry → add industry context to the prompt

**Limitations:**
- Uses LLM training data only — information may not reflect the latest news
- For real-time research, web search integration is planned for v0.2.0

**Common issues:**
| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Generic or shallow output | Company not well known | Provide more context in the input |
| Missing Key Takeaways | Prompt not followed | Reinforce rules in prompt |
| Outdated information | LLM knowledge cutoff | Accept limitation in v0.1.0, use web search in v0.2.0 |

---

### 3.3 RFP Analyzer Agent

| Property | Value |
|----------|-------|
| **File** | `agents/rfp-analyzer-agent.hocon` |
| **Prompt** | `prompts/rfp-analyzer-prompt.md` |
| **Type** | Leaf Agent |
| **Version** | v0.1.0 |

**What it does:**
Reads the full RFP or RFI document text and extracts structured intelligence across 7 areas: RFP summary, scope of work, key requirements, evaluation criteria, timeline, Cognizant fit analysis, and red flags. Produces Top 5 Win Themes.

**Input it expects:**
```
Full RFP or RFI document text (pasted as plain text)
Optionally: client name or deal context
```

**Output it produces:**
A structured **RFP Analysis Summary** with 7 sections and Top 5 Win Themes.

**How to tune it:**
- To emphasize specific evaluation criteria → highlight them in the prompt
- To customize fit analysis for Cognizant capabilities → add capability context to the prompt
- To add new sections → extend the Output Format in the prompt

**Common issues:**
| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Incomplete extraction | RFP text was truncated | Ensure full RFP text is pasted |
| Generic Win Themes | RFP lacked specific criteria | Acceptable — flag as gap in output |
| Missing fit analysis | No Cognizant context in prompt | Add relevant Cognizant capability hints |

---

### 3.4 Competitive Intel Agent

| Property | Value |
|----------|-------|
| **File** | `agents/competitive-intel-agent.hocon` |
| **Prompt** | `prompts/competitive-intel-prompt.md` |
| **Type** | Leaf Agent |
| **Version** | v0.1.0 |

**What it does:**
Identifies the 3–5 most likely competitors for the deal based on client industry, deal size, service type, and geography. Profiles each competitor and produces a Competitive Positioning Sheet with clear differentiation strategies for Cognizant.

**Input it expects:**
```
Client Intelligence Brief (from client-research-agent)
RFP Analysis Summary (from rfp-analyzer-agent, optional)
Deal domain / service area
```

**Output it produces:**
A structured **Competitive Positioning Sheet** with 5 sections and Recommended Differentiators for the proposal.

**How to tune it:**
- To focus on specific competitors → name them in the input context
- To emphasize specific Cognizant strengths → add them to the prompt
- To cover a niche market → add market context to the prompt

**Common issues:**
| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Wrong competitors identified | Deal context unclear | Provide more specific deal context |
| Weak differentiators | Generic Cognizant positioning | Add specific Cognizant capabilities to prompt |
| Missing risk assessment | Prompt not followed | Reinforce rules in prompt |

---

### 3.5 Proposal Writer Agent

| Property | Value |
|----------|-------|
| **File** | `agents/proposal-writer-agent.hocon` |
| **Prompt** | `prompts/proposal-writer-prompt.md` |
| **Type** | Leaf Agent |
| **Version** | v0.1.0 |

**What it does:**
The most complex agent in DealCraft. Takes all three research outputs (client brief, RFP summary, competitive sheet) and synthesizes them into a professional, tailored proposal draft covering 8 sections from cover page to next steps.

**Input it expects:**
```
Client Intelligence Brief
RFP Analysis Summary (optional)
Competitive Positioning Sheet
```

**Output it produces:**
A complete **Proposal Draft** with 8 sections and Writer's Notes for the BD team.

**How to tune it:**
- To change proposal structure → edit the sections in the prompt
- To adjust tone → edit the Tone & Style rules in the prompt
- To add company boilerplate → add standard Cognizant content to the prompt
- To improve tailoring quality → ensure upstream agents produce richer outputs

**Common issues:**
| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Generic proposal content | Upstream agents produced thin output | Improve client/RFP inputs |
| Missing sections | Token limit reached | Reduce other section lengths |
| Too many placeholders | Missing information | Acceptable in v0.1.0 — fill manually |

---

### 3.6 Report Assembler Agent

| Property | Value |
|----------|-------|
| **File** | `agents/report-assembler-agent.hocon` |
| **Prompt** | `prompts/report-assembler-prompt.md` |
| **Type** | Assembler Agent |
| **Version** | v0.1.0 |

**What it does:**
The final agent in the pipeline. Takes all four documents (client brief, RFP summary, competitive sheet, proposal draft), writes a Package Summary, assembles everything into one clean BD Package, and adds a BD Team Checklist with action items and quality flags.

**Input it expects:**
```
Client Intelligence Brief
RFP Analysis Summary (optional)
Competitive Positioning Sheet
Proposal Draft
```

**Output it produces:**
The complete **DealCraft BD Package** — a single, presentation-ready document.

**How to tune it:**
- To customize the Package Summary format → edit the prompt's output template
- To add/remove checklist items → edit the BD Team Checklist section in the prompt
- To add quality checks → add rules to the prompt's quality check section

**Common issues:**
| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Missing documents in package | Upstream agent failed | Check orchestrator logs |
| Weak Package Summary | Inputs were thin | Improve upstream agent outputs |
| Checklist not populated | Agent skipped it | Reinforce rules in prompt |

---

## 4. How to Add a New Agent

Follow these steps to add a new agent to DealCraft:

### Step 1 — Create the prompt file
```
prompts/[function]-prompt.md
```
Define: Role, Input, Processing Instructions, Output Format, Rules.

### Step 2 — Create the HOCON definition file
```
agents/[function]-agent.hocon
```
Reference the prompt file and set `"tools": []` if it's a leaf agent.

### Step 3 — Register the agent in the orchestrator
In `agents/orchestrator-agent.hocon`, add the new agent to the `tools` array.

### Step 4 — Update the orchestrator prompt
In `prompts/orchestrator-prompt.md`, add the new agent to the agent table and update the workflow sequence.

### Step 5 — Update the network file
In `networks/dealcraft-network.hocon`, add the new agent reference.

### Step 6 — Document it
Add the new agent's profile to this guide and update the architecture diagram in `docs/architecture.md`.

### Step 7 — Update changelog
Add an entry in `docs/changelog.md` under `[Unreleased]`.

---

## 5. Prompt Tuning Tips

| Goal | Technique |
|------|-----------|
| More structured output | Add explicit output templates with section headers |
| More concise output | Add word/section length limits to the prompt |
| More tailored content | Add client/deal specific context to the input |
| Better quality control | Add a Rules section with numbered, specific rules |
| Consistent formatting | Use code blocks in the prompt to show exact output format |
| Reduce hallucination | Add explicit rules: "Never fabricate. State 'Not available' if unknown." |

---

## 6. Versioning Agents

When making significant changes to an agent's prompt or config:

1. Update the `Version` field in the prompt file header
2. Note what changed and why in a comment at the top of the file
3. Log the change in `docs/changelog.md`
4. Test with all 3 scenarios in `docs/testing-guide.md` before committing

---

*DealCraft Agent Guide v0.1.0 — Last Updated: 2026-03-26*