"""
coded_tools/common/create_chart.py
════════════════════════════════════
CreateChart — generate a chart image (PNG) from tabular data.

Supported chart types:
  bar            — vertical grouped bar chart
  horizontal_bar — horizontal grouped bar chart
  line           — line chart with optional markers
  pie            — pie chart
  donut          — donut chart (pie with centre hole)
  stacked_bar    — stacked vertical bar chart

Data format (same as write_xlsx / read_xlsx):
  CSV text  — first row = headers, column 0 = x-axis labels / pie labels
  JSON      — array of arrays or array of objects

Column mapping:
  bar / horizontal_bar / line / stacked_bar:
    column 0   → x-axis labels (categories)
    column 1+  → one series each
  pie / donut:
    column 0   → slice labels
    column 1   → slice values

Output: PNG saved to output_dir (or absolute path).

Cognizant brand colours used by default:
  #2E308E  accent blue  (primary)
  #06C7CC  teal
  #7373D8  purple
  #000048  dark navy
  #4A90D9  sky blue
  #F5A623  amber

HOCON class reference
──────────────────────
    "class": "coded_tools.common.create_chart.CreateChart"

HOCON tool block (copy-paste into any network)
───────────────────────────────────────────────
    {
        "name": "create_chart",
        "class": "coded_tools.common.create_chart.CreateChart",
        "function": {
            "description": "Generate a chart PNG from tabular data. Supports bar, horizontal_bar, line, pie, donut, stacked_bar. Data as CSV text (first row = headers) or JSON array.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":       { "type": "string",  "description": "Output PNG path, relative to output_dir (e.g. 'outputs/revenue_chart.png')." },
                    "data":       { "type": "string",  "description": "Tabular data as CSV text (first row = headers) or JSON array of arrays/objects." },
                    "chart_type": { "type": "string",  "description": "Chart type: bar (default), horizontal_bar, line, pie, donut, stacked_bar." },
                    "title":      { "type": "string",  "description": "Chart title (optional)." },
                    "x_label":    { "type": "string",  "description": "X-axis label for bar/line charts (optional)." },
                    "y_label":    { "type": "string",  "description": "Y-axis label for bar/line charts (optional)." },
                    "width":      { "type": "number",  "description": "Image width in inches (default 10)." },
                    "height":     { "type": "number",  "description": "Image height in inches (default 6)." },
                    "agent":      { "type": "string",  "description": "Calling agent name (audit log)." }
                },
                "required": ["path", "data"]
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
import csv
import io
import json
import logging
import os
from typing import Any

import matplotlib
matplotlib.use("Agg")   # non-interactive backend — must be set before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.common._base import log_call, resolve_output_path

logger = logging.getLogger(__name__)

# ── Cognizant brand palette ───────────────────────────────────────────────────
BRAND_COLORS = [
    "#2E308E",  # accent blue
    "#06C7CC",  # teal
    "#7373D8",  # purple
    "#4A90D9",  # sky blue
    "#F5A623",  # amber
    "#000048",  # dark navy
    "#50C878",  # emerald
    "#E74C3C",  # red (for contrast)
]
BG_COLOR   = "#FFFFFF"
TEXT_COLOR = "#000048"
GRID_COLOR = "#E8E8F0"
DPI        = 150


# ── Data parsing ──────────────────────────────────────────────────────────────

def _parse_data(content: str) -> list[list[str]]:
    """Parse CSV text or JSON into a list of rows (each row = list of str)."""
    stripped = content.strip()
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
            if not data:
                return []
            if isinstance(data[0], dict):
                headers = list(data[0].keys())
                rows = [headers]
                for obj in data:
                    rows.append([str(obj.get(h, "")) for h in headers])
                return rows
            return [[str(cell) for cell in row] for row in data]
        except json.JSONDecodeError:
            pass
    reader = csv.reader(io.StringIO(stripped))
    return [r for r in reader if any(c.strip() for c in r)]


def _to_float(val: str) -> float:
    try:
        return float(str(val).replace(",", "").strip())
    except ValueError:
        return 0.0


# ── Chart renderers ───────────────────────────────────────────────────────────

def _apply_style(fig, ax, title: str, x_label: str, y_label: str):
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.yaxis.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
    if x_label:
        ax.set_xlabel(x_label, color=TEXT_COLOR, fontsize=10)
    if y_label:
        ax.set_ylabel(y_label, color=TEXT_COLOR, fontsize=10)


def _bar_chart(rows: list[list[str]], title, x_label, y_label, width, height,
               horizontal=False, stacked=False) -> plt.Figure:
    headers = rows[0]
    data_rows = rows[1:]
    categories = [r[0] for r in data_rows]
    series_names = headers[1:]
    series_data = [[_to_float(r[i + 1]) if i + 1 < len(r) else 0.0
                    for r in data_rows] for i in range(len(series_names))]

    fig, ax = plt.subplots(figsize=(width, height))
    x = np.arange(len(categories))
    n = len(series_names)
    bar_w = 0.7 / max(n, 1) if not stacked else 0.5

    if stacked:
        bottoms = np.zeros(len(categories))
        for i, (name, vals) in enumerate(zip(series_names, series_data)):
            color = BRAND_COLORS[i % len(BRAND_COLORS)]
            if horizontal:
                ax.barh(x, vals, left=bottoms, color=color, label=name, height=0.5)
            else:
                ax.bar(x, vals, bottom=bottoms, color=color, label=name,
                       width=0.5, zorder=3)
            bottoms += np.array(vals)
    else:
        for i, (name, vals) in enumerate(zip(series_names, series_data)):
            offset = (i - (n - 1) / 2) * bar_w
            color = BRAND_COLORS[i % len(BRAND_COLORS)]
            if horizontal:
                ax.barh(x + offset, vals, color=color, label=name, height=bar_w * 0.9)
            else:
                ax.bar(x + offset, vals, width=bar_w * 0.9, color=color,
                       label=name, zorder=3)

    if horizontal:
        ax.set_yticks(x)
        ax.set_yticklabels(categories, color=TEXT_COLOR)
        ax.xaxis.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.7)
        ax.yaxis.grid(False)
    else:
        ax.set_xticks(x)
        ax.set_xticklabels(categories, color=TEXT_COLOR,
                           rotation=30 if len(categories) > 5 else 0, ha="right")

    _apply_style(fig, ax, title, x_label, y_label)
    if n > 1:
        ax.legend(fontsize=9, framealpha=0.8)
    fig.tight_layout()
    return fig


def _line_chart(rows: list[list[str]], title, x_label, y_label, width, height) -> plt.Figure:
    headers = rows[0]
    data_rows = rows[1:]
    categories = [r[0] for r in data_rows]
    series_names = headers[1:]
    series_data = [[_to_float(r[i + 1]) if i + 1 < len(r) else 0.0
                    for r in data_rows] for i in range(len(series_names))]

    fig, ax = plt.subplots(figsize=(width, height))
    x = np.arange(len(categories))
    markers = ["o", "s", "^", "D", "v", "P"]

    for i, (name, vals) in enumerate(zip(series_names, series_data)):
        color = BRAND_COLORS[i % len(BRAND_COLORS)]
        ax.plot(x, vals, marker=markers[i % len(markers)], color=color,
                label=name, linewidth=2, markersize=6, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, color=TEXT_COLOR,
                       rotation=30 if len(categories) > 5 else 0, ha="right")
    _apply_style(fig, ax, title, x_label, y_label)
    if len(series_names) > 1:
        ax.legend(fontsize=9, framealpha=0.8)
    fig.tight_layout()
    return fig


def _pie_chart(rows: list[list[str]], title, width, height, donut=False) -> plt.Figure:
    data_rows = rows[1:] if len(rows) > 1 and not _to_float(rows[0][1]) else rows
    labels = [r[0] for r in data_rows]
    values = [abs(_to_float(r[1])) if len(r) > 1 else 1.0 for r in data_rows]

    colors = [BRAND_COLORS[i % len(BRAND_COLORS)] for i in range(len(labels))]
    wedge_props = {"linewidth": 1.5, "edgecolor": "white"}

    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        wedgeprops=wedge_props,
        startangle=90,
        pctdistance=0.75 if donut else 0.6,
    )
    for t in texts:
        t.set_color(TEXT_COLOR)
        t.set_fontsize(9)
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(8)
        at.set_fontweight("bold")

    if donut:
        centre = plt.Circle((0, 0), 0.5, fc=BG_COLOR)
        ax.add_patch(centre)

    if title:
        ax.set_title(title, color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    return fig


# ── Main class ────────────────────────────────────────────────────────────────

CHART_TYPES = {"bar", "horizontal_bar", "line", "pie", "donut", "stacked_bar"}


class CreateChart(CodedTool):
    """Generate a chart PNG from tabular data using matplotlib."""

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        path_raw   = (args.get("path")       or "").strip()
        data_raw   =  args.get("data")
        chart_type = (args.get("chart_type") or "bar").strip().lower()
        title      = (args.get("title")      or "").strip()
        x_label    = (args.get("x_label")    or "").strip()
        y_label    = (args.get("y_label")    or "").strip()
        width      = float(args.get("width")  or 10)
        height     = float(args.get("height") or 6)
        agent      = (args.get("agent")      or "unknown-agent").strip()

        if not path_raw:
            return "Error: create_chart requires 'path'."
        if not data_raw:
            return "Error: create_chart requires 'data'."
        if chart_type not in CHART_TYPES:
            return f"Error: unknown chart_type '{chart_type}'. Choose from: {', '.join(sorted(CHART_TYPES))}."
        if not path_raw.lower().endswith(".png"):
            path_raw += ".png"

        try:
            abs_path = resolve_output_path(path_raw, sly_data)
        except ValueError as exc:
            log_call(sly_data, tool="CreateChart", agent=agent, target=path_raw,
                     status="ERROR", detail=str(exc))
            return f"Error: {exc}"

        try:
            rows = _parse_data(data_raw)
        except Exception as exc:
            return f"Error: could not parse data as CSV or JSON: {exc}"

        if len(rows) < 2:
            return "Error: data must have at least a header row and one data row."

        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            if chart_type == "bar":
                fig = _bar_chart(rows, title, x_label, y_label, width, height)
            elif chart_type == "horizontal_bar":
                fig = _bar_chart(rows, title, x_label, y_label, width, height, horizontal=True)
            elif chart_type == "stacked_bar":
                fig = _bar_chart(rows, title, x_label, y_label, width, height, stacked=True)
            elif chart_type == "line":
                fig = _line_chart(rows, title, x_label, y_label, width, height)
            elif chart_type == "pie":
                fig = _pie_chart(rows, title, width, height)
            elif chart_type == "donut":
                fig = _pie_chart(rows, title, width, height, donut=True)

            fig.savefig(abs_path, dpi=DPI, bbox_inches="tight", facecolor=BG_COLOR)
            plt.close(fig)
            file_size = os.path.getsize(abs_path)

        except Exception as exc:
            log_call(sly_data, tool="CreateChart", agent=agent, target=path_raw,
                     status="ERROR", detail=str(exc))
            logger.exception("CreateChart failed for %s", path_raw)
            return f"Error: failed to create chart '{path_raw}': {exc}"

        detail = f"{chart_type}, {len(rows) - 1} data rows, {file_size} bytes"
        log_call(sly_data, tool="CreateChart", agent=agent, target=path_raw,
                 status="OK", detail=detail)
        logger.debug("CreateChart: %s (%s, %d bytes)", path_raw, chart_type, file_size)
        return f"OK: created '{path_raw}' — {chart_type} chart, {file_size} bytes."

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)
