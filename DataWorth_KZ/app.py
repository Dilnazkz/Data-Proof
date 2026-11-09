"""DataWorth KZ — interactive research prototype (Streamlit).

Run:  streamlit run app.py
Every number on screen comes from trained models (models/, results/predictions*.npz) and
financial_engine.py. Monetary parameters are user-set ASSUMPTIONS. Experimental data: UCI Taiwan 2005,
not Kazakhstani data. This prototype is NOT integrated with any real bank.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import confusion_matrix

from dvf_live import GROUP_INFO, BASE_FIELDS, bundle, evaluate_model, evaluate_subsets, frontier, optimal_subset, subset_fields, subset_key
from financial_engine import FinParams, bayes_threshold, ead, profit_curve

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
NAVY, PANEL, INK, MUTED, GRID = "#FFFFFF", "#F3F6FB", "#0F1B2D", "#5B6577", "#E6EAF0"
ACCENT = "#2563EB"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SET_COL = {"A": BLUE, "B": ORANGE, "C": AQUA}
ALGO_KZ = {"LogReg": "Logistic Regression", "RandomForest": "Random Forest", "GradBoost": "Gradient Boosting"}
SETS = {"A": ["LIMIT_BAL", "PAY_0"], "B": ["LIMIT_BAL", "PAY_0", "PAY_2", "PAY_3", "BILL_AMT1", "PAY_AMT1"]}

st.set_page_config(page_title="DataWorth KZ", page_icon="◆", layout="wide")
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, button, input, label {{font-family: 'Inter', system-ui, sans-serif;}}
.stApp {{background: linear-gradient(180deg, #F3F7FD 0%, #FAFBFD 320px);}}
.block-container {{padding-top: 2rem; max-width: 1320px;}}
h1 {{font-weight:700 !important; color:{INK}; letter-spacing:-0.02em; font-size:2.1rem !important;}}
h2, h3, h4, h5 {{color:{INK}; letter-spacing:-0.01em; font-weight:600 !important;}}
section[data-testid="stSidebar"] {{background:#FFFFFF; border-right:1px solid {GRID};}}
section[data-testid="stSidebar"] .stRadio label {{padding:6px 10px; border-radius:8px;}}
section[data-testid="stSidebar"] .stRadio label:hover {{background:#EEF4FF;}}
div[data-testid="stMetric"] {{background:#FFFFFF; border:1px solid {GRID}; border-radius:14px; padding:16px 18px;
  box-shadow:0 1px 2px rgba(16,24,40,.04), 0 4px 12px rgba(16,24,40,.04);}}
div[data-testid="stMetricLabel"] p {{color:{MUTED}; font-size:0.80rem; font-weight:500;}}
div[data-testid="stMetricValue"] > div {{font-size:1.6rem; font-weight:650; color:{INK}; white-space:normal; overflow-wrap:anywhere; line-height:1.25;}}
div[data-testid="stMetricDelta"] > div {{white-space:normal;}}
div[data-testid="stPlotlyChart"] {{background:#FFFFFF; border:1px solid {GRID}; border-radius:14px; padding:10px;
  box-shadow:0 1px 2px rgba(16,24,40,.04);}}
div[data-testid="stExpander"] {{background:#FFFFFF; border-radius:12px;}}
.stTabs [data-baseweb="tab-list"] {{gap:4px;}}
.stTabs [data-baseweb="tab"] {{background:#FFFFFF; border:1px solid {GRID}; border-radius:10px 10px 0 0; padding:6px 14px;}}
.dw-hero {{background:linear-gradient(120deg, #1D4ED8 0%, #3B82F6 55%, #60A5FA 100%); color:#fff; border-radius:18px; padding:26px 30px; margin-bottom:18px;
  box-shadow:0 8px 24px rgba(37,99,235,.18);}}
.dw-hero h2 {{color:#fff !important; margin:0 0 6px 0; font-size:1.7rem;}}
.dw-hero p {{color:#E6EEFF; margin:0; font-size:0.98rem;}}
.dw-brand {{font-weight:700; font-size:1.25rem; color:{INK};}}
.dw-brand span {{color:{ACCENT};}}
.dw-tag {{display:inline-block; padding:3px 10px; border-radius:999px; background:#EEF4FF; color:{ACCENT}; font-size:0.74rem; font-weight:500; margin:0 6px 6px 0;}}
.dw-note {{color:{MUTED}; font-size:0.85rem;}}
.dw-formula {{background:#FFFFFF; border:1px solid {GRID}; border-left:4px solid {ACCENT}; padding:12px 16px; border-radius:10px; color:{INK};}}
.dw-section {{font-size:0.78rem; font-weight:600; color:{MUTED}; text-transform:uppercase; letter-spacing:.06em; margin:18px 0 6px;}}
</style>""", unsafe_allow_html=True)


def fig_layout(fig, title=None, h=360, xt=None, yt=None):
    fig.update_layout(template="plotly_white", paper_bgcolor=NAVY, plot_bgcolor=NAVY, height=h,
                      margin=dict(l=10, r=10, t=40 if title else 10, b=10), title=title,
                      font=dict(color=INK, size=12, family="Inter, system-ui, sans-serif"), legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.2),
                      hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID, font=dict(color=INK)))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, title=xt)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title=yt)
    return fig


@st.cache_data
def load_tables():
    t = {n: pd.read_csv(RES / f"{n}.csv") for n in ["model_comparison", "paired_differences", "financial_main_models",
                                                    "sensitivity_margin_lgd", "dvf_subsets", "tuning_log"]}
    t["eda"] = json.loads((RES / "eda.json").read_text())
    t["curves"] = json.loads((RES / "curves.json").read_text())
    t["summary"] = json.loads((RES / "dvf_summary.json").read_text())
    t["robust"] = json.loads((RES / "robustness_logreg_ohe.json").read_text())
    return t


@st.cache_resource
def get_bundle():
    return bundle()


@st.cache_resource
def get_model(name):
    return joblib.load(ROOT / "models" / f"{name}.joblib")


@st.cache_data
def subsets_for(margin, lgd, ccf, op, cost_bp, lam_bp):
    return evaluate_subsets(FinParams(margin, lgd, ccf, op, cost_bp, lam_bp))


def param_sidebar(key):
    with st.sidebar:
        st.markdown("### Қаржылық болжамдар")
        m = st.slider("Маржа m, EAD-тен %", 1.0, 40.0, 10.0, 0.5, key=f"m_{key}") / 100
        l = st.slider("LGD, %", 10.0, 100.0, 75.0, 1.0, key=f"l_{key}") / 100
        c = st.slider("CCF (пайдаланылмаған лимит), %", 0.0, 100.0, 50.0, 5.0, key=f"c_{key}") / 100
        st.caption("Бұлар өлшенген факт емес — сценарийлік болжамдар.")
    return m, l, c


T = load_tables()
B = get_bundle()

with st.sidebar:
    st.markdown('<div class="dw-brand">◆ DataWorth <span>KZ</span></div>', unsafe_allow_html=True)
    st.caption("Financial Data Valuation · Privacy-Aware Credit Risk")
    st.markdown('<span class="dw-tag">Зерттеу прототипі</span><span class="dw-tag">Модель: UCI · Taiwan 2005</span><span class="dw-tag">Параметрлер: ҚНРДА · ҰБ 2026</span>', unsafe_allow_html=True)
    st.markdown('<div class="dw-section">Навигация</div>', unsafe_allow_html=True)
    page = st.radio("Бөлім", ["Dashboard", "Credit Risk Laboratory", "Data Value Frontier", "Financial Simulator",
                              "Privacy & Consent", "Қазақстан сценарийлері", "Research Results"], label_visibility="collapsed")
    st.divider()

mc = T["model_comparison"].set_index("model")
summ = T["summary"]["profit_diff_bootstrap_base"]

# ------------------------------------------------------------------ DASHBOARD
if page == "Dashboard":
    st.title("DataWorth KZ")
    st.markdown('<div class="dw-hero"><h2>Банкке қанша дерек жеткілікті?</h2>'
                '<p>6 өріс 19 өрістің экономикалық нәтижесін береді: кеңейтілген деректердің қосымша пайдасы статистикалық маңызды емес. '
                'Барлық көрсеткіштер — test деректері (n = 4 500).</p></div>', unsafe_allow_html=True)
    e = T["eda"]
    k = st.columns(5)
    k[0].metric("Клиенттер", f"{e['shape']['rows']:,}".replace(",", " "))
    k[1].metric("Дефолт үлесі", f"{e['default_rate']*100:.1f}%")
    k[2].metric("Ең жоғары ROC-AUC", f"{mc.roc_auc.max():.3f}", mc.roc_auc.idxmax().replace("_", " · "), delta_color="off")
    k[3].metric("B vs A, NT$ / кл", f"+{summ['GradBoost_B-A']['mean_per_client']:,.0f}".replace(",", " "), "95% CI > 0")
    k[4].metric("C vs B, NT$ / кл", f"{summ['GradBoost_C-B']['mean_per_client']:,.0f}".replace(",", " "), "маңызды емес", delta_color="off")

    c1, c2 = st.columns([1.1, 1])
    with c1:
        fm = T["financial_main_models"]
        fm = fm[(fm.scenario == "base") & (fm.model != "approve_all")].copy()
        fm["set"], fm["algo"] = fm.model.str[0], fm.model.str[2:]
        fig = go.Figure()
        for s in "ABC":
            d = fm[fm.set == s]
            fig.add_bar(x=[ALGO_KZ[a] for a in d.algo], y=d.profit_per_client, name=f"Model {s}", marker_color=SET_COL[s],
                        hovertemplate="%{x}<br>Π = %{y:,.0f} NT$/клиент<extra>Model " + s + "</extra>")
        fig_layout(fig, "Модельдік қаржылық нәтиже Π, базалық сценарий", 360, None, "NT$ / клиент")
        fig.update_layout(bargap=0.25, bargroupgap=0.08)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = go.Figure()
        for s in "ABC":
            d = mc[mc.set == s]
            fig.add_bar(x=[ALGO_KZ[a] for a in d.algo], y=d.roc_auc, name=f"Model {s}", marker_color=SET_COL[s],
                        error_y=dict(type="data", symmetric=False, array=d.roc_auc_ci_hi - d.roc_auc, arrayminus=d.roc_auc - d.roc_auc_ci_lo, color=MUTED),
                        hovertemplate="%{x}<br>AUC = %{y:.3f}<extra>Model " + s + "</extra>")
        fig_layout(fig, "ROC-AUC және 95% CI", 360, None, "ROC-AUC")
        fig.update_yaxes(range=[0.65, 0.82])
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Дерек топтарының салыстырылуы")
    rows = []
    for s, n in (("A", 2), ("B", 6), ("C", 19)):
        r = mc.loc[f"{s}_GradBoost"]
        f = T["financial_main_models"].query("scenario=='base' and model==@s+'_GradBoost'").iloc[0]
        rows.append({"Жиынтық": f"Model {s}", "Өрістер": n, "ROC-AUC": round(r.roc_auc, 3), "PR-AUC": round(r.pr_auc, 3),
                     "Brier": round(r.brier, 4), "Π, NT$/клиент": round(f.profit_per_client), "Мақұлдау": f"{f.approval_rate*100:.1f}%",
                     "Мақұлданғандағы дефолт": f"{f.bad_rate_approved*100:.1f}%"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.markdown('<p class="dw-note">Gradient Boosting, базалық сценарий: m = 10%, LGD = 75%, CCF = 50%. Шек validation-да таңдалды, нәтиже test-те өлшенді.</p>', unsafe_allow_html=True)

# ------------------------------------------------------------------ CREDIT RISK LAB
elif page == "Credit Risk Laboratory":
    st.title("Credit Risk Laboratory")
    c = st.columns([1, 1, 1.4])
    algo = c[0].selectbox("Алгоритм", list(ALGO_KZ), format_func=ALGO_KZ.get, index=2)
    show = c[1].multiselect("Модельдер", ["A", "B", "C"], default=["A", "B", "C"])
    thr = c[2].slider("Жіктеу шегі (PD ≥ шек → «дефолт»)", 0.05, 0.80, 0.25, 0.01)
    tabs = st.tabs(["ROC", "Precision–Recall", "Калибрлеу", "Confusion matrix", "Параметрлер"])
    cur = T["curves"]
    with tabs[0]:
        fig = go.Figure()
        for s in show:
            k = f"{s}_{algo}"
            fig.add_scatter(x=cur[k]["roc"]["fpr"], y=cur[k]["roc"]["tpr"], name=f"Model {s} · AUC {mc.loc[k,'roc_auc']:.3f}", line=dict(color=SET_COL[s], width=2))
        fig.add_scatter(x=[0, 1], y=[0, 1], line=dict(dash="dash", color=MUTED, width=1), showlegend=False, hoverinfo="skip")
        st.plotly_chart(fig_layout(fig, None, 420, "False Positive Rate", "True Positive Rate"), use_container_width=True)
    with tabs[1]:
        fig = go.Figure()
        for s in show:
            k = f"{s}_{algo}"
            fig.add_scatter(x=cur[k]["pr"]["recall"], y=cur[k]["pr"]["precision"], name=f"Model {s} · PR-AUC {mc.loc[k,'pr_auc']:.3f}", line=dict(color=SET_COL[s], width=2))
        fig.add_hline(y=T["eda"]["default_rate"], line=dict(dash="dot", color=MUTED), annotation_text="кездейсоқ модель")
        st.plotly_chart(fig_layout(fig, None, 420, "Recall", "Precision"), use_container_width=True)
    with tabs[2]:
        fig = go.Figure()
        for s in show:
            k = f"{s}_{algo}"
            fig.add_scatter(x=cur[k]["calibration"]["mean_pred"], y=cur[k]["calibration"]["frac_pos"], mode="lines+markers",
                            name=f"Model {s} · Brier {mc.loc[k,'brier']:.4f}", line=dict(color=SET_COL[s], width=2), marker=dict(size=8))
        fig.add_scatter(x=[0, 1], y=[0, 1], line=dict(dash="dash", color=MUTED, width=1), showlegend=False, hoverinfo="skip")
        st.plotly_chart(fig_layout(fig, None, 420, "Болжанған PD (децильдер)", "Нақты дефолт үлесі"), use_container_width=True)
    with tabs[3]:
        cols = st.columns(max(1, len(show)))
        for col, s in zip(cols, show):
            p = B["main_test"][f"{s}_{algo}"]
            cm = confusion_matrix(B["y_te"], (p >= thr).astype(int))
            tn, fp, fn, tp = cm.ravel()
            fig = go.Figure(go.Heatmap(z=cm, x=["Болжам: 0", "Болжам: 1"], y=["Нақты: 0", "Нақты: 1"], colorscale=[[0, "#EEF4FF"], [1, "#2a78d6"]],
                                       text=cm, texttemplate="%{text}", showscale=False))
            fig_layout(fig, f"Model {s}", 280); fig.update_yaxes(autorange="reversed")
            col.plotly_chart(fig, use_container_width=True)
            prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
            col.caption(f"Precision {prec:.3f} · Recall {rec:.3f} · F1 {2*prec*rec/max(prec+rec,1e-9):.3f}")
    with tabs[4]:
        cols = ["model", "best_params", "val_roc_auc", "roc_auc", "roc_auc_ci_lo", "roc_auc_ci_hi", "pr_auc", "brier", "precision", "recall", "f1", "threshold"]
        st.dataframe(T["model_comparison"][cols].round(4), hide_index=True, use_container_width=True)
        st.caption("Гиперпараметрлер validation ROC-AUC бойынша таңдалды (tuning_log.csv). Кестедегі шек — validation-дағы F1-максимум.")
    st.info("PD-нің төмендеуі — модельдің бағасы, клиенттің нақты дефолт тәуекелінің төмендеуі емес.")

# ------------------------------------------------------------------ DVF
elif page == "Data Value Frontier":
    st.title("Data Value Frontier")
    m, l, c = param_sidebar("dvf")
    with st.sidebar:
        cost = st.slider("Деректер тобының құны, б.п. EAD / клиент", 0.0, 50.0, 0.0, 0.5)
        lam = st.slider("Құпиялық айыппұлы λ, б.п. / өріс", 0.0, 10.0, 0.0, 0.25)
    st.markdown('<div class="dw-formula"><b>V(S) = Π(S) − Π(S₀) − C(S)</b>, &nbsp; C(S) = N·[ c·|топтар| + λ·|өрістер − 2| ] · EAD̄ · 10⁻⁴</div>', unsafe_allow_html=True)
    st.write("")
    tab = subsets_for(m, l, c, 0.0, cost, lam)
    st.markdown("##### Ақпарат топтарын қосу / алып тастау")
    st.caption("Базалық S₀ әрқашан қосулы: LIMIT_BAL, PAY_0.")
    gc = st.columns(3)
    defaults = {"G1", "G2", "G3"}
    chosen = [g for i, g in enumerate(GROUP_INFO) if gc[i % 3].checkbox(f"{g}: {GROUP_INFO[g][0]} ({', '.join(GROUP_INFO[g][1]) if len(GROUP_INFO[g][1]) < 3 else str(len(GROUP_INFO[g][1])) + ' өріс'})", value=g in defaults, key=f"chk_{g}")]
    key = subset_key(chosen)
    row = tab.set_index("subset").loc[key]
    opt = optimal_subset(tab)
    k = st.columns(5)
    k[0].metric("Таңдалған жиынтық", key, f"{int(row.n_fields)} өріс", delta_color="off")
    k[1].metric("Π, NT$ / клиент", f"{row.test_profit_pc:,.0f}".replace(",", " "))
    k[2].metric("Деректер шығыны C(S)", f"{row.data_cost_pc:,.0f}".replace(",", " "))
    k[3].metric("Таза құн V(S)", f"{row.test_net_value_pc:,.0f}".replace(",", " "))
    k[4].metric("Оңтайлы жиынтық", opt.subset, f"{int(opt.n_fields)} өріс · V = {opt.test_net_value_pc:,.0f}".replace(",", " "), delta_color="off")
    fr = frontier(tab)
    fig = go.Figure()
    fig.add_scatter(x=tab.n_fields, y=tab.test_net_value_pc, mode="markers", name="64 комбинация",
                    marker=dict(size=9, color="#B8C2D3", line=dict(color=NAVY, width=2)), text=tab.subset,
                    hovertemplate="%{text}<br>%{x} өріс<br>V = %{y:,.0f} NT$<extra></extra>")
    fig.add_scatter(x=fr.max_fields, y=fr.test_net_value_pc, mode="lines", line_shape="hv", name="Frontier (validation бойынша таңдау)",
                    line=dict(color=ACCENT, width=2.5), text=fr.subset, hovertemplate="≤ %{x} өріс → %{text}<br>V = %{y:,.0f}<extra></extra>")
    fig.add_scatter(x=[row.n_fields], y=[row.test_net_value_pc], mode="markers", name="Таңдалған", marker=dict(size=16, color=ORANGE, line=dict(color=NAVY, width=2)))
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    fig_layout(fig, None, 430, "Пайдаланылған шикі өрістер саны (құпиялық жүктемесі)", "V(S), NT$ / клиент (test)")
    fig.update_xaxes(range=[1.3, 19.7], dtick=1)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Барлық 64 жиынтықтың кестесі"):
        show_cols = ["subset", "n_fields", "threshold", "approval_rate", "test_profit_pc", "data_cost_pc", "val_net_value_pc", "test_net_value_pc"]
        st.dataframe(tab[show_cols].sort_values("val_net_value_pc", ascending=False).round(3), hide_index=True, use_container_width=True)
    st.caption(f"Оңтайлы жиынтық validation бойынша таңдалады, мән test-те көрсетіледі. Орташа EAD = {tab.attrs['mean_ead']:,.0f} NT$. "
               "Барлық 64 модель бірдей Gradient Boosting баптауларымен оқытылған — тек ақпарат өзгереді.".replace(",", " "))

# ------------------------------------------------------------------ FINANCIAL SIMULATOR
elif page == "Financial Simulator":
    st.title("Financial Simulator")
    m, l, c = param_sidebar("sim")
    with st.sidebar:
        op = st.number_input("Операциялық шығын, NT$ / клиент", 0.0, 5000.0, 0.0, 50.0)
        dcost = st.number_input("Деректер құны, NT$ / клиент (бір топ)", 0.0, 5000.0, 0.0, 10.0)
    p = FinParams(m, l, c, op)
    t1, t2 = st.tabs(["Портфель", "Бір клиент"])
    with t1:
        c1, c2 = st.columns([1, 1.3])
        algo = c1.selectbox("Алгоритм", list(ALGO_KZ), format_func=ALGO_KZ.get, index=2, key="sim_algo")
        mode = c1.radio("Шешім шегі", ["Validation бойынша оңтайлы", "Bayes: m / (m + LGD)", "Қолмен"], index=0)
        manual = c1.slider("Қолмен шек", 0.02, 0.80, 0.15, 0.01, disabled=mode != "Қолмен")
        ev, et = ead(B["limit_va"], B["bill_va"], c), ead(B["limit_te"], B["bill_te"], c)
        res = {}
        for s, ng in (("A", 0), ("B", 3), ("C", 6)):
            k = f"{s}_{algo}"
            th = None if mode.startswith("Validation") else (bayes_threshold(p) if mode.startswith("Bayes") else manual)
            r = evaluate_model(B["main_val"][k], B["main_test"][k], p, th)
            r["data_cost_pc"] = ng * dcost
            r["net_pc"] = r["profit_per_client"] - r["data_cost_pc"]
            res[s] = r
        with c2:
            g, prof = profit_curve(B["y_te"], B["main_test"][f"B_{algo}"], et, p)
            fig = go.Figure()
            for s in "ABC":
                g, prof = profit_curve(B["y_te"], B["main_test"][f"{s}_{algo}"], et, p)
                fig.add_scatter(x=g, y=prof / len(et), name=f"Model {s}", line=dict(color=SET_COL[s], width=2),
                                hovertemplate="шек %{x:.2f}<br>Π = %{y:,.0f} NT$<extra>Model " + s + "</extra>")
                fig.add_scatter(x=[res[s]["threshold"]], y=[res[s]["profit_per_client"]], mode="markers", showlegend=False,
                                marker=dict(size=11, color=SET_COL[s], line=dict(color=NAVY, width=2)), hoverinfo="skip")
            fig.add_vline(x=bayes_threshold(p), line=dict(dash="dot", color=MUTED), annotation_text="Bayes шегі")
            fig_layout(fig, "Шек → модельдік пайда Π(t), test", 330, "PD шегі t", "NT$ / клиент")
            fig.update_xaxes(range=[0, 0.83])
            st.plotly_chart(fig, use_container_width=True)
        tbl = pd.DataFrame({f"Model {s}": {
            "Шек t": round(r["threshold"], 3), "Мақұлдау үлесі": f"{r['approval_rate']*100:.1f}%",
            "Мақұлданғандағы дефолт": f"{r['bad_rate_approved']*100:.1f}%",
            "Маржа табысы, NT$/кл": round(r["margin_income"] / len(et)), "Нақты шығын, NT$/кл": round(r["realized_loss"] / len(et)),
            "Модельдік ECL = PD×LGD×EAD, NT$/кл": round(r["model_ecl_approved"] / len(et)),
            "Қате бас тарту (жоғалған маржа), NT$/кл": round(r["missed_margin_false_reject"] / len(et)),
            "Болдырылмаған шығын, NT$/кл": round(r["avoided_loss_true_reject"] / len(et)),
            "Π, NT$/кл": round(r["profit_per_client"]), "Деректер құны, NT$/кл": round(r["data_cost_pc"]),
            "Таза нәтиже, NT$/кл": round(r["net_pc"])} for s, r in res.items()})
        st.dataframe(tbl.astype(str), use_container_width=True)
        st.caption("Шешім: лимитті келесі кезеңге жалғастыру (PD < t) немесе тоқтату. Дефолтсыз клиент: +m·EAD; дефолт: −LGD·EAD.")
    with t2:
        st.markdown("Бір клиенттің PD-і **нақты оқытылған** Model A және Model B (Gradient Boosting) арқылы есептеледі.")
        cc = st.columns(3)
        lim = cc[0].number_input("LIMIT_BAL, NT$", 10000, 1000000, 120000, 10000)
        pay0 = cc[0].selectbox("PAY_0 (соңғы ай)", list(range(-2, 9)), index=2, help="-2/-1/0 — уақытында; 1…8 — кешіктірілген айлар")
        pay2 = cc[1].selectbox("PAY_2", list(range(-2, 9)), index=2)
        pay3 = cc[1].selectbox("PAY_3", list(range(-2, 9)), index=2)
        bill = cc[2].number_input("BILL_AMT1, NT$", -50000, 1000000, 40000, 1000)
        pamt = cc[2].number_input("PAY_AMT1, NT$", 0, 1000000, 2000, 500)
        xa = np.array([[lim, pay0]]); xb = np.array([[lim, pay0, pay2, pay3, bill, pamt]])
        pda = float(get_model("A_GradBoost").predict_proba(xa)[0, 1]); pdb = float(get_model("B_GradBoost").predict_proba(xb)[0, 1])
        e_i = float(ead(lim, bill, c)); t = bayes_threshold(p)
        k = st.columns(4)
        k[0].metric("PD — Model A", f"{pda*100:.1f}%"); k[1].metric("PD — Model B", f"{pdb*100:.1f}%")
        k[2].metric("EAD", f"{e_i:,.0f} NT$".replace(",", " ")); k[3].metric("Bayes шегі", f"{t*100:.1f}%")
        for nm, pdv in (("Model A", pda), ("Model B", pdb)):
            ecl = pdv * l * e_i; exp_profit = (1 - pdv) * m * e_i - ecl
            dec = "Мақұлдау" if pdv < t else "Бас тарту"
            st.markdown(f"**{nm}:** ECL = PD×LGD×EAD = {ecl:,.0f} NT$ · күтілетін нәтиже = {exp_profit:,.0f} NT$ → **{dec}**".replace(",", " "))

# ------------------------------------------------------------------ PRIVACY & CONSENT
elif page == "Privacy & Consent":
    st.title("Privacy & Consent")
    st.markdown("Деректерді минимизациялау: банк **мақсатқа қажетті ең аз** ақпаратты сұрауы тиіс. Құпиялық бұл жобада "
                "өлшенген факт емес — ашық сипатталған **модельдік шектеу**: өрістер саны мен тарих тереңдігі және λ айыппұлы.")
    m, l, c = param_sidebar("prv")
    with st.sidebar:
        lam = st.slider("Құпиялық айыппұлы λ, б.п. / өріс", 0.0, 10.0, 1.0, 0.25, key="lam_prv")
    tab = subsets_for(m, l, c, 0.0, 0.0, lam).set_index("subset")
    scen = [("Минималды келісім", "S0", "Лимит + соңғы ай мәртебесі", "1 ай"),
            ("Іріктелген келісім (Model B)", "G1+G2+G3", "+ 2–3 ай мәртебесі, соңғы шот және төлем", "3 ай"),
            ("Кеңейтілген келісім (Model C)", "G1+G2+G3+G4+G5+G6", "+ 6 айлық толық шот/төлем тарихы", "6 ай")]
    rows = [{"Сценарий": a, "Жиынтық": s, "Деректер": d, "Тарих": h, "Өрістер": int(tab.loc[s, "n_fields"]),
             "Құпиялық жүктемесі": f"{(tab.loc[s,'n_fields'])/19*100:.0f}%",
             "Π, NT$/кл": round(tab.loc[s, "test_profit_pc"]), "V(S) λ-мен, NT$/кл": round(tab.loc[s, "test_net_value_pc"])} for a, s, d, h in scen]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    b_, c_ = tab.loc["G1+G2+G3"], tab.loc["G1+G2+G3+G4+G5+G6"]
    k = st.columns(3)
    k[0].metric("Алынып тасталған өрістер (C → B)", "13 / 19", "−68%", delta_color="off")
    k[1].metric("Π өзгерісі (C → B)", f"{b_.test_profit_pc - c_.test_profit_pc:+,.0f} NT$/кл".replace(",", " "))
    k[2].metric("Оңтайлы жиынтық (λ ескерілген)", optimal_subset(subsets_for(m, l, c, 0.0, 0.0, lam).reset_index(drop=True)).subset)
    lams = np.arange(0, 10.25, 0.5)
    opt = [optimal_subset(subsets_for(m, l, c, 0.0, 0.0, float(x))) for x in lams]
    fig = go.Figure(go.Scatter(x=lams, y=[o.n_fields for o in opt], mode="lines+markers", line_shape="hv", line=dict(color=ACCENT, width=2),
                               text=[o.subset for o in opt], hovertemplate="λ = %{x} б.п.<br>%{y} өріс: %{text}<extra></extra>"))
    st.plotly_chart(fig_layout(fig, "Құпиялық бағасы өскенде оңтайлы өрістер саны", 320, "λ, б.п. / өріс", "Оңтайлы жиынтықтағы өрістер"), use_container_width=True)
    st.markdown("#### Келісім қағидаттары (ұсыныс)")
    st.markdown("""
- **Мақсатты шектеу:** келісім нақты мақсатқа (кредиттік лимитті қайта бағалау) беріледі.
- **Минимизациялау:** әдепкі сұрау — DVF анықтаған жиынтық; кеңейтілген деректер тек экономикалық негізделгенде.
- **Түйіршікті келісім:** клиент ақпарат топтарын (G1–G6) жеке-жеке бере не кері қайтара алады.
- **Мерзім:** келісімнің жарамдылық мерзімі және кері қайтару мүмкіндігі.
- **Есептілік:** банк қай топ не үшін қолданылғанын клиентке көрсетеді.
""")
    st.caption("Құқықтық негіз: ҚР «Дербес деректер және оларды қорғау туралы» Заңы (2013, № 94-V); Open Banking-тегі клиент келісімі ҰБ/ҰТК платформасы арқылы тіркеледі. "
               "Болашақ API интеграциясы — тек архитектуралық ұсыныс; прототип нақты банк жүйесіне қосылмаған.")

# ------------------------------------------------------------------ KAZAKHSTAN SCENARIOS
elif page == "Қазақстан сценарийлері":
    st.title("Қазақстан сценарийлері")
    st.markdown('<div class="dw-hero"><h2>Аралас зерттеу тәсілі</h2><p>PD модельдері — Тайвань деректерінде (UCI, 2005) оқытылған. '
                'Қаржылық параметрлер — Қазақстанның 2026 жылғы ресми статистикасы (ҚНРДА, Ұлттық Банк). '
                'Нәтижелер теңгемен берілген сценарийлік есеп, Қазақстан банктерінің нақты пайдасы емес.</p></div>', unsafe_allow_html=True)
    KZ_STATS = pd.DataFrame([
        ["Жеке тұлғаларға кредиттер", "26,1 трлн ₸", "01.08.2026", "ҚНРДА"],
        ["Тұтынушылық қарыздар", "17,4 трлн ₸", "01.08.2026", "ҚНРДА"],
        ["NPL90+, жеке тұлғалар", "4,7% (1,2 трлн ₸)", "01.08.2026", "ҚНРДА"],
        ["Тұтынушылық қарыздар мөлшерлемесі", "22,5%", "2026, шілде", "ҚНРДА"],
        ["Жеке тұлғалардың мерзімді депозиттері", "14,7%", "2026, шілде", "ҚНРДА"],
        ["Базалық мөлшерлеме", "15,75%", "23.10.2026", "Ұлттық Банк"],
        ["Бір кредитке шаққандағы орташа қарыз", "≈ 698 мың ₸ (27,5 трлн / 39,4 млн)", "01.01.2026", "Кредиттік бюро (Tengrinews)"],
    ], columns=["Көрсеткіш", "Мәні", "Күні", "Дереккөз"])
    PRESETS = {"1 — базалық": (22.5, 14.7, 75.0, 0.0, 0.0), "2 — жоғары тәуекел": (22.5, 15.75, 90.0, 0.0, 0.0),
               "3 — деректер құны жоғары": (22.5, 14.7, 75.0, 10.0, 5.0), "Өз параметрлерім": None}
    with st.sidebar:
        st.markdown("### Қазақстан параметрлері")
        pre = st.selectbox("Сценарий", list(PRESETS), index=0)
        d = PRESETS[pre] or (22.5, 14.7, 75.0, 0.0, 0.0)
        free = PRESETS[pre] is None
        r_c = st.number_input("Кредит мөлшерлемесі, % (жылдық)", 5.0, 60.0, d[0], 0.25, disabled=not free)
        r_f = st.number_input("Қаржыландыру құны, %", 0.0, 40.0, d[1], 0.25, disabled=not free)
        lgd_kz = st.slider("LGD, % (болжам)", 10.0, 100.0, d[2], 1.0, disabled=not free)
        c_kz = st.slider("Деректер тобының құны c, б.п.", 0.0, 50.0, d[3], 0.5, disabled=not free)
        lam_kz = st.slider("Құпиялық бағасы λ, б.п./өріс", 0.0, 12.0, d[4], 0.25, disabled=not free)
        e_kz = st.number_input("Орташа сома Ē, ₸", 50_000, 5_000_000, 698_000, 1_000)
        st.caption("Мөлшерлемелер — ресми статистика; LGD, c, λ — болжам.")
    m_kz = max((r_c - r_f) / 100, 0.0005)
    tab_kz = subsets_for(m_kz, lgd_kz / 100, 0.5, 0.0, c_kz, lam_kz)
    kf = e_kz / tab_kz.attrs["mean_ead"]                   # NT$ model units → tenge (linear rescaling)
    optk = optimal_subset(tab_kz)
    bk = tab_kz.set_index("subset")
    k = st.columns(5)
    k[0].metric("Маржа m = r − f", f"{m_kz*100:.2f}%")
    k[1].metric("Бейс шегі t*", f"{m_kz/(m_kz+lgd_kz/100):.3f}")
    k[2].metric("V(B), ₸/клиент", f"{bk.loc['G1+G2+G3','test_net_value_pc']*kf:,.0f}".replace(",", " "))
    k[3].metric("V(C), ₸/клиент", f"{bk.loc['G1+G2+G3+G4+G5+G6','test_net_value_pc']*kf:,.0f}".replace(",", " "))
    k[4].metric("Оңтайлы жиынтық", optk.subset, f"{int(optk.n_fields)} өріс", delta_color="off")
    c1, c2 = st.columns(2)
    p_kz = FinParams(m_kz, lgd_kz / 100, 0.5)
    rows = []
    for algo in ["LogReg", "RandomForest", "GradBoost"]:
        for s_ in "ABC":
            r_ = evaluate_model(B["main_val"][f"{s_}_{algo}"], B["main_test"][f"{s_}_{algo}"], p_kz)
            rows.append({"Алгоритм": ALGO_KZ[algo], "Жиынтық": s_, "Π, ₸/клиент": r_["profit_per_client"] * kf, "Мақұлдау": r_["approval_rate"]})
    pm = pd.DataFrame(rows)
    fig = go.Figure()
    for s_ in "ABC":
        q = pm[pm["Жиынтық"] == s_]
        fig.add_bar(x=q["Алгоритм"], y=q["Π, ₸/клиент"], name=f"Model {s_}", marker_color=SET_COL[s_])
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    c1.plotly_chart(fig_layout(fig, "Модельдік пайда, ₸/клиент (test, деректер шығынынсыз)", 380), use_container_width=True)
    frk = frontier(tab_kz)
    fig2 = go.Figure()
    fig2.add_scatter(x=tab_kz.n_fields, y=tab_kz.test_net_value_pc * kf, mode="markers", name="64 комбинация", text=tab_kz.subset,
                     marker=dict(size=8, color="#B8C2D3"), hovertemplate="%{text}<br>%{x} өріс<br>V = %{y:,.0f} ₸<extra></extra>")
    fig2.add_scatter(x=frk.max_fields, y=frk.test_net_value_pc * kf, mode="lines", line_shape="hv", name="Frontier", line=dict(color=ACCENT, width=2.5))
    fig2.add_hline(y=0, line=dict(color=MUTED, width=1))
    c2.plotly_chart(fig_layout(fig2, "Data Value Frontier, ₸/клиент (test)", 380, "Өрістер саны", "V(S), ₸"), use_container_width=True)
    st.markdown("#### Үш сценарийді салыстыру (алдын ала есептелген, results/kz_optimal.csv)")
    ko = pd.read_csv(RES / "kz_optimal.csv")
    names = {"TW_base": "Тайвань параметрлері (салыстыру)", "KZ1_base": "1 — базалық", "KZ2_high_risk": "2 — жоғары тәуекел",
             "KZ3_data_cost": "3 — деректер құны жоғары", "KZ_monthly": "Айлық көкжиек (тексеріс)"}
    ko["Сценарий"] = ko.scenario.map(names)
    st.dataframe(ko[["Сценарий", "optimal_subset", "n_fields", "test_net_value_pc_kzt", "B_test_net_value_pc_kzt", "C_test_net_value_pc_kzt"]]
                 .rename(columns={"optimal_subset": "Оңтайлы жиынтық", "n_fields": "Өріс", "test_net_value_pc_kzt": "V(S*), ₸",
                                  "B_test_net_value_pc_kzt": "V(B), ₸", "C_test_net_value_pc_kzt": "V(C), ₸"}).round(0),
                 hide_index=True, use_container_width=True)
    cl, cr = st.columns(2)
    with cl:
        st.markdown("#### Қазақстан статистикасы")
        st.dataframe(KZ_STATS, hide_index=True, use_container_width=True)
    with cr:
        st.markdown("#### Дереккөздердің шекарасы")
        st.markdown("""
- **Тайвань деректері:** PD болжамы, алгоритмдерді салыстыру, ROC-AUC және басқа метрикалар, 64 жиынтықтың болжам сапасы.
- **Қазақстан деректері:** маржа (кредит және депозит мөлшерлемесі), нарық көлемі, сомаларды теңгеге масштабтау.
- **Қолданылмайды:** NPL90+ клиенттің PD-і ретінде; Тайвань PD-і Қазақстан үшін калибрленген ықтималдық ретінде.
- **Болжам:** LGD, CCF, деректер құны c, құпиялық бағасы λ.
""")
    st.caption("Дереккөздер: ҚНРДА «О состоянии банковского сектора Казахстана на 1 августа 2026 года»; Ұлттық Банк, базалық мөлшерлеме туралы шешім 23.10.2026; "
               "Tengrinews, 11.06.2026 (кредиттік бюро деректері). Масштабтау сызықтық болғандықтан, жиынтықтардың реті Ē-ге тәуелді емес.")

# ------------------------------------------------------------------ RESEARCH RESULTS
else:
    st.title("Research Results")
    st.markdown("#### Гипотезаларды тексеру")
    pdiff = T["paired_differences"]
    hyp = pd.DataFrame([
        {"Гипотеза": "H1: B экономикалық тұрғыдан C-дан кем емес", "Дәлел": f"Π(C)−Π(B), GB: {summ['GradBoost_C-B']['mean_per_client']:,.0f} [{summ['GradBoost_C-B']['ci_lo']:,.0f}; {summ['GradBoost_C-B']['ci_hi']:,.0f}]; RF: {summ['RandomForest_C-B']['mean_per_client']:,.0f} [{summ['RandomForest_C-B']['ci_lo']:,.0f}; {summ['RandomForest_C-B']['ci_hi']:,.0f}]", "Қорытынды": "Ішінара расталды (GB — иә, RF — жоқ)"},
        {"Гипотеза": "H2: A → B маңызды экономикалық пайда береді", "Дәлел": f"Π(B)−Π(A), GB: +{summ['GradBoost_B-A']['mean_per_client']:,.0f} [{summ['GradBoost_B-A']['ci_lo']:,.0f}; {summ['GradBoost_B-A']['ci_hi']:,.0f}]; m ≥ 3% торында 24/24 оң", "Қорытынды": "Базалық және оптимистік сценарийде расталды; айлық сценарийде жоқ"},
        {"Гипотеза": "H3: ақпарат құны алгоритм мен кодтауға тәуелді", "Дәлел": f"LogReg AUC: A {mc.loc['A_LogReg','roc_auc']:.3f} → C {mc.loc['C_LogReg','roc_auc']:.3f}; one-hot: {T['robust']['A']['test_roc_auc']:.3f} → {T['robust']['C']['test_roc_auc']:.3f}", "Қорытынды": "Расталды"},
        {"Гипотеза": "H4: Қазақстан параметрлері жиынтық құнын және модель таңдауын өзгертеді", "Дәлел": "Базалық/жоғары тәуекел: оңтайлы жиынтық 6 өріс (өзгермеді); жоғары тәуекел: U95(C−B) = 98% Π(B), ең жақсы — RF+B; деректер құны жоғары: 3 өріс", "Қорытынды": "Ішінара расталды (сценарийлік)"},
    ])
    st.dataframe(hyp, hide_index=True, use_container_width=True)
    st.markdown("#### Жұптық bootstrap айырмалары (test, 1000 қайталау)")
    st.dataframe(pdiff.round(4), hide_index=True, use_container_width=True)
    st.markdown("#### Сезімталдық: C − B қосымша құны (Gradient Boosting)")
    se = T["sensitivity_margin_lgd"]
    pv = se.pivot(index="lgd", columns="margin", values="value_C_vs_B_per_client")
    vmax = float(np.abs(pv.values).max())
    fig = go.Figure(go.Heatmap(z=pv.values, x=[f"{x*100:.0f}%" for x in pv.columns], y=[f"{y*100:.0f}%" for y in pv.index],
                               colorscale=[[0, "#eb6834"], [0.5, "#F1F1EF"], [1, "#2a78d6"]], zmin=-vmax, zmax=vmax,
                               text=np.round(pv.values).astype(int), texttemplate="%{text}", colorbar=dict(title="NT$/кл")))
    st.plotly_chart(fig_layout(fig, None, 320, "Маржа m", "LGD"), use_container_width=True)
    st.markdown("#### Есептеу әдістемесі")
    st.markdown("""
1. **Деректер:** UCI Default of Credit Card Clients (30 000; Тайвань, 2005). Демографиялық белгілер алынып тасталды.
2. **Бөлу:** stratified 70/15/15, seed = 42; preprocessing тек train-де; гиперпараметрлер мен шек — validation-да; test — бір рет.
3. **Модельдер:** Logistic Regression, Random Forest, Gradient Boosting × Model A (2), B (6), C (19 белгі).
4. **Метрикалар:** ROC-AUC, PR-AUC, Precision, Recall, F1, Brier, калибрлеу, bootstrap 95% CI.
5. **Қаржы:** EAD = max(BILL₁,0) + CCF·max(LIMIT − BILL₁, 0); Π = Σ_мақұлданған [(1−y)·m·EAD − y·LGD·EAD]; V(S) = Π(S) − Π(S₀) − C(S).
6. **DVF:** 2⁶ = 64 ақпарат комбинациясы, өрістер бюджеті бойынша фронтир, сценарийлер мен сезімталдық.
""")
    st.warning("Шектеу: деректер Қазақстандікі емес, мақсат — келесі айдағы төлем кешігуі; барлық ақшалай параметрлер болжам.")
