# Common Coded Tools — Design Guide
**Location:** `neuro-san-studio/coded_tools/common/`  
**Applies to:** All Neuro SAN agent networks in this studio  
**Last updated:** May 2026

---

## What this is

A shared library of reusable coded tools that any agent network can reference directly.  
**Do not copy these into individual network folders.** Use the shared versions — one fix improves all networks at once.

---

## Server startup — LiteLLM must run before Neuro SAN

All agent LLM calls route through the **LiteLLM proxy** on `localhost:4000`.
The `ai_search` tool also uses it for synthesis. If the proxy is not running,
agents get no Sonnet → Haiku fallback and all LLM calls fail.

### Automatic check — built into every app

`C:\my-projects\litellm_health.py` is a shared module (importable from the
shared venv) that every hybrid app calls on startup:

```
python app.py   ← AppMagic, BidMagic, any new hybrid app
```

What you see when the proxy isn't running:

```
  ⚠  LiteLLM proxy isn't running — all agent LLM calls will fail.
     Starting LiteLLM proxy in background...
     LiteLLM proxy ready after 6s ✓

Starting AppMagic on http://localhost:5006
```

What you see when it's already up:

```
  LiteLLM proxy ✓  (port 4000 already listening)

Starting BidMagic on http://localhost:5005
```

No manual intervention needed — the proxy starts itself.

### Neuro SAN startup

```powershell
# In neuro-san-studio/ (VS Code integrated terminal)
python start_neuro_san.py
```

Same check runs before Neuro SAN launches. Use this instead of `python -m run`.

### Adding the check to a new hybrid app

In `app.py`, inside the `if __name__ == "__main__":` block:

```python
if __name__ == "__main__":
    port = PORT
    import sys as _sys, os as _os                     # resolve C:\my-projects\ from any subfolder
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from litellm_health import ensure_litellm_running
    ensure_litellm_running()                          # ← add these four lines
    print(f"Starting MyApp on http://localhost:{port}")
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
```

### Requirements
```
ANTHROPIC_API_KEY=<your-key>   ← neuro-san-studio/.env or shell env
litellm>=1.60.0                ← pip install "litellm>=1.60.0"
```

---

## Available tools

| Tool | Class path | Reads | Writes | What it does |
|---|---|:---:|:---:|---|
| `list_files` | `coded_tools.common.list_files.ListFiles` | — | — | List files in input or output directory (glob filter) |
| `read_file` | `coded_tools.common.read_file.ReadFile` | text | — | Read any text file; line-range slicing for large files |
| `write_file` | `coded_tools.common.write_file.WriteFile` | — | text | Write or append text; chunked-write for large output |
| `read_pdf` | `coded_tools.common.read_pdf.ReadPdf` | PDF | — | Extract text from PDF; page-range slicing |
| `read_docx` | `coded_tools.common.read_docx.ReadDocx` | DOCX | — | Extract headings, paragraphs, tables from Word; block-range slicing |
| `read_pptx` | `coded_tools.common.read_pptx.ReadPptx` | PPTX | — | Extract per-slide text + speaker notes; slide-range slicing |
| `read_xlsx` | `coded_tools.common.read_xlsx.ReadXlsx` | XLSX | — | Read Excel sheet as CSV; row-range slicing; list sheet names |
| `write_docx` | `coded_tools.common.write_docx.WriteDocx` | — | DOCX | Create or append to a Cognizant-branded Word file |
| `write_pptx` | `coded_tools.common.write_pptx.WritePptx` | — | PPTX | Create or append to a Cognizant-branded PowerPoint |
| `write_xlsx` | `coded_tools.common.write_xlsx.WriteXlsx` | — | XLSX | Write tabular data (CSV or JSON) to Excel; append rows or sheets |
| `convert_to_pdf` | `coded_tools.common.convert_to_pdf.ConvertToPdf` | DOCX | PDF | Convert a Word document to PDF using Microsoft Word |
| `create_chart` | `coded_tools.common.create_chart.CreateChart` | — | PNG | Bar, line, pie, donut, stacked bar charts from CSV/JSON data |
| `create_diagram` | `coded_tools.common.create_diagram.CreateDiagram` | — | PNG | Flowcharts and architecture diagrams from JSON node+edge spec |
| `search_web` | `coded_tools.common.search_web.SearchWeb` | — | — | DuckDuckGo search — titles, URLs, snippets |
| `ai_search` | `coded_tools.common.ai_search.AiSearch` | — | — | DuckDuckGo + AI synthesis into a focused answer |
| `ocr_image` | `coded_tools.common.ocr_image.OcrImage` | image | — | Extract text/details from image using Claude vision |

---

## File type support

| Tool | `.txt` `.md` | `.pdf` | `.docx` | `.pptx` | `.xlsx` | `.jpg` `.png` etc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `read_file` | ✅ | ⚠️ garbled | ⚠️ garbled | ⚠️ garbled | ⚠️ garbled | ⚠️ garbled |
| `write_file` | ✅ | — | — | — | — | — |
| `read_pdf` | — | ✅ | — | — | — | — |
| `read_docx` | — | — | ✅ | — | — | — |
| `read_pptx` | — | — | — | ✅ | — | — |
| `read_xlsx` | — | — | — | — | ✅ | — |
| `write_docx` | — | — | ✅ | — | — | — |
| `write_pptx` | — | — | — | ✅ | — | — |
| `write_xlsx` | — | — | — | — | ✅ | — |
| `convert_to_pdf` | — | DOCX→PDF | — | — | — | — |
| `create_chart` | — | — | — | — | — | PNG out |
| `create_diagram` | — | — | — | — | — | PNG out |
| `ocr_image` | — | — | — | — | — | ✅ |

> `write_docx` and `write_pptx` use `Cognizant_Template.docx/.pptx` from `coded_tools/assets/` by default. Falls back to plain styling if the template file is missing.  
> **convert_to_pdf** requires Microsoft Word installed on the Neuro SAN server (Windows only).

---

## Directory layout — input / output split (Option A)

Tools separate READ paths from WRITE paths using sly_data keys.
Set these from your Flask app before calling Neuro SAN:

```python
sly_data = {
    "input_dir":  "/path/to/app/uploads",    # READ tools resolve relative paths here
    "output_dir": "/path/to/app/outputs",    # WRITE tools resolve relative paths here
    "workspace_dir": "/path/to/workspace",   # fallback for both (backward-compat)
    "log_dir": "/path/to/project/logs",      # where tool_calls.log is written
                                             # scope per deal/project — NOT per phase
                                             # or iteration — so you see the full
                                             # picture in one file
}
```

### log_dir — one log per deal or project

Always scope `log_dir` to the **deal or project level**, never deeper.
One `tool_calls.log` per deal/project means you can read the whole history in one place — every tool call, every agent, every phase, in chronological order.

```
# ✅ Good — one log for the whole deal
log_dir = repository/acme-corp-erp-2026/logs/

# ❌ Too narrow — forces you to check multiple folders to understand a deal
log_dir = repository/acme-corp-erp-2026/iter_3/logs/
```

### Reference implementations

**BidMagic** (`bidmagic/services/ai_bridge.py`):
```python
log_dir = os.path.join(BASE_DIR, "repository", deal_slug, "logs")
# → repository/acme-corp-erp-2026/logs/tool_calls.log
# All iterations and phases for a deal in one log.
```

**AppMagic** (`appmagic/services/ai_bridge.py`):
```python
log_dir = os.path.join(project_folder_path, "logs")
# → projects/my-app/logs/tool_calls.log
# All agent activity for a project in one log.
```

### Resolution order

**Read tools** (`read_file`, `read_pdf`, `read_docx`, `read_pptx`, `read_xlsx`, `ocr_image`, `convert_to_pdf` input):
1. `sly_data["input_dir"]`      ← preferred
2. `sly_data["workspace_dir"]`  ← fallback
3. `sly_data["project_folder"]` ← BidMagic/DealCraft backward-compat
4. `COMMON_INPUT_DIR` env var
5. `COMMON_WORKSPACE_DIR` env var
6. Current working directory    ← last resort (logged as warning)

**Write tools** (`write_file`, `write_docx`, `write_pptx`, `write_xlsx`, `convert_to_pdf` output):
1. `sly_data["output_dir"]`     ← preferred
2. `sly_data["workspace_dir"]`  ← fallback
3. `sly_data["project_folder"]` ← BidMagic/DealCraft backward-compat
4. `COMMON_OUTPUT_DIR` env var
5. `COMMON_WORKSPACE_DIR` env var
6. Current working directory    ← last resort (logged as warning)

### Path rules

**Read tools:**
- Relative paths → resolved against `input_dir`
- **Absolute paths allowed** — for Flask upload folders outside the workspace  
  e.g. `C:/my-projects/bidmagic/uploads/rfp.pdf`

**Write tools:**
- Path must be **relative** — e.g. `outputs/report.docx`, not `C:/...`
- `..` traversal that escapes the output directory is **rejected**
- Parent directories are **auto-created** on write

### Typical directory structure

```
<input_dir>/               ← Flask uploads land here; agents read from here
├── rfp.pdf
├── client_deck.pptx
└── data.xlsx

<output_dir>/              ← agents write results here
├── outputs/
│   ├── proposal.docx
│   ├── proposal.pdf
│   └── pricing.xlsx
└── logs/
    └── tool_calls.log     ← every tool call logged automatically
```

### Backward compatibility

Existing networks that only set `workspace_dir` (or `project_folder`) continue to work unchanged — both `input_dir` and `output_dir` fall through to `workspace_dir`.

---

## Large files — slicing and truncation hints

All read tools cap output at **64 KB**. When a file exceeds this, the response
includes an exact hint telling the agent what parameters to use on the next call.
The agent must follow the hint and call again — it never needs to guess.

### Truncation hint format

```
[TRUNCATED — N item(s) not shown. Call again with start_X=Y]
```

Where `X` and `Y` depend on the tool:

| Tool | Slice parameters | Hint example |
|---|---|---|
| `read_file` | `start_line`, `end_line` | `Call again with start_line=450` |
| `read_pdf` | `start_page`, `end_page` | `Call again with start_page=8` |
| `read_docx` | `start_para`, `end_para` | `Call again with start_para=120` |
| `read_pptx` | `start_slide`, `end_slide` | `Call again with start_slide=15` |
| `read_xlsx` | `start_row`, `max_rows` | `Call again with start_row=501` |

### How an agent should handle truncation

```
1. Call read_pdf(path="rfp.pdf") → reads pages 1–7, returns [TRUNCATED ... Call again with start_page=8]
2. Call read_pdf(path="rfp.pdf", start_page=8) → reads pages 8–14, returns [TRUNCATED ... Call again with start_page=15]
3. Call read_pdf(path="rfp.pdf", start_page=15) → reads remaining pages, no truncation marker
```

### Agent prompt guidance

Include this in agent instructions when the agent reads large files:

> "If a read tool returns `[TRUNCATED ...]`, follow the hint immediately and call the same tool again with the parameters shown. Continue until you receive a response with no truncation marker."

---

## Append modes — writing large outputs in chunks

LLM tool-call output is typically limited to ~8 KB per call.
For large documents, use `mode="append"` to build files across multiple calls.

### write_file — text chunking

```
call 1 → write_file(path="outputs/report.md", content="# Section 1\n...", mode="write")
call 2 → write_file(path="outputs/report.md", content="# Section 2\n...", mode="append")
call 3 → write_file(path="outputs/report.md", content="# Section 3\n...", mode="append")
```

### write_docx — append paragraphs/tables/headings

```
call 1 → write_docx(path="outputs/proposal.docx", content="# Executive Summary\n...", mode="write")
call 2 → write_docx(path="outputs/proposal.docx", content="## Section 2\n...", mode="append")
```

- `mode="write"` — creates a fresh document from the Cognizant template
- `mode="append"` — opens the existing `.docx` and adds content at the end

### write_pptx — append slides

```
call 1 → write_pptx(path="outputs/deck.pptx", content="=== COVER: Title | Sub ===\n=== Slide 1 ===\n...", mode="write")
call 2 → write_pptx(path="outputs/deck.pptx", content="=== Slide 6 ===\n...\n=== CLOSING: Thanks ===", mode="append")
```

- `mode="write"` — creates a fresh presentation from the Cognizant template
- `mode="append"` — opens the existing `.pptx` and adds new slides at the end

### write_xlsx — three modes

| Mode | What it does |
|---|---|
| `write` (default) | Create new file (or overwrite existing) |
| `append_sheet` | Add a new named sheet to an existing workbook |
| `append_rows` | Add rows to an existing sheet (skips re-writing the header) |

```
# First call — creates file with Pricing sheet
write_xlsx(path="outputs/model.xlsx", sheet="Pricing", content="...", mode="write")

# Second call — adds a second sheet
write_xlsx(path="outputs/model.xlsx", sheet="Assumptions", content="...", mode="append_sheet")

# Third call — adds more data rows to an existing sheet
write_xlsx(path="outputs/model.xlsx", sheet="Pricing", content="new,row,data", mode="append_rows")
```

---

## How to add a tool to your network

### Step 1 — Add the tool block to your HOCON

Each tool's `.py` file has a ready-to-paste HOCON block in its module docstring.
Example — adding `read_pdf` and `write_docx` to an agent:

```hocon
{
    "name": "read_pdf",
    "class": "coded_tools.common.read_pdf.ReadPdf",
    "function": {
        "description": "Extract text from a PDF file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path":       { "type": "string",  "description": "Path to the PDF (input_dir-relative or absolute)." },
                "start_page": { "type": "integer", "description": "1-based start page (optional)." },
                "end_page":   { "type": "integer", "description": "1-based end page, inclusive (optional)." },
                "agent":      { "type": "string",  "description": "Calling agent name (audit log)." }
            },
            "required": ["path"]
        }
    }
}
```

### Step 2 — Add to your agent's `"tools"` list

```hocon
{
    "name": "my_agent",
    "instructions": "...",
    "tools": ["read_pdf", "read_xlsx", "write_docx", "write_file"]
}
```

### Step 3 — Set directory keys in sly_data (from your Flask app)

```python
# Option A — separate input and output directories (recommended)
sly_data = {
    "input_dir":  "/c/my-projects/myapp/uploads",   # where agents READ from
    "output_dir": "/c/my-projects/myapp/outputs",   # where agents WRITE to
}

# Simple/legacy — single workspace directory (still works)
sly_data = {
    "workspace_dir": "/c/my-projects/myapp/workspace",
}
```

> **Backward compat:** Tools also check `project_folder` in sly_data,
> so BidMagic / DealCraft networks work without changes.

---

## Tool return conventions

All tools return `str`. The agent reads this directly.

| Prefix | Meaning |
|---|---|
| `OK: ...` | Success with a summary |
| `NOT_FOUND: ...` | File/path does not exist |
| `EMPTY: ...` | Directory exists but is empty |
| `Error: ...` | Something failed — agent should handle or retry |
| `[TRUNCATED ...]` | Output was too large — follow the hint to call again with next range |
| `[WARNING ...]` | Soft limit hit; result may be incomplete |

---

## Per-tool reference with examples

---

### `list_files`
**Class:** `coded_tools.common.list_files.ListFiles`  
**What it does:** List files in the input or output directory. Optional glob pattern filter.

```
Parameters:
  path     (optional, default ".")       — sub-path to list, relative to the chosen directory
  dir      (optional, default "input")   — "input" (uploaded files) or "output" (generated files)
  pattern  (optional)                    — glob filter, e.g. "*.pdf" or "*.md"
  agent    (optional)                    — for audit log

Returns: newline-separated list of relative file paths
         EMPTY: if directory exists but contains no matching files
```

**Examples:**
```
# List all input files (uploaded)
list_files(agent="my-agent")

# List all PDFs in the input directory
list_files(pattern="*.pdf", agent="my-agent")

# List all files the agent has written to outputs
list_files(dir="output", agent="my-agent")

# List Excel files in a sub-folder of inputs
list_files(path="data/", pattern="*.xlsx", agent="my-agent")
```

---

### `read_file`
**Class:** `coded_tools.common.read_file.ReadFile`  
**What it does:** Read any **text** file. Line-range slicing for large files.

```
Parameters:
  path        (required)  — relative path (resolved against input_dir), or absolute
  start_line  (optional)  — 1-based line to start from
  end_line    (optional)  — 1-based line to stop at (inclusive)
  agent       (optional)  — for audit log

Returns: file content as string (capped at 64 KB)
         [TRUNCATED — N lines not shown. Call again with start_line=X] if file exceeds 64 KB
```

**Examples:**
```
# Read a whole file
read_file(path="config.json", agent="my-agent")

# Read lines 50–150 of a large log
read_file(path="run.log", start_line=50, end_line=150, agent="my-agent")

# Continue after truncation: response said "Call again with start_line=451"
read_file(path="analysis.md", start_line=451, agent="my-agent")
```

---

### `write_file`
**Class:** `coded_tools.common.write_file.WriteFile`  
**What it does:** Write or append **text** to a file. Use `mode="append"` for chunked writes.

```
Parameters:
  path     (required)                  — relative path in output_dir (auto-creates parent dirs)
  content  (required)                  — text to write
  mode     (optional, default "write") — "write" (overwrite) or "append"
  agent    (optional)                  — for audit log

Returns: "OK: wrote/appended to 'path' (+N bytes, file now M bytes total)."
Limit:   Warn at >15 KB per call — split into chunks using mode="append"
```

**Examples:**
```
# Write a markdown report
write_file(path="outputs/summary.md", content="# Summary\n...", agent="my-agent")

# First chunk of a large document
write_file(path="outputs/report.md", content="# Section 1\n...", mode="write", agent="my-agent")

# Subsequent chunks
write_file(path="outputs/report.md", content="# Section 2\n...", mode="append", agent="my-agent")
write_file(path="outputs/report.md", content="# Section 3\n...", mode="append", agent="my-agent")
```

---

### `read_pdf`
**Class:** `coded_tools.common.read_pdf.ReadPdf`  
**What it does:** Extract text from a PDF file. Page markers inserted. Supports page-range slicing.

```
Parameters:
  path        (required)  — PDF path (input_dir-relative or absolute)
  start_page  (optional)  — 1-based page number to start from
  end_page    (optional)  — 1-based page number to stop at (inclusive)
  agent       (optional)  — for audit log

Returns: extracted text with "--- Page N ---" markers (capped at 64 KB)
         [TRUNCATED — N page(s) not shown. Call again with start_page=X]
Library: pdfplumber
```

**Examples:**
```
# Read an entire RFP
read_pdf(path="rfp.pdf", agent="rfp-analyst")

# Read pages 5 to 20 of a large document
read_pdf(path="annual_report.pdf", start_page=5, end_page=20, agent="my-agent")

# Read an uploaded file by absolute path (Flask upload)
read_pdf(path="C:/my-projects/bidmagic/uploads/tender_doc.pdf", agent="bid-agent")

# Handle truncation — response said "Call again with start_page=8"
read_pdf(path="rfp.pdf", start_page=8, agent="rfp-analyst")
```

---

### `read_docx`
**Class:** `coded_tools.common.read_docx.ReadDocx`  
**What it does:** Extract text from a Word document. Headings formatted as `#` / `##` / `###`. Tables as pipe-separated rows. Block-range slicing for large documents.

```
Parameters:
  path        (required)  — .docx path (input_dir-relative or absolute)
  start_para  (optional)  — 1-based block to start from (paragraphs + tables both count as blocks)
  end_para    (optional)  — 1-based block to stop at, inclusive
  agent       (optional)  — for audit log

Returns: structured text — headings, paragraphs, tables (capped at 64 KB)
         [TRUNCATED — N block(s) not shown. Call again with start_para=X]
Library: python-docx
```

**Examples:**
```
# Read a requirements document
read_docx(path="requirements.docx", agent="business-analyst")

# Read an uploaded SOW
read_docx(path="C:/my-projects/bidmagic/uploads/sow.docx", agent="bid-agent")

# Handle truncation — response said "Call again with start_para=85"
read_docx(path="requirements.docx", start_para=85, agent="business-analyst")
```

**Sample output:**
```
# Executive Summary
This proposal addresses the requirements outlined in the RFP dated March 2026.

## Section 1: Scope of Work
The engagement covers three workstreams...

[Table 1]
|Phase|Duration|Resources|
|Discovery|4 weeks|2 consultants|
|Design|6 weeks|3 consultants|
```

---

### `read_pptx`
**Class:** `coded_tools.common.read_pptx.ReadPptx`  
**What it does:** Extract per-slide text + speaker notes from a PowerPoint file. Slide-range slicing.

```
Parameters:
  path          (required)               — .pptx path (input_dir-relative or absolute)
  start_slide   (optional)               — 1-based slide to start from
  end_slide     (optional)               — 1-based slide to stop at (inclusive)
  include_notes (optional, default true) — include speaker notes
  agent         (optional)               — for audit log

Returns: slide-by-slide text with "=== Slide N: Title ===" markers (capped at 64 KB)
         [TRUNCATED — N slide(s) not shown. Call again with start_slide=X]
Library: python-pptx
```

**Examples:**
```
# Read a full pitch deck
read_pptx(path="pitch_deck.pptx", agent="presentation-analyst")

# Read slides 3 to 10 of a large deck
read_pptx(path="deck.pptx", start_slide=3, end_slide=10, agent="my-agent")

# Read without speaker notes
read_pptx(path="deck.pptx", include_notes=false, agent="my-agent")

# Handle truncation — response said "Call again with start_slide=15"
read_pptx(path="pitch_deck.pptx", start_slide=15, agent="presentation-analyst")
```

**Sample output:**
```
=== Slide 1: Cognizant Proposal for Acme Corp ===
Confidential | May 2026

=== Slide 2: Agenda ===
1. Understanding your challenges
2. Our proposed approach
3. Team and credentials
[Notes: Spend 2 minutes on this slide. Ask if they have any upfront questions.]
```

---

### `read_xlsx`
**Class:** `coded_tools.common.read_xlsx.ReadXlsx`  
**What it does:** Read Excel sheet data as CSV-formatted text. Row-range slicing for large sheets.

```
Parameters:
  path      (required)              — .xlsx path (input_dir-relative or absolute)
  sheet     (optional)              — sheet name, 1-based index, or "list" to see all sheets
  start_row (optional, default 1)   — 1-based row to start from (row 1 = header)
  max_rows  (optional, default 500) — maximum rows to return per call
  agent     (optional)              — for audit log

Returns: CSV-formatted text (header row first) or sheet list (capped at 64 KB)
         [TRUNCATED — more rows exist. Call again with start_row=X]
Library: openpyxl
```

**Examples:**
```
# Read the first (active) sheet
read_xlsx(path="price_list.xlsx", agent="estimator")

# Read a specific sheet by name
read_xlsx(path="financials.xlsx", sheet="Q1 2026", agent="analyst")

# List all sheets first, then read the right one
read_xlsx(path="workbook.xlsx", sheet="list", agent="my-agent")
# Returns: Sheets in 'workbook.xlsx':
#   1. Summary
#   2. Detail
#   3. Assumptions

# Handle truncation — response said "Call again with start_row=501"
read_xlsx(path="big_data.xlsx", sheet="Transactions", start_row=501, agent="my-agent")
```

**Sample output:**
```
Region,Product,Q1 Sales,Q2 Sales,Total
North,Platform A,450000,520000,970000
South,Platform A,310000,380000,690000
East,Platform B,280000,295000,575000
```

---

### `write_docx`
**Class:** `coded_tools.common.write_docx.WriteDocx`  
**What it does:** Create or append to a Word (.docx) file from markdown-like structured text. Uses Cognizant template by default.

```
Parameters:
  path          (required)                   — relative path in output_dir (e.g. "outputs/report.docx")
  content       (required)                   — markdown-like text (see syntax below)
  title         (optional)                   — document title, added as a cover heading (write mode only)
  mode          (optional, default "write")  — "write" (create fresh from template) or
                                               "append" (add content to existing file)
  template_path (optional)                   — override the Cognizant template (write mode only)
  agent         (optional)                   — for audit log

Returns: "OK: wrote/appended to 'path' (N bytes)."
Library: python-docx

Content syntax:
  # Heading 1      → Word Heading 1
  ## Heading 2     → Word Heading 2
  ### Heading 3    → Word Heading 3
  - bullet item    → Bullet list
  * bullet item    → Bullet list
  |col1|col2|col3| → Table row (first row = bold header)
  ---              → Page break
  blank line       → ignored (paragraphs auto-spaced)
  anything else    → Normal paragraph
```

**Examples:**
```
# Write a simple analysis report
write_docx(
    path="outputs/analysis.docx",
    title="RFP Analysis — Acme Corp",
    content="""
# Executive Summary
Cognizant recommends bidding on this opportunity. Win probability: High.

## Key Findings
- Budget aligns with our T&M model
- Timeline is aggressive but achievable

## Scoring Summary
|Criterion|Score|Weight|
|Technical fit|8/10|30%|
|Commercial fit|7/10|25%|
""",
    agent="bid-qualification-agent"
)

# Append a second section to the same document
write_docx(
    path="outputs/analysis.docx",
    content="""
## Competitive Landscape
- TCS and Infosys likely to bid
- Our differentiator: pre-built AI accelerators
""",
    mode="append",
    agent="bid-qualification-agent"
)
```

---

### `write_pptx`
**Class:** `coded_tools.common.write_pptx.WritePptx`  
**What it does:** Create or append slides to a Cognizant-branded PowerPoint. Uses `Cognizant_Template.pptx` by default.

```
Parameters:
  path           (required)                   — relative path in output_dir (e.g. "outputs/deck.pptx")
  content        (required)                   — slide content using slide-marker syntax (see below)
  mode           (optional, default "write")  — "write" (create fresh from template) or
                                                "append" (add slides to existing file)
  template_path  (optional)                   — override the Cognizant template (write mode only)
  agent          (optional)                   — for audit log

Returns: "OK: wrote/appended slides to 'path' — N slides, M bytes."
Library: python-pptx

Slide syntax:
  === COVER: Title | Subtitle ===    → Cover slide (dark bg, white text, layout 3)
  === DIVIDER: Section Title ===     → Section divider (dark gradient, layout 1)
  === CLOSING: Message ===           → Closing slide (light bg, layout 0)
  === Slide Title ===                → Standard content slide (light bg, layout 2)
  - bullet text                      → Bullet point on the current slide
  * bullet text                      → Bullet point on the current slide
  Plain text                         → Body paragraph on the current slide
```

**Examples:**
```
# First batch of slides
write_pptx(
    path="outputs/proposal.pptx",
    content="""
=== COVER: Cognizant Proposal for Acme Corp | Digital Transformation — May 2026 ===

=== DIVIDER: Understanding Your Challenges ===

=== Acme Corp — Current State ===
- Legacy ERP causing 30% operational inefficiency
- No real-time supply chain visibility

=== Our Proposed Approach ===
- Phase 1: Discovery & Design (4 weeks)
- Phase 2: Core Platform Build (12 weeks)
""",
    agent="proposal-writer"
)

# Append closing slides to the same deck
write_pptx(
    path="outputs/proposal.pptx",
    content="""
=== Why Cognizant ===
- 500+ SAP implementations globally
- Pre-built accelerators reduce timeline by 30%

=== CLOSING: Thank You — Let's Build the Future Together ===
""",
    mode="append",
    agent="proposal-writer"
)
```

---

### `write_xlsx`
**Class:** `coded_tools.common.write_xlsx.WriteXlsx`  
**What it does:** Write tabular data (CSV text or JSON array) to an Excel file. Auto-formats header row and column widths. Three write modes.

```
Parameters:
  path     (required)                   — relative path in output_dir
  content  (required)                   — CSV text OR JSON array of arrays/objects
  sheet    (optional, default "Sheet1") — sheet name
  mode     (optional, default "write")  — "write" (create/overwrite file)
                                          "append_sheet" (add new sheet to existing file)
                                          "append_rows" (add rows to existing sheet)
  agent    (optional)                   — for audit log

Returns: "OK: wrote/appended to 'path' — sheet='X', N rows (M bytes)."
Library: openpyxl
Header row: bold white text on navy blue background (#0033A0)
```

**Examples:**
```
# Write a pricing table from CSV text
write_xlsx(
    path="outputs/pricing.xlsx",
    sheet="Pricing",
    content="""Role,Level,Daily Rate,Days,Total
Solution Architect,Senior,850,30,25500
Business Analyst,Mid,650,45,29250""",
    agent="estimator-agent"
)

# Append a second sheet to the same workbook
write_xlsx(
    path="outputs/pricing.xlsx",
    sheet="Assumptions",
    mode="append_sheet",
    content="""Assumption,Value
Exchange rate USD/INR,83.5
Inflation adjustment,3%""",
    agent="commercial-agent"
)

# Append more data rows to an existing sheet (header skipped automatically)
write_xlsx(
    path="outputs/pricing.xlsx",
    sheet="Pricing",
    mode="append_rows",
    content="""QA Engineer,Mid,600,30,18000
PM,Senior,900,90,81000""",
    agent="estimator-agent"
)

# Write from JSON array of objects
write_xlsx(
    path="outputs/risks.xlsx",
    sheet="Risks",
    content='[{"Risk":"Timeline slippage","Probability":"High","Impact":"High"},{"Risk":"Scope creep","Probability":"Medium","Impact":"High"}]',
    agent="risk-agent"
)
```

---

### `convert_to_pdf`
**Class:** `coded_tools.common.convert_to_pdf.ConvertToPdf`  
**What it does:** Convert a Word (.docx) file to PDF using the Microsoft Word COM API.

```
Parameters:
  input_path   (required)  — source .docx (input_dir-relative or absolute)
  output_path  (optional)  — destination .pdf (output_dir-relative)
                             Default: same folder as input, .pdf extension
  agent        (optional)  — for audit log

Returns: "OK: converted 'input' → 'output' (N bytes)."
Requires: Microsoft Word installed on the Neuro SAN server (Windows only)
Library:  docx2pdf

Typical agent workflow:
  1. write_docx  → create outputs/report.docx
  2. convert_to_pdf → create outputs/report.pdf
  3. Return PDF path to Flask app for download
```

**Examples:**
```
# Convert and save alongside the DOCX
convert_to_pdf(input_path="outputs/proposal.docx", agent="proposal-writer")
# → outputs/proposal.pdf

# Convert to a specific output path
convert_to_pdf(
    input_path="outputs/draft.docx",
    output_path="outputs/final/report_v1.pdf",
    agent="report-agent"
)

# Convert an uploaded DOCX (absolute path) and save to output_dir
convert_to_pdf(
    input_path="C:/my-projects/bidmagic/uploads/client_template.docx",
    output_path="outputs/converted_template.pdf",
    agent="document-agent"
)
```

---

### `search_web`
**Class:** `coded_tools.common.search_web.SearchWeb`  
**What it does:** Search DuckDuckGo and return a numbered list of results (title, URL, snippet).

```
Parameters:
  query       (required)             — search query string
  max_results (optional, default 5)  — number of results (max 20)
  region      (optional, default "wt-wt") — region code: "in-en" (India), "us-en" (US)
  timelimit   (optional)             — "d" (day), "w" (week), "m" (month), "y" (year)
  agent       (optional)             — for audit log

Returns: numbered list of title / URL / snippet
No API key required. Calls DuckDuckGo via the ddgs package.
```

**Examples:**
```
# Company research
search_web(query="Acme Corp annual revenue 2025 2026", max_results=5, agent="research-agent")

# Recent news
search_web(query="TCS Q4 2026 results earnings", timelimit="m", agent="competitive-intel-agent")

# Technology landscape
search_web(query="Anthropic Claude API pricing models 2026", max_results=5, agent="my-agent")
```

---

### `ai_search`
**Class:** `coded_tools.common.ai_search.AiSearch`  
**What it does:** DuckDuckGo search + AI synthesis via LiteLLM proxy. Returns a focused, cited answer instead of raw links.

```
Parameters:
  query       (required)             — search query
  purpose     (optional)             — context for AI synthesis (makes answer more targeted)
  max_results (optional, default 8)  — search results to synthesise from (max 15)
  timelimit   (optional)             — "d", "w", "m" — time filter
  agent       (optional)             — for audit log

Returns: synthesised answer with inline [1][2] citations + URL list
Fallback: if LiteLLM proxy is unreachable → returns raw search results
Requires: LiteLLM proxy running on localhost:4000
```

**Examples:**
```
# Competitive intelligence with purpose context
ai_search(
    query="Infosys key differentiators and win themes 2026",
    purpose="Writing the competitive analysis section of a Cognizant bid response",
    agent="competitive-intel-agent"
)

# Recent technology news
ai_search(
    query="Pega GenAI features release 2026",
    purpose="Identifying new Pega capabilities to reference in a proposal",
    timelimit="m",
    agent="pega-agent"
)
```

---

### `ocr_image`
**Class:** `coded_tools.common.ocr_image.OcrImage`  
**What it does:** Extract text and details from an image file using Claude vision. Accepts input_dir-relative or absolute paths.

```
Parameters:
  path    (required)                — image path (input_dir-relative or absolute)
  model   (optional, default "haiku") — model to use:
            "haiku"  — fast + cheap (clean screenshots, printed text, clear diagrams)
            "sonnet" — better (dense layouts, low-res scans, mixed text+graphics)
            "opus"   — best (handwriting, damaged docs, complex technical diagrams)
  prompt  (optional)                — custom extraction instruction
  agent   (optional)                — for audit log

Returns: extracted text / description as plain string
Formats: .jpg .jpeg .png .gif .webp
Note:    Calls Anthropic API directly — NOT through LiteLLM proxy.
         ANTHROPIC_API_KEY must be set.
```

**Examples:**
```
# Extract all text from a screenshot
ocr_image(path="screenshot.png", agent="my-agent")

# Read an invoice with sonnet for better accuracy
ocr_image(path="invoice.jpg", model="sonnet", agent="finance-agent")

# Read an uploaded architecture diagram (absolute path)
ocr_image(
    path="C:/my-projects/bidmagic/uploads/client_architecture.png",
    model="sonnet",
    prompt="List every component, service, and integration arrow in this architecture diagram",
    agent="architect-agent"
)

# Extract requirement IDs from a scanned form
ocr_image(
    path="rfp_appendix_scan.png",
    model="haiku",
    prompt="Extract all requirement IDs and their text. Format as REQ-001: <text>",
    agent="rfp-analyst"
)
```

---

## Audit log

Every common tool automatically writes to:
```
<log_dir>/tool_calls.log        ← if sly_data["log_dir"] is set (recommended)
<output_dir>/logs/tool_calls.log ← fallback when log_dir is not set
```

**Always set `log_dir`** to a per-deal or per-project path so logs
don't accumulate in a single global file. Example for a Flask app:

```python
sly_data["log_dir"] = os.path.join(BASE_DIR, "repository", f"{deal_id}_{client}", "logs")
# → repository/5_acme/logs/tool_calls.log
```

Format:
```
2026-05-27 10:30:00  ReadPdf       agent=rfp-analyst              OK      rfp.pdf  | 45 pages total
2026-05-27 10:30:15  AiSearch      agent=competitive-intel-agent  OK      Infosys 2026 differentiators  | synthesised from 8 results
2026-05-27 10:31:02  WriteDocx     agent=proposal-writer-agent    OK      outputs/proposal.docx  | write: 24680 bytes (Cognizant template)
2026-05-27 10:31:20  WriteXlsx     agent=estimator-agent          OK      outputs/pricing.xlsx  | mode=write, sheet='Pricing', 12 rows, 8192 bytes
2026-05-27 10:31:45  OcrImage      agent=architect-agent          OK      architecture.png  | model=sonnet, 1842 chars extracted
```

---

## How to write a new shared coded tool

Follow these rules so your tool is consistent with the library.

### 1. File location
```
coded_tools/common/my_tool.py
```

### 2. Class structure
```python
from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.common._base import log_call, resolve_input_path, resolve_output_path

class MyTool(CodedTool):
    async def async_invoke(self, args: dict, sly_data: dict) -> str:
        agent = (args.get("agent") or "unknown-agent").strip()
        ...
        log_call(sly_data, tool="MyTool", agent=agent, target=..., status="OK", detail=...)
        return "OK: ..."
```

### 3. HOCON class reference
```
"class": "coded_tools.common.my_tool.MyTool"
```

### 4. Module docstring must include
- What the tool does (1 paragraph)
- The HOCON class reference line
- A complete, copy-paste-ready HOCON tool block
- `sly_data keys read` section listing `input_dir`/`output_dir` as appropriate

### 5. Return conventions
- Always return `str`
- Success: `"OK: ..."` or return the data directly (for read/search tools)
- Errors: `"Error: <message>"` — the calling agent will see this and can retry
- Never raise exceptions — catch all errors and return `"Error: ..."`

### 6. Path resolution for new file tools

```python
import os
from coded_tools.common._base import resolve_input_path, resolve_output_path

# READ tools — absolute paths allowed (for Flask upload folders)
abs_path = resolve_input_path(path_raw, sly_data)

# WRITE tools — strict sandbox (relative paths only, no ".." traversal)
abs_path = resolve_output_path(path_raw, sly_data)   # raises ValueError if invalid
```

### 7. Truncation hints — tell the agent exactly what to call next

```python
# BAD — vague, agent must guess
content += "\n\n[TRUNCATED at 64KB]"

# GOOD — agent can call again without guessing
next_page = last_page + 1
content += f"\n\n[TRUNCATED — {remaining} page(s) not shown. Call again with start_page={next_page}]"
```

### 8. Update this file
Add your tool to the **Available tools** table and the **File type support** table.
Add a **Per-tool reference** section with examples.

---

## What NOT to do

| ❌ Don't | ✅ Do instead |
|---|---|
| Copy `write_file.py` into your network folder | Use `"class": "coded_tools.common.write_file.WriteFile"` |
| Hardcode absolute paths in agent instructions | Use relative paths — directory root is set by sly_data |
| Use `project_folder` as the key in new networks | Use `input_dir`/`output_dir` — `project_folder` is legacy |
| Put API keys in tool code | Read from env vars |
| Raise exceptions from a tool | Catch all errors; return `"Error: ..."` |
| Write >8 KB in one `write_file` call | Use chunked writes with `mode="append"` |
| Start Neuro SAN with `python -m run` | Use `python start_neuro_san.py` (starts LiteLLM first) |
| Use `read_file` on PDFs / DOCX / XLSX | Use the format-specific tool (`read_pdf`, `read_docx`, `read_xlsx`) |
| Use `get_workspace()` in new tools | Use `get_input_dir()` or `get_output_dir()` — `get_workspace()` is legacy |
| Return `[TRUNCATED at NKB]` | Return `[TRUNCATED — N items not shown. Call again with start_X=Y]` |

---

## Network folder convention

Every project gets its **own subfolder** inside `registries/`. Do not put
project HOCON files directly in `registries/` root — that's how we ended up
with a flat pile of unrelated files.

### Standard layout

```
neuro-san-studio/
├── registries/
│   ├── llm_config.hocon          ← shared LLM config (not project-specific)
│   ├── manifest.hocon            ← lists every active network
│   ├── sdlc_pipeline/            ← ✅ reference implementation
│   │   └── sdlc_pipeline.hocon
│   ├── bidmagic/                 ← one folder per Flask app / product
│   │   ├── dealcraft_qualification.hocon
│   │   ├── dealcraft_research.hocon
│   │   ├── dealcraft_solution.hocon
│   │   ├── dealcraft_commercial.hocon
│   │   └── dealcraft_proposal.hocon
│   └── pega_automate/
│       └── pega_automate.hocon
│
├── coded_tools/
│   ├── common/                   ← shared tools (all networks)
│   └── <project>/                ← project-specific coded tools
│
└── agent_prompts/
    └── <project>/                ← markdown prompt files per project
```

### Rules

1. **One folder per project** — name matches the Flask app (`bidmagic/`, `appmagic/`, etc.)
2. **manifest.hocon entry** uses the subfolder path: `"bidmagic/dealcraft_qualification.hocon": true`
3. **`include` paths** inside a HOCON use `../` to reach shared config:  
   `include "../llm_config.hocon"`
4. **No HOCON files in `registries/` root** except `llm_config.hocon` and `manifest.hocon`

### manifest.hocon entry format

```hocon
# bidmagic phase networks
"bidmagic/dealcraft_qualification.hocon": true,
"bidmagic/dealcraft_research.hocon":      true,
```

---

## Migration guide — existing networks

### Switching to Option A (input/output split)

Old way (still works):
```python
sly_data = {"workspace_dir": "/path/to/workspace"}
```

New way (recommended for Flask apps):
```python
sly_data = {
    "input_dir":  "/path/to/app/uploads",
    "output_dir": "/path/to/app/outputs",
}
```

No HOCON changes needed — all tools fall through to `workspace_dir` if `input_dir`/`output_dir` are not set.

### Switching class references from network-specific to shared common

```hocon
# Before (network-specific copy)
"class": "coded_tools.bidmagic.write_file.WriteFile"

# After (shared common — gets all improvements automatically)
"class": "coded_tools.common.write_file.WriteFile"
```

---

*This is the single source of truth for `coded_tools/common/`.  
Update it whenever a new tool is added or an existing one changes.*
