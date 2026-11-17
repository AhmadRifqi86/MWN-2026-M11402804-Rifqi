#!/usr/bin/env python3
"""A4 — Kong et al. (IEEE JSAC 2004) Fig. 7 reproduced in ns-3.48, plotted against the paper.

Input  : kong_fig7_sweep.csv (kong-edca runs: 3 variants x M = 5..30 x seeds 1..10)
         kong_retry_sensitivity.csv (Table I PHY, retry limit 2..7 attempts, M = 15 and 30, 3 seeds)
Outputs: assets/img/a4/a4_fig7_reproduction.png  (same axes as the paper's Fig. 7a, 7b)
         assets/img/a4/a4_explain.png            (AC3 share; Little's-law check; retry limit)
Paper values are read off Fig. 7 by eye: approximate, +/- ~0.01 throughput and ~3 ms delay.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets", "img", "a4")
AC3, AC1, GREY = "#2f63e6", "#d97a2b", "#586274"
PAYLOAD_BITS, RATE = 8000, 11e6

M = np.array([5, 10, 15, 20, 25, 30])
paper = {  # read off Kong Fig. 7: "ana" = analytical curve, "sim" = NS-2 points
    "S_ac3_ana": [0.58, 0.59, 0.60, 0.603, 0.605, 0.605],
    "S_ac1_ana": [0.12, 0.095, 0.08, 0.07, 0.065, 0.06],
    "S_ac3_sim": [0.58, 0.59, 0.60, 0.603, 0.605, 0.605],
    "S_ac1_sim": [0.12, 0.09, 0.07, 0.055, 0.045, 0.035],
    "D_ac3_ana": [8, 12, 15, 18, 21, 24],
    "D_ac1_ana": [36, 71, 108, 147, 188, 230],
    "D_ac3_sim": [6, 11, 14, 16, 18, 17],
    "D_ac1_sim": [28, 62, 97, 135, 178, 210],
}
paper = {k: np.array(v, dtype=float) for k, v in paper.items()}

df = pd.read_csv(os.path.join(HERE, "kong_fig7_sweep.csv"))
df["share"] = df.S_ac3 / (df.S_ac3 + df.S_ac1)
VARIANTS = [((0, 7), "ns-3, 802.11b PHY", "-o", None),
            ((1, 7), "ns-3, Table I PHY", "-^", "white"),
            ((1, 4), "ns-3, Table I PHY, 4 attempts", "--s", "white")]


def sel(v):
    return df[(df.ideal_plcp == v[0]) & (df.retry == v[1])]


def stats(v, col):
    g = sel(v).groupby("M")[col]
    return g.mean(), 1.96 * g.std() / np.sqrt(g.size())


def little_ms(S, m):
    """Mean head-of-line time per delivered frame implied by throughput S under saturation."""
    return m * PAYLOAD_BITS / (S * RATE) * 1e3


# ------------------------------------------------------------------ Fig. 7 (same axes)
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
for v, label, fmt, mfc in VARIANTS:
    for col, color, name in (("S_ac3", AC3, "AC3"), ("S_ac1", AC1, "AC1")):
        mu, ci = stats(v, col)
        ax[0].errorbar(mu.index, mu, yerr=ci, fmt=fmt, color=color, mfc=mfc, ms=5, capsize=3,
                       lw=1.4, label=f"{name} {label}")
    for col, color, name in (("D_ac3_ms", AC3, "AC3"), ("D_ac1_ms", AC1, "AC1")):
        mu, ci = stats(v, col)
        ax[1].errorbar(mu.index, mu, yerr=ci, fmt=fmt, color=color, mfc=mfc, ms=5, capsize=3,
                       lw=1.4, label=f"{name} {label}")
for name, color in (("ac3", AC3), ("ac1", AC1)):
    ax[0].plot(M, paper[f"S_{name}_ana"], ":", color=color, lw=1.6, label=f"{name.upper()} paper analysis")
    ax[0].plot(M, paper[f"S_{name}_sim"], "D", color=color, ms=4.5, alpha=0.55,
               label=f"{name.upper()} paper NS-2")
    ax[1].plot(M, paper[f"D_{name}_ana"], ":", color=color, lw=1.6, label=f"{name.upper()} paper analysis")
    ax[1].plot(M, paper[f"D_{name}_sim"], "D", color=color, ms=4.5, alpha=0.55,
               label=f"{name.upper()} paper NS-2")
ax[0].set(title="(a) Normalized throughput  —  paper Fig. 7(a)", xlim=(5, 30), ylim=(0, 1),
          xlabel="Number of stations (one AC3 and one AC1 per station)",
          ylabel="Normalized throughput of each AC")
ax[1].set(title="(b) Mean access delay  —  paper Fig. 7(b)", xlim=(5, 30),
          xlabel="Number of stations (one AC3 and one AC1 per station)",
          ylabel="Mean access delay of each AC (ms)")
ax[1].set_ylim(0, 350)
ax[1].axhline(250, color=GREY, lw=0.8, ls="--")
ax[1].text(5.3, 256, "paper's axis limit (250 ms)", fontsize=8, color=GREY)
for a in ax:
    a.grid(alpha=0.3)
ax[0].legend(fontsize=7.2, ncol=2, loc="upper center")
ax[1].legend(fontsize=7.2, ncol=2, loc="upper left")
fig.suptitle("Kong et al. 2004, Fig. 7 — ns-3.48 (10 seeds, 30 s each, 95 % CI) vs the paper; "
             "retry limit 7 attempts unless stated",
             fontsize=11.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "a4_fig7_reproduction.png"), dpi=130)
plt.close(fig)

# ------------------------------------------------------------------ explanations
fig, ax = plt.subplots(1, 3, figsize=(17, 4.9))
for v, label, fmt, mfc in VARIANTS:
    mu, ci = stats(v, "share")
    ax[0].errorbar(mu.index, mu, yerr=ci, fmt=fmt, color=AC3 if v[0] else GREY, mfc=mfc,
                   ms=5, capsize=3, label=label)
ax[0].plot(M, paper["S_ac3_ana"] / (paper["S_ac3_ana"] + paper["S_ac1_ana"]), ":", color=AC1, lw=1.8,
           label="paper analysis")
ax[0].plot(M, paper["S_ac3_sim"] / (paper["S_ac3_sim"] + paper["S_ac1_sim"]), "D", color=AC1, ms=5,
           alpha=0.6, label="paper NS-2")
ax[0].set(title="(a) AC3 share of the total throughput", xlabel="Number of stations M",
          ylabel="S_AC3 / (S_AC3 + S_AC1)", xlim=(5, 30), ylim=(0.75, 1.0))

# (b) measured delay vs the delay implied by the throughput (Little's law, saturation)
lim = 400
ax[1].plot([0, lim], [0, lim], color=GREY, lw=1, label="measured = M·L / (S·R)")
for v, label, fmt, mfc in VARIANTS:
    d = sel(v).groupby("M").mean(numeric_only=True)
    for col_s, col_d, color in (("S_ac3", "D_ac3_ms", AC3), ("S_ac1", "D_ac1_ms", AC1)):
        ax[1].plot(little_ms(d[col_s], d.index), d[col_d], fmt.lstrip("-"), color=color,
                   mfc=mfc or color, ms=6, ls="none")
for name, color in (("ac3", AC3), ("ac1", AC1)):
    ax[1].plot(little_ms(paper[f"S_{name}_ana"], M), paper[f"D_{name}_ana"], "*", color=color, ms=10)
    ax[1].plot(little_ms(paper[f"S_{name}_sim"], M), paper[f"D_{name}_sim"], "D", color=color, ms=5,
               alpha=0.6)
for v, label, fmt, mfc in VARIANTS:
    ax[1].plot([], [], fmt.lstrip("-"), color=GREY, mfc=mfc or GREY, label=label)
ax[1].plot([], [], "*", color=GREY, ms=10, label="paper analysis")
ax[1].plot([], [], "D", color=GREY, alpha=0.6, label="paper NS-2")
ax[1].set(title="(b) Delivered-frame delay vs M·L/(S·R) (blue AC3, orange AC1)",
          xlabel="M · payload / (S · 11 Mb/s)  [ms]", ylabel="reported mean access delay [ms]",
          xlim=(0, lim), ylim=(0, lim))
# (c) retry limit: dropping the frames that wait longest shortens the delivered-frame delay
rs = pd.read_csv(os.path.join(HERE, "kong_retry_sensitivity.csv"))
for col_s, col_d, color, name in (("S_ac3", "D_ac3_ms", AC3, "AC3"), ("S_ac1", "D_ac1_ms", AC1, "AC1")):
    rs[name] = rs[col_d] / little_ms(rs[col_s], rs.M)
    for m, fmt in ((15, ":o"), (30, "-o")):
        r = rs[rs.M == m].groupby("retry")[name].mean()
        ax[2].plot(r.index, r, fmt, color=color, ms=5, label=f"ns-3 {name}, M = {m}")
k = list(M).index(30)
for name, color in (("ac3", AC3), ("ac1", AC1)):
    ana = paper[f"D_{name}_ana"][k] / little_ms(paper[f"S_{name}_ana"][k], 30)
    sim = paper[f"D_{name}_sim"][k] / little_ms(paper[f"S_{name}_sim"][k], 30)
    ax[2].axhline(ana, color=color, ls=":", lw=1.2)
    ax[2].axhline(sim, color=color, ls="--", lw=1, alpha=0.6)
ax[2].plot([], [], ":", color=GREY, label="paper analysis, M = 30")
ax[2].plot([], [], "--", color=GREY, alpha=0.6, label="paper NS-2, M = 30")
ax[2].set(title="(c) Retry limit vs delay / Little's-law delay (Table I PHY)",
          xlabel="retry limit (transmission attempts)", ylabel="D / (M·L / (S·R))", ylim=(0.3, 1.05))
for a in ax:
    a.grid(alpha=0.3)
    a.legend(fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "a4_explain.png"), dpi=130)
plt.close(fig)

# ------------------------------------------------------------------ console summary
summ = df.groupby(["ideal_plcp", "retry", "M"]).agg(
    S_ac3=("S_ac3", "mean"), S_ac1=("S_ac1", "mean"), D_ac3=("D_ac3_ms", "mean"),
    D_ac1=("D_ac1_ms", "mean"), share=("share", "mean"), drop_ac3=("drop_ac3", "sum"),
    drop_ac1=("drop_ac1", "sum"), runs=("seed", "count"), assoc_min=("associated", "min"))
print(summ.round(4).to_string())
for v, *_ in VARIANTS:
    d = sel(v).groupby("M").mean(numeric_only=True)
    print("variant", v, "D/Little AC3:", (d.D_ac3_ms / little_ms(d.S_ac3, d.index)).round(3).tolist(),
          "AC1:", (d.D_ac1_ms / little_ms(d.S_ac1, d.index)).round(3).tolist())
for k in ("ana", "sim"):
    print("paper", k, "D/Little AC3:", (paper[f"D_ac3_{k}"] / little_ms(paper[f"S_ac3_{k}"], M)).round(2).tolist(),
          "AC1:", (paper[f"D_ac1_{k}"] / little_ms(paper[f"S_ac1_{k}"], M)).round(2).tolist())
