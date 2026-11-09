"""Builds DataWorth_KZ_Results.xlsx from results/*. DVF sheet keeps live Excel formulas for C(S) and V(S)."""
import json
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

R = Path("results"); OUT = Path("DataWorth_KZ_Results.xlsx")
F = "Arial"; HFILL = PatternFill("solid", fgColor="0B1F3A"); YEL = PatternFill("solid", fgColor="FFFF00")
H = Font(name=F, bold=True, color="FFFFFF", size=10); N = Font(name=F, size=10); BL = Font(name=F, size=10, color="0000FF")
GR = Font(name=F, size=10, color="008000"); BOLD = Font(name=F, size=10, bold=True); TITLE = Font(name=F, size=13, bold=True)
thin = Border(bottom=Side(style="thin", color="D0D5DD"))
wb = Workbook()

def write_df(ws, df, r0=1, fmts=None):
    for j, c in enumerate(df.columns, 1):
        cell = ws.cell(r0, j, c); cell.font = H; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical="center")
    for i, row in enumerate(df.itertuples(index=False), r0 + 1):
        for j, v in enumerate(row, 1):
            cell = ws.cell(i, j, v); cell.font = N; cell.border = thin
            if fmts and df.columns[j - 1] in fmts: cell.number_format = fmts[df.columns[j - 1]]
    for j, c in enumerate(df.columns, 1):
        w = max(len(str(c)), *(len(str(x)) for x in df.iloc[:, j - 1].head(50))) if len(df) else len(str(c))
        ws.column_dimensions[get_column_letter(j)].width = min(max(10, w + 2), 48)
    ws.freeze_panes = ws.cell(r0 + 1, 1)

# 0. README
ws = wb.active; ws.title = "README"
lines = [("DataWorth KZ — эксперимент нәтижелері", TITLE),
 ("Деректер: UCI Default of Credit Card Clients (Тайвань, 2005, n = 30 000). Қазақстан деректері емес.", N),
 ("Бөлу: stratified 70/15/15, seed 42. Шектер мен гиперпараметрлер — validation, барлық көрсеткіштер — test (n = 4 500).", N),
 ("Барлық сандар Python есептеулерінен алынды (model_training.py, dvf_experiment.py). DVF парағында C(S) және V(S) — тірі Excel формулалары.", N),
 ("Ақшалай параметрлер (маржа, LGD, CCF, деректер құны, λ) — болжам, өлшенген факт емес.", N),
 ("", N), ("Түстер: көк мәтін — енгізілетін болжам; сары фон — өзгертуге болатын негізгі параметр; қара — формула; жасыл — басқа параққа сілтеме.", N),
 ("", N), ("Парақтар:", BOLD)]
sheets = ["Assumptions — DVF формулаларының кіріс параметрлері", "DVF_Subsets — 64 ақпарат комбинациясы, тірі V(S)", "Model_Comparison — 9 модель, метрикалар, 95% CI",
          "Paired_Differences — ақпарат және алгоритм әсері", "Financial_Main — 3 сценарий бойынша Π", "DVF_Frontier — өрістер бюджеті бойынша фронтир",
          "DVF_Optimal_Sets — құн/λ торындағы оңтайлы жиынтық", "Sensitivity — маржа × LGD", "Profit_Bootstrap — Π айырмаларының CI", "EDA — деректер сипаттамасы", "Tuning_Log — гиперпараметрлерді таңдау"]
for i, (t, f) in enumerate(lines + [(s, N) for s in sheets], 1):
    c = ws.cell(i, 1, t); c.font = f
ws.column_dimensions["A"].width = 130

# 1. Assumptions
summ = json.loads((R / "dvf_summary.json").read_text())
wa = wb.create_sheet("Assumptions")
rows = [("Параметр", "Мән", "Түсініктеме"),
        ("Деректер тобының құны c, б.п. EAD / клиент", 0, "Болжам (сценарий): бір ақпарат тобын сұрау/өңдеу шығыны"),
        ("Құпиялық айыппұлы λ, б.п. / өріс / клиент", 0, "Болжам: құпиялық шектеуінің модельдік бағасы"),
        ("Орташа EAD (test), NT$", round(summ["mean_ead_test_NT$"], 2), "Python: EAD = max(BILL_AMT1,0) + 0.5·max(LIMIT_BAL − BILL_AMT1, 0)"),
        ("Маржа m (Π бағаны үшін)", 0.10, "Базалық сценарий; Π мәндері осы параметрмен Python-да есептелген"),
        ("LGD (Π бағаны үшін)", 0.75, "Базалық сценарий"),
        ("Bayes шегі m/(m+LGD)", "=B5/(B5+B6)", "Формула")]
for i, r in enumerate(rows, 1):
    for j, v in enumerate(r, 1):
        c = wa.cell(i, j, v); c.font = H if i == 1 else N
        if i == 1: c.fill = HFILL
for rr in (2, 3): wa.cell(rr, 2).font = BL; wa.cell(rr, 2).fill = YEL
for rr in (4, 5, 6): wa.cell(rr, 2).font = BL
wa["B5"].number_format = wa["B6"].number_format = "0.0%"; wa["B7"].number_format = "0.000"; wa["B4"].number_format = "#,##0"
wa.column_dimensions["A"].width = 44; wa.column_dimensions["B"].width = 14; wa.column_dimensions["C"].width = 80
wa["A9"] = "B2 және B3 мәндерін өзгертсеңіз, DVF_Subsets парағындағы C(S), V(S) және оңтайлы жиынтық қайта есептеледі."; wa["A9"].font = BOLD

# 2. DVF_Subsets with formulas
sd = pd.read_csv(R / "dvf_subsets.csv")
n_va, n_te = 4500, 4500
sd = sd.sort_values(["n_fields", "subset"]).reset_index(drop=True)
wd = wb.create_sheet("DVF_Subsets")
cols = ["Жиынтық", "Топтар саны", "Өрістер саны", "Val ROC-AUC", "Test ROC-AUC", "Val Π, NT$/кл", "Test Π, NT$/кл",
        "C(S), NT$/кл", "Val V(S), NT$/кл", "Test V(S), NT$/кл", "Оңтайлы ме?"]
for j, c in enumerate(cols, 1):
    x = wd.cell(1, j, c); x.font = H; x.fill = HFILL; x.alignment = Alignment(wrap_text=True)
s0 = sd.index[sd.subset == "S0"][0] + 2
last = len(sd) + 1
for i, r in enumerate(sd.itertuples(), 2):
    vals = [r.subset, r.n_groups, r.n_fields, r.val_roc_auc, r.test_roc_auc, r.val_profit_base / n_va, r.test_profit_base / n_te]
    for j, v in enumerate(vals, 1):
        c = wd.cell(i, j, v); c.font = N
    wd.cell(i, 8, f"=(B{i}*Assumptions!$B$2+(C{i}-2)*Assumptions!$B$3)*0.0001*Assumptions!$B$4").font = GR
    wd.cell(i, 9, f"=F{i}-$F${s0}-H{i}").font = N
    wd.cell(i, 10, f"=G{i}-$G${s0}-H{i}").font = N
    wd.cell(i, 11, f'=IF(I{i}=MAX($I$2:$I${last}),"✔ оңтайлы","")').font = BOLD
    for j, fmt in ((4, "0.0000"), (5, "0.0000"), (6, "#,##0;(#,##0);-"), (7, "#,##0;(#,##0);-"), (8, "#,##0;(#,##0);-"), (9, "#,##0;(#,##0);-"), (10, "#,##0;(#,##0);-")):
        wd.cell(i, j).number_format = fmt
wd.cell(last + 2, 1, "Оңтайлы жиынтық (validation V(S) бойынша):").font = BOLD
wd.cell(last + 2, 6, f"=INDEX($A$2:$A${last},MATCH(MAX($I$2:$I${last}),$I$2:$I${last},0))").font = BOLD
wd.cell(last + 3, 1, "Оның test V(S), NT$/клиент:").font = BOLD
wd.cell(last + 3, 6, f"=INDEX($J$2:$J${last},MATCH(MAX($I$2:$I${last}),$I$2:$I${last},0))").font = BOLD
wd.cell(last + 3, 6).number_format = "#,##0;(#,##0);-"
wd.cell(last + 5, 1, "Π бағандары — Python мәні (Gradient Boosting, базалық сценарий m=10%, LGD=75%, CCF=50%; шек validation-да таңдалған). Таңдау validation бойынша, test — тәуелсіз бағалау.").font = N
wd["F1"].comment = Comment("Python: dvf_experiment.py → results/dvf_subsets.csv (val_profit_base / 4500)", "DataWorth KZ")
for j, w in enumerate([22, 9, 9, 11, 11, 13, 13, 12, 13, 13, 12], 1): wd.column_dimensions[get_column_letter(j)].width = w
wd.freeze_panes = "B2"

# other sheets
pct = "0.0%"; m4 = "0.0000"; money = "#,##0;(#,##0);-"
mc = pd.read_csv(R / "model_comparison.csv")
write_df(wb.create_sheet("Model_Comparison"), mc.drop(columns=["accuracy"]), fmts={c: m4 for c in mc.columns if mc[c].dtype == float})
pdf = pd.read_csv(R / "paired_differences.csv"); write_df(wb.create_sheet("Paired_Differences"), pdf, fmts={"diff": m4, "ci_lo": m4, "ci_hi": m4, "p_le_0": "0.000"})
fm = pd.read_csv(R / "financial_main_models.csv")
write_df(wb.create_sheet("Financial_Main"), fm, fmts={**{c: money for c in ["profit", "profit_per_client", "margin_income", "realized_loss", "model_ecl_approved", "missed_margin_false_reject", "avoided_loss_true_reject"]},
                                                       "approval_rate": pct, "bad_rate_approved": pct, "return_on_exposure": "0.00%", "threshold": "0.000"})
fr = pd.read_csv(R / "dvf_frontier.csv"); write_df(wb.create_sheet("DVF_Frontier"), fr, fmts={"test_gross_value": money, "test_gross_value_per_client": money, "test_roc_auc": m4})
op = pd.read_csv(R / "dvf_optimal_sets.csv"); write_df(wb.create_sheet("DVF_Optimal_Sets"), op, fmts={"test_net_value": money, "test_net_value_per_client": money})
se = pd.read_csv(R / "sensitivity_margin_lgd.csv"); write_df(wb.create_sheet("Sensitivity"), se, fmts={"margin": pct, "lgd": pct, **{c: money for c in se.columns if c.startswith(("profit", "value"))}, "breakeven_bp_C_vs_B_per_field": "0.00"})
pb = pd.DataFrame([{"comparison": k, **v} for k, v in summ["profit_diff_bootstrap_base"].items()])
write_df(wb.create_sheet("Profit_Bootstrap"), pb, fmts={"mean_per_client": money, "ci_lo": money, "ci_hi": money, "p_le_0": "0.000"})
eda = json.loads((R / "eda.json").read_text())
flat = [("Бақылаулар", eda["shape"]["rows"]), ("Белгілер (ID мен мақсатсыз)", eda["shape"]["features_excl_id_target"]), ("Дефолт үлесі", eda["default_rate"]),
        ("Non-default / default", f'{eda["class_counts"]["0"]} / {eda["class_counts"]["1"]}'), ("Жетіспейтін мәндер", eda["missing_values_total"]),
        ("Қайталанатын жолдар (ID-сыз)", eda["duplicate_rows_excl_id"])] + [(f"Аномалия: {k}", str(v)) for k, v in eda["anomalies"].items()] + \
       [(f"Дефолт үлесі, PAY_0 = {k}", v["default_rate"]) for k, v in eda["default_rate_by_PAY_0"].items()] + \
       [(f"Дефолт үлесі, LIMIT_BAL {k}", v) for k, v in eda["default_rate_by_limit_quintile"].items()] + \
       [(f"Корреляция мақсатпен: {k}", v) for k, v in eda["corr_with_target"].items()] + [("Leakage шолуы", eda["leakage_review"])]
write_df(wb.create_sheet("EDA"), pd.DataFrame(flat, columns=["Көрсеткіш", "Мән"]))
write_df(wb.create_sheet("Tuning_Log"), pd.read_csv(R / "tuning_log.csv"), fmts={"val_roc_auc": m4})
for w in wb.worksheets:
    w.sheet_view.showGridLines = False
wb.save(OUT); print("saved", OUT)
