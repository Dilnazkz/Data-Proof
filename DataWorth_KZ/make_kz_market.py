"""Kazakhstan retail credit market figures from published ARDFM statistics (values typed from releases; sources in paper)."""
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np, pandas as pd
F = Path(__file__).resolve().parent / "figures"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"; C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6, "lines.linewidth": 2})
# (a) retail loans, trn KZT (1.1.2024 and 1.1.2025 back-calculated from ARDFM annual growth rates 23.9% and 19.8%)
port = pd.DataFrame({"date": ["01.01.2024*", "01.01.2025*", "01.01.2026", "01.08.2026", "01.10.2026"], "retail": [16.7, 20.7, 24.8, 26.1, 26.7],
                     "consumer": [np.nan, 13.8, 16.7, 17.4, 17.7]})
# (b) NPL90+, %
npl = pd.DataFrame([("2024-01-01", 2.9, 3.4, np.nan), ("2025-01-01", 3.1, 3.8, 6.3), ("2025-07-01", np.nan, np.nan, 7.4), ("2025-10-01", 3.5, 4.5, np.nan),
                    ("2026-01-01", np.nan, np.nan, 5.0), ("2026-02-01", 3.8, np.nan, np.nan), ("2026-04-01", 3.9, 4.7, np.nan), ("2026-06-01", 4.2, np.nan, np.nan),
                    ("2026-07-01", 4.1, 4.8, 5.1), ("2026-08-01", 4.1, 4.7, np.nan), ("2026-10-01", 3.9, np.nan, np.nan)], columns=["d", "bank", "retail", "mfo"])
npl["d"] = pd.to_datetime(npl.d)
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.7))
x = np.arange(len(port)); ax[0].bar(x, port.retail, .6, color=C1, label="Жеке тұлғаларға кредиттер")
ax[0].bar(x, port.consumer, .6, color=C2, alpha=.85, label="оның ішінде тұтынушылық")
for i, v in enumerate(port.retail): ax[0].text(i, v + .4, f"{v:.1f}".replace(".", ","), ha="center", fontsize=9, color=INK)
ax[0].set_xticks(x); ax[0].set_xticklabels(port.date, fontsize=8.5); ax[0].set_ylabel("трлн ₸"); ax[0].set_ylim(0, 30)
ax[0].set_title("а) Банктердің бөлшек кредит портфелі", fontsize=10); ax[0].legend(frameon=False, fontsize=8, loc="upper left")
for col, c, lab in (("bank", C1, "Банктер, бүкіл портфель"), ("retail", C2, "Банктер, жеке тұлғалар"), ("mfo", C3, "МҚҰ, жеке тұлғалар")):
    d = npl.dropna(subset=[col]); ax[1].plot(d.d, d[col], color=c, marker="o", ms=4, label=lab)
ax[1].set_ylabel("NPL90+, %"); ax[1].set_title("ә) 90 күннен асқан мерзімі өткен қарыздар үлесі", fontsize=10); ax[1].legend(frameon=False, fontsize=8)
import matplotlib.dates as md; ax[1].xaxis.set_major_locator(md.MonthLocator(bymonth=[1, 7])); ax[1].xaxis.set_major_formatter(md.DateFormatter("%m.%Y")); ax[1].tick_params(axis="x", labelsize=8.5)
fig.tight_layout(); fig.savefig(F / "kz_market.png", dpi=180); plt.close(fig)
# sensitivity heatmap (GB, tenge)
s = pd.read_csv(F.parent / "results" / "kz_sensitivity.csv")
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.3))
for a, col, t in ((ax[0], "B_minus_A", "а) Π(B) − Π(A), ₸/клиент"), (ax[1], "C_minus_B", "ә) Π(C) − Π(B), ₸/клиент")):
    pv = s.pivot(index="lgd", columns="r_cons", values=col); vm = np.abs(pv.values).max()
    a.imshow(pv.values, cmap="RdBu", vmin=-vm, vmax=vm, aspect="auto", origin="lower")
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]): a.text(j, i, f"{pv.values[i, j]:,.0f}".replace(",", " "), ha="center", va="center", fontsize=8.5, color="white" if abs(pv.values[i, j]) > .6 * vm else INK)
    a.set_xticks(range(pv.shape[1])); a.set_xticklabels([f"{v*100:.1f}%".replace(".0%", "%").replace(".", ",") for v in pv.columns])
    a.set_yticks(range(pv.shape[0])); a.set_yticklabels([f"{v*100:.0f}%" for v in pv.index]); a.grid(False)
    a.set_xlabel("Тұтынушылық кредит мөлшерлемесі (депозит 14,7%)"); a.set_ylabel("LGD"); a.set_title(t, fontsize=10)
fig.tight_layout(); fig.savefig(F / "kz_sensitivity.png", dpi=180); plt.close(fig); print("ok")
