#!/usr/bin/env python3
"""Analytical model of Y. Xiao, "Performance analysis of priority schemes for IEEE 802.11
and IEEE 802.11e wireless LANs," IEEE Trans. Wireless Commun., 4(4):1506-1515, 2005.

Implements eqs. (1)-(21): per-class saturation throughput S_i, saturation delay E[D_i]
and frame-dropping probability P_i,drop for N backoff-differentiated priority classes.

PHY: IEEE 802.11a at 6 Mb/s (data and control), frame payload 1024 bytes, basic access,
as in Sections V-VI of the paper.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import fsolve


# ---------------- IEEE 802.11a OFDM timing (6 Mb/s) ----------------
SLOT = 9e-6          # delta
SIFS = 16e-6
DIFS = SIFS + 2 * SLOT   # 34 us
T_PREAMBLE = 16e-6
T_SIGNAL = 4e-6
T_SYM = 4e-6
N_DBPS = 24          # data bits per OFDM symbol at 6 Mb/s
MAC_HDR = 28         # MAC header + FCS (bytes)
ACK_LEN = 14         # bytes


def ofdm_time(nbytes):
    """Air time of a PPDU carrying nbytes of MAC data (preamble+SIGNAL+service+tail)."""
    nsym = math.ceil((16 + 8 * nbytes + 6) / N_DBPS)
    return T_PREAMBLE + T_SIGNAL + nsym * T_SYM


@dataclass
class Timing:
    payload: int = 1024

    @property
    def T_payload(self):           # T_E(L): time to transmit the payload itself
        return 8 * self.payload / 6e6

    @property
    def T_frame(self):             # T_H + T_E(L)
        return ofdm_time(MAC_HDR + self.payload)

    @property
    def T_ack(self):
        return ofdm_time(ACK_LEN)

    @property
    def Ts(self):                  # eq. (12), basic access
        return self.T_frame + SIFS + self.T_ack + DIFS

    @property
    def Tc(self):                  # eq. (13), basic access, L* = L (fixed frame size)
        return self.T_frame + SIFS + self.T_ack + DIFS

    @property
    def To(self):                  # eq. (22): SIFS + ACK timeout (timeout ~ ACK time + slot)
        return SIFS + self.T_ack + SLOT


def windows(W0, sigma, L, cwmax):
    """Eq. (1): window size W_{i,j}, j = 0..L."""
    m = math.log(cwmax / W0, sigma)
    return np.array([min(sigma ** j * W0, cwmax) if j > m else sigma ** j * W0
                     for j in range(L + 1)])


def tau_of_p(p, W):
    """Eqs. (5)-(6): transmission probability for a class given its collision prob p."""
    L = len(W) - 1
    j = np.arange(L + 1)
    denom = np.sum((1 + (W - 1) / (2 * (1 - p))) * p ** j)   # sum_k (W-k)/W = (W-1)/2
    b000 = 1 / denom
    return b000 * (1 - p ** (L + 1)) / (1 - p)


def solve(n, W0, sigma, L, cwmax, timing=Timing()):
    """Solve the fixed point and return per-class metrics.
    n, W0, sigma, L, cwmax: per-class lists (class 0 = highest priority)."""
    N = len(n)
    Ws = [windows(W0[i], sigma[i], L[i], cwmax[i]) for i in range(N)]

    def p_of_tau(tau):
        p = np.empty(N)
        for i in range(N):
            prod = 1.0
            for h in range(N):
                prod *= (1 - tau[h]) ** (n[h] - 1 if h == i else n[h])
            p[i] = 1 - prod                                     # eq. (7)
        return p

    def F(p):
        p = np.clip(p, 1e-9, 1 - 1e-9)
        tau = np.array([tau_of_p(p[i], Ws[i]) for i in range(N)])
        return p_of_tau(tau) - p

    p = fsolve(F, np.full(N, 0.3), xtol=1e-13)
    tau = np.array([tau_of_p(p[i], Ws[i]) for i in range(N)])
    pb = 1 - np.prod([(1 - tau[h]) ** n[h] for h in range(N)])          # eq. (8)
    ps_i = np.array([n[i] * tau[i] * (1 - tau[i]) ** (n[i] - 1)
                     * np.prod([(1 - tau[h]) ** n[h] for h in range(N) if h != i])
                     for i in range(N)])                                  # eq. (9)
    ps = ps_i.sum()                                                       # eq. (10)
    t = timing
    Eslot = (1 - pb) * SLOT + ps * t.Ts + (pb - ps) * t.Tc
    S = ps_i * t.T_payload / Eslot                                       # eq. (11)

    out = []
    for i in range(N):
        W, Li, pi = Ws[i], L[i], p[i]
        j = np.arange(Li + 1)
        cond = pi ** j * (1 - pi) / (1 - pi ** (Li + 1))
        EX = np.sum(cond * np.array([np.sum((W[:jj + 1] - 1) / 2) for jj in j]))  # eq. (18)
        EB = EX / (1 - pi) * pi                                                 # eq. (19)
        EN = np.sum(j * cond)                                                   # eq. (20)
        ED = (EX * SLOT + EB * (ps / pb * t.Ts + (pb - ps) / pb * t.Tc)
              + EN * (t.Tc + t.To) + t.Ts)                                      # eq. (21)
        out.append(dict(S=S[i], delay_us=ED * 1e6, p=pi, tau=tau[i],
                        drop=pi ** (Li + 1)))                                   # eq. (16)
    return out


if __name__ == "__main__":
    # Table I of the paper: [sigma0, sigma1] = [1.7, 2], [L0, L1] = [4, 7],
    # [W00, W10] = [16, 32], CWmax = 1024, n0 = n1
    paper = {10: ((0.520821, 25082.262785), (0.154653, 86495.210138)),
             30: ((0.465941, 67000.549513), (0.101312, 342341.299834))}
    for n in (10, 30):
        res = solve([n, n], [16, 32], [1.7, 2.0], [4, 7], [1024, 1024])
        for c in (0, 1):
            S_p, D_p = paper[n][c]
            print(f"n={n} class{c}: S={res[c]['S']:.6f} (paper {S_p:.6f}, err "
                  f"{100*(res[c]['S']-S_p)/S_p:+.2f}%)  D={res[c]['delay_us']:.0f} us "
                  f"(paper {D_p:.0f}, err {100*(res[c]['delay_us']-D_p)/D_p:+.2f}%)  "
                  f"drop={res[c]['drop']:.4f}")
