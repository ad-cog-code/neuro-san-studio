# DealCraft — Changelog
> File: docs/changelog.md
> Format: [Semantic Versioning](https://semver.org/)
> Convention: Keep a Changelog (https://keepachangelog.com)

---

All notable changes to DealCraft will be documented in this file.

---

## [Unreleased]
> Changes staged for the next version

### Planned
- Real-time web search integration for client research
- PDF/DOCX document upload support
- Structured JSON output from all agents
- PDF export of final BD Package

---

## [0.1.0] — 2026-03-26
> MVP — First working version of DealCraft

### Added
- Initial project structure with kebab-case naming convention
- `orchestrator-agent` — central coordinator of the BD pipeline
- `client-research-agent` — client intelligence and profiling
- `rfp-analyzer-agent` — RFP/RFI document analysis
- `competitive-intel-agent` — competitor analysis and positioning
- `proposal-writer-agent` — tailored proposal drafting
- `report-assembler-agent` — final BD package assembly
- `dealcraft-network.hocon` — agent network topology definition
- System prompts for all 6 agents in `prompts/` folder
- Sample RFP document — NorthBridge Bank Digital Transformation (Banking & FS)
- Sample client brief for smoke testing
- Testing guide with 3 structured test scenarios
- Product blueprint and architecture documentation
- README.md with setup, usage, and roadmap
- `.gitignore` configured to protect `.env` and `outputs/`

### Architecture
- Multi-agent sequential pipeline
- Orchestrator → Specialist Agents → Report Assembler
- Powered by Claude (Anthropic) via Neuro-SAN Studio
- LLM: `claude-sonnet-4-6`

---

## How to Update This File

When making changes to DealCraft, add an entry under `[Unreleased]` using these categories:

| Category | When to use |
|----------|-------------|
| `Added` | New features or agents |
| `Changed` | Changes to existing functionality |
| `Fixed` | Bug fixes |
| `Removed` | Removed features |
| `Security` | Security-related changes |

When releasing a new version, move `[Unreleased]` items under a new version heading:
```
## [0.2.0] — YYYY-MM-DD
```