import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
fig, ax = plt.subplots(figsize=(11, 4.2)); ax.set_xlim(0, 110); ax.set_ylim(0, 42); ax.axis("off")
INK, BLUE, LB, GR = "#0F1B2D", "#2563EB", "#EEF4FF", "#E6EAF0"
def box(x, y, w, h, title, lines, fc=LB, ec=BLUE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w/2, y + h - 3, title, ha="center", va="top", fontsize=10.5, weight="bold", color=INK)
    for i, l in enumerate(lines): ax.text(x + w/2, y + h - 8.2 - i*3.6, l, ha="center", va="top", fontsize=8.6, color="#3B4659")
def arr(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, color=BLUE, lw=1.6))
box(1, 14, 18, 22, "1. Деректер", ["ҚНРДА, ҰБ, ПКБ, БНС", "мөлшерлеме, NPL, қарыз", "клиенттік жиын: 30 000", "70 / 15 / 15"], fc="#FFFFFF", ec="#94A3B8")
box(23, 14, 19, 22, "2. Ақпарат топтары", ["S₀ = LIMIT_BAL, PAY_0", "+ G1 … G6", "A (2) · B (6) · C (19)", "2⁶ = 64 комбинация"])
box(46, 14, 19, 22, "3. PD модельдері", ["Logistic Regression", "Random Forest", "Gradient Boosting", "ROC/PR-AUC, Brier, CI"])
box(69, 14, 19, 22, "4. Қаржы қозғалтқышы", ["m = r − f (ҚНРДА)", "EAD (₸), LGD", "шешім: PD < t", "Π(S), C(S)"])
box(92, 14, 17, 22, "5. DVF", ["V(S) = Π − Π₀ − C", "оңтайлы жиынтық", "фронтир", "3 сценарий (₸)"], fc="#DBEAFE")
for x in (19.8, 42.8, 65.8, 88.8): arr(x, 25, x + 2.6, 25)
ax.add_patch(FancyBboxPatch((23, 1.5), 86, 8, boxstyle="round,pad=0.4,rounding_size=1.6", fc="#FFFFFF", ec=GR, lw=1.2))
ax.text(66, 5.5, "Streamlit прототипі: Dashboard · Credit Risk Lab · DVF · Financial Simulator · Privacy & Consent · Қазақстан сценарийлері · Research Results",
        ha="center", va="center", fontsize=9.2, color=INK)
arr(100, 13.6, 100, 10.2)
ax.text(1, 41, "Validation: гиперпараметр, шек, оңтайлы жиынтық таңдалады   |   Test: тек соңғы бағалау", fontsize=8.8, color="#5B6577")
fig.tight_layout(); fig.savefig("figures/architecture.png", dpi=200); print("ok")
