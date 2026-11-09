"""Robustness: is the weak information effect in Logistic Regression an artefact of raw PAY coding?
LogReg-OHE: one-hot PAY_* status codes + signed-log transformed amounts (fitted on TRAIN only)."""
import json, numpy as np
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from data_loader import FEATURE_SETS, TARGET, load
RES = Path(__file__).resolve().parent / "results"
df = load(); y = df[TARGET].values
sp = np.load(RES / "split_indices.npz"); tr, va, te = sp["train"], sp["val"], sp["test"]
slog = FunctionTransformer(lambda x: np.sign(x) * np.log1p(np.abs(x)))
out = {}
for s, feats in FEATURE_SETS.items():
    cat = [f for f in feats if f.startswith("PAY_") and not f.startswith("PAY_AMT")]
    num = [f for f in feats if f not in cat]
    best = None
    for C in (0.01, 0.1, 1.0):
        pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=20), cat),
                                 ("num", make_pipeline(slog, StandardScaler()), num)])
        m = make_pipeline(pre, LogisticRegression(C=C, max_iter=3000)).fit(df[feats].iloc[tr], y[tr])
        a = roc_auc_score(y[va], m.predict_proba(df[feats].iloc[va])[:, 1])
        if best is None or a > best[0]: best = (a, C, m)
    pt = best[2].predict_proba(df[feats].iloc[te])[:, 1]
    out[s] = {"C": best[1], "val_roc_auc": best[0], "test_roc_auc": roc_auc_score(y[te], pt),
              "test_pr_auc": average_precision_score(y[te], pt)}
    print(s, {k: round(v, 4) for k, v in out[s].items()})
(RES / "robustness_logreg_ohe.json").write_text(json.dumps(out, indent=2))
