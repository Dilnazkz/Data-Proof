"""DataWorth KZ — live (interactive) DVF computations used by the Streamlit app and tests.

Everything here re-uses predictions that were produced by model_training.py / dvf_experiment.py,
so the app recalculates the economics instantly without re-training models.
Selection rule (no test leakage): thresholds and the optimal data set are chosen on VALIDATION;
the reported value is measured on TEST.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from data_loader import TARGET, load
from financial_engine import FinParams, decision_profit, ead, profit_curve

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"

GROUP_INFO = {
    "G1": ("Төлем мәртебесі, 2–3 ай бұрын", ["PAY_2", "PAY_3"]),
    "G2": ("Соңғы шот қалдығы", ["BILL_AMT1"]),
    "G3": ("Соңғы төлем сомасы", ["PAY_AMT1"]),
    "G4": ("Төлем мәртебесі, 4–6 ай бұрын", ["PAY_4", "PAY_5", "PAY_6"]),
    "G5": ("Шот қалдықтары, 2–6 ай", [f"BILL_AMT{i}" for i in range(2, 7)]),
    "G6": ("Төлем сомалары, 2–6 ай", [f"PAY_AMT{i}" for i in range(2, 7)]),
}
BASE_FIELDS = ["LIMIT_BAL", "PAY_0"]


def subset_key(groups) -> str:
    g = sorted(groups, key=lambda x: int(x[1:]))
    return "+".join(g) if g else "S0"


def subset_fields(groups) -> list[str]:
    return BASE_FIELDS + [f for g in sorted(groups, key=lambda x: int(x[1:])) for f in GROUP_INFO[g][1]]


@lru_cache(maxsize=1)
def bundle():
    df = load()
    sp = np.load(RES / "split_indices.npz")
    va, te = sp["val"], sp["test"]
    y = df[TARGET].values
    main = np.load(RES / "predictions.npz")
    sub = np.load(RES / "dvf_subset_predictions.npz")
    return {
        "df": df, "va": va, "te": te, "y_va": y[va], "y_te": y[te],
        "limit_va": df.LIMIT_BAL.values[va], "bill_va": df.BILL_AMT1.values[va],
        "limit_te": df.LIMIT_BAL.values[te], "bill_te": df.BILL_AMT1.values[te],
        "main_val": {k[4:]: main[k] for k in main.files if k.startswith("val_")},
        "main_test": {k[5:]: main[k] for k in main.files if k.startswith("test_")},
        "sub_val": {k[5:]: sub[k] for k in sub.files if k.startswith("val__")},
        "sub_test": {k[6:]: sub[k] for k in sub.files if k.startswith("test__")},
    }


def exposures(b, ccf):
    return ead(b["limit_va"], b["bill_va"], ccf), ead(b["limit_te"], b["bill_te"], ccf)


def evaluate_model(pv, pt, p: FinParams, threshold: float | None = None):
    """Threshold from validation (unless fixed), profit on test."""
    b = bundle()
    ev, et = exposures(b, p.ccf)
    if threshold is None:
        g, prof = profit_curve(b["y_va"], pv, ev, p)
        threshold = float(g[int(np.argmax(prof))])
    return decision_profit(b["y_te"], pt, et, threshold, p)


def evaluate_subsets(p: FinParams) -> pd.DataFrame:
    """All 64 information sets under parameters p: Π, gross value, data cost, net value V(S)."""
    b = bundle()
    ev, et = exposures(b, p.ccf)
    mean_ead = float(et.mean())
    n_va, n_te = len(b["y_va"]), len(b["y_te"])
    rows = []
    for key in b["sub_val"]:
        groups = [] if key == "S0" else key.split("+")
        g, prof_v = profit_curve(b["y_va"], b["sub_val"][key], ev, p)
        j = int(np.argmax(prof_v)); t = float(g[j])
        d = decision_profit(b["y_te"], b["sub_test"][key], et, t, p)
        n_fields = len(subset_fields(groups))
        cost_pc = (len(groups) * p.data_cost_bp + (n_fields - 2) * p.privacy_lambda_bp) * 1e-4 * mean_ead
        rows.append({"subset": key, "groups": groups, "n_groups": len(groups), "n_fields": n_fields,
                     "threshold": t, "val_profit_pc": prof_v[j] / n_va, "test_profit_pc": d["profit"] / n_te,
                     "approval_rate": d["approval_rate"], "bad_rate_approved": d["bad_rate_approved"],
                     "data_cost_pc": cost_pc})
    out = pd.DataFrame(rows)
    s0 = out.set_index("subset").loc["S0"]
    out["val_net_value_pc"] = out.val_profit_pc - s0.val_profit_pc - out.data_cost_pc
    out["test_gross_value_pc"] = out.test_profit_pc - s0.test_profit_pc
    out["test_net_value_pc"] = out.test_gross_value_pc - out.data_cost_pc
    out.attrs["mean_ead"] = mean_ead
    return out.sort_values(["n_fields", "subset"]).reset_index(drop=True)


def optimal_subset(table: pd.DataFrame, max_fields: int = 19) -> pd.Series:
    t = table[table.n_fields <= max_fields]
    return t.loc[t.val_net_value_pc.idxmax()]


def frontier(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in sorted(table.n_fields.unique()):
        r = optimal_subset(table, k)
        rows.append({"max_fields": int(k), "subset": r.subset, "test_net_value_pc": r.test_net_value_pc,
                     "val_net_value_pc": r.val_net_value_pc})
    return pd.DataFrame(rows)
