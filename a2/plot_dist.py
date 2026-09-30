#!/usr/bin/env python3
"""Verify the generated XR traffic against the 3GPP-style model.

Reads the two logs written by xr-traffic.cc and produces:
  dist_frame_size.png   frame size   PDF + CDF vs truncated-Normal model (+ KS test)
  dist_frame_iat.png    frame inter-arrival PDF + CDF vs truncated-Normal model (+ KS test)
  dist_packet.png       packet size and packet inter-departure distributions,
                        compared with what the frame model predicts after fragmentation

Usage (inside ns-3-dev, after running the simulation):
    python3 plot_dist.py [--rate 30] [--fps 60] [--size-std-pct 10.5]
                         [--jitter-std 2.0] [--jitter-bound 4.0] [--max-payload 1400]
Pass the same values you gave xr-traffic.
"""
import argparse
import math

import matplotlib

matplotlib.use("Agg")  # headless: write PNGs, no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLUE, ORANGE = "#2f63e6", "#d97a2b"

ap = argparse.ArgumentParser()
ap.add_argument("--frames", default="xr-frames.csv")
ap.add_argument("--packets", default="xr-packets.csv")
ap.add_argument("--rate", type=float, default=30.0, help="Mbps")
ap.add_argument("--fps", type=float, default=60.0)
ap.add_argument("--size-std-pct", type=float, default=10.5)
ap.add_argument("--jitter-std", type=float, default=2.0, help="ms")
ap.add_argument("--jitter-bound", type=float, default=4.0, help="ms, truncation +/-")
ap.add_argument("--max-payload", type=int, default=1400, help="bytes")
args = ap.parse_args()

frames = pd.read_csv(args.frames)
packets = pd.read_csv(args.packets)

size_mu = args.rate * 1e6 / args.fps / 8.0
size_sd = size_mu * args.size_std_pct / 100.0
size_bound = 3 * size_sd
iat_mu = 1e3 / args.fps
iat_sd, iat_bound = args.jitter_std, args.jitter_bound

_erf = np.vectorize(math.erf)


def phi(z):
    return np.exp(-0.5 * z**2) / np.sqrt(2 * np.pi)


def Phi(z):
    return 0.5 * (1 + _erf(z / np.sqrt(2)))


def truncnorm(mu, sd, bound):
    """PDF, CDF and std of Normal(mu, sd) truncated to [mu-bound, mu+bound]."""
    k = bound / sd
    mass = Phi(k) - Phi(-k)
    pdf = lambda x: np.where(np.abs(x - mu) <= bound, phi((x - mu) / sd) / (sd * mass), 0.0)
    cdf = lambda x: np.clip((Phi((x - mu) / sd) - Phi(-k)) / mass, 0.0, 1.0)
    std = sd * np.sqrt(1 - 2 * k * phi(k) / mass)
    return pdf, cdf, float(std)


def ecdf(data):
    x = np.sort(data)
    return x, np.arange(1, len(x) + 1) / len(x)


def verify(data, mu, sd, bound, xlabel, unit, fname):
    """PDF + CDF against the truncated-Normal model, with a Kolmogorov-Smirnov test."""
    pdf, cdf, tstd = truncnorm(mu, sd, bound)
    xs = np.linspace(mu - bound * 1.05, mu + bound * 1.05, 400)
    ex, ey = ecdf(data)
    n = len(ex)
    m = cdf(ex)
    ks = float(max(np.max(ey - m), np.max(m - (ey - 1.0 / n))))
    ks_crit = 1.36 / np.sqrt(n)  # 5 % significance
    verdict = "PASS" if ks < ks_crit else "FAIL"

    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    a.hist(data, bins=40, density=True, color=BLUE, alpha=0.55, edgecolor="white",
           label="generated")
    a.plot(xs, pdf(xs), "-", color=ORANGE, lw=2,
           label=f"model: N({mu:.1f}, {sd:.1f}) cut at ±{bound:.1f}")
    a.set(title="PDF", xlabel=f"{xlabel} [{unit}]", ylabel="density")
    a.legend(fontsize=8)
    b.step(ex, ey, where="post", color=BLUE, lw=2, label="generated (ECDF)")
    b.plot(xs, cdf(xs), "--", color=ORANGE, lw=2, label="model CDF")
    b.set(title="CDF", xlabel=f"{xlabel} [{unit}]", ylabel="P(X ≤ x)")
    b.legend(fontsize=8)
    fig.suptitle(f"{xlabel}: generated mean={data.mean():.2f}, std={data.std():.2f}  |  "
                 f"model mean={mu:.2f}, std={tstd:.2f}  |  KS={ks:.3f} "
                 f"(crit {ks_crit:.3f}, {verdict}), n={n}", fontsize=10)
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    print(f"{fname}: generated mean={data.mean():.3f} std={data.std():.3f} {unit} | "
          f"model mean={mu:.3f} std={tstd:.3f} {unit} | KS={ks:.4f} crit={ks_crit:.4f} "
          f"-> {verdict}")


# ---- frame level: this is where the 3GPP model is defined ----
verify(frames["frame_bytes"].to_numpy(float), size_mu, size_sd, size_bound,
       "frame size", "B", "dist_frame_size.png")
verify(frames["iat_s"].to_numpy(float)[1:] * 1e3, iat_mu, iat_sd, iat_bound,
       "frame inter-arrival time", "ms", "dist_frame_iat.png")

# ---- packet level: a consequence of fragmenting each frame into <= max_payload packets ----
rng = np.random.default_rng(0)
mc = rng.normal(size_mu, size_sd, 200_000)
mc = np.rint(mc[np.abs(mc - size_mu) <= size_bound]).astype(int)
full = mc // args.max_payload
rest = mc % args.max_payload
model_sizes = np.concatenate([np.full(full.sum(), args.max_payload), rest[rest > 0]])

sizes = packets["size_bytes"].to_numpy(int)
gaps_ms = np.diff(packets["t_send_s"].to_numpy(float)) * 1e3
share_full = np.mean(sizes == args.max_payload)
share_full_model = np.mean(model_sizes == args.max_payload)
pkts_per_frame = len(sizes) / len(frames)

fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
bins = np.linspace(0, args.max_payload, 29)
a.hist(model_sizes, bins=bins, density=True, histtype="step", color=ORANGE, lw=2,
       label="model (fragmented frames)")
a.hist(sizes, bins=bins, density=True, color=BLUE, alpha=0.55, edgecolor="white",
       label="generated")
a.set_yscale("log")
a.set(title="Packet size PDF (log scale)", xlabel="packet size [B]", ylabel="density")
a.legend(fontsize=8)
gx, gy = ecdf(gaps_ms)
b.step(gx, gy, where="post", color=BLUE, lw=2)
b.set(title="Packet inter-departure ECDF", xlabel="gap between packets [ms]",
      ylabel="P(X ≤ x)")
b.annotate(f"{np.mean(gaps_ms == 0):.1%} of gaps are 0 ms\n(packets of the same frame)",
           xy=(0.5, 0.5), xycoords="axes fraction", fontsize=9)
fig.suptitle(f"packet level: {len(sizes)} packets, {pkts_per_frame:.1f} per frame  |  "
             f"full {args.max_payload} B packets: generated {share_full:.1%}, "
             f"model {share_full_model:.1%}", fontsize=10)
fig.tight_layout()
fig.savefig("dist_packet.png", dpi=130)
print(f"dist_packet.png: {len(sizes)} packets, {pkts_per_frame:.2f}/frame, "
      f"full-size share generated {share_full:.3%} vs model {share_full_model:.3%}")
