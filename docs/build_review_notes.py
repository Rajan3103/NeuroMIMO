"""Builds docs/NeuroMIMO_Review_Notes.pdf: preparation notes for a project review in
Wireless Mobile Communication (talk script, facts to memorise, theory refresher,
expected questions with answers, and honest answers about known weaknesses).

Reuses the page layout and styles of build_documentation.py. Project numbers are
read from backend/results/.

Usage (from the repository root):
    python docs/build_review_notes.py
"""

import os
import sys
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, NextPageTemplate, PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_documentation import (  # noqa: E402  (path set up above)
    BODY,
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

OUTPUT = os.path.join(ROOT, "docs", "NeuroMIMO_Review_Notes.pdf")

S["qa_q"] = ParagraphStyle("qa_q", parent=S["q"], fontSize=10.2, leading=13.4, spaceBefore=7, spaceAfter=1)
S["qa_a"] = ParagraphStyle("qa_a", parent=S["body"], fontSize=10, leading=13.4, leftIndent=10, spaceAfter=3)
S["say"] = ParagraphStyle("say", parent=S["body"], fontName=ITALIC, fontSize=10, leading=13.6)
S["formula"] = ParagraphStyle("formula", parent=S["eq"], fontSize=10.5, leading=15, spaceBefore=2, spaceAfter=4)


class NotesTemplate(DocTemplate):
    def _header(self, canv, doc):
        canv.saveState()
        top = A4[1] - 18 * mm
        canv.setFont(ITALIC, 10.5)
        canv.drawString(self.leftMargin, top, "NeuroMIMO — Review Preparation Notes")
        canv.setFont(BODY, 10.5)
        canv.drawRightString(A4[0] - self.rightMargin, top, str(doc.page - 1))
        canv.setLineWidth(0.5)
        canv.line(self.leftMargin, top - 4, A4[0] - self.rightMargin, top - 4)
        canv.restoreState()


def callout(text, W, fill="#EEF3FB", edge="#1F4E9E"):
    t = Table([[Paragraph(text, S["box_note"] if "box_note" in S else S["body"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fill)),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor(edge)),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


S["box_note"] = ParagraphStyle("box_note", parent=S["body"], fontSize=9.8, leading=13.2, spaceAfter=0)


def qa(question, answer):
    return KeepTogether([Paragraph(question, S["qa_q"]), Paragraph(answer, S["qa_a"])])


def formula(text):
    return Paragraph(text, S["formula"])


# -----------------------------------------------------------------------------
# Sections
# -----------------------------------------------------------------------------
def how_to_use(story, W):
    story.append(section("1. How to Use These Notes Tonight"))
    story.append(P(
        "Your review is about two things: whether you understand <b>Wireless Mobile Communication</b> "
        "theory, and whether you understand <b>your own project</b> well enough to defend it. These notes "
        "cover both. Suggested plan for tonight (about 2½ hours):"))
    rows = [["Time", "Do this", "Section"]]
    rows += [
        ["20 min", "Practise the 60-second pitch and the 5-minute talk out loud, twice.", "2, 3"],
        ["15 min", "Memorise the project numbers card.", "4"],
        ["45 min", "Read the theory refresher; write each formula once by hand.", "5"],
        ["40 min", "Cover the answers and test yourself on the expected questions.", "6"],
        ["15 min", "Read the weaknesses section carefully; these are the hardest questions.", "7"],
        ["15 min", "Check the demo works and pack the backups.", "8"],
    ]
    story.append(booktabs(rows, [W * 0.13, W * 0.72, W * 0.15], zebra=True, align_center_from=2))
    story.append(Spacer(1, 6))
    story.append(callout(
        "<b>Golden rules for the review.</b> (1) Answer the question asked, then stop. (2) Use your own "
        "numbers: “at 0 dB the DNN gives −8.7 dB NMSE” sounds far stronger than "
        "“it works well”. (3) If you do not know, say so and say how you would find out; never "
        "invent. (4) Admit weaknesses before the professor finds them; it shows you understand your work.",
        W))


def pitch(story, W):
    story.append(section("2. Your 60-Second Pitch"))
    story.append(P("Learn this almost word for word. It is the answer to “Tell me about your project.”"))
    story.append(callout(
        "“My project, NeuroMIMO, studies <b>channel estimation</b> in a <b>2×2 MIMO-OFDM</b> "
        "system, the same physical-layer technology used in 4G, 5G and Wi-Fi. The receiver must know how "
        "the wireless channel distorts the signal, and it learns this from known <b>pilot</b> symbols. "
        "I compare three estimators on identical channels: <b>Least Squares</b>, <b>Linear MMSE</b>, and "
        "a <b>residual deep neural network</b> in PyTorch that refines the LS estimate. I simulate "
        "Rayleigh multipath fading over 0 to 30 dB SNR and measure NMSE, bit error rate with confidence "
        "intervals, and speed. The DNN slightly beats LS at low SNR and comes close to LMMSE without "
        "needing channel statistics, but it hits an error floor around −25 dB at high SNR, which I analyse. Everything runs through a "
        "FastAPI backend and a React dashboard, so results are reproducible and interactive.”",
        W, fill="#F2F8EF", edge="#2E7D32"))


def talk(story, W):
    story.append(section("3. Five-Minute Review Talk"))
    story.append(P("One idea per minute. Show the dashboard or the PDF figures while you speak."))
    parts = [
        ("Minute 1 — Problem",
         "Wireless signals reach the receiver through many reflected paths (multipath), so each frequency "
         "is attenuated and rotated differently, and noise is added. In MIMO-OFDM the receiver must estimate "
         "this channel to separate the two streams and recover the data. Classical LS is simple but noisy; "
         "LMMSE is better but needs channel statistics and a matrix inverse. Can a neural network do better?"),
        ("Minute 2 — System model",
         "2 transmit and 2 receive antennas, 64 subcarriers, 16-sample cyclic prefix, 14 OFDM symbols per "
         "frame, QPSK. Comb pilots: antenna 0 on subcarriers 0, 16, 32, 48 and antenna 1 on 8, 24, 40, 56, so "
         "they never overlap. Channel: 4-tap Rayleigh with an exponential power delay profile, plus AWGN."),
        ("Minute 3 — Estimators",
         "LS divides the received pilot by the known pilot and interpolates with a DFT method. LMMSE applies "
         "a Wiener filter using the channel correlation. The DNN is a residual MLP, 512→256→128"
         "→256→512, 330,112 parameters: it takes the LS estimate and learns only the correction. "
         "Training data are split by channel so the test channels are never seen."),
        ("Minute 4 — Results",
         "Show the NMSE-vs-SNR figure. At 0 dB LMMSE is best (−9.1 dB), then the DNN (−8.7 dB) and LS (−8.4 dB). Above about 15 dB the DNN "
         "levels off near −25 dB while LS reaches −38.6 dB at 30 dB. All estimators run in under "
         "1 ms per frame. BER points carry 95% Wilson confidence intervals."),
        ("Minute 5 — Insight and future work",
         "The floor comes from training one small network over the whole SNR range. Fixes: give the SNR to the "
         "network as an input, use a CNN over time and frequency, and test realistic ray-traced channels, "
         "which I have started with a DeepMIMO loader. The software is tested with 83 automated tests."),
    ]
    for title, text in parts:
        story.append(KeepTogether([P(title, "h2"), Paragraph(text, S["say"])]))


def numbers_card(story, W):
    sweep = load("snr_sweep_results.json")
    infer = load("inference_time_results.json")
    rec = {a: by_snr(r) for a, r in sweep["records"].items()}
    lat = infer["results"]
    bits = rec["LS"][0.0]["total_bits"]

    story.append(PageBreak())
    story.append(section("4. Project Numbers to Memorise"))
    rows = [["Item", "Value", "Why it matters"]]
    rows += [
        ["Antennas", "2 × 2 MIMO", "Two parallel streams (spatial multiplexing)"],
        ["Subcarriers / CP", "64 / 16 samples", "CP is 25% of the symbol, 20% overhead; must exceed the channel length"],
        ["Frame", "14 OFDM symbols", "Same as one 5G NR slot"],
        ["Pilots", "4 per transmit antenna", "Spacing 16 per antenna; enough to resolve 4 taps"],
        ["Data subcarriers", "56 per symbol", "64 minus 8 pilot positions"],
        ["Bits per frame", "3,136 (QPSK)", "2 antennas × 14 symbols × 56 × 2 bits"],
        ["Channel", "4-tap Rayleigh, exp. PDP", "Frequency-selective, block fading"],
        ["SNR range", "0 to 30 dB, step 5", f"{sweep['num_trials_per_snr']} trials per point, "
                                             f"{bits:,} bits per point"],
        ["DNN", "512→256→128→256→512", "Residual MLP, LayerNorm, GELU, dropout 0.05"],
        ["DNN parameters", "330,112", "Small enough for real-time CPU inference"],
        ["Training", "30,000 samples, 40 epochs", "Adam, MSE loss, 70/15/15 split, best-validation checkpoint"],
        ["Equaliser", "MMSE < 15 dB, ZF ≥ 15 dB", "MMSE avoids noise boost at low SNR"],
        ["Tests", "83 automated tests", "pytest; frontend builds with TypeScript"],
    ]
    story.append(booktabs(rows, [W * 0.2, W * 0.3, W * 0.5], zebra=True, align_center_from=99))
    story.append(P("Key Results", "h2"))
    rows = [["Metric", "LS", "LMMSE", "DNN"]]
    for snr in (0.0, 15.0, 30.0):
        rows.append([f"NMSE @ {snr:.0f} dB", fmt_nmse(rec["LS"][snr]), fmt_nmse(rec["MMSE"][snr]),
                     fmt_nmse(rec["DNN"][snr])])
    rows.append(["BER @ 30 dB", f"{rec['LS'][30.0]['ber']:.4f}", f"{rec['MMSE'][30.0]['ber']:.4f}",
                 f"{rec['DNN'][30.0]['ber']:.4f}"])
    rows.append(["Mean latency", f"{lat['LS']['mean_ms']:.2f} ms", f"{lat['MMSE']['mean_ms']:.2f} ms",
                 f"{lat['DNN']['mean_ms']:.2f} ms"])
    story.append(booktabs(rows, [W * 0.28, W * 0.24, W * 0.24, W * 0.24], zebra=True))
    story.append(callout(
        "<b>How to read NMSE in dB:</b> −10 dB means the error power is 10% of the channel power; "
        "−20 dB means 1%; −30 dB means 0.1%. So −38.6 dB is about 0.014% error.", W))


def theory(story, W):
    story.append(PageBreak())
    story.append(section("5. Wireless Mobile Communication Refresher"))
    story.append(P("The theory most likely to be asked, each linked to where it appears in your project."))

    story.append(P("5.1 Large-Scale Propagation", "h2"))
    story += bullets([
        "<b>Free-space (Friis):</b> received power falls with the square of distance.",
    ])
    story.append(formula("P<sub>r</sub> = P<sub>t</sub> G<sub>t</sub> G<sub>r</sub> λ² / "
                         "((4π)² d²)"))
    story += bullets([
        "<b>Log-distance path loss</b> with path-loss exponent n (2 in free space, about 2.7–5 in "
        "cities) and log-normal <b>shadowing</b> X<sub>σ</sub> from buildings and obstacles:",
    ])
    story.append(formula("PL(d) [dB] = PL(d<sub>0</sub>) + 10 n log<sub>10</sub>(d / d<sub>0</sub>) + "
                         "X<sub>σ</sub>"))
    story.append(P("<i>Project link:</i> NeuroMIMO normalises average channel power to 1 and sets the SNR "
                   "directly, so large-scale effects are absorbed into the SNR. DeepMIMO channels include "
                   "real path loss, which the loader normalises away."))

    story.append(P("5.2 Small-Scale Fading and Multipath", "h2"))
    story += bullets([
        "<b>Multipath:</b> copies of the signal arrive with different delays and phases and add up.",
        "<b>Rayleigh fading:</b> no line-of-sight path; many scattered paths make the channel a complex "
        "Gaussian, so its amplitude is Rayleigh distributed: p(r) = (r/σ²) exp(−r²/2"
        "σ²).",
        "<b>Rician fading:</b> one strong line-of-sight path plus scatter; the K-factor is the ratio of LoS "
        "power to scattered power (K = 0 gives Rayleigh).",
        "<b>RMS delay spread σ<sub>τ</sub>:</b> how spread out in time the echoes are.",
        "<b>Coherence bandwidth:</b> the frequency range over which the channel is roughly constant, "
        "B<sub>c</sub> ≈ 1/(5σ<sub>τ</sub>) (50% correlation) or 1/(50σ<sub>τ</sub>) "
        "(90% correlation).",
        "<b>Flat vs frequency-selective:</b> if signal bandwidth &lt; B<sub>c</sub> the fading is flat; "
        "otherwise it is frequency-selective (different subcarriers fade differently).",
        "<b>Doppler shift:</b> f<sub>d</sub> = (v/λ) cosθ; maximum f<sub>m</sub> = v/λ.",
        "<b>Coherence time:</b> how long the channel stays constant, T<sub>c</sub> ≈ 0.423 / f<sub>m</sub>.",
        "<b>Slow vs fast fading:</b> slow if the symbol time is much shorter than T<sub>c</sub>; fast "
        "otherwise.",
    ])
    story.append(P("<i>Project link:</i> 4-tap channel = frequency-selective (the |H| plot rises and falls "
                   "across subcarriers). Block fading (constant over the 14-symbol frame) = slow fading. "
                   "Doppler is not modelled yet; it is listed as future work."))

    story.append(P("5.3 Noise, SNR and BER", "h2"))
    story += bullets([
        "<b>AWGN:</b> additive white Gaussian noise from the receiver electronics.",
        "<b>SNR in dB</b> = 10 log<sub>10</sub>(P<sub>signal</sub>/P<sub>noise</sub>). 3 dB = double, "
        "10 dB = 10×, 30 dB = 1000×.",
        "<b>E<sub>b</sub>/N<sub>0</sub></b> is energy per bit over noise density. For QPSK, E<sub>s</sub>/"
        "N<sub>0</sub> = 2 E<sub>b</sub>/N<sub>0</sub> (2 bits per symbol).",
        "<b>QPSK BER in AWGN:</b> P<sub>b</sub> = Q(√(2E<sub>b</sub>/N<sub>0</sub>)), falls "
        "exponentially (a “waterfall”).",
        "<b>BER in Rayleigh fading:</b> P<sub>b</sub> = ½(1 − √(γ/(1+γ))) ≈ "
        "1/(4γ) at high SNR, so it falls only linearly: fading costs a lot. Diversity (more antennas) "
        "makes it fall faster.",
        "<b>Shannon capacity:</b> C = B log<sub>2</sub>(1 + SNR) bits/s.",
    ])

    story.append(P("5.4 Digital Modulation", "h2"))
    story += bullets([
        "<b>QPSK:</b> 4 phases, 2 bits per symbol. <b>16-QAM:</b> 16 points, 4 bits per symbol, needs "
        "higher SNR for the same BER.",
        "<b>Gray coding:</b> neighbouring constellation points differ in one bit, so the most likely symbol "
        "error causes only one bit error.",
        "<b>Constellation diagram:</b> shows the received points; noise spreads them, a channel error "
        "rotates or scales them (see the Signal Visualization page).",
    ])

    story.append(P("5.5 OFDM", "h2"))
    story += bullets([
        "Splits a wideband, frequency-selective channel into N narrow, flat subcarriers, so each needs only "
        "a one-tap equaliser H[k].",
        "Subcarriers are orthogonal: spacing Δf = 1/T<sub>symbol</sub>, so their spectra overlap but "
        "do not interfere. Implemented with the IFFT (transmitter) and FFT (receiver).",
        "<b>Cyclic prefix:</b> copy the last samples to the front. If CP length ≥ channel length it "
        "removes inter-symbol interference and keeps subcarriers orthogonal (circular convolution).",
    ])
    story.append(formula("Y[k] = H[k] X[k] + W[k]"))
    story += bullets([
        "<b>Advantages:</b> simple equalisation, robust to multipath, flexible resource allocation (OFDMA).",
        "<b>Disadvantages:</b> high peak-to-average power ratio (PAPR); sensitive to frequency offset and "
        "Doppler (inter-carrier interference); CP overhead.",
        "<b>Standards:</b> LTE uses 15 kHz spacing; 5G NR uses 15·2<sup>μ</sup> kHz (15, 30, 60, "
        "120 kHz) with 14 symbols per slot.",
    ])
    story.append(P("<i>Project link:</i> 64 subcarriers, CP 16 ≥ 4 taps, so no ISI; 14 symbols per "
                   "frame like a 5G NR slot."))

    story.append(P("5.6 MIMO", "h2"))
    story += bullets([
        "<b>Diversity gain:</b> send the same data over several paths to fight fading (e.g. Alamouti code "
        "with 2 transmit antennas).",
        "<b>Multiplexing gain:</b> send different data streams at once; capacity grows by about "
        "min(N<sub>t</sub>, N<sub>r</sub>) times at high SNR.",
    ])
    story.append(formula("C = log<sub>2</sub> det( I + (SNR/N<sub>t</sub>) H H<super>H</super> ) bits/s/Hz"))
    story += bullets([
        "<b>Received signal per subcarrier:</b> <b>y</b> = <b>H</b><b>x</b> + <b>n</b>, with <b>H</b> a "
        "2×2 matrix.",
        "<b>Zero-forcing equaliser:</b> <b>W</b> = (<b>H</b><super>H</super><b>H</b>)<super>−1</super>"
        "<b>H</b><super>H</super>; removes interference but amplifies noise.",
        "<b>MMSE equaliser:</b> <b>W</b> = (<b>H</b><super>H</super><b>H</b> + σ²<b>I</b>)"
        "<super>−1</super><b>H</b><super>H</super>; balances interference and noise.",
    ])
    story.append(P("<i>Project link:</i> 2×2 spatial multiplexing (two streams); MMSE equaliser below "
                   "15 dB, zero-forcing above."))

    story.append(P("5.7 Channel Estimation", "h2"))
    story += bullets([
        "<b>Pilot patterns:</b> block-type (whole symbols of pilots; good for slow fading), comb-type "
        "(some subcarriers in every symbol; good for fast fading), lattice (both).",
        "<b>Sampling rule:</b> pilots sample the channel in frequency, so you need at least as many pilots "
        "as channel taps (N<sub>p</sub> ≥ L), i.e. spacing ≤ N/L. In time, pilots must repeat "
        "faster than the coherence time.",
        "<b>LS:</b> Ĥ = Y/X at pilots. Unbiased, no prior needed, but error = noise/|X|².",
        "<b>LMMSE:</b> Ĥ = <b>R</b><sub>HP</sub>(<b>R</b><sub>PP</sub> + σ²<b>I</b>)"
        "<super>−1</super>Ĥ<sub>LS</sub>. Uses channel correlation; best linear estimator; needs "
        "statistics and an O(N<sub>p</sub>³) inverse.",
        "<b>Interpolation:</b> linear, spline, or DFT-based (transform to time, keep the taps, transform "
        "back).",
        "<b>Deep learning:</b> learn the estimator from data (e.g. ChannelNet, DNN estimators).",
    ])
    story.append(P("<i>Project link:</i> comb pilots, 4 per antenna = 4 taps, exactly enough. With spacing "
                   "16 overall (2 pilots per antenna) every estimator fails, which demonstrates the "
                   "sampling rule."))

    story.append(P("5.8 Cellular Basics (in case they come up)", "h2"))
    rows = [["Generation", "Key technology", "Multiple access"]]
    rows += [
        ["1G (1980s)", "Analogue voice", "FDMA"],
        ["2G (GSM, 1990s)", "Digital voice, SMS", "TDMA + FDMA"],
        ["3G (UMTS)", "Mobile data", "CDMA"],
        ["4G (LTE)", "All-IP broadband, MIMO-OFDM", "OFDMA (downlink)"],
        ["5G (NR)", "Massive MIMO, mmWave, flexible numerology", "OFDMA"],
    ]
    story.append(booktabs(rows, [W * 0.24, W * 0.46, W * 0.30], zebra=True, align_center_from=99))
    story += bullets([
        "<b>Cell and frequency reuse:</b> the area is divided into cells; the same frequencies are reused in "
        "distant cells to increase capacity. Smaller cells mean more reuse.",
        "<b>Handoff (handover):</b> switching a call to a new base station as the user moves.",
        "<b>Co-channel interference:</b> interference from cells using the same frequency.",
    ])


QUESTIONS = [
    ("Basics", [
        ("What is channel estimation and why is it needed?",
         "Working out how the channel changed the signal (gain and phase on each subcarrier, for each antenna "
         "pair). The receiver needs it to equalise and to separate the MIMO streams; wrong estimates mean bit "
         "errors."),
        ("Why use OFDM?",
         "It turns a frequency-selective channel into many flat subchannels, each equalised with one complex "
         "gain, and the cyclic prefix removes inter-symbol interference."),
        ("Why is the cyclic prefix 16 samples?",
         "It must be at least as long as the channel impulse response. The channel has 4 taps, so 16 gives a "
         "large safety margin. The cost is 20% overhead (16 of 80 samples)."),
        ("What is the difference between diversity and multiplexing?",
         "Diversity sends the same information over several paths for reliability; multiplexing sends "
         "different streams at once for higher data rate. My project uses 2×2 spatial multiplexing."),
        ("What is Rayleigh fading?",
         "Fading with no line-of-sight path: many scattered paths add up to a complex Gaussian channel whose "
         "amplitude follows a Rayleigh distribution."),
        ("What are pilots and why comb-type?",
         "Known symbols on known subcarriers. Comb pilots appear in every OFDM symbol, so they track changes "
         "over time; they suit fast-changing channels. The two antennas use different subcarriers so their "
         "pilots do not interfere."),
    ]),
    ("Project design", [
        ("Why 2×2 MIMO and 64 subcarriers?",
         "It is the smallest real MIMO case and keeps simulation and training fast on a laptop, while still "
         "showing frequency selectivity and stream separation. Scaling to 4×4 or more is future work."),
        ("Why a residual network?",
         "The LS estimate is already close. The network only learns the correction "
         "Ĥ<sub>DNN</sub> = Ĥ<sub>LS</sub> + f(Ĥ<sub>LS</sub>), which is easier to learn, trains "
         "faster and starts from LS quality instead of from zero."),
        ("What is the input and output of the DNN?",
         "Input: the LS estimate, 2×2×64 complex values split into 512 real numbers (real and "
         "imaginary parts). Output: 512 numbers forming the refined channel."),
        ("Where does the training data come from?",
         "It is simulated: random Rayleigh channels, random SNR between 0 and 30 dB, pilots sent through the "
         "channel with noise. The noisy LS estimate is the input and the true channel is the target. This is "
         "standard in channel-estimation research because the true channel is known in simulation."),
        ("How did you avoid data leakage and overfitting?",
         "Each sample uses its own new channel and the samples are split 70/15/15 into train, validation and "
         "test, so test channels are never seen. The model saved is the one with the best validation loss, "
         "with dropout 0.05 and LayerNorm."),
        ("Why compare on identical channels?",
         "The random generator is reset with the same seed for each estimator, so they all see the same "
         "channels and noise. Differences then come only from the estimators, not from luck."),
        ("What is NMSE?",
         "Mean squared estimation error divided by channel power, in dB. Lower is better: −20 dB means the "
         "error is 1% of the channel power."),
        ("Why Wilson confidence intervals and the rule of three?",
         "BER from a finite number of bits is uncertain. The Wilson interval gives a reliable 95% range; when "
         "zero errors occur, the rule of three gives the upper bound 3/N<sub>bits</sub> instead of claiming a "
         "BER of zero."),
    ]),
    ("Results", [
        ("Does the DNN beat LS?",
         "At low SNR it is slightly better than LS (−8.7 dB vs −8.4 dB at 0 dB) and close to LMMSE (−9.1 dB). "
         "At high SNR it is worse: it levels off around −25 dB while LS keeps improving to −38.6 dB. I report this honestly rather than hiding it."),
        ("Why does the DNN have an error floor at high SNR?",
         "One small network is trained over the whole 0–30 dB range, so it learns an average amount of "
         "denoising. At high SNR the LS estimate is already very accurate and the network's own approximation "
         "error dominates. Fixes: give SNR as an input, train separate models per SNR band, or use a larger "
         "model."),
        ("Why does BER level off instead of going to zero at high SNR?",
         "In Rayleigh fading some frames hit deep fades, so BER only falls about linearly with SNR. With "
         "15 frames per point a few bad channels dominate the errors."),
        ("Is it fast enough for real systems?",
         "Mean latency is about 0.1 ms for LS, 0.4 ms for LMMSE and 0.65 ms for the DNN per frame on a CPU, "
         "all well below a 1 ms 5G slot. On a GPU or with batching the DNN would be faster."),
        ("What happens with fewer pilots?",
         "With 2 pilots per antenna the channel (4 taps) is under-sampled and every estimator fails (about "
         "−4 dB NMSE). This confirms the rule that the number of pilots must be at least the number of "
         "channel taps."),
    ]),
    ("Critical and future work", [
        ("What is new in your project?",
         "An honest, reproducible comparison: identical channels for all estimators, the full 0–30 dB "
         "range including where the DNN loses, confidence intervals on BER, latency and generalisation tests, "
         "and an interactive dashboard plus a DeepMIMO loader for realistic channels."),
        ("Your data is synthetic. Is that a problem?",
         "Simulation is the standard first step because the true channel is known exactly. To move toward "
         "real conditions I added a DeepMIMO loader for ray-traced channels from realistic scenes; testing "
         "on those is the next step."),
        ("What are the limitations?",
         "Small 2×2 system, block fading with no Doppler, perfect synchronisation, one modulation for "
         "training, and the DNN high-SNR floor. Each is listed as future work."),
        ("What would you do next?",
         "Feed SNR to the network; try a CNN over time and frequency (like ChannelNet); add Doppler with the "
         "Jakes model; scale to 4×4 and 8×8; evaluate on DeepMIMO channels; learn pilot placement."),
    ]),
]


def questions(story, W):
    story.append(PageBreak())
    story.append(section("6. Expected Questions and Model Answers"))
    story.append(P("Cover the answers with a sheet of paper and answer out loud first."))
    for group, items in QUESTIONS:
        story.append(P(group, "h2"))
        for i, (q, a) in enumerate(items, 1):
            story.append(qa(f"Q. {q}", a))


def weaknesses(story, W):
    story.append(PageBreak())
    story.append(section("7. Known Weaknesses: Answer These Honestly"))
    story.append(P(
        "A good examiner looks for the weak spots. Knowing them and explaining them is a strength."))

    sweep = load("snr_sweep_results.json")
    rec = {a: by_snr(r) for a, r in sweep["records"].items()}
    # LMMSE NMSE from the saved results before the noise-scaling fix
    lmmse_before = {0.0: "\u22124.01 dB", 10.0: "\u221214.71 dB", 20.0: "\u221227.30 dB", 30.0: "\u221238.41 dB"}

    story.append(P("7.1 The LMMSE bug you found and fixed", "h2"))
    story.append(P(
        "<b>What happened:</b> earlier results showed LMMSE <i>worse</i> than LS at low SNR (\u22124.0 dB "
        "against \u22128.4 dB at 0 dB), which contradicts theory. If the professor has seen older slides "
        "or PDFs, be ready to explain."))
    story.append(P(
        "<b>The cause:</b> the receiver averages each pilot over the 14 OFDM symbols of the frame, which "
        "reduces the pilot noise 14 times (about 11.5 dB). The LMMSE filter was given the un-averaged noise "
        "variance \u03c3\u00b2 instead of \u03c3\u00b2/14, so it assumed far more noise than there was "
        "and over-smoothed the estimate. <b>The fix</b> passes \u03c3\u00b2/14 to the estimators (the "
        "equaliser still uses \u03c3\u00b2, because data symbols are not averaged), with a regression test."))
    rows = [["SNR", "LS", "LMMSE before fix", "LMMSE after fix"]]
    for snr in (0.0, 10.0, 20.0, 30.0):
        rows.append([f"{snr:.0f} dB", fmt_nmse(rec["LS"][snr]), lmmse_before[snr], fmt_nmse(rec["MMSE"][snr])])
    story.append(booktabs(rows, [W * 0.16, W * 0.26, W * 0.29, W * 0.29], zebra=True))
    story.append(P("Saved results, 15 trials per SNR point, seed 42.", "caption"))
    story.append(callout(
        "<b>What to say:</b> \u201cI found that my LMMSE used the noise variance before pilot averaging over "
        "the 14 symbols. With the correct value \u03c3\u00b2/14 it is now the best estimator at low SNR, "
        f"{fmt_nmse(rec['MMSE'][0.0])} against {fmt_nmse(rec['LS'][0.0])} for LS at 0 dB, as theory "
        "predicts. The gain is small because with 4 pilots and 4 taps the DFT-based LS estimate is already "
        "efficient.\u201d", W, fill="#FFF6E5", edge="#E0A030"))

    story.append(P("7.2 The DNN model was retrained", "h2"))
    story.append(P(
        "The model file in the repository had been overwritten by a 2-epoch test model (an old test bug, "
        "since fixed). It was retrained on 30,000 simulated channels (21,000 training, 4,500 validation, "
        "4,500 test) for 40 epochs with batch size 128 and learning rate 0.001, keeping the checkpoint with "
        "the best validation loss. All results and figures were then regenerated."))

    story.append(P("7.3 Other weaknesses", "h2"))
    rows = [["Weakness", "Honest answer"]]
    rows += [
        ["DNN error floor at high SNR", "Explained in Section 6; SNR-aware input or per-SNR models would fix it."],
        ["Only simulated channels", "Standard practice; DeepMIMO loader added for realistic ray-traced channels."],
        ["No Doppler / mobility", "Block fading assumed; Jakes Doppler model is planned."],
        ["Small 2×2 system", "Chosen for speed and clarity; code is structured to scale."],
        ["Perfect synchronisation", "Timing and frequency offset are not modelled, as in most estimation studies."],
        ["Only 15 trials per SNR", "Confidence intervals are shown; more trials would narrow them."],
    ]
    story.append(booktabs(rows, [W * 0.32, W * 0.68], zebra=True, align_center_from=99))


def demo(story, W):
    story.append(PageBreak())
    story.append(section("8. Demo Plan and Checklist"))
    story.append(P("Demo order (about 3 minutes)", "h2"))
    story += bullets([
        "<b>Overview page:</b> point to the pipeline steps and the status cards (API connected, model ready).",
        "<b>MIMO-OFDM Simulator:</b> run at 0 dB, then at 20 dB, and show NMSE and BER improve.",
        "<b>Signal Visualization:</b> show the constellation and the channel frequency response (frequency "
        "selectivity).",
        "<b>Performance Comparison:</b> show the NMSE and BER curves and the summary cards.",
        "<b>ML Model Training:</b> show the loss curve (do not start a long training run during the review).",
    ])
    story.append(P("Start the app before you walk in", "h2"))
    story.append(code_box("""
# Terminal 1 (project folder)
uvicorn neuromimo.api.main:app --app-dir backend --port 8000
# Terminal 2
cd frontend
npm run dev          # open http://localhost:5173
""", W))
    story.append(P(
        f"The first simulation after starting can take about 2 seconds while the model loads; run one "
        f"simulation in advance so the demo is fast."))
    story.append(P("Checklist", "h2"))
    story += bullets([
        "Laptop charged; charger packed; app already running; browser zoom set so charts are readable.",
        f"Backup if the laptop fails: the PDFs in {mono('docs/')} and the figures in "
        f"{mono('backend/results/')} on a USB drive or phone.",
        "Printed or offline copy of the 60-second pitch and the numbers card.",
        "Know where each part of the code is (Section 4 of the explainer PDF).",
        "Sleep. A rested explanation beats an extra hour of reading.",
    ])


def build():
    doc = NotesTemplate(OUTPUT, title="NeuroMIMO — Review Preparation Notes", author="NeuroMIMO",
                        subject="Wireless Mobile Communication project review")
    W = doc.width
    story = [
        Spacer(1, 50 * mm),
        P("NeuroMIMO", "title"),
        Spacer(1, 6),
        P("R<font size='12'>EVIEW</font> P<font size='12'>REPARATION</font> N<font size='12'>OTES</font>",
          "subtitle"),
        Spacer(1, 22 * mm),
        P("Wireless Mobile Communication • Project Review", "tag"),
        Spacer(1, 22 * mm),
        P("Pitch, talk script, numbers to memorise, theory refresher, expected questions with answers, and "
          "honest answers about known weaknesses.", "abstract"),
        Spacer(1, 80 * mm),
        P(date.today().strftime("%B %d, %Y").replace(" 0", " "), "date"),
        NextPageTemplate("toc"),
        PageBreak(),
    ]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc0", fontName=BODY, fontSize=10.5, leading=15,
                                      textColor=LINK_BLUE, leftIndent=10)]
    story += [Spacer(1, 25 * mm), P("Contents", "toc_title"), toc, NextPageTemplate("main"), PageBreak()]

    how_to_use(story, W)
    pitch(story, W)
    talk(story, W)
    numbers_card(story, W)
    theory(story, W)
    questions(story, W)
    weaknesses(story, W)
    demo(story, W)

    doc.multiBuild(story)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
