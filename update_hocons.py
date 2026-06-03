"""
update_hocons.py — Replace file tool definitions in all 5 BidMagic HOCONs.

Changes per HOCON:
  • Replaces the write_file / read_file / list_files coded tool declarations
    with full function blocks + correct class paths (coded_tools.bidmagic.*)
  • Removes any reference to coded_tools.dealcraft.* or bare class declarations
"""
import os
import re

HOCON_DIR = "registries"
HOCON_FILES = [
    "dealcraft_qualification.hocon",
    "dealcraft_research.hocon",
    "dealcraft_solution.hocon",
    "dealcraft_commercial.hocon",
    "dealcraft_proposal.hocon",
]

# ── Canonical file-tools block ────────────────────────────────────────────────
# This replaces everything between the "# ── File tools" comment and the
# closing of the tools array.

FILE_TOOLS_BLOCK = '''
        # ── File tools (shared BidMagic coded tools) ─────────────────────────
        # Class path uses Phase-1 direct resolution: coded_tools.bidmagic.*
        # Do NOT shorten to write_file.WriteFile — that requires a matching
        # coded_tools/<network_name>/ folder which we do not want per network.
        {
            "name": "write_file",
            "function": {
                "description": "Write content to a file in the deal repository. Use mode='write' to create/overwrite; mode='append' to add to an existing file. For documents > ~3 000 chars, split into chunks: first call mode='write', subsequent calls mode='append' for the SAME path. All paths are relative to the repository root (project_folder in sly_data, which BidMagic sets to BASE_DIR).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path inside the deal repository — use the EXACT path from Section 6 of _context_index.md that is designated for YOUR agent. Do NOT write to another agent's path."
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write. Keep each chunk ≤ 3 000 chars when splitting large documents."
                        },
                        "mode": {
                            "type": "string",
                            "description": "'write' (default) — create or overwrite. 'append' — add to end of existing file. Always 'write' on the first call for a given path."
                        },
                        "agent": {
                            "type": "string",
                            "description": "Your agent name, e.g. 'bid-qualification-agent'. Written to the tool log."
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            "class": "coded_tools.bidmagic.write_file.WriteFile"
        },
        {
            "name": "read_file",
            "function": {
                "description": "Read a file from the deal repository and return its content. Use this to read _context_index.md (path given in the orchestrator message), client RFP files listed in Section 2, global learning files in Section 5, or prior phase outputs in Section 3. Returns NOT_FOUND if the file does not exist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path inside the deal repository, e.g. 'repository/5_acme/iter_1/01_qualification/_context_index.md'."
                        },
                        "agent": {
                            "type": "string",
                            "description": "Your agent name. Written to the tool log."
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Optional: first line to return (1-based). Use with end_line to slice large files."
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Optional: last line to return (inclusive). Use with start_line to slice large files."
                        }
                    },
                    "required": ["path"]
                }
            },
            "class": "coded_tools.bidmagic.read_file.ReadFile"
        },
        {
            "name": "list_files",
            "function": {
                "description": "List files under a folder in the deal repository. Returns a newline-separated list of paths relative to the repository root. Useful for discovering which client input files exist (browse repository/<deal>/client_inputs/ci_vN/) or verifying which agent outputs have been written.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Folder path relative to the repository root. Defaults to '.' (the entire repository). Tip: scope to a specific subfolder to avoid large listings."
                        },
                        "agent": {
                            "type": "string",
                            "description": "Your agent name. Written to the tool log."
                        }
                    }
                }
            },
            "class": "coded_tools.bidmagic.list_files.ListFiles"
        }
    ]
}'''

# Pattern that matches the file-tools section through end of file
# (covers both ── dash lengths used across the 5 HOCONs)
PATTERN = re.compile(
    r"""
        # \s*──\s*File\s+tools.*?  # comment line (any dash count)
        \{[^}]*"name"\s*:\s*"write_file"[^}]*\}  \s*,?\s*
        \{[^}]*"name"\s*:\s*"read_file"[^}]*\}   \s*,?\s*
        \{[^}]*"name"\s*:\s*"list_files"[^}]*\}  \s*
        \]\s*\}                                   # closes tools array and network object
    """,
    re.VERBOSE | re.DOTALL,
)

changed = 0
for fname in HOCON_FILES:
    fpath = os.path.join(HOCON_DIR, fname)
    if not os.path.exists(fpath):
        print(f"SKIP (not found): {fname}")
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content, n = PATTERN.subn(FILE_TOOLS_BLOCK, content)
    if n:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)
        changed += 1
        print(f"UPDATED ({n} replacement): {fname}")
    else:
        print(f"NO MATCH: {fname}")

print(f"\n{changed}/{len(HOCON_FILES)} HOCONs updated")
