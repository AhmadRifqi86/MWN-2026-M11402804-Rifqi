#!/usr/bin/env python3
"""A4 — Xiao (IEEE TWC 2005) reproduced in ns-3.48 (xiao-priority.cc + txop-cw-growth.patch).

Input  : xiao_sweep.csv (run_xiao_sweep.sh: 29 points x 10 seeds)
Outputs: assets/img/a4/a4_xiao_fig2-4_ns3.png  (paper Figs. 2-4 axes: S, delay, P_drop vs n)
         assets/img/a4/a4_xiao_knobs_ns3.png   (paper Figs. 5, 7, 9: one knob at a time)
Paper references: Table I (analysis and OPNET, exact numbers), the analytical curves recomputed
with xiao_model.py (within ~1 % of the paper's analysis, see §7), and the few points of
Figs. 5, 7, 9 read off by eye.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from xiao_model import solve

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets", "img", "a4")
C = ("#2f63e6", "#d97a2b")
GREY = "#586274"

df = pd.read_csv(os.path.join(HERE, "xiao_sweep.csv"))

# Table I of the paper (n0 = n1 = 10 and 30): analysis and OPNET simulation
TAB = {10: dict(S_ana=(0.520821, 0.154653), S_sim=(0.5161, 0.1532),
                D_ana=(25.08226, 86.49521), D_sim=(25.53374, 88.39810)),
       30: dict(S_ana=(0.465941, 0.101312), S_sim=(0.4638, 0.1008),
                D_ana=(67.00055, 342.34130), D_sim=(67.73756, 348.84578))}


def agg(sub, key):
    g = sub.groupby(key)
    out = {}
    for col in ("S0", "S1", "D0_ms", "D1_ms", "P0", "P1"):
        out[col] = (g[col].mean(), 1.96 * g[col].std() / np.sqrt(g.size()))
    return out


def ns3(ax, x, mu, ci, color, label=None):
    ax.errorbar(x, mu, yerr=ci, fmt="^", color=color, mfc="white", ms=6, capsize=3, mew=1.4,
                ls="none", label=label)


# ------------------------------------------------------------------ Figs. 2-4
sub = df[df.exp == "fig2-4"]
a = agg(sub, "n0")
ns = np.arange(5, 41)
mod = [solve([n, n], [16, 32], [1.7, 2.0], [4, 7], [1024, 1024]) for n in ns]
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
for c in (0, 1):
    for k, (col, scale) in enumerate((("S", 1), ("delay_us", 1e-3), ("drop", 1))):
        ax[k].plot(ns, [m[c][col] * scale for m in mod], "-", color=C[c], lw=1.4,
                   label=f"class {c}: Xiao analysis (recomputed)")
    for k, col in enumerate((f"S{c}", f"D{c}_ms", f"P{c}")):
        mu, ci = a[col]
        ns3(ax[k], mu.index, mu, ci, C[c], label=f"class {c}: ns-3.48 (10 seeds)")
    for n in (10, 30):
        for k, key in ((0, "S"), (1, "D")):
            ax[k].plot(n, TAB[n][f"{key}_ana"][c], "s", mfc="none", mec=C[c], ms=9, mew=1.5)
            ax[k].plot(n, TAB[n][f"{key}_sim"][c], "x", color=C[c], ms=9, mew=1.8)
ax[0].plot([], [], "s", mfc="none", mec=GREY, ms=9, label="paper Table I, analysis")
ax[0].plot([], [], "x", color=GREY, ms=9, label="paper Table I, OPNET")
ax[0].set(title="(a) Saturation throughput — paper Fig. 2", ylabel="normalized throughput S")
ax[1].set(title="(b) Saturation delay — paper Fig. 3", ylabel="delay [ms]")
ax[2].set(title="(c) Frame-dropping probability — paper Fig. 4", ylabel="P_drop")
for x in ax:
    x.set(xlabel="number of stations per class n (n0 = n1)", xlim=(4, 41))
    x.grid(alpha=0.3)
ax[0].set_ylim(0, 0.7)
ax[0].legend(fontsize=7.5, loc="upper right")
fig.suptitle("Xiao 2005, combined scheme (W0 = 16/32, σ = 1.7/2, L = 4/7, CWmax = 1024, 802.11a "
             "6 Mb/s, 1024 B) — ns-3.48 vs the paper", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "a4_xiao_fig2-4_ns3.png"), dpi=130)
plt.close(fig)

# ------------------------------------------------------------------ Figs. 5, 7, 9
KNOBS = [("fig5", "W0_1", "initial window of class 1, W1,0", "(a) paper Fig. 5",
          lambda v: solve([10, 10], [16, v], [2, 2], [7, 7], [1024, 1024]),
          {16: (0.34, 0.34)}),
         ("fig7", "sigma1", "window-increasing factor of class 1, σ1", "(b) paper Fig. 7",
          lambda v: solve([10, 10], [16, 16], [2, v], [7, 7], [1024, 1024]),
          {2.0: (0.325, None), 1.6: (0.18, None)}),
         ("fig9", "L1", "retry limit of class 1, L1", "(c) paper Fig. 9",
          lambda v: solve([10, 10], [16, 16], [2, 2], [8, int(v)], [1024, 1024]),
          {0: (0.09, 0.53)})]
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
for k, (exp, key, xlabel, title, model, read) in enumerate(KNOBS):
    sub = df[df.exp == exp]
    a = agg(sub, key)
    xs = np.linspace(sub[key].min(), sub[key].max(), 41) if exp == "fig7" else np.sort(sub[key].unique())
    mod = [model(v) for v in xs]
    for c in (0, 1):
        ax[k].plot(xs, [m[c]["S"] for m in mod], "-", color=C[c], lw=1.4,
                   label=f"class {c}: Xiao analysis (recomputed)")
        mu, ci = a[f"S{c}"]
        ns3(ax[k], mu.index, mu, ci, C[c], label=f"class {c}: ns-3.48")
        for xv, vals in read.items():
            if vals[c] is not None:
                ax[k].plot(xv, vals[c], "D", color=C[c], ms=7, alpha=0.6)
    ax[k].plot([], [], "D", color=GREY, alpha=0.6, ms=7, label="paper figure (read off)")
    ax[k].set(title=title, xlabel=xlabel, ylabel="normalized throughput S", ylim=(0, 0.65))
    ax[k].grid(alpha=0.3)
ax[0].legend(fontsize=7.5)
fig.suptitle("Xiao 2005, one knob at a time (n0 = n1 = 10) — ns-3.48 vs the paper", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "a4_xiao_knobs_ns3.png"), dpi=130)
plt.close(fig)

# ------------------------------------------------------------------ console summary
sub = df[df.exp == "fig2-4"]
print("runs", len(df), "| all associated:", bool((df.associated == df.n0 + df.n1).all()))
s = sub.groupby("n0").agg(S0=("S0", "mean"), S1=("S1", "mean"), D0=("D0_ms", "mean"),
                          D1=("D1_ms", "mean"), P0=("P0", "mean"), P1=("P1", "mean"),
                          a0=("acked0", "min"), a1=("acked1", "min"))
print(s.round(4).to_string())
for n in (10, 30):
    r = s.loc[n]
    m = solve([n, n], [16, 32], [1.7, 2.0], [4, 7], [1024, 1024])
    for c in (0, 1):
        for key, val, ana, sim in (("S", r[f"S{c}"], TAB[n]["S_ana"][c], TAB[n]["S_sim"][c]),
                                   ("D", r[f"D{c}"], TAB[n]["D_ana"][c], TAB[n]["D_sim"][c])):
            print(f"n={n} class{c} {key}: ns-3 {val:.4f}  paper ana {ana:.4f} ({100*(val-ana)/ana:+.1f} %)"
                  f"  OPNET {sim:.4f} ({100*(val-sim)/sim:+.1f} %)")
        print(f"n={n} class{c} P: ns-3 {r[f'P{c}']:.4f}  model {m[c]['drop']:.4f}")
for col in ("S0", "S1", "D0_ms", "D1_ms"):
    g = df.groupby(["exp", "n0", "W0_1", "sigma1", "L1"])[col]
    print(col, "max CI / mean %:", round((1.96 * g.std() / np.sqrt(g.size()) / g.mean()).max() * 100, 2))
for exp, key, *_ in KNOBS:
    sub = df[df.exp == exp].groupby(key)[["S0", "S1"]].mean()
    print(exp, sub.round(3).to_dict("list"))
