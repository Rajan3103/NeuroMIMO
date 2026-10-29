"""Builds docs/NeuroMIMO_Feature_Guide.pdf: every feature of the project with a
screenshot, what it does, how to demo it, what to say, and a likely question.

Screenshots live in docs/screenshots/ (captured from the running app).
Reuses the layout of build_documentation.py; result numbers come from
backend/results/.

Usage (from the repository root):
    python docs/build_feature_guide.py
"""

import os
import sys
from datetime import date

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
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
    code_box,
    fmt_nmse,
    load,
    mono,
    section,
)

OUTPUT = os.path.join(ROOT, "docs", "NeuroMIMO_Feature_Guide.pdf")
SHOTS = os.path.join(ROOT, "docs", "screenshots")

S["fg_label"] = ParagraphStyle("fg_label", parent=S["body"], fontName=BOLD, fontSize=9.6, leading=12.5,
                               spaceAfter=0, textColor=colors.HexColor("#1F4E9E"))
S["fg_text"] = ParagraphStyle("fg_text", parent=S["body"], fontSize=9.8, leading=13.2, spaceAfter=0)
S["fg_say"] = ParagraphStyle("fg_say", parent=S["fg_text"], fontName=ITALIC)


class GuideTemplate(DocTemplate):
    def _header(self, canv, doc):
        canv.saveState()
        top = A4[1] - 18 * mm
        canv.setFont(ITALIC, 10.5)
        canv.drawString(self.leftMargin, top, "NeuroMIMO — Feature Guide for the Demo")
        canv.setFont(BODY, 10.5)
        canv.drawRightString(A4[0] - self.rightMargin, top, str(doc.page - 1))
        canv.setLineWidth(0.5)
        canv.line(self.leftMargin, top - 4, A4[0] - self.rightMargin, top - 4)
        canv.restoreState()


def screenshot(name, caption, W):
    path = os.path.join(SHOTS, name + ".jpg")
    with Image.open(path) as im:
        ratio = im.height / im.width
    img = RLImage(path, width=W, height=W * ratio)
    frame = Table([[img]], colWidths=[W])
    frame.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, RULE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return KeepTogether([frame, P(caption, "caption")])


def info_card(W, rows):
    """Labelled rows: What it is / What you see / How to demo / What to say / If asked."""
    data = []
    for label, content in rows:
        style = S["fg_say"] if label == "What to say" else S["fg_text"]
        if isinstance(content, list):
            cell = [Paragraph(f"{i}. {step}", style) for i, step in enumerate(content, 1)]
        else:
            cell = Paragraph(content, style)
        data.append([Paragraph(label, S["fg_label"]), cell])
    t = Table(data, colWidths=[W * 0.2, W * 0.8])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F4F6FA")),
    ]
    for i, (label, _) in enumerate(rows):
        if label == "What to say":
            style.append(("BACKGROUND", (1, i), (1, i), colors.HexColor("#F2F8EF")))
        if label == "If asked":
            style.append(("BACKGROUND", (1, i), (1, i), colors.HexColor("#FFF6E5")))
    t.setStyle(TableStyle(style))
    return t


def callout(text, W, fill="#EEF3FB", edge="#1F4E9E"):
    t = Table([[Paragraph(text, S["fg_text"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fill)),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor(edge)),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


# -----------------------------------------------------------------------------
# Sections
# -----------------------------------------------------------------------------
def intro(story, W):
    story.append(section("1. Demo Plan"))
    story.append(P(
        "NeuroMIMO has <b>9 features in the web dashboard</b> and <b>6 features behind the scenes</b>. This "
        "guide explains each one with a real screenshot, the steps to show it, a sentence to say, and the "
        "question a faculty member is most likely to ask. A complete demo takes about 10–12 minutes."))
    rows = [["Order", "Feature", "Time", "Main point"]]
    rows += [
        ["1", "Overview Dashboard + 1-click demo", "1 min", "What the project is; a live result in one click"],
        ["2", "MIMO-OFDM Simulator", "2 min", "Any setting, full transmit–channel–receive chain"],
        ["3", "Channel Estimation Lab", "2 min", "LS vs LMMSE vs DNN on the same channel"],
        ["4", "Signal Visualization", "1 min", "Constellation, channel response, pilots"],
        ["5", "Performance Comparison", "2 min", "The research results over 0–30 dB"],
        ["6", "ML Model Training", "1 min", "Train the DNN live and watch the loss"],
        ["7", "Experiment History", "30 s", "Every run is saved and exportable"],
        ["8", "About & Methodology", "30 s", "Theory and equations"],
        ["9", "Theme picker", "15 s", "Finishing touch"],
    ]
    story.append(booktabs(rows, [W * 0.09, W * 0.36, W * 0.1, W * 0.45], zebra=True, align_center_from=99))

    story.append(P("Before the Faculty Arrives", "h2"))
    story.append(code_box("""
# Terminal 1 (project folder)
uvicorn neuromimo.api.main:app --app-dir backend --port 8000
# Terminal 2
cd frontend
npm run dev                    # open http://localhost:5173
""", W))
    story += bullets([
        "Check the top bar shows a green <b>API Connected</b> badge and the model card says <b>Ready</b>.",
        "<b>Warm up:</b> run one simulation and run the Estimation Lab benchmark <b>twice</b>. The first "
        "PyTorch call after a start or a training run is slow; the second shows the real latency.",
        "Set the browser zoom so the charts are easy to read from a distance (90–100%).",
        "Keep the PDFs in <font face='Mono'>docs/</font> and this guide's screenshots open as a backup in case "
        "the laptop or network fails.",
    ])


def feature(story, W, number, title, shots, rows):
    story.append(PageBreak())
    story.append(section(f"{number}. {title}"))
    story.append(screenshot(shots[0][0], shots[0][1], W))
    story.append(Spacer(1, 4))
    story.append(info_card(W, rows))
    for name, caption in shots[1:]:
        story.append(Spacer(1, 8))
        story.append(screenshot(name, caption, W))


def ui_features(story, W, rec, lat):
    feature(story, W, 2, "Overview Dashboard and 1-Click Demo", [
        ("01-overview", "The landing page: project summary, system cards and the transceiver pipeline."),
        ("02-overview-demo", "After pressing “1-Click Interactive Demo (20 dB)”: a live result with "
                             "NMSE, BER, bit errors and the constellation."),
        ("03-overview-results", "Further down: the research figures with their key takeaway."),
    ], [
        ("What it is", "The home page. It explains the project and shows the system's live status: 2×2 "
                       "MIMO, QPSK/16-QAM, 64-FFT with 16-sample CP, and whether the trained DNN is ready."),
        ("What you see", "Four status cards, the six-step transceiver pipeline (bits → OFDM → channel "
                         "→ demodulation → estimation → equalisation), and the main result figures."),
        ("How to demo", ["Point to the green API Connected badge and the model card (330,112 parameters).",
                         "Walk through the six pipeline boxes in one sentence each.",
                         "Press <b>1-Click Interactive Demo (20 dB)</b> and read out the NMSE and bit errors.",
                         "Scroll down to the NMSE and BER figures."]),
        ("What to say", "“This platform simulates a complete 2×2 MIMO-OFDM link and compares three "
                        "channel estimators. One click runs a full transmission at 20 dB and shows the "
                        "estimation error and the recovered constellation.”"),
        ("If asked", "<b>Is this real radio data?</b> No, it is a simulation, which lets us know the true "
                     "channel exactly. Realistic ray-traced channels can be loaded with the DeepMIMO loader."),
    ])

    feature(story, W, 3, "MIMO-OFDM Simulator", [
        ("04-simulator-config", "Configuration: transceiver parameters, channel and noise, and the estimator."),
        ("05-simulator-results", "Results of one run at 20 dB with LS: NMSE, BER, SER, constellation and "
                                 "channel magnitude response."),
    ], [
        ("What it is", "A full single transmission with settings you choose. It runs the 12-step chain: bits, "
                       "modulation, pilots, IFFT + CP, channel, noise, FFT, pilot extraction, estimation, "
                       "equalisation, demodulation and metrics."),
        ("What you see", "Three setting panels and, after running, four metric cards (NMSE, BER, SER, "
                         "estimator), the IQ constellation and the channel's magnitude across 64 subcarriers."),
        ("How to demo", ["Keep 2×2, QPSK, 64 subcarriers, Rayleigh; set SNR to <b>5 dB</b> and press "
                         "<b>Run Simulation</b>: the constellation is scattered.",
                         "Set SNR to <b>25 dB</b> and run again: the four QPSK clusters become tight and BER falls.",
                         "Switch the estimator to <b>Linear MMSE</b> or <b>PyTorch Residual Net</b> and compare.",
                         "Point to the channel magnitude plot: it rises and falls across subcarriers."]),
        ("What to say", "“Each run sends 3,136 bits through a random 4-tap Rayleigh channel. The "
                        "dips in this curve are frequency-selective fading, which is why the receiver must "
                        "estimate the channel on every subcarrier.”"),
        ("If asked", "<b>What is SER?</b> Symbol error rate: the fraction of QPSK symbols with at least one "
                     "wrong bit. With 2 bits per symbol it is roughly twice the BER at low error rates."),
    ])

    feature(story, W, 4, "Channel Estimation Lab", [
        ("06-estimation-benchmark", "Head-to-head benchmark at 15 dB over 10 channel realisations."),
        ("08-estimation-cfr", "“Simulate & Predict CFR”: the true channel (green) and the DNN's "
                              "estimate (purple dashed) across all 64 subcarriers."),
    ], [
        ("What it is", "The core comparison. LS, LMMSE and the DNN estimate <b>the same</b> channel from "
                       "<b>the same</b> noisy pilots, so differences come only from the estimators."),
        ("What you see", "Cards with each estimator's formula, advantages and trade-offs; a results table "
                         "(NMSE, BER, SER, latency); bar charts of NMSE and latency; and a live plot of the true "
                         "versus DNN-predicted channel."),
        ("How to demo", ["Set SNR to <b>0</b> and press <b>Run Head-to-Head Benchmark</b>: LMMSE is best "
                         "(\u22129.35 dB), then the DNN (\u22128.96 dB), then LS (\u22128.50 dB).",
                         "Set SNR to <b>25</b> and run again: LS (\u221233.28 dB) and LMMSE (\u221233.25 dB) now "
                         "beat the DNN (\u221225.73 dB). The seed is fixed, so you will see exactly these numbers.",
                         "Press <b>Simulate & Predict CFR</b> and show how closely the dashed DNN curve follows "
                         "the true channel."]),
        ("What to say", "“At low SNR LMMSE is best because it uses channel statistics; the DNN beats LS "
                        "without those statistics. At high SNR the DNN levels off, which is its known "
                        "limitation.”"),
        ("If asked", "<b>Why is the DNN slower?</b> It runs a 330k-parameter network. This page shows about "
                     "1.5\u20132 ms per frame because it includes Python and web-request overhead; the dedicated "
                     f"timing test, which measures only the network after warm-up, gives {lat['DNN']['mean_ms']:.2f} "
                     "ms, inside a 1 ms 5G slot. The first click after a start is slower because PyTorch "
                     "initialises."),
    ])

    feature(story, W, 5, "Signal Visualization", [
        ("09-visualization", "Metric cards, IQ constellation and channel frequency response at 20 dB with the DNN."),
        ("10-visualization-pdp", "Power delay profile of the 4 channel taps and the 64-subcarrier pilot grid."),
    ], [
        ("What it is", "A visual tour of the physical layer for one transmission, with your choice of SNR, "
                       "modulation, channel model and estimator."),
        ("What you see", "IQ constellation (transmitted vs equalised), channel magnitude or phase per "
                         "subcarrier, the multipath power delay profile (strongest tap first), and the "
                         "subcarrier grid showing each antenna's pilots."),
        ("How to demo", ["Move the SNR slider and press <b>Update Visualizations</b>.",
                         "Switch <b>Magnitude</b>/<b>Phase</b> on the channel response.",
                         "Show the pilot grid: antenna 0 uses 0, 16, 32, 48 and antenna 1 uses 8, 24, 40, 56."]),
        ("What to say", "“The delay profile shows the direct path and three weaker echoes. The pilot grid "
                        "shows the two antennas' pilots never collide, so each channel can be measured "
                        "separately.”"),
        ("If asked", "<b>Why only 4 pilots per antenna?</b> The channel has 4 taps, and you need at least as "
                     "many pilots as taps to reconstruct it. With 2 pilots every estimator fails."),
    ])

    feature(story, W, 6, "Performance Comparison", [
        ("11-comparison", "Summary cards computed from the data, and NMSE/BER waterfall curves over 0–30 dB."),
        ("12-comparison-table", "Latency chart and the full benchmark table."),
        ("13-comparison-figures", "The “Publication Figures” tab with the six 300 DPI figures."),
    ], [
        ("What it is", "The research results: every estimator over 0–30 dB SNR with 15 Monte Carlo trials "
                       "per point (105 channel realisations), from the saved benchmark files."),
        ("What you see", "Four summary cards (DNN vs LS, DNN vs LMMSE, latency, SNR range) calculated from the "
                         "data, NMSE and BER curves, a latency chart, a table, and the publication figures."),
        ("How to demo", ["Read the curves left to right: noisy (0 dB) to clean (30 dB).",
                         "Point to where the purple DNN curve flattens around 20 dB.",
                         "Optionally press <b>Run Quick Sweep</b> to recompute live (takes a few seconds).",
                         "Open <b>Publication Figures</b> and click one to enlarge it."]),
        ("What to say", f"“At 0 dB LMMSE gives {fmt_nmse(rec['MMSE'][0.0])}, the DNN "
                        f"{fmt_nmse(rec['DNN'][0.0])} and LS {fmt_nmse(rec['LS'][0.0])}. At 30 dB LS and "
                        f"LMMSE reach {fmt_nmse(rec['LS'][30.0])} while the DNN levels off near −25 dB "
                        "because one small network is trained across the whole SNR range.”"),
        ("If asked", "<b>Are these numbers reliable?</b> Every estimator sees identical channels and noise "
                     "(same random seed), each BER point has a 95% Wilson confidence interval, and the "
                     "results are reproducible from the command line."),
    ])

    feature(story, W, 7, "ML Model Training", [
        ("15-training-done", "Model studio: architecture, 330,112 parameters, device and job state."),
        ("16-training-curve", "Live loss curve: training and validation loss falling over 20 epochs."),
    ], [
        ("What it is", "Trains the residual DNN from the browser. It generates a fresh simulated dataset, "
                       "splits it 80/20, trains with Adam on an MSE loss in a background thread, and saves "
                       "the best checkpoint."),
        ("What you see", "Architecture and parameter cards, hyperparameter inputs (epochs, batch size, "
                         "learning rate, number of channels, SNR range), the live loss curve, and a checkpoint "
                         "panel with <b>Run Test Inference</b>."),
        ("How to demo", ["Show the hyperparameters; do <b>not</b> start a long run during the demo.",
                         "If you have time, set epochs to 5 and press <b>Start Training</b>: the curve updates "
                         "every second.",
                         "Press <b>Run Test Inference</b> to check the saved model works."]),
        ("What to say", "“The network learns only a correction to the LS estimate. Training and "
                        "validation loss fall together, which shows it is learning without overfitting.”"),
        ("If asked", "<b>Important:</b> training from this page <b>replaces</b> the saved model. The project's "
                     "model was trained with 30,000 channels for 40 epochs from the command line; a short "
                     "browser run gives a weaker model. Keep a copy of "
                     "<font face='Mono'>backend/models/neuromimo_dnn.pt</font> before the demo, or skip "
                     "pressing Start Training."),
    ])

    feature(story, W, 8, "Experiment History", [
        ("17-history", "Every simulation and benchmark saved in SQLite, with search, filters and CSV export."),
    ], [
        ("What it is", "An audit log. Each run from the dashboard is stored in a SQLite database with its "
                       "settings and results."),
        ("What you see", "Totals (number of runs, best NMSE, average latency), a searchable table, an "
                         "algorithm filter, and <b>Export CSV</b>."),
        ("How to demo", ["Show that the runs you just made appear at the top.",
                         "Filter by algorithm, then press <b>Export CSV</b>."]),
        ("What to say", "“Every experiment is recorded, so results can be traced and exported for the "
                        "report.”"),
        ("If asked", "<b>Where is the data stored?</b> In <font face='Mono'>backend/data/experiments.db</font>, "
                     "a SQLite file created automatically."),
    ])

    feature(story, W, 9, "About & Methodology", [
        ("18-about", "Theory, equations and the evaluation method."),
    ], [
        ("What it is", "The theory page: the system model, the LS, LMMSE and DNN formulas, MIMO equalisation, "
                       "and the statistics used (Wilson intervals and the rule of three)."),
        ("What you see", "Summary cards, equation blocks and a comparison table of the three estimators."),
        ("How to demo", ["Scroll to the three estimator formulas and explain each in one line."]),
        ("What to say", "“LS divides by the pilot, LMMSE adds channel statistics, and the DNN learns the "
                        "correction from data.”"),
        ("If asked", "<b>What is the rule of three?</b> If no errors are seen in N bits, the true error rate "
                     "is below 3/N with 95% confidence, so we never claim a BER of zero."),
    ])

    feature(story, W, 10, "Colour Theme Picker", [
        ("19-theme-menu", "The palette button opens four dark themes."),
        ("20-theme-matrix", "The Performance Comparison page in the Matrix theme."),
    ], [
        ("What it is", "Four dark colour themes (Neon, Nebula, Matrix, Solar), chosen from the palette button "
                       "and remembered by the browser."),
        ("What you see", "A menu with colour swatches; the whole app recolours instantly. Chart line colours "
                         "stay fixed so each estimator keeps its colour."),
        ("How to demo", ["Click the palette icon and pick another theme, then switch back."]),
        ("What to say", "“A small usability feature: the interface is themeable, and the estimator "
                        "colours stay consistent across themes and figures.”"),
        ("If asked", "<b>How does it work?</b> Colours come from CSS variables; switching the theme changes "
                     "the variables, so no page code changes."),
    ])


def backend_features(story, W, rec):
    story.append(PageBreak())
    story.append(section("11. Features Behind the Scenes"))
    story.append(P("These have no page of their own, but they make the project complete. Mention them "
                   "briefly or show them in a terminal if asked."))
    items = [
        ("REST API with interactive docs",
         f"13 endpoints (FastAPI) power the dashboard. With the backend running, open "
         f"{mono('http://127.0.0.1:8000/docs')} to see and try every endpoint in the browser (needs internet "
         "for the docs page styling)."),
        ("Reproducible experiments",
         f"{mono('python -m neuromimo.evaluation.run_experiments_cli --trials 15')} reruns all five "
         "experiments (SNR sweep, AWGN vs Rayleigh, generalisation, pilot density, timing) and regenerates the "
         "JSON, CSV and 300 DPI figures in about 10 seconds."),
        ("Command-line training",
         f"{mono('python -m neuromimo.estimation.train_cli --samples 30000 --epochs 40 --batch-size 128 --lr 0.001')} "
         "trains the project's model and reports the held-out test NMSE."),
        ("DeepMIMO loader",
         f"Loads realistic ray-traced channels: {mono('python -m neuromimo.evaluation.deepmimo_cli channels.npy')} "
         "benchmarks all estimators on them, and train_cli --deepmimo trains on them with a by-user split."),
        ("Automated tests",
         f"85 tests ({mono('python -m pytest backend/tests -q')}) check the modulation, OFDM, channels, "
         "estimators, metrics, API, DeepMIMO loader and that LMMSE beats LS at low SNR."),
        ("Documentation",
         "Generated PDFs in docs/: project documentation, problem–solution–working, explainer with "
         "abbreviations, research pack with literature survey, review notes, and this feature guide."),
    ]
    for title, text in items:
        story.append(KeepTogether([P(title, "h2"), P(text)]))

    story.append(P("Feature Summary", "h2"))
    rows = [["Feature", "Where", "What it proves"]]
    rows += [
        ["Overview + 1-click demo", "Dashboard", "The system works end to end"],
        ["Simulator", "Dashboard", "The full physical layer is implemented"],
        ["Estimation Lab", "Dashboard", "Fair comparison on identical channels"],
        ["Signal Visualization", "Dashboard", "Understanding of fading, pilots and constellations"],
        ["Performance Comparison", "Dashboard", "The research results over 0–30 dB"],
        ["Model Training", "Dashboard", "The DNN is trained, not just loaded"],
        ["Experiment History", "Dashboard", "Results are recorded and traceable"],
        ["About & Methodology", "Dashboard", "The theory behind the code"],
        ["Theme picker", "Dashboard", "Attention to usability"],
        ["REST API, CLIs, tests", "Terminal", "Reproducibility and software quality"],
        ["DeepMIMO loader", "Terminal", "A path to realistic channels"],
    ]
    story.append(booktabs(rows, [W * 0.32, W * 0.18, W * 0.5], zebra=True, align_center_from=99))


def troubleshooting(story, W):
    story.append(PageBreak())
    story.append(section("12. If Something Goes Wrong"))
    rows = [["Problem", "Fix"]]
    rows += [
        ["Red “Backend Offline” badge", "Start the backend (Terminal 1), then press the refresh button "
                                                   "in the top bar."],
        ["First DNN result is slow", "Normal: PyTorch initialises on first use. Run it again; later runs are fast."],
        ["“Address already in use”", "A server is already running. Close the old terminal, or use "
                                               "another port (e.g. --port 8001, and update vite.config.ts)."],
        ["Charts empty for a moment", "Wait a second after the page loads; the first request fills them."],
        ["Model card not “Ready”", "The model file is missing; restore backend/models/neuromimo_dnn.pt "
                                             "or train with train_cli."],
        ["Laptop or network fails", "Present from this PDF's screenshots and the other PDFs in docs/."],
    ]
    story.append(booktabs(rows, [W * 0.32, W * 0.68], zebra=True, align_center_from=99))
    story.append(Spacer(1, 10))
    story.append(callout(
        "<b>Closing line for the demo:</b> “NeuroMIMO shows, on identical channels and with confidence "
        "intervals, that a small residual network beats Least Squares in noisy conditions without needing "
        "channel statistics, and it also shows honestly where the network falls short. Everything you saw is "
        "reproducible from the command line and covered by automated tests.”", W,
        fill="#EAF5EC", edge="#2E7D32"))


def build():
    sweep = load("snr_sweep_results.json")
    lat = load("inference_time_results.json")["results"]
    rec = {a: by_snr(r) for a, r in sweep["records"].items()}

    doc = GuideTemplate(OUTPUT, title="NeuroMIMO — Feature Guide", author="NeuroMIMO",
                        subject="Every feature with screenshots, demo steps and talking points")
    W = doc.width
    story = [
        Spacer(1, 50 * mm),
        P("NeuroMIMO", "title"),
        Spacer(1, 6),
        P("F<font size='12'>EATURE</font> G<font size='12'>UIDE</font>", "subtitle"),
        Spacer(1, 22 * mm),
        P("Every feature, with screenshots, demo steps and what to say", "tag"),
        Spacer(1, 22 * mm),
        P("Prepared for the faculty demo of the AI-enhanced MIMO-OFDM channel estimation platform.", "abstract"),
        Spacer(1, 80 * mm),
        P(date.today().strftime("%B %d, %Y").replace(" 0", " "), "date"),
        NextPageTemplate("toc"),
        PageBreak(),
    ]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc0", fontName=BODY, fontSize=10.5, leading=15,
                                      textColor=LINK_BLUE, leftIndent=10)]
    story += [Spacer(1, 25 * mm), P("Contents", "toc_title"), toc, NextPageTemplate("main"), PageBreak()]

    intro(story, W)
    ui_features(story, W, rec, lat)
    backend_features(story, W, rec)
    troubleshooting(story, W)

    doc.multiBuild(story)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
