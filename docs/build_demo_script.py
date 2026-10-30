"""Builds docs/NeuroMIMO_Demo_Day_Script.pdf: a short, printable script for the
live demo - setup checklist, then for each dashboard page what to click, what
you will see and what to say, plus do/don't rules and quick answers.

The numbers in the click-by-click steps are the exact values the app shows with
its fixed random seed (42). Reuses the layout of build_documentation.py and the
screenshots in docs/screenshots/.

Usage (from the repository root):
    python docs/build_demo_script.py
"""

import os
import sys

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, KeepTogether, NextPageTemplate, PageBreak, Paragraph, Spacer, Table, TableStyle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_documentation import (  # noqa: E402  (path set up above)
    BODY,
    BOLD,
    ITALIC,
    MONO,
    ROOT,
    RULE_GREY,
    S,
    DocTemplate,
    P,
    booktabs,
    code_box,
)

OUTPUT = os.path.join(ROOT, "docs", "NeuroMIMO_Demo_Day_Script.pdf")
SHOTS = os.path.join(ROOT, "docs", "screenshots")

S["ds_title"] = ParagraphStyle("ds_title", parent=S["title"], fontSize=24, leading=29)
S["ds_text"] = ParagraphStyle("ds_text", parent=S["body"], fontSize=9.6, leading=12.8, spaceAfter=0, alignment=0)
S["ds_say"] = ParagraphStyle("ds_say", parent=S["ds_text"], fontName=ITALIC)
S["ds_label"] = ParagraphStyle("ds_label", parent=S["ds_text"], fontName=BOLD, textColor=colors.HexColor("#1F4E9E"))
S["ds_head"] = ParagraphStyle("ds_head", parent=S["h1"], fontSize=13.5, leading=17, spaceBefore=6, spaceAfter=4)
S["ds_check"] = ParagraphStyle("ds_check", parent=S["ds_text"], leftIndent=14, firstLineIndent=-14, spaceAfter=3)

CHECKBOX = "☐"


class ScriptTemplate(DocTemplate):
    def _header(self, canv, doc):
        canv.saveState()
        top = A4[1] - 18 * mm
        canv.setFont(ITALIC, 10.5)
        canv.drawString(self.leftMargin, top, "NeuroMIMO — Demo Day Script")
        canv.setFont(BODY, 10.5)
        canv.drawRightString(A4[0] - self.rightMargin, top, str(doc.page))
        canv.setLineWidth(0.5)
        canv.line(self.leftMargin, top - 4, A4[0] - self.rightMargin, top - 4)
        canv.restoreState()


def checklist(items):
    return [Paragraph(f"<font face='{MONO}'>{CHECKBOX}</font>&nbsp;&nbsp;{item}", S["ds_check"]) for item in items]


def callout(text, W, fill="#EEF3FB", edge="#1F4E9E"):
    t = Table([[Paragraph(text, S["ds_text"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fill)),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor(edge)),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def thumb(name, width):
    path = os.path.join(SHOTS, name + ".jpg")
    with Image.open(path) as im:
        ratio = im.height / im.width
    img = RLImage(path, width=width, height=width * ratio)
    box = Table([[img]], colWidths=[width])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, RULE_GREY),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                             ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return box


def page_block(W, number, page, minutes, shot, do, see, say):
    """One dashboard page: thumbnail on the left, Do / You will see / Say on the right."""
    tw = W * 0.34
    right = []
    right.append(Paragraph("DO", S["ds_label"]))
    right += [Paragraph(f"{i}. {step}", S["ds_text"]) for i, step in enumerate(do, 1)]
    right.append(Spacer(1, 4))
    right.append(Paragraph("YOU WILL SEE", S["ds_label"]))
    right.append(Paragraph(see, S["ds_text"]))
    right.append(Spacer(1, 4))
    right.append(Paragraph("SAY", S["ds_label"]))
    right.append(Paragraph(say, S["ds_say"]))
    body = Table([[thumb(shot, tw), right]], colWidths=[tw + 8, W - tw - 8])
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("LEFTPADDING", (1, 0), (1, 0), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    head = Paragraph(f"Step {number}: {page} <font size='10' color='#5A6472'>({minutes})</font>", S["ds_head"])
    return KeepTogether([head, body, Spacer(1, 8)])


def build():
    doc = ScriptTemplate(OUTPUT, title="NeuroMIMO — Demo Day Script", author="NeuroMIMO",
                         subject="What to do and say on each page during the live demo")
    W = doc.width
    story = [NextPageTemplate("main")]

    # ---------------- Page 1: title + setup checklist ----------------
    story += [
        Paragraph("NeuroMIMO — Demo Day Script", S["ds_title"]),
        P("What to do before the demo, what to click on each page, what you will see, and what to say. "
          "Total demo time: about 10 minutes plus questions.", "abstract"),
        Spacer(1, 8),
        P("A. Setup: 30 minutes before", "h2"),
    ]
    story += checklist([
        "<b>Get the latest code.</b> The SER fix and the DNN-settings fix are on the "
        f"<font face='{MONO}'>claude/hopeful-gauss-589grm</font> branch (run the commands below, or merge "
        "that branch into main first).",
        "<b>Back up the trained model:</b> copy "
        f"<font face='{MONO}'>backend/models/neuromimo_dnn.pt</font> to a safe place.",
        "<b>Start both servers</b> (two terminals, commands below).",
        "Open <b>http://localhost:5173</b>. Check the top bar: green <b>API Connected</b>; the ML card says "
        "<b>Ready</b>, 330,112 parameters.",
        "<b>Warm up</b> (first PyTorch calls are slow): press the 1-click demo, run one simulation, press the "
        "Estimation Lab benchmark <b>twice</b>, open Performance Comparison and Signal Visualization once.",
        "Theme on <b>Neon</b>; browser full screen (F11); zoom 90–100%; close other tabs and notifications.",
        "Laptop charged and plugged in. Backup: the PDFs in <font face='Mono'>docs/</font> and "
        "<font face='Mono'>docs/screenshots/</font> on your phone or a USB drive.",
    ])
    story.append(Spacer(1, 4))
    story.append(code_box("""
# Get the branch with the latest fixes (project folder)
git fetch origin
git checkout claude/hopeful-gauss-589grm
git pull
# Terminal 1
uvicorn neuromimo.api.main:app --app-dir backend --port 8000
# Terminal 2
cd frontend
npm run dev
""", W))
    story.append(Spacer(1, 8))
    story.append(P("B. Opening: 30 seconds", "h2"))
    story.append(callout(
        "“Good morning. My project is <b>NeuroMIMO</b>, AI-enhanced channel estimation for 2×2 "
        "MIMO-OFDM, the physical layer of 4G, 5G and Wi-Fi. A receiver must estimate how the wireless "
        "channel distorts the signal using a few known pilot symbols. I compare three estimators on "
        "identical channels: Least Squares, Linear MMSE and a residual deep neural network, and I built a "
        "web platform to run and explore everything. Let me show you.”", W, fill="#F2F8EF", edge="#2E7D32"))

    # ---------------- Demo flow at a glance ----------------
    story.append(PageBreak())
    story.append(P("C. Demo Flow at a Glance", "h2"))
    rows = [["Step", "Page (left menu)", "Time", "Key message"]]
    rows += [
        ["1", "Overview Dashboard", "1 min", "What the system is; a live result in one click"],
        ["2", "MIMO-OFDM Simulator", "2 min", "Noise matters: 5 dB vs 25 dB"],
        ["3", "Channel Estimation Lab", "2 min", "LS vs LMMSE vs DNN on the same channel"],
        ["4", "Signal Visualization", "1 min", "Fading, echoes and pilots, visually"],
        ["5", "Performance Comparison", "2 min", "The research result over 0–30 dB"],
        ["6", "ML Model Training", "1 min", "How the DNN is trained (show, do not train)"],
        ["7", "Experiment History", "30 s", "Every run is recorded"],
        ["8", "About & Methodology", "30 s", "The theory and equations"],
        ["9", "Theme picker", "15 s", "Finishing touch"],
    ]
    story.append(booktabs(rows, [W * 0.08, W * 0.3, W * 0.1, W * 0.52], zebra=True, align_center_from=99))
    story.append(Spacer(1, 8))

    # ---------------- Page-by-page script ----------------
    story.append(P("D. Page-by-Page Script", "h2"))
    story.append(page_block(W, 1, "Overview Dashboard", "1 min", "02-overview-demo", [
        "Point to the green <b>API Connected</b> badge and the <b>ML Channel Estimator: Ready</b> card.",
        "Read the six pipeline boxes in one breath: bits, OFDM, channel, demodulation, estimation, equaliser.",
        "Press <b>1-Click Interactive Demo (20 dB)</b>.",
        "Scroll down to the two result figures.",
    ], "NMSE <b>−23.68 dB</b>, <b>0 bit errors of 896</b>, and four tight QPSK clusters in the "
       "constellation.",
       "“One click sends a full frame through a random multipath channel at 20 dB. The channel estimate "
       "is accurate to about 0.4%, and every bit is recovered.”"))

    story.append(page_block(W, 2, "MIMO-OFDM Simulator", "2 min", "05-simulator-results", [
        "Show the three panels: transceiver, channel and noise, estimator. Keep <b>2×2</b> and <b>64 "
        "subcarriers</b>.",
        "Set SNR to <b>5 dB</b>, press <b>Run Simulation</b>.",
        "Set SNR to <b>25 dB</b>, run again.",
        "Optional: switch to <b>16QAM</b> at 20 dB and run.",
        "Point to the <b>channel magnitude</b> curve rising and falling.",
    ], "5 dB: NMSE −13.35 dB, BER 0.13 (408 of 3,136 bits), scattered points. 25 dB: NMSE −33.35 dB, "
       "<b>0 bit errors</b>, tight clusters. 16QAM at 20 dB: BER 0.022 (16 points, 4 bits each).",
       "“Less noise means a better channel estimate and fewer errors. The dips in this curve are "
       "frequency-selective fading from the echoes, which is why the channel must be estimated on every "
       "subcarrier.”"))

    story.append(page_block(W, 3, "Channel Estimation Lab", "2 min", "06-estimation-benchmark", [
        "Read the three cards: the formula of LS, LMMSE and the DNN.",
        "Set SNR to <b>0</b>, press <b>Run Head-to-Head Benchmark</b>.",
        "Set SNR to <b>25</b>, run again.",
        "Scroll down, press <b>Simulate & Predict CFR</b>.",
    ], "0 dB: LMMSE <b>−9.35</b>, DNN <b>−8.96</b>, LS <b>−8.50 dB</b>. 25 dB: LS −33.28, "
       "LMMSE −33.25, DNN −25.73 dB. The CFR plot: purple dashed DNN curve on top of the green true "
       "channel.",
       "“All three see exactly the same channel and noise. In heavy noise LMMSE is best because it knows "
       "the channel statistics; the DNN beats LS <i>without</i> them. In clean conditions LS and LMMSE win: "
       "the DNN has an error floor, which is its known limitation.”"))

    story.append(page_block(W, 4, "Signal Visualization", "1 min", "10-visualization-pdp", [
        "Let the page load (charts fill in after a second).",
        "Click <b>Phase</b>, then back to <b>Magnitude</b> on the channel response.",
        "Scroll to the <b>power delay profile</b> and the <b>subcarrier grid</b>.",
    ], "Four taps, strongest first; the 64-tone grid with antenna 0 pilots at 0, 16, 32, 48 and antenna 1 at "
       "8, 24, 40, 56.",
       "“This is the multipath: a direct path and three weaker echoes. The two antennas place pilots on "
       "different subcarriers, so they never interfere and each channel can be measured.”"))

    story.append(page_block(W, 5, "Performance Comparison", "2 min", "11-comparison", [
        "Read the four summary cards (computed from the data).",
        "Trace the NMSE curves from 0 dB to 30 dB; point where the purple DNN curve flattens.",
        "Scroll to the table, then open <b>Publication Figures</b> and click one to enlarge.",
    ], "At 0 dB: LMMSE −9.05, DNN −8.67, LS −8.38 dB. At 30 dB: LS and LMMSE −38.64 dB, DNN "
       "−25.96 dB. 15 trials per SNR point, 105 channels in total.",
       "“This is the main result. The DNN helps most in noisy conditions; at high SNR one small network "
       "trained across the whole range levels off. Every point uses identical channels and has a 95% "
       "confidence interval.”"))

    story.append(page_block(W, 6, "ML Model Training", "1 min", "16-training-curve", [
        "Show the architecture card (Residual MLP, 330,112 parameters) and the hyperparameters.",
        "Show the loss curve and explain it. <b>Do not press Start Training</b> (see the warning below).",
        "Press <b>Run Test Inference</b> to show the saved model works.",
    ], "Training and validation loss falling together over the epochs.",
       "“The network takes the noisy LS estimate and learns only a correction. The final model was "
       "trained on 30,000 simulated channels for 40 epochs; both losses fall together, so it is not "
       "overfitting.”"))

    story.append(page_block(W, 7, "Experiment History", "30 s", "17-history", [
        "Show that the runs you just did are at the top.",
        "Choose an algorithm in the filter, then press <b>Export CSV</b>.",
    ], "Run count, best NMSE, average latency and a searchable table.",
       "“Every run is stored in a SQLite database, so results are traceable and exportable.”"))

    story.append(page_block(W, 8, "About & Methodology", "30 s", "18-about", [
        "Scroll to the three estimator formulas.",
    ], "System model Y = HX + W and the LS, LMMSE and DNN equations.",
       "“LS divides by the pilot, LMMSE adds channel statistics, and the DNN learns the correction from "
       "data.”"))

    story.append(page_block(W, 9, "Theme Picker", "15 s", "19-theme-menu", [
        "Click the palette icon (top right), choose <b>Matrix</b>, then switch back to <b>Neon</b>.",
    ], "The whole interface recolours; chart line colours stay the same.",
       "“A small usability feature; the estimator colours stay consistent everywhere.”"))

    story.append(P("E. Closing: 30 seconds", "h2"))
    story.append(callout(
        "“To summarise: on identical channels and with confidence intervals, a small residual network "
        "beats Least Squares in noisy conditions without needing channel statistics, and stays within a "
        "fraction of a dB of LMMSE, while I also show where it falls short at high SNR. Everything is "
        "reproducible from the command line and covered by 88 automated tests. Thank you; I am happy to take "
        "questions.”", W, fill="#F2F8EF", edge="#2E7D32"))

    # ---------------- Do / Don't + questions + troubleshooting ----------------
    story.append(PageBreak())
    story.append(P("F. Do and Don't", "h2"))
    rows = [["Do", "Don't"]]
    rows += [
        ["Keep <b>2×2</b> and <b>64 subcarriers</b> whenever the DNN is selected.",
         "Pick 128/256 subcarriers or 2×4/4×4 with the DNN: it only supports 2×2, 64 "
         "subcarriers (you will see a message)."],
        ["Use LS or LMMSE if you want to show other FFT sizes.",
         "Show 4×4 as a result: with 4 antennas there are too few pilots per antenna, so NMSE is poor "
         "(about −4 dB)."],
        ["Click the Estimation Lab benchmark twice so the latency is realistic.",
         "Quote the first-click latency; it includes PyTorch start-up."],
        ["Show the training page and explain the loss curve.",
         "Press <b>Start Training</b>: it <b>overwrites the trained model</b> with a weaker quick model. If you "
         "must, restore your backup afterwards and restart the backend."],
        ["Say the numbers on screen out loud (e.g. “−9.35 dB”).", "Say “it works "
                                                                              "well” without a number."],
        ["Admit the DNN's high-SNR floor and explain why.", "Claim the DNN beats everything."],
    ]
    data = [[Paragraph(a, S["ds_text"]), Paragraph(b, S["ds_text"])] for a, b in rows[1:]]
    data.insert(0, [Paragraph("<b>Do</b>", S["ds_text"]), Paragraph("<b>Don't</b>", S["ds_text"])])
    t = Table(data, colWidths=[W * 0.5, W * 0.5])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY), ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE_GREY),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#DFF3E8")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FDECEC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)

    story.append(P("G. Quick Answers to Likely Questions", "h2"))
    qa = [
        ("Is the data real?", "Simulated, so the true channel is known exactly; a DeepMIMO loader reads "
                              "realistic ray-traced channels."),
        ("Why does the DNN lose at high SNR?", "One small network is trained over 0–30 dB; when noise is "
                                               "tiny, its own approximation error dominates. Fix: give it the "
                                               "SNR as input or train per SNR range."),
        ("Why is LMMSE best at low SNR?", "It uses the channel's statistics and the noise level to filter "
                                          "the noise; the DNN gets close without them."),
        ("What is NMSE?", "Estimation error relative to channel power; −20 dB means 1% error."),
        ("How did you avoid overfitting?", "Separate train/validation/test channels; the best-validation "
                                           "checkpoint is kept; both losses fall together."),
        ("Why 4 pilots per antenna?", "The channel has 4 taps; you need at least as many pilots as taps."),
        ("How fast is it?", "LS 0.12 ms, LMMSE 0.40 ms, DNN 0.65 ms per frame on a CPU, inside a 1 ms 5G slot."),
        ("What would you do next?", "SNR-aware DNN, a CNN over time and frequency, Doppler, larger MIMO, "
                                    "and DeepMIMO channels."),
    ]
    rows = [["Question", "Answer"]] + [[q, a] for q, a in qa]
    story.append(booktabs(rows, [W * 0.3, W * 0.7], zebra=True, align_center_from=99))

    story.append(P("H. If Something Goes Wrong", "h2"))
    rows = [["Problem", "Fix"]]
    rows += [
        ["Red “Backend Offline”", "Start Terminal 1 again, then press refresh in the top bar."],
        ["A page shows an error banner", "Read it out; for DNN-settings messages, return to 2×2 and 64 "
                                         "subcarriers."],
        ["First DNN result is slow", "Normal start-up; run it again."],
        ["Model card not Ready", "Copy your backup model back to backend/models/ and restart the backend."],
        ["Laptop or network fails", "Present from the screenshots and the PDFs on your phone or USB drive."],
    ]
    story.append(booktabs(rows, [W * 0.3, W * 0.7], zebra=True, align_center_from=99))

    doc.multiBuild(story)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
