"""DataWorth KZ — Kazakhstan adaptation (hybrid research approach, Nov 2026).

Taiwan (UCI) data  → client-level PD models (unchanged; predictions re-used, no re-training).
Kazakhstan data    → only the FINANCIAL parameters of the decision model (official ARDFM / NBK statistics)
                     plus clearly labelled scenario assumptions (LGD, CCF, data cost, privacy charge).

Nothing here re-labels Taiwanese clients as Kazakh clients and nothing converts Kazakh NPL90+ into PD.

Official inputs (see KZ_SOURCES):
  r_cons  = 22.5 %  weighted average rate on consumer loans in tenge, July 2026 (ARDFM, release on 01.08.2026)
  r_dep   = 14.7 %  weighted average rate on individuals' term deposits in tenge, July 2026 (same release)
  r_base  = 15.75 % NBK base rate, decision of 23.10.2026
  E_kz    = 27.5 trn KZT / 39.4 mn loans ≈ 698 000 KZT — average outstanding debt per loan in the credit bureau
            on 01.01.2026 (derived estimate; used only to rescale exposures to tenge)
Scenario assumptions: LGD 75 % / 90 %, CCF 50 %, data cost c and privacy charge λ.

Horizon: the UCI target is a 1-month delinquency flag. In the KZ scenarios m is the ANNUAL spread
(r_cons − funding cost) and y is used as a proxy for a default event within the horizon (assumption, discussed in
the paper). A horizon-consistent monthly variant (m = spread / 12) is reported as a robustness check.

Rescaling: EAD_kz_i = EAD_i × E_kz / mean(EAD_test). Π, V and C are linear in this factor, so subset rankings and
thresholds do not depend on it (scale invariance, see revision_analysis R4).
Outputs → results/kz_*.csv, results/kz_summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from data_loader import TARGET, load
from dvf_live import subset_fields
from financial_engine import FinParams, decision_profit, ead, profit_curve

RES = Path(__file__).resolve().parent / "results"
SEED, B_BOOT = 42, 2000

KZ_SOURCES = {
    "r_cons": (22.5, "%", "2026 ж. шілде", "ҚНРДА: банк секторының 01.08.2026 жағдайы"),
    "r_dep": (14.7, "%", "2026 ж. шілде", "ҚНРДА: банк секторының 01.08.2026 жағдайы"),
    "r_base": (15.75, "%", "23.10.2026 шешімі", "ҚР Ұлттық Банкі"),
    "debt_bureau_trn": (27.5, "трлн ₸", "01.01.2026", "Бірінші кредиттік бюро (Tengrinews арқылы)"),
    "loans_bureau_mn": (39.4, "млн кредит", "01.01.2026", "Tengrinews"),
}
R_CONS, R_DEP, R_BASE = 0.225, 0.147, 0.1575
E_KZ = 27.5e12 / 39.4e6  # ≈ 697 970 KZT

SCEN = {
    "KZ1_base": dict(label="1 — базалық", p=FinParams(margin=R_CONS - R_DEP, lgd=0.75),
                     note="m = 22,5% − 14,7% = 7,8% (жылдық); LGD = 75% (болжам)"),
    "KZ2_high_risk": dict(label="2 — жоғары тәуекел", p=FinParams(margin=R_CONS - R_BASE, lgd=0.90),
                          note="m = 22,5% − 15,75% = 6,75%; LGD = 90% (болжам)"),
    "KZ3_data_cost": dict(label="3 — деректер құны жоғары",
                          p=FinParams(margin=R_CONS - R_DEP, lgd=0.75, data_cost_bp=10.0, privacy_lambda_bp=5.0),
                          note="m = 7,8%; LGD = 75%; c = 10 б.п./топ; λ = 5 б.п./өріс (болжам)"),
    "KZ_monthly": dict(label="Айлық көкжиек (тексеріс)", p=FinParams(margin=(R_CONS - R_DEP) / 12, lgd=0.75),
                       note="m = 7,8% / 12 = 0,65% (айлық); LGD = 75%"),
}
TW_BASE = FinParams(0.10, 0.75)


def best_t(y, pd_hat, e, p):
    g, prof = profit_curve(y, pd_hat, e, p)
    j = int(np.argmax(prof))
    return float(g[j]), float(prof[j])


def per_client(y, pd_hat, e, t, p):
    a = pd_hat < t
    return np.where(a, np.where(y == 0, p.margin * e, -p.lgd * e), 0.0)


def main():
    df = load(); y = df[TARGET].values
    sp = np.load(RES / "split_indices.npz"); va, te = sp["val"], sp["test"]
    pr = np.load(RES / "predictions.npz"); sub = np.load(RES / "dvf_subset_predictions.npz")
    E_tw = ead(df.LIMIT_BAL.values, df.BILL_AMT1.values, 0.5)
    k = E_KZ / E_tw[te].mean()
    E = E_tw * k                                           # exposures in tenge (rescaled)
    yv, yt, ev, et = y[va], y[te], E[va], E[te]
    out = {"scale_factor_kzt_per_ntd": k, "E_kz": E_KZ, "sources": KZ_SOURCES}

    # ---- (1) main models A/B/C × 3 algorithms
    rows, boot = [], []
    for sk, sc in {**{"TW_base": dict(label="Тайвань базалық (салыстыру)", p=TW_BASE, note="m=10%, LGD=75%")}, **SCEN}.items():
        p = sc["p"]
        for algo in ("LogReg", "RandomForest", "GradBoost"):
            prof = {}
            for s in "ABC":
                t, _ = best_t(yv, pr[f"val_{s}_{algo}"], ev, p)
                d = decision_profit(yt, pr[f"test_{s}_{algo}"], et, t, p)
                prof[s] = per_client(yt, pr[f"test_{s}_{algo}"], et, t, p)
                rows.append({"scenario": sk, "label": sc["label"], "algo": algo, "set": s, "threshold": t,
                             "bayes_t": p.margin / (p.margin + p.lgd), "approval_rate": d["approval_rate"],
                             "bad_rate_approved": d["bad_rate_approved"], "profit_pc_kzt": d["profit_per_client"],
                             "profit_per_100k_clients_bn_kzt": d["profit_per_client"] * 1e5 / 1e9})
            if algo != "LogReg":
                rng = np.random.default_rng(SEED)
                for a_, b_ in (("B", "A"), ("C", "B")):
                    dd = prof[a_] - prof[b_]
                    bs = dd[rng.integers(0, len(dd), (B_BOOT, len(dd)))].mean(axis=1)
                    boot.append({"scenario": sk, "algo": algo, "comparison": f"{a_}-{b_}", "mean_diff_kzt": dd.mean(),
                                 "ci95_lo": np.percentile(bs, 2.5), "ci95_hi": np.percentile(bs, 97.5),
                                 "U95": np.percentile(bs, 95), "profit_B": prof["B"].mean()})
    models = pd.DataFrame(rows); models.to_csv(RES / "kz_models.csv", index=False)
    bt = pd.DataFrame(boot)
    bt["U95_pct_of_PiB"] = np.where(bt.profit_B > 0, bt.U95 / bt.profit_B * 100, np.nan)
    bt.to_csv(RES / "kz_bootstrap.csv", index=False)

    # ---- (2) 64 subsets under each scenario
    srows = []
    for sk, sc in {**{"TW_base": dict(label="Тайвань базалық", p=TW_BASE)}, **SCEN}.items():
        p = sc["p"]; mean_e = float(et.mean())
        base = {}
        for key in [kk[5:] for kk in sub.files if kk.startswith("val__")]:
            groups = [] if key == "S0" else key.split("+")
            t, pv = best_t(yv, sub[f"val__{key}"], ev, p)
            d = decision_profit(yt, sub[f"test__{key}"], et, t, p)
            nf = len(subset_fields(groups))
            cost = (len(groups) * p.data_cost_bp + (nf - 2) * p.privacy_lambda_bp) * 1e-4 * mean_e
            base[key] = dict(scenario=sk, subset=key, n_groups=len(groups), n_fields=nf, threshold=t,
                             val_profit_pc=pv / len(yv), test_profit_pc=d["profit_per_client"],
                             approval_rate=d["approval_rate"], data_cost_pc=cost)
        s0 = base["S0"]
        for r in base.values():
            r["val_net_value_pc"] = r["val_profit_pc"] - s0["val_profit_pc"] - r["data_cost_pc"]
            r["test_net_value_pc"] = r["test_profit_pc"] - s0["test_profit_pc"] - r["data_cost_pc"]
            srows.append(r)
    subs = pd.DataFrame(srows); subs.to_csv(RES / "kz_subsets.csv", index=False)

    opt, fr = [], []
    for sk, g in subs.groupby("scenario", sort=False):
        o = g.loc[g.val_net_value_pc.idxmax()]
        b = g.set_index("subset").loc["G1+G2+G3"]; c = g.set_index("subset").loc["G1+G2+G3+G4+G5+G6"]
        opt.append({"scenario": sk, "optimal_subset": o.subset, "n_fields": int(o.n_fields),
                    "test_net_value_pc_kzt": o.test_net_value_pc, "B_test_net_value_pc_kzt": b.test_net_value_pc,
                    "C_test_net_value_pc_kzt": c.test_net_value_pc, "S0_test_profit_pc_kzt": g.set_index("subset").loc["S0", "test_profit_pc"],
                    "opt_approval": o.approval_rate})
        for kf in sorted(g.n_fields.unique()):
            gg = g[g.n_fields <= kf]; r = gg.loc[gg.val_net_value_pc.idxmax()]
            fr.append({"scenario": sk, "max_fields": int(kf), "subset": r.subset, "test_net_value_pc_kzt": r.test_net_value_pc})
    opt = pd.DataFrame(opt); opt.to_csv(RES / "kz_optimal.csv", index=False)
    pd.DataFrame(fr).to_csv(RES / "kz_frontier.csv", index=False)

    # ---- (3) H4: does the KZ parameterisation change the optimal set / best model?
    best_model = models.loc[models.groupby("scenario").profit_pc_kzt.idxmax(), ["scenario", "algo", "set", "profit_pc_kzt"]]
    tw_opt = opt.set_index("scenario").loc["TW_base", "optimal_subset"]
    out["H4"] = {sk: {"optimal_subset": opt.set_index("scenario").loc[sk, "optimal_subset"],
                      "differs_from_TW_base": bool(opt.set_index("scenario").loc[sk, "optimal_subset"] != tw_opt)}
                 for sk in SCEN}
    out["best_model"] = best_model.to_dict(orient="records")
    (RES / "kz_summary.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float))

    pd.set_option("display.width", 250)
    print("scale k =", round(k, 3), " E_kz =", round(E_KZ))
    print(models[models.algo == "GradBoost"].round(3).to_string())
    print(models.pivot_table(index=["scenario", "algo"], columns="set", values="profit_pc_kzt").round(0).to_string())
    print(bt.round(1).to_string()); print(opt.round(1).to_string()); print(json.dumps(out["H4"], ensure_ascii=False))
    print(best_model.round(0).to_string())


if __name__ == "__main__":
    main()
