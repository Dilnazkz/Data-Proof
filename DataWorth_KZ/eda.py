"""DataWorth KZ — Exploratory Data Analysis. Outputs results/eda.json and figures/*.png"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data_loader import load, TARGET, PAY_STATUS, BILL, PAY_AMT, FEATURE_SETS, integrity_check

ROOT = Path(__file__).resolve().parent
RES, FIG = ROOT / "results", ROOT / "figures"
RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
NAVY, BLUE, GREY = "#0B1F3A", "#1F6FEB", "#8B95A5"


def main():
    df = load()
    out = {"integrity": integrity_check(df)}
    out["shape"] = {"rows": df.shape[0], "columns": df.shape[1],
                    "features_excl_id_target": df.shape[1] - 2}
    out["default_rate"] = round(float(df[TARGET].mean()), 4)
    out["class_counts"] = df[TARGET].value_counts().sort_index().to_dict()
    out["imbalance_ratio_nondefault_to_default"] = round(out["class_counts"][0] / out["class_counts"][1], 3)
    out["missing_values_total"] = int(df.isna().sum().sum())
    out["duplicate_rows_excl_id"] = int(df.drop(columns="ID").duplicated().sum())

    # undocumented / anomalous codes
    anomalies = {
        "EDUCATION_codes_0_5_6": int(df["EDUCATION"].isin([0, 5, 6]).sum()),
        "MARRIAGE_code_0": int((df["MARRIAGE"] == 0).sum()),
        "PAY_status_value_counts_PAY_0": df["PAY_0"].value_counts().sort_index().to_dict(),
        "PAY_status_minus2_or_0_share_all_months": round(float(df[PAY_STATUS].isin([-2, 0]).mean().mean()), 4),
        "negative_BILL_AMT_rows": int((df[BILL] < 0).any(axis=1).sum()),
        "BILL_AMT1_min": float(df["BILL_AMT1"].min()),
        "PAY_AMT1_max": float(df["PAY_AMT1"].max()),
        "zero_activity_rows_all_bills_and_payments_zero": int(((df[BILL] == 0).all(axis=1) & (df[PAY_AMT] == 0).all(axis=1)).sum()),
    }
    out["anomalies"] = anomalies

    lb = df["LIMIT_BAL"]
    out["limit_bal"] = {k: float(v) for k, v in lb.describe(percentiles=[.25, .5, .75, .95, .99]).items()}
    q = pd.qcut(lb, 5, duplicates="drop")
    out["default_rate_by_limit_quintile"] = {str(k): round(float(v), 4) for k, v in df.groupby(q, observed=True)[TARGET].mean().items()}
    out["default_rate_by_PAY_0"] = {int(k): {"n": int(g.shape[0]), "default_rate": round(float(g[TARGET].mean()), 4)}
                                    for k, g in df.groupby("PAY_0")}
    df_ = df.copy()
    df_["ratio_pay_to_bill_1"] = np.where(df_["BILL_AMT1"] > 0, df_["PAY_AMT1"] / df_["BILL_AMT1"], np.nan)
    rq = pd.qcut(df_["ratio_pay_to_bill_1"].clip(upper=2), 5, duplicates="drop")
    out["default_rate_by_payment_to_bill_ratio_quintile"] = {str(k): round(float(v), 4) for k, v in df_.groupby(rq, observed=True)[TARGET].mean().items()}
    out["corr_BILL_AMT1_PAY_AMT2"] = round(float(df["BILL_AMT1"].corr(df["PAY_AMT2"])), 4)

    feats = FEATURE_SETS["C"]
    corr = df[feats + [TARGET]].corr()
    out["corr_with_target"] = corr[TARGET].drop(TARGET).round(4).sort_values(key=abs, ascending=False).to_dict()
    out["corr_BILL_AMT_mean_offdiag"] = round(float(corr.loc[BILL, BILL].values[np.triu_indices(6, 1)].mean()), 4)
    out["corr_PAY_status_mean_offdiag"] = round(float(corr.loc[PAY_STATUS, PAY_STATUS].values[np.triu_indices(6, 1)].mean()), 4)
    out["demographic_default_rates"] = {c: {int(k): round(float(v), 4) for k, v in df.groupby(c)[TARGET].mean().items()}
                                        for c in ["SEX", "MARRIAGE"]}

    out["leakage_review"] = (
        "Target = default in Oct 2005; all features refer to Apr–Sep 2005 (PAY_0 = Sep status, BILL/PAY_AMT1 = Sep). "
        "No feature is computed from the target month. ID is dropped. Residual risk: random (not time-based) split, "
        "since the file contains one snapshot of different clients; no client appears twice.")

    (RES / "eda.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))

    # ---- figures
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.hist(lb / 1000, bins=50, color=BLUE, alpha=.85)
    ax.set_xlabel("LIMIT_BAL, мың NT$"); ax.set_ylabel("Клиенттер саны"); ax.set_title("Кредит лимитінің таралуы")
    fig.tight_layout(); fig.savefig(FIG / "eda_limit_bal.png", dpi=180); plt.close(fig)

    p = pd.DataFrame(out["default_rate_by_PAY_0"]).T
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.bar(p.index.astype(str), p["default_rate"] * 100, color=NAVY)
    ax.set_xlabel("PAY_0 (қыркүйектегі төлем мәртебесі)"); ax.set_ylabel("Дефолт үлесі, %")
    ax.set_title("Соңғы айдағы төлем тәртібі және дефолт")
    fig.tight_layout(); fig.savefig(FIG / "eda_pay0_default.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 6.2))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.columns, fontsize=7)
    fig.colorbar(im, ax=ax, shrink=.8); ax.set_title("Model C белгілерінің корреляциясы")
    fig.tight_layout(); fig.savefig(FIG / "eda_corr.png", dpi=180); plt.close(fig)
    print(json.dumps({k: out[k] for k in ["shape", "default_rate", "class_counts", "missing_values_total", "duplicate_rows_excl_id", "anomalies"]}, indent=1, default=str))
    print("corr target:", list(out["corr_with_target"].items())[:6])
    print("PAY_0:", out["default_rate_by_PAY_0"])
    print("limit q:", out["default_rate_by_limit_quintile"])
    print("ratio q:", out["default_rate_by_payment_to_bill_ratio_quintile"])
    print("bill corr", out["corr_BILL_AMT_mean_offdiag"], "pay corr", out["corr_PAY_status_mean_offdiag"])


if __name__ == "__main__":
    main()
