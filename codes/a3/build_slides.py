#!/usr/bin/env python3
"""Build assets/ppt/a3-M11402804-AhmadRifqi.pptx (13 slides), same style as the A1/A2 decks.

Run from anywhere:  python3 codes/a3/build_slides.py
"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
IMG = os.path.join(REPO, "assets", "img", "a3")
OUT = os.path.join(REPO, "assets", "ppt", "a3-M11402804-AhmadRifqi.pptx")

INK = RGBColor(0x14, 0x1A, 0x24)
ACCENT = RGBColor(0x2F, 0x63, 0xE6)
PEAK = RGBColor(0xD9, 0x7A, 0x2B)
MUTED = RGBColor(0x58, 0x62, 0x74)
FAINT = RGBColor(0x8A, 0x94, 0xA4)
BG = RGBColor(0xFF, 0xFF, 0xFF)
CARD = RGBColor(0xEC, 0xF1, 0xFC)
CARD2 = RGBColor(0xF6, 0xF8, 0xFB)
HAIR = RGBColor(0xD9, 0xE0, 0xEA)
GOOD = RGBColor(0x1E, 0x8E, 0x5A)

HEAD, BODY, MONO = "Segoe UI Semibold", "Segoe UI", "Consolas"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
MX = 0.95
CW = 11.4  # content width


# ---------------------------------------------------------------- helpers
def slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s


def textbox(s, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tb, tf


def run(p, text, size, color=INK, bold=False, font=BODY, italic=False, spacing=None, sub=False):
    r = p.add_run()
    r.text = text
    f = r.font
    f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, font
    f.color.rgb = color
    if sub:
        r._r.get_or_add_rPr().set("baseline", "-25000")
    if spacing is not None:
        r._r.get_or_add_rPr().set("spc", str(int(spacing * 100)))
    return r


def para(tf, first=False, space_after=6, line=1.08, align=PP_ALIGN.LEFT):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(space_after)
    p.alignment = align
    pPr = p._p.get_or_add_pPr()
    ln = pPr.find(qn("a:lnSpc"))
    if ln is None:
        ln = pPr.makeelement(qn("a:lnSpc"), {})
        pPr.insert(0, ln)
    for c in list(ln):
        ln.remove(c)
    ln.append(ln.makeelement(qn("a:spcPct"), {"val": str(int(line * 100000))}))
    return p


def rect(s, x, y, w, h, fill=None, line=None, line_w=1.0, radius=0.08):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                             Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        shp.adjustments[0] = radius
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def hline(s, x, y, w, color=HAIR, weight=1.5):
    ln = s.shapes.add_connector(2, Inches(x), Inches(y), Inches(x + w), Inches(y))
    ln.line.color.rgb = color
    ln.line.width = Pt(weight)


def picture(s, name, x, y, w=None, h=None):
    pic = s.shapes.add_picture(os.path.join(IMG, name), Inches(x), Inches(y),
                               width=Inches(w) if w else None, height=Inches(h) if h else None)
    pic.line.color.rgb = HAIR
    pic.line.width = Pt(1)
    return pic


def header(s, num, section, corner_text, title_text, size=30, rule=True):
    _, tf = textbox(s, MX, 0.62, 8, 0.5)
    p = para(tf, first=True, space_after=0)
    run(p, num + "   ", 14, FAINT, bold=True, font=MONO, spacing=1.5)
    run(p, "•  ", 14, PEAK, bold=True)
    run(p, section.upper(), 14, ACCENT, bold=True, font=MONO, spacing=2.2)
    _, tf = textbox(s, 8.4, 0.64, 4.0, 0.4)
    p = para(tf, first=True, space_after=0, align=PP_ALIGN.RIGHT)
    run(p, corner_text, 11.5, FAINT, font=MONO, spacing=1.2)
    _, tf = textbox(s, MX, 1.2, CW, 0.9)
    p = para(tf, first=True, space_after=0, line=1.05)
    run(p, title_text, size, INK, bold=True, font=HEAD)
    if rule:
        hline(s, MX, 2.0, 2.1, weight=2)


def bullets(s, x, y, w, h, items, size=15, gap=9):
    """items: list of segment lists [(text, kind)], kind in n|b|pk|mono|good."""
    _, tf = textbox(s, x, y, w, h)
    for i, it in enumerate(items):
        p = para(tf, first=(i == 0), space_after=gap, line=1.13)
        run(p, "▪  ", size, ACCENT, bold=True)
        for txt, kind in it:
            if kind == "pk":
                run(p, txt, size, PEAK, bold=True)
            elif kind == "good":
                run(p, txt, size, GOOD, bold=True)
            elif kind == "b":
                run(p, txt, size, INK, bold=True)
            elif kind == "mono":
                run(p, txt, size - 1, ACCENT, font=MONO)
            else:
                run(p, txt, size, INK)


def T(t):
    return [(t, "n")]


def legend(s, x, y, w, h, heading, rows, sym_w=None, sym_size=12, desc_size=12):
    rect(s, x, y, w, h, fill=CARD2, line=HAIR, radius=0.06)
    _, tf = textbox(s, x + 0.25, y + 0.18, w - 0.5, h - 0.3)
    p = para(tf, first=True, space_after=8)
    run(p, heading, 9.5, FAINT, bold=True, font=MONO, spacing=1.2)
    for sym, desc in rows:
        p = para(tf, space_after=6, line=1.08)
        run(p, sym + "  ", sym_size, ACCENT, bold=True, font=MONO)
        run(p, desc, desc_size, MUTED)


def card(s, x, y, w, h, heading, lines, color=ACCENT, fill=CARD2, size=14.5):
    rect(s, x, y, w, h, fill=fill, line=HAIR, radius=0.05)
    _, tf = textbox(s, x + 0.25, y + 0.22, w - 0.5, h - 0.35)
    p = para(tf, first=True, space_after=10)
    run(p, heading.upper(), 11, color, bold=True, font=MONO, spacing=1.5)
    for ln in lines:
        p = para(tf, space_after=7, line=1.12)
        if isinstance(ln, tuple):
            run(p, ln[0], size, INK, bold=True)
            run(p, ln[1], size, INK)
        else:
            run(p, ln, size, INK)


def table(s, x, y, w, col_w, rows, size=11.5, head_size=11.5, row_h=0.36):
    shp = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w),
                             Inches(row_h * len(rows)))
    tbl = shp.table
    tblPr = tbl._tbl.tblPr
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        tblPr.remove(style)
    for c, cw in enumerate(col_w):
        tbl.columns[c].width = Inches(cw)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_h)
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACCENT if r == 0 else (CARD2 if r % 2 else BG)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            if r == 0:
                run(p, val, head_size, BG, bold=True)
            else:
                bold = c == 0
                color = PEAK if isinstance(val, str) and val.startswith("!") else INK
                run(p, val.lstrip("!"), size, color, bold=bold or color == PEAK)
    return tbl


def image_slide(num, section, corner_text, title_text, img, note=None):
    s = slide()
    header(s, num, section, corner_text, title_text, size=26, rule=False)
    h = 5.45 if note is None else 5.0
    w = h * 1690 / 910
    picture(s, img, (13.333 - w) / 2, 1.85, w=w)
    if note:
        _, tf = textbox(s, MX, 1.85 + h + 0.12, CW, 0.4)
        p = para(tf, first=True, space_after=0, align=PP_ALIGN.CENTER)
        run(p, note, 12, MUTED, italic=True)
    return s


# ---------------------------------------------------------------- 1 title
s = slide()
rect(s, 0, 0, 0.16, 7.5, fill=ACCENT, radius=0)
_, tf = textbox(s, MX, 1.85, CW, 3.8)
p = para(tf, first=True, space_after=14)
run(p, "ASSIGNMENT A3 · LITERATURE REVIEW", 15, ACCENT, bold=True, font=MONO, spacing=3)
p = para(tf, space_after=12, line=1.05)
run(p, "How IEEE 802.11e ", 40, INK, bold=True, font=HEAD)
run(p, "prioritizes", 40, ACCENT, bold=True, font=HEAD)
run(p, " traffic — and what the models assume", 40, INK, bold=True, font=HEAD)
p = para(tf, space_after=0, line=1.2)
run(p, "Partly reproducing two IEEE papers.", 19, MUTED)
hline(s, MX, 5.75, CW, weight=1.2)
_, tf = textbox(s, MX, 5.9, CW, 1.2)
for i, (k, v) in enumerate([
        ("Student ", "M11402804 · Ahmad Rifqi Fadhlurrahman · Basic path: 802.11e"),
        ("Paper   ", "Kong, Tsang, Bensaou & Gao — IEEE JSAC, 2004"),
        ("Paper   ", "Y. Xiao — IEEE Trans. Wireless Commun., 2005")]):
    p = para(tf, first=(i == 0), space_after=3)
    run(p, k, 12.5, INK, bold=True, font=MONO)
    run(p, v, 12.5, FAINT, font=MONO)

# ---------------------------------------------------------------- 2 background
s = slide()
header(s, "01", "Background", "802.11e EDCA", "EDCA: four queues, four sets of rules")
bullets(s, MX, 2.45, 6.8, 4.7, [
    [("Plain 802.11 (DCF) ", "b"), ("treats every frame the same: wait an idle DIFS, back off a random number of slots, double the window after a collision.", "n")],
    [("802.11e EDCA ", "b"), ("splits traffic into four access categories — voice, video, best effort, background — each with its own queue and rules.", "n")],
    [("A higher class waits less and backs off less, so it ", "n"), ("wins the channel more often", "pk"), (".", "n")],
    [("Both papers ask: ", "b"), ("for a given set of rules, how much throughput and delay does each class get?", "n")],
], size=15, gap=11)
legend(s, 8.2, 2.45, 4.15, 3.0, "THE KNOBS PER CLASS", [
    ("AIFS ", "idle wait before counting down"),
    ("CWmin", "first backoff window"),
    ("CWmax", "largest backoff window"),
    ("Retry", "attempts before a frame is dropped"),
    ("VC   ", "virtual collision: two queues of one station tie → the higher class sends"),
], sym_size=11.5, desc_size=11.5)

# ---------------------------------------------------------------- 3 P1 problem
s = slide()
header(s, "02", "Kong et al. 2004", "IEEE JSAC 22(10)", "Kong et al.: first full analytical EDCA model")
cw3 = (CW - 0.4) / 3
card(s, MX, 2.4, cw3, 3.9, "Problem", [
    "EDCA had been studied only by simulation.",
    "DCF models (Bianchi) miss AIFS, per-class windows and virtual collisions.",
    "Goal: per-class throughput and mean access delay from a model."])
card(s, MX + cw3 + 0.2, 2.4, cw3, 3.9, "Importance", [
    "EDCA is the mandatory QoS mechanism of 802.11e.",
    "Voice and video need bounded delay.",
    "A model evaluates a parameter set in seconds, not one long simulation per point."])
card(s, MX + 2 * (cw3 + 0.2), 2.4, cw3, 3.9, "Challenges", [
    "Different AIFS → a 3rd state dimension for frozen time.",
    "Virtual collisions couple queues inside one station.",
    "EDCA counts down in the last AIFS slot; finite retry limit.",
    "Coupled non-linear fixed point; delay needs a recursion."], color=PEAK)

# ---------------------------------------------------------------- 4 P1 system model
image_slide("03", "Kong et al. · System model", "3-D Markov chain per AC",
            "System model: saturated BSS, two ACs per station",
            "kong_system_model.png")

# ---------------------------------------------------------------- 5 P1 reported results
s = slide()
header(s, "04", "Kong et al. · Reported results", "NS-2 vs analysis", "AC3 is protected; AC1 pays for it", size=28)
table(s, MX, 2.35, CW, [1.5, 3.4, 6.5], [
    ["Figure", "Experiment", "Result reported in the paper"],
    ["Fig. 7", "one AC3 + one AC1 per station, M = 5…30", "AC3 throughput flat at ≈ 0.6; AC1 halves 0.12 → 0.06. AC1 delay ≈ 230 ms at M = 30, AC3 < 25 ms"],
    ["Fig. 8", "M = 15, simulation", "AC3 ≈ 6.5 Mb/s, AC1 ≈ 1 Mb/s; AC3 frames almost all within 100 ms, AC1 tail > 300 ms"],
    ["Fig. 9", "CW[AC3] = 7…63, 15…127, 31…255", "smaller AC3 window → more AC3 throughput; with equal windows AC3 still wins (shorter AIFS)"],
    ["Fig. 10", "AIFS[AC1] = 3, 4, 5", "!AIFS is a strong lever — AIFS[AC1] = 5 starves AC1 (≈ 1.1 s delay at M = 30)"],
    ["Figs. 11–12", "M₃ AC3-only and M₁ AC1-only stations", "more AC3 stations hurt AC1 badly, not vice versa → admission control is needed"],
], size=12, head_size=12.5, row_h=0.72)

# ---------------------------------------------------------------- 5 P1 ns-3 settings
s = slide()
header(s, "05", "Kong et al. · ns-3 settings", "ns-3.48", "Rebuilding Kong et al.'s experiment in ns-3.48")
table(s, MX, 2.35, CW, [2.3, 3.6, 5.5], [
    ["Item", "Paper (Table I)", "ns-3.48 setting"],
    ["Topology", "M stations → AP, ideal channel", "1 AP + M STAs on a 5 m circle, M = 5…30"],
    ["Traffic", "saturated AC3 + AC1, 1000 B", "2 PacketSocketClients per STA (AC_VO, AC_BK), 4 Mb/s each"],
    ["PHY", "11 Mb/s, header 192 bits", "802.11b, DsssRate11Mbps for data and control"],
    ["AIFS / SIFS", "AC3 3, AC1 4 slots · SIFS 1 slot", "AIFSN 2 / 3 · SetSifs(20 µs) · slot 20 µs"],
    ["CW", "AC3 15–127 · AC1 31–255", "MinCws / MaxCws on VO_Txop and BK_Txop"],
    ["Access", "RTS/CTS, one frame per TXOP", "RtsCtsThreshold 0 · TxopLimits 0"],
    ["Retry limit", "!not reported", "FrameRetryLimit 7 (ns-3 default)"],
    ["Time / seeds", "!not reported", "13 s (stats 3–13 s) · seeds 1–5, 95 % CI"],
], size=12, head_size=12.5, row_h=0.5)

# ---------------------------------------------------------------- 7 P1 points to check
s = slide()
header(s, "06", "Kong et al. · Points to check", "before A4", "What the paper leaves for the reproduction to fix", size=28)
bullets(s, MX, 2.4, CW, 4.6, [
    [("F1 — idealized PHY: ", "b"), ("Table I sends the 192-bit PHY header at 11 Mb/s (≈ 17 µs); real 802.11b needs ", "n"), ("192 µs", "pk"), (" per frame. Max normalized throughput 0.74 vs 0.49, so compare AC3's ", "n"), ("share", "b"), (", not its absolute throughput.", "n")],
    [("F2 — delay definition: ", "b"), ("Little's law on the paper's own AC3 throughput at M = 30 gives ≈ 36 ms, but Fig. 7b shows ≈ 22 ms — the definition must be fixed and stated.", "n")],
    [("F3 — association: ", "b"), ("NS-2 had no association phase; in ns-3, saturated traffic must start only after all M stations are associated.", "n")],
    [("Not reported: ", "b"), ("retry limit, simulation time, number of seeds.", "pk")],
], size=16, gap=14)

# ---------------------------------------------------------------- 7 P2 problem
s = slide()
header(s, "07", "Xiao 2005", "IEEE TWC 4(4)", "Xiao: three backoff knobs, with frame loss")
card(s, MX, 2.4, cw3, 3.9, "Problem", [
    "DCF lets a voice frame wait arbitrarily long.",
    "Earlier priority schemes: simulation only, or models with an infinite retry limit.",
    "Goal: model priorities from W₀, σ and the retry limit, incl. EDCA's backoff."])
card(s, MX + cw3 + 0.2, 2.4, cw3, 3.9, "Importance", [
    "All three knobs need only small changes to DCF.",
    "Throughput, delay and frame-dropping probability per class guide parameter design.",
    "Retry limit trades loss against delay for real-time traffic."])
card(s, MX + 2 * (cw3 + 0.2), 2.4, cw3, 3.9, "Challenges", [
    "A finite retry limit changes the chain and gives frame loss.",
    "The counter freezes while the channel is busy.",
    "Classes coupled through one collision process.",
    "An accurate delay model."], color=PEAK)

# ---------------------------------------------------------------- 8 P2 system model
image_slide("08", "Xiao · System model", "2-D Markov chain per class",
            "System model: N classes, one class per station",
            "xiao_system_model.png")

# ---------------------------------------------------------------- 10 P2 reported results
s = slide()
header(s, "09", "Xiao · Reported results", "OPNET vs analysis", "Each knob moves bandwidth between the classes", size=28)
table(s, MX, 2.35, CW, [1.5, 3.4, 6.5], [
    ["Figure", "Experiment", "Result reported in the paper"],
    ["Table I", "n₀ = n₁ = 10 and 30", "analysis vs OPNET within 0.45–2.2 %, e.g. class 0 throughput 0.5208 vs 0.5161 at n = 10"],
    ["Figs. 2–4", "combined scheme, n = 5…40", "class 0: much higher throughput, much lower delay — but drops more frames (≈ 9 % vs 2.4 % at n = 40)"],
    ["Figs. 5–8", "W₁,₀ = 16…56, σ₁ = 1.6…2.6", "each knob alone shifts bandwidth between classes; total throughput rises slightly"],
    ["Figs. 9–11", "L₁,retry = 0…8", "!smaller retry limit → better throughput and delay, more dropped frames (suits voice)"],
], size=12, head_size=12.5, row_h=0.72)

# ---------------------------------------------------------------- 11 P2 ns-3 settings
s = slide()
header(s, "10", "Xiao · ns-3 settings", "ns-3.48", "Rebuilding Xiao's experiment in ns-3.48")
table(s, MX, 2.3, CW, [2.3, 3.6, 5.5], [
    ["Item", "Paper", "ns-3.48 setting"],
    ["Topology / traffic", "n₀ + n₁ stations, saturated, 1024 B", "1 AP + (n₀ + n₁) STAs, one saturating client per STA"],
    ["PHY / access", "802.11a, 6 Mb/s, basic access", "OfdmRate6Mbps for data and control · RTS/CTS off"],
    ["W₀, CWmax", "[16, 32], 1024", "MinCws {15}, {31} · MaxCws {1023}"],
    ["σ", "![1.7, 2]", "!not supported — patch Txop::UpdateFailedCw"],
    ["Retry limit", "[4, 7]", "FrameRetryLimit per STA (one class per STA)"],
    ["Time / seeds", "!not reported (> 95 % CI)", "≥ 10 s after association · 10 seeds"],
], size=12, head_size=12.5, row_h=0.46)
bullets(s, MX, 5.75, CW, 1.4, [
    [("PHY timing not stated: ", "b"), ("slot, SIFS, DIFS taken from the 802.11a standard.", "n")],
    [("F4 — Fig. 7 is inconsistent: ", "pk"), ("the same configuration reads ≈ 0.325 in Fig. 7 but ≈ 0.34 in Figs. 5 and 9 — validate against Table I instead.", "n")],
], size=13.5, gap=6)

# ---------------------------------------------------------------- 11 what changed
s = slide()
header(s, "11", "Revised proposal", "A1 → A3", "What changed from A1, and why")
table(s, MX, 2.3, CW, [1.9, 3.0, 3.0, 3.5], [
    ["", "A1", "A3", "Why"],
    ["Technology", "802.16 OFDMA, admission control", "802.11e EDCA", "basic path is 802.11e; ns-3.48 has no WiMAX"],
    ["Base papers", "El Bouchti et al. (IJCSIS)", "Kong (JSAC), Xiao (TWC)", "A3 requires IEEE; validated baselines"],
    ["QoS lever", "one threshold C", "CWmin, CWmax, AIFSN, retry per AC", "the knobs 802.11e exposes"],
    ["Traffic", "MMPP with λ₁(t)", "saturated → Poisson → MMPP → 3GPP XR → λ(t)", "!both papers assume saturation"],
    ["Tools", "DTMC + ns-3 WiMAX", "Xiao model + ns-3 wifi", "fast sweeps + protocol-accurate check"],
    ["Metrics", "blocking, drop, delay", "+ 95th-pct delay, budget violations, starvation", "XR has a 10 ms budget; Kong et al. shows starvation"],
], size=11.5, head_size=12, row_h=0.62)

# ---------------------------------------------------------------- 12 proposal
s = slide()
header(s, "12", "Revised proposal", "final project", "Optimal EDCA parameters under realistic traffic", size=29)
rect(s, MX, 2.35, CW, 1.05, fill=CARD, line=HAIR, radius=0.08)
_, tf = textbox(s, MX + 0.3, 2.5, CW - 0.6, 0.8, anchor=MSO_ANCHOR.MIDDLE)
p = para(tf, first=True, space_after=0, line=1.12)
run(p, "Research question  ", 13, ACCENT, bold=True, font=MONO)
run(p, "Is the EDCA parameter set that is best under saturation still best for non-saturated, "
       "bursty or frame-based traffic — and how much QoS does it lose if not?", 15, INK)
steps = [("A4 · Baseline", "Kong et al. Fig. 7 in ns-3 with fixed throughput and delay definitions; Xiao Table I in ns-3."),
         ("Traffic models", "Saturated, Poisson, MMPP, 3GPP XR video (A2) in AC_VI, time-of-day λ(t)."),
         ("Policy search", "Sweep CWmin, CWmax, AIFSN, retry per AC; maximize throughput s.t. ≤ 1 % XR budget violations, no starved AC."),
         ("Compare", "Per-traffic optimum vs 802.11e defaults vs the saturation-optimal set.")]
sw = (CW - 0.6) / 4
for i, (h, t) in enumerate(steps):
    card(s, MX + i * (sw + 0.2), 3.65, sw, 2.75, f"{i + 1} · {h}", [t], size=14,
         color=PEAK if i == 2 else ACCENT)

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides._sldIdLst))
