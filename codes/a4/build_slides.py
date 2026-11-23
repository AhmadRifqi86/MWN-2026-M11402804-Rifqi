#!/usr/bin/env python3
"""Build assets/ppt/a4-M11402804-AhmadRifqi.pptx (18 slides), same style as the A3 deck.

Run from anywhere:  python3 codes/a4/build_slides.py
"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
IMG = os.path.join(REPO, "assets", "img", "a4")
OUT = os.path.join(REPO, "assets", "ppt", "a4-M11402804-AhmadRifqi.pptx")

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
WARM = RGBColor(0xFD, 0xF3, 0xEA)

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


def fit_picture(s, name, y, max_w=CW, max_h=4.6):
    """Centre an image horizontally, as large as fits in max_w x max_h; returns its bottom edge."""
    from PIL import Image
    pw, ph = Image.open(os.path.join(IMG, name)).size
    w = min(max_w, max_h * pw / ph)
    h = w * ph / pw
    picture(s, name, (13.333 - w) / 2, y, w=w)
    return y + h


def why(s, y, text, x=MX, w=CW, h=0.52, size=13, label="WHY THE GAP", color=PEAK, fill=WARM):
    """Short labelled callout under a result (default: 'why the gap')."""
    rect(s, x, y, w, h, fill=fill, line=color, line_w=1.0, radius=0.12)
    _, tf = textbox(s, x + 0.2, y, w - 0.4, h, anchor=MSO_ANCHOR.MIDDLE)
    p = para(tf, first=True, space_after=0, line=1.05)
    run(p, label + "   ", 10.5, color, bold=True, font=MONO, spacing=1.2)
    run(p, text, size, INK)


def note(s, y, text, size=12.5):
    _, tf = textbox(s, MX, y, CW, 0.5)
    p = para(tf, first=True, space_after=0, align=PP_ALIGN.CENTER)
    run(p, text, size, MUTED, italic=True)


# ---------------------------------------------------------------- title
s = slide()
rect(s, 0, 0, 0.16, 7.5, fill=ACCENT, radius=0)
_, tf = textbox(s, MX, 1.85, CW, 3.8)
p = para(tf, first=True, space_after=14)
run(p, "ASSIGNMENT A4 · BASELINE REPRODUCTION", 15, ACCENT, bold=True, font=MONO, spacing=3)
p = para(tf, space_after=12, line=1.05)
run(p, "Kong et al. and Xiao in ", 40, INK, bold=True, font=HEAD)
run(p, "ns-3", 40, ACCENT, bold=True, font=HEAD)
run(p, ": what matches, and why the rest does not", 40, INK, bold=True, font=HEAD)
p = para(tf, space_after=0, line=1.2)
run(p, "470 runs plotted against the papers' analysis and simulation, with every gap explained or tested.",
    19, MUTED)
hline(s, MX, 5.75, CW, weight=1.2)
_, tf = textbox(s, MX, 5.85, CW, 1.4)
for i, (k, v) in enumerate([
        ("Student ", "M11402804 · Ahmad Rifqi Fadhlurrahman · Advanced path: 802.11e EDCA"),
        ("Papers  ", "Kong et al. — IEEE JSAC 2004, Fig. 7 · Y. Xiao — IEEE TWC 2005, Table I, Figs. 2–5, 7, 9"),
        ("Tool    ", "ns-3.48 (commit d2add90b4) in the A2 Docker image, two small patches")]):
    p = para(tf, first=(i == 0), space_after=3)
    run(p, k, 12.5, INK, bold=True, font=MONO)
    run(p, v, 12.5, FAINT, font=MONO)

cw2 = (CW - 0.3) / 2
cw3 = (CW - 0.4) / 3

# ---------------------------------------------------------------- 01 the result
s = slide()
header(s, "01", "Kong et al. · the result", "Kong et al. Fig. 7", "Fig. 7: two ACs per station, M = 5…30", size=29)
card(s, MX, 2.35, 3.9, 4.35, "Why this figure", [
    "The paper's validation figure: analysis and NS-2 side by side.",
    "Every EDCA parameter is in Table I.",
    "The saturated two-class network the final project starts from."], size=14)
table(s, MX + 4.15, 2.35, CW - 4.15, [2.65, 0.77, 0.77, 0.77, 0.77, 0.77, 0.75], [
    ["Read off Fig. 7", "M=5", "10", "15", "20", "25", "30"],
    ["S_AC3 analysis ≈ NS-2", "0.58", "0.59", "0.60", "0.603", "0.605", "0.605"],
    ["S_AC1 analysis", "0.12", "0.095", "0.08", "0.07", "0.065", "0.06"],
    ["S_AC1 NS-2", "0.12", "0.09", "0.07", "0.055", "0.045", "0.035"],
    ["D_AC3 [ms] ana / NS-2", "8 / 6", "12 / 11", "15 / 14", "18 / 16", "21 / 18", "24 / 17"],
    ["D_AC1 [ms] ana / NS-2", "36 / 28", "71 / 62", "108 / 97", "147 / 135", "188 / 178", "230 / 210"],
], size=11.5, head_size=12, row_h=0.55)
_, tf = textbox(s, MX + 4.15, 5.85, CW - 4.15, 0.85)
p = para(tf, first=True, space_after=0, line=1.15)
run(p, "Read by eye: ±0.01 throughput, ±3 ms delay. Panel (a) y 0–1, panel (b) y 0–250 ms. "
       "Delay = \"first transmission attempt until successfully transmitted\" (§IV-B).", 12, MUTED, italic=True)

# ---------------------------------------------------------------- 02 setup figure
s = slide()
header(s, "02", "Kong et al. · setup", "topology + timing", "One AP, M stations, and the PHY header", size=28)
b = fit_picture(s, "a4_setup.png", 2.2, max_h=4.3)
note(s, b + 0.15, "The paper sends the 192-bit PHY header at 11 Mb/s; real 802.11b sends it at 1 Mb/s (192 µs), "
                  "four times per exchange → PHY variants.")

# ---------------------------------------------------------------- 03 parameters
s = slide()
header(s, "03", "Kong et al. · setup", "paper vs ns-3.48", "Parameters: Table I mapped onto ns-3.48", size=28)
table(s, MX, 2.2, CW, [2.0, 3.6, 5.8], [
    ["Item", "Paper (Table I, §V)", "ns-3.48"],
    ["Topology", "M stations → AP, ideal channel", "1 AP + M STAs on a 5 m circle, M = 5, 10, …, 30"],
    ["Traffic", "saturated AC3 + AC1, 1000 B", "2 PacketSocketClients per STA, 4 Mb/s each, Priority 6 (AC_VO) / 1 (AC_BK)"],
    ["PHY header", "192 bits at 11 Mb/s", "!A: standard 192 µs at 1 Mb/s · B, C: 192 bits at 11 Mb/s (patch)"],
    ["Rate / slot / SIFS", "11 Mb/s · 20 µs · 1 slot", "DsssRate11Mbps data + control · slot 20 µs · SetSifs(20 µs)"],
    ["AIFS · CW", "3 / 4 slots · 15–127 / 31–255", "AIFSN 2 / 3 · MinCws/MaxCws 15/127 (VO), 31/255 (BK)"],
    ["Access", "RTS/CTS, one frame per TXOP", "RtsCtsThreshold 0 · TxopLimits 0"],
    ["Retry limit", "!not reported", "!A, B: 7 attempts (ns-3 default) · C: 4 attempts (= 4 CW values in Table I)"],
    ["Time / queue", "!not reported", "33 s: associate, traffic from 2 s, stats 3–33 s · queue lifetime 3600 s"],
    ["Metrics", "S per AC; mean access delay", "payload at AP / 30 s / 11 Mb/s · head-of-line → ACK · retry-limit drops"],
], size=11.5, head_size=12, row_h=0.46)

# ---------------------------------------------------------------- 04 flowchart
s = slide()
header(s, "04", "Kong et al. · setup", "kong-edca.cc + pipeline", "One run, and the sweep around it", size=28, rule=False)
fit_picture(s, "a4_flowchart.png", 1.95, max_h=5.2)

# ---------------------------------------------------------------- 05 repeatability
s = slide()
header(s, "05", "How to repeat it", "parameters · seeds · runs", "Seeds, runs and versions", size=29)
table(s, MX, 2.35, cw2 + 0.6, [1.9, cw2 + 0.6 - 1.9], [
    ["", "Value"],
    ["Simulator", "ns-3.48, commit d2add90b4, optimized"],
    ["Platform", "Docker ns3lab (A2): Ubuntu 24.04.5, g++ 13.3"],
    ["Patches", "dsss-ideal-plcp (Kong), txop-cw-growth (Xiao σ)"],
    ["Seeds", "SetSeed(1), SetRun(1…10)"],
    ["Kong runs", "3 variants × 6 M × 10 = 180 (+48 sensitivity)"],
    ["Xiao runs", "29 points × 10 seeds = 290"],
    ["Error bars", "95 % CI = 1.96 · s / √10"],
], size=12, head_size=12.5, row_h=0.5)
xr = MX + cw2 + 0.9
rect(s, xr, 2.35, CW - (cw2 + 0.9), 4.0, fill=CARD2, line=HAIR, radius=0.04)
_, tf = textbox(s, xr + 0.25, 2.55, CW - (cw2 + 0.9) - 0.5, 3.7)
p = para(tf, first=True, space_after=10)
run(p, "INSIDE THE CONTAINER", 11, ACCENT, bold=True, font=MONO, spacing=1.5)
for ln in ["cd /work/ns-3-dev",
           "git apply /work/a4/*.patch",
           "cp /work/a4/*.cc scratch/",
           "./ns3 build kong-edca xiao-priority",
           "bash /work/a4/run_sweep.sh 16",
           "bash /work/a4/run_xiao_sweep.sh 16",
           "",
           "# host",
           "python3 codes/a4/plot_fig7.py",
           "python3 codes/a4/plot_xiao_ns3.py"]:
    p = para(tf, space_after=4, line=1.05)
    run(p, ln or " ", 12.5, FAINT if ln.startswith("#") else INK, font=MONO)

# ---------------------------------------------------------------- 06 result figure
s = slide()
header(s, "06", "Kong et al. · result", "same axes as Fig. 7", "Fig. 7 in ns-3: the shape reproduces", size=28, rule=False)
b = fit_picture(s, "a4_fig7_reproduction.png", 1.95, max_h=3.8)
note(s, b + 0.06, "Dotted = paper analysis, ◆ = paper NS-2, ● = A, △ = B, □ = C. Panel (b) extended to 350 ms.", size=12)
why(s, b + 0.48, "A = real 802.11b PHY, 7 attempts  ·  B = paper's PHY, 7 attempts  ·  "
                 "C = paper's PHY, 4 attempts (implied)",
    label="VARIANTS", color=ACCENT, fill=CARD, h=0.46, size=12.5)
why(s, b + 1.06, "Basically the PHY header: the paper sends it at 11 Mb/s, real 802.11b at 1 Mb/s (→ half the throughput); "
                "the delay gap is the retry limit the paper does not report.")

# ---------------------------------------------------------------- 07 result numbers
s = slide()
header(s, "07", "Kong et al. · result", "mean of 10 seeds", "What matches and what does not", size=29)
table(s, MX, 2.3, 6.7, [0.55, 2.35, 0.95, 0.95, 0.95, 0.95], [
    ["M", "", "S_AC3", "S_AC1", "D_AC3", "D_AC1"],
    ["15", "paper analysis / NS-2", "0.60", "0.08", "15 / 14", "108 / 97"],
    ["", "A: 802.11b, 7 att.", "0.311", "0.063", "33.1", "157.3"],
    ["", "B: Table I, 7 att.", "0.526", "0.102", "19.5", "96.5"],
    ["", "C: Table I, 4 att.", "0.528", "0.100", "16.1", "78.9"],
    ["30", "paper analysis / NS-2", "0.605", "0.06", "24 / 17", "230 / 210"],
    ["", "A", "0.309", "0.056", "59.4", "325.7"],
    ["", "B", "0.530", "0.090", "34.4", "198.7"],
    ["", "C", "0.529", "0.088", "26.2", "153.5"],
], size=11.5, head_size=12, row_h=0.43)
_, tf = textbox(s, MX, 6.27, 6.7, 0.5)
p = para(tf, first=True, space_after=0)
run(p, "Delays in ms. 95 % CI ≤ ±0.002 throughput, ±6.6 ms delay.", 11.5, MUTED, italic=True)
why(s, 6.62, "A: header at 1 Mb/s vs 11 Mb/s. B/C: AC3 delay needs 4 attempts (unreported). "
             "Small leftover: ns-3 gives AC1 a bit more share.", w=6.7, h=0.62, size=11.5)
xr = MX + 7.0
card(s, xr, 2.3, CW - 7.0, 2.25, "Matches", [
    "Shape and ranking of all curves.",
    "B: AC1 delay within 8 % of NS-2.",
    "C: AC3 delay within 11 % of the analysis (M ≥ 10)."], color=GOOD, size=13)
card(s, xr, 4.7, CW - 7.0, 2.1, "Does not match", [
    "A: throughput about half.",
    "B, C: AC3 throughput 12–13 % low; AC1 falls too slowly."], color=PEAK, size=13)

# ---------------------------------------------------------------- 08 PHY mismatch
s = slide()
header(s, "08", "Kong · parameter mismatch", "PHY header", "The idealized PHY header explains the factor ≈ 1.7", size=28)
table(s, MX, 2.35, CW, [4.6, 3.4, 3.4], [
    ["One RTS/CTS/DATA/ACK exchange incl. AIFS[AC3]", "Exchange time", "Upper bound on S"],
    ["Paper, Table I", "977 µs", "0.745"],
    ["ns-3, Table I PHY (B, C)", "982 µs", "0.741"],
    ["ns-3, 802.11b PHY (A)", "!1 680 µs", "!0.433"],
], size=13, head_size=13, row_h=0.55)
card(s, MX, 4.8, cw3, 1.85, "Predicted", ["B / A = 0.741 / 0.433 = 1.71×"], size=15)
card(s, MX + cw3 + 0.2, 4.8, cw3, 1.85, "Measured (AC3)", ["0.530 / 0.309 = 1.72× at M = 30; 1.66–1.72 over all M"], color=GOOD, size=15)
card(s, MX + 2 * (cw3 + 0.2), 4.8, cw3, 1.85, "Consequence", ["Variant A is protocol-accurate; B and C isolate the other gaps."], size=15)

# ---------------------------------------------------------------- 09 explain figure
s = slide()
header(s, "09", "Kong · the remaining gaps", "share · Little · retry", "Two gaps that remain with the PHY matched", size=28, rule=False)
b = fit_picture(s, "a4_explain.png", 1.95, max_h=3.9)
bullets(s, MX, b + 0.15, CW, 1.4, [
    [("(a) Share S₃/(S₃+S₁): ", "b"), ("all three variants 0.80 → 0.85, paper 0.83 → 0.91: ns-3 differentiates ", "n"), ("2.5–6.3 points", "pk"), (" less.", "n")],
    [("(b, c) Delivered-frame delay / M·L/(S·R): ", "b"), ("set by the retry limit; ", "n"), ("4 attempts → 0.64 / 0.62", "pk"), (" at M = 30, paper analysis 0.67 / 0.63.", "n")],
], size=13.5, gap=5)

# ---------------------------------------------------------------- 10 share candidates
s = slide()
header(s, "10", "Kong · unmodelled effect", "AC3 share", "What lowers ns-3's AC3 share? Candidates tested", size=28)
table(s, MX, 2.3, CW, [3.1, 4.3, 4.0], [
    ["Candidate", "Test", "Result"],
    ["AIFS offset (last-slot countdown)", "AIFSN (1,2), (2,3), (3,4) · M = 15, 30 · 3 seeds", "share 0.838–0.842 / 0.853 → not the cause"],
    ["Retry limit (not reported)", "2, 3, 4, 5, 7 attempts · M = 15, 30 · 3 seeds", "share ≤ 0.872 even with 53 % drops → not the cause"],
    ["MAC header 38 B vs 34 B", "frame-time arithmetic", "0.4 % of the exchange → negligible"],
    ["Model approximations", "not testable in ns-3", "!open — paper's own NS-2 disagrees with its analysis"],
    ["2004 NS-2 802.11e module", "would need that module", "!open"],
], size=12, head_size=12.5, row_h=0.68)

# ---------------------------------------------------------------- 11 retry limit
s = slide()
header(s, "11", "Kong · parameter mismatch", "retry limit", "The unreported retry limit sets the delay", size=28)
table(s, MX, 2.3, 6.2, [3.6, 1.3, 1.3], [
    ["D / (M·L/(S·R)), M = 30", "AC3", "AC1"],
    ["ns-3, 7 attempts (B)", "0.84", "0.82"],
    ["ns-3, 5 attempts", "0.70", "0.69"],
    ["ns-3, 4 attempts (C)", "!0.64", "!0.62"],
    ["ns-3, 3 attempts", "0.57", "0.56"],
    ["paper analysis", "!0.67", "!0.63"],
    ["paper NS-2", "0.47", "0.34"],
], size=12.5, head_size=12.5, row_h=0.52)
bullets(s, MX + 6.6, 2.3, CW - 6.6, 4.5, [
    [("Little's law holds in ns-3: ", "b"), ("head-of-line time over all frames = 0.99–1.00 of M·L/(S·R).", "n")],
    [("Dropped frames waited longest, ", "b"), ("so leaving them out shortens the delivered-frame delay.", "n")],
    [("4 attempts = the 4 CW values ", "b"), ("Table I lists per AC; it fits the analysis within 5 % for M ≥ 15.", "n")],
    [("NS-2 needs 2–3 attempts: ", "b"), ("no single retry limit fits both.", "pk")],
], size=14, gap=10)

# ---------------------------------------------------------------- 12 Kong summary
s = slide()
header(s, "12", "Kong · summary", "differences explained", "Every Kong gap has a stated reason", size=29)
table(s, MX, 2.3, CW, [3.4, 3.4, 4.6], [
    ["Quantity", "Match?", "Reason"],
    ["Shape and ranking of all curves", "yes", "—"],
    ["Absolute throughput, 802.11b PHY", "!about half", "parameter mismatch: idealized PHY header"],
    ["Absolute throughput, Table I PHY", "AC3 12–13 % low", "follows from the share gap"],
    ["AC3 share", "!2.5–6.3 points low", "unmodelled effect / model approximation (open)"],
    ["AC3 delay", "within 11 % with 4 attempts", "parameter mismatch: unreported retry limit"],
    ["AC1 delay", "within 8 % of NS-2 (7 attempts)", "retry limit + share gap"],
    ["Different traffic model?", "no", "saturated as in the paper: 4 Mb/s per AC, far above what an AC gets"],
    ["Too few runs?", "no", "all CI half-widths < 2.5 % of the mean"],
], size=12, head_size=12.5, row_h=0.5)

# ---------------------------------------------------------------- 13 Xiao setup
s = slide()
header(s, "13", "Xiao 2005 · setup", "xiao-priority.cc", "Xiao: three backoff knobs per class, in ns-3", size=28)
table(s, MX, 2.3, CW, [2.4, 3.6, 5.4], [
    ["Knob / item", "Paper (class 0 / class 1)", "ns-3.48"],
    ["Initial window W₀", "16 / 32", "MinCws {15} / {31} per STA (non-QoS DCF)"],
    ["Window factor σ", "1.7 / 2", "!Txop::CwGrowthFactor — new attribute (txop-cw-growth.patch)"],
    ["Retry limit L", "4 / 7 retransmissions", "FrameRetryLimit = L + 1 attempts"],
    ["CWmax · DIFS", "1024 · equal for all", "MaxCws {1023} · AIFSN 2"],
    ["PHY · access", "802.11a 6 Mb/s · basic", "OfdmRate6Mbps data + control · no RTS/CTS"],
    ["Frame", "1052 B (28 B header + 1024 B)", "1016 B payload + 36 B = 1052 B"],
    ["Time · runs", "> 95 % CI", "20 s after association · 10 seeds · 290 runs"],
], size=12, head_size=12.5, row_h=0.52)
_, tf = textbox(s, MX, 6.6, CW, 0.4)
p = para(tf, first=True, space_after=0)
run(p, "Verified: CW of class 0 goes 15 → 26 → 45 → 78 → 133 (CwTrace) = 16 · 1.7ᵏ − 1.", 12, MUTED, italic=True)

# ---------------------------------------------------------------- 14 Xiao Figs 2-4
s = slide()
header(s, "14", "Xiao · result", "Table I, Figs. 2–4", "Combined scheme: ns-3 differentiates much less", size=28, rule=False)
b = fit_picture(s, "a4_xiao_fig2-4_ns3.png", 1.9, max_h=2.75)
table(s, MX, b + 0.15, CW, [2.4, 2.25, 2.25, 2.25, 2.25], [
    ["n = 10 / 30", "S class 0", "S class 1", "delay class 0", "delay class 1"],
    ["ns-3.48", "0.469 / 0.380", "0.174 / 0.142", "25.3 / 72.0 ms", "74.5 / 228 ms"],
    ["paper OPNET", "0.516 / 0.464", "0.153 / 0.101", "25.5 / 67.7 ms", "88.4 / 349 ms"],
    ["ns-3 vs OPNET", "!−9 / −18 %", "!+13 / +41 %", "−1 / +6 %", "!−16 / −35 %"],
], size=11.5, head_size=12, row_h=0.36)
_, tf = textbox(s, MX, b + 0.15 + 4 * 0.36 + 0.08, CW, 0.3)
p = para(tf, first=True, space_after=0)
run(p, "Same x-axes and quantities as the paper's Figs. 2–4; delay in ms (paper: µs); y-ranges widened to fit the ns-3 points.",
    11, MUTED, italic=True)
why(s, b + 0.15 + 4 * 0.36 + 0.42, "Basically ns-3 collides a bit more often (p 0.66 vs 0.58); class 0's low retry limit "
                                  "turns that into twice the drops, so class 1 takes the freed airtime.")

# ---------------------------------------------------------------- 15 Xiao knobs
s = slide()
header(s, "15", "Xiao · result", "Figs. 5, 7, 9", "One knob at a time: close to the model", size=28, rule=False)
b = fit_picture(s, "a4_xiao_knobs_ns3.png", 1.95, max_h=2.95)
bullets(s, MX, b + 0.15, CW, 1.6, [
    [("Every knob works in the paper's direction; ", "b"), ("total throughput 2–3.4 % below the model.", "n")],
    [("Fig. 7, σ₁ = 1.6: ", "b"), ("ns-3 0.249, model 0.238, paper ≈ 0.18 — confirms A3: the paper's Fig. 7 used another setting.", "n")],
    [("Fig. 9, L₁ = 0: ", "b"), ("largest gap — class 1 0.434 vs 0.508 (model).", "pk")],
], size=13.5, gap=5)
why(s, 6.5, "Same slightly higher collision probability in ns-3: only 2–3 % with one knob, "
            "largest at L₁ = 0 where every failed attempt is a drop.")

# ---------------------------------------------------------------- 16 Xiao explanation
s = slide()
header(s, "16", "Xiao · explaining the gap", "per-attempt collision probability", "ns-3 collides more often than the model's fixed point", size=27)
table(s, MX, 2.3, CW, [3.4, 1.6, 3.3, 3.1], [
    ["Setting", "p, model", "P(fail | stage j), ns-3", "P_drop: measured vs p^(L+1)"],
    ["Combined, n = 30, class 0", "0.580", "!0.66, 0.66, 0.67, 0.66", "0.130 vs 0.66⁵ = 0.125"],
    ["Combined, n = 30, class 1", "0.588", "0.61–0.62", "0.020 vs 0.61⁸ = 0.019"],
    ["Equal knobs (DCF), n = 10", "0.416", "0.44–0.49", "—"],
], size=12, head_size=12, row_h=0.5)
card(s, MX, 4.55, cw3, 2.3, "Holds in ns-3", [
    "p is equal at every stage (decoupling).",
    "P_drop = p^(L+1) (eq. 16)."], color=GOOD, size=13.5)
card(s, MX + cw3 + 0.2, 4.55, cw3, 2.3, "Amplified", [
    "Class 0 has 5 attempts: drops double (13 % vs 6.6 %), its airtime goes to class 1."], color=PEAK, size=13.5)
card(s, MX + 2 * (cw3 + 0.2), 4.55, cw3, 2.3, "Likely cause (open)", [
    "Post-collision timing: ACK timeout 45 µs vs EIFS 94 µs. OPNET matched the model; ns-3 does not."],
     size=13.5)
_, tf = textbox(s, MX, 6.92, CW, 0.35)
p = para(tf, first=True, space_after=0)
run(p, "Excluded: ", 11.5, INK, bold=True)
run(p, "PHY constants (≈ 1 %) · frame size · σ / retry implementation · "
       "traffic model (saturated) · run count (CI < 4 %)", 11.5, MUTED)

# ---------------------------------------------------------------- 17 takeaways
s = slide()
header(s, "17", "Baseline for the final project", "what carries over", "What the final project takes from these baselines", size=27)
cw4 = (CW - 0.6) / 4
for i, (h, t) in enumerate([
        ("Standard PHY", "Use real 802.11 timing and report the retry limit; variants B, C only explain the gaps."),
        ("Delay + drops", "Report delivered-frame delay with drop probability; keep the MAC queue lifetime long."),
        ("Models ≠ truth", "Analytical models give direction; absolute values under strong priority need ns-3."),
        ("σ available", "CwGrowthFactor joins CWmin, CWmax, AIFSN, retry in the policy search.")]):
    card(s, MX + i * (cw4 + 0.2), 2.4, cw4, 3.0, h, [t], size=14, color=PEAK if i == 1 else ACCENT)
rect(s, MX, 5.7, CW, 0.9, fill=CARD, line=HAIR, radius=0.1)
_, tf = textbox(s, MX + 0.3, 5.8, CW - 0.6, 0.7, anchor=MSO_ANCHOR.MIDDLE)
p = para(tf, first=True, space_after=0)
run(p, "Next  ", 13, ACCENT, bold=True, font=MONO)
run(p, "replace saturation with Poisson, MMPP and 3GPP XR traffic, then search the EDCA parameters per traffic model.", 15, INK)

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides._sldIdLst))
