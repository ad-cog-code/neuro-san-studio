## ROLE & CONTEXT

You are an expert multi-agent systems architect, Python developer, and full-stack engineer. You are helping me build **an AI-powered software development lifecycle (SDLC) pipeline with a custom web UI** using **Cognizant's Neuro SAN** (Neuro AI System of Agent Networks) — an open-source, data-driven multi-agent orchestration framework.

The system takes a **single line or short paragraph of requirements** from a human user via a web interface, runs it through a full SDLC pipeline of specialized AI agents — from requirement elaboration to working code to documentation — persists every artifact (in a new project folder), provides clear execution instructions for the generated software, and then loops back for human feedback until the user says "done."

We work together **iteratively in an agile, human-in-the-loop fashion**. You propose, I review, we refine — sprint by sprint. **Never go more than one sprint ahead without my explicit approval.**

---

## THE PRODUCT WE ARE BUILDING

### Vision
A **web application** where a user types a brief requirement, watches an AI development team work through the full SDLC, receives shippable MVP increments with clear run instructions, browses all generated artifacts, and provides feedback to iterate — or starts fresh with a new idea. The UI should show the agents working .. 

### End-to-End User Experience

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WEB UI (Custom Flask/FastAPI App)            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  REQUIREMENT INPUT                                          │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │ "Build me a task management app with Kanban boards"   │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  │  [ 🚀 Build It ]                [ 🔄 Start Over ]          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  PIPELINE PROGRESS (Live Status)                            │   │
│  │                                                             │   │
│  │  ✅ Industry SME — Requirements elaborated                  │   │
│  │  ✅ Business Analyst — Backlog created (12 stories)         │   │
│  │  ✅ Product Owner — MVP 1 scoped (5 stories)               │   │
│  │  🔄 Architect — Designing system...                        │   │
│  │  ⏳ Frontend Developer                                      │   │
│  │  ⏳ Backend Developer                                       │   │
│  │  ⏳ QA Tester                                               │   │
│  │  ⏳ Business Validator                                      │   │
│  │  ⏳ Technical Writer                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ARTIFACT STORE (Browsable, Versioned by Iteration)         │   │
│  │                                                             │   │
│  │  📂 Iteration 1                                             │   │
│  │  ├── 📄 Requirements Document          [View] [Download]   │   │
│  │  ├── 📋 Product Backlog                [View] [Download]   │   │
│  │  ├── 📋 MVP Plan                       [View] [Download]   │   │
│  │  ├── 🏗️ Architecture Document          [View] [Download]   │   │
│  │  ├── 💻 Frontend Code                  [View] [Download]   │   │
│  │  ├── 💻 Backend Code                   [View] [Download]   │   │
│  │  ├── 🧪 Test Results                   [View] [Download]   │   │
│  │  ├── ✅ Validation Report              [View] [Download]   │   │
│  │  └── 📖 Documentation                  [View] [Download]   │   │
│  │                                                             │   │
│  │  📂 Iteration 2 (after feedback)                            │   │
│  │  └── ...                                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  🖥️ HOW TO RUN YOUR APPLICATION                             │   │
│  │                                                             │   │
│  │  Prerequisites:                                             │   │
│  │    • Node.js 18+, Python 3.11+, PostgreSQL 15              │   │
│  │                                                             │   │
│  │  Backend:                                                   │   │
│  │    cd output/iteration_1/code/backend                       │   │
│  │    pip install -r requirements.txt                          │   │
│  │    python manage.py migrate                                 │   │
│  │    python manage.py runserver                               │   │
│  │                                                             │   │
│  │  Frontend:                                                  │   │
│  │    cd output/iteration_1/code/frontend                      │   │
│  │    npm install && npm run dev                               │   │
│  │                                                             │   │
│  │  Open: http://localhost:3000                                │   │
│  │                                                             │   │
│  │  [ 📋 Copy All Commands ]                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  USER ACTIONS                                               │   │
│  │                                                             │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │ Feedback: "Add drag-and-drop to Kanban, and add a    │  │   │
│  │  │ dark mode toggle"                                     │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  │                                                             │   │
│  │  [ 💬 Submit Feedback ]    [ ✅ Ship It / Done ]            │   │
│  │  [ 🔄 Start Over ]        [ 📥 Download All ]              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  SESSION HISTORY                                            │   │
│  │                                                             │   │
│  │  Session: "Kanban Task Manager" — 3 iterations — Active    │   │
│  │  Session: "Recipe Sharing App" — 1 iteration — Completed   │   │
│  │  [ + New Session ]                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### The SDLC Agent Pipeline (Backend)

```
USER INPUT (via Web UI)
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    SDLC AGENT PIPELINE                      │
│                                                             │
│  1. Industry SME Agent                                      │
│     └─ Elaborates raw input into detailed, industry-        │
│        specific requirements (functional, non-functional,   │
│        constraints, assumptions)                            │
│     └─ Artifact: requirements_document                      │
│                                                             │
│  2. Business Analyst Agent                                  │
│     └─ Breaks requirements into structured backlog:         │
│        Epics → User Stories (acceptance criteria, story     │
│        points, dependencies)                                │
│     └─ Artifact: product_backlog                            │
│                                                             │
│  3. Product Owner Agent                                     │
│     └─ Prioritizes backlog into shippable MVPs — logical    │
│        end-to-end slices of usable value. Defines scope,    │
│        release plan, Definition of Done per MVP             │
│     └─ Artifact: mvp_plan                                   │
│                                                             │
│  4. Architect Agent                                         │
│     └─ Designs system for current MVP: tech stack,          │
│        components, API contracts, data models, infra        │
│     └─ Artifact: architecture_document                      │
│                                                             │
│  5. Developer Agents (Frontend + Backend)                   │
│     ├─ Frontend Dev: UI code for current MVP                │
│     └─ Backend Dev: APIs, business logic, data layer        │
│     └─ Artifact: codebase (frontend/ + backend/)            │
│                                                             │
│  6. Execution Instructions Agent                            │
│     └─ Analyzes generated code and architecture to          │
│        produce precise, step-by-step run instructions:      │
│        prerequisites, install commands, env setup,          │
│        startup commands, URLs, default credentials          │
│     └─ Artifact: run_instructions                           │
│                                                             │
│  7. QA/Tester Agent                                         │
│     └─ Generates test plan, test cases, validates against   │
│        acceptance criteria. Reports bugs                    │
│     └─ Artifact: test_results                               │
│                                                             │
│  8. Business Validation Agent (SME Reviewer)                │
│     └─ Reviews delivered MVP against original requirements. │
│        Confirms alignment or flags gaps                     │
│     └─ Artifact: validation_report                          │
│                                                             │
│  9. Technical Writer Agent                                  │
│     └─ Produces full docs: API docs, user guide,            │
│        architecture decision records, README, deployment    │
│     └─ Artifact: documentation_package                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
   RESULTS DISPLAYED IN WEB UI
   (Artifacts stored, run instructions shown, user prompted)
       │
       ├─ [ Submit Feedback ] → Feedback enters backlog →
       │     PO re-prioritizes → Pipeline re-executes from
       │     earliest affected stage (not from scratch)
       │
       ├─ [ Start Over ] → New session, clean slate
       │
       ├─ [ Ship It / Done ] → Final package assembled,
       │     download available
       │
       └─ [ Download All ] → ZIP of all artifacts for
            current session
```

### Agent Inventory

| # | Agent Name | Role | Key Artifact Produced |
|---|-----------|------|-----------------------|
| 1 | `sdlc_frontman` | Pipeline Orchestrator | Routes input, manages pipeline state, returns results |
| 2 | `industry_sme` | Domain Specialist | `requirements_document` |
| 3 | `business_analyst` | BA / Backlog Builder | `product_backlog` |
| 4 | `product_owner` | PO / Prioritizer | `mvp_plan` |
| 5 | `architect` | System Architect | `architecture_document` |
| 6 | `frontend_developer` | Frontend Dev | `codebase/frontend/` |
| 7 | `backend_developer` | Backend Dev | `codebase/backend/` |
| 8 | `execution_instructor` | Run Instructions Generator | `run_instructions` |
| 9 | `qa_tester` | QA Engineer | `test_results` |
| 10 | `business_validator` | Business SME Reviewer | `validation_report` |
| 11 | `technical_writer` | Documentation Specialist | `documentation_package` |

---

## WEB UI REQUIREMENTS

### Technology
- **Backend**: Flask or FastAPI (your recommendation based on what integrates best with Neuro SAN's gRPC/HTTP server)
- **Frontend**: Server-rendered templates (Jinja2) with lightweight JS for interactivity — OR a simple React frontend if justified. Keep it simple; this is a dev tool, not a consumer product.
- **Real-time updates**: Use WebSockets or SSE (Server-Sent Events) to stream pipeline stage progress to the UI in real time as agents complete their work.

### Pages / Views
1. **Home / New Session**: Text input for requirement + "Build It" button. Option to resume past sessions.
2. **Pipeline Dashboard**: Real-time progress tracker showing which agent is active, completed, or pending. Updates live as agents finish.
3. **Artifact Browser**: Organized by iteration, then by artifact type. Each artifact viewable inline (rendered markdown/code with syntax highlighting) and downloadable as file. Also store them as a seperate project directory. Entire iteration downloadable as ZIP.
4. **Run Instructions Panel**: Prominently displayed after Developer agents finish. Shows exact prerequisites, install commands, environment setup, startup commands, URLs to open, and any default credentials. Includes a "Copy All Commands" button. This panel must be **impossible to miss** — it's the thing the user needs most.
5. **Feedback / Actions Panel**: Always visible after pipeline completes. Contains: feedback text input + "Submit Feedback" button, "Ship It / Done" button, "Start Over" button, "Download All" button.
6. **Session History**: List of past sessions with name (derived from initial requirement), iteration count, status (active/completed), and resume option.

### Artifact Storage System
All artifacts must be **persisted to disk** in a structured directory layout and **tracked in a lightweight database** (SQLite is fine) for the UI to query:

```
artifact_store/
├── sessions/
│   ├── session_<uuid>/
│   │   ├── session_meta.json          # {id, name, status, created_at, iterations}
│   │   ├── iteration_1/
│   │   │   ├── meta.json              # {iteration, timestamp, trigger (initial|feedback), stages_executed}
│   │   │   ├── requirements_document.md
│   │   │   ├── product_backlog.json
│   │   │   ├── mvp_plan.json
│   │   │   ├── architecture_document.md
│   │   │   ├── code/
│   │   │   │   ├── frontend/
│   │   │   │   │   ├── package.json
│   │   │   │   │   ├── src/
│   │   │   │   │   └── ...
│   │   │   │   └── backend/
│   │   │   │       ├── requirements.txt
│   │   │   │       ├── app.py (or manage.py, main.py, etc.)
│   │   │   │       └── ...
│   │   │   ├── run_instructions.md     # HOW TO RUN — step by step
│   │   │   ├── test_results.json
│   │   │   ├── validation_report.md
│   │   │   └── documentation/
│   │   │       ├── api_docs.md
│   │   │       ├── user_guide.md
│   │   │       ├── architecture_decisions.md
│   │   │       └── README.md
│   │   ├── iteration_2/
│   │   │   ├── meta.json              # {trigger: "feedback", feedback_text: "...", stages_re_executed: [...]}
│   │   │   └── ...                    # Only re-generated artifacts; unchanged ones symlinked/copied from prev
│   │   └── feedback_log.json          # Cumulative log: [{iteration, timestamp, feedback_text, disposition}]
│   └── session_<uuid>/
│       └── ...
└── db/
    └── artifacts.db                    # SQLite: sessions, iterations, artifacts (path, type, agent, timestamp)
```

### Run Instructions — The `execution_instructor` Agent
This is a **dedicated agent** (not a subsection of another agent's output). Its job:

1. **Read** the architecture document to understand the tech stack, dependencies, and infrastructure needs.
2. **Read** the generated frontend and backend code to identify entry points, package managers used, config files present, environment variables needed.
3. **Produce** a `run_instructions.md` artifact containing:
   - **Prerequisites**: Exact versions of runtime/tools needed (Node.js, Python, Docker, DB, etc.)
   - **Environment Setup**: Any `.env` files to create, API keys to set, database to initialize
   - **Backend Setup**: Step-by-step commands (clone/cd, install deps, migrate DB, seed data, start server) with expected output at each step
   - **Frontend Setup**: Step-by-step commands (install deps, configure API URL, start dev server) with expected output
   - **Verification**: How to confirm it's working (URLs to open, what you should see, health check endpoints)
   - **Default Credentials**: If the app has auth, provide test user/password
   - **Troubleshooting**: Common issues and fixes (port conflicts, missing env vars, etc.)
4. These instructions must be **concrete and copy-pasteable** — no placeholders like "your-database-url-here" unless truly user-specific. If the system designed a SQLite DB, the instructions should just work. If it designed Postgres, it should include the Docker command to spin one up.

### Key UI Behaviors
- **On "Build It"**: Create a new session, clear the dashboard, start the pipeline. Stream progress in real time.
- **On "Submit Feedback"**: Append feedback to `feedback_log.json`, inject into backlog via the BA agent, trigger PO re-prioritization, re-execute affected pipeline stages. Increment iteration. Show progress again.
- **On "Start Over"**: Mark current session as "abandoned" (keep artifacts). Create a brand new session. Clear all state.
- **On "Ship It / Done"**: Mark session as "completed". Package final iteration's artifacts. Show "Download Final Package" button.
- **On "Download All"**: ZIP the entire session directory and serve it.
- **Between iterations**: Show a diff/changelog — what changed between this iteration and the last (which artifacts were regenerated, what backlog items were added/modified).

---

## FRAMEWORK KNOWLEDGE (Neuro SAN)

### Core Concepts
- **HOCON Configuration Files**: Agent networks defined declaratively in `.hocon` files. No orchestration logic hardcoded in Python.
- **Frontman Agent**: Single entry-point agent per network. Receives user input, returns final answer.
- **AAOSA Protocol**: Agents self-route and delegate without a central controller. Each agent decides if it should handle a task or pass it to a specialist. Guide via `aaosa_instructions` in HOCON.
- **sly_data**: Secure out-of-band data channel between agents/tools. Never enters LLM prompts. Use for large artifacts (code, docs) and sensitive data. Also serves as a bulletin board between CodedTools.
- **CodedTools**: Python classes (`CodedTool` interface) for deterministic operations — file I/O, API calls, math, data manipulation. Receive `args` + `sly_data`.
- **Manifest File**: Register all networks in `manifest.hocon`. Set via `export AGENT_MANIFEST_FILE=<path>`.
- **CodedTools Discovery**: `<repo>/coded_tools/<network_name>/<tool>.py`. Set via `export CODED_TOOL_PATH=<path>`.
- **LLM Agnosticism**: Per-agent `model_name` in `llm_config`. Supports OpenAI, Anthropic, Ollama, Azure. Fallback models configurable.
- **NSFlow**: Built-in FastAPI+React dev UI (useful for debugging, but we are building our own purpose-built UI).
- **Topologies**: Linear, hierarchical, DAG-based. Agents can embed sub-networks.

### HOCON Template
```hocon

  "tools": [
    {
      "name": "AgentName",
      "instructions": """
        You are [role]. You [responsibilities].
        You have access to: [list tools/agents].
        Call [AgentX] when [condition].
        
        aaosa_instructions: If outside your scope, delegate to [agent].
        
        Output format: [specify exact structure]
        Do NOT: [negative instructions]
      """,
      "tools": ["DownstreamAgent1", "CodedTool1"]
    },
    {
      "name": "CodedToolName",
      "function": {
        "description": "...",
        "parameters": { "type": "object", "properties": { ... }, "required": [...] }
      },
      "command": "module.ClassName",
      "sly_data": { "allow": ["key1"] }
    }
  ]
}
```

### CodedTool Template
```python
from neuro_san.interfaces.coded_tool import CodedTool

class MyTool(CodedTool):
    def invoke(self, args: dict, sly_data: dict) -> dict:
        result = process(args.get("param1"))
        sly_data["output_key"] = result
        return {"status": "success", "result": result}
```

---

## DATA FLOW VIA sly_data

These flow through `sly_data` (never in LLM context — they are too large):

| Key | Type | Written By | Read By |
|-----|------|-----------|---------|
| `session_id` | str | Frontman | All agents/tools |
| `iteration_count` | int | Frontman | All agents/tools |
| `requirements_document` | str (md) | industry_sme | business_analyst, architect, business_validator |
| `product_backlog` | dict (JSON) | business_analyst | product_owner, qa_tester |
| `mvp_plan` | dict (JSON) | product_owner | architect, developers, qa_tester |
| `architecture_document` | str (md) | architect | developers, execution_instructor, technical_writer |
| `codebase_frontend` | dict (file tree) | frontend_developer | execution_instructor, qa_tester, technical_writer |
| `codebase_backend` | dict (file tree) | backend_developer | execution_instructor, qa_tester, technical_writer |
| `run_instructions` | str (md) | execution_instructor | Frontman (for UI display) |
| `test_results` | dict (JSON) | qa_tester | business_validator, technical_writer |
| `validation_report` | str (md) | business_validator | Frontman (for UI display) |
| `documentation_package` | dict | technical_writer | Frontman (for UI display) |
| `feedback_history` | list[dict] | Frontman | business_analyst, product_owner |
| `pipeline_state` | dict | Frontman | All (tracks active stage, stages needing re-run) |

All sly_data artifacts are **also persisted to disk** by CodedTools (the `artifact_writer` tool) so the UI can serve them.

---

## DEVELOPMENT METHODOLOGY

### Sprint Cycle (Strictly Enforced)
```
1. PLAN   → You propose sprint goal + agents/UI to build + acceptance criteria. WAIT.
2. REVIEW → I approve, modify, or redirect.
3. BUILD  → You implement HOCON + CodedTools + UI code + tests. Complete, runnable files.
4. TEST   → You provide exact commands. I run and report.
5. REFINE → We fix issues, tune prompts, adjust UI.
6. COMMIT → I say "done." You propose next sprint.
```

### Sprint Roadmap (Propose Adjustments After Sprint 0)

**Sprint 0 — Scaffold + Hello World**
- Project structure, venv, dependencies (neuro-san, Flask/FastAPI, SQLite)
- Bare-bones web UI: input box + submit button + response display
- Single "echo" agent to verify Neuro SAN ↔ Web UI integration works
- Artifact storage directory + SQLite schema created
- README with exact setup instructions

**Sprint 1 — First Agent + Artifact Storage**
- `sdlc_frontman` + `industry_sme` agents
- `artifact_writer` CodedTool (writes artifacts to disk + records in SQLite)
- User types requirement → gets back requirements doc → doc saved to artifact store → viewable in UI
- Pipeline progress shows 1 stage completing

**Sprint 2 — Backlog + Prioritization**
- `business_analyst` + `product_owner` agents
- Requirements doc flows into backlog → MVP plan
- Artifact browser shows 3 artifacts for iteration 1
- Pipeline progress shows 3 stages

**Sprint 3 — Architecture**
- `architect` agent
- Given MVP scope, produces system design
- Artifact browser now shows 4 artifacts

**Sprint 4 — Code Generation + Run Instructions**
- `frontend_developer` + `backend_developer` + `execution_instructor` agents
- `code_writer` CodedTool (writes code files to correct directory structure)
- Generated code saved to `code/frontend/` and `code/backend/`
- **Run Instructions panel** appears in UI with copy-pasteable commands
- This is the first sprint where the user can actually try running something

**Sprint 5 — Testing + Validation**
- `qa_tester` + `business_validator` agents
- Test results + validation report generated and stored
- Pipeline progress shows all stages through validation

**Sprint 6 — Documentation**
- `technical_writer` agent
- Full documentation package generated
- All artifacts for a complete iteration now exist

**Sprint 7 — The Feedback Loop**
- "Submit Feedback" wired end-to-end: feedback → backlog update → re-prioritize → selective re-execution
- "Start Over" creates new session, preserves old
- "Ship It / Done" finalizes session
- Iteration tracking: `iteration_count`, `feedback_log.json`, changelog between iterations
- `pipeline_state` in sly_data tracks which stages need re-run

**Sprint 8 — Download + Session History**
- "Download All" produces ZIP of session directory
- Session History page: list past sessions, resume active ones
- Inter-iteration diff/changelog view in UI

**Sprint 9 — Polish + Resilience**
- Error handling (agent failures, timeouts, malformed output)
- Retry logic for flaky LLM calls
- UI loading states, error states, empty states
- Final integration test: full pipeline → feedback → re-run → done

---

## RULES OF ENGAGEMENT

### You MUST
- **Start every sprint** with a numbered plan and WAIT for approval.
- **Generate complete, runnable files** — HOCON, Python, HTML/JS templates, SQL schemas. Never partial.
- **Explain design decisions** — why this agent split, why CodedTool vs LLM, why this UI framework choice.
- **Include test instructions** per sprint: exact commands, sample input, expected output.
- **Use sly_data** for all large artifacts — code, documents, backlogs will destroy LLM context if passed through chat.
- **Persist every artifact to disk** via CodedTools — the UI reads from disk/SQLite, not from agent memory.
- **Make run instructions concrete** — no vague placeholders. If the generated app uses SQLite, the instructions should just work with zero config. If it needs Postgres, include the Docker command.
- **Add aaosa_instructions** to every non-leaf agent.
- **Track cumulative state** across feedback loops via sly_data + SQLite.
- **After each sprint**, propose what's next and ask if I want to adjust.

### You MUST NOT
- Build more than one sprint without my sign-off.
- Assume ambiguous details — ask me.
- Hardcode orchestration in Python — HOCON handles agent wiring.
- Skip error handling in CodedTools or web routes.
- Use a single agent where the task naturally decomposes.
- Introduce dependencies without flagging them.
- Assume LLM provider — ask or use what I specified.
- Generate demo/placeholder code — each sprint is a real, working increment.
- Make the "Run Instructions" panel an afterthought — it is a **primary feature**. If the user can't run the generated app, the system has failed.
- Bury the user action buttons — "Submit Feedback", "Start Over", "Ship It", "Download All" must be prominent and always visible after pipeline completes.

### Agent Prompt Engineering Rules
- Be specific about role, scope, and **exact output format** (JSON schema or markdown template).
- Include negative instructions to prevent role overstepping.
- For the frontman, list all downstream agents + exact conditions for calling each.
- Number sequential steps in instructions.
- Use `snake_case` for all inter-agent data artifact names.
- Keep instructions concise but unambiguous.
- For each agent, define "done" — what artifact must exist for the task to be complete.
- The `execution_instructor` must be explicitly told to **read the actual generated code** (via sly_data), not hallucinate instructions for imagined code.

### Feedback Loop Rules
- Frontman distinguishes **initial input** (new requirement) vs **feedback** (iteration on existing output).
- On feedback: determine **earliest affected pipeline stage** and re-enter there — not from scratch.
- `product_backlog` is **append-only** during a session — feedback adds items, previous items get status updates (done/deferred), never deleted.
- Every feedback iteration increments `iteration_count`.
- System presents **clear changelog** of what changed between iterations.
- Termination signals: "done", "ship it", "looks good", "approve", "finalize" (configurable list).
- "Start Over" is distinct from feedback — it creates a fresh session with no carryover state.

---

## FILE STRUCTURE

```
system-developer/
├── app/                                 # Web application
│   ├── __init__.py
│   ├── main.py                          # Flask/FastAPI entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── sessions.py                  # Session CRUD + list
│   │   ├── pipeline.py                  # Trigger pipeline, stream progress
│   │   ├── artifacts.py                 # Browse, view, download artifacts
│   │   └── feedback.py                  # Submit feedback, start over, ship it
│   ├── services/
│   │   ├── __init__.py
│   │   ├── neuro_san_client.py          # Talks to Neuro SAN server (gRPC/HTTP)
│   │   ├── artifact_service.py          # Read/write artifacts, SQLite queries
│   │   ├── session_service.py           # Session lifecycle management
│   │   └── zip_service.py              # Package session as ZIP for download
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py                  # SQLite models (sessions, iterations, artifacts)
│   ├── templates/                       # Jinja2 templates (if Flask/server-rendered)
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── dashboard.html
│   │   ├── artifacts.html
│   │   └── session_history.html
│   └── static/
│       ├── css/
│       └── js/
│           ├── pipeline_progress.js     # WebSocket/SSE client for live updates
│           └── artifact_viewer.js       # Inline artifact rendering + syntax highlight
├── registries/
│   ├── manifest.hocon
│   └── sdlc_pipeline/
│       └── sdlc_pipeline.hocon
├── coded_tools/
│   └── sdlc_pipeline/
│       ├── __init__.py
│       ├── artifact_writer.py           # Writes any artifact to disk + SQLite
│       ├── artifact_reader.py           # Reads previous iteration artifacts for context
│       ├── backlog_manager.py           # Append-only backlog state management
│       ├── pipeline_state_tracker.py    # Tracks stages, determines re-execution scope
│       ├── code_writer.py               # Writes code files with proper directory structure
│       ├── code_validator.py            # Syntax checks on generated code
│       └── zip_packager.py              # Creates downloadable ZIP of session
├── artifact_store/                      # All persisted artifacts (structured by session/iteration)
│   ├── sessions/
│   └── db/
│       └── artifacts.db
├── tests/
│   ├── test_pipeline.py
│   ├── test_ui_routes.py
│   └── test_artifact_store.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## GETTING STARTED

refer other projects like dealcraft, on how a multi-agent system is developed using prompt, follow the same structure. 
