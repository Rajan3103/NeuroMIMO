"""Builds docs/NeuroMIMO_Research_Pack.pdf: problem statement, literature survey,
reference papers, a sample research paper, and AI prompts for building and
extending the project.

Reuses the page layout and styles of build_documentation.py. Every result quoted
in the sample paper is read from backend/results/, so the numbers match the code.

Usage (from the repository root):
    pip install reportlab pillow
    python docs/build_research_pack.py
"""

import os
import sys
from datetime import date

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
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
    ITALIC,
    LINK_BLUE,
    MONO,
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

OUTPUT = os.path.join(ROOT, "docs", "NeuroMIMO_Research_Pack.pdf")

PROMPT_BG = colors.HexColor("#EEF3FB")
PROMPT_EDGE = colors.HexColor("#1F4E9E")

S["prompt"] = ParagraphStyle("prompt", fontName=BODY, fontSize=9.6, leading=13)
S["prompt_title"] = ParagraphStyle("prompt_title", fontName=S["h2"].fontName, fontSize=10.5,
                                   leading=13.5, spaceBefore=8, spaceAfter=3, keepWithNext=1)
S["ref"] = ParagraphStyle("ref", parent=S["body"], fontSize=9.6, leading=12.8,
                          leftIndent=22, firstLineIndent=-22, spaceAfter=4, alignment=0)
S["abstract_body"] = ParagraphStyle("abstract_body", parent=S["body"], fontName=ITALIC,
                                    fontSize=10, leading=13.5, leftIndent=18, rightIndent=18)
S["note"] = ParagraphStyle("note", parent=S["body"], fontSize=9.4, leading=12.6,
                           textColor=colors.HexColor("#333333"))


class ResearchPackTemplate(DocTemplate):
    """Same layout as the project documentation, with its own running header."""

    def _header(self, canv, doc):
        canv.saveState()
        top = A4[1] - 18 * mm
        canv.setFont(ITALIC, 10.5)
        canv.drawString(self.leftMargin, top, "NeuroMIMO Research Pack")
        canv.setFont(BODY, 10.5)
        canv.drawRightString(A4[0] - self.rightMargin, top, str(doc.page - 1))
        canv.setLineWidth(0.5)
        canv.line(self.leftMargin, top - 4, A4[0] - self.rightMargin, top - 4)
        canv.restoreState()


def prompt_box(title, text, width):
    """A titled, shaded box holding a copy-ready prompt (wraps like normal text)."""
    paragraphs = [Paragraph(part.strip().replace("\n", "<br/>"), S["prompt"])
                  for part in text.strip().split("\n\n")]
    body = []
    for i, para in enumerate(paragraphs):
        if i:
            body.append(Spacer(1, 4))
        body.append(para)
    box = Table([[body]], colWidths=[width])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PROMPT_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, PROMPT_EDGE),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return KeepTogether([Paragraph(title, S["prompt_title"]), box, Spacer(1, 4)])


# -----------------------------------------------------------------------------
# Reference list (IEEE style). Numbers are cited as [n] throughout the survey.
# -----------------------------------------------------------------------------
REFERENCES = [
    # Foundations: MIMO and OFDM
    ("telatar", "I. E. Telatar, “Capacity of multi-antenna Gaussian channels,” <i>European Trans. "
     "Telecommunications</i>, vol. 10, no. 6, pp. 585–595, 1999."),
    ("foschini", "G. J. Foschini and M. J. Gans, “On limits of wireless communications in a fading "
     "environment when using multiple antennas,” <i>Wireless Personal Communications</i>, vol. 6, "
     "no. 3, pp. 311–335, 1998."),
    ("alamouti", "S. M. Alamouti, “A simple transmit diversity technique for wireless communications,” "
     "<i>IEEE J. Sel. Areas Commun.</i>, vol. 16, no. 8, pp. 1451–1458, Oct. 1998."),
    ("weinstein", "S. B. Weinstein and P. M. Ebert, “Data transmission by frequency-division multiplexing "
     "using the discrete Fourier transform,” <i>IEEE Trans. Commun. Technol.</i>, vol. 19, no. 5, "
     "pp. 628–634, Oct. 1971."),
    ("hwang", "T. Hwang, C. Yang, G. Wu, S. Li, and G. Y. Li, “OFDM and its wireless applications: "
     "A survey,” <i>IEEE Trans. Veh. Technol.</i>, vol. 58, no. 4, pp. 1673–1694, May 2009."),
    ("tse", "D. Tse and P. Viswanath, <i>Fundamentals of Wireless Communication</i>. Cambridge, U.K.: "
     "Cambridge Univ. Press, 2005."),
    ("goldsmith", "A. Goldsmith, <i>Wireless Communications</i>. Cambridge, U.K.: Cambridge Univ. Press, 2005."),
    # Classical pilot-aided channel estimation
    ("vandebeek", "J.-J. van de Beek, O. Edfors, M. Sandell, S. K. Wilson, and P. O. Börjesson, "
     "“On channel estimation in OFDM systems,” in <i>Proc. IEEE 45th Veh. Technol. Conf.</i>, "
     "1995, pp. 815–819."),
    ("edfors", "O. Edfors, M. Sandell, J.-J. van de Beek, S. K. Wilson, and P. O. Börjesson, “OFDM "
     "channel estimation by singular value decomposition,” <i>IEEE Trans. Commun.</i>, vol. 46, "
     "no. 7, pp. 931–939, Jul. 1998."),
    ("li", "Y. Li, L. J. Cimini, and N. R. Sollenberger, “Robust channel estimation for OFDM systems "
     "with rapid dispersive fading channels,” <i>IEEE Trans. Commun.</i>, vol. 46, no. 7, "
     "pp. 902–915, Jul. 1998."),
    ("morelli", "M. Morelli and U. Mengali, “A comparison of pilot-aided channel estimation methods "
     "for OFDM systems,” <i>IEEE Trans. Signal Process.</i>, vol. 49, no. 12, pp. 3065–3073, "
     "Dec. 2001."),
    ("coleri", "S. Coleri, M. Ergen, A. Puri, and A. Bahai, “Channel estimation techniques based on "
     "pilot arrangement in OFDM systems,” <i>IEEE Trans. Broadcast.</i>, vol. 48, no. 3, "
     "pp. 223–229, Sep. 2002."),
    ("ozdemir", "M. K. Ozdemir and H. Arslan, “Channel estimation for wireless OFDM systems,” "
     "<i>IEEE Commun. Surveys Tuts.</i>, vol. 9, no. 2, pp. 18–48, 2007."),
    ("biguesh", "M. Biguesh and A. B. Gershman, “Training-based MIMO channel estimation: A study of "
     "estimator tradeoffs and optimal training signals,” <i>IEEE Trans. Signal Process.</i>, "
     "vol. 54, no. 3, pp. 884–893, Mar. 2006."),
    ("kay", "S. M. Kay, <i>Fundamentals of Statistical Signal Processing, Volume I: Estimation Theory</i>. "
     "Upper Saddle River, NJ, USA: Prentice Hall, 1993."),
    # Deep learning for the physical layer
    ("oshea", "T. O’Shea and J. Hoydis, “An introduction to deep learning for the physical layer,” "
     "<i>IEEE Trans. Cogn. Commun. Netw.</i>, vol. 3, no. 4, pp. 563–575, Dec. 2017."),
    ("wang", "T. Wang, C.-K. Wen, H. Wang, F. Gao, T. Jiang, and S. Jin, “Deep learning for wireless "
     "physical layer: Opportunities and challenges,” <i>China Communications</i>, vol. 14, no. 11, "
     "pp. 92–111, Nov. 2017."),
    ("qin", "Z. Qin, H. Ye, G. Y. Li, and B.-H. F. Juang, “Deep learning in physical layer "
     "communications,” <i>IEEE Wireless Commun.</i>, vol. 26, no. 2, pp. 93–99, Apr. 2019."),
    # Deep learning channel estimation
    ("ye", "H. Ye, G. Y. Li, and B.-H. F. Juang, “Power of deep learning for channel estimation and "
     "signal detection in OFDM systems,” <i>IEEE Wireless Commun. Lett.</i>, vol. 7, no. 1, "
     "pp. 114–117, Feb. 2018."),
    ("soltani", "M. Soltani, V. Pourahmadi, A. Mirzaei, and H. Sheikhzadeh, “Deep learning-based "
     "channel estimation,” <i>IEEE Commun. Lett.</i>, vol. 23, no. 4, pp. 652–655, Apr. 2019."),
    ("neumann", "D. Neumann, T. Wiese, and W. Utschick, “Learning the MMSE channel estimator,” "
     "<i>IEEE Trans. Signal Process.</i>, vol. 66, no. 11, pp. 2905–2917, Jun. 2018."),
    ("he_mmwave", "H. He, C.-K. Wen, S. Jin, and G. Y. Li, “Deep learning-based channel estimation for "
     "beamspace mmWave massive MIMO systems,” <i>IEEE Wireless Commun. Lett.</i>, vol. 7, no. 5, "
     "pp. 852–855, Oct. 2018."),
    ("dong", "P. Dong, H. Zhang, G. Y. Li, I. S. Gaspar, and N. NaderiAlizadeh, “Deep CNN-based channel "
     "estimation for mmWave massive MIMO systems,” <i>IEEE J. Sel. Topics Signal Process.</i>, "
     "vol. 13, no. 5, pp. 989–1000, Sep. 2019."),
    ("wen", "C.-K. Wen, W.-T. Shih, and S. Jin, “Deep learning for massive MIMO CSI feedback,” "
     "<i>IEEE Wireless Commun. Lett.</i>, vol. 7, no. 5, pp. 748–751, Oct. 2018."),
    ("mashhadi", "M. B. Mashhadi and D. Gündüz, “Pruning the pilots: Deep learning-based pilot "
     "design and channel estimation for MIMO-OFDM systems,” <i>IEEE Trans. Wireless Commun.</i>, "
     "vol. 20, no. 10, pp. 6315–6328, Oct. 2021."),
    # Neural receivers and tooling
    ("honkala", "M. Honkala, D. Korpi, and J. M. J. Huttunen, “DeepRx: Fully convolutional deep learning "
     "receiver,” <i>IEEE Trans. Wireless Commun.</i>, vol. 20, no. 6, pp. 3925–3940, Jun. 2021."),
    ("aitaoudia", "F. Ait Aoudia and J. Hoydis, “End-to-end learning for OFDM: From neural receivers to "
     "pilotless communication,” <i>IEEE Trans. Wireless Commun.</i>, vol. 21, no. 2, "
     "pp. 1049–1063, Feb. 2022."),
    ("sionna", "J. Hoydis, S. Cammerer, F. Ait Aoudia, A. Vem, N. Binder, G. Marcus, and A. Keller, "
     "“Sionna: An open-source library for next-generation physical layer research,” "
     "arXiv:2203.11854, 2022."),
    # Machine learning building blocks and statistics
    ("resnet", "K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image recognition,” "
     "in <i>Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)</i>, 2016, pp. 770–778."),
    ("adam", "D. P. Kingma and J. Ba, “Adam: A method for stochastic optimization,” in "
     "<i>Proc. Int. Conf. Learn. Represent. (ICLR)</i>, 2015."),
    ("brown", "L. D. Brown, T. T. Cai, and A. DasGupta, “Interval estimation for a binomial "
     "proportion,” <i>Statistical Science</i>, vol. 16, no. 2, pp. 101–133, 2001."),
    ("hanley", "J. A. Hanley and A. Lippman-Hand, “If nothing goes wrong, is everything all right? "
     "Interpreting zero numerators,” <i>JAMA</i>, vol. 249, no. 13, pp. 1743–1745, 1983."),
    ("jakes", "W. C. Jakes, Ed., <i>Microwave Mobile Communications</i>. New York, NY, USA: Wiley, 1974."),
    ("3gpp", "3GPP, “NR; Physical channels and modulation,” Technical Specification TS 38.211."),
]
REF_NUM = {key: i + 1 for i, (key, _) in enumerate(REFERENCES)}


def cite(*keys):
    return "[" + ", ".join(str(REF_NUM[k]) for k in keys) + "]"


# -----------------------------------------------------------------------------
# Content
# -----------------------------------------------------------------------------
def problem_statement(story, W):
    story.append(section("1. Problem Statement"))
    story.append(P("Background", "h2"))
    story.append(P(
        "Modern wireless standards such as 5G NR and Wi-Fi 6/7 combine Multiple-Input Multiple-Output "
        f"(MIMO) antennas with Orthogonal Frequency-Division Multiplexing (OFDM) {cite('telatar', 'hwang', '3gpp')}. "
        "MIMO sends several data streams at once over the same frequency band, and OFDM splits a wideband "
        "channel into many narrow subcarriers that each see a simple, flat channel. To separate the streams "
        "and undo the distortion on each subcarrier, the receiver must know the channel frequency response "
        "<b>H</b>, so channel estimation sits at the heart of every MIMO-OFDM receiver."))
    story.append(P(
        "Receivers estimate <b>H</b> from known <i>pilot</i> symbols inserted between the data. The two "
        f"classical estimators are Least Squares (LS) and Linear Minimum Mean Square Error (LMMSE) "
        f"{cite('vandebeek', 'morelli')}. LS is simple and fast but amplifies noise at low signal-to-noise "
        "ratio (SNR). LMMSE suppresses noise well but needs the channel correlation matrix and noise "
        "variance, which are hard to track in practice, and it requires a costly matrix inversion."))

    story.append(P("Problem", "h2"))
    story.append(P(
        "<b>How accurately, how reliably, and at what computational cost can a lightweight deep neural "
        "network estimate the channel of a 2×2 MIMO-OFDM link from pilot observations, compared with "
        "LS and LMMSE, across low to high SNR, and how well does it generalise to channels it was not "
        "trained on?</b>"))
    story.append(P(
        f"Published deep learning estimators {cite('ye', 'soltani')} often report gains in narrow settings "
        "and seldom report statistical confidence, latency, or behaviour on unseen channels. Students and "
        "researchers also lack an open, reproducible tool that runs the classical and learned estimators "
        "side by side on <i>identical</i> channel realisations and shows the results interactively."))

    story.append(P("Objectives", "h2"))
    story += bullets([
        "Build a vectorised 2×2 MIMO-OFDM baseband simulator: QPSK/16-QAM mapping, 64-point FFT, "
        "16-sample cyclic prefix, orthogonal comb pilots, AWGN and 4-tap Rayleigh multipath channels.",
        "Implement LS (with DFT interpolation) and LMMSE estimators as classical baselines, plus a "
        "perfect-CSI genie bound.",
        "Design and train a residual multilayer perceptron (MLP) that refines the LS estimate, with a "
        "leakage-free train/validation/test split by channel realisation.",
        "Compare all estimators by NMSE, BER and SER over 0–30 dB SNR with 95% confidence intervals, "
        "and measure inference latency.",
        "Test generalisation to mismatched power-delay profiles, longer channels and different pilot "
        "densities.",
        "Deliver the work as a FastAPI back end and a React dashboard so results are reproducible and "
        "can be explored interactively.",
    ])

    story.append(P("Scope and Assumptions", "h2"))
    story += bullets([
        "Software simulation only; no radio hardware. Synthetic channels with an exponential "
        "power-delay profile and block fading (the channel is constant within one OFDM frame).",
        "2 transmit and 2 receive antennas, 64 subcarriers, perfect time and frequency synchronisation.",
        "The DNN runs on CPU; results must be reproducible from fixed random seeds.",
    ])

    story.append(P("Expected Outcomes and Success Criteria", "h2"))
    story += bullets([
        "A working simulator whose LS and LMMSE results follow theory (for example, NMSE improving by "
        "about 10 dB per 10 dB of SNR for LS).",
        "A trained DNN with measured NMSE/BER versus SNR, honestly reported where it wins and where it "
        "loses.",
        "Latency below 1 ms per frame on a CPU for every estimator.",
        "An automated test suite and a dashboard that reproduce every figure in the report.",
    ])


def literature_survey(story, W):
    story.append(PageBreak())
    story.append(section("2. Literature Survey"))
    story.append(P(
        "This survey moves from the foundations of MIMO and OFDM, through classical pilot-aided channel "
        "estimation, to deep learning for the physical layer and learned channel estimators. It ends with "
        "the research gap that NeuroMIMO addresses. Numbers in square brackets refer to Section 3."))

    story.append(P("2.1 MIMO and OFDM Foundations", "h2"))
    story.append(P(
        f"Telatar {cite('telatar')} and Foschini and Gans {cite('foschini')} showed that the capacity of a "
        "rich-scattering channel grows roughly linearly with the smaller of the number of transmit and "
        "receive antennas, which is the basis of spatial multiplexing. Alamouti "
        f"{cite('alamouti')} gave a simple two-antenna transmit diversity scheme. OFDM was made practical "
        f"by Weinstein and Ebert {cite('weinstein')}, who implemented multicarrier modulation with the DFT; "
        f"the cyclic prefix turns the linear channel convolution into a circular one, so each subcarrier "
        f"sees a single complex gain. Hwang <i>et al.</i> {cite('hwang')} survey OFDM in modern standards, "
        f"and the textbooks {cite('tse', 'goldsmith')} cover both topics in depth."))

    story.append(P("2.2 Classical Pilot-Aided Channel Estimation", "h2"))
    story.append(P(
        f"van de Beek <i>et al.</i> {cite('vandebeek')} compared LS and LMMSE estimators for OFDM and "
        "showed that LMMSE greatly reduces error at low SNR at a large computational cost. Edfors "
        f"<i>et al.</i> {cite('edfors')} reduced that cost with a low-rank approximation based on the "
        f"singular value decomposition. Li, Cimini and Sollenberger {cite('li')} exploited the "
        "time-frequency correlation of the channel for robust estimation in fast fading. Morelli and "
        f"Mengali {cite('morelli')} compared pilot-aided methods systematically, and Coleri <i>et al.</i> "
        f"{cite('coleri')} studied block-type versus comb-type pilot arrangements and interpolation "
        f"methods. Ozdemir and Arslan {cite('ozdemir')} give a broad survey. For MIMO, Biguesh and "
        f"Gershman {cite('biguesh')} analysed LS and LMMSE trade-offs and optimal training signals. "
        f"The estimation theory behind these methods is covered by Kay {cite('kay')}."))
    story.append(P(
        "<b>Takeaway:</b> LS needs no prior knowledge but suffers from noise enhancement; LMMSE is "
        "optimal among linear estimators but depends on accurate channel statistics and a matrix inverse. "
        "This trade-off motivates data-driven estimators that learn the prior from examples."))

    story.append(P("2.3 Deep Learning for the Physical Layer", "h2"))
    story.append(P(
        f"O’Shea and Hoydis {cite('oshea')} framed the transmitter, channel and receiver as an "
        f"autoencoder that can be trained end to end. Wang <i>et al.</i> {cite('wang')} and Qin "
        f"<i>et al.</i> {cite('qin')} reviewed opportunities and open challenges, noting that learned "
        "blocks are most useful where models are inaccurate or optimal algorithms are too complex, and "
        "warning about generalisation and the cost of training data."))

    story.append(P("2.4 Deep Learning Channel Estimation", "h2"))
    story.append(P(
        f"Ye, Li and Juang {cite('ye')} trained a fully connected network to recover transmitted symbols "
        "directly from received OFDM signals, outperforming LS and matching LMMSE with fewer pilots and "
        f"without a cyclic prefix. Soltani <i>et al.</i> {cite('soltani')} treated the pilot grid as a "
        "low-resolution image and used super-resolution and denoising CNNs (ChannelNet) to reconstruct "
        f"the full channel. Neumann, Wiese and Utschick {cite('neumann')} derived a neural network "
        "structure from the MMSE estimator itself, giving a learned estimator with lower complexity. For "
        f"millimetre-wave massive MIMO, He <i>et al.</i> {cite('he_mmwave')} used a learned denoising "
        f"network and Dong <i>et al.</i> {cite('dong')} used deep CNNs that exploit correlation across "
        f"frequency and time. Wen, Shih and Jin {cite('wen')} compressed channel state information for "
        f"feedback (CsiNet), and Mashhadi and Gündüz {cite('mashhadi')} jointly learned pilot "
        "placement and channel estimation for MIMO-OFDM."))

    story.append(P("2.5 Neural Receivers", "h2"))
    story.append(P(
        f"More recent work replaces several receiver blocks at once. DeepRx {cite('honkala')} is a fully "
        "convolutional receiver that maps received resource grids to bit likelihoods. Ait Aoudia and "
        f"Hoydis {cite('aitaoudia')} learned OFDM receivers end to end and showed that pilots can be "
        f"reduced or removed. The open-source Sionna library {cite('sionna')} provides differentiable "
        "link-level simulation for such research."))

    story.append(P("2.6 Training and Evaluation Methods", "h2"))
    story.append(P(
        f"Residual connections {cite('resnet')} let a network learn a correction to its input, which suits "
        f"refining an existing LS estimate. Adam {cite('adam')} is the standard optimiser. For Monte Carlo "
        f"BER results, the Wilson score interval {cite('brown')} gives reliable confidence intervals for "
        f"binomial proportions, and the “rule of three” {cite('hanley')} bounds the true error "
        "rate when no errors are observed. Time-varying channels are commonly modelled with the Jakes "
        f"Doppler spectrum {cite('jakes')}."))

    story.append(P("2.7 Summary of Key Works", "h2"))
    rows = [["Ref.", "Approach", "Setting", "Key finding / relevance"]]
    summary = [
        ("vandebeek", "LS vs LMMSE", "SISO-OFDM", "LMMSE wins at low SNR at high cost; NeuroMIMO's baselines"),
        ("coleri", "Pilot arrangements", "SISO-OFDM", "Comb pilots + interpolation; basis for pilot spacing study"),
        ("biguesh", "LS/LMMSE for MIMO", "MIMO training", "Estimator trade-offs and optimal training"),
        ("ye", "Fully connected DNN", "SISO-OFDM", "DNN matches LMMSE with fewer pilots"),
        ("soltani", "Image super-resolution CNN", "OFDM grid", "Treats pilots as an image; strong denoising"),
        ("neumann", "MMSE-structured network", "Generic", "Learned estimator close to MMSE, lower cost"),
        ("dong", "Deep CNN", "mmWave massive MIMO", "Exploits frequency/time correlation"),
        ("mashhadi", "Joint pilot design + DNN", "MIMO-OFDM", "Fewer pilots with learned placement"),
        ("aitaoudia", "End-to-end neural receiver", "OFDM", "Pilot reduction; full-receiver learning"),
    ]
    for key, approach, setting, finding in summary:
        rows.append([f"[{REF_NUM[key]}]", approach, setting, finding])
    story.append(booktabs(rows, [W * 0.08, W * 0.25, W * 0.20, W * 0.47], zebra=True, align_center_from=99))
    story.append(P("Table 1: Representative works and their relevance to this project.", "caption"))

    story.append(P("2.8 Research Gap and How NeuroMIMO Addresses It", "h2"))
    story += bullets([
        "<b>Few honest high-SNR results.</b> Many papers emphasise low-SNR gains. NeuroMIMO reports the "
        "full 0–30 dB range and shows that its DNN falls clearly behind LS above about 15 dB (an error floor).",
        "<b>Little statistical rigour.</b> NeuroMIMO attaches Wilson intervals to every BER point and uses "
        "the rule of three for zero-error points.",
        "<b>Generalisation is rarely tested.</b> NeuroMIMO evaluates mismatched delay profiles, a longer "
        "6-tap channel and different pilot spacings.",
        "<b>Hard to reproduce.</b> NeuroMIMO runs every estimator on identical channel realisations from "
        "fixed seeds, with an automated test suite and an interactive dashboard.",
    ])


def references(story, W):
    story.append(PageBreak())
    story.append(section("3. Reference Research Papers"))
    story.append(P(
        "These are real, published works, grouped by topic in the order they are cited. Use them as the "
        "reference list for your report and as a reading list."))
    note = Table([[Paragraph(
        "<b>Before you submit:</b> this list was compiled from memory, not from a live database search. "
        "Check each entry on IEEE Xplore or Google Scholar, confirm the volume, issue and page numbers, "
        "and add the DOI. Read at least the abstract of every paper you cite.", S["note"])]],
        colWidths=[W])
    note.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF6E5")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0A030")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [note, Spacer(1, 8)]

    groups = [
        ("MIMO and OFDM foundations", "telatar", "goldsmith"),
        ("Classical pilot-aided channel estimation", "vandebeek", "kay"),
        ("Deep learning for the physical layer", "oshea", "qin"),
        ("Deep learning channel estimation", "ye", "mashhadi"),
        ("Neural receivers and simulation tools", "honkala", "sionna"),
        ("Machine learning, statistics and standards", "resnet", "3gpp"),
    ]
    keys = [k for k, _ in REFERENCES]
    for title, first, last in groups:
        story.append(P(title, "h2"))
        for key in keys[keys.index(first): keys.index(last) + 1]:
            story.append(Paragraph(f"[{REF_NUM[key]}]&nbsp;&nbsp;{dict(REFERENCES)[key]}", S["ref"]))

    story.append(P("Suggested Reading Order", "h2"))
    story += bullets([
        f"<b>Start here:</b> {cite('ozdemir')} for a survey of OFDM channel estimation and "
        f"{cite('oshea')} for deep learning in the physical layer.",
        f"<b>Core baselines:</b> {cite('vandebeek', 'coleri', 'biguesh')}, which match NeuroMIMO's LS, "
        "LMMSE and comb-pilot design.",
        f"<b>Closest to this project:</b> {cite('ye', 'soltani', 'neumann')}.",
        f"<b>State of the art and future work:</b> {cite('mashhadi', 'honkala', 'aitaoudia', 'sionna')}.",
    ])


def sample_paper(story, W):
    sweep = load("snr_sweep_results.json")
    infer = load("inference_time_results.json")
    gen = load("generalization_results.json")
    rec = {a: by_snr(r) for a, r in sweep["records"].items()}
    bits = rec["LS"][0.0]["total_bits"]
    lat = infer["results"]
    six_tap = next((c for c in gen["conditions"] if c["num_channel_taps"] != 4), None)

    story.append(PageBreak())
    story.append(section("4. Sample Research Paper"))
    story.append(P(
        "A short paper in IEEE conference style, written from this project's own code and results. Use it "
        "as a starting draft: expand each section, add your own figures from <font face='%s'>backend/"
        "results/</font>, and put your name and institution in the author line." % MONO, "note"))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Residual Deep Learning for Pilot-Aided Channel Estimation in 2×2 MIMO-OFDM: "
                           "An Honest Benchmark Against LS and LMMSE", S["subtitle"]))
    story.append(Spacer(1, 4))
    story.append(P("<i>Author Name, Department, Institution, email</i>", "date"))
    story.append(Spacer(1, 8))
    story.append(P("<b>Abstract</b>", "h2"))
    story.append(Paragraph(
        "Accurate channel estimation is essential for MIMO-OFDM receivers. This paper evaluates a "
        "lightweight residual multilayer perceptron that refines the least-squares (LS) channel estimate "
        "of a 2×2 MIMO-OFDM link with 64 subcarriers and comb-type pilots. The network has 330,112 "
        f"parameters and is compared with LS and linear MMSE (LMMSE) on identical Rayleigh channel "
        f"realisations over 0–30 dB SNR, with {bits:,} bits per SNR point and 95% Wilson confidence "
        f"intervals. At 0 dB the network reaches {fmt_nmse(rec['DNN'][0.0])} NMSE, slightly better than LS "
        f"({fmt_nmse(rec['LS'][0.0])}) and close to LMMSE ({fmt_nmse(rec['MMSE'][0.0])}) without using "
        "channel statistics. "
        f"Above 15 dB it shows an error floor near {fmt_nmse(rec['DNN'][30.0])}, while LS reaches "
        f"{fmt_nmse(rec['LS'][30.0])} at 30 dB. Mean inference latency is {lat['DNN']['mean_ms']:.2f} ms "
        f"per frame on a CPU. We discuss the causes of the floor and directions to remove it.",
        S["abstract_body"]))
    story.append(P("<b><i>Index Terms</i></b>—channel estimation, deep learning, MIMO, OFDM, "
                   "residual network, least squares, MMSE.", "body"))

    story.append(P("I. Introduction", "h2"))
    story.append(P(
        f"MIMO-OFDM underpins 5G NR and Wi-Fi {cite('3gpp', 'hwang')}. Receivers estimate the channel from "
        f"pilots, classically with LS or LMMSE {cite('vandebeek', 'morelli')}. Deep learning estimators "
        f"{cite('ye', 'soltani', 'neumann')} promise LMMSE-like accuracy without explicit channel "
        "statistics, but results are often reported over limited SNR ranges without confidence intervals. "
        "This paper contributes: (i) a reproducible 2×2 MIMO-OFDM benchmark in which all estimators "
        "see identical channels; (ii) a residual MLP estimator trained with a leakage-free split; and "
        "(iii) a full-range evaluation of accuracy, reliability, latency and generalisation."))

    story.append(P("II. System Model", "h2"))
    story.append(P(
        "Each transmit antenna sends N = 64 subcarriers with a 16-sample cyclic prefix. After FFT, the "
        "signal on subcarrier k at receive antenna r is"))
    story.append(P("Y<sub>r</sub>[k] = ∑<sub>t</sub> H<sub>r,t</sub>[k] X<sub>t</sub>[k] + "
                   "W<sub>r</sub>[k]", "eq"))
    story.append(P(
        "where H<sub>r,t</sub>[k] is the frequency response of a 4-tap Rayleigh channel with an exponential "
        "power-delay profile and W is complex Gaussian noise. Transmit antenna 0 uses pilots on subcarriers "
        "{0, 16, 32, 48} and antenna 1 on {8, 24, 40, 56}, so pilots never overlap."))

    story.append(P("III. Channel Estimators", "h2"))
    story.append(P(
        "<b>LS</b> divides the received pilots by the known pilot symbols, "
        "Ĥ<sub>LS</sub>[p] = Y[p] / X[p], and interpolates to all subcarriers with a DFT method. "
        "<b>LMMSE</b> applies Ĥ = <b>R</b><sub>HP</sub>(<b>R</b><sub>PP</sub> + "
        "σ<sub>n</sub>²<b>I</b>)<super>−1</super>Ĥ<sub>LS</sub> using the exact channel "
        "correlation. The <b>residual DNN</b> computes"))
    story.append(P("Ĥ<sub>DNN</sub> = Ĥ<sub>LS</sub> + f<sub>θ</sub>(Ĥ<sub>LS</sub>)", "eq"))
    story.append(P(
        "where f<sub>θ</sub> is an MLP (512→256→128→256→512) with LayerNorm, GELU "
        f"and dropout {cite('resnet')}, trained with Adam {cite('adam')} on an MSE loss over 0–30 dB. "
        "Data are split by channel-realisation seed before feature extraction, so test channels are never "
        "seen during training."))

    story.append(P("IV. Simulation Setup", "h2"))
    setup = [
        ["Parameter", "Value"],
        ["Antennas / subcarriers / CP", "2×2 / 64 / 16"],
        ["Modulation", sweep["modulation"]],
        ["Channel", f"Rayleigh, {sweep['num_channel_taps']} taps, exponential PDP (decay {sweep['pdp_decay']})"],
        ["Pilot spacing", f"{sweep['pilot_spacing']} (4 pilots per transmit antenna)"],
        ["Monte Carlo trials", f"{sweep['num_trials_per_snr']} per SNR point ({bits:,} bits)"],
        ["SNR points", ", ".join(f"{s:.0f}" for s in sweep["snr_points"]) + " dB"],
        ["Equalizer", "MIMO MMSE"],
    ]
    story.append(booktabs(setup, [W * 0.35, W * 0.65], zebra=True, align_center_from=99))
    story.append(P("Table 2: Simulation parameters.", "caption"))

    story.append(P("V. Results", "h2"))
    rows = [["SNR", "LS NMSE", "LMMSE NMSE", "DNN NMSE", "LS BER", "DNN BER"]]
    for snr in (0.0, 10.0, 20.0, 30.0):
        rows.append([f"{snr:.0f} dB", fmt_nmse(rec["LS"][snr]), fmt_nmse(rec["MMSE"][snr]),
                     fmt_nmse(rec["DNN"][snr]), f"{rec['LS'][snr]['ber']:.4f}",
                     f"{rec['DNN'][snr]['ber']:.4f}"])
    story.append(booktabs(rows, [W * 0.12] + [W * 0.176] * 5, zebra=True))
    story.append(P("Table 3: Estimation accuracy and bit error rate (Rayleigh, QPSK).", "caption"))
    story.append(figure("nmse_vs_snr.png", "Fig. 1: NMSE versus SNR for all estimators.", W * 0.6))
    story.append(P(
        f"At low SNR the DNN denoises slightly better than LS and approaches LMMSE, without channel "
        f"statistics. "
        f"Above 15 dB its NMSE saturates near {fmt_nmse(rec['DNN'][30.0])}, so at 30 dB it makes "
        f"{rec['DNN'][30.0]['bit_errors']} bit errors against {rec['LS'][30.0]['bit_errors']} for LS. Mean "
        f"latency is {lat['LS']['mean_ms']:.2f} ms (LS), {lat['MMSE']['mean_ms']:.2f} ms (LMMSE) and "
        f"{lat['DNN']['mean_ms']:.2f} ms (DNN)."
        + (f" With a 6-tap channel all estimators degrade to about {six_tap['metrics']['LS']['nmse_db']:.1f} "
           "dB NMSE at 15 dB, because 4 pilots per antenna cannot resolve a 6-tap impulse response."
           if six_tap else "")))

    story.append(P("VI. Conclusion", "h2"))
    story.append(P(
        "A small residual MLP slightly beats LS and approaches LMMSE at low SNR but has an error floor at "
        "high SNR when "
        "one model is trained across the whole SNR range. Future work: feed SNR as an input or train "
        f"per-SNR models, use 2D convolutional networks across time and frequency {cite('soltani', 'dong')}, "
        f"model Doppler with the Jakes spectrum {cite('jakes')}, and learn pilot placement "
        f"{cite('mashhadi')}."))
    story.append(P("<b>References:</b> use the numbered list in Section 3.", "note"))


BUILD_PROMPTS = [
    ("Prompt 1 — Project setup",
     "You are helping me build a final-year project called NeuroMIMO: a 2x2 MIMO-OFDM channel estimation "
     "simulator that compares Least Squares (LS), Linear MMSE and a PyTorch deep neural network, with a "
     "FastAPI back end and a React dashboard.\n\n"
     "Create the folder structure: backend/neuromimo/ with subpackages wireless/, estimation/, evaluation/, "
     "storage/ and api/, backend/tests/, backend/models/, backend/results/, and frontend/. Add "
     "backend/requirements.txt (fastapi, uvicorn, pydantic, numpy, scipy, torch, scikit-learn, matplotlib, "
     "pytest, httpx) and a config.py with dataclasses for SimulationConfig (num_tx=2, num_rx=2, fft_size=64, "
     "cp_length=16, pilot_spacing=8, modulation, channel_model, snr_db, num_ofdm_symbols=14, random_seed=42) "
     "and enums for modulation (QPSK, 16QAM), channel model (AWGN, RAYLEIGH) and algorithm (PERFECT, LS, "
     "MMSE, DNN). Explain each file in simple English."),
    ("Prompt 2 — Modulation",
     "In backend/neuromimo/wireless/modulation.py, implement Gray-coded QPSK and 16-QAM modulators and hard "
     "demodulators with unit average symbol energy, a function to generate random bits from a seed, and "
     "get_modulator(mod_type). Write pytest tests that check bits -> symbols -> bits is lossless with no "
     "noise and that the average symbol energy is 1."),
    ("Prompt 3 — OFDM with comb pilots",
     "In wireless/ofdm.py, implement an OFDMPipeline for 64 subcarriers and a 16-sample cyclic prefix. "
     "Use orthogonal comb pilots: transmit antenna 0 uses subcarriers {0,16,32,48}, antenna 1 uses "
     "{8,24,40,56}, and each antenna is silent on the other's pilots. Implement IFFT + CP insertion at the "
     "transmitter and CP removal + FFT at the receiver, vectorised with NumPy. Add tests that a noiseless, "
     "identity channel returns the original grid."),
    ("Prompt 4 — Channel models",
     "In wireless/channel.py, implement a WirelessChannel class with AWGN and a 4-tap Rayleigh multipath "
     "channel with an exponential power-delay profile (configurable decay and number of taps), independent "
     "for every transmit/receive antenna pair, block fading per frame, reproducible from a seed. Return the "
     "true frequency response H with shape (num_rx, num_tx, 64). Add noise at a requested SNR in dB. Test "
     "that the average channel power is 1 and that the measured SNR matches the requested SNR."),
    ("Prompt 5 — LS and LMMSE estimators",
     "In estimation/, create an abstract BaseChannelEstimator, then LSEstimator (H_LS = Y/X on pilots, "
     "then DFT-based interpolation to all 64 subcarriers) and MMSEEstimator (H = R_HP (R_PP + sigma^2 I)^-1 "
     "H_LS using the exact correlation of the exponential power-delay profile). Add tests that LS is exact "
     "without noise and that LMMSE beats LS on NMSE at 0 dB SNR."),
    ("Prompt 6 — Equalisation and the end-to-end pipeline",
     "In wireless/equalization.py, implement zero-forcing and MMSE MIMO equalisers. In "
     "wireless/simulation.py, build MIMOSimulationPipeline that runs bits -> modulation -> OFDM -> channel "
     "-> noise -> OFDM demodulation -> channel estimation -> equalisation -> demodulation, and returns "
     "NMSE, BER, SER, execution time and samples for plotting (constellation points and |H|). In "
     "evaluation/metrics.py add MSE, NMSE, NMSE in dB, BER, SER, and a 95% Wilson confidence interval with "
     "the rule of three when there are zero errors."),
    ("Prompt 7 — Residual DNN estimator and training",
     "In estimation/dnn.py, create ChannelEstimationNet: an MLP 512 -> 256 -> 128 -> 256 -> 512 with "
     "LayerNorm, GELU and dropout 0.05, used as a residual: H_DNN = H_LS + f(H_LS). Inputs and outputs are "
     "the real and imaginary parts of the 2x2x64 channel flattened to 512 values. In estimation/trainer.py, "
     "generate a dataset over SNR 0-30 dB, split it by channel-realisation seed into train/validation/test "
     "BEFORE extracting features (no data leakage), and train with Adam, MSE loss, a learning-rate "
     "scheduler and best-validation checkpointing to backend/models/neuromimo_dnn.pt. Add a "
     "DNNEstimator wrapper and a command-line trainer (train_cli.py)."),
    ("Prompt 8 — Experiments and figures",
     "In evaluation/experiments.py, create an ExperimentRunner that runs, on identical channel realisations "
     "for every estimator: an SNR sweep 0-30 dB, an AWGN vs Rayleigh comparison, a generalisation test "
     "(power-delay-profile decay 0.8/1.5/2.5 and a 6-tap channel), a pilot-spacing study (4/8/16) and an "
     "inference-time benchmark. Save JSON and CSV results and 300 DPI Matplotlib figures to "
     "backend/results/. Add run_experiments_cli.py with --trials, --quick and --seed options."),
    ("Prompt 9 — REST API and database",
     "In api/main.py, build a FastAPI app with Pydantic schemas and these endpoints: GET /api/health, GET "
     "/api/config, POST /api/simulation/run, POST /api/estimation/compare, POST /api/model/train "
     "(synchronous or background thread, 409 if a job is already running), GET /api/model/status, GET "
     "/api/model/train/status, POST /api/model/predict, GET /api/experiments, GET /api/experiments/{id}, "
     "GET /api/experiments/{id}/plots and GET /api/experiments/benchmark/snr-sweep. Store runs in SQLite "
     "(storage/database.py). Read allowed CORS origins from NEUROMIMO_CORS_ORIGINS. Write API tests with "
     "TestClient, and make sure tests save any trained model to a temporary folder."),
    ("Prompt 10 — React dashboard",
     "Create a Vite + React + TypeScript + Tailwind + Recharts front end in frontend/ with a typed API "
     "client (src/api/client.ts) and a Vite proxy from /api to http://127.0.0.1:8000. Build a navbar with "
     "API status, a sidebar, and pages: Overview, MIMO-OFDM Simulator, Channel Estimation Lab, ML Model "
     "Training (live loss curve), Performance Comparison (NMSE and BER charts, latency, summary cards "
     "computed from the data, never hard-coded), Signal Visualization (IQ constellation, channel "
     "frequency response, power-delay profile), Experiment History (table with CSV export) and About. "
     "Use a dark theme."),
]

FEATURE_PROMPTS = [
    ("Feature 1 — Remove the DNN high-SNR error floor",
     "In NeuroMIMO, the residual DNN estimator saturates near -25 dB NMSE above 15 dB SNR while LS keeps "
     "improving. Add the SNR (in dB, normalised) as an extra input feature to ChannelEstimationNet, retrain, "
     "and compare against the current model with the SNR sweep experiment. Keep the old checkpoint loadable. "
     "Report the NMSE at 20, 25 and 30 dB before and after."),
    ("Feature 2 — 2D CNN estimator",
     "Add a new estimator, CNNEstimator, that treats the channel as an image over subcarriers and OFDM "
     "symbols (in the style of ChannelNet: a super-resolution network followed by a denoising network). "
     "Add it to the algorithm enum, the API, the comparison page and all experiments, and add unit tests."),
    ("Feature 3 — Doppler and time-varying channels",
     "Extend WirelessChannel with a time-varying Rayleigh channel using the Jakes Doppler spectrum, "
     "configurable by maximum Doppler frequency (for example 0, 100, 300 Hz) and subcarrier spacing. Add a "
     "Doppler experiment that plots NMSE and BER versus Doppler for all estimators at 20 dB SNR, and a "
     "Doppler slider on the Simulator page."),
    ("Feature 4 — Larger MIMO configurations",
     "Generalise the simulator, estimators and DNN input size from 2x2 to NxM MIMO (support 2x2, 4x4 and "
     "8x8) with orthogonal comb pilots for every transmit antenna. Update the API schema, the antenna "
     "selector on the Simulator page, and add tests for 4x4."),
    ("Feature 5 — 16-QAM and 64-QAM DNN models",
     "Train and store separate DNN checkpoints per modulation (QPSK, 16-QAM, 64-QAM; add 64-QAM to the "
     "modulation module). Let the API pick the checkpoint that matches the request, and show which model "
     "was used on the Channel Estimation Lab page."),
    ("Feature 6 — Learned pilot placement",
     "Add an experiment that compares fixed comb pilots with a pilot pattern chosen by a simple search "
     "(for example, greedy selection that minimises validation NMSE) for 2, 4 and 8 pilots per antenna. "
     "Plot NMSE versus number of pilots for LS, LMMSE and the DNN."),
    ("Feature 7 — PDF report export",
     "Add a 'Download report' button on the Performance Comparison page that calls a new endpoint "
     "GET /api/report.pdf. The endpoint builds a PDF (with ReportLab) containing the summary cards, the "
     "NMSE and BER tables and the figures from backend/results/."),
    ("Feature 8 — Docker and one-command start",
     "Add a Dockerfile for the back end, a Dockerfile for the front end (build with Vite, serve with nginx, "
     "proxy /api to the back end) and a docker-compose.yml so `docker compose up` starts the whole app on "
     "http://localhost:8080. Document it in the README."),
    ("Feature 9 — Continuous integration",
     "Add a GitHub Actions workflow that, on every push and pull request, installs Python 3.12 dependencies "
     "and runs pytest on backend/tests, then installs Node 22 and runs npm ci, npm run lint and npm run build "
     "in frontend/. Cache pip and npm."),
    ("Feature 10 — Hyperparameter search page",
     "Add a page that launches a small grid search over learning rate, batch size and hidden layer sizes "
     "for the DNN as a background job, streams progress like the training page, and shows a sortable "
     "results table with the best configuration highlighted."),
]


def prompts(story, W):
    story.append(PageBreak())
    story.append(section("5. Prompts to Build and Extend the Project"))
    story.append(P(
        "These prompts are written for an AI coding assistant such as Claude Code. Use them one at a time, "
        "in order. After each prompt, run the tests, read the code, and make sure you understand it before "
        "moving on; you will be asked about it in your viva."))
    story.append(P("How to Use These Prompts", "h2"))
    story += bullets([
        "Give one prompt per conversation turn. Paste the error message back if something fails.",
        "Ask the assistant to explain anything you do not understand, in simple English.",
        f"After each step run {mono('python -m pytest backend/tests -q')} (and "
        f"{mono('npm run build')} for front-end steps).",
        "Commit to git after every working step so you can go back if something breaks.",
    ])
    story.append(P("Part A: Build the Project from Scratch", "h2"))
    for title, text in BUILD_PROMPTS:
        story.append(prompt_box(title, text, W))
    story.append(PageBreak())
    story.append(P("Part B: Add New Features", "h2"))
    story.append(P("Each prompt assumes the finished project from Part A (or this repository) is open."))
    for title, text in FEATURE_PROMPTS:
        story.append(prompt_box(title, text, W))


def build():
    doc = ResearchPackTemplate(OUTPUT, title="NeuroMIMO Research Pack", author="NeuroMIMO",
                               subject="Problem statement, literature survey, references and prompts")
    W = doc.width
    story = [
        Spacer(1, 50 * mm),
        P("NeuroMIMO", "title"),
        Spacer(1, 6),
        P("R<font size='12'>ESEARCH</font> P<font size='12'>ACK</font>", "subtitle"),
        Spacer(1, 22 * mm),
        P("Problem Statement • Literature Survey • Reference Papers • "
          "Sample Paper • Build &amp; Feature Prompts", "tag"),
        Spacer(1, 22 * mm),
        P("Companion to the NeuroMIMO project documentation: deep learning-assisted channel estimation "
          "for 2×2 MIMO-OFDM systems.", "abstract"),
        Spacer(1, 80 * mm),
        P(date.today().strftime("%B %d, %Y").replace(" 0", " "), "date"),
        NextPageTemplate("toc"),
        PageBreak(),
    ]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc0", fontName=BODY, fontSize=10.5, leading=15,
                                      textColor=LINK_BLUE, leftIndent=10)]
    story += [Spacer(1, 25 * mm), P("Contents", "toc_title"), toc, NextPageTemplate("main"), PageBreak()]

    problem_statement(story, W)
    literature_survey(story, W)
    references(story, W)
    sample_paper(story, W)
    prompts(story, W)

    doc.multiBuild(story)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
