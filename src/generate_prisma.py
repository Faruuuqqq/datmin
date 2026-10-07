"""PRISMA 2020 flow diagram — funnel resmi 740-409-231-127-9 (query + PUBYEAR, 30 Sep 2026).

Locked numbers (see reports/prisma.diagram.md):
  Identification: Databases 740, Registers 0
    removed before screening: duplicates 0, automation 0, other 0
  Screening: screened 740, older-than-2021 331 -> sought 409,
    excluded language 20 + doctype 178 (overlap footnote) -> English articles 231,
    inaccessible 104 -> accessible 127 -> assessed 127,
    excluded theme/title/abstract 118 = Pass-1 57 + notretrieved/standby 45 + Pass-2 16
  Included: studies 9, reports 9.
Arithmetic: 740=331+409 | 409-178=231 (20 overlap) | 231=104+127 | 127=118+9.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

N_DB = 740
N_REG = 0
N_OLD, N_SOUGHT1 = 331, 409
N_LANG, N_DOCTYPE, N_ENGLISH = 20, 178, 231
N_INACCESS, N_ACCESS = 104, 127
N_EXCLUDED_THEME, N_INCLUDED = 118, 9

INCLUDED_9 = [
    "61. Geothermal time-series clustering (Geothermics 2026) — k-Means, SIL/DBI",
    "77. Drilling optimization + sliding window (PLOS ONE 2026)",
    "14. Unsupervised wellbore deviation (Front. AI 2026)",
    "60. STADe sliding-windows oil&gas (IJ CIP 2025)",
    "79. Geothermal steam SSA anomaly (Eng. Proc. 2025)",
    "131. 3W Petrobras flow DNN (Geoenergy 2024)",
    "80. Permian profiles, elbow+CH (EEE 2026)",
    "12. Drilling AE segmentation (JAMDSM 2023)",
    "161. Kazakhstan oil-well K-Means, Elbow K=10 (SOCAR 2026)",
]


def create_prisma_diagram():
    fig, ax = plt.subplots(figsize=(15, 22), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    c_phase_bg, c_phase_txt = "#1E3A8A", "#FFFFFF"
    c_main_box, c_main_border, c_main_header = "#F8FAFC", "#2563EB", "#1E40AF"
    c_excl_box, c_excl_border, c_excl_header = "#FFF1F2", "#E11D48", "#9F1239"
    c_incl_box, c_incl_border, c_incl_header = "#F0FDF4", "#16A34A", "#15803D"
    c_text_dark, c_text_muted, c_arrow = "#0F172A", "#475569", "#334155"

    def draw_box(x, y, w, h, bg, border, lw=1.8, r=1.5):
        ax.add_patch(patches.FancyBboxPatch(
            (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
            facecolor=bg, edgecolor=border, linewidth=lw, zorder=2))

    def draw_phase_banner(y_bottom, height, phase_id, title_id, title_en):
        draw_box(2, y_bottom, 14, height, c_phase_bg, c_phase_bg, lw=1, r=1.2)
        mid = y_bottom + height / 2
        ax.text(6.2, mid, phase_id.upper(), color=c_phase_txt,
                fontsize=12, fontweight="bold", ha="center", va="center", rotation=90)
        ax.text(11.2, mid, f"{title_id}\n({title_en})",
                color="#93C5FD", fontsize=8, fontweight="semibold",
                ha="center", va="center", rotation=90, multialignment="center")

    def arrow_down(x, y_from, y_to):
        ax.annotate("", xy=(x, y_to), xytext=(x, y_from),
                    arrowprops=dict(arrowstyle="->", color=c_arrow, lw=2, mutation_scale=15))

    def arrow_right(x_from, x_to, y):
        ax.annotate("", xy=(x_to, y), xytext=(x_from, y),
                    arrowprops=dict(arrowstyle="->", color=c_arrow, lw=2, mutation_scale=15))

    ax.text(50, 97.8, "DIAGRAM ALIR PRISMA 2020 — IDENTIFICATION OF STUDIES VIA DATABASES AND REGISTERS",
            fontsize=14, fontweight="bold", color="#0F172A", ha="center", va="center")
    ax.text(50, 96.1, "Utah FORGE Well 56-32 sensor clustering review  |  Scopus Q-RAW v6 4-block + PUBYEAR 2021–2026 + OA/journal/English/article",
            fontsize=10, fontstyle="italic", color="#334155", ha="center", va="center")
    ax.plot([5, 95], [94.9, 94.9], color="#CBD5E1", lw=1.5)

    # ---------------- TAHAP 1: IDENTIFICATION (y 78–94) ----------------
    draw_phase_banner(78, 16, "TAHAP 1", "IDENTIFIKASI", "Identification")
    draw_box(18, 78, 41, 16, c_main_box, c_main_border)
    ax.text(38.5, 92.4, "RECORDS IDENTIFIED FROM*", fontsize=11, fontweight="bold",
            color=c_main_header, ha="center")
    ax.text(20, 86.5,
            f"• Databases (Scopus Q-RAW v6)\n     n = {N_DB}\n\n"
            f"• Registers\n     n = {N_REG}",
            fontsize=9.5, color=c_text_dark, va="center", linespacing=1.5)
    ax.text(20, 80.0, f"→ Records screened: n = {N_DB}",
            fontsize=9.5, fontweight="bold", color=c_main_header, va="center")

    draw_box(63, 78, 34, 16, c_excl_box, c_excl_border)
    ax.text(80, 92.4, "RECORDS REMOVED BEFORE SCREENING", fontsize=10, fontweight="bold",
            color=c_excl_header, ha="center")
    ax.text(64.5, 85.5,
            "• Duplicate records removed: n = 0\n"
            "   (DOI + EID check: 0 duplicates)\n\n"
            "• Marked as ineligible by automation: n = 0\n"
            "   (manual screening, no auto-exclude)\n\n"
            "• Removed for other reasons: n = 0",
            fontsize=8.8, color=c_text_dark, va="center", linespacing=1.4)
    arrow_right(59, 63, 86)
    arrow_down(38.5, 78, 74)

    # ---------------- TAHAP 2: SCREENING (y 34–74) ----------------
    draw_phase_banner(34, 40, "TAHAP 2", "PENAPISAN", "Screening")
    draw_box(18, 34, 41, 40, c_main_box, c_main_border)
    ax.text(38.5, 72.2, "SCREENING FLOW", fontsize=11, fontweight="bold",
            color=c_main_header, ha="center")
    ax.text(20, 53.5,
            f"• Records screened: n = {N_DB}\n\n"
            f"• Records excluded older than 2021: n = {N_OLD}\n"
            f"   → Reports sought for retrieval: n = {N_SOUGHT1}\n\n"
            f"• Records Exclude:\n"
            f"   - Language Non-English: n = {N_LANG}*\n"
            f"   - Document type Non-Article: n = {N_DOCTYPE}*\n"
            f"   → English-language articles: n = {N_ENGLISH}\n\n"
            f"• Records inaccessible: n = {N_INACCESS}\n"
            f"   → Fully accessible records: n = {N_ACCESS}\n\n"
            f"• Reports assessed for eligibility: n = {N_ACCESS}\n"
            f"   *20 non-English overlap di dalam 178",
            fontsize=8.6, color=c_text_dark, va="center", linespacing=1.4)

    draw_box(63, 34, 34, 40, c_excl_box, c_excl_border)
    ax.text(80, 72.2, "REPORTS EXCLUDED (THEME)", fontsize=10, fontweight="bold",
            color=c_excl_header, ha="center")
    ax.text(80, 70.5, f"(n = {N_EXCLUDED_THEME} dari {N_ACCESS} assessed)",
            fontsize=8.5, fontstyle="italic", color=c_text_muted, ha="center")
    ax.text(64.5, 53.0,
            "Record excluded based on theme,\n"
            "title, abstract, subject specific:\n\n"
            "• Pass-1 title/abstract: n = 57\n"
            "   (E1 off-topic 21 / E2 non-sensor 20 /\n"
            "    E3 no-method 16)\n\n"
            "• Not retrieved + standby: n = 45\n"
            "   (E5 dead links 4 + Batch-2 standby 41)\n\n"
            "• Pass-2 full-text: n = 16\n"
            "   (E3 4 / E2 2 / E4 2 / E1 1 / backup 7)",
            fontsize=8.6, color=c_text_dark, va="center", linespacing=1.45)
    arrow_right(59, 63, 53.5)
    arrow_down(38.5, 34, 30)

    # ---------------- TAHAP 3: INCLUDED (y 2–30) ----------------
    draw_phase_banner(2, 28, "TAHAP 3", "INKLUSI", "Included")
    draw_box(18, 2, 79, 28, c_incl_box, c_incl_border, lw=2.2)
    ax.text(57.5, 28.0, f"STUDIES INCLUDED IN REVIEW: n = {N_INCLUDED}  |  REPORTS: n = {N_INCLUDED}",
            fontsize=11.5, fontweight="bold", color=c_incl_header, ha="center")
    ax.text(57.5, 26.4, "OA journal articles, English, 2021–2026 (syarat ≥ 8 TERLAMPUI)",
            fontsize=8.8, fontstyle="italic", color="#166534", ha="center")
    incl_text = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(INCLUDED_9))
    ax.text(20, 15, incl_text, fontsize=8.6, color="#14532D", va="center", linespacing=1.7)

    ax.text(50, 0.4,
            f"Check: {N_DB}={N_OLD}+{N_SOUGHT1} | {N_SOUGHT1}-{N_DOCTYPE}={N_ENGLISH} | "
            f"{N_ENGLISH}={N_INACCESS}+{N_ACCESS} | {N_ACCESS}={N_EXCLUDED_THEME}+{N_INCLUDED}",
            fontsize=8, color=c_text_muted, ha="center", va="center")

    outdir = Path(__file__).resolve().parent.parent / "figures"
    outdir.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf", "svg"):
        p = outdir / f"prisma_flowchart_restart_v6.{suffix}"
        if suffix == "png":
            plt.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
        else:
            plt.savefig(p, bbox_inches="tight", facecolor="white")
        print("saved:", p)
    plt.close()


if __name__ == "__main__":
    create_prisma_diagram()
