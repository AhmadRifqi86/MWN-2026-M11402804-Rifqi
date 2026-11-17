#!/usr/bin/env python3
"""A4 — flowchart of the simulation (one kong-edca run) and of the analysis pipeline.

Output: assets/img/a4/a4_flowchart.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "a4")
INK, MUTED, ACC, PEAK, HAIR = "#141a24", "#586274", "#2f63e6", "#d97a2b", "#cdd4de"
CARD, CARD2, WARM = "#ecf1fc", "#f6f8fb", "#fbeee3"


def box(ax, x, y, w, h, title, body, fc=CARD2, ec=HAIR, tc=ACC):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
                                fc=fc, ec=ec, lw=1.1))
    ax.text(x + 0.012, y + h - 0.022, title, fontsize=8.6, weight="bold", color=tc, va="top",
            family="monospace")
    ax.text(x + 0.012, y + h - 0.058, body, fontsize=8.3, color=INK, va="top", linespacing=1.38)


def arrow(ax, x0, y0, x1, y1, color=MUTED):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, color=color,
                                 lw=1.4))


fig = plt.figure(figsize=(14, 6.7))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0.12, 1)
ax.axis("off")

# ---------------------------------------------------------------- left column: one run
ax.text(0.02, 0.965, "One simulation run — kong-edca.cc", fontsize=12, weight="bold", color=INK)
W, H, X = 0.42, 0.105, 0.02
steps = [
    ("1 · PARAMETERS", "M, seed (RngRun), idealPlcp, retryLimit 7 or 4 attempts, 1000 B,\n"
                       "SIFS 20 µs, AIFSN 2 / 3, CW 15–127 / 31–255, simTime 33 s", CARD, ACC),
    ("2 · BUILD THE BSS", "1 AP + M STAs on a 5 m circle · 802.11b, 11 Mb/s data + control\n"
                          "RTS/CTS for every frame · TXOP limit 0 · MAC queue lifetime 3600 s", CARD2, ACC),
    ("3 · PHY VARIANT", "idealPlcp = 0 → standard 192 µs PLCP at 1 Mb/s\n"
                        "idealPlcp = 1 → 192 bits at 11 Mb/s (patched DsssPhy, Table I)", WARM, PEAK),
    ("4 · ASSOCIATE, THEN SATURATE", "t = 0–2 s: stations associate (Assoc trace counts them)\n"
                                     "t = 2 s: per STA one AC3 (UP 6) + one AC1 (UP 1) client, 4 Mb/s each", CARD2, ACC),
    ("5 · MEASURE (t = 3–33 s)", "AP Rx trace → payload bytes per AC → S = bits / 30 s / 11 Mb/s\n"
                                 "AckedMpdu / DroppedMpdu → head-of-line → ACK time, retry-limit drops", CARD2, ACC),
    ("6 · OUTPUT", "one CSV line: S_ac3, S_ac1, D_ac3, D_ac1, frames, drops, associated", CARD, ACC),
]
y = 0.84
for i, (t, b, fc, tc) in enumerate(steps):
    box(ax, X, y, W, H, t, b, fc=fc, tc=tc)
    if i < len(steps) - 1:
        arrow(ax, X + W / 2, y, X + W / 2, y - 0.03)
    y -= H + 0.03

# ---------------------------------------------------------------- right column: pipeline
ax.text(0.52, 0.965, "Sweep and analysis", fontsize=12, weight="bold", color=INK)
X2, W2 = 0.52, 0.46
box(ax, X2, 0.80, W2, 0.12, "RUN_SWEEP.SH  (inside the ns3lab container)",
    "3 variants (PHY × retry) × M ∈ {5, …, 30} × seeds 1–10\n= 180 runs, in parallel → kong_fig7_sweep.csv", CARD, ACC)
arrow(ax, X2 + W2 / 2, 0.80, X2 + W2 / 2, 0.765)
box(ax, X2, 0.625, W2, 0.14, "PLOT_FIG7.PY",
    "mean and 95 % CI over the 10 seeds per point\n"
    "paper values read off Fig. 7 (analysis curve + NS-2 points)\n"
    "→ a4_fig7_reproduction.png (same axes as Fig. 7a, 7b)", CARD2, ACC)
arrow(ax, X2 + W2 / 2, 0.625, X2 + W2 / 2, 0.59)
box(ax, X2, 0.42, W2, 0.17, "EXPLAIN THE DIFFERENCES",
    "PHY overhead: S_max per exchange (draw_setup.py)\n"
    "AC3 share S3 / (S3 + S1): cancels the PHY overhead\n"
    "Little's law D = M · L / (S · R); retry limit 2–7 attempts\n"
    "→ a4_explain.png", WARM, PEAK)
arrow(ax, X2 + W2 / 2, 0.42, X2 + W2 / 2, 0.385)
box(ax, X2, 0.255, W2, 0.13, "REPORT",
    "parameters, seeds, run count, ns-3 version and patch\n"
    "→ a4 study note and slides", CARD, ACC)
arrow(ax, X + W, 0.84 - 5 * (H + 0.03) + H / 2, X2, 0.86, color=ACC)
ax.text(0.465, 0.53, "×180", fontsize=10, color=ACC, weight="bold", rotation=62)
ax.text(X2, 0.19, "Paper digitizing error ≈ ±0.01 in throughput and ±3 ms in delay;\n"
        "ns-3 error bars are 1.96 · std / √10 over seeds.", fontsize=8.5, color=MUTED, linespacing=1.4)
fig.savefig(os.path.join(OUT, "a4_flowchart.png"), dpi=130)
print("wrote a4_flowchart.png")
