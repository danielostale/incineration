# Bloque 1 — docstring del módulo
r"""
dashboard.py — Interactive HTML dashboard for the Stage-0 MSW model
====================================================================

Run this script after simulate() has produced outputs_endogenous.csv:

    python wm/dashboard.py

Reads ``outputs_endogenous.csv`` from the working directory and writes
``MSW_Dashboard.html`` — a fully self-contained interactive dashboard
that opens in any browser. No server required.

Four tabs
---------
1. Physical Flows   — mass flows through the treatment network over time
2. Money Flows      — inter-agent payments and net balances
3. Environment      — GHG, damages, and stock evolution
4. Sankey           — year-specific mass-flow Sankey diagram
"""

# Bloque 2 — imports
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Bloque 3 — paleta de colores
# ---------------------------------------------------------------------------
# Palette — dark analytical theme, waste-sector greens and earth tones
# ---------------------------------------------------------------------------
BG        = "#0f1117"
CARD      = "#1a1d27"
BORDER    = "#2a2d3a"
TEXT      = "#e8eaf0"
MUTED     = "#7a7f96"
GREEN     = "#4caf7d"
TEAL      = "#26c6da"
AMBER     = "#ffb74d"
RED       = "#ef5350"
PURPLE    = "#ab47bc"
BLUE      = "#5c9eff"
GREY      = "#607d8b"

# Bloque 4 — diccionarios de colores por variable
FLOW_COLORS = {
    "gen_total": GREEN,
    "Q_HAUL":    TEAL,
    "Q_MRF":     BLUE,
    "Q_CMP":     AMBER,
    "Q_WTE":     PURPLE,
    "Q_LF":      RED,
    "Q_mat":     GREEN,
    "Q_cmp":     AMBER,
}

MONEY_COLORS = {
    "gen_to_mun":   TEAL,
    "mun_to_haul":  BLUE,
    "tipping":      AMBER,
    "landfill_tax": RED,
    "rev_mat":      GREEN,
    "rev_E":        PURPLE,
}

NET_COLORS = {
    "net_MUN":  TEAL,
    "net_HAUL": BLUE,
    "net_T":    AMBER,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Bloque 5 — helper _line
def _line(df: pd.DataFrame, cols: list[str], colors: dict,
          labels: dict | None = None, y_title: str = "") -> go.Figure:
    """Multi-line time series."""
    fig = go.Figure()
    for col in cols:
        if col not in df.columns:
            continue
        lbl = (labels or {}).get(col, col)
        fig.add_trace(go.Scatter(
            x=df["year"], y=df[col], name=lbl,
            mode="lines+markers",
            line=dict(color=colors.get(col, MUTED), width=2),
            marker=dict(size=5),
            hovertemplate=f"<b>{lbl}</b><br>Year: %{{x}}<br>Value: %{{y:,.0f}}<extra></extra>",
        ))
    fig.update_layout(**_layout(y_title=y_title))
    return fig


# Bloque 6 — helper _layout
def _layout(**kwargs) -> dict:
    base = dict(
        paper_bgcolor=CARD,
        plot_bgcolor=BG,
        font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=12),
        legend=dict(
            bgcolor=CARD, bordercolor=BORDER, borderwidth=1,
            font=dict(color=TEXT, size=11),
        ),
        margin=dict(l=60, r=30, t=40, b=50),
        hovermode="x unified",
        xaxis=dict(
            gridcolor=BORDER, zerolinecolor=BORDER,
            tickfont=dict(color=MUTED),
        ),
        yaxis=dict(
            gridcolor=BORDER, zerolinecolor=BORDER,
            tickfont=dict(color=MUTED),
            title=dict(font=dict(color=MUTED)),
        ),
    )
    base.update(kwargs)
    return base


# Bloque 7 — helper _fig_to_json
def _fig_to_json(fig: go.Figure) -> str:
    return fig.to_json()


# ---------------------------------------------------------------------------
# Tab 1 — Physical flows
# ---------------------------------------------------------------------------

# Bloque 8 — función tab_physical
def tab_physical(df: pd.DataFrame) -> str:
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[
            "Generation, collection and source-separated streams (t/yr)",
            "Treatment node throughput (t/yr)",
            "Recovered outputs and capacity overflow (t/yr)",
            "Landfill diversion rate",
        ],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    # ------------------------------------------------------------------
    # Panel 1 — generation, total collection and source-separated streams
    # ------------------------------------------------------------------
    panel1_series = [
        ("gen_total", "Total generation", GREEN, "solid", 3),
        ("Q_HAUL", "Total collected", TEAL, "solid", 3),
        ("Q_HAUL_R", "Collected recyclables", BLUE, "dash", 2),
        ("Q_HAUL_O", "Collected organics", AMBER, "dash", 2),
        ("Q_HAUL_G", "Collected general/residual", GREY, "dash", 2),
    ]

    for col, lbl, color, dash, width in panel1_series:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["year"],
                    y=df[col],
                    name=lbl,
                    mode="lines+markers",
                    line=dict(color=color, width=width, dash=dash),
                    marker=dict(size=5),
                    hovertemplate=f"<b>{lbl}</b>: %{{y:,.0f}} t<extra></extra>",
                ),
                row=1,
                col=1,
            )

    # ------------------------------------------------------------------
    # Panel 2 — treatment node throughput
    # ------------------------------------------------------------------
    for col, lbl in [
        ("Q_MRF", "MRF"),
        ("Q_CMP", "Composting"),
        ("Q_WTE", "WTE"),
        ("Q_LF", "Landfill"),
    ]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["year"],
                    y=df[col],
                    name=lbl,
                    mode="lines+markers",
                    line=dict(color=FLOW_COLORS.get(col, MUTED), width=2),
                    marker=dict(size=5),
                    hovertemplate=f"<b>{lbl}</b>: %{{y:,.0f}} t<extra></extra>",
                ),
                row=1,
                col=2,
            )

    # ------------------------------------------------------------------
    # Panel 3 — recovered outputs and capacity overflow
    # ------------------------------------------------------------------
    panel3_series = [
        ("Q_mat", "Recovered recyclables", GREEN, "solid", 2),
        ("Q_cmp", "Compost output", AMBER, "solid", 2),
        ("overflow_R", "Recyclables overflow", BLUE, "dash", 2),
        ("overflow_O", "Organics overflow", RED, "dash", 2),
    ]

    for col, lbl, color, dash, width in panel3_series:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["year"],
                    y=df[col],
                    name=lbl,
                    mode="lines+markers",
                    line=dict(color=color, width=width, dash=dash),
                    marker=dict(size=5),
                    hovertemplate=f"<b>{lbl}</b>: %{{y:,.0f}} t<extra></extra>",
                ),
                row=2,
                col=1,
            )

    # Optional: WTE electricity, if useful, but keep it visually secondary.
    if "E_WTE" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=df["E_WTE"],
                name="Electricity from WTE",
                mode="lines+markers",
                line=dict(color=PURPLE, width=1, dash="dot"),
                marker=dict(size=4),
                hovertemplate="<b>Electricity from WTE</b>: %{y:,.1f} MWh<extra></extra>",
            ),
            row=2,
            col=1,
        )

    # ------------------------------------------------------------------
    # Panel 4 — diversion rates
    # ------------------------------------------------------------------
    for col, lbl, color in [
        ("D_LF", "Landfill diversion", GREEN),
        ("D_NC", "Non-combustion diversion", TEAL),
    ]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["year"],
                    y=df[col] * 100,
                    name=lbl,
                    mode="lines+markers",
                    line=dict(color=color, width=2),
                    marker=dict(size=5),
                    hovertemplate=f"<b>{lbl}</b>: %{{y:.1f}}%<extra></extra>",
                ),
                row=2,
                col=2,
            )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    fig.update_layout(
        paper_bgcolor=CARD,
        plot_bgcolor=BG,
        font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=12),
        legend=dict(
            bgcolor=CARD,
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(color=TEXT, size=10),
        ),
        margin=dict(l=60, r=30, t=60, b=50),
        hovermode="x unified",
        height=560,
    )

    for ann in fig.layout.annotations:
        ann.font.color = MUTED
        ann.font.size = 12

    for axis in [
        "xaxis",
        "xaxis2",
        "xaxis3",
        "xaxis4",
        "yaxis",
        "yaxis2",
        "yaxis3",
        "yaxis4",
    ]:
        fig.update_layout(
            **{
                axis: dict(
                    gridcolor=BORDER,
                    zerolinecolor=BORDER,
                    tickfont=dict(color=MUTED),
                )
            }
        )

    # Avoid misleading visual differences between generation and collection.
    # They should be equal up to floating-point precision when there is no
    # informal leakage.
    if "gen_total" in df.columns and "Q_HAUL" in df.columns:
        ymax_gc = max(
            df["gen_total"].max(),
            df["Q_HAUL"].max(),
            df["Q_HAUL_R"].max() if "Q_HAUL_R" in df.columns else 0,
            df["Q_HAUL_O"].max() if "Q_HAUL_O" in df.columns else 0,
            df["Q_HAUL_G"].max() if "Q_HAUL_G" in df.columns else 0,
        )
        fig.update_yaxes(
            range=[0, ymax_gc * 1.05],
            tickformat=",.0f",
            row=1,
            col=1,
        )

    # Percent axis for diversion.
    fig.update_yaxes(
        range=[0, 100],
        ticksuffix="%",
        row=2,
        col=2,
    )

    return _fig_to_json(fig)


# ---------------------------------------------------------------------------
# Tab 2 — Money flows
# ---------------------------------------------------------------------------

# Bloque 9 — función tab_money
def tab_money(df: pd.DataFrame) -> str:
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Inter-agent payments ($/yr)",
            "Net balances by agent ($/yr)",
            "Revenue streams — Treatment operator ($/yr)",
            "Cumulative landfill tax collected ($/yr)",
        ],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    # Panel 1 — payments
    for col, lbl in [("gen_to_mun", "GEN → MUN"),
                     ("mun_to_haul", "MUN → HAUL"),
                     ("tipping", "HAUL → T (tipping)")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["year"], y=df[col], name=lbl,
                mode="lines+markers",
                line=dict(color=MONEY_COLORS.get(col, MUTED), width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{lbl}</b>: $%{{y:,.0f}}<extra></extra>",
            ), row=1, col=1)

    # Panel 2 — net balances
    for col, lbl in [("net_MUN", "MUN net"),
                     ("net_HAUL", "HAUL net"),
                     ("net_T", "Treatment net")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["year"], y=df[col], name=lbl,
                mode="lines+markers",
                line=dict(color=NET_COLORS.get(col, MUTED), width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{lbl}</b>: $%{{y:,.0f}}<extra></extra>",
            ), row=1, col=2)
    # Zero reference line
    fig.add_hline(y=0, line=dict(color=BORDER, width=1, dash="dot"), row=1, col=2)

    # Panel 3 — Treatment revenues
    for col, lbl in [("rev_mat", "Material sales"),
                     ("rev_E", "Electricity sales"),
                     ("tipping", "Tipping revenue")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["year"], y=df[col], name=lbl,
                mode="lines+markers",
                line=dict(color=MONEY_COLORS.get(col, MUTED), width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{lbl}</b>: $%{{y:,.0f}}<extra></extra>",
            ), row=2, col=1)

    # Panel 4 — landfill tax
    if "landfill_tax" in df.columns:
        fig.add_trace(go.Bar(
            x=df["year"], y=df["landfill_tax"], name="Landfill tax",
            marker_color=RED, opacity=0.8,
            hovertemplate="<b>LF tax</b>: $%{y:,.0f}<extra></extra>",
        ), row=2, col=2)

    fig.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=BG,
        font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=12),
        legend=dict(bgcolor=CARD, bordercolor=BORDER, borderwidth=1,
                    font=dict(color=TEXT, size=10)),
        margin=dict(l=60, r=30, t=60, b=50),
        hovermode="x unified",
        height=560,
        barmode="group",
    )
    for ann in fig.layout.annotations:
        ann.font.color = MUTED
        ann.font.size = 12
    for axis in ["xaxis", "xaxis2", "xaxis3", "xaxis4",
                 "yaxis", "yaxis2", "yaxis3", "yaxis4"]:
        fig.update_layout(**{axis: dict(gridcolor=BORDER, zerolinecolor=BORDER,
                                        tickfont=dict(color=MUTED))})
    return _fig_to_json(fig)


# ---------------------------------------------------------------------------
# Tab 3 — Environment
# ---------------------------------------------------------------------------

# Bloque 10 — función tab_environment
def tab_environment(df: pd.DataFrame) -> str:
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "GHG emissions (tCO₂e/yr)",
            "Monetised damages ($/yr)",
            "Cumulative landfill stock (tons)",
            "Sorting shares — Households",
        ],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    # Panel 1 — GHG
    for col, lbl, color in [("GHG_dir", "Direct GHG", RED),
                              ("GHG_net", "Net GHG (after avoided)", AMBER)]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["year"], y=df[col], name=lbl,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{lbl}</b>: %{{y:,.0f}} tCO₂e<extra></extra>",
            ), row=1, col=1)

    # Panel 2 — damages
    for col, lbl, color in [("D_climate", "Climate damage", AMBER),
                              ("D_air", "Air quality damage", RED),
                              ("D_env", "Total env. damage", PURPLE)]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["year"], y=df[col], name=lbl,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{lbl}</b>: $%{{y:,.0f}}<extra></extra>",
            ), row=1, col=2)

    # Panel 3 — landfill stock
    if "S_LF" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["S_LF"], name="S_LF (cumulative)",
            mode="lines", fill="tozeroy",
            line=dict(color=RED, width=2),
            fillcolor="rgba(239,83,80,0.15)",
            hovertemplate="<b>Landfill stock</b>: %{y:,.0f} t<extra></extra>",
        ), row=2, col=1)

    # Panel 4 — sorting shares
    for col, lbl, color in [("sR", "Recyclables (sR)", BLUE),
                              ("sO", "Organics (sO)", GREEN),
                              ("sG", "General (sG)", GREY)]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["year"], y=df[col] * 100, name=lbl,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{lbl}</b>: %{{y:.1f}}%<extra></extra>",
            ), row=2, col=2)

    fig.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=BG,
        font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=12),
        legend=dict(bgcolor=CARD, bordercolor=BORDER, borderwidth=1,
                    font=dict(color=TEXT, size=10)),
        margin=dict(l=60, r=30, t=60, b=50),
        hovermode="x unified",
        height=560,
    )
    for ann in fig.layout.annotations:
        ann.font.color = MUTED
        ann.font.size = 12
    for axis in ["xaxis", "xaxis2", "xaxis3", "xaxis4",
                 "yaxis", "yaxis2", "yaxis3", "yaxis4"]:
        fig.update_layout(**{axis: dict(gridcolor=BORDER, zerolinecolor=BORDER,
                                        tickfont=dict(color=MUTED))})
    return _fig_to_json(fig)


# ---------------------------------------------------------------------------
# Tab 4 — Sankey (year-specific, controlled by dropdown)
# ---------------------------------------------------------------------------

# Bloque 11 — función tab_sankey
def tab_sankey(df: pd.DataFrame) -> str:
    """Returns a JSON list of one Sankey figure per year."""
    figures = []
    nodes = ["Generation", "Haulers", "MRF", "Composting", "WTE", "Landfill",
             "Recovered Material", "Compost Output", "Ash"]
    node_colors = [GREEN, TEAL, BLUE, AMBER, PURPLE, RED, GREEN, AMBER, GREY]
    idx = {n: i for i, n in enumerate(nodes)}

    for _, row in df.iterrows():
        q_haul = row.get("Q_HAUL", 0)
        q_mrf  = row.get("Q_MRF", 0)
        q_cmp  = row.get("Q_CMP", 0)
        q_wte  = row.get("Q_WTE", 0)
        q_lf   = row.get("Q_LF", 0)
        q_mat  = row.get("Q_mat", 0)
        q_cmp_out = row.get("Q_cmp", 0)
        q_ash  = row.get("Q_ash", 0)
        rej_mrf = row.get("rej_MRF", q_mrf - q_mat if q_mrf > 0 else 0)
        rej_cmp = row.get("rej_CMP", q_cmp - q_cmp_out if q_cmp > 0 else 0)

        sources, targets, values, link_colors = [], [], [], []

        def _add(s, t, v, color="rgba(100,100,120,0.3)"):
            if v > 0:
                sources.append(idx[s]); targets.append(idx[t])
                values.append(round(v, 1)); link_colors.append(color)

        _add("Generation", "Haulers",          q_haul,   "rgba(38,198,218,0.4)")
        _add("Haulers",    "MRF",               q_mrf,    "rgba(92,158,255,0.4)")
        _add("Haulers",    "Composting",        q_cmp,    "rgba(255,183,77,0.4)")
        _add("Haulers",    "WTE",               q_wte,    "rgba(171,71,188,0.4)")
        _add("Haulers",    "Landfill",          max(0, q_lf - rej_mrf - rej_cmp - q_ash),
                                                           "rgba(239,83,80,0.4)")
        _add("MRF",        "Recovered Material", q_mat,   "rgba(76,175,125,0.4)")
        _add("MRF",        "Landfill",          rej_mrf,  "rgba(239,83,80,0.3)")
        _add("Composting", "Compost Output",    q_cmp_out,"rgba(255,183,77,0.4)")
        _add("Composting", "Landfill",          rej_cmp,  "rgba(239,83,80,0.3)")
        _add("WTE",        "Ash",               q_ash,    "rgba(96,125,139,0.4)")
        _add("Ash",        "Landfill",          q_ash,    "rgba(239,83,80,0.3)")

        fig = go.Figure(go.Sankey(
            node=dict(
                pad=18, thickness=22,
                line=dict(color=BORDER, width=0.5),
                label=nodes,
                color=node_colors,
                hovertemplate="<b>%{label}</b><br>Flow: %{value:,.0f} t<extra></extra>",
            ),
            link=dict(
                source=sources, target=targets, value=values,
                color=link_colors,
                hovertemplate="<b>%{source.label} → %{target.label}</b><br>%{value:,.0f} t<extra></extra>",
            ),
        ))
        fig.update_layout(
            paper_bgcolor=CARD,
            font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=12),
            margin=dict(l=20, r=20, t=20, b=20),
            height=480,
        )
        figures.append(json.loads(fig.to_json()))

    return json.dumps(figures)


# ---------------------------------------------------------------------------
# HTML shell
# ---------------------------------------------------------------------------

# Bloque 12 — HTML_TEMPLATE: <head> + CSS
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Miami-Dade MSW — Model Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:     {BG};
    --card:   {CARD};
    --border: {BORDER};
    --text:   {TEXT};
    --muted:  {MUTED};
    --green:  {GREEN};
    --teal:   {TEAL};
    --amber:  {AMBER};
    --red:    {RED};
    --blue:   {BLUE};
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 14px;
    min-height: 100vh;
  }}

  /* ── Header ── */
  header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--card);
  }}
  .header-left h1 {{
    font-size: 17px;
    font-weight: 600;
    letter-spacing: -0.3px;
    color: var(--text);
  }}
  .header-left p {{
    font-size: 12px;
    color: var(--muted);
    margin-top: 2px;
  }}
  .badge {{
    font-size: 11px;
    font-weight: 500;
    color: var(--green);
    background: rgba(76,175,125,0.12);
    border: 1px solid rgba(76,175,125,0.25);
    border-radius: 4px;
    padding: 3px 10px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}

  /* ── KPI strip ── */
  .kpi-strip {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 1px;
    background: var(--border);
    border-bottom: 1px solid var(--border);
  }}
  .kpi {{
    background: var(--card);
    padding: 14px 20px;
  }}
  .kpi-label {{
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 5px;
  }}
  .kpi-value {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }}
  .kpi-sub {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 2px;
  }}
  .kpi-value.green  {{ color: var(--green); }}
  .kpi-value.teal   {{ color: var(--teal);  }}
  .kpi-value.amber  {{ color: var(--amber); }}
  .kpi-value.red    {{ color: var(--red);   }}
  .kpi-value.blue   {{ color: var(--blue);  }}
  .kpi-value.purple {{ color: #ab47bc;       }}

  /* ── Tabs ── */
  .tab-bar {{
    display: flex;
    padding: 0 32px;
    background: var(--card);
    border-bottom: 1px solid var(--border);
    gap: 4px;
  }}
  .tab-btn {{
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--muted);
    cursor: pointer;
    font-family: inherit;
    font-size: 13px;
    font-weight: 500;
    padding: 12px 16px;
    transition: color 0.15s, border-color 0.15s;
  }}
  .tab-btn:hover  {{ color: var(--text); }}
  .tab-btn.active {{ color: var(--text); border-bottom-color: var(--teal); }}

  /* ── Content ── */
  .content {{
    padding: 24px 32px;
    max-width: 1400px;
    margin: 0 auto;
  }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}

  .section-title {{
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 14px;
  }}

  .chart-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 20px;
  }}

  /* ── Sankey controls ── */
  .sankey-controls {{
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
  }}
  .sankey-controls label {{
    font-size: 12px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .year-slider {{
    -webkit-appearance: none;
    appearance: none;
    width: 320px;
    height: 4px;
    border-radius: 2px;
    background: var(--border);
    outline: none;
  }}
  .year-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 16px; height: 16px;
    border-radius: 50%;
    background: var(--teal);
    cursor: pointer;
  }}
  .year-display {{
    font-size: 18px;
    font-weight: 700;
    color: var(--teal);
    min-width: 50px;
  }}

  /* ── Flow table ── */
  .flow-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    margin-top: 16px;
  }}
  .flow-table th {{
    text-align: left;
    padding: 8px 12px;
    color: var(--muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border);
  }}
  .flow-table td {{
    padding: 8px 12px;
    border-bottom: 1px solid rgba(42,45,58,0.5);
    color: var(--text);
  }}
  .flow-table tr:last-child td {{ border-bottom: none; }}
  .flow-arrow {{ color: var(--muted); margin: 0 4px; }}
  .amount-cell {{ font-variant-numeric: tabular-nums; text-align: right; }}
</style>
</head>
<body>

""" + """\
""" + r"""<header>
  <div class="header-left">
    <h1>Miami-Dade MSW · Model Dashboard</h1>
    <p>Stage 0 — Deterministic accounting · {n_years} periods · {year_min}–{year_max}</p>
    <div style="margin-top:6px;display:flex;gap:18px;font-size:11px">
      <span style="color:#ffb74d;font-weight:600">CSV data generated: {csv_generated_at}</span>
      <span style="color:#26c6da;font-weight:600">Dashboard built: {dashboard_built_at}</span>
    </div>
  </div>
  <span class="badge">Stage 0</span>
</header>

<!-- KPI strip -->
<div class="kpi-strip">
  <div class="kpi">
    <div class="kpi-label">Generation (baseline)</div>
    <div class="kpi-value teal">{gen_base}</div>
    <div class="kpi-sub">tons / year</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Landfill diversion</div>
    <div class="kpi-value green">{d_lf_last}</div>
    <div class="kpi-sub">final year</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">WTE throughput</div>
    <div class="kpi-value purple">{q_wte_last}</div>
    <div class="kpi-sub">tons / year (final)</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Net GHG (final)</div>
    <div class="kpi-value amber">{ghg_last}</div>
    <div class="kpi-sub">tCO₂e / year</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Total env. damage</div>
    <div class="kpi-value red">{d_env_last}</div>
    <div class="kpi-sub">$ / year (final)</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Landfill stock</div>
    <div class="kpi-value blue">{s_lf_last}</div>
    <div class="kpi-sub">cumulative tons (final)</div>
  </div>
</div>

<!-- Tab bar -->
<div class="tab-bar">
  <button class="tab-btn active" onclick="showTab('physical', this)">⚖ Physical Flows</button>
  <button class="tab-btn" onclick="showTab('money', this)">💰 Money Flows</button>
  <button class="tab-btn" onclick="showTab('environment', this)">🌿 Environment</button>
  <button class="tab-btn" onclick="showTab('sankey', this)">🔀 Sankey</button>
</div>

<!-- Tab panels -->
<div class="content">

  <!-- Tab 1: Physical -->
  <div id="tab-physical" class="tab-panel active">
    <p class="section-title">Mass flows through the treatment network</p>
    <div class="chart-card">
      <div id="chart-physical"></div>
    </div>
  </div>

  <!-- Tab 2: Money -->
  <div id="tab-money" class="tab-panel">
    <p class="section-title">Inter-agent payments and net balances</p>
    <div class="chart-card">
      <div id="chart-money"></div>
    </div>
    <div class="chart-card">
      <p class="section-title" style="margin-bottom:8px">Payment network — final year</p>
      <table class="flow-table" id="flow-table"></table>
    </div>
  </div>

  <!-- Tab 3: Environment -->
  <div id="tab-environment" class="tab-panel">
    <p class="section-title">Emissions, damages, and behavioural stocks</p>
    <div class="chart-card">
      <div id="chart-environment"></div>
    </div>
  </div>

  <!-- Tab 4: Sankey -->
  <div id="tab-sankey" class="tab-panel">
    <p class="section-title">Mass-flow Sankey — select year</p>
    <div class="chart-card">
      <div class="sankey-controls">
        <label>Year</label>
        <input type="range" class="year-slider" id="year-slider"
               min="0" max="{n_years_minus1}" value="0"
               oninput="updateSankey(this.value)">
        <span class="year-display" id="year-display">{year_min}</span>
      </div>
      <div id="chart-sankey"></div>
    </div>
  </div>

</div><!-- /content -->

<script>
// ── Data injected from Python ──────────────────────────────────────────────
const figPhysical    = {fig_physical};
const figMoney       = {fig_money};
const figEnvironment = {fig_environment};
const sankeyFigs     = {sankey_figs};
const years          = {years_list};
const lastRow        = {last_row};

// ── Tab switching ──────────────────────────────────────────────────────────
function showTab(name, btn) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
  if (name === 'sankey') updateSankey(document.getElementById('year-slider').value);
}}

// ── Render static charts ───────────────────────────────────────────────────
const plotConfig = {{
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
  displaylogo: false,
}};

Plotly.newPlot('chart-physical',    figPhysical.data,    figPhysical.layout,    plotConfig);
Plotly.newPlot('chart-money',       figMoney.data,       figMoney.layout,       plotConfig);
Plotly.newPlot('chart-environment', figEnvironment.data, figEnvironment.layout, plotConfig);

// ── Flow table (final year) ────────────────────────────────────────────────
const flows = [
  {{ from: 'Generators', to: 'Municipality', field: 'gen_to_mun',   color: '#26c6da' }},
  {{ from: 'Municipality', to: 'Haulers',   field: 'mun_to_haul',  color: '#5c9eff' }},
  {{ from: 'Haulers', to: 'Treatment',      field: 'tipping',      color: '#ffb74d' }},
  {{ from: 'Treatment', to: 'Government',   field: 'landfill_tax', color: '#ef5350' }},
  {{ from: 'Treatment', to: 'Market',       field: 'rev_mat',      color: '#4caf7d' }},
  {{ from: 'Treatment', to: 'Grid',         field: 'rev_E',        color: '#ab47bc' }},
];
const tbl = document.getElementById('flow-table');
tbl.innerHTML = `<tr>
  <th>From</th><th></th><th>To</th><th style="text-align:right">Amount ($/yr)</th>
</tr>` + flows.map(f => {{
  const val = lastRow[f.field] ?? 0;
  return `<tr>
    <td style="color:${{f.color}};font-weight:600">${{f.from}}</td>
    <td class="flow-arrow">→</td>
    <td>${{f.to}}</td>
    <td class="amount-cell">${{val.toLocaleString('en-US', {{maximumFractionDigits:0}})}}</td>
  </tr>`;
}}).join('');

// ── Sankey ─────────────────────────────────────────────────────────────────
function updateSankey(idx) {{
  idx = parseInt(idx);
  document.getElementById('year-display').textContent = years[idx];
  const fig = sankeyFigs[idx];
  Plotly.react('chart-sankey', fig.data, fig.layout, plotConfig);
}}
updateSankey(0);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# Bloque 17 — función build_dashboard
def build_dashboard(
    csv_path: str | Path = "outputs_endogenous.csv",
    out_path: str | Path = "MSW_Dashboard.html",
) -> None:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Model output not found: {csv_path}\n"
            "Run 'python -m wm.run' first to generate outputs_endogenous.csv"
        )

    df = pd.read_csv(csv_path)
    last = df.iloc[-1]
    first = df.iloc[0]

    # Scenario metadata.
    # These columns are added by run.py. If the CSV was produced by an older
    # version of the pipeline, the dashboard still builds and reports that the
    # scenario was not recorded.
    def _text_col(col: str, default: str) -> str:
        if col in df.columns and pd.notna(first.get(col)):
            return str(first.get(col))
        return default

    scenario_id = _text_col("scenario_id", "not recorded")
    scenario_name = _text_col("scenario_name", "Scenario not recorded")
    scenario_logic = _text_col(
        "scenario_logic",
        "This CSV does not contain scenario metadata. Re-run wm.run with the scenario-enabled pipeline.",
    )
    scenario_mechanisms = _text_col(
        "scenario_mechanisms",
        "Active mechanisms not recorded.",
    )

    # Timestamps: when the CSV was generated vs. when this dashboard was built.
    csv_mtime = os.path.getmtime(csv_path)
    csv_generated_at = datetime.fromtimestamp(csv_mtime).strftime("%Y-%m-%d %H:%M:%S")
    dashboard_built_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _fmt(v, suffix=""):
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = 0.0

        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.1f}M{suffix}"
        if abs(v) >= 1_000:
            return f"{v/1_000:.0f}k{suffix}"
        return f"{v:.1f}{suffix}"

    def _safe_last_row(row: pd.Series) -> dict:
        """
        Convert only numeric values for JavaScript tables.

        Scenario metadata columns are text. The previous version attempted to
        convert every column to float, which fails once scenario_id = value_1,
        value_2, etc. are added to outputs_endogenous.csv.
        """
        out = {}
        for k, v in row.items():
            if pd.isna(v):
                continue

            try:
                out[k] = round(float(v), 2)
            except (TypeError, ValueError):
                continue

        return out

    html = HTML_TEMPLATE.format(
        BG=BG, CARD=CARD, BORDER=BORDER, TEXT=TEXT, MUTED=MUTED,
        GREEN=GREEN, TEAL=TEAL, AMBER=AMBER, RED=RED, BLUE=BLUE,
        csv_generated_at=csv_generated_at,
        dashboard_built_at=dashboard_built_at,
        n_years=len(df),
        n_years_minus1=len(df) - 1,
        year_min=int(df["year"].min()),
        year_max=int(df["year"].max()),
        gen_base=_fmt(first.get("gen_total", 0), " t"),
        d_lf_last=f"{float(last.get('D_LF', 0))*100:.1f}%",
        q_wte_last=_fmt(last.get("Q_WTE", 0), " t"),
        ghg_last=_fmt(last.get("GHG_net", 0), ""),
        d_env_last=_fmt(last.get("D_env", 0), ""),
        s_lf_last=_fmt(last.get("S_LF", 0), " t"),
        fig_physical=tab_physical(df),
        fig_money=tab_money(df),
        fig_environment=tab_environment(df),
        sankey_figs=tab_sankey(df),
        years_list=json.dumps(df["year"].tolist()),
        last_row=json.dumps(_safe_last_row(last)),
    )

    # Replace the generic dashboard badge with the active scenario id.
    html = html.replace(
        '<span class="badge">Stage 0</span>',
        f'<span class="badge">{scenario_id}</span>',
        1,
    )

    # Add an explicit scenario card above the dashboard content.
    scenario_card = f"""
<div style="max-width:1400px;margin:20px auto 0;padding:0 32px;">
  <div style="
      background:{CARD};
      border:1px solid {BORDER};
      border-left:4px solid {TEAL};
      border-radius:6px;
      padding:14px 18px;
  ">
    <div style="
        font-size:11px;
        color:{MUTED};
        text-transform:uppercase;
        letter-spacing:0.7px;
        margin-bottom:6px;
    ">
      Active parametrization
    </div>
    <div style="font-size:16px;font-weight:700;color:{TEXT};margin-bottom:6px;">
      {scenario_id} — {scenario_name}
    </div>
    <div style="font-size:12px;color:{TEXT};line-height:1.45;margin-bottom:6px;">
      {scenario_logic}
    </div>
    <div style="font-size:12px;color:{MUTED};line-height:1.45;">
      <strong style="color:{TEAL};">Active mechanisms:</strong> {scenario_mechanisms}
    </div>
  </div>
</div>
"""

    html = html.replace(
        '<div class="content">',
        scenario_card + '\n<div class="content">',
        1,
    )

    out_path = Path(out_path)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to: {out_path}")
    print(f"Open in browser: file:///{out_path.resolve()}")


# Bloque 18 — entry point
if __name__ == "__main__":
    build_dashboard()