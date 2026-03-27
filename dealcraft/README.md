# DealCraft
### AI-Powered BD Command Center

> Transform a client name or RFP document into a complete, presentation-ready BD package — in minutes, not days.

Built on **Neuro-SAN Studio** | Powered by **Claude (Anthropic)** | By **Cognizant AI Lab**

---

## What is DealCraft?

DealCraft is a multi-agent AI system designed for Business Development and Pre-Sales teams. It automates the most time-consuming parts of the BD lifecycle — client research, RFP analysis, competitive positioning, and proposal writing — using a network of specialized AI agents that collaborate to produce a complete BD package autonomously.

---

## The Problem It Solves

| Challenge | Impact |
|-----------|--------|
| Manual client research | 4–6 hours per opportunity |
| RFP analysis and extraction | 3–5 hours per document |
| Competitive positioning | Ad hoc, inconsistent |
| Proposal first draft | 1–2 days of effort |
| **Total time to first draft** | **2–3 days** |

DealCraft reduces this to **under 30 minutes.**

---

## How It Works

DealCraft uses a network of 6 specialized AI agents, each responsible for one part of the BD workflow:

```
INPUT: Client Name and/or RFP Document
              ↓
    ┌─────────────────────┐
    │  orchestrator-agent │  ← Coordinates the entire workflow
    └─────────────────────┘
       ↓       ↓       ↓       ↓       ↓
  [client] [rfp]  [comp]  [prop]
  research  analy  etitive  osal
  -agent    zer    -intel   -writer
            agent  -agent   -agent
       ↓       ↓       ↓       ↓
    ┌─────────────────────────┐
    │  report-assembler-agent │  ← Produces final BD Package
    └─────────────────────────┘
              ↓
OUTPUT: Complete BD Package
```

### Agent Responsibilities

| Agent | Output |
|-------|--------|
| `orchestrator-agent` | Coordinates all agents, manages workflow |
| `client-research-agent` | Client Intelligence Brief |
| `rfp-analyzer-agent` | RFP Analysis Summary |
| `competitive-intel-agent` | Competitive Positioning Sheet |
| `proposal-writer-agent` | Tailored Proposal Draft |
| `report-assembler-agent` | Final assembled BD Package |

---

## Output — The DealCraft BD Package

Every run produces a complete BD Package containing:

- **Client Intelligence Brief** — Company overview, strategic priorities, pain points, tech landscape
- **RFP Analysis Summary** — Scope, requirements, evaluation criteria, fit analysis, win themes
- **Competitive Positioning Sheet** — Competitor profiles, Cognizant differentiators, positioning strategy
- **Proposal Draft** — Executive summary, solution approach, why Cognizant, value outcomes, next steps
- **BD Team Checklist** — Action items, gaps to fill, quality flags

---

## Project Structure

```
dealcraft/
├── agents/                         # Agent definitions (.hocon)
│   ├── orchestrator-agent.hocon
│   ├── client-research-agent.hocon
│   ├── rfp-analyzer-agent.hocon
│   ├── competitive-intel-agent.hocon
│   ├── proposal-writer-agent.hocon
│   └── report-assembler-agent.hocon
├── networks/                       # Agent network topology
│   └── dealcraft-network.hocon
├── prompts/                        # System prompts for each agent
│   ├── orchestrator-prompt.md
│   ├── client-research-prompt.md
│   ├── rfp-analyzer-prompt.md
│   ├── competitive-intel-prompt.md
│   ├── proposal-writer-prompt.md
│   └── report-assembler-prompt.md
├── samples/                        # Sample inputs for testing
│   ├── sample-rfp.txt
│   └── sample-client-brief.txt
├── outputs/                        # Generated BD packages (gitignored)
├── docs/                           # Documentation
│   ├── architecture.md
│   ├── agent-guide.md
│   ├── testing-guide.md
│   └── changelog.md
├── tests/                          # Test cases and results
│   └── test-scenarios.md
├── .env                            # API keys — never commit this
├── .gitignore
└── README.md
```

---

## Prerequisites

- Python 3.13.x
- Git
- [Neuro-SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio) installed and running
- A Claude (Anthropic) API key

---

## Getting Started

### Step 1 — Clone and set up Neuro-SAN Studio
Follow the [Neuro-SAN Studio setup guide](https://github.com/cognizant-ai-lab/neuro-san-studio) to get the base platform running.

### Step 2 — Place DealCraft in your Neuro-SAN Studio directory
```
neuro-san-studio/
└── dealcraft/        ← this project goes here
```

### Step 3 — Configure your API key
Add your Claude API key to the `.env` file in the root of `neuro-san-studio`:
```
ANTHROPIC_API_KEY="your-api-key-here"
```

### Step 4 — Update LLM config
In `registries/llm_config.hocon`, set:
```hocon
{
    "llm_config": {
        "class": "anthropic",
        "model_name": "claude-sonnet-4-6",
    }
}
```

### Step 5 — Launch Neuro-SAN Studio
```powershell
python -m run
```

### Step 6 — Open DealCraft
Navigate to `http://localhost:5171/` and select the `dealcraft-network` from the left panel.

---

## Running Your First Test

**Quick smoke test — paste this into the chat:**
```
Research NorthBridge Bank PLC and prepare a BD package.
```

**Full pipeline test — paste the sample RFP:**
```
Analyze the following RFP and prepare a complete BD package:
[paste content of samples/sample-rfp.txt]
```

For detailed test instructions, see `docs/testing-guide.md`.

---

## Versioning

| Version | Status | Description |
|---------|--------|-------------|
| v0.1.0 | 🔄 In Progress | MVP — core agents, text output |
| v0.2.0 | 📋 Planned | Full agent network, structured output |
| v1.0.0 | 🔮 Roadmap | Web search, document upload, PDF export |

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files & folders | kebab-case | `client-research-agent.hocon` |
| Agent names | `[function]-agent` | `rfp-analyzer-agent` |
| Prompt files | `[function]-prompt.md` | `orchestrator-prompt.md` |
| Network files | `[product]-network.hocon` | `dealcraft-network.hocon` |
| Versions | `v[MAJOR].[MINOR].[PATCH]` | `v0.1.0` |

---

## Roadmap

### v0.2.0
- [ ] Competitive intel with real-time web search
- [ ] Structured JSON output from each agent
- [ ] Improved proposal formatting

### v1.0.0
- [ ] PDF/DOCX document upload support
- [ ] Formatted PDF export of BD Package
- [ ] UI enhancements
- [ ] Performance benchmarking

---

## Built With

- [Neuro-SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio) — Multi-agent AI framework
- [Claude by Anthropic](https://www.anthropic.com) — Large Language Model
- Python 3.13

---

## Team

| Role | Name |
|------|------|
| Product Owner & Developer | [Your Name] |
| Organization | Cognizant Technology Solutions |

---

## License

Internal use only — Cognizant Technology Solutions
Not for distribution outside the organization.

---

*DealCraft v0.1.0 — AI-Powered BD Command Center*
*Built on Neuro-SAN Studio by Cognizant AI Lab*