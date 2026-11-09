"""Figure 7 (paper): Kazakhstan financial scenarios — GB model profit by information set and KZ DVF frontier."""
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
COL = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6, "lines.linewidth": 2})
R = Path(__file__).resolve().parent / "results"; F = Path(__file__).resolve().parent / "figures"
m = pd.read_csv(R / "kz_models.csv"); fr = pd.read_csv(R / "kz_frontier.csv")
sc = [("KZ1_base", "1 — базалық"), ("KZ2_high_risk", "2 — жоғары\nтәуекел"), ("KZ3_data_cost", "3 — деректер\nқұны жоғары")]
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.8))
g = m[m.algo == "GradBoost"]
for i, s in enumerate("ABC"):
    v = [g[(g.scenario == k) & (g.set == s)].profit_pc_kzt.iloc[0] for k, _ in sc]
    axs[0].bar([j + (i - 1) * .27 for j in range(3)], v, .25, color=COL[s], label=f"Model {s}")
axs[0].axhline(0, color=INK, lw=1); axs[0].set_xticks(range(3)); axs[0].set_xticklabels([l for _, l in sc])
axs[0].set_ylabel("Π, ₸ / клиент (test, GB)"); axs[0].set_title("а) Модельдік пайда (деректер шығынынсыз)", fontsize=10)
axs[0].legend(frameon=False, fontsize=8)
for (k, l), c in zip(sc, ["#2a78d6", "#eb6834", "#1baf7a"]):
    d = fr[fr.scenario == k]
    axs[1].step(d.max_fields, d.test_net_value_pc_kzt, where="post", color=c, label=l.replace("\n", " "))
axs[1].axhline(0, color=INK, lw=1); axs[1].set(xlabel="Өрістер бюджеті k", ylabel="V(S*), ₸ / клиент (test)")
axs[1].set_title("ә) Data Value Frontier, Қазақстан сценарийлері", fontsize=10); axs[1].legend(frameon=False, fontsize=8, loc="center right", bbox_to_anchor=(1, .62)); axs[1].set_xticks(range(2, 20, 2))
fig.tight_layout(); fig.savefig(F / "kz_scenarios.png", dpi=180); plt.close(fig)
print("ok")
