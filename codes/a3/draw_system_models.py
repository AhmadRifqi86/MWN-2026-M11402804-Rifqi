#!/usr/bin/env python3
"""Draw the system-model diagrams for the two A3 papers.

Writes assets/img/a3/kong_system_model.png and assets/img/a3/xiao_system_model.png.
Each figure: environment (top-left), one station's MAC (top-right), and the
inputs -> model -> outputs/metrics chain (bottom).
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "a3")
INK, MUTED, ACC, PEAK = "#141a24", "#586274", "#2f63e6", "#d97a2b"
CARD, CARD2, HAIR = "#ecf1fc", "#f6f8fb", "#cdd4de"


def box(ax, x, y, w, h, text, fc=CARD2, ec=HAIR, fs=9, weight="normal", color=INK, ha="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.012",
                                fc=fc, ec=ec, lw=1.1))
    tx = x + w / 2 if ha == "center" else x + 0.012
    ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=color, weight=weight,
            linespacing=1.35)


def arrow(ax, x0, y0, x1, y1, color=MUTED, lw=1.4, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=12,
                                 color=color, lw=lw))


def label(ax, x, y, text, fs=8.5, color=ACC):
    ax.text(x, y, text, fontsize=fs, color=color, weight="bold", family="monospace")


def environment(ax, x0, y0, w, h, n_shown, caption, two_queues):
    box(ax, x0, y0, w, h, "", fc="white")
    label(ax, x0 + 0.01, y0 + h - 0.035, "ENVIRONMENT")
    cx, cy, r = x0 + w * 0.5, y0 + h * 0.47, min(w, h) * 0.30
    ax.add_patch(Circle((cx, cy), 0.022, fc=ACC, ec="none"))
    ax.text(cx, cy - 0.045, "AP", ha="center", fontsize=8.5, color=INK, weight="bold")
    import math
    for i in range(n_shown):
        a = 2 * math.pi * i / n_shown + 0.3
        sx, sy = cx + r * math.cos(a) * 1.25, cy + r * math.sin(a)
        ax.add_patch(FancyBboxPatch((sx - 0.018, sy - 0.018), 0.036, 0.036,
                                    boxstyle="round,pad=0.002", fc=CARD, ec=ACC, lw=0.9))
        if two_queues:
            ax.plot([sx - 0.009, sx - 0.009], [sy - 0.011, sy + 0.011], color=ACC, lw=2)
            ax.plot([sx + 0.009, sx + 0.009], [sy - 0.011, sy + 0.011], color=PEAK, lw=2)
        else:
            ax.plot([sx, sx], [sy - 0.011, sy + 0.011], color=(ACC if i % 2 else PEAK), lw=2.4)
        arrow(ax, sx + (cx - sx) * 0.18, sy + (cy - sy) * 0.18, sx + (cx - sx) * 0.78,
              sy + (cy - sy) * 0.78, color=HAIR, lw=1.0)
    ax.text(x0 + w / 2, y0 + 0.022, caption, ha="center", fontsize=8, color=MUTED, linespacing=1.3)


def chain(ax, y0, h, inputs, model, outputs):
    w_in, w_mod, w_out = 0.30, 0.34, 0.30
    x_in, x_mod, x_out = 0.01, 0.01 + w_in + 0.02, 0.01 + w_in + w_mod + 0.04
    box(ax, x_in, y0, w_in, h, inputs, fs=8.6, ha="left")
    box(ax, x_mod, y0, w_mod, h, model, fc=CARD, ec=ACC, fs=8.6, ha="left")
    box(ax, x_out, y0, w_out, h, outputs, fs=8.6, ha="left")
    label(ax, x_in + 0.01, y0 + h - 0.03, "INPUTS")
    label(ax, x_mod + 0.01, y0 + h - 0.03, "ANALYTICAL MODEL")
    label(ax, x_out + 0.01, y0 + h - 0.03, "OUTPUTS / METRICS")
    arrow(ax, x_in + w_in, y0 + h / 2, x_mod, y0 + h / 2, color=ACC, lw=1.8)
    arrow(ax, x_mod + w_mod, y0 + h / 2, x_out, y0 + h / 2, color=ACC, lw=1.8)


def new_fig(title):
    fig = plt.figure(figsize=(13, 7.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0.15, 1)
    ax.axis("off")
    ax.text(0.01, 0.965, title, fontsize=13, weight="bold", color=INK)
    return fig, ax


# ------------------------------------------------------------------ Kong et al. 2004
fig, ax = new_fig("System model — Kong, Tsang, Bensaou & Gao, IEEE JSAC 2004 (EDCA, saturated)")
environment(ax, 0.01, 0.50, 0.40, 0.43, 8,
            "Infrastructure BSS, M stations, uplink to the AP\n"
            "ideal channel: no errors, no capture, no hidden nodes\nevery AC always has a frame (saturation)",
            two_queues=True)

# one station's MAC
x0, y0, w, h = 0.43, 0.50, 0.56, 0.43
box(ax, x0, y0, w, h, "", fc="white")
label(ax, x0 + 0.01, y0 + h - 0.035, "ONE STATION (MAC)")
box(ax, x0 + 0.02, y0 + 0.25, 0.14, 0.09, "AC3 queue\n(high priority)", fc=CARD, ec=ACC, fs=8.5)
box(ax, x0 + 0.02, y0 + 0.10, 0.14, 0.09, "AC1 queue\n(low priority)", fc="#fbeee3", ec=PEAK, fs=8.5)
box(ax, x0 + 0.19, y0 + 0.25, 0.15, 0.09, "EDCA function\nAIFS = 3 slots\nCW 15 → 127", fs=8)
box(ax, x0 + 0.19, y0 + 0.10, 0.15, 0.09, "EDCA function\nAIFS = 4 slots\nCW 31 → 255", fs=8)
box(ax, x0 + 0.37, y0 + 0.155, 0.08, 0.13, "virtual\ncollision\nhandler", fs=8)
box(ax, x0 + 0.47, y0 + 0.155, 0.075, 0.13, "PHY\n802.11b\n11 Mb/s", fs=8)
for yy in (0.295, 0.145):
    arrow(ax, x0 + 0.16, y0 + yy, x0 + 0.19, y0 + yy)
arrow(ax, x0 + 0.34, y0 + 0.295, x0 + 0.37, y0 + 0.24)
arrow(ax, x0 + 0.34, y0 + 0.145, x0 + 0.37, y0 + 0.20)
arrow(ax, x0 + 0.45, y0 + 0.22, x0 + 0.47, y0 + 0.22)
ax.text(x0 + 0.02, y0 + 0.035,
        "Both ACs back off independently. If they reach zero in the same slot, AC3 transmits and AC1\n"
        "suffers a virtual collision (doubles its CW as if it collided on air). RTS/CTS, one frame per TXOP.",
        fontsize=8, color=MUTED, linespacing=1.35)

chain(ax, 0.165, 0.31,
      "Stations M (5–30), or M3 / M1 per AC\n"
      "AIFS[AC3] = 3, AIFS[AC1] = 4 slots\n"
      "CW[AC3] = {15, 31, 63, 127}\n"
      "CW[AC1] = {31, 63, 127, 255}\n"
      "retry limit m + h (not reported)\n"
      "payload 1000 B, slot 20 µs, SIFS 1 slot\n"
      "data rate 11 Mb/s, RTS/CTS or basic",
      "3-D DTMC per AC:  (j, k, d)\n"
      "  j  backoff stage (−2, −1 special)\n"
      "  k  backoff counter\n"
      "  d  remaining freeze / tx / collision slots\n"
      "fixed point (eqs. 6–11):\n"
      "  τ_i ← p_i,  p_i = 1−(1−τ)^(M−1) Π(1−τ_i')\n"
      "  p_b = 1 − (1 − υ)^M\n"
      "delay: recursion over states (eqs. 18–22)",
      "Normalized throughput per AC  S_i  (eq. 12)\n"
      "Mean access delay per AC  D  (eq. 22)\n"
      "   first transmission attempt → success\n"
      "Access-delay distribution (simulation)\n"
      "Bandwidth per AC over time (simulation)\n\n"
      "Validation: NS-2 simulation")
fig.savefig(os.path.join(OUT, "kong_system_model.png"), dpi=130)
plt.close(fig)

# ------------------------------------------------------------------ Xiao 2005
fig, ax = new_fig("System model — Y. Xiao, IEEE Trans. Wireless Commun. 2005 (backoff-based priorities)")
environment(ax, 0.01, 0.50, 0.40, 0.43, 8,
            "Single-hop WLAN, N priority classes, n_i stations in class i\n"
            "each station belongs to one class and is always backlogged\n"
            "ideal channel, no hidden nodes (802.11a, 6 Mb/s)",
            two_queues=False)

x0, y0, w, h = 0.43, 0.50, 0.56, 0.43
box(ax, x0, y0, w, h, "", fc="white")
label(ax, x0 + 0.01, y0 + h - 0.035, "THREE BACKOFF KNOBS PER CLASS i")
rows = [("W_i,0", "initial window (CWmin)", "smaller → earlier access"),
        ("σ_i", "window-increasing factor", "W_i,j = σ_i^j · W_i,0 (DCF: σ = 2)"),
        ("L_i,retry", "retry limit", "frame dropped after L_i,retry + 1 attempts")]
for r, (sym, name, note) in enumerate(rows):
    yy = y0 + h - 0.12 - r * 0.085
    box(ax, x0 + 0.02, yy, 0.11, 0.065, sym, fc=CARD, ec=ACC, fs=10, weight="bold", color=ACC)
    ax.text(x0 + 0.15, yy + 0.042, name, fontsize=9.5, color=INK, weight="bold")
    ax.text(x0 + 0.15, yy + 0.014, note, fontsize=8.5, color=MUTED)
ax.text(x0 + 0.02, y0 + 0.035,
        "Higher priority i: W_i,0 ≤ W_j,0,  σ_i ≤ σ_j,  L_i ≤ L_j (at least one strict).\n"
        "EDCF case: σ = 2, same L, W_i,0 = CWmin[i]; AIFS differentiation is not modelled.",
        fontsize=8, color=MUTED, linespacing=1.35)

chain(ax, 0.165, 0.31,
      "Classes N (paper: 2) and n_i (5–40)\n"
      "W_i,0 = [16, 32],  CWmax = 1024\n"
      "σ_i = [1.7, 2]\n"
      "L_i,retry = [4, 7]\n"
      "frame 1024 B, basic access\n"
      "802.11a: 6 Mb/s data and control\n"
      "(slot, SIFS, DIFS from the 802.11a PHY)",
      "2-D DTMC per class:  {i, j, k}\n"
      "  j  backoff stage 0 … L_i,retry\n"
      "  k  backoff counter 0 … W_i,j − 1\n"
      "  counter frozen while the channel is busy\n"
      "fixed point (eqs. 5–7):\n"
      "  τ_i = b_i,0,0 (1 − p_i^(L+1)) / (1 − p_i)\n"
      "  p_i = 1 − Π_h (1 − τ_h)^(n_h − [h = i])\n"
      "p_b, p_s,i (eqs. 8–10)",
      "Saturation throughput  S_i  (eq. 11)\n"
      "Saturation delay  E[D_i]  (eq. 21)\n"
      "   access + transmission + IFS\n"
      "Frame-dropping prob.  p_i^(L+1)  (eq. 16)\n\n"
      "Validation: OPNET 8.0A simulation\n"
      "(>95 % confidence intervals, Table I)")
fig.savefig(os.path.join(OUT, "xiao_system_model.png"), dpi=130)
plt.close(fig)
print("wrote kong_system_model.png, xiao_system_model.png")
