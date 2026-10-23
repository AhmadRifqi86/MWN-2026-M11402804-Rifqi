#!/usr/bin/env python3
"""A4 — simulation setup figure: topology (left) and one RTS/CTS/DATA/ACK exchange drawn to scale
for the paper's Table I PHY and for ns-3's 802.11b PHY (right).

Output: assets/img/a4/a4_setup.png
"""
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "a4")
INK, MUTED, ACC, PEAK, HAIR = "#141a24", "#586274", "#2f63e6", "#d97a2b", "#cdd4de"
RATE = 11.0  # Mb/s = bits per us
SIFS, AIFS3 = 20.0, 60.0


def exchange(plcp_us, rts_bits, cts_bits, data_bits, ceil):
    """Durations (us) of RTS, CTS, DATA, ACK incl. PLCP; ns-3 rounds the PSDU time up to 1 us."""
    f = (lambda b: math.ceil(b / RATE)) if ceil else (lambda b: b / RATE)
    return [("RTS", plcp_us + f(rts_bits)), ("SIFS", SIFS), ("CTS", plcp_us + f(cts_bits)), ("SIFS", SIFS),
            ("DATA", plcp_us + f(data_bits)), ("SIFS", SIFS), ("ACK", plcp_us + f(cts_bits)),
            ("AIFS[AC3]", AIFS3)]


rows = [
    ("Paper, Table I\n(192-bit PLCP at 11 Mb/s,\n272-bit MAC header)", exchange(192 / RATE, 160, 112, 8000 + 272, False)),
    ("ns-3, Table I PHY\n(dsss-ideal-plcp.patch)", exchange(17.455, 160, 112, (1000 + 38) * 8, True)),
    ("ns-3, 802.11b PHY\n(192 µs PLCP at 1 Mb/s)", exchange(192.0, 160, 112, (1000 + 38) * 8, True)),
]
payload_us = 8000 / RATE

fig = plt.figure(figsize=(14, 5.2))
# ---------------------------------------------------------------- topology
ax = fig.add_axes([0.0, 0.0, 0.33, 1.0])
ax.set_aspect("equal", adjustable="datalim")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.text(0.02, 0.92, "Topology and traffic", fontsize=12, weight="bold", color=INK)
cx, cy, r = 0.5, 0.5, 0.3
ax.add_patch(Circle((cx, cy), r, fill=False, ec=HAIR, ls="--"))
ax.add_patch(Circle((cx, cy), 0.035, fc=ACC, ec="none"))
ax.text(cx, cy - 0.075, "AP", ha="center", fontsize=10, weight="bold", color=INK)
for i in range(10):
    a = 2 * math.pi * i / 10 + 0.2
    sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
    ax.add_patch(FancyBboxPatch((sx - 0.03, sy - 0.03), 0.06, 0.06, boxstyle="round,pad=0.004",
                                fc="#ecf1fc", ec=ACC, lw=0.9))
    ax.plot([sx - 0.012] * 2, [sy - 0.018, sy + 0.018], color=ACC, lw=2.4)
    ax.plot([sx + 0.012] * 2, [sy - 0.018, sy + 0.018], color=PEAK, lw=2.4)
    ax.add_patch(FancyArrowPatch((sx + (cx - sx) * 0.2, sy + (cy - sy) * 0.2),
                                 (sx + (cx - sx) * 0.8, sy + (cy - sy) * 0.8),
                                 arrowstyle="-|>", mutation_scale=9, color=HAIR, lw=0.9))
ax.text(0.5, 0.09, "M = 5 … 30 stations on a 5 m circle (ideal channel)\n"
        "each: saturated AC3 (blue, AC_VO) + AC1 (orange, AC_BK)\n1000-byte payload, uplink to the AP",
        ha="center", fontsize=9, color=MUTED, linespacing=1.4)

# ---------------------------------------------------------------- timing
ax = fig.add_axes([0.42, 0.14, 0.56, 0.72])
colors = {"RTS": "#8fb0f5", "CTS": "#8fb0f5", "ACK": "#8fb0f5", "DATA": ACC, "SIFS": "#e6eaf0",
          "AIFS[AC3]": "#fbe1c9"}
for k, (name, segs) in enumerate(rows):
    y = len(rows) - 1 - k
    x = 0.0
    for lab, dur in segs:
        ax.barh(y, dur, left=x, height=0.55, color=colors[lab], ec="white", lw=0.8)
        if lab in ("RTS", "CTS", "ACK") and dur > 100:
            ax.text(x + dur / 2, y, lab, ha="center", va="center", fontsize=7.5, color=INK)
        if lab == "DATA":
            ax.text(x + dur / 2, y, "DATA (1000 B payload)", ha="center", va="center", fontsize=8.5,
                    color="white", weight="bold")
        x += dur
    ax.text(x + 15, y, f"{x:.0f} µs  →  S_max = {payload_us / x:.2f}", va="center", fontsize=9.5,
            color=INK, weight="bold")
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=8.5)
ax.set_xlim(0, 2350)
ax.set_xlabel("time [µs]")
ax.grid(axis="x", alpha=0.3)
ax.set_title("One successful RTS/CTS/DATA/ACK exchange, to scale (no backoff, no collisions)",
             fontsize=10.5, color=INK, loc="left")
fig.text(0.42, 0.03, "S_max = payload time (727 µs) / cycle time: the highest normalized throughput the "
         "PHY allows, before any backoff or collision.", fontsize=8.5, color=MUTED)
fig.savefig(os.path.join(OUT, "a4_setup.png"), dpi=130)
for name, segs in rows:
    tot = sum(d for _, d in segs)
    print(name.split("\n")[0], round(tot, 1), "us, S_max", round(payload_us / tot, 3))
