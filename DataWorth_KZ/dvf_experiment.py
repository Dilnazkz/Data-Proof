"""DataWorth KZ — Data Value Frontier experiment.

1. Financial result Π of the 9 main models (A/B/C × 3 algorithms), threshold chosen on VALIDATION.
2. Exhaustive search over 2^6 = 64 combinations of information groups on top of the base S0
   (Gradient Boosting with fixed hyper-parameters, so only the information changes).
3. DVF = for every privacy budget (max number of raw fields), the best net value V(S).
4. Scenario & sensitivity analysis over margin, LGD, data cost and privacy charge.
5. Paired bootstrap (test) of Π differences between information sets.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

from data_loader import TARGET, load
from financial_engine import FinParams, best_threshold, decision_profit, ead, net_value, bayes_threshold

SEED = 42
ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"

BASE = ["LIMIT_BAL", "PAY_0"]
GROUPS = {
    "G1_status_m2_m3": ["PAY_2", "PAY_3"],
    "G2_bill_m1": ["BILL_AMT1"],
    "G3_payment_m1": ["PAY_AMT1"],
    "G4_status_m4_m6": ["PAY_4", "PAY_5", "PAY_6"],
    "G5_bill_m2_m6": ["BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"],
    "G6_payment_m2_m6": ["PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"],
}
GB_PARAMS = dict(learning_rate=0.05, max_leaf_nodes=15, max_iter=500, early_stopping=True,
                 validation_fraction=0.1, n_iter_no_change=30, random_state=SEED)
SCENARIOS = {"conservative": FinParams(margin=0.05, lgd=0.90), "base": FinParams(margin=0.10, lgd=0.75),
             "optimistic": FinParams(margin=0.20, lgd=0.45)}


def main():
    df = load()
    sp = np.load(RES / "split_indices.npz"); tr, va, te = sp["train"], sp["val"], sp["test"]
    y = df[TARGET].values
    base_p = SCENARIOS["base"]
    E = ead(df.LIMIT_BAL, df.BILL_AMT1, base_p.ccf)
    mean_ead = float(E[te].mean())
    out = {"mean_ead_test_NT$": mean_ead, "bayes_threshold_base": bayes_threshold(base_p),
           "n_test": int(len(te)), "test_default_rate": float(y[te].mean())}

    # ---------- 1. main models
    pr = np.load(RES / "predictions.npz")
    main_rows = []
    for sc, p in SCENARIOS.items():
        for k in [f[5:] for f in pr.files if f.startswith("test_")]:
            t = best_threshold(y[va], pr[f"val_{k}"], E[va], p)
            r = decision_profit(y[te], pr[f"test_{k}"], E[te], t, p)
            main_rows.append({"scenario": sc, "model": k, **r})
        # no-model benchmarks
        for name, ph in (("approve_all", np.zeros(len(te))), ):
            r = decision_profit(y[te], ph, E[te], 0.5, p)
            main_rows.append({"scenario": sc, "model": name, **r})
    mdf = pd.DataFrame(main_rows); mdf.to_csv(RES / "financial_main_models.csv", index=False)

    # ---------- 2. exhaustive subsets
    names = list(GROUPS)
    rows, preds = [], {}
    for r_ in range(len(names) + 1):
        for combo in itertools.combinations(names, r_):
            feats = BASE + [f for g in combo for f in GROUPS[g]]
            m = HistGradientBoostingClassifier(**GB_PARAMS).fit(df[feats].values[tr], y[tr])
            pv = m.predict_proba(df[feats].values[va])[:, 1]; pt = m.predict_proba(df[feats].values[te])[:, 1]
            key = "+".join(g.split("_")[0] for g in combo) or "S0"
            preds[key] = (pv, pt)
            row = {"subset": key, "groups": list(combo), "n_groups": len(combo), "n_fields": len(feats),
                   "val_roc_auc": roc_auc_score(y[va], pv), "test_roc_auc": roc_auc_score(y[te], pt),
                   "test_pr_auc": average_precision_score(y[te], pt)}
            for sc, p in SCENARIOS.items():
                t = best_threshold(y[va], pv, E[va], p)
                row[f"val_profit_{sc}"] = decision_profit(y[va], pv, E[va], t, p)["profit"]
                d = decision_profit(y[te], pt, E[te], t, p)
                row[f"test_profit_{sc}"] = d["profit"]; row[f"threshold_{sc}"] = t
                row[f"approval_{sc}"] = d["approval_rate"]
            rows.append(row)
            print(f"{key:22s} fields={len(feats):2d} valAUC={row['val_roc_auc']:.4f} testAUC={row['test_roc_auc']:.4f}"
                  f"  Π_test(base)={row['test_profit_base']/1e6:8.2f}M")
    sdf = pd.DataFrame(rows)
    np.savez_compressed(RES / "dvf_subset_predictions.npz",
                        **{f"val__{k}": v[0] for k, v in preds.items()}, **{f"test__{k}": v[1] for k, v in preds.items()})
    for sc in SCENARIOS:
        p0v = sdf.loc[sdf.subset == "S0", f"val_profit_{sc}"].iloc[0]
        p0t = sdf.loc[sdf.subset == "S0", f"test_profit_{sc}"].iloc[0]
        sdf[f"val_gross_value_{sc}"] = sdf[f"val_profit_{sc}"] - p0v
        sdf[f"test_gross_value_{sc}"] = sdf[f"test_profit_{sc}"] - p0t
    sdf.to_csv(RES / "dvf_subsets.csv", index=False)

    # ---------- 3. DVF and optimal set under cost scenarios (selection on VALIDATION, reported on TEST)
    n_va, n_te = len(va), len(te)
    cost_grid = [0, 1, 2, 5, 10, 20]   # bp of mean EAD per extra group per client
    lam_grid = [0, 0.5, 1, 2]          # bp of mean EAD per extra raw field per client
    opt_rows = []
    for sc, p in SCENARIOS.items():
        for c in cost_grid:
            for lam in lam_grid:
                q = FinParams(**{**p.as_dict(), "data_cost_bp": c, "privacy_lambda_bp": lam})
                nv_val = [net_value(r[f"val_profit_{sc}"], sdf.loc[sdf.subset == "S0", f"val_profit_{sc}"].iloc[0],
                                    n_va, r.n_groups, r.n_fields - 2, mean_ead, q)["net_value"] for _, r in sdf.iterrows()]
                j = int(np.argmax(nv_val)); best = sdf.iloc[j]
                nv_te = net_value(best[f"test_profit_{sc}"], sdf.loc[sdf.subset == "S0", f"test_profit_{sc}"].iloc[0],
                                  n_te, best.n_groups, best.n_fields - 2, mean_ead, q)
                opt_rows.append({"scenario": sc, "data_cost_bp": c, "privacy_lambda_bp": lam, "optimal_subset": best.subset,
                                 "n_fields": int(best.n_fields), "test_net_value": nv_te["net_value"],
                                 "test_net_value_per_client": nv_te["net_value"] / n_te})
    odf = pd.DataFrame(opt_rows); odf.to_csv(RES / "dvf_optimal_sets.csv", index=False)

    frontier = []
    for sc in SCENARIOS:
        for k in sorted(sdf.n_fields.unique()):
            sub = sdf[sdf.n_fields <= k]
            j = sub[f"val_profit_{sc}"].idxmax()
            frontier.append({"scenario": sc, "max_fields": int(k), "best_subset": sdf.loc[j, "subset"],
                             "test_gross_value": float(sdf.loc[j, f"test_gross_value_{sc}"]),
                             "test_gross_value_per_client": float(sdf.loc[j, f"test_gross_value_{sc}"] / n_te),
                             "test_roc_auc": float(sdf.loc[j, "test_roc_auc"])})
    pd.DataFrame(frontier).to_csv(RES / "dvf_frontier.csv", index=False)

    # ---------- 4. sensitivity: margin × LGD for A/B/C (GradBoost), break-even data cost
    sens = []
    for m_ in (0.03, 0.05, 0.10, 0.15, 0.20, 0.30):
        for l_ in (0.45, 0.60, 0.75, 0.90):
            p = FinParams(margin=m_, lgd=l_)
            pf = {}
            for s in "ABC":
                k = f"{s}_GradBoost"
                t = best_threshold(y[va], pr[f"val_{k}"], E[va], p)
                pf[s] = decision_profit(y[te], pr[f"test_{k}"], E[te], t, p)["profit"]
            sens.append({"margin": m_, "lgd": l_, **{f"profit_{s}": v for s, v in pf.items()},
                         "value_B_vs_A_per_client": (pf["B"] - pf["A"]) / n_te,
                         "value_C_vs_B_per_client": (pf["C"] - pf["B"]) / n_te,
                         "breakeven_bp_C_vs_B_per_field": (pf["C"] - pf["B"]) / n_te / 13 / mean_ead * 1e4})
    pd.DataFrame(sens).to_csv(RES / "sensitivity_margin_lgd.csv", index=False)

    # ---------- 5. paired bootstrap of Π differences (base scenario, GradBoost & RF)
    rng = np.random.default_rng(SEED)
    boots = {}
    for algo in ("GradBoost", "RandomForest", "LogReg"):
        prof_i = {}
        for s in "ABC":
            k = f"{s}_{algo}"
            t = best_threshold(y[va], pr[f"val_{k}"], E[va], base_p)
            a = pr[f"test_{k}"] < t
            yt, et = y[te], E[te]
            prof_i[s] = np.where(a, np.where(yt == 0, base_p.margin * et, -base_p.lgd * et), 0.0)
        for a_, b_ in (("B", "A"), ("C", "B"), ("C", "A")):
            d = prof_i[a_] - prof_i[b_]
            bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)])
            boots[f"{algo}_{a_}-{b_}"] = {"mean_per_client": float(d.mean()), "ci_lo": float(np.percentile(bs, 2.5)),
                                          "ci_hi": float(np.percentile(bs, 97.5)), "p_le_0": float((bs <= 0).mean())}
    out["profit_diff_bootstrap_base"] = boots
    (RES / "dvf_summary.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
