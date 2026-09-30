"""PRISMA 2020 flow diagram — Restart v6 (locked 30 Sep 2026).

Locked numbers (see reports/prisma.diagram.md):
  Identification: Databases 740, Registers 0
    removed before screening: duplicates 0, automation 0, other-reasons 565
  Screening: screened 175, excluded 105 (OLD-48 / E1-21 / E2-20 / E3-16),
    sought 70, not retrieved 45 (E5-4 + standby-41), assessed 25
  Eligibility: assessed 25, excluded 16 (E3-4 / E2-2 / E4-2 / E1-1 / backup-7)
  Included: studies 9, reports 9.
Arithmetic: 740=565+175 | 175=105+70 | 70=45+25 | 25=16+9.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# Locked counts — edit here only if re-screening changes them.
N_DB = 740
N_REG = 0
N_DUP, N_AUTO, N_OTHER = 0, 0, 565
N_SCREENED, N_EXCLUDED_SCR = 175, 105
N_SOUGHT, N_NOT_RETRIEVED, N_ASSESSED = 70, 45, 25
N_EXCLUDED_ELIG, N_INCLUDED = 16, 9

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
    fig, ax = plt.subplots(figsize=(15, 20), dpi=300)
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

    # Title
    ax.text(50, 97.8, "DIAGRAM ALIR PRISMA 2020 — IDENTIFICATION OF STUDIES VIA DATABASES AND REGISTERS",
            fontsize=14, fontweight="bold", color="#0F172A", ha="center", va="center")
    ax.text(50, 96.1, "Utah FORGE Well 56-32 sensor clustering review  |  Scopus Q-RAW v6 (4-block) + Q-FILTERED OA/journal/English/article",
            fontsize=10, fontstyle="italic", color="#334155", ha="center", va="center")
    ax.plot([5, 95], [94.9, 94.9], color="#CBD5E1", lw=1.5)

    # ---------------- TAHAP 1: IDENTIFICATION (y 76–94) ----------------
    draw_phase_banner(76, 18, "TAHAP 1", "IDENTIFIKASI", "Identification")
    draw_box(18, 76, 41, 18, c_main_box, c_main_border)
    ax.text(38.5, 92.4, "RECORDS IDENTIFIED FROM*", fontsize=11, fontweight="bold",
            color=c_main_header, ha="center")
    ax.text(20, 85.5,
            f"• Databases (Scopus Q-RAW v6, no filter)\n     n = {N_DB}\n\n"
            f"• Registers\n     n = {N_REG}",
            fontsize=9.5, color=c_text_dark, va="center", linespacing=1.5)
    ax.text(20, 78.6, f"→ Records screened: n = {N_DB + N_REG - N_DUP - N_AUTO - N_OTHER}",
            fontsize=9.5, fontweight="bold", color=c_main_header, va="center")

    draw_box(63, 76, 34, 18, c_excl_box, c_excl_border)
    ax.text(80, 92.4, "RECORDS REMOVED BEFORE SCREENING", fontsize=10, fontweight="bold",
            color=c_excl_header, ha="center")
    ax.text(64.5, 84.5,
            f"• Duplicate records removed: n = {N_DUP}\n"
            f"   (DOI + EID check: 0 duplicates)\n\n"
            f"• Marked as ineligible by automation: n = {N_AUTO}\n"
            f"   (manual screening, no auto-exclude)\n\n"
            f"• Removed for other reasons: n = {N_OTHER}\n"
            f"   (Scopus filters: non-OA + non-journal\n"
            f"    + non-English + non-article)",
            fontsize=8.6, color=c_text_dark, va="center", linespacing=1.35)
    arrow_right(59, 63, 85)
    arrow_down(38.5, 76, 71.5)

    # ---------------- TAHAP 2: SCREENING (y 40–71.5) ----------------
    draw_phase_banner(40, 31.5, "TAHAP 2", "PENAPISAN", "Screening")
    draw_box(18, 40, 41, 31.5, c_main_box, c_main_border)
    ax.text(38.5, 69.7, "SCREENING FLOW", fontsize=11, fontweight="bold",
            color=c_main_header, ha="center")
    ax.text(20, 55.5,
            f"• Records screened: n = {N_SCREENED}\n\n"
            f"• Records excluded: n = {N_EXCLUDED_SCR}\n"
            f"   (Older-than-2021: 48 / E1 off-topic: 21 /\n"
            f"    E2 non-sensor: 20 / E3 no-method: 16)\n\n"
            f"• Reports sought for retrieval: n = {N_SOUGHT}\n"
            f"   (Include 55 + Maybe 15;\n"
            f"    Batch-1 direct-domain 28 + Batch-2 42)\n\n"
            f"• Reports not retrieved: n = {N_NOT_RETRIEVED}\n"
            f"   (E5 dead links 4 + Batch-2 standby 41)\n\n"
            f"• Reports assessed for eligibility: n = {N_ASSESSED}\n"
            f"   (Batch-1 24 + No.161 conditional 1)",
            fontsize=8.8, color=c_text_dark, va="center", linespacing=1.4)

    draw_box(63, 40, 34, 31.5, c_excl_box, c_excl_border)
    ax.text(80, 69.7, "REPORTS EXCLUDED (ELIGIBILITY)", fontsize=10, fontweight="bold",
            color=c_excl_header, ha="center")
    ax.text(80, 68.0, f"(Full-text review: n = {N_EXCLUDED_ELIG})", fontsize=8.5,
            fontstyle="italic", color=c_text_muted, ha="center")
    ax.text(64.5, 55.0,
            "• Reason 1 — E3 no clustering link: n = 4\n\n"
            "• Reason 2 — E2 not sensor time-series: n = 2\n\n"
            "• Reason 3 — E4 no preprocessing detail: n = 2\n\n"
            "• Reason 4 — E1 off-topic confirmed: n = 1\n\n"
            "• Reason 5 — backup-sufficiency standby: n = 7\n"
            "   (No.7/54/57/67/74/143/156, eligible)",
            fontsize=8.6, color=c_text_dark, va="center", linespacing=1.45)
    arrow_right(59, 63, 55.5)
    arrow_down(38.5, 40, 35.5)

    # ---------------- TAHAP 3: INCLUDED (y 4–35.5) ----------------
    draw_phase_banner(4, 31.5, "TAHAP 3", "INKLUSI", "Included")
    draw_box(18, 4, 79, 31.5, c_incl_box, c_incl_border, lw=2.2)
    ax.text(57.5, 33.4, f"STUDIES INCLUDED IN REVIEW: n = {N_INCLUDED}  |  REPORTS: n = {N_INCLUDED}",
            fontsize=11.5, fontweight="bold", color=c_incl_header, ha="center")
    ax.text(57.5, 31.7, "OA journal articles, English, 2021–2026 (syarat ≥ 8 TERLAMPUI)",
            fontsize=8.8, fontstyle="italic", color="#166534", ha="center")
    incl_text = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(INCLUDED_9))
    ax.text(20, 19, incl_text, fontsize=8.6, color="#14532D", va="center", linespacing=1.7)

    # Footer arithmetic check
    ax.text(50, 1.5,
            f"Check: {N_DB}={N_OTHER}+{N_SCREENED}  |  {N_SCREENED}={N_EXCLUDED_SCR}+{N_SOUGHT}  |  "
            f"{N_SOUGHT}={N_NOT_RETRIEVED}+{N_ASSESSED}  |  {N_ASSESSED}={N_EXCLUDED_ELIG}+{N_INCLUDED}",
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
