#!/usr/bin/env python3
"""Reproduce the numerical results of Xiao (IEEE TWC 2005), Figs. 2-11 and Table I,
with xiao_model.py. Writes PNGs to assets/img/a4/."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from xiao_model import solve

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "img", "a4")
os.makedirs(OUT, exist_ok=True)
C0, C1, TOT = "#2f63e6", "#d97a2b", "#555555"


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)


# ---------- Figs. 2-4 + Table I: combined scheme vs number of stations ----------
ns = np.arange(5, 41, 5)
res = [solve([n, n], [16, 32], [1.7, 2.0], [4, 7], [1024, 1024]) for n in ns]
S = np.array([[r[c]["S"] for c in (0, 1)] for r in res])
D = np.array([[r[c]["delay_us"] for c in (0, 1)] for r in res])
P = np.array([[r[c]["drop"] for c in (0, 1)] for r in res])

table_n = [10, 30]
tab_S_ana = [[0.520821, 0.154653], [0.465941, 0.101312]]
tab_S_sim = [[0.5161, 0.1532], [0.4638, 0.1008]]
tab_D_ana = [[25082.26, 86495.21], [67000.55, 342341.30]]
tab_D_sim = [[25533.74, 88398.10], [67737.56, 348845.78]]

fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
for c, col in ((0, C0), (1, C1)):
    ax[0].plot(ns, S[:, c], "-o", color=col, ms=4, label=f"class {c} (this model)")
    ax[1].plot(ns, D[:, c] / 1e3, "-o", color=col, ms=4, label=f"class {c} (this model)")
    ax[2].plot(ns, P[:, c], "-o", color=col, ms=4, label=f"class {c} (this model)")
    ax[0].scatter(table_n, [t[c] for t in tab_S_ana], marker="s", s=60, facecolors="none",
                  edgecolors=col, label=f"class {c} paper analysis (Table I)")
    ax[0].scatter(table_n, [t[c] for t in tab_S_sim], marker="x", s=60, color=col,
                  label=f"class {c} paper simulation (Table I)")
    ax[1].scatter(table_n, [t[c] / 1e3 for t in tab_D_ana], marker="s", s=60, facecolors="none",
                  edgecolors=col)
    ax[1].scatter(table_n, [t[c] / 1e3 for t in tab_D_sim], marker="x", s=60, color=col)
style(ax[0], "Saturation throughput (paper Fig. 2)", "number of stations per class n", "normalized throughput S")
style(ax[1], "Saturation delay (paper Fig. 3)", "number of stations per class n", "delay [ms]")
style(ax[2], "Frame-dropping probability (paper Fig. 4)", "number of stations per class n", "P_drop")
ax[0].legend(fontsize=7)
ax[2].legend(fontsize=7)
fig.suptitle("Xiao 2005 reproduced: σ=[1.7, 2], L_retry=[4, 7], W0=[16, 32], CWmax=1024, "
             "802.11a 6 Mb/s, 1024-byte frames", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "xiao_fig2-4_vs_stations.png"), dpi=130)

# ---------- Figs. 5, 7, 9: one metric differentiated at a time (n0 = n1 = 10) ----------
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
w1 = np.arange(16, 57, 8)
r = [solve([10, 10], [16, w], [2, 2], [7, 7], [1024, 1024]) for w in w1]
ax[0].plot(w1, [x[0]["S"] for x in r], "-o", color=C0, ms=4, label="class 0")
ax[0].plot(w1, [x[1]["S"] for x in r], "-o", color=C1, ms=4, label="class 1")
ax[0].plot(w1, [x[0]["S"] + x[1]["S"] for x in r], "--", color=TOT, label="total")
style(ax[0], "Initial window W1,0 (paper Fig. 5)", "CWmin of class 1", "normalized throughput S")

sig = np.round(np.arange(1.6, 2.61, 0.2), 2)
r = [solve([10, 10], [16, 16], [2, s], [7, 7], [1024, 1024]) for s in sig]
ax[1].plot(sig, [x[0]["S"] for x in r], "-o", color=C0, ms=4, label="class 0")
ax[1].plot(sig, [x[1]["S"] for x in r], "-o", color=C1, ms=4, label="class 1")
style(ax[1], "Window-increasing factor σ1 (paper Fig. 7)", "σ of class 1", "normalized throughput S")

lr = np.arange(0, 9)
r = [solve([10, 10], [16, 16], [2, 2], [8, int(l)], [1024, 1024]) for l in lr]
ax[2].plot(lr, [x[0]["S"] for x in r], "-o", color=C0, ms=4, label="class 0")
ax[2].plot(lr, [x[1]["S"] for x in r], "-o", color=C1, ms=4, label="class 1")
style(ax[2], "Retry limit L1 (paper Fig. 9)", "retry limit of class 1", "normalized throughput S")
for a in ax:
    a.legend(fontsize=8)
fig.suptitle("Xiao 2005 reproduced: each backoff knob alone, n0 = n1 = 10", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "xiao_fig5-7-9_knobs.png"), dpi=130)

print("Fig.5 anchor (W1,0=16): S0=%.3f S1=%.3f (paper both ~0.34)"
      % (solve([10, 10], [16, 16], [2, 2], [7, 7], [1024, 1024])[0]["S"],
         solve([10, 10], [16, 16], [2, 2], [7, 7], [1024, 1024])[1]["S"]))
print("Fig.7 anchor (sigma1=2): S=%.3f (paper ~0.325)"
      % solve([10, 10], [16, 16], [2, 2], [7, 7], [1024, 1024])[0]["S"])
x = solve([10, 10], [16, 16], [2, 2], [8, 0], [1024, 1024])
print("Fig.9 anchor (L1=0): S0=%.3f S1=%.3f (paper ~0.09 / ~0.53)" % (x[0]["S"], x[1]["S"]))
print("wrote", sorted(f for f in os.listdir(OUT) if f.startswith("xiao")))
