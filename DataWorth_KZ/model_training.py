"""DataWorth KZ — Model A/B/C × {Logistic Regression, Random Forest, Gradient Boosting}.

Protocol
  * one stratified split 70/15/15 (seed 42), identical for every model;
  * all preprocessing lives inside sklearn Pipelines fitted on TRAIN only;
  * hyper-parameters and decision thresholds are chosen on VALIDATION only;
  * TEST is touched once, for final metrics and bootstrap 95% CIs (paired resamples).
Demographic fields (SEX, EDUCATION, MARRIAGE, AGE) are deliberately excluded.
"""
from __future__ import annotations

import itertools
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data_loader import FEATURE_SETS, TARGET, load

SEED = 42
ROOT = Path(__file__).resolve().parent
RES, MOD = ROOT / "results", ROOT / "models"
RES.mkdir(exist_ok=True); MOD.mkdir(exist_ok=True)

ALGOS = {
    "LogReg": (lambda p: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, **p)),
               [{"C": c} for c in (0.01, 0.1, 1.0, 10.0)]),
    "RandomForest": (lambda p: RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=SEED, **p),
                     [{"max_depth": d, "min_samples_leaf": l} for d, l in itertools.product((8, 12), (10, 50))]),
    "GradBoost": (lambda p: HistGradientBoostingClassifier(max_iter=500, early_stopping=True, validation_fraction=0.1,
                                                           n_iter_no_change=30, random_state=SEED, **p),
                  [{"learning_rate": lr, "max_leaf_nodes": m} for lr, m in itertools.product((0.05, 0.1), (15, 31))]),
}


def split(df: pd.DataFrame):
    idx = np.arange(len(df))
    tr, tmp = train_test_split(idx, test_size=0.30, stratify=df[TARGET], random_state=SEED)
    va, te = train_test_split(tmp, test_size=0.50, stratify=df[TARGET].iloc[tmp], random_state=SEED)
    return tr, va, te


def f1_threshold(y, p):
    pr, rc, th = precision_recall_curve(y, p)
    f1 = 2 * pr * rc / np.clip(pr + rc, 1e-12, None)
    return float(th[np.nanargmax(f1[:-1])])


def point_metrics(y, p, t):
    yhat = (p >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, yhat).ravel()
    return {"roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p), "brier": brier_score_loss(y, p),
            "precision": precision_score(y, yhat), "recall": recall_score(y, yhat), "f1": f1_score(y, yhat),
            "accuracy": (tp + tn) / len(y), "threshold": t, "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def bootstrap(y, preds: dict, n=1000, seed=SEED):
    rng = np.random.default_rng(seed)
    keys = list(preds)
    out = {k: {"roc_auc": [], "pr_auc": [], "brier": []} for k in keys}
    for _ in range(n):
        b = rng.integers(0, len(y), len(y))
        yb = y[b]
        for k in keys:
            pb = preds[k][b]
            out[k]["roc_auc"].append(roc_auc_score(yb, pb))
            out[k]["pr_auc"].append(average_precision_score(yb, pb))
            out[k]["brier"].append(brier_score_loss(yb, pb))
    return {k: {m: np.array(v) for m, v in d.items()} for k, d in out.items()}


def main():
    t0 = time.time()
    df = load()
    tr, va, te = split(df)
    y = df[TARGET].values
    np.savez(RES / "split_indices.npz", train=tr, val=va, test=te)

    rows, val_pred, test_pred, tuning = [], {}, {}, []
    for fs, feats in FEATURE_SETS.items():
        X = df[feats].values
        for algo, (make, grid) in ALGOS.items():
            best = None
            for params in grid:
                m = make(params).fit(X[tr], y[tr])
                auc = roc_auc_score(y[va], m.predict_proba(X[va])[:, 1])
                tuning.append({"set": fs, "algo": algo, "params": params, "val_roc_auc": round(auc, 5)})
                if best is None or auc > best[0]:
                    best = (auc, params, m)
            auc_v, params, m = best
            pv, pt = m.predict_proba(X[va])[:, 1], m.predict_proba(X[te])[:, 1]
            key = f"{fs}_{algo}"
            val_pred[key], test_pred[key] = pv, pt
            t = f1_threshold(y[va], pv)
            met = point_metrics(y[te], pt, t)
            rows.append({"model": key, "set": fs, "n_features": len(feats), "algo": algo,
                         "best_params": json.dumps(params), "val_roc_auc": auc_v, **met})
            joblib.dump(m, MOD / f"{key}.joblib")
            print(f"{key:18s} val AUC {auc_v:.4f}  test AUC {met['roc_auc']:.4f}  PR {met['pr_auc']:.4f}  {params}")

    # bootstrap CIs and paired differences on TEST
    bs = bootstrap(y[te], test_pred)
    res = pd.DataFrame(rows)
    for m in ("roc_auc", "pr_auc", "brier"):
        res[f"{m}_ci_lo"] = [np.percentile(bs[k][m], 2.5) for k in res.model]
        res[f"{m}_ci_hi"] = [np.percentile(bs[k][m], 97.5) for k in res.model]
    res.to_csv(RES / "model_comparison.csv", index=False)

    diffs = []
    for algo in ALGOS:  # information effect, algorithm held fixed
        for a, b in (("B", "A"), ("C", "B"), ("C", "A")):
            for m in ("roc_auc", "pr_auc"):
                d = bs[f"{a}_{algo}"][m] - bs[f"{b}_{algo}"][m]
                diffs.append({"type": "information_effect", "algo": algo, "comparison": f"{a}-{b}", "metric": m,
                              "diff": float(np.mean(d)), "ci_lo": float(np.percentile(d, 2.5)),
                              "ci_hi": float(np.percentile(d, 97.5)), "p_le_0": float(np.mean(d <= 0))})
    for fs in FEATURE_SETS:  # algorithm effect, information held fixed
        for a, b in (("GradBoost", "LogReg"), ("RandomForest", "LogReg"), ("GradBoost", "RandomForest")):
            d = bs[f"{fs}_{a}"]["roc_auc"] - bs[f"{fs}_{b}"]["roc_auc"]
            diffs.append({"type": "algorithm_effect", "algo": f"{a}-{b}", "comparison": fs, "metric": "roc_auc",
                          "diff": float(np.mean(d)), "ci_lo": float(np.percentile(d, 2.5)),
                          "ci_hi": float(np.percentile(d, 97.5)), "p_le_0": float(np.mean(d <= 0))})
    pd.DataFrame(diffs).to_csv(RES / "paired_differences.csv", index=False)
    pd.DataFrame(tuning).to_csv(RES / "tuning_log.csv", index=False)

    curves = {}
    for k, p in test_pred.items():
        fpr, tpr, _ = roc_curve(y[te], p)
        pr, rc, _ = precision_recall_curve(y[te], p)
        pt_, pp_ = calibration_curve(y[te], p, n_bins=10, strategy="quantile")
        sel = np.linspace(0, len(fpr) - 1, min(200, len(fpr))).astype(int)
        sel2 = np.linspace(0, len(pr) - 1, min(200, len(pr))).astype(int)
        curves[k] = {"roc": {"fpr": fpr[sel].tolist(), "tpr": tpr[sel].tolist()},
                     "pr": {"recall": rc[sel2].tolist(), "precision": pr[sel2].tolist()},
                     "calibration": {"mean_pred": pp_.tolist(), "frac_pos": pt_.tolist()}}
    (RES / "curves.json").write_text(json.dumps(curves))
    np.savez_compressed(RES / "predictions.npz", **{f"val_{k}": v for k, v in val_pred.items()},
                        **{f"test_{k}": v for k, v in test_pred.items()})
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
