"""DataWorth KZ — revision analyses requested by the scientific audit (Nov 2026).

R1  H1 re-test: non-inferiority view of Π(B) vs Π(C). Paired bootstrap of per-client profit
    differences on TEST (thresholds fixed from VALIDATION). We report the one-sided 95% upper
    bound of the advantage of C over B (U95). H1 (non-inferiority) holds for a margin δ only if U95 < δ.
    No margin was pre-registered, so we report U95 and the smallest margin δ* = max(U95, 0) at which H1 would hold.
R2  EAD that does not use BILL_AMT1: EAD_lim = u × LIMIT_BAL (u = 0.5, assumption). Re-runs A/B/C and
    the 64-subset optimum, so that the decision layer uses only S0 fields.
R3  Privacy charge λ scan 0…12 bp/field and data cost c scan 0…50 bp/group (validation selection, test value).
R4  Scale invariance: the optimal threshold and subset ranking depend on m / LGD only.
R5  Horizon-consistent illustrative scenario: m = 2% per month, LGD = 75% (ratio 0.027).
All outputs → results/revision_*.{csv,json}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from data_loader import TARGET, load
from financial_engine import FinParams, decision_profit, ead, profit_curve

SEED = 42
RES = Path(__file__).resolve().parent / "results"
B_BOOT = 2000


def per_client_profit(y, pd_hat, e, t, p):
    a = pd_hat < t
    return np.where(a, np.where(y == 0, p.margin * e, -p.lgd * e), 0.0)


def best_t(y, pd_hat, e, p):
    g, prof = profit_curve(y, pd_hat, e, p)
    return float(g[int(np.argmax(prof))])


def boot_diff(d, rng, n=B_BOOT):
    idx = rng.integers(0, len(d), (n, len(d)))
    return d[idx].mean(axis=1)


def main():
    df = load(); y = df[TARGET].values
    sp = np.load(RES / "split_indices.npz"); va, te = sp["val"], sp["test"]
    pr = np.load(RES / "predictions.npz")
    sub = np.load(RES / "dvf_subset_predictions.npz")
    out = {}

    E_bal = ead(df.LIMIT_BAL.values, df.BILL_AMT1.values, 0.5)
    E_lim = 0.5 * df.LIMIT_BAL.values.astype(float)
    scen = {"conservative": FinParams(0.05, 0.90), "base": FinParams(0.10, 0.75), "optimistic": FinParams(0.20, 0.45),
            "monthly_2pct": FinParams(0.02, 0.75)}

    # ---------------- R1 + R2 + R5: paired bootstrap of profit differences
    rows = []
    for ead_name, E in (("balance_based", E_bal), ("limit_based", E_lim)):
        mean_ead = float(E[te].mean())
        for sc, p in scen.items():
            for algo in ("GradBoost", "RandomForest", "LogReg"):
                prof = {}
                for s in "ABC":
                    k = f"{s}_{algo}"
                    t = best_t(y[va], pr[f"val_{k}"], E[va], p)
                    prof[s] = per_client_profit(y[te], pr[f"test_{k}"], E[te], t, p)
                rng = np.random.default_rng(SEED)
                for a, b in (("B", "A"), ("C", "B")):
                    d = prof[a] - prof[b]
                    bs = boot_diff(d, rng)
                    rows.append({"ead": ead_name, "scenario": sc, "algo": algo, "comparison": f"{a}-{b}",
                                 "profit_A": prof["A"].mean(), "profit_B": prof["B"].mean(), "profit_C": prof["C"].mean(),
                                 "mean_diff": float(d.mean()), "ci95_lo": float(np.percentile(bs, 2.5)),
                                 "ci95_hi": float(np.percentile(bs, 97.5)), "one_sided_U95": float(np.percentile(bs, 95)),
                                 "one_sided_L95": float(np.percentile(bs, 5)), "p_le_0": float((bs <= 0).mean()),
                                 "mean_ead": mean_ead})
    bt = pd.DataFrame(rows)
    cb = bt.comparison == "C-B"
    bt.loc[cb, "U95_bp_of_EAD"] = bt.loc[cb, "one_sided_U95"] / bt.loc[cb, "mean_ead"] * 1e4
    bt.loc[cb, "U95_pct_of_PiB"] = np.where(bt.loc[cb, "profit_B"] > 0, bt.loc[cb, "one_sided_U95"] / bt.loc[cb, "profit_B"] * 100, np.nan)
    bt.to_csv(RES / "revision_bootstrap.csv", index=False)

    # ---------------- R2: 64-subset optimum under limit-based EAD (and baseline for reference)
    opt_rows = []
    for ead_name, E in (("balance_based", E_bal), ("limit_based", E_lim)):
        for sc, p in scen.items():
            best = None
            for key in sub.files:
                if not key.startswith("val__"): continue
                k = key[5:]
                g, pv = profit_curve(y[va], sub[key], E[va], p)
                j = int(np.argmax(pv))
                if best is None or pv[j] > best[1]:
                    best = (k, pv[j], float(g[j]))
            k, _, t = best
            nf = 2 + sum({"G1": 2, "G2": 1, "G3": 1, "G4": 3, "G5": 5, "G6": 5}[g] for g in ([] if k == "S0" else k.split("+")))
            tv = decision_profit(y[te], sub[f"test__{k}"], E[te], t, p)["profit_per_client"]
            t0 = best_t(y[va], sub["val__S0"], E[va], p)
            tv0 = decision_profit(y[te], sub["test__S0"], E[te], t0, p)["profit_per_client"]
            opt_rows.append({"ead": ead_name, "scenario": sc, "optimal_subset": k, "n_scoring_fields": nf,
                             "fields_processed_incl_EAD": nf + (1 if (ead_name == "balance_based" and "G2" not in k.split("+")) else 0),
                             "test_value_vs_S0_per_client": tv - tv0})
    pd.DataFrame(opt_rows).to_csv(RES / "revision_optimal_by_ead.csv", index=False)

    # ---------------- R3: λ and c scans (baseline EAD, base scenario)
    from dvf_live import evaluate_subsets, optimal_subset
    lam_rows = []
    for lam in np.arange(0, 12.01, 0.5):
        tab = evaluate_subsets(FinParams(privacy_lambda_bp=float(lam)))
        o = optimal_subset(tab)
        lam_rows.append({"lambda_bp": float(lam), "optimal_subset": o.subset, "n_fields": int(o.n_fields),
                         "test_net_value_pc": float(o.test_net_value_pc),
                         "B_test_net_value_pc": float(tab.set_index("subset").loc["G1+G2+G3", "test_net_value_pc"])})
    pd.DataFrame(lam_rows).to_csv(RES / "revision_lambda_scan.csv", index=False)
    c_rows = []
    for c in (0, 1, 2, 5, 10, 15, 20, 30, 50):
        o = optimal_subset(evaluate_subsets(FinParams(data_cost_bp=float(c))))
        c_rows.append({"data_cost_bp": c, "optimal_subset": o.subset, "n_fields": int(o.n_fields), "test_net_value_pc": float(o.test_net_value_pc)})
    pd.DataFrame(c_rows).to_csv(RES / "revision_cost_scan.csv", index=False)

    # analytic break-even λ* between B and its best smaller competitor on VALIDATION
    tab0 = evaluate_subsets(FinParams())
    s = tab0.set_index("subset")
    mean_ead = tab0.attrs["mean_ead"]
    be = []
    for k, r in s.iterrows():
        if r.n_fields < s.loc["G1+G2+G3", "n_fields"]:
            dv = s.loc["G1+G2+G3", "val_net_value_pc"] - r.val_net_value_pc   # value gap (λ=0)
            dfld = s.loc["G1+G2+G3", "n_fields"] - r.n_fields
            be.append({"vs_subset": k, "fields": int(r.n_fields), "val_gap_pc": float(dv), "lambda_star_bp": float(dv / dfld / mean_ead * 1e4)})
    be = pd.DataFrame(be).sort_values("lambda_star_bp")
    be.to_csv(RES / "revision_lambda_breakeven.csv", index=False)
    out["lambda_star_min"] = be.iloc[0].to_dict()

    # ---------------- R4: scale invariance
    t1 = evaluate_subsets(FinParams(0.10, 0.75)); t2 = evaluate_subsets(FinParams(0.20, 1.50))
    out["scale_invariance"] = {"same_optimal": optimal_subset(t1).subset == optimal_subset(t2).subset,
                               "profit_ratio_B": float(t2.set_index("subset").loc["G1+G2+G3", "test_profit_pc"] / t1.set_index("subset").loc["G1+G2+G3", "test_profit_pc"])}
    # ---------------- leakage note: share of rows where BILL_AMT1 (Sep) is used — it is observed before the Oct target
    out["ead_fields"] = {"balance_based": ["LIMIT_BAL", "BILL_AMT1"], "limit_based": ["LIMIT_BAL"]}
    (RES / "revision_summary.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float))

    pd.set_option("display.width", 250)
    print(bt[(bt.algo != "LogReg")][["ead", "scenario", "algo", "comparison", "profit_A", "profit_B", "profit_C", "mean_diff", "ci95_lo", "ci95_hi", "one_sided_U95", "U95_bp_of_EAD", "U95_pct_of_PiB"]].round(1).to_string())
    print(pd.DataFrame(opt_rows).to_string())
    print(pd.DataFrame(lam_rows).to_string()); print(pd.DataFrame(c_rows).to_string()); print(be.head(5).round(2).to_string()); print(out)


if __name__ == "__main__":
    main()
