#!/usr/bin/env python3
"""Compare the ns-3 reproduction of Kong et al. (IEEE JSAC 2004) with the paper's Fig. 7-8.

Inputs : kong_ns3_sweep.csv (kong-edca runs, M = 5..30, 5 seeds), delays_n15.csv (M = 15)
Output : assets/img/a3/kong_ns3_vs_paper.png
Paper values are read off Fig. 7 (analysis curves) by eye: approximate, +/- ~0.01 / ~3 ms.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets", "img", "a3")
AC3, AC1 = "#2f63e6", "#d97a2b"

M = np.array([5, 10, 15, 20, 25, 30])
paper = {  # read off Kong Fig. 7 (approximate)
    "S_ac3": [0.58, 0.595, 0.60, 0.605, 0.605, 0.605],
    "S_ac1": [0.12, 0.095, 0.08, 0.07, 0.065, 0.06],
    "D_ac3": [7, 10, 13, 16, 19, 22],
    "D_ac1": [36, 71, 108, 147, 188, 230],
}

df = pd.read_csv(os.path.join(HERE, "kong_ns3_sweep.csv"))
g = df.groupby("M")
mean = g.mean(numeric_only=True)
ci = 1.96 * g.std(numeric_only=True) / np.sqrt(g.size().values[:, None])  # 95 % CI


def ns3(ax, col, color, label, scale=1.0):
    ax.errorbar(mean.index, mean[col] * scale, yerr=ci[col] * scale, fmt="-o", color=color,
                ms=4, capsize=3, label=label)


fig, ax = plt.subplots(1, 4, figsize=(19, 4.4))
# (a) absolute normalized throughput
ns3(ax[0], "S_ac3", AC3, "AC3 ns-3")
ns3(ax[0], "S_ac1", AC1, "AC1 ns-3")
ax[0].plot(M, paper["S_ac3"], "--s", color=AC3, mfc="none", label="AC3 paper Fig. 7a")
ax[0].plot(M, paper["S_ac1"], "--s", color=AC1, mfc="none", label="AC1 paper Fig. 7a")
ax[0].set(title="Normalized throughput", xlabel="stations M (one AC3 + one AC1 each)",
          ylabel="throughput / 11 Mb/s", ylim=(0, 0.8))

# (b) share of the total throughput taken by AC3 — insensitive to the PHY-overhead gap
share_ns3 = df.assign(sh=df.S_ac3 / (df.S_ac3 + df.S_ac1)).groupby("M").sh
ax[1].errorbar(M, share_ns3.mean(), yerr=1.96 * share_ns3.std() / np.sqrt(share_ns3.size()),
               fmt="-o", color=AC3, ms=4, capsize=3, label="ns-3")
ax[1].plot(M, np.array(paper["S_ac3"]) / (np.array(paper["S_ac3"]) + np.array(paper["S_ac1"])),
           "--s", color=AC3, mfc="none", label="paper Fig. 7a")
ax[1].set(title="AC3 share of total throughput", xlabel="stations M", ylabel="S_AC3 / (S_AC3 + S_AC1)",
          ylim=(0.7, 1.0))

# (c) mean access delay
ns3(ax[2], "D_ac3_ms", AC3, "AC3 ns-3")
ns3(ax[2], "D_ac1_ms", AC1, "AC1 ns-3")
ax[2].plot(M, paper["D_ac3"], "--s", color=AC3, mfc="none", label="AC3 paper Fig. 7b")
ax[2].plot(M, paper["D_ac1"], "--s", color=AC1, mfc="none", label="AC1 paper Fig. 7b")
ax[2].set(title="Mean access delay", xlabel="stations M", ylabel="delay [ms]")

# (d) access-delay CDF at M = 15 (paper Fig. 8b)
d = pd.read_csv(os.path.join(HERE, "delays_n15.csv"))
for ac, color in (("AC3", AC3), ("AC1", AC1)):
    x = np.sort(d[d.ac == ac].delay_ms.values)
    ax[3].step(x, np.arange(1, len(x) + 1) / len(x) * 100, where="post", color=color,
               label=f"{ac} ns-3 (n={len(x)})")
ax[3].set(title="Access-delay CDF, M = 15 (paper Fig. 8b)", xlabel="access delay [ms]",
          ylabel="cumulative fraction [%]", xlim=(0, 500))

for a in ax:
    a.grid(alpha=0.3)
    a.legend(fontsize=7.5)
fig.suptitle("Kong et al. 2004 in ns-3.48 (802.11b, Table I EDCA settings, RTS/CTS, 5 seeds, 95 % CI) "
             "vs paper Fig. 7-8", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "kong_ns3_vs_paper.png"), dpi=130)

print(mean[["S_ac3", "S_ac1", "D_ac3_ms", "D_ac1_ms"]].round(4).to_string())
print("AC3 share ns-3:", share_ns3.mean().round(3).to_dict())
for ac in ("AC3", "AC1"):
    x = d[d.ac == ac].delay_ms.values
    print(ac, "CDF: P(<=50ms)=%.1f%%  P(<=100ms)=%.1f%%  P(<=300ms)=%.1f%%"
          % tuple(100 * np.mean(x <= t) for t in (50, 100, 300)))
