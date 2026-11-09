"""Publication figures (PNG) from results/*. Colors: validated reference palette slots 1-3."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
R, F = Path("results"), Path("figures"); F.mkdir(exist_ok=True)
COL = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6, "lines.linewidth": 2})
cur = json.loads((R / "curves.json").read_text())
mc = pd.read_csv(R / "model_comparison.csv").set_index("model")
algo = "GradBoost"
fig, axs = plt.subplots(1, 3, figsize=(12, 3.8))
for s in "ABC":
    k = f"{s}_{algo}"; c = cur[k]; lab = f"Model {s} (AUC {mc.loc[k,'roc_auc']:.3f})"
    axs[0].plot(c["roc"]["fpr"], c["roc"]["tpr"], color=COL[s], label=lab)
    axs[1].plot(c["pr"]["recall"], c["pr"]["precision"], color=COL[s], label=f"Model {s} (PR-AUC {mc.loc[k,'pr_auc']:.3f})")
    axs[2].plot(c["calibration"]["mean_pred"], c["calibration"]["frac_pos"], color=COL[s], marker="o", ms=4, label=f"Model {s} (Brier {mc.loc[k,'brier']:.4f})")
axs[0].plot([0, 1], [0, 1], ls="--", color=MUTED, lw=1); axs[2].plot([0, 1], [0, 1], ls="--", color=MUTED, lw=1)
axs[0].set(xlabel="False Positive Rate", ylabel="True Positive Rate", title="ROC (test, Gradient Boosting)")
axs[1].set(xlabel="Recall", ylabel="Precision", title="Precision–Recall (test)")
axs[2].set(xlabel="Болжанған PD", ylabel="Нақты дефолт үлесі", title="Calibration (test)")
for a in axs: a.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(F / "roc_pr_calibration.png", dpi=180); plt.close(fig)

# AUC with CI by set & algorithm
fig, ax = plt.subplots(figsize=(7, 3.6))
algos = ["LogReg", "RandomForest", "GradBoost"]; w = .26
for i, s in enumerate("ABC"):
    xs = [j + (i - 1) * w for j in range(3)]
    v = [mc.loc[f"{s}_{a}", "roc_auc"] for a in algos]
    lo = [v[j] - mc.loc[f"{s}_{a}", "roc_auc_ci_lo"] for j, a in enumerate(algos)]
    hi = [mc.loc[f"{s}_{a}", "roc_auc_ci_hi"] - v[j] for j, a in enumerate(algos)]
    ax.bar(xs, v, w * .92, color=COL[s], label=f"Model {s}", yerr=[lo, hi], ecolor=INK, capsize=3)
ax.set_xticks(range(3)); ax.set_xticklabels(["Logistic Regression", "Random Forest", "Gradient Boosting"])
ax.set_ylim(.65, .82); ax.set_ylabel("ROC-AUC (test, 95% CI)"); ax.legend(frameon=False, ncol=3)
ax.set_title("Ақпарат көлемі × алгоритм")
fig.tight_layout(); fig.savefig(F / "auc_by_set_algo.png", dpi=180); plt.close(fig)

# DVF
sd = pd.read_csv(R / "dvf_subsets.csv"); fr = pd.read_csv(R / "dvf_frontier.csv"); fr = fr[fr.scenario == "base"]
n = 4500
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.scatter(sd.n_fields, sd.test_gross_value_base / n, s=28, color="#a8a7a2", label="64 ақпарат комбинациясы", zorder=2)
ax.step(fr.max_fields, fr.test_gross_value_per_client, where="post", color=COL["A"], label="Data Value Frontier (validation бойынша таңдалған)", zorder=3)
for s, nm in (("S0", "A"), ("G1+G2+G3", "B"), ("G1+G2+G3+G4+G5+G6", "C")):
    r = sd[sd.subset == s].iloc[0]
    ax.scatter(r.n_fields, r.test_gross_value_base / n, s=80, color=COL[nm], edgecolor="white", linewidth=2, zorder=4)
    ax.annotate(f"Model {nm}", (r.n_fields, r.test_gross_value_base / n), textcoords="offset points", xytext=(6, 8), color=INK)
ax.set(xlabel="Пайдаланылған шикі өрістер саны (құпиялық жүктемесі)", ylabel="Π(S) − Π(S₀), NT$ / клиент (test)",
       title="Data Value Frontier — базалық сценарий (m=10%, LGD=75%)")
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(F / "dvf_frontier.png", dpi=180); plt.close(fig)

# sensitivity
se = pd.read_csv(R / "sensitivity_margin_lgd.csv")
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for a, col, t in ((axs[0], "value_B_vs_A_per_client", "B − A қосымша құны"), (axs[1], "value_C_vs_B_per_client", "C − B қосымша құны")):
    for lgd, c in zip((0.45, 0.60, 0.75, 0.90), ("#9ec5f0", "#5d9ee6", "#2a78d6", "#154a8a")):
        d = se[se.lgd == lgd]; a.plot(d.margin * 100, d[col], color=c, marker="o", ms=4, label=f"LGD {int(lgd*100)}%")
    a.axhline(0, color=INK, lw=1); a.set(xlabel="Маржа m, %", title=t)
axs[0].set_ylabel("NT$ / клиент (test, Gradient Boosting)"); axs[1].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(F / "sensitivity.png", dpi=180); plt.close(fig)
print("ok")
