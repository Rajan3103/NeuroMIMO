"""Builds docs/NeuroMIMO_Problem_Solution_Working.pdf: the whole project told as
one story - the problem, the solution, and how it works step by step.

Reuses the layout of build_documentation.py and the diagram helpers of
build_project_explainer.py. Result numbers are read from backend/results/.

Usage (from the repository root):
    python docs/build_problem_solution.py
"""

import os
import sys
from datetime import date

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, NextPageTemplate, PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_documentation import (  # noqa: E402  (path set up above)
    BODY,
    BOLD,
    ITALIC,
    LINK_BLUE,
    ROOT,
    RULE_GREY,
    S,
    DocTemplate,
    P,
    booktabs,
    bullets,
    by_snr,
    figure,
    fmt_nmse,
    load,
    mono,
    section,
)
from build_project_explainer import (  # noqa: E402
    C_API,
    C_CORE,
    C_EDGE,
    C_FRONT,
    C_STORE,
    C_TEXT,
    _arrow,
    _box,
    architecture_diagram,
    diagram_block,
    flow_diagram,
)

OUTPUT = os.path.join(ROOT, "docs", "NeuroMIMO_Problem_Solution_Working.pdf")

S["ps_box"] = ParagraphStyle("ps_box", parent=S["body"], fontSize=10, leading=13.6, spaceAfter=0)
S["ps_label"] = ParagraphStyle("ps_label", parent=S["body"], fontName=BOLD, fontSize=10.5, leading=13,
                               spaceAfter=0, textColor=colors.HexColor("#1B2430"))


class StoryTemplate(DocTemplate):
    def _header(self, canv, doc):
        canv.saveState()
        top = A4[1] - 18 * mm
        canv.setFont(ITALIC, 10.5)
        canv.drawString(self.leftMargin, top, "NeuroMIMO — Problem, Solution and Working")
        canv.setFont(BODY, 10.5)
        canv.drawRightString(A4[0] - self.rightMargin, top, str(doc.page - 1))
        canv.setLineWidth(0.5)
        canv.line(self.leftMargin, top - 4, A4[0] - self.rightMargin, top - 4)
        canv.restoreState()


def callout(text, W, fill="#EEF3FB", edge="#1F4E9E"):
    t = Table([[Paragraph(text, S["ps_box"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fill)),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor(edge)),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def summary_grid(W, problem, solution, outcome):
    """Three coloured cards: Problem, Solution, Result."""
    cells = []
    for label, text, colour in (("THE PROBLEM", problem, "#FDECEC"), ("THE SOLUTION", solution, "#EAF5EC"),
                                ("THE RESULT", outcome, "#EEF3FB")):
        cells.append([Paragraph(label, S["ps_label"]), Spacer(1, 3), Paragraph(text, S["ps_box"])])
    t = Table([[c] for c in cells], colWidths=[W])
    style = [("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY),
             ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
             ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
             ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE_GREY)]
    for i, colour in enumerate(("#FDECEC", "#EAF5EC", "#EEF3FB")):
        style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(colour)))
    t.setStyle(TableStyle(style))
    return t


def multipath_diagram(W):
    """Transmitter, receiver, a direct path, two reflected paths and noise."""
    h = 170
    d = Drawing(W, h)
    _box(d, 6, 62, 92, 44, C_FRONT, ["Transmitter", "2 antennas"])
    _box(d, W - 98, 62, 92, 44, C_FRONT, ["Receiver", "2 antennas"])
    # Reflectors (buildings)
    for x, y, label in ((W * 0.42, 132, "Building"), (W * 0.42, 6, "Vehicle / wall")):
        d.add(Rect(x, y, 80, 28, fillColor=C_STORE, strokeColor=C_EDGE, strokeWidth=0.8))
        d.add(String(x + 40, y + 10, label, fontName=BODY, fontSize=8, fillColor=C_TEXT, textAnchor="middle"))
    tx_r, rx_l = 98, W - 98
    _arrow(d, tx_r, 84, rx_l, 84, "direct path (strongest, first)", 0, 4)
    # Reflected path via top building
    top_mid = (W * 0.42 + 40, 132)
    d.add(Line(tx_r, 98, top_mid[0], top_mid[1], strokeColor=C_EDGE, strokeWidth=1, strokeDashArray=[3, 2]))
    _arrow(d, top_mid[0], top_mid[1], rx_l, 98, "echo (later, weaker)", 34, 8)
    # Reflected path via bottom reflector
    bot_mid = (W * 0.42 + 40, 34)
    d.add(Line(tx_r, 70, bot_mid[0], bot_mid[1], strokeColor=C_EDGE, strokeWidth=1, strokeDashArray=[3, 2]))
    _arrow(d, bot_mid[0], bot_mid[1], rx_l, 70, "echo (later, weaker)", 34, -12)
    d.add(String(W - 52, 116, "+ noise", fontName=ITALIC, fontSize=8.5, fillColor=colors.HexColor("#B03030"),
                 textAnchor="middle"))
    return d


def residual_diagram(W):
    """H_LS -> network -> correction -> + -> refined estimate."""
    h = 82
    d = Drawing(W, h)
    bw, bh, y = (W - 4 * 22) / 5, 46, 12
    xs = [i * (bw + 22) for i in range(5)]
    labels = [
        (["Noisy pilots", "Y = H X + noise"], C_FRONT),
        (["LS estimate", "H_LS = Y / X"], C_CORE),
        (["Neural network", "f(H_LS)"], C_API),
        (["Add correction", "H_LS + f(H_LS)"], C_CORE),
        (["Refined channel", "H_DNN"], C_STORE),
    ]
    for x, (lines, fill) in zip(xs, labels):
        _box(d, x, y, bw, bh, fill, lines, size=7.8)
    for i in range(4):
        _arrow(d, xs[i] + bw, y + bh / 2, xs[i + 1], y + bh / 2)
    # Skip connection: LS estimate goes straight to the adder
    d.add(Line(xs[1] + bw / 2, y + bh, xs[1] + bw / 2, y + bh + 8, strokeColor=C_EDGE, strokeWidth=1))
    d.add(Line(xs[1] + bw / 2, y + bh + 8, xs[3] + bw / 2, y + bh + 8, strokeColor=C_EDGE, strokeWidth=1))
    _arrow(d, xs[3] + bw / 2, y + bh + 8, xs[3] + bw / 2, y + bh, "skip connection", -(xs[3] - xs[1]) / 2, 7)
    return d


# -----------------------------------------------------------------------------
# Sections
# -----------------------------------------------------------------------------
def one_page_summary(story, W, rec):
    story.append(section("The Project in One Page"))
    story.append(P(
        "<b>NeuroMIMO</b> is a software platform that simulates a modern wireless link (the kind used in 5G "
        "and Wi-Fi) and studies how the receiver can work out what the air has done to the signal. It "
        "compares two classical methods with an artificial-intelligence method and shows everything in an "
        "interactive web dashboard."))
    story.append(Spacer(1, 4))
    story.append(summary_grid(
        W,
        "A radio signal reaches the receiver through many reflected paths and picks up noise, so every "
        "frequency is weakened and rotated differently. To recover the data, the receiver must estimate "
        "this <b>channel</b> from a few known <b>pilot</b> symbols, fast and accurately. The simple method "
        "(Least Squares) is noisy; the best classical method (LMMSE) needs knowledge of the channel's "
        "statistics that a real receiver does not have.",
        "Build a complete 2×2 MIMO-OFDM simulator and compare three channel estimators on exactly the "
        "same channels: <b>Least Squares</b>, <b>Linear MMSE</b>, and a <b>residual deep neural "
        "network</b> that takes the noisy LS estimate and learns to correct it. Measure accuracy, bit "
        "errors with confidence intervals, and speed, and serve it all through a FastAPI backend and a "
        "React dashboard.",
        f"At 0 dB SNR (very noisy) LMMSE is best ({fmt_nmse(rec['MMSE'][0.0])}), and the DNN "
        f"({fmt_nmse(rec['DNN'][0.0])}) beats LS ({fmt_nmse(rec['LS'][0.0])}) <i>without</i> needing "
        "channel statistics. At high SNR the DNN levels off near −25 dB while LS and LMMSE reach "
        f"{fmt_nmse(rec['LS'][30.0])}. Every estimator runs in under 1 ms per frame. The project shows "
        "where learning helps, where it does not, and why.",
    ))


def problem(story, W):
    story.append(PageBreak())
    story.append(section("1. The Problem"))

    story.append(P("1.1 Background: how modern wireless links work", "h2"))
    story.append(P(
        "Phones, Wi-Fi routers and 5G base stations all use two key technologies. <b>MIMO</b> "
        "(Multiple-Input Multiple-Output) uses several antennas at each end to send several data streams at "
        "the same time on the same frequency, multiplying the data rate. <b>OFDM</b> (Orthogonal "
        "Frequency-Division Multiplexing) splits the frequency band into many narrow <i>subcarriers</i> "
        "that each carry part of the data. Together, MIMO-OFDM is the physical layer of 4G LTE, 5G NR and "
        "Wi-Fi 6/7."))

    story.append(P("1.2 What goes wrong in the air", "h2"))
    story.append(diagram_block(multipath_diagram(W),
                               "Figure 1: The signal arrives through a direct path and delayed echoes, "
                               "plus noise."))
    story += bullets([
        "<b>Multipath:</b> the signal bounces off buildings, walls and vehicles, so several copies arrive at "
        "slightly different times. They add up constructively at some frequencies and cancel at others "
        "(<i>frequency-selective fading</i>).",
        "<b>Fading:</b> with no clear line of sight the combined signal strength varies randomly "
        "(<i>Rayleigh fading</i>).",
        "<b>Noise:</b> the receiver's electronics add random noise. The weaker the signal compared with the "
        "noise (low SNR), the harder it is to read.",
        "<b>MIMO mixing:</b> each receive antenna hears <i>both</i> transmit antennas at once, mixed "
        "together.",
    ])

    story.append(P("1.3 Why the receiver must estimate the channel", "h2"))
    story.append(P(
        "On each subcarrier k, what the receiver gets is the transmitted symbols multiplied by the channel, "
        "plus noise:"))
    story.append(P("<b>y</b>[k] = <b>H</b>[k] · <b>x</b>[k] + <b>n</b>[k]", "eq"))
    story.append(P(
        "Here <b>H</b>[k] is a 2×2 matrix of complex numbers: how each transmit antenna reaches each "
        "receive antenna on that frequency. To recover the data <b>x</b>, the receiver has to undo "
        "<b>H</b>, so it must first <b>estimate</b> it. A wrong estimate means wrongly decoded bits. "
        "The transmitter helps by sending <b>pilots</b>: known symbols on known subcarriers. Comparing what "
        "arrived with what was sent reveals the channel at those positions."))

    story.append(P("1.4 Why this is hard", "h2"))
    rows = [["Difficulty", "In this project"]]
    rows += [
        ["Few measurements", "Only 4 pilots per transmit antenna, but the channel is needed on all 64 subcarriers."],
        ["Many unknowns", "Four separate channels (2 transmit × 2 receive antennas) per subcarrier."],
        ["Noise", "At 0 dB SNR the noise is as strong as the signal, so pilot measurements are very noisy."],
        ["Unknown statistics", "A real receiver does not know the channel's correlation or the exact noise level."],
        ["Real-time deadline", "A 5G slot lasts about 1 ms, so the estimate must be computed in well under that."],
    ]
    story.append(booktabs(rows, [W * 0.26, W * 0.74], zebra=True, align_center_from=99))

    story.append(P("1.5 Limits of the existing solutions", "h2"))
    rows = [["Method", "Strength", "Weakness"]]
    rows += [
        ["Least Squares (LS)", "Simple, fast, needs no prior knowledge",
         "Passes all the pilot noise into the estimate; poor at low SNR"],
        ["Linear MMSE (LMMSE)", "Best linear estimator; removes noise using statistics",
         "Needs the channel correlation and noise level; matrix inverse is costly"],
        ["Published deep learning", "Can learn the channel's structure from data",
         "Often shown only in favourable conditions, without confidence intervals or speed"],
    ]
    story.append(booktabs(rows, [W * 0.24, W * 0.36, W * 0.40], zebra=True, align_center_from=99))

    story.append(Spacer(1, 6))
    story.append(callout(
        "<b>Problem statement.</b> How accurately, how reliably and how fast can a lightweight deep neural "
        "network estimate the channel of a 2×2 MIMO-OFDM link from pilot symbols, compared with LS and "
        "LMMSE, across noisy and clean conditions (0–30 dB SNR), and does it work without knowing the "
        "channel statistics?", W, fill="#FDECEC", edge="#B03030"))


def solution(story, W):
    story.append(PageBreak())
    story.append(section("2. The Solution"))

    story.append(P("2.1 The idea", "h2"))
    story.append(P(
        "Instead of claiming that AI is better, NeuroMIMO builds a fair test bench. It simulates the whole "
        "radio link, runs every estimator on <b>exactly the same</b> channels and noise, and measures them "
        "with the same yardsticks. The AI estimator is designed to need only what a real receiver has: the "
        "noisy pilot measurements."))

    story.append(P("2.2 What was built", "h2"))
    rows = [["Component", "What it is", "Why it is needed"]]
    rows += [
        ["MIMO-OFDM simulator", "Transmitter, channel and receiver in Python/NumPy",
         "Creates realistic signals where the true channel is known, so errors can be measured exactly"],
        ["Least Squares estimator", "Received pilot ÷ known pilot, then DFT interpolation",
         "The simple baseline every receiver can run"],
        ["LMMSE estimator", "Wiener filter using channel statistics and noise level",
         "The classical best-case reference"],
        ["Residual DNN estimator", "PyTorch network that corrects the LS estimate",
         "The learned method under test"],
        ["Perfect-CSI reference", "Uses the true channel",
         "Shows the best possible bit error rate"],
        ["Evaluation framework", "Five experiments, confidence intervals, timing",
         "Makes the comparison fair, honest and repeatable"],
        ["Web platform", "FastAPI backend + React dashboard",
         "Lets anyone run, train and explore the results"],
        ["DeepMIMO loader", "Reads ray-traced channels from realistic scenes",
         "Tests the methods beyond the built-in channel model"],
    ]
    story.append(booktabs(rows, [W * 0.24, W * 0.36, W * 0.40], zebra=True, align_center_from=99))

    story.append(P("2.3 The key idea: a residual network", "h2"))
    story.append(diagram_block(residual_diagram(W), "Figure 2: The DNN learns only the correction to LS."))
    story.append(P(
        "The LS estimate is already roughly right; its problem is noise. So the network is not asked to "
        "find the channel from scratch. It takes the LS estimate as input and learns a <b>correction</b> "
        "that is added back:"))
    story.append(P("Ĥ<sub>DNN</sub> = Ĥ<sub>LS</sub> + f<sub>θ</sub>(Ĥ<sub>LS</sub>)", "eq"))
    story.append(P(
        "This is easier to learn, trains faster, and means the network starts from LS quality rather than "
        "from nothing. The network is small (330,112 parameters), so it runs in real time on an ordinary "
        "CPU."))

    story.append(P("2.4 Design decisions", "h2"))
    rows = [["Decision", "Reason"]]
    rows += [
        ["2×2 antennas, 64 subcarriers", "The smallest real MIMO case: fast to simulate and train on a laptop."],
        ["Comb pilots, 4 per antenna", "Pilots in every symbol; 4 pilots are exactly enough for a 4-tap channel."],
        ["Orthogonal pilot positions", "The two antennas use different subcarriers, so their pilots never collide."],
        ["16-sample cyclic prefix", "Longer than the channel, so echoes do not spill into the next symbol."],
        ["Identical channels for all methods", "Differences then come from the estimators, not from luck."],
        ["Train/validation/test split", "The network is tested on channels it never saw during training."],
        ["Confidence intervals on BER", "A finite test has uncertainty; the intervals show how much."],
    ]
    story.append(booktabs(rows, [W * 0.34, W * 0.66], zebra=True, align_center_from=99))


def working(story, W):
    story.append(PageBreak())
    story.append(section("3. How It Works"))
    story.append(P(
        "This section follows one frame of data from the transmitter, through the air, to the receiver, "
        "then explains how the network learns and how results are measured."))

    story.append(P("3.1 The complete signal chain", "h2"))
    steps = [
        ["1. Bits", "random 0s and 1s"],
        ["2. Modulation", "QPSK / 16-QAM", "symbols"],
        ["3. Frame assembly", "insert comb pilots"],
        ["4. IFFT + CP", "to time domain"],
        ["5. Channel", "Rayleigh / AWGN /", "DeepMIMO"],
        ["6. Noise", "AWGN at target SNR"],
        ["7. CP removal + FFT", "back to subcarriers"],
        ["8. Pilot extraction", "average over", "14 symbols"],
        ["9. Estimation", "LS • LMMSE • DNN", "• perfect"],
        ["10. Equalisation", "MMSE (<15 dB)", "or zero-forcing"],
        ["11. Demodulation", "symbols to bits"],
        ["12. Metrics", "NMSE • BER • SER", "• time"],
    ]
    story.append(diagram_block(flow_diagram(steps, W), "Figure 3: One frame from transmitter to metrics."))

    story.append(P("3.2 Transmitter (steps 1–4)", "h2"))
    story += bullets([
        "<b>Bits:</b> random data, 3,136 bits per frame with QPSK (2 antennas × 14 symbols × 56 "
        "data subcarriers × 2 bits).",
        "<b>Modulation:</b> each pair of bits becomes one QPSK symbol (a point on a circle). Gray coding "
        "means a small error flips only one bit.",
        "<b>Frame assembly:</b> antenna 0 puts pilots on subcarriers 0, 16, 32, 48 and antenna 1 on 8, 24, "
        "40, 56; each stays silent on the other's pilots. The other 56 subcarriers carry data.",
        "<b>IFFT + cyclic prefix:</b> the IFFT turns the 64 subcarriers into a time signal, and the last 16 "
        "samples are copied to the front as a guard against echoes.",
    ])

    story.append(P("3.3 The channel (steps 5–6)", "h2"))
    story += bullets([
        "<b>Rayleigh multipath:</b> each of the 4 antenna pairs gets 4 random echo taps, the first strongest "
        "and later ones weaker (exponential power delay profile). The channel stays constant for the whole "
        "14-symbol frame (block fading).",
        "<b>Noise:</b> Gaussian noise is added so that the received signal has exactly the requested SNR, "
        "from 0 dB (noise as strong as signal) to 30 dB (signal 1000 times stronger).",
        "<b>Optional realism:</b> instead of the random model, channels can come from DeepMIMO ray-tracing "
        "of real-looking scenes.",
    ])

    story.append(P("3.4 Receiver (steps 7–12)", "h2"))
    story += bullets([
        "<b>CP removal + FFT:</b> the receiver drops the guard samples and returns to the 64 subcarriers.",
        "<b>Pilot extraction:</b> it reads the pilot subcarriers and averages each pilot over the 14 symbols, "
        "which cuts the noise 14 times (the channel does not change within the frame).",
        "<b>Channel estimation:</b> one of the estimators (Section 3.5) produces Ĥ for all 64 "
        "subcarriers and all four antenna pairs.",
        "<b>Equalisation:</b> the receiver undoes Ĥ on the data subcarriers to separate the two streams "
        "(MMSE equaliser below 15 dB, zero-forcing above).",
        "<b>Demodulation and metrics:</b> symbols become bits again; the receiver counts errors and compares "
        "Ĥ with the true channel.",
    ])

    story.append(P("3.5 The three estimators", "h2"))
    rows = [["Estimator", "How it works", "Needs"]]
    rows += [
        ["Least Squares",
         "Divide each received pilot by the known pilot (Ĥ = Y/X), then fill in the other "
         "subcarriers with DFT interpolation.", "Nothing extra"],
        ["Linear MMSE",
         "Smooth the LS pilot estimates with a Wiener filter built from the channel's frequency correlation "
         "and the pilot noise level (σ²/14 after averaging).", "Channel statistics + noise level"],
        ["Residual DNN",
         "Feed the LS estimate (512 numbers) through a 512→256→128→256→512 network "
         "and add its output as a correction.", "A trained model"],
    ]
    story.append(booktabs(rows, [W * 0.18, W * 0.58, W * 0.24], zebra=True, align_center_from=99))

    story.append(P("3.6 How the network learns", "h2"))
    steps = [
        ["1. Draw channels", "30,000 random", "channels"],
        ["2. Random SNR", "uniform 0–30 dB"],
        ["3. Send pilots", "through channel", "+ noise"],
        ["4. Input", "noisy LS estimate", "(512 values)"],
        ["5. Target", "true channel H", "(512 values)"],
        ["6. Split", "70% train, 15% val,", "15% test"],
        ["7. Train", "Adam, MSE loss,", "40 epochs"],
        ["8. Keep best", "lowest validation", "loss checkpoint"],
    ]
    story.append(diagram_block(flow_diagram(steps, W, fill=C_API), "Figure 4: Training the residual DNN."))
    story.append(P(
        "Because this is a simulation, the true channel is known for every example, so the network can "
        "be taught the right answer. It only ever sees what a real receiver would have (the noisy LS "
        "estimate), and it is tested on channels it never saw during training."))

    story.append(P("3.7 How the results are measured", "h2"))
    story += bullets([
        "<b>NMSE:</b> how far Ĥ is from the true channel, relative to the channel's power, in dB. "
        "−10 dB means 10% error, −20 dB means 1%.",
        "<b>BER / SER:</b> the fraction of wrong bits and symbols after the whole receiver.",
        "<b>95% confidence intervals:</b> Wilson intervals on every BER point; when no errors are seen, the "
        "“rule of three” gives an upper bound instead of claiming zero.",
        "<b>Fairness:</b> the random generator is reset with the same seed for every estimator, so all of "
        "them face identical channels and noise.",
        "<b>Speed:</b> each estimator is timed 100 times after 10 warm-up runs.",
    ])

    story.append(KeepTogether([
        P("3.8 How you use it", "h2"),
        architecture_diagram(W),
        P("Figure 5: The web platform around the simulator.", "caption"),
    ]))
    story.append(P(
        f"You open the dashboard in a browser, choose settings and press a button. The React page sends the "
        f"settings to the FastAPI backend (for example {mono('POST /api/simulation/run')}), the backend runs "
        "the signal chain of Figure 3, saves the run in SQLite and returns the numbers, and the page draws "
        "the charts. Training runs in the background while the page shows the loss curve live."))


def results(story, W, rec, lat):
    story.append(PageBreak())
    story.append(section("4. What the Solution Achieved"))
    rows = [["SNR", "LS", "LMMSE", "DNN", "Best"]]
    for snr in (0.0, 10.0, 20.0, 30.0):
        vals = {a: rec[a][snr]["nmse_db"] for a in ("LS", "MMSE", "DNN")}
        best = min(vals, key=vals.get)
        rows.append([f"{snr:.0f} dB", fmt_nmse(rec["LS"][snr]), fmt_nmse(rec["MMSE"][snr]),
                     fmt_nmse(rec["DNN"][snr]), {"MMSE": "LMMSE"}.get(best, best)])
    story.append(booktabs(rows, [W * 0.14, W * 0.215, W * 0.215, W * 0.215, W * 0.215], zebra=True))
    story.append(P("Table: channel estimation error (NMSE, lower is better), Rayleigh channel, QPSK.", "caption"))
    story.append(figure("nmse_vs_snr.png", "Figure 6: NMSE versus SNR for every estimator.", W * 0.7))

    story.append(P("Answering the problem statement", "h2"))
    story += bullets([
        f"<b>Accuracy in noisy conditions:</b> LMMSE is best ({fmt_nmse(rec['MMSE'][0.0])} at 0 dB), as "
        f"theory predicts. The DNN ({fmt_nmse(rec['DNN'][0.0])}) beats LS ({fmt_nmse(rec['LS'][0.0])}) and "
        "comes close to LMMSE <b>without knowing the channel statistics</b>, which a real receiver lacks.",
        f"<b>Accuracy in clean conditions:</b> the DNN levels off near −25 dB while LS and LMMSE keep "
        f"improving to {fmt_nmse(rec['LS'][30.0])}. One small network trained across the whole 0–30 dB "
        "range cannot match LS when the noise is tiny.",
        f"<b>Speed:</b> LS {lat['LS']['mean_ms']:.2f} ms, LMMSE {lat['MMSE']['mean_ms']:.2f} ms, DNN "
        f"{lat['DNN']['mean_ms']:.2f} ms per frame on a CPU, all well inside a 1 ms 5G slot.",
        "<b>Reliability:</b> every result is reproducible from fixed seeds and covered by 88 automated tests.",
    ])

    story.append(P("Problems found and fixed during the project", "h2"))
    story += bullets([
        "<b>LMMSE noise level:</b> LMMSE was first given the noise level before pilot averaging (σ² "
        "instead of σ²/14), which made it look worse than LS. Fixing it made LMMSE the best "
        "estimator at low SNR, matching theory.",
        "<b>Overwritten model:</b> a test had overwritten the trained model with a 2-epoch test model. The "
        "test was fixed, and the DNN was retrained on 30,000 channels.",
    ])


def conclusion(story, W):
    story.append(section("5. Conclusion"))
    story.append(callout(
        "NeuroMIMO shows that a small residual neural network can estimate a MIMO-OFDM channel better than "
        "Least Squares in noisy conditions and close to LMMSE, <b>without the channel statistics LMMSE "
        "needs</b>, and fast enough for real time. It also shows honestly where it falls short: at high "
        "SNR it has an error floor. The platform makes this comparison fair, repeatable and easy to explore.",
        W, fill="#EAF5EC", edge="#2E7D32"))
    story.append(P("Limitations", "h2"))
    story += bullets([
        "Simulated channels by default (the DeepMIMO loader is the step toward realism).",
        "Small 2×2 system, block fading with no Doppler, perfect synchronisation.",
        "The DNN's high-SNR error floor.",
    ])
    story.append(P("Future work", "h2"))
    story += bullets([
        "Give the SNR to the network as an input, or train one model per SNR range, to remove the floor.",
        "Use a convolutional network across time and frequency.",
        "Add moving users (Doppler, Jakes model) and larger antenna arrays (4×4, 8×8).",
        "Evaluate on DeepMIMO ray-traced channels and learn the pilot placement.",
    ])


def build():
    sweep = load("snr_sweep_results.json")
    lat = load("inference_time_results.json")["results"]
    rec = {a: by_snr(r) for a, r in sweep["records"].items()}

    doc = StoryTemplate(OUTPUT, title="NeuroMIMO — Problem, Solution and Working", author="NeuroMIMO",
                        subject="The whole project: problem, solution and how it works")
    W = doc.width
    story = [
        Spacer(1, 50 * mm),
        P("NeuroMIMO", "title"),
        Spacer(1, 6),
        P("P<font size='12'>ROBLEM</font>, S<font size='12'>OLUTION AND</font> W<font size='12'>ORKING</font>",
          "subtitle"),
        Spacer(1, 22 * mm),
        P("The whole project, explained from start to finish", "tag"),
        Spacer(1, 22 * mm),
        P("AI-enhanced channel estimation for 2×2 MIMO-OFDM wireless systems: what problem it solves, "
          "how the solution is designed, and how every part works.", "abstract"),
        Spacer(1, 80 * mm),
        P(date.today().strftime("%B %d, %Y").replace(" 0", " "), "date"),
        NextPageTemplate("toc"),
        PageBreak(),
    ]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc0", fontName=BODY, fontSize=10.5, leading=15,
                                      textColor=LINK_BLUE, leftIndent=10)]
    story += [Spacer(1, 25 * mm), P("Contents", "toc_title"), toc, NextPageTemplate("main"), PageBreak()]

    one_page_summary(story, W, rec)
    problem(story, W)
    solution(story, W)
    working(story, W)
    results(story, W, rec, lat)
    conclusion(story, W)

    doc.multiBuild(story)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
