"""DataWorth KZ test-suite.  Run:  python -m pytest -q tests/"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_loader import FEATURE_SETS, DEMOGRAPHIC, TARGET, integrity_check, load  # noqa: E402
from financial_engine import FinParams, bayes_threshold, decision_profit, ead, net_value, profit_curve, best_threshold  # noqa: E402
import dvf_live  # noqa: E402

RES = ROOT / "results"


# ---------------- data
def test_dataset_matches_uci_reference():
    chk = integrity_check(load())
    assert chk["matches_reference"], chk


def test_feature_sets_sizes_and_no_demographics():
    assert [len(FEATURE_SETS[s]) for s in "ABC"] == [2, 6, 19]
    for s in "ABC":
        assert not set(FEATURE_SETS[s]) & set(DEMOGRAPHIC)
        assert TARGET not in FEATURE_SETS[s] and "ID" not in FEATURE_SETS[s]
    assert set(FEATURE_SETS["A"]) < set(FEATURE_SETS["B"]) < set(FEATURE_SETS["C"])


def test_split_disjoint_complete_stratified():
    sp = np.load(RES / "split_indices.npz")
    tr, va, te = sp["train"], sp["val"], sp["test"]
    assert len(set(tr) & set(va)) == len(set(tr) & set(te)) == len(set(va) & set(te)) == 0
    assert len(tr) + len(va) + len(te) == 30000
    assert (len(tr), len(va), len(te)) == (21000, 4500, 4500)
    y = load()[TARGET].values
    rates = [y[i].mean() for i in (tr, va, te)]
    assert max(rates) - min(rates) < 0.002


# ---------------- financial engine
def test_ead_formula():
    assert np.allclose(ead([100, 100, 100], [40, -10, 150], 0.5), [70, 50, 150])


def test_decision_profit_hand_calculation():
    p = FinParams(margin=0.1, lgd=0.8)
    y = np.array([0, 1, 0, 1]); pdh = np.array([0.05, 0.10, 0.50, 0.60]); e = np.array([100., 200., 300., 400.])
    r = decision_profit(y, pdh, e, 0.2, p)          # approve first two
    assert r["approval_rate"] == 0.5
    assert np.isclose(r["profit"], 0.1 * 100 - 0.8 * 200)
    assert np.isclose(r["missed_margin_false_reject"], 0.1 * 300)
    assert np.isclose(r["avoided_loss_true_reject"], 0.8 * 400)
    assert np.isclose(r["model_ecl_approved"], 0.05 * 0.8 * 100 + 0.10 * 0.8 * 200)


def test_bayes_threshold():
    assert np.isclose(bayes_threshold(FinParams(margin=0.1, lgd=0.75)), 0.1 / 0.85)


def test_profit_curve_equals_slow_loop():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500); pdh = rng.random(500); e = rng.uniform(1e3, 1e5, 500)
    p = FinParams(margin=0.12, lgd=0.6, op_cost=3.0)
    g, fast = profit_curve(y, pdh, e, p)
    slow = [decision_profit(y, pdh, e, t, p)["profit"] for t in g]
    assert np.allclose(fast, slow)
    assert np.isclose(best_threshold(y, pdh, e, p), g[int(np.argmax(fast))])


def test_net_value_and_breakeven():
    p = FinParams(data_cost_bp=10, privacy_lambda_bp=1)
    nv = net_value(1_000_000, 400_000, 1000, 3, 4, 100_000, p)
    assert np.isclose(nv["data_cost"], (3 * 10 + 4 * 1) * 1e-4 * 100_000 * 1000)
    assert np.isclose(nv["break_even_cost_per_client"], 600.0)


# ---------------- experiment integrity
def test_results_reproduce_reported_numbers():
    mc = pd.read_csv(RES / "model_comparison.csv").set_index("model")
    assert len(mc) == 9
    assert (mc.roc_auc_ci_lo <= mc.roc_auc).all() and (mc.roc_auc <= mc.roc_auc_ci_hi).all()
    s = json.loads((RES / "dvf_summary.json").read_text())["profit_diff_bootstrap_base"]
    assert s["GradBoost_B-A"]["ci_lo"] > 0          # H2
    assert s["GradBoost_C-B"]["ci_lo"] < 0 < s["GradBoost_C-B"]["ci_hi"] or s["GradBoost_C-B"]["ci_hi"] < 0


def test_live_engine_matches_batch_experiment():
    t = dvf_live.evaluate_subsets(FinParams())
    assert len(t) == 64
    batch = pd.read_csv(RES / "dvf_subsets.csv").set_index("subset")
    live = t.set_index("subset")
    n = 4500
    for k in ["S0", "G1+G2+G3", "G1+G2+G3+G4+G5+G6"]:
        assert np.isclose(live.loc[k, "test_profit_pc"] * n, batch.loc[k, "test_profit_base"], rtol=1e-9)
    assert dvf_live.optimal_subset(t).subset == "G1+G2+G3"


def test_selection_uses_validation_not_test():
    """Optimal set must not change if TEST outcomes are scrambled (no test leakage)."""
    b = dvf_live.bundle()
    before = dvf_live.optimal_subset(dvf_live.evaluate_subsets(FinParams())).subset
    saved = b["y_te"].copy()
    try:
        b["y_te"][:] = np.random.default_rng(1).permutation(saved)
        after = dvf_live.optimal_subset(dvf_live.evaluate_subsets(FinParams())).subset
    finally:
        b["y_te"][:] = saved
    assert before == after


def test_data_cost_shrinks_optimal_set():
    small = dvf_live.optimal_subset(dvf_live.evaluate_subsets(FinParams(data_cost_bp=0)))
    big = dvf_live.optimal_subset(dvf_live.evaluate_subsets(FinParams(data_cost_bp=200)))
    assert big.n_fields <= small.n_fields
    assert big.subset == "S0"


# ---------------- web app (every page actually executes)
PAGES = ["Dashboard", "Credit Risk Laboratory", "Data Value Frontier", "Financial Simulator", "Privacy & Consent", "Қазақстан сценарийлері", "Research Results"]


@pytest.mark.parametrize("page", PAGES)
def test_app_pages_render(page):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception
    assert at.title[0].value in (page, "DataWorth KZ")


def test_app_dvf_reacts_to_parameters():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run(); at.sidebar.radio[0].set_value("Data Value Frontier").run()
    opt_before = [m for m in at.metric if m.label == "Оңтайлы жиынтық"][0].value
    cost = [s for s in at.sidebar.slider if s.label.startswith("Деректер тобының құны")][0]
    cost.set_value(50.0).run()
    opt_after = [m for m in at.metric if m.label == "Оңтайлы жиынтық"][0].value
    assert not at.exception
    assert opt_before == "G1+G2+G3" and opt_after != opt_before


# ---------------- revision analyses (Nov 2026 audit)
def test_scale_invariance_of_decision():
    """Optimal subset and threshold depend only on m/LGD: doubling both doubles profit."""
    t1 = dvf_live.evaluate_subsets(FinParams(0.10, 0.75)); t2 = dvf_live.evaluate_subsets(FinParams(0.20, 1.50))
    assert dvf_live.optimal_subset(t1).subset == dvf_live.optimal_subset(t2).subset
    a = t1.set_index("subset").test_profit_pc; b = t2.set_index("subset").test_profit_pc
    assert np.allclose(b, 2 * a)


def test_revision_outputs_consistent():
    bt = pd.read_csv(RES / "revision_bootstrap.csv")
    r = bt[(bt.ead == "balance_based") & (bt.scenario == "base") & (bt.algo == "GradBoost") & (bt.comparison == "C-B")].iloc[0]
    assert round(r.mean_diff) == -482 and r.one_sided_U95 < 0           # GB: B non-inferior to C for any margin >= 0
    r2 = bt[(bt.ead == "balance_based") & (bt.scenario == "base") & (bt.algo == "RandomForest") & (bt.comparison == "C-B")].iloc[0]
    assert r2.one_sided_U95 > 0                                         # RF: non-inferiority needs a positive margin
    lam = pd.read_csv(RES / "revision_lambda_scan.csv")
    assert lam.loc[lam.lambda_bp == 8.5, "n_fields"].item() == 6 and lam.loc[lam.lambda_bp == 9.0, "n_fields"].item() == 3
    opt = pd.read_csv(RES / "revision_optimal_by_ead.csv")
    assert opt[(opt.ead == "limit_based") & (opt.scenario == "base")].optimal_subset.item() == "G1+G2+G3"


# ---------------- Kazakhstan adaptation (hybrid approach)
def test_kz_rescaling_reproduces_taiwan_result():
    """TW-parameter profits in ₸ are the NT$ model results × the linear scale factor (no new information added)."""
    s = json.loads((RES / "kz_summary.json").read_text())
    k = s["scale_factor_kzt_per_ntd"]
    bt = pd.read_csv(RES / "kz_bootstrap.csv")
    r = bt[(bt.scenario == "TW_base") & (bt.algo == "GradBoost") & (bt.comparison == "B-A")].iloc[0]
    ref = json.loads((RES / "dvf_summary.json").read_text())["profit_diff_bootstrap_base"]["GradBoost_B-A"]["mean_per_client"]
    assert abs(r.mean_diff_kzt / k - ref) < 1.0
    assert abs(s["E_kz"] - 27.5e12 / 39.4e6) < 1


def test_kz_margin_from_official_rates():
    import kz_adaptation as kz
    assert abs(kz.SCEN["KZ1_base"]["p"].margin - (0.225 - 0.147)) < 1e-12
    assert abs(kz.SCEN["KZ2_high_risk"]["p"].margin - (0.225 - 0.1575)) < 1e-12
    assert kz.SCEN["KZ3_data_cost"]["p"].data_cost_bp == 10 and kz.SCEN["KZ3_data_cost"]["p"].privacy_lambda_bp == 5


def test_kz_live_engine_matches_batch():
    """App path (dvf_live + scaling) reproduces results/kz_optimal.csv for every KZ scenario."""
    import kz_adaptation as kz
    o = pd.read_csv(RES / "kz_optimal.csv").set_index("scenario")
    for sk in ("KZ1_base", "KZ2_high_risk", "KZ3_data_cost"):
        tab = dvf_live.evaluate_subsets(kz.SCEN[sk]["p"])
        f = kz.E_KZ / tab.attrs["mean_ead"]
        opt = dvf_live.optimal_subset(tab)
        assert opt.subset == o.loc[sk, "optimal_subset"]
        assert abs(opt.test_net_value_pc * f - o.loc[sk, "test_net_value_pc_kzt"]) < 1.0
