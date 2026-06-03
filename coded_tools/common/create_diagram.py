"""
coded_tools/common/create_diagram.py
══════════════════════════════════════
CreateDiagram — generate a flowchart / architecture diagram PNG from a
structured JSON description of nodes and edges.

Node types:
  box          — rectangle (default; process step, system component)
  diamond      — decision / gateway
  oval         — start / end / terminal
  cylinder     — database / storage
  parallelogram — input / output

Layout:
  Nodes are auto-arranged in layers using topological sort (BFS from source
  nodes). Direction can be "vertical" (top→bottom, default) or "horizontal"
  (left→right).

Content format (JSON):
  {
    "nodes": [
      {"id": "n1", "label": "Start",      "type": "oval"},
      {"id": "n2", "label": "Read RFP",   "type": "box"},
      {"id": "n3", "label": "Qualifies?", "type": "diamond"},
      {"id": "n4", "label": "Submit Bid", "type": "box"},
      {"id": "n5", "label": "End",        "type": "oval"}
    ],
    "edges": [
      {"from": "n1", "to": "n2"},
      {"from": "n2", "to": "n3"},
      {"from": "n3", "to": "n4", "label": "Yes"},
      {"from": "n3", "to": "n5", "label": "No"},
      {"from": "n4", "to": "n5"}
    ]
  }

Optional node fields:
  color  — fill colour (hex, e.g. "#06C7CC"); defaults to Cognizant palette
  row    — explicit row/layer override (0-based)
  col    — explicit column override within a row (0-based)

Output: PNG saved to output_dir.

HOCON class reference
──────────────────────
    "class": "coded_tools.common.create_diagram.CreateDiagram"

HOCON tool block (copy-paste into any network)
───────────────────────────────────────────────
    {
        "name": "create_diagram",
        "class": "coded_tools.common.create_diagram.CreateDiagram",
        "function": {
            "description": "Generate a flowchart or architecture diagram PNG from a JSON description of nodes and edges. Node types: box, diamond, oval, cylinder, parallelogram. Auto-arranges into layers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":      { "type": "string", "description": "Output PNG path, relative to output_dir (e.g. 'outputs/flow.png')." },
                    "content":   { "type": "string", "description": "JSON with 'nodes' (id, label, type, color) and 'edges' (from, to, label) arrays." },
                    "title":     { "type": "string", "description": "Diagram title shown at the top (optional)." },
                    "direction": { "type": "string", "description": "'vertical' (top-to-bottom, default) or 'horizontal' (left-to-right)." },
                    "width":     { "type": "number", "description": "Image width in inches (default 12)." },
                    "height":    { "type": "number", "description": "Image height in inches (default 8)." },
                    "agent":     { "type": "string", "description": "Calling agent name (audit log)." }
                },
                "required": ["path", "content"]
            }
        }
    }

sly_data keys read
───────────────────
    output_dir     (preferred) — where the PNG is saved
    workspace_dir  (fallback)
    project_folder (fallback)  — bidmagic/dealcraft compat
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import defaultdict, deque
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.common._base import log_call, resolve_output_path

logger = logging.getLogger(__name__)

# ── Brand palette ─────────────────────────────────────────────────────────────
NODE_COLORS = {
    "box":           "#2E308E",   # accent blue
    "diamond":       "#06C7CC",   # teal
    "oval":          "#000048",   # dark navy
    "cylinder":      "#7373D8",   # purple
    "parallelogram": "#4A90D9",   # sky blue
}
TEXT_COLOR   = "#FFFFFF"
EDGE_COLOR   = "#000048"
LABEL_COLOR  = "#000048"
BG_COLOR     = "#FFFFFF"
DPI          = 150

# Node geometry (in data units)
NODE_W  = 2.2
NODE_H  = 0.8
H_GAP   = 1.2   # horizontal gap between nodes in same layer
V_GAP   = 1.6   # vertical gap between layers


# ── Layout ────────────────────────────────────────────────────────────────────

def _assign_layers(nodes: list[dict], edges: list[dict]) -> dict[str, int]:
    """BFS topological layer assignment. Returns {node_id: layer}."""
    id_set = {n["id"] for n in nodes}
    in_edges = defaultdict(set)
    out_edges = defaultdict(set)
    for e in edges:
        if e["from"] in id_set and e["to"] in id_set:
            in_edges[e["to"]].add(e["from"])
            out_edges[e["from"]].add(e["to"])

    # Check explicit row overrides first
    layers: dict[str, int] = {}
    for n in nodes:
        if "row" in n:
            layers[n["id"]] = int(n["row"])

    # BFS from sources (no incoming edges) for remaining nodes
    sources = [n["id"] for n in nodes if not in_edges[n["id"]] and n["id"] not in layers]
    if not sources:
        sources = [nodes[0]["id"]]

    queue = deque()
    for s in sources:
        if s not in layers:
            layers[s] = 0
        queue.append(s)

    visited = set(layers.keys())
    while queue:
        nid = queue.popleft()
        for child in out_edges[nid]:
            new_layer = layers[nid] + 1
            if child not in layers or layers[child] < new_layer:
                layers[child] = new_layer
            if child not in visited:
                visited.add(child)
                queue.append(child)

    # Any unvisited nodes get the next available layer
    max_layer = max(layers.values(), default=0)
    for n in nodes:
        if n["id"] not in layers:
            max_layer += 1
            layers[n["id"]] = max_layer

    return layers


def _assign_positions(nodes: list[dict], layers: dict[str, int],
                      direction: str) -> dict[str, tuple[float, float]]:
    """Assign (x, y) centre positions for each node."""
    layer_members: dict[int, list[str]] = defaultdict(list)
    for n in nodes:
        layer_members[layers[n["id"]]].append(n["id"])

    # Apply explicit col overrides within a layer
    node_col: dict[str, int] = {}
    for n in nodes:
        if "col" in n:
            node_col[n["id"]] = int(n["col"])

    positions: dict[str, tuple[float, float]] = {}
    num_layers = max(layers.values(), default=0) + 1

    for layer_idx in range(num_layers):
        members = layer_members[layer_idx]
        # Sort by explicit col if given
        members.sort(key=lambda nid: node_col.get(nid, members.index(nid)))
        n_cols = len(members)
        total_w = n_cols * NODE_W + (n_cols - 1) * H_GAP
        start_x = -total_w / 2 + NODE_W / 2

        for col_idx, nid in enumerate(members):
            cx = start_x + col_idx * (NODE_W + H_GAP)
            cy = -layer_idx * (NODE_H + V_GAP)

            if direction == "horizontal":
                positions[nid] = (layer_idx * (NODE_W + V_GAP), -col_idx * (NODE_H + H_GAP))
            else:
                positions[nid] = (cx, cy)

    return positions


# ── Shape renderers ───────────────────────────────────────────────────────────

def _draw_box(ax, cx, cy, w, h, color, text, fontsize=8):
    rect = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.05",
        facecolor=color, edgecolor="white", linewidth=1.5, zorder=3
    )
    ax.add_patch(rect)
    ax.text(cx, cy, text, ha="center", va="center", color=TEXT_COLOR,
            fontsize=fontsize, fontweight="bold", zorder=4,
            wrap=True, multialignment="center")


def _draw_diamond(ax, cx, cy, w, h, color, text, fontsize=8):
    hw, hh = w / 2, h / 2 * 1.3
    diamond = plt.Polygon(
        [(cx, cy + hh), (cx + hw, cy), (cx, cy - hh), (cx - hw, cy)],
        closed=True, facecolor=color, edgecolor="white", linewidth=1.5, zorder=3
    )
    ax.add_patch(diamond)
    ax.text(cx, cy, text, ha="center", va="center", color=TEXT_COLOR,
            fontsize=fontsize - 1, fontweight="bold", zorder=4, multialignment="center")


def _draw_oval(ax, cx, cy, w, h, color, text, fontsize=8):
    ellipse = mpatches.Ellipse(
        (cx, cy), w * 1.1, h * 1.1,
        facecolor=color, edgecolor="white", linewidth=1.5, zorder=3
    )
    ax.add_patch(ellipse)
    ax.text(cx, cy, text, ha="center", va="center", color=TEXT_COLOR,
            fontsize=fontsize, fontweight="bold", zorder=4)


def _draw_cylinder(ax, cx, cy, w, h, color, text, fontsize=8):
    # Body
    rect = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.02",
        facecolor=color, edgecolor="white", linewidth=1.5, zorder=3
    )
    ax.add_patch(rect)
    # Top ellipse cap
    cap = mpatches.Ellipse((cx, cy + h / 2), w, h * 0.25,
                           facecolor=color, edgecolor="white", linewidth=1.5, zorder=4)
    ax.add_patch(cap)
    ax.text(cx, cy, text, ha="center", va="center", color=TEXT_COLOR,
            fontsize=fontsize, fontweight="bold", zorder=5)


def _draw_parallelogram(ax, cx, cy, w, h, color, text, fontsize=8):
    skew = w * 0.15
    para = plt.Polygon(
        [(cx - w / 2 + skew, cy + h / 2),
         (cx + w / 2 + skew, cy + h / 2),
         (cx + w / 2 - skew, cy - h / 2),
         (cx - w / 2 - skew, cy - h / 2)],
        closed=True, facecolor=color, edgecolor="white", linewidth=1.5, zorder=3
    )
    ax.add_patch(para)
    ax.text(cx, cy, text, ha="center", va="center", color=TEXT_COLOR,
            fontsize=fontsize, fontweight="bold", zorder=4)


def _draw_node(ax, ntype: str, cx, cy, color, text):
    fs = 8 if len(text) < 20 else 7
    if ntype == "diamond":
        _draw_diamond(ax, cx, cy, NODE_W, NODE_H, color, text, fs)
    elif ntype == "oval":
        _draw_oval(ax, cx, cy, NODE_W, NODE_H, color, text, fs)
    elif ntype == "cylinder":
        _draw_cylinder(ax, cx, cy, NODE_W, NODE_H, color, text, fs)
    elif ntype == "parallelogram":
        _draw_parallelogram(ax, cx, cy, NODE_W, NODE_H, color, text, fs)
    else:
        _draw_box(ax, cx, cy, NODE_W, NODE_H, color, text, fs)


def _edge_boundary(cx, cy, ntype: str, dx, dy):
    """Return the point on the node boundary closest to direction (dx, dy)."""
    if ntype == "diamond":
        hw, hh = NODE_W / 2, NODE_H / 2 * 1.3
    elif ntype == "oval":
        hw, hh = NODE_W / 2 * 1.1, NODE_H / 2 * 1.1
    else:
        hw, hh = NODE_W / 2, NODE_H / 2

    if abs(dy) < 1e-9:
        return (cx + np.sign(dx) * hw, cy)
    if abs(dx) < 1e-9:
        return (cx, cy + np.sign(dy) * hh)
    # Clip to box/ellipse boundary
    t_x = hw / abs(dx) if dx != 0 else float("inf")
    t_y = hh / abs(dy) if dy != 0 else float("inf")
    t = min(t_x, t_y)
    return (cx + dx * t, cy + dy * t)


def _draw_edge(ax, pos: dict, src_id: str, dst_id: str, src_type: str, dst_type: str,
               label: str = ""):
    sx, sy = pos[src_id]
    ex, ey = pos[dst_id]
    dx, dy = ex - sx, ey - sy
    dist = max((dx ** 2 + dy ** 2) ** 0.5, 1e-6)

    start = _edge_boundary(sx, sy, src_type, dx / dist, dy / dist)
    end   = _edge_boundary(ex, ey, dst_type, -dx / dist, -dy / dist)

    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=dict(
            arrowstyle="-|>",
            color=EDGE_COLOR,
            lw=1.4,
            mutation_scale=14,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=2,
    )

    if label:
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        ax.text(mx, my, label, ha="center", va="center",
                fontsize=7, color=LABEL_COLOR, style="italic",
                bbox=dict(facecolor=BG_COLOR, edgecolor="none", alpha=0.8, pad=1),
                zorder=5)


# ── Main class ────────────────────────────────────────────────────────────────

class CreateDiagram(CodedTool):
    """Generate a flowchart / architecture diagram PNG from JSON node+edge description."""

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        path_raw  = (args.get("path")      or "").strip()
        content   =  args.get("content")
        title     = (args.get("title")     or "").strip()
        direction = (args.get("direction") or "vertical").strip().lower()
        width     = float(args.get("width")  or 12)
        height    = float(args.get("height") or 8)
        agent     = (args.get("agent")     or "unknown-agent").strip()

        if not path_raw:
            return "Error: create_diagram requires 'path'."
        if not content:
            return "Error: create_diagram requires 'content'."
        if direction not in ("vertical", "horizontal"):
            direction = "vertical"
        if not path_raw.lower().endswith(".png"):
            path_raw += ".png"

        try:
            abs_path = resolve_output_path(path_raw, sly_data)
        except ValueError as exc:
            log_call(sly_data, tool="CreateDiagram", agent=agent, target=path_raw,
                     status="ERROR", detail=str(exc))
            return f"Error: {exc}"

        # Parse content
        try:
            spec = json.loads(content.strip())
            nodes: list[dict] = spec.get("nodes", [])
            edges: list[dict] = spec.get("edges", [])
            title = title or spec.get("title", "")
        except json.JSONDecodeError as exc:
            return f"Error: 'content' must be valid JSON with 'nodes' and 'edges' arrays: {exc}"

        if not nodes:
            return "Error: 'nodes' array is empty — nothing to draw."

        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # Layout
            layers    = _assign_layers(nodes, edges)
            positions = _assign_positions(nodes, layers, direction)
            node_map  = {n["id"]: n for n in nodes}

            # Canvas sizing
            all_x = [p[0] for p in positions.values()]
            all_y = [p[1] for p in positions.values()]
            pad = max(NODE_W, NODE_H) * 1.2
            xlim = (min(all_x) - pad, max(all_x) + pad)
            ylim = (min(all_y) - pad, max(all_y) + pad)

            fig, ax = plt.subplots(figsize=(width, height))
            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            ax.set_aspect("equal")
            ax.axis("off")

            # Draw edges first (behind nodes)
            for e in edges:
                src_id = e.get("from", "")
                dst_id = e.get("to", "")
                if src_id not in positions or dst_id not in positions:
                    continue
                src_type = node_map.get(src_id, {}).get("type", "box")
                dst_type = node_map.get(dst_id, {}).get("type", "box")
                _draw_edge(ax, positions, src_id, dst_id, src_type, dst_type,
                           label=e.get("label", ""))

            # Draw nodes
            for n in nodes:
                nid   = n["id"]
                ntype = n.get("type", "box").lower()
                label = n.get("label", nid)
                color = n.get("color") or NODE_COLORS.get(ntype, NODE_COLORS["box"])
                cx, cy = positions[nid]
                _draw_node(ax, ntype, cx, cy, color, label)

            # Title
            if title:
                fig.suptitle(title, color=LABEL_COLOR, fontsize=13,
                             fontweight="bold", y=0.98)

            fig.tight_layout()
            fig.savefig(abs_path, dpi=DPI, bbox_inches="tight", facecolor=BG_COLOR)
            plt.close(fig)
            file_size = os.path.getsize(abs_path)

        except Exception as exc:
            log_call(sly_data, tool="CreateDiagram", agent=agent, target=path_raw,
                     status="ERROR", detail=str(exc))
            logger.exception("CreateDiagram failed for %s", path_raw)
            return f"Error: failed to create diagram '{path_raw}': {exc}"

        detail = f"{len(nodes)} nodes, {len(edges)} edges, {file_size} bytes"
        log_call(sly_data, tool="CreateDiagram", agent=agent, target=path_raw,
                 status="OK", detail=detail)
        logger.debug("CreateDiagram: %s (%d nodes, %d edges, %d bytes)",
                     path_raw, len(nodes), len(edges), file_size)
        return f"OK: created '{path_raw}' — {len(nodes)} nodes, {len(edges)} edges, {file_size} bytes."

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)
