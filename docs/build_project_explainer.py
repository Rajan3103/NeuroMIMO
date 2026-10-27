"""Builds docs/NeuroMIMO_Project_Explained.pdf: a plain-English guide to the whole
project with abbreviations, key concepts, architecture and workflow diagrams.

Reuses the page layout and styles of build_documentation.py. Result numbers are
read from backend/results/, so they always match the code.

Usage (from the repository root):
    pip install reportlab pillow
    python docs/build_project_explainer.py
"""

import os
import sys
from datetime import date

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, NextPageTemplate, PageBreak, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_documentation import (  # noqa: E402  (path set up above)
    BODY,
    BOLD,
    ITALIC,
    LINK_BLUE,
    ROOT,
    S,
    DocTemplate,
    P,
    booktabs,
    bullets,
    by_snr,
    code_box,
    figure,
    fmt_ber,
    fmt_nmse,
    load,
    mono,
    section,
)

OUTPUT = os.path.join(ROOT, "docs", "NeuroMIMO_Project_Explained.pdf")

# Diagram palette (prints well in colour and greyscale)
C_FRONT = colors.HexColor("#DCEFFB")
C_API = colors.HexColor("#E6E1F7")
C_CORE = colors.HexColor("#DFF3E8")
C_STORE = colors.HexColor("#FBEBD5")
C_EDGE = colors.HexColor("#3A4A5E")
C_TEXT = colors.HexColor("#1B2430")

S["box_note"] = ParagraphStyle("box_note", parent=S["body"], fontSize=9.6, leading=13,
                               textColor=colors.HexColor("#333333"))


class ExplainerTemplate(DocTemplate):
    def _header(self, canv, doc):
        canv.saveState()
        top = A4[1] - 18 * mm
        canv.setFont(ITALIC, 10.5)
        canv.drawString(self.leftMargin, top, "NeuroMIMO — The Project Explained")
        canv.setFont(BODY, 10.5)
        canv.drawRightString(A4[0] - self.rightMargin, top, str(doc.page - 1))
        canv.setLineWidth(0.5)
        canv.line(self.leftMargin, top - 4, A4[0] - self.rightMargin, top - 4)
        canv.restoreState()


# -----------------------------------------------------------------------------
# Diagram helpers
# -----------------------------------------------------------------------------
def _box(d, x, y, w, h, fill, lines, bold_first=True, size=8.2):
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=fill, strokeColor=C_EDGE, strokeWidth=0.8))
    n = len(lines)
    line_h = size + 2.2
    start = y + h / 2 + (n - 1) * line_h / 2 - size * 0.35
    for i, text in enumerate(lines):
        font = BOLD if (i == 0 and bold_first) else BODY
        d.add(String(x + w / 2, start - i * line_h, text, fontName=font, fontSize=size,
                     fillColor=C_TEXT, textAnchor="middle"))


def _arrow(d, x1, y1, x2, y2, label=None, label_dx=0, label_dy=3):
    d.add(Line(x1, y1, x2, y2, strokeColor=C_EDGE, strokeWidth=1))
    # Arrowhead pointing at (x2, y2)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 5
    left = (x2 - size * math.cos(ang - 0.4), y2 - size * math.sin(ang - 0.4))
    right = (x2 - size * math.cos(ang + 0.4), y2 - size * math.sin(ang + 0.4))
    d.add(Polygon([x2, y2, left[0], left[1], right[0], right[1]], fillColor=C_EDGE, strokeColor=C_EDGE))
    if label:
        d.add(String((x1 + x2) / 2 + label_dx, (y1 + y2) / 2 + label_dy, label, fontName=ITALIC,
                     fontSize=7.2, fillColor=C_EDGE, textAnchor="middle"))


def architecture_diagram(W):
    h = 330
    d = Drawing(W, h)
    col = W / 2

    # Layer 1: user + browser
    _box(d, col - 95, h - 42, 190, 34, C_FRONT, ["User (web browser)", "http://localhost:5173"])
    # Layer 2: frontend
    _box(d, 10, h - 120, W - 20, 52, C_FRONT,
         ["React Frontend (Vite + TypeScript + Tailwind + Recharts)",
          "8 pages: Overview • Simulator • Estimation Lab • Training • Comparison",
          "Signal Visualization • Experiment History • About   |   api/client.ts"])
    _arrow(d, col, h - 42, col, h - 68, "clicks / views", 34, 0)
    # Layer 3: API
    _box(d, 10, h - 192, W - 20, 44, C_API,
         ["FastAPI Backend (neuromimo/api/main.py + schemas.py)",
          "13 REST endpoints • Pydantic validation • CORS • background training thread"])
    _arrow(d, col - 40, h - 120, col - 40, h - 148, "HTTP JSON via /api proxy", -52, 0)
    _arrow(d, col + 40, h - 148, col + 40, h - 120, "JSON results", 30, 0)
    # Layer 4: core packages
    bw = (W - 20 - 3 * 8) / 4
    pkgs = [
        ["wireless/", "modulation, OFDM,", "channel, equalizer,", "simulation, deepmimo"],
        ["estimation/", "LS, LMMSE, DNN,", "trainer, train_cli"],
        ["evaluation/", "metrics, benchmarks,", "experiments, CLIs"],
        ["storage/", "database.py", "(SQLite access)"],
    ]
    for i, lines in enumerate(pkgs):
        x = 10 + i * (bw + 8)
        _box(d, x, h - 268, bw, 50, C_CORE, lines)
        _arrow(d, x + bw / 2, h - 192, x + bw / 2, h - 218)
    # Layer 5: storage
    sw = (W - 20 - 2 * 10) / 3
    stores = [
        ["models/neuromimo_dnn.pt", "trained DNN weights"],
        ["results/", "JSON, CSV, 300 DPI PNG"],
        ["data/experiments.db", "SQLite run history"],
    ]
    for i, lines in enumerate(stores):
        x = 10 + i * (sw + 10)
        _box(d, x, 6, sw, 34, C_STORE, lines)
    _arrow(d, 10 + bw * 1.5 + 8, h - 268, 10 + sw / 2, 40)
    _arrow(d, 10 + 2 * (bw + 8) + bw / 2, h - 268, 10 + sw * 1.5 + 10, 40)
    _arrow(d, 10 + 3 * (bw + 8) + bw / 2, h - 268, 10 + sw * 2.5 + 20, 40)
    return d


def flow_diagram(steps, W, per_row=4, box_h=40, fill=C_CORE):
    """Left-to-right flow that wraps onto new rows (snake order)."""
    rows = (len(steps) + per_row - 1) // per_row
    gap = 16
    bw = (W - (per_row - 1) * gap) / per_row
    row_gap = 24
    h = rows * box_h + (rows - 1) * row_gap + 4
    d = Drawing(W, h)
    positions = []
    for i, lines in enumerate(steps):
        r, c = divmod(i, per_row)
        if r % 2 == 1:
            c = per_row - 1 - c
        x = c * (bw + gap)
        y = h - 2 - (r + 1) * box_h - r * row_gap
        _box(d, x, y, bw, box_h, fill, lines, size=7.8)
        positions.append((x, y, r))
    for i in range(len(steps) - 1):
        x, y, r = positions[i]
        x2, y2, r2 = positions[i + 1]
        if r == r2:
            if r % 2 == 0:
                _arrow(d, x + bw, y + box_h / 2, x2, y2 + box_h / 2)
            else:
                _arrow(d, x, y + box_h / 2, x2 + bw, y2 + box_h / 2)
        else:
            _arrow(d, x + bw / 2, y, x2 + bw / 2, y2 + box_h)
    return d


def diagram_block(drawing, caption):
    return KeepTogether([drawing, P(caption, "caption")])


# -----------------------------------------------------------------------------
# Content
# -----------------------------------------------------------------------------
ABBREVIATIONS = [
    ("3GPP", "3rd Generation Partnership Project", "The body that writes mobile standards such as 5G."),
    ("5G NR", "Fifth Generation New Radio", "The current mobile network standard."),
    ("Adam", "Adaptive Moment Estimation", "The optimiser used to train the neural network."),
    ("API", "Application Programming Interface", "The set of web addresses the frontend calls."),
    ("AWGN", "Additive White Gaussian Noise", "Random noise added to every received sample."),
    ("BER", "Bit Error Rate", "Fraction of received bits that are wrong."),
    ("BS", "Base Station", "The cell tower side of the link."),
    ("CFR", "Channel Frequency Response", "The channel gain on each subcarrier, written H[k]."),
    ("CI", "Confidence Interval / Continuous Integration", "A range likely to hold the true value; or automatic testing on every push."),
    ("CIR", "Channel Impulse Response", "The channel in the time domain (one value per delay tap)."),
    ("CLI", "Command-Line Interface", "A program you run from the terminal."),
    ("CNN", "Convolutional Neural Network", "A network that slides small filters over data."),
    ("CORS", "Cross-Origin Resource Sharing", "Browser rule for which websites may call the API."),
    ("CP", "Cyclic Prefix", "Copy of the end of each OFDM symbol placed at its start to absorb echoes."),
    ("CPU / GPU", "Central / Graphics Processing Unit", "Processors; the DNN runs on the CPU."),
    ("CSI", "Channel State Information", "Knowledge of the channel H at the receiver."),
    ("CSV", "Comma-Separated Values", "A simple spreadsheet file format."),
    ("CUDA", "Compute Unified Device Architecture", "NVIDIA's GPU computing platform (optional)."),
    ("dB", "Decibel", "Logarithmic unit: 10·log10(ratio)."),
    ("DFT", "Discrete Fourier Transform", "Converts between time and frequency; the FFT computes it fast."),
    ("DNN", "Deep Neural Network", "A neural network with several hidden layers."),
    ("DPI", "Dots Per Inch", "Image resolution; figures are saved at 300 DPI."),
    ("FFT / IFFT", "(Inverse) Fast Fourier Transform", "Fast algorithms for the DFT and its inverse."),
    ("GELU", "Gaussian Error Linear Unit", "The activation function used in the DNN."),
    ("HTTP", "Hypertext Transfer Protocol", "How the browser and backend talk."),
    ("ICI", "Inter-Carrier Interference", "Leakage between subcarriers (e.g. from Doppler)."),
    ("IQ", "In-phase and Quadrature", "The real and imaginary parts of a complex symbol."),
    ("ISI", "Inter-Symbol Interference", "Overlap of one symbol's echoes into the next."),
    ("JSON", "JavaScript Object Notation", "Text format for data sent by the API."),
    ("KPI", "Key Performance Indicator", "The summary numbers on dashboard cards."),
    ("LMMSE / MMSE", "(Linear) Minimum Mean Square Error", "Estimator that uses channel statistics to remove noise."),
    ("LoS", "Line of Sight", "A direct path between transmitter and receiver."),
    ("LS", "Least Squares", "Simplest estimator: received pilot divided by sent pilot."),
    ("MIMO", "Multiple-Input Multiple-Output", "Several antennas at both ends of the link."),
    ("MLP", "Multilayer Perceptron", "A fully connected neural network."),
    ("mmWave", "Millimetre Wave", "Very high radio frequencies (about 24–100 GHz)."),
    ("MSE", "Mean Squared Error", "Average of squared errors; the DNN's training loss."),
    ("NMSE", "Normalised Mean Squared Error", "MSE divided by channel power; lower is better."),
    ("OFDM", "Orthogonal Frequency-Division Multiplexing", "Splits a wide band into many narrow subcarriers."),
    ("PDP", "Power Delay Profile", "How channel power is spread over delay taps."),
    ("QAM", "Quadrature Amplitude Modulation", "16-QAM sends 4 bits per symbol."),
    ("QPSK", "Quadrature Phase Shift Keying", "Sends 2 bits per symbol using 4 phases."),
    ("REST", "Representational State Transfer", "Style of web API using URLs and HTTP methods."),
    ("Rx / Tx", "Receiver / Transmitter", "The receiving and sending sides (or antennas)."),
    ("SER", "Symbol Error Rate", "Fraction of received symbols that are wrong."),
    ("SISO", "Single-Input Single-Output", "One antenna at each end."),
    ("SNR", "Signal-to-Noise Ratio", "Signal power over noise power, in dB; higher is cleaner."),
    ("SQLite", "Structured Query Language Lite", "A small file-based database."),
    ("TTI", "Transmission Time Interval", "One scheduling slot in mobile systems."),
    ("UE", "User Equipment", "The phone or device side of the link."),
    ("UI", "User Interface", "The dashboard screens."),
    ("ZF", "Zero-Forcing", "Equaliser that inverts the channel matrix exactly."),
]


def overview(story, W):
    story.append(section("1. What Is NeuroMIMO?"))
    story.append(P(
        "NeuroMIMO is a software project that simulates how a modern wireless link (like 5G or Wi-Fi) "
        "sends data through the air, and compares three ways for the receiver to work out how the air "
        "has distorted the signal. One of those ways is an artificial-intelligence model (a deep neural "
        "network). Everything runs on a normal computer, with no radio hardware."))
    story.append(P("The Idea in Simple Words", "h2"))
    story.append(P(
        "Imagine shouting a message across a busy hall. Your voice bounces off walls, arrives as several "
        "echoes, and mixes with background noise. If the listener first hears a few <i>known</i> words, "
        "they can learn how the hall distorts sound and then understand the rest of your message. In "
        "wireless systems those known words are called <b>pilots</b>, and working out the distortion is "
        "called <b>channel estimation</b>."))
    story.append(P(
        "NeuroMIMO compares three “listeners”: <b>Least Squares (LS)</b>, the simplest; "
        "<b>Linear MMSE</b>, a smarter statistical method; and a <b>Deep Neural Network (DNN)</b> that "
        "learns from thousands of examples. It measures how accurate, how reliable and how fast each one "
        "is, and shows the results in an interactive web dashboard."))
    story.append(P("What the Project Does", "h2"))
    story += bullets([
        "Simulates a 2×2 MIMO-OFDM link: 2 transmit and 2 receive antennas, 64 subcarriers, QPSK or "
        "16-QAM, Rayleigh multipath fading or a plain noise (AWGN) channel.",
        "Estimates the channel with LS, LMMSE and a residual DNN, plus a “perfect knowledge” "
        "reference that shows the best possible result.",
        "Trains the DNN in PyTorch, from the command line or from the dashboard, with a live loss chart.",
        "Runs repeatable experiments (SNR sweep, AWGN vs Rayleigh, generalisation, pilot density, speed) "
        "and saves tables and 300 DPI figures.",
        "Can also use realistic ray-traced channels from DeepMIMO instead of the built-in channel model.",
        "Serves everything through a REST API (FastAPI) and a React dashboard with four colour themes.",
    ])


def abbreviations(story, W):
    story.append(PageBreak())
    story.append(section("2. List of Abbreviations"))
    story.append(P("Every short form used in the project, the code and this document, in alphabetical order."))
    rows = [["Abbreviation", "Full form", "Meaning in this project"]]
    rows += [[a, b, c] for a, b, c in ABBREVIATIONS]
    story.append(booktabs(rows, [W * 0.17, W * 0.36, W * 0.47], zebra=True, align_center_from=99))


def concepts(story, W):
    story.append(PageBreak())
    story.append(section("3. Key Concepts"))
    items = [
        ("MIMO (multiple antennas)",
         "With 2 antennas at each end, two data streams travel at the same time on the same frequency. "
         "The receiver separates them using its knowledge of the 2×2 channel matrix, so it must "
         "estimate four channel paths (each transmit antenna to each receive antenna)."),
        ("OFDM (many narrow subcarriers)",
         "The band is split into 64 subcarriers. Echoes would make a wideband signal hard to equalise, "
         "but each narrow subcarrier only sees one complex gain H[k]. A 16-sample cyclic prefix absorbs "
         "the echoes between OFDM symbols."),
        ("Pilots",
         "Known symbols placed on fixed subcarriers. Transmit antenna 0 uses subcarriers 0, 16, 32, 48 and "
         "antenna 1 uses 8, 24, 40, 56, and each antenna stays silent on the other's pilots, so they never "
         "interfere. The remaining 56 subcarriers carry data."),
        ("The channel H",
         "A Rayleigh channel has 4 delay taps with an exponential power delay profile: the direct, strongest "
         "path first and weaker echoes after it. In the frequency domain this gives a gain that rises and "
         "falls across the 64 subcarriers."),
        ("Noise and SNR",
         "Random noise is added at a chosen signal-to-noise ratio. 0 dB means signal and noise are equally "
         "strong (very noisy); 30 dB means the signal is 1000 times stronger (very clean)."),
        ("Least Squares (LS)",
         "Divides each received pilot by the known pilot: Ĥ<sub>LS</sub>[p] = Y[p] / X[p]. It then "
         "fills in the other subcarriers with DFT interpolation. Fast and needs no prior knowledge, but it "
         "passes all the noise straight into the estimate."),
        ("Linear MMSE (LMMSE)",
         "Combines the LS estimate with the known statistics of the channel and the noise level to "
         "suppress noise: Ĥ = <b>R</b><sub>HP</sub>(<b>R</b><sub>PP</sub> + σ²<b>I</b>)"
         "<super>−1</super>Ĥ<sub>LS</sub>. Strong in theory, but it needs those statistics and a "
         "matrix inversion."),
        ("Residual DNN",
         "A neural network that takes the LS estimate (512 numbers: real and imaginary parts of 2×2"
         "×64 values) and predicts a correction: Ĥ<sub>DNN</sub> = Ĥ<sub>LS</sub> + "
         "f<sub>θ</sub>(Ĥ<sub>LS</sub>). Layers 512→256→128→256→512 with "
         "LayerNorm, GELU and dropout; 330,112 trainable parameters."),
        ("Equalisation",
         "After estimating H, the receiver undoes the channel to recover the transmitted symbols. NeuroMIMO "
         "uses an MMSE equaliser below 15 dB SNR and zero-forcing at 15 dB and above."),
        ("Metrics",
         "NMSE measures how close the estimated channel is to the true one (lower is better, in dB). BER and "
         "SER count wrong bits and symbols after the whole receiver. Every BER point has a 95% Wilson "
         "confidence interval, and zero-error points use the “rule of three” upper bound."),
    ]
    for title, text in items:
        story.append(KeepTogether([P(title, "h2"), P(text)]))


def architecture(story, W):
    story.append(PageBreak())
    story.append(section("4. System Architecture"))
    story.append(P(
        "NeuroMIMO has three layers: a React frontend in the browser, a FastAPI backend that exposes the "
        "simulation as a web API, and a Python core that does the signal processing and machine learning. "
        "Results are stored in files and a small SQLite database."))
    story.append(diagram_block(architecture_diagram(W), "Figure 1: Overall system architecture."))

    story.append(P("Backend Modules", "h2"))
    rows = [["Package / file", "Responsibility"]]
    rows += [
        [mono("config.py"), "Simulation settings (antennas, FFT size, pilots, SNR, seed) and enums."],
        [mono("wireless/modulation.py"), "Gray-coded QPSK and 16-QAM mapping and demapping; random bits."],
        [mono("wireless/ofdm.py"), "Pilot insertion, IFFT + cyclic prefix, CP removal + FFT, pilot extraction."],
        [mono("wireless/channel.py"), "AWGN and Rayleigh multipath channels; adds noise at the target SNR."],
        [mono("wireless/deepmimo.py"), "Loads DeepMIMO ray-traced channels and prepares them for the pipeline."],
        [mono("wireless/equalization.py"), "Zero-forcing and MMSE MIMO equalisers."],
        [mono("wireless/simulation.py"), "MIMOSimulationPipeline: runs one full transmission end to end."],
        [mono("estimation/ls.py, mmse.py"), "Least Squares (with DFT interpolation) and LMMSE estimators."],
        [mono("estimation/dnn.py"), "ChannelEstimationNet (residual MLP) and the DNNEstimator wrapper."],
        [mono("estimation/trainer.py"), "Dataset generation, leakage-free splitting, training loop, checkpoints."],
        [mono("evaluation/metrics.py"), "MSE, NMSE, BER, SER and confidence intervals."],
        [mono("evaluation/experiments.py"), "ExperimentRunner: SNR sweep, channel comparison, generalisation, "
                                            "pilot density, inference time; saves JSON/CSV/figures."],
        [mono("storage/database.py"), "SQLite tables for simulation runs and training runs."],
        [mono("api/main.py, schemas.py"), "FastAPI routes, request validation and the background training job."],
    ]
    story.append(booktabs(rows, [W * 0.36, W * 0.64], zebra=True, align_center_from=99))

    story.append(P("Frontend Structure", "h2"))
    rows = [["Part", "What it does"]]
    rows += [
        [mono("src/api/client.ts"), "Typed functions for every API call; shows backend error messages."],
        [mono("src/theme.ts"), "The four dark colour themes and saving the user's choice."],
        [mono("components/layout/"), "Navbar (API status, theme picker, refresh) and Sidebar (navigation)."],
        [mono("components/common/"), "Reusable StatCard, Badge, Modal, LoadingSpinner, ErrorBanner."],
        [mono("pages/"), "One file per dashboard page (see Section 6)."],
        [mono("vite.config.ts"), "Dev server on port 5173 that forwards /api calls to the backend on 8000."],
    ]
    story.append(booktabs(rows, [W * 0.32, W * 0.68], zebra=True, align_center_from=99))


def workflows(story, W):
    story.append(PageBreak())
    story.append(section("5. Workflows"))

    story.append(P("5.1 Signal Processing Pipeline (one transmission)", "h2"))
    story.append(P(
        f"This is what {mono('MIMOSimulationPipeline.run_single_shot()')} does every time you press "
        "“Run Simulation”. One frame has 14 OFDM symbols; with QPSK that is 3,136 bits."))
    steps = [
        ["1. Bits", "random 0s and 1s"],
        ["2. Modulation", "QPSK / 16-QAM", "symbols"],
        ["3. Frame assembly", "insert comb pilots"],
        ["4. IFFT + CP", "to time domain"],
        ["5. Channel", "Rayleigh / AWGN /", "DeepMIMO"],
        ["6. Noise", "AWGN at target SNR"],
        ["7. CP removal + FFT", "back to subcarriers"],
        ["8. Pilot extraction", "split pilots / data"],
        ["9. Estimation", "LS • LMMSE • DNN", "• perfect"],
        ["10. Equalisation", "MMSE (<15 dB)", "or zero-forcing"],
        ["11. Demodulation", "symbols to bits"],
        ["12. Metrics", "NMSE • BER • SER", "• time"],
    ]
    story.append(diagram_block(flow_diagram(steps, W), "Figure 2: Transmit → channel → receive pipeline."))
    rows = [["Step", "What happens and why"]]
    rows += [
        ["1–2", "Random bits are mapped to complex symbols (2 bits per QPSK symbol, Gray coded so a "
                     "small error flips only one bit)."],
        ["3", "Each transmit antenna's 14×64 grid gets 4 pilots per symbol; the other antenna is silent "
              "on those subcarriers."],
        ["4", "The IFFT turns subcarriers into a time signal; a 16-sample cyclic prefix guards against echoes."],
        ["5–6", "The 2×2 channel H multiplies each subcarrier and noise is added so the received "
                     "signal has exactly the requested SNR."],
        ["7–8", "The receiver removes the prefix, applies the FFT and separates pilot and data subcarriers."],
        ["9", "The chosen estimator produces Ĥ for all 64 subcarriers; NMSE compares it with the true H."],
        ["10–11", "The equaliser undoes Ĥ on the data subcarriers and the demodulator recovers the bits."],
        ["12", "Wrong bits and symbols are counted; constellation points and |H| are returned for the charts."],
    ]
    story.append(booktabs(rows, [W * 0.12, W * 0.88], zebra=True, align_center_from=99))

    story.append(P("5.2 DNN Training Workflow", "h2"))
    steps = [
        ["1. Draw channels", "Rayleigh or", "DeepMIMO users"],
        ["2. Random SNR", "uniform 0–30 dB"],
        ["3. Transmit pilots", "through channel", "+ noise"],
        ["4. LS estimate", "input features", "(512 values)"],
        ["5. True H", "target values", "(512 values)"],
        ["6. Split 70/15/15", "by channel seed", "or user"],
        ["7. Train", "Adam, MSE loss,", "LR scheduler"],
        ["8. Save best", "lowest validation", "loss checkpoint"],
    ]
    story.append(diagram_block(flow_diagram(steps, W, fill=C_API),
                               "Figure 3: How the DNN learns (estimation/trainer.py)."))
    story.append(P(
        "Every synthetic sample uses its own freshly drawn channel, so splitting the samples 70/15/15 means "
        "the test set holds channels the network has never seen. With DeepMIMO the <b>users</b> are split "
        "first, so no user's channel appears in two sets. The input is only what a real receiver has (the "
        "noisy LS estimate); the true channel is used only as the answer during training."))

    story.append(P("5.3 Dashboard Request Workflow", "h2"))
    steps = [
        ["User clicks", "“Run Simulation”"],
        ["client.ts", "POST /api/simulation/run", "with settings (JSON)"],
        ["Vite proxy", "forwards to", "port 8000"],
        ["FastAPI", "validates with", "Pydantic schema"],
        ["Pipeline", "runs steps 1–12", "(Figure 2)"],
        ["SQLite", "saves the run", "to history"],
        ["JSON response", "metrics + samples"],
        ["React page", "updates cards", "and charts"],
    ]
    story.append(diagram_block(flow_diagram(steps, W, fill=C_FRONT),
                               "Figure 4: What happens between a click and the charts updating."))
    story.append(P(
        "Training works the same way but runs in a background thread: the page starts a job with "
        f"{mono('POST /api/model/train')} and then polls {mono('GET /api/model/train/status')} every second "
        "to draw the live loss curve."))

    story.append(P("5.4 Experiment Workflow", "h2"))
    story.append(P(
        f"{mono('python -m neuromimo.evaluation.run_experiments_cli')} runs five experiments, and every "
        "estimator sees identical channels and noise (the random generator is reset with the same seed):"))
    story += bullets([
        "<b>SNR sweep:</b> NMSE and BER at 0, 5, …, 30 dB.",
        "<b>Channel comparison:</b> flat AWGN versus Rayleigh multipath.",
        "<b>Generalisation:</b> different delay-profile decay values and a longer 6-tap channel.",
        "<b>Pilot density:</b> pilot spacing 4, 8 and 16.",
        "<b>Inference time:</b> 100 timed runs per estimator after 10 warm-up runs.",
    ])
    story.append(P(
        f"Results go to {mono('backend/results/')} as JSON, CSV and 300 DPI PNG figures, which the "
        "Performance Comparison page and these PDFs read."))

    story.append(P("5.5 DeepMIMO Workflow", "h2"))
    steps = [
        ["DeepMIMO", "generate OFDM", "channels"],
        ["np.save", "channels.npy", "(users, rx, tx, sc)"],
        ["Loader", "2×2, 64 subcarriers,", "drop empty, normalise"],
        ["Benchmark or train", "deepmimo_cli /", "train_cli --deepmimo"],
    ]
    story.append(diagram_block(flow_diagram(steps, W, fill=C_STORE),
                               "Figure 5: Using realistic ray-traced channels."))


def dashboard_and_api(story, W):
    story.append(PageBreak())
    story.append(section("6. Dashboard Pages and API"))
    rows = [["Page", "What you can do there"]]
    rows += [
        ["Overview Dashboard", "Project summary, system status cards, pipeline steps and the research figures."],
        ["MIMO-OFDM Simulator", "Choose antennas, modulation, channel, SNR, pilots and estimator; run one transmission."],
        ["Channel Estimation Lab", "Run LS, LMMSE and DNN head to head on the same channel; compare true vs predicted H."],
        ["ML Model Training", "Set epochs, batch size, learning rate and SNR range; train and watch the loss curve."],
        ["Performance Comparison", "NMSE and BER waterfalls, latency, a metrics table and summary cards computed from data."],
        ["Signal Visualization", "IQ constellation, channel frequency response, power delay profile and subcarrier grid."],
        ["Experiment History", "Search and filter saved runs and export them to CSV."],
        ["About & Methodology", "Theory, equations and how the evaluation was done."],
    ]
    story.append(booktabs(rows, [W * 0.30, W * 0.70], zebra=True, align_center_from=99))
    story.append(P("The palette button in the top bar switches between the Neon, Nebula, Matrix and Solar dark "
                   "themes.", "box_note"))

    story.append(P("REST API Endpoints", "h2"))
    rows = [["Method", "Endpoint", "Purpose"]]
    rows += [
        ["GET", "/api/health", "Backend status, device and library versions"],
        ["GET", "/api/config", "Supported settings and defaults"],
        ["POST", "/api/simulation/run", "Run one end-to-end transmission"],
        ["POST", "/api/estimation/compare", "Compare several estimators on one channel"],
        ["POST", "/api/model/train", "Train the DNN (now or in the background)"],
        ["GET", "/api/model/status", "Is a trained model available, and how big is it"],
        ["GET", "/api/model/train/status", "Live training progress"],
        ["POST", "/api/model/predict", "Run the DNN on a channel"],
        ["GET", "/api/experiments", "List saved runs"],
        ["GET", "/api/experiments/{id}", "One saved run"],
        ["GET", "/api/experiments/{id}/plots", "List result figures"],
        ["GET", "/api/experiments/{id}/plots/{name}", "Download one figure"],
        ["GET", "/api/experiments/benchmark/snr-sweep", "The pre-computed SNR sweep results"],
    ]
    rows = [rows[0]] + [[m, Paragraph(mono(e), S["cell"]), p] for m, e, p in rows[1:]]
    story.append(booktabs(rows, [W * 0.11, W * 0.47, W * 0.42], zebra=True, align_center_from=99))


def results(story, W):
    sweep = load("snr_sweep_results.json")
    infer = load("inference_time_results.json")
    rec = {a: by_snr(r) for a, r in sweep["records"].items()}
    lat = infer["results"]

    story.append(PageBreak())
    story.append(section("7. What the Results Show"))
    story.append(P(
        f"Rayleigh channel, QPSK, {sweep['num_trials_per_snr']} trials per SNR point. Numbers are read from "
        f"{mono('backend/results/')}."))
    rows = [["SNR", "LS NMSE", "LMMSE NMSE", "DNN NMSE", "LS BER", "DNN BER"]]
    for snr in (0.0, 10.0, 20.0, 30.0):
        rows.append([f"{snr:.0f} dB", fmt_nmse(rec["LS"][snr]), fmt_nmse(rec["MMSE"][snr]),
                     fmt_nmse(rec["DNN"][snr]), fmt_ber(rec["LS"][snr]), fmt_ber(rec["DNN"][snr])])
    story.append(booktabs(rows, [W * 0.10, W * 0.15, W * 0.16, W * 0.15, W * 0.22, W * 0.22], zebra=True))
    story.append(Spacer(1, 6))
    story.append(figure("nmse_vs_snr.png", "Figure 6: Channel estimation error versus SNR.", W * 0.7))
    story += bullets([
        f"<b>Noisy conditions (0–10 dB):</b> LMMSE is best, as theory predicts ({fmt_nmse(rec['MMSE'][0.0])} "
        f"at 0 dB). The DNN ({fmt_nmse(rec['DNN'][0.0])}) is slightly better than LS "
        f"({fmt_nmse(rec['LS'][0.0])}) and close to LMMSE, without needing channel statistics.",
        f"<b>Clean conditions (20–30 dB):</b> the DNN levels off near {fmt_nmse(rec['DNN'][30.0])} while "
        f"LS keeps improving to {fmt_nmse(rec['LS'][30.0])}. One small network trained on the whole 0–30 "
        "dB range cannot match LS when the noise is tiny.",
        f"<b>Speed:</b> all estimators take under 1 ms per frame on a CPU (LS {lat['LS']['mean_ms']:.2f} ms, "
        f"LMMSE {lat['MMSE']['mean_ms']:.2f} ms, DNN {lat['DNN']['mean_ms']:.2f} ms).",
        "<b>Pilots matter:</b> with 2 pilots per antenna (spacing 16) every estimator fails, because a 4-tap "
        "channel needs at least 4 pilots to be resolved.",
    ])


def tech_and_run(story, W):
    story.append(PageBreak())
    story.append(section("8. Technology Stack"))
    rows = [["Layer", "Technology", "Used for"]]
    rows += [
        ["Signal processing", "Python, NumPy, SciPy", "Modulation, FFT, channels, estimators, statistics"],
        ["Machine learning", "PyTorch", "The residual DNN, training and inference"],
        ["Figures", "Matplotlib", "300 DPI result figures"],
        ["Backend", "FastAPI, Uvicorn, Pydantic", "REST API, validation, background training"],
        ["Storage", "SQLite", "History of simulations and training runs"],
        ["Frontend", "React 19, TypeScript, Vite", "The dashboard and its build tooling"],
        ["Styling and charts", "Tailwind CSS, Recharts, lucide-react", "Themes, interactive charts, icons"],
        ["Testing", "pytest, FastAPI TestClient, oxlint", "80 backend tests and frontend linting"],
        ["Documents", "ReportLab", "The project PDFs in docs/"],
    ]
    story.append(booktabs(rows, [W * 0.22, W * 0.35, W * 0.43], zebra=True, align_center_from=99))

    story.append(section("9. How to Run It"))
    story.append(P("Backend (first terminal, from the project folder):", "h2"))
    story.append(code_box("""
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
python -m pytest backend/tests -q
uvicorn neuromimo.api.main:app --app-dir backend --port 8000
""", W))
    story.append(P("Frontend (second terminal):", "h2"))
    story.append(code_box("""
cd frontend
npm ci
npm run dev                        # then open http://localhost:5173
""", W))
    story.append(P("Useful commands (from backend/):", "h2"))
    story.append(code_box("""
# Train the DNN
python -m neuromimo.estimation.train_cli --samples 500 --epochs 15
# Reproduce every experiment and figure
python -m neuromimo.evaluation.run_experiments_cli --trials 15
# Benchmark on DeepMIMO channels
python -m neuromimo.evaluation.deepmimo_cli channels.npy
""", W))


def build():
    doc = ExplainerTemplate(OUTPUT, title="NeuroMIMO — The Project Explained", author="NeuroMIMO",
                            subject="Abbreviations, concepts, architecture and workflows")
    W = doc.width
    story = [
        Spacer(1, 50 * mm),
        P("NeuroMIMO", "title"),
        Spacer(1, 6),
        P("T<font size='12'>HE</font> P<font size='12'>ROJECT</font> E<font size='12'>XPLAINED</font>", "subtitle"),
        Spacer(1, 22 * mm),
        P("Abbreviations • Key Concepts • Architecture • Workflows • Results", "tag"),
        Spacer(1, 22 * mm),
        P("A plain-English guide to the AI-enhanced 2×2 MIMO-OFDM channel estimation platform: what it "
          "does, how it is built, and how data flows through it.", "abstract"),
        Spacer(1, 80 * mm),
        P(date.today().strftime("%B %d, %Y").replace(" 0", " "), "date"),
        NextPageTemplate("toc"),
        PageBreak(),
    ]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc0", fontName=BODY, fontSize=10.5, leading=15,
                                      textColor=LINK_BLUE, leftIndent=10)]
    story += [Spacer(1, 25 * mm), P("Contents", "toc_title"), toc, NextPageTemplate("main"), PageBreak()]

    overview(story, W)
    abbreviations(story, W)
    concepts(story, W)
    architecture(story, W)
    workflows(story, W)
    dashboard_and_api(story, W)
    results(story, W)
    tech_and_run(story, W)

    doc.multiBuild(story)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
