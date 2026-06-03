# HOCON + Coded Tools — Best Practices for Neuro SAN
## Learnt from BidMagic V2 (May 2026)

This document captures hard-won rules from building the 5-network BidMagic
DealCraft V2 system. Every "Don't" below caused a real bug.

---

## 1  Folder Structure

```
neuro-san-studio/
├── registries/
│   ├── manifest.hocon          ← registers every network
│   ├── llm_config.hocon        ← shared LLM config (include in every HOCON)
│   ├── dealcraft_qualification.hocon
│   ├── dealcraft_research.hocon
│   └── ...
├── coded_tools/
│   ├── bidmagic/               ← shared tools for ALL BidMagic networks
│   │   ├── __init__.py
│   │   ├── _paths.py           ← path resolution + tool_calls.log
│   │   ├── write_file.py       ← WriteFile coded tool
│   │   ├── read_file.py        ← ReadFile coded tool
│   │   └── list_files.py       ← ListFiles coded tool
│   ├── sdlc_pipeline/          ← tools for sdlc_pipeline network only
│   │   └── ...
│   └── ...
└── dealcraft/
    └── prompts/v2/             ← agent instruction markdown files
```

**Rule:** Shared coded tools live in `coded_tools/<project>/`, not inside any
network-specific subfolder. Any network that needs them references them by
fully-qualified class path.

---

## 2  Class Resolution — How Neuro SAN Finds Coded Tools

Neuro SAN resolves a `"class"` field in two phases:

### Phase 1 — Direct fully-qualified import (tried first)
```hocon
"class": "coded_tools.bidmagic.write_file.WriteFile"
```
Python resolves this as:
```python
from coded_tools.bidmagic.write_file import WriteFile
```
This is the **recommended approach**. It is explicit, unambiguous, and works
regardless of which `registries/` subfolder the HOCON lives in.

### Phase 2 — Hierarchical resolution (fallback)
If Phase 1 fails, Neuro SAN prepends the AGENT_TOOL_PATH + network name and
tries progressively shorter prefixes. For a network named `dealcraft_qualification`:
1. `coded_tools.dealcraft_qualification.write_file.WriteFile`
2. `coded_tools.write_file.WriteFile`

Phase 2 only works if the coded tool lives in a folder named **exactly** after
the agent network. For shared tools this is impractical — use Phase 1 always.

---

## 3  Coded Tool Declaration in HOCON

### ✅ DO — full `function` block with description + parameters

```hocon
{
    "name": "write_file",
    "function": {
        "description": "Write content to a file in the deal repository...",
        "parameters": {
            "type": "object",
            "properties": {
                "path":    { "type": "string", "description": "..." },
                "content": { "type": "string", "description": "..." },
                "mode":    { "type": "string", "description": "..." },
                "agent":   { "type": "string", "description": "..." }
            },
            "required": ["path", "content"]
        }
    },
    "class": "coded_tools.bidmagic.write_file.WriteFile"
}
```

### ❌ DON'T — bare class declaration without `function` block

```hocon
{
    "name": "write_file",
    "class": "write_file.WriteFile"      # BROKEN — two problems:
}                                         # 1. No function schema → LLM can't see the tool
                                          # 2. Short class path → Phase 1 fails, Phase 2 fails
```

**Why it breaks:** Without a `function` block the LLM receives no JSON schema
for the tool. The model says "I don't have a write_file tool available" even
though the tool is listed in the network's tools array. The agent answers
directly instead of delegating — you get a 5-second response and 0 files written.

---

## 4  Class Path Rules

| Pattern | Works? | Notes |
|---------|--------|-------|
| `"class": "coded_tools.bidmagic.write_file.WriteFile"` | ✅ Yes | Explicit — always use this |
| `"class": "write_file.WriteFile"` | ❌ No | Module `write_file` not on sys.path |
| `"class": "sdlc_pipeline.write_file.WriteFile"` | ❌ No | `sdlc_pipeline` not a top-level module |
| `"class": "coded_tools.sdlc_pipeline.write_file.WriteFile"` | ✅ Yes | Works if file exists; prefer project-specific tools |

**Rule:** Always start the class path with `coded_tools.` — that package IS on
sys.path when Neuro SAN runs from `neuro-san-studio/`.

---

## 5  `project_folder` in `sly_data` — The Path Root Contract

Every coded tool resolves file paths **relative to `sly_data["project_folder"]`**.
The calling application (BidMagic) sets this in `ai_bridge._build_sly_data()`.

### ✅ DO — set `project_folder` to the same root used to build paths in messages

```python
# ai_bridge.py
sly_data = {
    "project_folder": BASE_DIR,   # = C:/my-projects/bidmagic
    ...
}

# The message to the orchestrator uses the same root:
rel_path = os.path.relpath(ctx_idx_path, BASE_DIR)
# → "repository/5_acme/iter_1/01_qualification/_context_index.md"
```

When the orchestrator calls `read_file(path="repository/5_acme/iter_1/01_qualification/_context_index.md")`,
the tool resolves: `BASE_DIR / "repository/5_acme/..."` = correct absolute path.

### ❌ DON'T — set `project_folder` to a deeper path than the paths in the message

```python
sly_data = {
    "project_folder": "C:/my-projects/bidmagic/repository/5_acme",  # WRONG
    ...
}
# The message still has: "repository/5_acme/iter_1/..."
# Tool resolves: <deal_repo>/repository/5_acme/iter_1/... = PATH DOES NOT EXIST
```

**Symptom:** `ReadFile` returns `NOT_FOUND` for the context index. Agents can't
read their instructions and skip writing output files.

---

## 6  Section Numbering in Context Index vs Agent Prompts

### ✅ DO — reference correct section numbers consistently

The `_context_index.md` has 6 sections. Agent prompts must reference them correctly:

| Section | Content |
|---------|---------|
| Section 1 | Deal facts (context.md, intake.md) |
| Section 2 | Client inputs (RFP files) |
| Section 3 | Prior phase outputs |
| Section 4 | Refinement context |
| Section 5 | Global learning library |
| Section 6 | Phase output files (one per agent) |

Agent prompt step line must say **Section 6**, not "Section 7":
```markdown
**Step 4**: Write output to ONLY YOUR OWN path from **Section 6** using write_file.
```

### ❌ DON'T — reference a section number that doesn't exist

```markdown
**Step 4**: Write output to the path in **Section 7** using write_file.
# Section 7 doesn't exist → agent reads Section 6 which says "Write EACH of these files"
# → agent writes ALL 6 files instead of just its own
```

---

## 7  Section 6 Language — "Write EACH" vs "Write ONLY YOURS"

The context index Section 6 is seen by **every sub-agent** that receives
`context_index_content`. The language must be unambiguous about single-file writes.

### ✅ DO — distinguish orchestrator vs individual agent scope

```markdown
SECTION 6 — PHASE OUTPUT FILES (one per agent)
══════════════════════════════════════════════════
ORCHESTRATOR: Delegate each file to the named specialist agent.
INDIVIDUAL AGENTS: Write ONLY your own designated file (one file each).

  bid-qualification.md  →  repository/5_acme/iter_1/01_qualification/bid-qualification.md
  rfp-analysis.md       →  repository/5_acme/iter_1/01_qualification/rfp-analysis.md
  ...

CRITICAL RULE: Each specialist agent writes exactly ONE file — its own designated output.
Do NOT write files that belong to other agents.
```

### ❌ DON'T — use "Write EACH" in a section every agent reads

```markdown
Write EACH of these files using write_file():
  bid-qualification.md  →  ...
  rfp-analysis.md       →  ...
```

**Symptom:** Every agent tries to write all 6 files. You see `rfp-analyzer-agent`
writing `bid-qualification.md`, and `bid-qualification-agent` writing
`service-line-analyzer.md`. Output files exist but contain wrong content.

---

## 8  Orchestrator vs Sub-Agent Tool Scope

The **thin orchestrator** pattern prevents the orchestrator from writing files
directly (which would produce one big file instead of 6 specialist outputs).

### ✅ DO — orchestrator has NO write_file

```hocon
{
    "name": "qualification-orchestrator",
    "tools": [
        "read_file",
        "list_files",
        "bid-qualification-agent",     # ← calls sub-agents, doesn't write itself
        "rfp-analyzer-agent",
        ...
    ]
}
```

### ❌ DON'T — give the orchestrator write_file

```hocon
{
    "name": "qualification-orchestrator",
    "tools": [
        "read_file", "write_file",     # WRONG — orchestrator will write one
        "list_files", ...              # combined file instead of delegating
    ]
}
```

**Symptom (histories=1 bug):** With `write_file` available, the orchestrator
answers the user prompt directly by writing one summary file and returning.
Sub-agents are never called. Duration: ~10 seconds. Files written: 0 out of N.

---

## 9  Sub-Agent Parameter Design

Each sub-agent must declare its parameters explicitly so the orchestrator LLM
knows what to pass.

### ✅ DO — declare `context_index_content` as a required parameter

```hocon
{
    "name": "bid-qualification-agent",
    "function": {
        "description": "Produces Bid Qualification report. Writes to iter_N/phase1-qualification/bid-qualification.md",
        "parameters": {
            "type": "object",
            "properties": {
                "context_index_content": {
                    "type": "string",
                    "description": "Full content of _context_index.md. Section 6 contains the exact output file path for this agent."
                }
            },
            "required": ["context_index_content"]
        }
    },
    "instructions": "dealcraft/prompts/v2/bid-qualification-v2.md",
    "llm_config": ${llm_config},
    "tools": ["read_file", "write_file", "list_files"]
}
```

### ❌ DON'T — omit parameters (orchestrator won't know what to pass)

```hocon
{
    "name": "bid-qualification-agent",
    "function": {
        "description": "Produces Bid Qualification report."
        # no parameters → orchestrator calls with no args → agent has no context
    }
}
```

---

## 10  Coded Tool Implementation Rules

### Python class requirements

```python
from neuro_san.interfaces.coded_tool import CodedTool

class WriteFile(CodedTool):
    """Must implement async_invoke (preferred) or invoke (sync, discouraged)."""

    async def async_invoke(self, args: dict, sly_data: dict) -> str:
        ...
        return "OK: ..."    # Always return a string — this becomes the tool result
```

- **Always return `str`** — Neuro SAN wraps the return value in an `AIMessage`.
- **Never raise** from `async_invoke` — catch all exceptions and return an error string.
- **No constructor arguments** — Neuro SAN instantiates with `ClassName()`.
- **No global state** — tools run in an async multi-threaded environment.
- **Log to `sly_data["project_folder"]/logs/tool_calls.log`** — always best-effort.

### Sandbox rule

Every file path must be validated against `project_folder` before use:

```python
candidate = os.path.abspath(os.path.join(project_folder, relative_path))
if not candidate.startswith(project_folder + os.sep):
    raise ValueError("path escapes project sandbox")
```

Reject absolute paths. Reject `..` traversals.

---

## 11  Chunked Writes — When and How to Split

Agent output files are typically 8–15 KB of Markdown. This fits comfortably in
one `write_file` call. However, very large documents (> 15 KB) should be split
to avoid hitting LLM structured-output token budgets.

### Threshold summary

| File size | Strategy |
|-----------|----------|
| < 8 KB | Single `write_file(mode="write")` call — no split needed |
| 8–15 KB | Single call still fine; tool will not warn |
| > 15 KB | Split into chunks — tool logs `WARN` if exceeded |

### ✅ DO — split at natural section boundaries

```markdown
# In the agent prompt, instruct the agent:
For large output files use two write_file calls, splitting at a ## heading:

  write_file(path=..., content="# Title\n## Section 1 ...\n## Section 2 ...", mode="write")
  write_file(path=..., content="\n## Section 3 ...\n## Section 4 ...", mode="append")
```

```python
# What the tool does on append to an existing file:
open(absolute_path, "a", encoding="utf-8").write(content)
```

The tool handles `mode="append"` on a non-existent file gracefully — it
treats the first append as a create, so agents don't need to check whether
the file exists first.

### ❌ DON'T — split mid-sentence or mid-table

```markdown
# Bad split point — breaks Markdown rendering:
chunk 1: "| Column A | Column B |\n|----------|"
chunk 2: "----------|\n| value    | value    |"
```

Split only at `##` heading boundaries. The reader will always see a complete
Markdown document.

### Practical agent prompt instruction for chunking

Add this to any sub-agent prompt whose output regularly exceeds 15 KB:

```markdown
## Writing Your Output
- Estimate length: if > 15 000 chars, split into two write_file calls.
- Call 1: mode="write"  — write sections 1 through N/2 (stop after a ## heading).
- Call 2: mode="append" — write the remaining sections to the same path.
- Never split mid-table, mid-list, or mid-code-block.
```

---

## 12  Manifest Registration

Every new HOCON must be registered in `registries/manifest.hocon`:

```hocon
# DealCraft V2 — five separate phase networks
"dealcraft_qualification.hocon": true,
"dealcraft_research.hocon":      true,
"dealcraft_solution.hocon":      true,
"dealcraft_commercial.hocon":    true,
"dealcraft_proposal.hocon":      true,
```

For networks that should be served but not shown publicly:
```hocon
"my_support_network.hocon": {
    "serve": true,
    "public": false
}
```

### Reload behaviour — HOCONs vs Coded Tools

| Change type | Reload required? |
|-------------|-----------------|
| Edit a `.hocon` file | **No restart** — Neuro SAN detects file changes and hot-reloads the affected network automatically. Watch `logs/server.log` for `REPLACED network for agent <name>`. |
| Edit a coded tool `.py` file | **Full restart required** — Python modules are imported once at startup. A running server will not pick up `.py` changes. |
| Add a new `.hocon` to manifest | **No restart** — file watcher picks up the new entry. |
| Add a new coded tool class | **Full restart required** — the class cannot be imported until Neuro SAN relaunches. |

> **How to restart:** Kill the process on port 4173 first (NSFlow UI), then restart
> the server: `python -m run --server-http-port 8080`

---

## 13  Debugging Checklist

When agents aren't writing files:

| Check | Command / Method |
|-------|-----------------|
| Is Neuro SAN running? | `curl http://localhost:8080/api/v1/list` |
| Is the network loaded? | Look for your network name in the list response |
| Did the orchestrator read the context index? | Check `logs/tool_calls.log` — first entry should be `ReadFile … _context_index.md OK` |
| Did sub-agents run? | Check `tool_calls.log` — should see `ReadFile` entries for each agent |
| Did sub-agents write? | Check `tool_calls.log` — look for `WriteFile … OK` entries |
| Are paths resolving? | Compare `project_folder` in sly_data with paths in `_context_index.md` |
| Is the class found? | Check Neuro SAN startup logs for "Failed to resolve class" errors |
| Are function blocks present? | If LLM says "I don't have X tool" — the `function` block is missing |

### Common failure patterns

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| 5-second response, 0 files written | `function` block missing from coded tool → LLM can't see tool | Add full `function` block to every coded tool declaration |
| `read_file` returns NOT_FOUND for context index | `project_folder` ≠ path root used in messages | Set `project_folder = BASE_DIR` (same root as `_rel()`) |
| All agents write all files (wrong) | Section 6 says "Write EACH" | Change to "Write ONLY YOUR OWN" + fix prompt section reference |
| Prompt says "Section 7" but context_index only has 6 sections | Prompt was written with wrong section number | `sed -i 's/Section 7/Section 6/g'` all agent prompts |
| Class not found: "Failed to resolve class WriteFile in module write_file" | Short class path `write_file.WriteFile` — no matching folder for Phase 2 | Use full path `coded_tools.bidmagic.write_file.WriteFile` |
| Orchestrator answers in 10s without calling sub-agents | Orchestrator has `write_file` in its tools list | Remove `write_file` from orchestrator's tools array |
| All agent calls complete at EXACTLY ~120s, no files written | `request_timeout_seconds` not set — default 120s cuts off pipeline before `write_file` | Add `"request_timeout_seconds": 600` at top level of HOCON |

---

## 14  Quick HOCON Template

> **Note:** For V3 per-agent dispatch (current architecture), use the template
> in Section 22 instead. This section shows the V2 multi-agent-per-call pattern
> for reference only.

Paste this skeleton when creating a new BidMagic phase network:

```hocon
# =============================================================
# DealCraft V2 — <Phase Name> Phase Network
# File: registries/dealcraft_<phase>.hocon
# Phase: N — <Phase Name> (<N> agents)
# =============================================================

{
    include "registries/llm_config.hocon",

    "metadata": {
        "description": "DealCraft V2 <Phase> Phase — <N> agents: ...",
        "tags": ["dealcraft", "bidmagic", "<phase>", "cognizant"],
        "sample_queries": [
            "Please coordinate the agents for this phase. Context index path: repository/..."
        ]
    },

    "tools": [

        # ── Thin Orchestrator ─────────────────────────────────────────────────
        # IMPORTANT: NO write_file in orchestrator tools — forces delegation
        {
            "name": "<phase>-orchestrator",
            "function": {
                "description": "Coordinates the <Phase> phase. Reads _context_index.md then delegates to <N> specialist agents. Does NOT write files itself."
            },
            "instructions": "dealcraft/prompts/v2/orchestrator-<phase>-prompt.md",
            "llm_config": ${llm_config},
            "tools": [
                "read_file",
                "list_files",
                "<agent-1-name>",
                "<agent-2-name>"
            ]
        },

        # ── Agent 1: <Agent Name> ─────────────────────────────────────────────
        {
            "name": "<agent-1-name>",
            "function": {
                "description": "<What this agent produces>. Writes to iter_N/phase<N>-<phase>/<file-key>.md",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "context_index_content": {
                            "type": "string",
                            "description": "Full content of _context_index.md. Section 6 has the exact output path for this agent."
                        }
                    },
                    "required": ["context_index_content"]
                }
            },
            "instructions": "dealcraft/prompts/v2/<file-key>-v2.md",
            "llm_config": ${llm_config},
            "tools": ["read_file", "write_file", "list_files"]
        },

        # ── File tools (shared BidMagic coded tools) ──────────────────────────
        # IMPORTANT: Use fully-qualified class paths — Phase 1 direct resolution
        {
            "name": "write_file",
            "function": {
                "description": "Write content to a file in the deal repository. mode='write' to create/overwrite; mode='append' to add to existing. Split files >3000 chars into chunks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path":    { "type": "string",  "description": "Relative path. Use EXACT path from Section 6 of _context_index.md. Write ONLY your own file." },
                        "content": { "type": "string",  "description": "Content to write. Keep chunks ≤ 8000 chars. Split at ## headings for large files." },
                        "mode":    { "type": "string",  "description": "'write' (default) or 'append'." },
                        "agent":   { "type": "string",  "description": "Your agent name. Logged." }
                    },
                    "required": ["path", "content"]
                }
            },
            "class": "coded_tools.bidmagic.write_file.WriteFile"
        },
        {
            "name": "read_file",
            "function": {
                "description": "Read a file from the deal repository. Returns content or NOT_FOUND.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path":  { "type": "string",  "description": "Relative path inside the deal repository." },
                        "agent": { "type": "string",  "description": "Your agent name. Logged." }
                    },
                    "required": ["path"]
                }
            },
            "class": "coded_tools.bidmagic.read_file.ReadFile"
        },
        {
            "name": "list_files",
            "function": {
                "description": "List files under a folder in the deal repository. Returns newline-separated relative paths.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path":  { "type": "string", "description": "Folder relative to repository root. Defaults to '.'." },
                        "agent": { "type": "string", "description": "Your agent name. Logged." }
                    }
                }
            },
            "class": "coded_tools.bidmagic.list_files.ListFiles"
        }
    ]
}
```

---

## 15  Agent Prompt Template (sub-agent)

```markdown
# BidMagic DealCraft V2 — <Agent Role> Agent

You are the **<Agent Role>** for Cognizant Pre-Sales.

## Protocol
**Step 1**: Parse `context_index_content` (passed as a parameter — do NOT call read_file for the context index itself).
**Step 2**: Read source files listed in Sections 2–4 using `read_file`.
**Step 3**: Produce your analysis.
**Step 4**: Write output to ONLY YOUR OWN path from **Section 6** using `write_file`.
           Do NOT write files assigned to other agents.

## Your Mission
<Describe what this agent specifically produces>

## Output Format
<Define the exact markdown structure of the output file>

## Key Rules
- Base analysis ONLY on provided context — never hallucinate client facts.
- Write exactly ONE file: the path designated for this agent in Section 6.
- For output files > 15 000 chars, split across multiple write_file calls:
  first call mode="write", subsequent calls mode="append" to the same path.
  Always split at a ## heading boundary — never mid-table or mid-list.
```

---

## 16  LangChain Parallel Tool Dispatch — "Call In Sequence" Is Not Honoured

**Background:** When an LLM with multiple sub-agents is asked to call them
"in sequence", LangChain's agent executor batch-dispatches ALL tool calls from
a single response in parallel via `asyncio`. This is not configurable via the
orchestrator prompt.

### What happens (V2 old architecture, one network call for all agents)

1. Flask sends one Neuro SAN request: "Coordinate the qualification phase."
2. The orchestrator LLM generates a response with 6 tool calls in ONE message:
   `call bid-qualification-agent`, `call rfp-analyzer-agent`, etc.
3. LangChain passes ALL 6 calls to `asyncio.gather()` simultaneously.
4. The fastest 2 agents complete and write their files.
5. When the orchestrator sees their results, it generates its final summary response.
6. **Neuro SAN cancels all remaining asyncio tasks** (the slow 4 agents).
7. The network call returns — 4 out of 6 files were never written.

### Diagnostic: read `logs/server.log`

```
# Cancellation evidence — all at the same timestamp:
Task from qualification-orchestrator.rfp-analyzer-agent cancelled
Task from qualification-orchestrator.eipo-analyzer-agent cancelled
Task from qualification-orchestrator.clause-decomposition-agent cancelled
Task from qualification-orchestrator.compliance-mapping-agent cancelled
```

If you see cancellations, the orchestrator triggered parallel execution.
The fix is **not** to reword the prompt — it is to change the architecture.

### ❌ Anti-pattern: single network call for all agents

```python
# ai_bridge.py — WRONG: one call, orchestrator dispatches all agents
result = invoke_agent("Coordinate all 6 qualification agents", network=network)
```

Even with prompt instructions like:
```
"Call agents strictly in sequence, one at a time, wait for each to complete"
```
…the LLM will still generate multiple tool calls in one response, and LangChain
will dispatch them all in parallel.

### ✅ Fix: one Neuro SAN call per agent (see Section 17)

---

## 17  V3 Per-Agent Sequential Dispatch Pattern

**Architecture:** Flask controls sequencing by calling the Neuro SAN network
once per agent. The orchestrator prompt is replaced with a "dispatcher" that
routes to exactly ONE named agent per call.

### How it works

```
Flask for-loop                Neuro SAN                    Sub-agent
──────────────────────────────────────────────────────────────────────
Call 1 → "Agent: bid-qual"  → dispatcher  → bid-qualification-agent → writes file
                              (completes)
Call 2 → "Agent: rfp-anal"  → dispatcher  → rfp-analyzer-agent      → writes file
                              (completes)
...
Call 6 → "Agent: compliance" → dispatcher → compliance-mapping-agent → writes file
```

No parallelism is possible because each network invocation calls exactly one agent.

### Flask side: `ai_bridge.py`

```python
# Read context index once
with open(ctx_idx_path, "r", encoding="utf-8") as f:
    ctx_content = f.read()

agents      = PHASE_AGENTS.get(phase_name, [])      # list of (agent_key, file_key)
hocon_names = PHASE_AGENT_HOCON_NAMES.get(phase_name, [])  # HOCON tool names

for i, (agent_key, file_key) in enumerate(agents):
    hocon_name = hocon_names[i] if i < len(hocon_names) else agent_key
    message = f"Agent: {hocon_name}\n\nContext index content:\n{ctx_content}"
    result  = invoke_agent(message, sly_data=sly_data, network=network)
    # log result, report progress ...
```

### Neuro SAN side: dispatcher orchestrator prompt

The `orchestrator-<phase>-prompt.md` becomes a pure router:

```markdown
## Your ONLY Job
1. Read the first line to get the agent name after `Agent: `
2. Extract context — everything after `Context index content:\n`
3. Call EXACTLY THAT ONE agent with `context_index_content` = extracted content
4. Return the agent's confirmation message verbatim

## CRITICAL RULES
- Call EXACTLY ONE agent — the one named on line 1
- Do NOT call read_file or write_file yourself
- Do NOT add commentary or analysis
```

### HOCON side: dispatcher has NO file tools

```hocon
{
    "name": "qualification-orchestrator",
    "tools": [
        # NO read_file, NO list_files — sub-agents are the only available tools.
        # This forces the LLM to call a sub-agent (its only available action).
        "bid-qualification-agent",
        "rfp-analyzer-agent",
        ...
    ]
}
```

See Section 18 for why removing file tools from the dispatcher is critical.

### `PHASE_AGENT_HOCON_NAMES` — parallel dict for HOCON names

`PHASE_AGENTS` stores `(agent_key, file_key)` tuples used by file scanning.
Adding a parallel `PHASE_AGENT_HOCON_NAMES` dict maps phase → ordered list of
HOCON tool names without breaking existing callers:

```python
# bidmagic/services/repository_service.py

PHASE_AGENTS = {
    "qualification": [
        ("bid_qualification", "bid-qualification"),
        ("rfp_analysis",      "rfp-analysis"),
        ...
    ],
}

PHASE_AGENT_HOCON_NAMES = {
    "qualification": [
        "bid-qualification-agent",
        "rfp-analyzer-agent",
        ...
    ],
}
```

The two lists are index-aligned. `ai_bridge.py` reads both:
```python
hocon_name = PHASE_AGENT_HOCON_NAMES[phase_name][i]
```

---

## 18  Dispatcher Tool List — Never Give File Tools to the Dispatcher

This is the most counter-intuitive rule. When an orchestrator has `read_file`
available, it will use it — even when you intended it to call a sub-agent.

### What goes wrong

```hocon
# WRONG — dispatcher can read files, so it does
{
    "name": "qualification-orchestrator",
    "tools": [
        "read_file",        # ← dispatcher will call this instead of sub-agents
        "list_files",
        "bid-qualification-agent",
        ...
    ]
}
```

**Sequence of events:**

1. Flask sends: `"Agent: bid-qualification-agent\n\nContext index content:\n[big content]"`
2. The dispatcher LLM sees "Context index content" and interprets it as a hint to READ more context.
3. It calls `read_file("repository/X/deal_context.md")` — the path it found in the context.
4. It receives the file content and returns that as its text response.
5. **It never calls `bid-qualification-agent`.**
6. Neuro SAN returns `ok=True` with the deal_context.md file content as response text.
7. No coded tool calls appeared in `server.log`. No files are written.

### ✅ Fix: dispatcher tools = sub-agents only

```hocon
{
    "name": "qualification-orchestrator",
    "tools": [
        # Only sub-agents — the dispatcher MUST call one (its only option)
        "bid-qualification-agent",
        "rfp-analyzer-agent",
        "service-line-analyzer-agent",
        "eipo-analyzer-agent",
        "clause-decomposition-agent",
        "compliance-mapping-agent"
    ]
}
```

With no file tools available, calling a sub-agent is the dispatcher's only
meaningful action. The LLM reliably routes to the correct agent.

### Diagnostic

| Symptom | Check |
|---------|-------|
| "ok=True" from all 6 agent calls but no files written | `raw_response` in `ai_task_log` will contain file content (e.g. `deal_context.md`), not agent analysis |
| `server.log` shows `Done with <network>.StreamingChat` but no `WriteFile` or `ReadFile` entries | Dispatcher generated a text response without calling any sub-agent |
| All 6 calls return in exactly ~120s | Neuro SAN's internal pipeline timeout — each call hits timeout processing context without writing |

---

## 19  Two Timeouts to Set — `request_timeout_seconds` and `max_execution_seconds`

Neuro SAN has **two independent timeout controls**. Both default to 120 seconds.
Both must be increased for the V3 dispatcher pattern.

### Timeout 1: `request_timeout_seconds` (HTTP streaming timeout)

Controls how long the HTTP streaming handler waits for the entire network call
to complete. Set at the **top level of the phase HOCON**.

```hocon
{
    include "registries/llm_config.hocon",
    "metadata": { ... },
    "request_timeout_seconds": 600,    # ← HTTP streaming timeout (10 min)
    "tools": [ ... ]
}
```

**What happens without it:** The HTTP connection closes at 120s even if the
agent is still running. The streaming response is terminated. `ok=True` may
still be returned (partial response), but no file was written.

### Timeout 2: `max_execution_seconds` (per-agent LLM chain timeout)

Controls how long each individual agent's LLM chain is allowed to run before
being forcibly cancelled. Set in **`registries/llm_config.hocon`** to apply
to all agents across all networks.

```hocon
# registries/llm_config.hocon
{
    "llm_config": {
        "class": "anthropic",
        "model_name": "claude-sonnet-4-6",
        "max_execution_seconds": 600,   # ← per-agent LLM chain timeout (10 min)
    }
}
```

**What happens without it:** Even with `request_timeout_seconds: 600`, each
agent's LLM chain is cancelled at 120s. The cancellation appears in
`server.log` as:
```
Task from <network>.<agent-name>:RunContextRunnable.invoke_agent_chain was cancelled
```

### Diagnostic: which timeout fired?

| Symptom | Which timeout |
|---------|---------------|
| All requests complete at EXACTLY 120s, `ok=True`, no files | `request_timeout_seconds` at default 120s |
| Agent reads RFP files, generates output, then gets cancelled, server.log shows `cancelled` | `max_execution_seconds` at 120s |
| Some agents complete (fast ones), others are cancelled | `max_execution_seconds`: slower agents exceed 120s |

### When to increase beyond 600s

If agents produce very large output files (> 50 KB) with many `write_file`
append calls, or if the RFP source documents are very large (> 100 KB), the
pipeline may take longer. Use 900s (15 min) in those cases.

---

## 20  Dispatcher "ok=True" Trap — Don't Confuse API Success with File Writes

The Neuro SAN HTTP client returns `ok=True` whenever the streaming API returns
non-empty text. This is independent of whether any sub-agent ran or any file
was written.

### What "ok=True" means vs doesn't mean

| Condition | Meaning |
|-----------|---------|
| `result["ok"] == True` | HTTP 200 received, streaming completed, non-empty text returned |
| **Does NOT mean** | A sub-agent ran |
| **Does NOT mean** | `write_file` was called |
| **Does NOT mean** | Any output file exists on disk |

### Always verify with `scan_agent_outputs`

```python
# ai_bridge.py — after the per-agent loop
agent_outputs = scan_agent_outputs(deal_id, client_name, iter_num_int, phase_name)
written = [a for a in agent_outputs if a["status"] == "written"]
# len(written) is the ground truth — not the succeeded counter above
```

### In your test script, check files not API results

```python
# Don't trust "6/6 agents OK" — trust the file system:
for ao in agent_outputs:
    assert ao["status"] == "written", f"{ao['file_key']} was not written"
    assert ao["char_count"] > 50,     f"{ao['file_key']} looks like a stub"
```

---

## 21  Updated Debugging Checklist (V3 additions)

Add these rows to the Section 13 checklist:

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| All agent API calls ok=True, but 0 files written | Dispatcher called `read_file` instead of sub-agent | Remove `read_file`/`list_files` from dispatcher's tools array |
| `server.log` shows completed requests but zero `WriteFile` entries | Same as above, or sub-agents not reached | Check `ai_task_log.raw_response` — if it contains file content, dispatcher deflected to `read_file` |
| `ai_task_log.raw_response` = deal_context.md content for all 6 agents | Dispatcher read the deal context file and returned it instead of delegating | Remove file tools from dispatcher |
| 4 out of 6 agent files missing, 2 of the faster agents wrote files | Old V2 parallel dispatch — LangChain ran all agents simultaneously, slow ones were cancelled | Upgrade to V3 per-agent dispatch (Section 17) |
| All agents cancelled simultaneously in `server.log` | Same — parallel execution, orchestrator returned before slow agents finished | Move to per-agent network calls in Flask loop |

---

## 22  Updated HOCON Template — V3 Dispatcher Pattern

For new BidMagic phase networks using the V3 per-agent dispatch architecture:

```hocon
# =============================================================
# DealCraft V3 — <Phase Name> Phase Network
# Architecture: dispatcher orchestrator (per-agent sequential calls)
# Flask sends one call per agent: "Agent: [hocon-name]\n\nContext index content:\n..."
# Dispatcher routes to exactly ONE agent per call — no parallel execution.
# =============================================================

{
    include "registries/llm_config.hocon",

    "metadata": {
        "description": "DealCraft V3 <Phase> Phase — <N> agents (per-agent sequential dispatch).",
        "tags": ["dealcraft", "bidmagic", "<phase>", "v3"],
        "sample_queries": [
            "Agent: <agent-1-name>\n\nContext index content:\n# Context Index ..."
        ]
    },

    "tools": [

        # ── Dispatcher Orchestrator ───────────────────────────────────────────
        # CRITICAL: NO read_file, NO list_files — only sub-agents as tools.
        # Removing file tools forces the LLM to call a sub-agent (its only option).
        # The dispatcher receives "Agent: [name]" and routes to that exact agent.
        {
            "name": "<phase>-orchestrator",
            "function": {
                "description": "Routes each call to exactly one specialist agent based on the 'Agent: [name]' line in the user message. Does NOT read files or write files itself."
            },
            "instructions": "dealcraft/prompts/v2/orchestrator-<phase>-prompt.md",
            "llm_config": ${llm_config},
            "tools": [
                # Sub-agents ONLY — no read_file, no list_files
                "<agent-1-name>",
                "<agent-2-name>"
            ]
        },

        # ── Agent 1: <Agent Name> ─────────────────────────────────────────────
        # Sub-agents receive context_index_content as a parameter — they still
        # have read_file to read RFP/source files referenced in the context.
        {
            "name": "<agent-1-name>",
            "function": {
                "description": "<What this agent produces>. Writes to iter_N/phase<N>-<phase>/<file-key>.md",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "context_index_content": {
                            "type": "string",
                            "description": "Full content of _context_index.md. Section 6 has the exact output path for this agent."
                        }
                    },
                    "required": ["context_index_content"]
                }
            },
            "instructions": "dealcraft/prompts/v2/<file-key>-v2.md",
            "llm_config": ${llm_config},
            "tools": ["read_file", "write_file", "list_files"]
        },

        # ── File tools (shared BidMagic coded tools) ──────────────────────────
        {
            "name": "write_file",
            "function": {
                "description": "Write content to a file in the deal repository. mode='write' to create/overwrite; mode='append' to add to existing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path":    { "type": "string",  "description": "Relative path. Use EXACT path from Section 6 of _context_index.md." },
                        "content": { "type": "string",  "description": "Content to write. Keep chunks <= 8000 chars. Split at ## headings." },
                        "mode":    { "type": "string",  "description": "'write' (default) or 'append'." },
                        "agent":   { "type": "string",  "description": "Your agent name. Logged." }
                    },
                    "required": ["path", "content"]
                }
            },
            "class": "coded_tools.bidmagic.write_file.WriteFile"
        },
        {
            "name": "read_file",
            "function": {
                "description": "Read a file from the deal repository. Returns content or NOT_FOUND.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path":  { "type": "string",  "description": "Relative path inside the deal repository." },
                        "agent": { "type": "string",  "description": "Your agent name. Logged." }
                    },
                    "required": ["path"]
                }
            },
            "class": "coded_tools.bidmagic.read_file.ReadFile"
        },
        {
            "name": "list_files",
            "function": {
                "description": "List files under a folder in the deal repository.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path":  { "type": "string", "description": "Folder relative to repository root." },
                        "agent": { "type": "string", "description": "Your agent name. Logged." }
                    }
                }
            },
            "class": "coded_tools.bidmagic.list_files.ListFiles"
        }
    ]
}
```

---

*Document owner: BidMagic team | Last updated: May 2026*
*Source: lessons from BidMagic V2 + V3 DealCraft build, neuro-san-studio*
