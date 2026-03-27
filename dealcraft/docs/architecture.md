# DealCraft — Architecture Document
> File: docs/architecture.md
> Version: v0.1.0
> Last Updated: 2026-03-26

---

## 1. Overview

DealCraft is a **multi-agent AI system** built on Neuro-SAN Studio. It follows a **sequential orchestration pattern** where a central orchestrator agent delegates tasks to specialist agents, collects their outputs, and passes them downstream until a final assembled output is produced.

The system is designed to be:
- **Modular** — each agent is independent and replaceable
- **Extensible** — new agents can be added without changing existing ones
- **Transparent** — every agent has a clearly defined input, output, and responsibility
- **Production-ready** — structured for evolution from MVP to full product

---

## 2. Architecture Pattern

DealCraft uses the **Hub-and-Spoke with Sequential Pipeline** pattern:

```
                        ┌─────────────────────────┐
                        │                         │
         INPUT ────────▶│    orchestrator-agent   │◀──── User
                        │    (Hub / Coordinator)  │
                        └─────────────┬───────────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
              ▼                       ▼                        ▼
  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐
  │ client-research   │  │  rfp-analyzer     │  │  competitive-intel    │
  │ -agent            │  │  -agent           │  │  -agent               │
  │                   │  │                   │  │                       │
  │ Output:           │  │ Output:           │  │ Output:               │
  │ Client Brief      │  │ RFP Summary       │  │ Competitive Sheet     │
  └────────┬──────────┘  └────────┬──────────┘  └──────────┬────────────┘
           │                      │                         │
           └──────────────────────┼─────────────────────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │   proposal-writer      │
                     │   -agent               │
                     │                        │
                     │   Output:              │
                     │   Proposal Draft       │
                     └────────────┬───────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │   report-assembler     │
                     │   -agent               │
                     │                        │
                     │   Output:              │
                     │   Final BD Package     │
                     └────────────────────────┘
                                  │
                                  ▼
                              OUTPUT
                          Complete BD Package
```

---

## 3. Agent Topology

### 3.1 Agent Types

| Type | Description | Agents |
|------|-------------|--------|
| **Hub Agent** | Coordinates workflow, delegates tasks, never executes domain tasks itself | `orchestrator-agent` |
| **Leaf Agent** | Executes a specific domain task, takes input, returns structured output | All other agents |
| **Assembler Agent** | Special leaf agent — takes multiple inputs, produces one unified output | `report-assembler-agent` |

### 3.2 Agent Communication Flow

```
Step 1:  User Input
              ↓
Step 2:  orchestrator-agent receives input
              ↓
Step 3:  orchestrator-agent calls client-research-agent
              ↓ (waits for output)
Step 4:  orchestrator-agent calls rfp-analyzer-agent (if RFP provided)
              ↓ (waits for output)
Step 5:  orchestrator-agent calls competitive-intel-agent
              ↓ (waits for output)
Step 6:  orchestrator-agent calls proposal-writer-agent
         with outputs from Steps 3, 4, 5
              ↓ (waits for output)
Step 7:  orchestrator-agent calls report-assembler-agent
         with all outputs from Steps 3, 4, 5, 6
              ↓ (waits for output)
Step 8:  Final BD Package returned to user
```

### 3.3 Data Flow Diagram

```
[User Input]
     │
     ├── client_name ─────────────────▶ client-research-agent
     │                                          │
     │                                          │ Client Intelligence Brief
     │                                          ▼
     ├── rfp_document ────────────────▶ rfp-analyzer-agent
     │                                          │
     │                                          │ RFP Analysis Summary
     │                                          ▼
     │                               competitive-intel-agent
     │                              (uses client brief + RFP summary)
     │                                          │
     │                                          │ Competitive Positioning Sheet
     │                                          ▼
     │                                 proposal-writer-agent
     │                             (uses all 3 outputs above)
     │                                          │
     │                                          │ Proposal Draft
     │                                          ▼
     │                                report-assembler-agent
     │                              (assembles all 4 outputs)
     │                                          │
     └──────────────────────────────────────────▼
                                       Final BD Package
```

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | Neuro-SAN Studio | Multi-agent orchestration |
| LLM | Claude Sonnet (Anthropic) | Language model for all agents |
| Language | Python 3.13 | Runtime environment |
| Config Format | HOCON | Agent and network definitions |
| Prompt Format | Markdown (.md) | Agent system prompts |
| API | Anthropic Claude API | LLM access |
| Environment | Python venv | Dependency isolation |

---

## 5. File Architecture

### 5.1 Configuration Layer (`agents/` + `networks/`)
- Defines **what** each agent is and **how** agents connect
- Written in HOCON format
- References prompt files and LLM config
- Network file ties all agents together into a runnable pipeline

### 5.2 Prompt Layer (`prompts/`)
- Defines **how** each agent thinks and behaves
- Written in Markdown for readability and easy editing
- Each prompt covers: role, input format, processing instructions, output format, rules
- Prompts are the primary lever for tuning agent quality

### 5.3 Sample Layer (`samples/`)
- Provides realistic test inputs
- Used for dry runs and demo preparation
- Should be updated with real inputs before production use

### 5.4 Output Layer (`outputs/`)
- Stores generated BD packages from test runs
- Gitignored — never committed to source control
- Useful for comparing output quality across versions

---

## 6. Design Decisions

### 6.1 Why Sequential and Not Parallel?
Each agent's output feeds into the next agent's input. For example, `proposal-writer-agent` needs the client brief, RFP summary, and competitive sheet before it can write. True parallelism is possible for Steps 3–5 (research agents) but sequential execution was chosen for v0.1.0 for simplicity and debuggability.

**Future consideration:** Parallelize Steps 3, 4, and 5 in v0.2.0 for faster execution.

### 6.2 Why Separate Prompt Files?
Keeping prompts in `.md` files (rather than inline in HOCON) makes them:
- Easier to read and edit without touching config files
- Version-controllable independently
- Reusable across different network configurations

### 6.3 Why an Assembler Agent?
Rather than having the orchestrator compile the final output, a dedicated `report-assembler-agent` handles this. This keeps the orchestrator's role pure (coordination only) and allows the assembler to apply its own quality checks, formatting logic, and checklist generation.

---

## 7. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| API key exposure | Stored in `.env`, never committed (in `.gitignore`) |
| Output data sensitivity | `outputs/` folder is gitignored |
| Client data in prompts | Sample data only in repo — real data never committed |
| LLM data privacy | Use Anthropic enterprise API with data privacy agreements |

---

## 8. Known Limitations (v0.1.0)

| Limitation | Impact | Planned Fix |
|------------|--------|-------------|
| No internet access | Client research uses LLM training data only | Web search in v0.2.0 |
| Text input only | RFP must be pasted as text | Document upload in v1.0.0 |
| Text output only | No formatted PDF/DOCX export | Export feature in v1.0.0 |
| Sequential execution | Slower than parallel | Parallel research agents in v0.2.0 |
| No memory | Each run is stateless | Persistent memory in v1.0.0 |

---

## 9. Future Architecture (v1.0.0 Vision)

```
dealcraft/
├── agents/               # All agent definitions
├── networks/             # Network topology
├── prompts/              # Agent prompts
├── tools/                # Custom tools (web search, doc parser)  ← NEW
├── memory/               # Persistent deal history                ← NEW
├── exporters/            # PDF/DOCX export modules                ← NEW
├── api/                  # REST API layer for integration         ← NEW
├── ui/                   # Web UI for non-technical users         ← NEW
├── samples/
├── outputs/
├── docs/
└── tests/
```

---

*DealCraft Architecture v0.1.0 — Last Updated: 2026-03-26*