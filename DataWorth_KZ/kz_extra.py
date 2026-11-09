"""Extra Kazakhstan analyses: data-cost / privacy break-evens and rate × LGD sensitivity, in tenge (KZ base scenario)."""
import json
import numpy as np, pandas as pd
from dvf_live import evaluate_subsets, optimal_subset, evaluate_model, bundle
from financial_engine import FinParams
import kz_adaptation as kz
R = kz.RES
base = kz.SCEN["KZ1_base"]["p"]
t0 = evaluate_subsets(base); f = kz.E_KZ / t0.attrs["mean_ead"]
rows = []
for c in [0, 2, 4, 6, 8, 10, 12, 15, 20, 30]:
    o = optimal_subset(evaluate_subsets(FinParams(base.margin, base.lgd, 0.5, 0, float(c), 0)))
    rows.append({"param": "c", "bp": c, "kzt_per_client": c * 1e-4 * kz.E_KZ, "optimal_subset": o.subset, "n_fields": int(o.n_fields), "test_V_kzt": o.test_net_value_pc * f})
for lam in [0, 1, 2, 3, 4, 5, 6, 8, 10]:
    o = optimal_subset(evaluate_subsets(FinParams(base.margin, base.lgd, 0.5, 0, 0, float(lam))))
    rows.append({"param": "lambda", "bp": lam, "kzt_per_client": lam * 1e-4 * kz.E_KZ, "optimal_subset": o.subset, "n_fields": int(o.n_fields), "test_V_kzt": o.test_net_value_pc * f})
scan = pd.DataFrame(rows); scan.to_csv(R / "kz_cost_scan.csv", index=False)
# analytic break-even on validation: B vs smaller sets
s = t0.set_index("subset"); B = s.loc["G1+G2+G3"]; be = []
for k, r in s.iterrows():
    if r.n_fields < B.n_fields:
        gap = B.val_net_value_pc - r.val_net_value_pc
        be.append({"vs": k, "lam_star_bp": gap / (B.n_fields - r.n_fields) / t0.attrs["mean_ead"] * 1e4,
                   "c_star_bp": gap / max(B.n_groups - r.n_groups, 1e-9) / t0.attrs["mean_ead"] * 1e4 if B.n_groups > r.n_groups else np.nan})
be = pd.DataFrame(be)
cg = [(k, (B.val_net_value_pc - r.val_net_value_pc) / (B.n_groups - r.n_groups) / t0.attrs["mean_ead"] * 1e4) for k, r in s.iterrows() if r.n_groups < B.n_groups]
cg = min(cg, key=lambda z: z[1])
out = {"lam_star_bp": float(be.lam_star_bp.min()), "lam_star_vs": be.loc[be.lam_star_bp.idxmin(), "vs"], "c_star_bp": float(cg[1]), "c_star_vs": cg[0]}
out["lam_star_kzt"] = out["lam_star_bp"] * 1e-4 * kz.E_KZ; out["c_star_kzt"] = out["c_star_bp"] * 1e-4 * kz.E_KZ
# sensitivity: consumer-loan rate × LGD (funding = deposit rate 14.7%)
b = bundle(); sens = []
for r in [0.18, 0.20, 0.225, 0.25, 0.28]:
    for lgd in [0.60, 0.75, 0.90]:
        p = FinParams(r - kz.R_DEP, lgd, 0.5)
        v = {st: evaluate_model(b["main_val"][f"{st}_GradBoost"], b["main_test"][f"{st}_GradBoost"], p)["profit_per_client"] * f for st in "ABC"}
        sens.append({"r_cons": r, "lgd": lgd, "margin": r - kz.R_DEP, "PiA": v["A"], "PiB": v["B"], "PiC": v["C"], "B_minus_A": v["B"] - v["A"], "C_minus_B": v["C"] - v["B"]})
sens = pd.DataFrame(sens); sens.to_csv(R / "kz_sensitivity.csv", index=False)
out["sens_B_gt_A_share"] = float((sens.B_minus_A > 0).mean()); out["sens_C_gt_B_share"] = float((sens.C_minus_B > 0).mean())
(R / "kz_extra.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float))
print(scan.round(0).to_string()); print(json.dumps(out, ensure_ascii=False, default=float)); print(sens.round(0).to_string())
