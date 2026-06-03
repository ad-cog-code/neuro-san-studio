#!/usr/bin/env python3
"""
build_prompts.py — Assemble compiled agent prompts for AppMagic SDLC pipeline.

Each compiled prompt = appmagic-startforagent.md + [agent-body].md + appmagic-endforagent.md

Usage:
    python build_prompts.py              # Build all agents
    python build_prompts.py architect    # Build one agent (partial name match, case-insensitive)

Output:
    prompts/compiled/<agent>-prompt.md

HOCON `instructions` paths should point to:
    system-developer/prompts/compiled/<agent>-prompt.md
"""

import os
import sys

PROMPTS_DIR  = os.path.dirname(os.path.abspath(__file__))
COMPILED_DIR = os.path.join(PROMPTS_DIR, "compiled")
START_FILE   = os.path.join(PROMPTS_DIR, "appmagic-startforagent.md")
END_FILE     = os.path.join(PROMPTS_DIR, "appmagic-endforagent.md")

# Agent body filename → compiled output filename (same names, different folder)
AGENTS = [
    "doc-analyst-prompt.md",
    "industry-sme-prompt.md",
    "business-analyst-prompt.md",
    "product-owner-prompt.md",
    "architect-prompt.md",
    "adaptive-learner-prompt.md",
    "frontend-developer-prompt.md",
    "backend-developer-prompt.md",
    "workflow-developer-prompt.md",
    "neuro-ai-developer-prompt.md",
    "technical-writer-prompt.md",
    "qa-tester-prompt.md",
    "business-validator-prompt.md",
    "app-finisher-prompt.md",
    "orchestrator-prompt.md",
]

SEPARATOR = "\n\n---\n\n"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def build_one(agent_file: str) -> None:
    body_path = os.path.join(PROMPTS_DIR, agent_file)
    if not os.path.exists(body_path):
        print(f"  SKIP (file not found): {agent_file}")
        return

    start   = read(START_FILE)
    body    = read(body_path)
    end     = read(END_FILE)
    compiled = SEPARATOR.join([start, body, end])

    out_path = os.path.join(COMPILED_DIR, agent_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(compiled)

    kb = len(compiled) / 1024
    print(f"  Built: {agent_file:<45} ({kb:.1f} KB)")


def main() -> None:
    os.makedirs(COMPILED_DIR, exist_ok=True)

    filter_term = sys.argv[1].lower() if len(sys.argv) > 1 else None

    targets = (
        [f for f in AGENTS if filter_term in f.lower()]
        if filter_term else AGENTS
    )

    if not targets:
        print(f"No agents matched '{filter_term}'. Available agents:")
        for a in AGENTS:
            print(f"  {a}")
        sys.exit(1)

    print(f"Building {len(targets)} prompt(s) -> {COMPILED_DIR}\n")
    for agent_file in targets:
        build_one(agent_file)

    print(f"\nDone. Run the Neuro SAN server to pick up the new prompts."
          f"\nHOCON paths should point to: system-developer/prompts/compiled/<agent>-prompt.md")


if __name__ == "__main__":
    main()
