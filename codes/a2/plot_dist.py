#!/usr/bin/env python3
"""Verify the generated XR traffic against the 3GPP TR 38.838 / TR 26.926 model.

Reads the two logs written by xr-traffic.cc and produces:
  dist_frame_size.png    frame size        PDF + CDF vs truncated Gaussian   (+ KS test)
  dist_frame_jitter.png  frame jitter J_k  PDF + CDF vs truncated Gaussian   (+ KS test)
  dist_frame_iat.png     frame inter-arrival T + J_k - J_(k-1): PDF + CDF vs the model
                         distribution (Monte Carlo from the jitter model)   (+ KS test)
  dist_packet.png        packet size and packet inter-departure, vs what the frame model
                         predicts after fragmentation

Usage (inside ns-3-dev, after running the simulation):
    python3 plot_dist.py [--rate 30] [--fps 60] [--size-std-pct 10.5] [--size-max-pct 150]
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
ap.add_argument("--rate", type=float, default=30.0, help="Mbit/s")
ap.add_argument("--fps", type=float, default=60.0)
ap.add_argument("--size-std-pct", type=float, default=10.5)
ap.add_argument("--size-max-pct", type=float, default=150.0, help="min is symmetric (100-(max-100))")
ap.add_argument("--jitter-std", type=float, default=2.0, help="ms")
ap.add_argument("--jitter-bound", type=float, default=4.0, help="ms, truncation +/-")
ap.add_argument("--max-payload", type=int, default=1400, help="bytes")
args = ap.parse_args()

frames = pd.read_csv(args.frames)
packets = pd.read_csv(args.packets)

size_mu = args.rate * 1e6 / (args.fps * 8.0)
size_sd = size_mu * args.size_std_pct / 100.0
size_bound = size_mu * (args.size_max_pct - 100.0) / 100.0
period_ms = 1e3 / args.fps
jit_sd, jit_bound = args.jitter_std, args.jitter_bound

_erf = np.vectorize(math.erf)
rng = np.random.default_rng(0)


def phi(z):
    return np.exp(-0.5 * z**2) / np.sqrt(2 * np.pi)


def Phi(z):
    return 0.5 * (1 + _erf(z / np.sqrt(2)))


def truncnorm(mu, sd, bound):
    """Analytic PDF, CDF and std of Normal(mu, sd) truncated to [mu-bound, mu+bound]."""
    k = bound / sd
    mass = Phi(k) - Phi(-k)
    pdf = lambda x: np.where(np.abs(x - mu) <= bound, phi((x - mu) / sd) / (sd * mass), 0.0)
    cdf = lambda x: np.clip((Phi((x - mu) / sd) - Phi(-k)) / mass, 0.0, 1.0)
    std = sd * np.sqrt(1 - 2 * k * phi(k) / mass)
    return pdf, cdf, float(std)


def truncnorm_samples(mu, sd, bound, n):
    x = rng.normal(mu, sd, int(n * 1.2) + 1000)
    x = x[np.abs(x - mu) <= bound]
    return x[:n]


def ecdf(data):
    x = np.sort(data)
    return x, np.arange(1, len(x) + 1) / len(x)


def ks_test(data, model_cdf):
    ex, ey = ecdf(data)
    m = model_cdf(ex)
    n = len(ex)
    ks = float(max(np.max(ey - m), np.max(m - (ey - 1.0 / n))))
    crit = 1.36 / np.sqrt(n)  # 5 % significance
    return ks, crit, ("PASS" if ks < crit else "FAIL")


def verify(data, model, xlabel, unit, fname, model_label):
    """model = dict(pdf, cdf, mean, std, lo, hi) — analytic or from Monte Carlo."""
    ks, crit, verdict = ks_test(data, model["cdf"])
    xs = np.linspace(model["lo"], model["hi"], 400)
    ex, ey = ecdf(data)

    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    a.hist(data, bins=40, density=True, color=BLUE, alpha=0.55, edgecolor="white",
           label="generated")
    a.plot(xs, model["pdf"](xs), "-", color=ORANGE, lw=2, label=model_label)
    a.set(title="PDF", xlabel=f"{xlabel} [{unit}]", ylabel="density")
    a.legend(fontsize=8)
    b.step(ex, ey, where="post", color=BLUE, lw=2, label="generated (ECDF)")
    b.plot(xs, model["cdf"](xs), "--", color=ORANGE, lw=2, label="model CDF")
    b.set(title="CDF", xlabel=f"{xlabel} [{unit}]", ylabel="P(X ≤ x)")
    b.legend(fontsize=8)
    fig.suptitle(f"{xlabel}: generated mean={data.mean():.2f}, std={data.std():.2f}  |  "
                 f"model mean={model['mean']:.2f}, std={model['std']:.2f}  |  KS={ks:.3f} "
                 f"(crit {crit:.3f}, {verdict}), n={len(data)}", fontsize=10)
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    print(f"{fname}: generated mean={data.mean():.3f} std={data.std():.3f} {unit} | "
          f"model mean={model['mean']:.3f} std={model['std']:.3f} {unit} | "
          f"KS={ks:.4f} crit={crit:.4f} -> {verdict}")


def analytic(mu, sd, bound):
    pdf, cdf, std = truncnorm(mu, sd, bound)
    return dict(pdf=pdf, cdf=cdf, mean=mu, std=std, lo=mu - 1.05 * bound, hi=mu + 1.05 * bound)


def empirical(samples, bins=200):
    """Model distribution known only through Monte Carlo samples."""
    s = np.sort(samples)
    dens, edges = np.histogram(s, bins=bins, density=True)
    centers = 0.5 * (edges[1:] + edges[:-1])
    pdf = lambda x: np.interp(x, centers, dens, left=0.0, right=0.0)
    cdf = lambda x: np.searchsorted(s, x, side="right") / len(s)
    span = s[-1] - s[0]
    return dict(pdf=pdf, cdf=cdf, mean=s.mean(), std=s.std(),
                lo=s[0] - 0.03 * span, hi=s[-1] + 0.03 * span)


# ---- frame level: this is where the 3GPP model is defined ----
verify(frames["frame_bytes"].to_numpy(float), analytic(size_mu, size_sd, size_bound),
       "frame size", "B", "dist_frame_size.png",
       f"model: N({size_mu:.0f}, {size_sd:.0f}) in "
       f"[{size_mu - size_bound:.0f}, {size_mu + size_bound:.0f}]")

verify(frames["jitter_ms"].to_numpy(float), analytic(0.0, jit_sd, jit_bound),
       "frame jitter J_k", "ms", "dist_frame_jitter.png",
       f"model: N(0, {jit_sd}) in [-{jit_bound}, {jit_bound}]")

j = truncnorm_samples(0.0, jit_sd, jit_bound, 400_000)
iat_model = period_ms + j[1:] - j[:-1]
verify(frames["iat_s"].to_numpy(float)[1:] * 1e3, empirical(iat_model),
       "frame inter-arrival time", "ms", "dist_frame_iat.png",
       f"model: {period_ms:.2f} + J_k - J_(k-1) (Monte Carlo)")

# ---- packet level: a consequence of fragmenting each frame into <= max_payload packets ----
mc = np.rint(truncnorm_samples(size_mu, size_sd, size_bound, 200_000)).astype(int)
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
           xy=(0.45, 0.5), xycoords="axes fraction", fontsize=9)
fig.suptitle(f"packet level: {len(sizes)} packets, {pkts_per_frame:.1f} per frame  |  "
             f"full {args.max_payload} B packets: generated {share_full:.1%}, "
             f"model {share_full_model:.1%}", fontsize=10)
fig.tight_layout()
fig.savefig("dist_packet.png", dpi=130)
print(f"dist_packet.png: {len(sizes)} packets, {pkts_per_frame:.2f}/frame, "
      f"full-size share generated {share_full:.3%} vs model {share_full_model:.3%}")
